from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import zipfile
import io
import os
from datetime import datetime
from .. import models, database
from ..schemas.export import ExportRequest, ExportJobStatus, FILE_TYPE_MAP

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
)

# In-memory job tracking (should use Redis/DB for production)
export_jobs = {}

def get_suffix(equipment_type: str, event_type: str) -> str:
    """Map equipment/event types to audit suffixes per M7 spec."""
    et = (equipment_type or "").upper()
    evt = (event_type or "").upper()
    
    # Priority 1: Events
    if evt == "REMOVAL": return "R"
    if evt == "UNAVAILABLE": return "UN"
    if evt == "AVAILABLE": return "AV"
    
    # Priority 2: Equipment Types
    if "FLOWMETER" in et or "PD METER" in et or "ULTRASONIC" in et: return "P"
    if "PRESSURE" in et or "TEMPERATURE" in et or "DP" in et or "TRANSMITTER" in et: return "S"
    if "ORIFICE" in et: return "OP"
    if "STRAIGHT RUN" in et or "ZANKER" in et: return "SR"
    
    return ""

@router.post("/prepare")
async def prepare_export(request: ExportRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    job_id = f"job_{datetime.utcnow().timestamp()}"
    export_jobs[job_id] = {"status": "PENDING", "progress": 0}
    
    background_tasks.add_task(generate_export_zip, job_id, request, db)
    return {"job_id": job_id}

@router.get("/status/{job_id}", response_model=ExportJobStatus)
async def get_status(job_id: str):
    if job_id not in export_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **export_jobs[job_id]}

async def generate_export_zip(job_id: str, request: ExportRequest, db: Session):
    try:
        export_jobs[job_id]["status"] = "PROCESSING"
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            
            # Use request.fpso_name or resolve from nodes
            fpso_trigram = request.fpso_name[:3].upper() if request.fpso_name else "FPSO"
            
            # Step 1: Resolve all child nodes if parent nodes are selected
            all_node_ids = set(request.fpso_nodes)
            current_level_ids = request.fpso_nodes
            
            while current_level_ids:
                child_nodes = db.query(models.HierarchyNode.id).filter(
                    models.HierarchyNode.parent_id.in_(current_level_ids)
                ).all()
                child_ids = [c[0] for c in child_nodes]
                if not child_ids:
                    break
                all_node_ids.update(child_ids)
                current_level_ids = child_ids

            # Step 2: Get all tags associated with these nodes
            tags = db.query(models.InstrumentTag).filter(
                models.InstrumentTag.hierarchy_node_id.in_(list(all_node_ids))
            ).all()

            for tag in tags:
                # --- METROLOGICAL CONFIRMATION ---
                # Structure: FPSO / "Metrological Confirmation" / System Tag / YYYY-MM-DD *
                
                # Fetch Calibrations (Certificates, Uncertainty, Evidence)
                results = db.query(models.CalibrationResult).join(models.CalibrationTask).filter(
                    models.CalibrationTask.tag == tag.tag_number,
                    models.CalibrationResult.created_at >= request.start_date,
                    models.CalibrationResult.created_at <= request.end_date
                ).all()

                for res in results:
                    suffix = get_suffix(res.task.equipment.equipment_type, res.task.type)
                    date_str = res.task.exec_date.strftime("%Y-%m-%d") if res.task.exec_date else res.created_at.strftime("%Y-%m-%d")
                    folder_path = f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/{date_str} {suffix}".strip()

                    # 4.1 Calibration certificates
                    if "CERTS" in request.file_types and res.certificate_url:
                        zip_file.writestr(f"{folder_path}/Certificate_{res.id}.pdf", b"Mock PDF Content")
                    
                    # 4.2 Uncertainty calculations (Uploaded or Generated)
                    if "UNCERTAINTY" in request.file_types and res.uncertainty_report_url:
                        zip_file.writestr(f"{folder_path}/Uncertainty_{res.id}.pdf", b"Mock Uncertainty Content")
                    
                    # 4.3 Calibration flow computer evidence
                    if "EVIDENCE" in request.file_types and res.fc_evidence_url:
                        zip_file.writestr(f"{folder_path}/FC_Evidence_{res.id}.png", b"Mock FC Evidence Content")

                # --- EQUIPMENT CHANGE REPORT (M6.3) ---
                if "CHANGES" in request.file_types:
                    histories = db.query(models.InstallationHistory).filter(
                        models.InstallationHistory.location == tag.tag_number,
                        models.InstallationHistory.installation_date >= request.start_date,
                        models.InstallationHistory.installation_date <= request.end_date
                    ).all()
                    
                    if histories:
                        content = "Date,Equipment SN,Action,Responsible,Notes\n"
                        for h in histories:
                            date_str = h.installation_date.strftime("%Y-%m-%d")
                            content += f"{date_str},{h.equipment.serial_number},{h.reason},{h.installed_by},{h.notes}\n"
                            
                            # Also create folders for Removal (R) etc if they are standalone events
                            suffix = get_suffix(None, h.reason)
                            if suffix:
                                folder_path = f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/{date_str} {suffix}"
                                zip_file.writestr(f"{folder_path}/Equipment_Log.txt", f"Action: {h.reason}".encode())

                        zip_file.writestr(f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/Equipment_Change_Report.csv", content.encode())

            # --- CHEMICAL ANALYSIS ---
            if "SAMPLING" in request.file_types:
                samples = db.query(models.Sample).filter(
                    models.Sample.collection_date >= request.start_date,
                    models.Sample.collection_date <= request.end_date
                ).all()
                
                for sample in samples:
                    # FPSO / "Chemical analysis" / Sample point tag – Sample point name / YYYY-MM-DD
                    date_str = sample.collection_date.strftime("%Y-%m-%d")
                    folder_path = f"{fpso_trigram}/Chemical analysis/{sample.location}/{date_str}"
                    
                    if sample.lab_report_url:
                        zip_file.writestr(f"{folder_path}/Lab_Report_{sample.sample_id}.pdf", b"Mock Lab Report")
                    # Validation report / Flow computer evidence for sampling
                    if sample.notes: # Using notes as a proxy for evidence existence in this MVP
                         zip_file.writestr(f"{folder_path}/Sampling_Evidence.txt", b"Mock Sampling Evidence")

        export_jobs[job_id]["status"] = "COMPLETED"
        export_jobs[job_id]["progress"] = 100
        
        file_path = f"/tmp/{job_id}.zip"
        with open(file_path, "wb") as f:
            f.write(zip_buffer.getvalue())
            
        export_jobs[job_id]["file_path"] = file_path

    except Exception as e:
        export_jobs[job_id]["status"] = "FAILED"
        export_jobs[job_id]["message"] = str(e)

@router.get("/download/{job_id}")
async def download_zip(job_id: str):
    if job_id not in export_jobs or export_jobs[job_id]["status"] != "COMPLETED":
        raise HTTPException(status_code=404, detail="File not ready")
    
    file_path = export_jobs[job_id].get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(file_path, filename="MMT_Audit_Export.zip", media_type="application/zip")
