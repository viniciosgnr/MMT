"""
Validation Engine — Applies statistical validation rules to extracted lab report data.

Rules:
  - CRO: O₂ > 0.5% → fail; density history 2σ check
  - PVT: density, RS, FE — all checked against 10-sample 2σ bands
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app import models
from app.services.pdf_parser import PVTResult, CROResult


SIGMA_MULTIPLIER = 2  # Standard deviations for acceptance band
HISTORY_SIZE = 10     # Number of past samples for 2σ comparison

# Hard Limits for Safety/Process Compliance
O2_LIMIT = 0.5   # (%)
H2S_LIMIT = 10.0 # (ppm)
BSW_LIMIT = 1.0  # (%)


@dataclass
class CheckResult:
    """Result of a single validation check."""
    parameter: str
    value: float
    unit: str
    status: str            # "pass", "fail", "warning", "insufficient_data"
    detail: str            # Human-readable explanation
    history_mean: Optional[float] = None
    history_std: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    history_values: List[float] = field(default_factory=list)
    history_dates: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Overall validation result for a report."""
    report_type: str
    overall_status: str   # "Approved" / "Reproved"
    checks: List[CheckResult] = field(default_factory=list)
    boletim: Optional[str] = None
    tag_point: Optional[str] = None

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")


def _get_parameter_history(
    db: Session,
    sample_point_id: int,
    parameter: str,
    exclude_sample_id: Optional[int] = None,
    limit: int = HISTORY_SIZE,
) -> List[dict]:
    """Query last N values of a parameter for a sample point.
    
    Returns list of dicts with keys: value, date, sample_id
    """
    query = (
        db.query(models.SampleResult, models.Sample)
        .join(models.Sample, models.SampleResult.sample_id == models.Sample.id)
        .filter(
            models.Sample.sample_point_id == sample_point_id,
            models.SampleResult.parameter == parameter,
        )
    )
    if exclude_sample_id:
        query = query.filter(models.Sample.id != exclude_sample_id)
    
    results = (
        query
        .order_by(desc(models.SampleResult.created_at))
        .limit(limit)
        .all()
    )
    
    return [
        {
            "value": sr.value,
            "date": s.sampling_date.isoformat() if s.sampling_date else str(sr.created_at),
            "sample_id": s.sample_id,
        }
        for sr, s in results
    ]


def _check_2sigma(
    parameter: str,
    value: float,
    unit: str,
    history: List[dict],
) -> CheckResult:
    """Check if a value falls within 2σ of the historical mean.
    
    When fewer than HISTORY_SIZE history points exist, the current value
    is replicated to fill the gap.  This bootstraps an initial baseline so
    the first sample always passes (σ = 0) and subsequent samples gradually
    build real variance.
    """
    hist_values = [h["value"] for h in history]
    hist_dates  = [h["date"]  for h in history]

    # Bootstrap: pad with the historical mean so the outlier does not mask itself
    bootstrapped = len(hist_values) < HISTORY_SIZE
    
    if not hist_values:
        # If no history, current value becomes the baseline
        mean_for_padding = value
    else:
        mean_for_padding = sum(hist_values) / len(hist_values)

    while len(hist_values) < HISTORY_SIZE:
        hist_values.append(mean_for_padding)
        hist_dates.append("bootstrap")

    mean = sum(hist_values) / len(hist_values)
    variance = sum((v - mean) ** 2 for v in hist_values) / (len(hist_values) - 1)
    std = math.sqrt(variance)

    lower = mean - SIGMA_MULTIPLIER * std
    upper = mean + SIGMA_MULTIPLIER * std

    within = lower <= value <= upper

    detail_suffix = " (bootstrapped baseline)" if bootstrapped else ""

    return CheckResult(
        parameter=parameter,
        value=value,
        unit=unit,
        status="pass" if within else "fail",
        detail=(
            f"Within 2σ range [{lower:.4f} – {upper:.4f}] (μ={mean:.4f}, σ={std:.4f}){detail_suffix}"
            if within
            else f"Outside 2σ range [{lower:.4f} – {upper:.4f}] (μ={mean:.4f}, σ={std:.4f}){detail_suffix}"
        ),
        history_mean=mean,
        history_std=std,
        lower_bound=lower,
        upper_bound=upper,
        history_values=hist_values,
        history_dates=hist_dates,
    )


def _check_hard_limit(parameter: str, value: float, unit: str, limit: float) -> CheckResult:
    """Check if a value exceeds a specific hard limit."""
    if value > limit:
        return CheckResult(
            parameter=parameter,
            value=value,
            unit=unit,
            status="fail",
            detail=f"{parameter} = {value}{unit} exceeds limit of {limit}{unit}",
        )
    return CheckResult(
        parameter=parameter,
        value=value,
        unit=unit,
        status="pass",
        detail=f"{parameter} = {value}{unit} is within {limit}{unit} limit",
    )

def _check_o2_limit(o2_value: float) -> CheckResult:
    return _check_hard_limit("o2", o2_value, "%", O2_LIMIT)

def _check_h2s_limit(h2s_value: float) -> CheckResult:
    return _check_hard_limit("h2s", h2s_value, "ppm", H2S_LIMIT)

def _check_bsw_limit(bsw_value: float) -> CheckResult:
    return _check_hard_limit("bsw", bsw_value, "%", BSW_LIMIT)


def validate_pvt(
    extracted: PVTResult,
    sample: models.Sample,
    db: Session,
) -> ValidationResult:
    """Validate a PVT report against historical data.
    
    Checks density, RS, and FE against 2σ bands from last 10 samples.
    """
    result = ValidationResult(
        report_type="PVT",
        overall_status="Approved",
        boletim=extracted.boletim,
        tag_point=extracted.tag_point,
    )
    
    sample_point_id = sample.sample_point_id
    
    # Check density (Massa específica)
    if extracted.density is not None:
        history = _get_parameter_history(db, sample_point_id, "density", sample.id)
        check = _check_2sigma("density", extracted.density, extracted.density_unit, history)
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
    
    # Check RS (Razão de Solubilidade)
    if extracted.rs is not None:
        history = _get_parameter_history(db, sample_point_id, "rs", sample.id)
        check = _check_2sigma("rs", extracted.rs, extracted.rs_unit, history)
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
    
    # Check FE (Fator de Encolhimento)
    if extracted.fe is not None:
        history = _get_parameter_history(db, sample_point_id, "fe", sample.id)
        check = _check_2sigma("fe", extracted.fe, extracted.fe_unit, history)
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
    
    # Check BS&W
    if extracted.bsw is not None:
        check = _check_bsw_limit(extracted.bsw)
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
    
    return result


def validate_cro(
    extracted: CROResult,
    sample: models.Sample,
    db: Session,
) -> ValidationResult:
    """Validate a CRO (Chromatography) report.
    
    Checks:
      1. O₂ hard limit (>0.5% = fail)
      2. Densidade Relativa do Gás Real against 2σ bands
    """
    result = ValidationResult(
        report_type="CRO",
        overall_status="Approved",
        boletim=extracted.boletim,
        tag_point=extracted.tag_point,
    )
    
    sample_point_id = sample.sample_point_id
    
    # Check O₂ hard limit
    if extracted.o2 is not None:
        check = _check_o2_limit(extracted.o2)
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
    
    # Check Densidade Relativa do Gás Real (dimensionless)
    if extracted.relative_density_real is not None:
        history = _get_parameter_history(db, sample_point_id, "relative_density_real", sample.id)
        check = _check_2sigma(
            "relative_density_real", extracted.relative_density_real, extracted.relative_density_real_unit, history
        )
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
            
    # Check H2S
    if extracted.h2s is not None:
        check = _check_h2s_limit(extracted.h2s)
        result.checks.append(check)
        if check.status == "fail":
            result.overall_status = "Reproved"
    
    return result


def validate_report(
    extracted: PVTResult | CROResult,
    sample: models.Sample,
    db: Session,
) -> ValidationResult:
    """Main entry point — validate a parsed report."""
    if isinstance(extracted, PVTResult):
        return validate_pvt(extracted, sample, db)
    elif isinstance(extracted, CROResult):
        return validate_cro(extracted, sample, db)
    else:
        raise ValueError(f"Unknown report type: {type(extracted)}")
