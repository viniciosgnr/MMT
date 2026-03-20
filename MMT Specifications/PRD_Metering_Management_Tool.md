# METERING MANAGEMENT TOOL — PRODUCT REQUIREMENTS DOCUMENT

| Field | Value |
|-------|-------|
| **Document ID** | OOSDOMPF-PRD-001 |
| **Project** | Asset Surveillance & Intelligence |
| **Client** | OIPOC |
| **Classification** | 2 — Restricted |
| **Author** | SBM Offshore — Metering Team |
| **Date** | March 2026 |

## REVISION STATUS

| Rev | Date | Author | Summary of Changes |
|-----|------|--------|-------------------|
| A | Mar 2026 | Metering Team | Initial issue |

---

## TABLE OF CONTENTS

1. Purpose of Document
2. Reference Documents
3. Abbreviations and Definitions
4. Current Overview & Context
5. Objectives
6. Business Value & Drivers
7. Business Interfaces
8. Business Challenges & Inefficiencies
9. Data Sources & Dependencies
10. Assumptions & Dependencies
11. Constraints
12. Business & Functional Requirements
13. Non-Functional Requirements
14. Requirements Traceability Matrix

---

# 1. PURPOSE OF DOCUMENT

## 1.1 Problem Context

Flow measurement on offshore production facilities plays a critical role in operational control, production performance tracking, contractual compliance, and environmental emission monitoring. For units operating under Brazilian jurisdiction, the regulatory framework imposed by the ANP (Agência Nacional do Petróleo) — particularly through the Metrological Technical Regulation RTM 01/2013 (Resolução Conjunta ANP/INMETRO nº 1), Resolução ANP nº 18/2014 (Failure Notification), and Resolução ANP nº 52/2013 (Gas and Oil Sampling) — demands rigorous, auditable management of the entire metering system.

The absence of a centralized tool capable of capturing the nuances of local regulation and storing all relevant data in a single, auditable repository exposes the organization to significant risks: non-compliance fines, contractual disputes with clients, and loss of operational visibility across a fleet of 10 FPSOs.

## 1.2 Product Scope

The Metering Management Tool (MMT) is a web-based application designed to manage the complete lifecycle of fiscal and operational metering systems aboard SBM Offshore's FPSO fleet in Brazil. The solution is structured around 12 functional modules, as defined in the Functional Specification (IS93502 — OOSDOMPF550001, Rev. C1):

| # | Module | Scope |
|---|--------|-------|
| M1 | Equipment Registration & Installation | Serial number tracking, tag assignments, installation/removal history |
| M2 | Metrological Confirmation | Calibration lifecycle, certificates, uncertainty calculations, FC updates |
| M3 | Chemical Analysis | Periodic sampling workflows (CRO, PVT, Enxofre, Viscosity), lab report validation, SLA tracking |
| M4 | Onshore Maintenance | Equipment maintenance tracking at onshore facilities |
| M5 | Synchronize Data | Data exchange with external systems (ANP, IFS) |
| M6 | Monitoring & Alerts | SLA-based alerting, overdue detection, compliance dashboards |
| M7 | Export Data | Structured data export for ANP audits (XML, ZIP archives) |
| M8 | Planning | Unified view of all upcoming calibrations, inspections, and samplings |
| M9 | Failure Notification (NFSM) | Mismeasurement notification management per Resolução ANP nº 18/2014 |
| M10 | Historical Reports | Audit-ready report generation with full traceability |
| M11 | Asset Hierarchy Browser (Configuration) | FPSO hierarchy modeling, metering system configuration, properties management |
| M12 | User & Access Management | Role-based access control, authentication, audit logging |

## 1.3 Document Purpose

This Product Requirements Document (PRD) serves as the **single source of truth** for what the MMT must deliver and why. It translates the business needs captured in the Functional Specification into structured, traceable product requirements that guide all downstream activities — design, development, testing, and acceptance.

Specifically, this document:

1. **Defines business context and value** — establishing the regulatory, operational, and contractual drivers that justify the initiative and the measurable outcomes expected.

2. **Specifies functional and non-functional requirements** — detailing what the system must do (capabilities per module) and how it must perform (availability, security, scalability, compliance).

3. **Establishes traceability** — linking each requirement to its originating business driver, functional specification reference, and acceptance criteria, enabling clear validation during User Acceptance Testing (UAT).

4. **Captures assumptions, constraints, and dependencies** — documenting the boundaries within which the solution must operate, including regulatory constraints, data dependencies, and integration requirements with external systems.

5. **Serves as the contractual baseline** — providing the agreed-upon requirements against which the contractor's deliverables will be evaluated, accepted, or rejected.

## 1.4 Intended Audience

| Role | Usage |
|------|-------|
| Metering Lead (ML) / Metering Engineer (ME) | Validate that requirements reflect operational reality |
| Product Owner / Business Analyst | Prioritize backlogs and trace features to business value |
| Development Team (Contractor) | Design and implement the solution per stated requirements |
| QA / UAT Team | Develop test cases and acceptance criteria |
| SBM Management / Stakeholders | Assess alignment with PACE program strategy and investment rationale |
| ANP Auditors (indirect) | Verify that the tool supports regulatory compliance obligations |

## 1.5 Document Lifecycle

This PRD is a **living document** maintained throughout the project lifecycle. It will be updated to reflect requirement changes approved through the project's change control process. All revisions will be tracked in the Revision Status table at the front of the document, with clear indication of what changed, who approved it, and the effective date.

The PRD complements — but does not replace — the detailed Software Requirements Specification (SRS) to be delivered by the contractor, which will provide implementation-level detail derived from the requirements stated herein.

---

# 2. REFERENCE DOCUMENTS

The following documents, standards, and guidelines are relevant to the definition, design, development, and validation of the Metering Management Tool. They are organized by category for ease of reference.

## 2.1 Regulatory & Legal

| Ref. | Document | Relevance |
|------|----------|-----------|
| [R1] | Resolução Conjunta ANP/INMETRO nº 1 — RTM 01/2013 | Primary metrological regulation. Calibration requirements, uncertainty limits, reporting obligations. |
| [R2] | Resolução ANP nº 18/2014 — Failure Notification | NFSM requirements, override procedures, notification timelines. |
| [R3] | Resolução ANP nº 52/2013 — Gas and Oil Sampling | Sampling frequencies, SLA timelines, laboratory validation requirements. |
| [R4] | Resolução ANP nº 65/2014 — Data Exchange | XML formats for regulatory submission of metering data. |
| [R5] | Ofício Circular ANP/NFP nº 01/2020 — RTM Clarifications | Interpretation of RTM 01/2013 requirements. |
| [R6] | ANP/NFP nº 02/2020, 835/2020, 841/2021 — COVID-19 Waivers | Temporary regulatory relaxations. |
| [R7] | Ofício Circular ANP/NFP nº 02/2021 — Resolução 18 Clarifications | Interpretation of failure notification procedures. |
| [R8] | Ofício ANP/NFP nº 906/2021 — Offloading XML | XML format for offloading data submission. |

## 2.2 International Standards

| Ref. | Document | Relevance |
|------|----------|-----------|
| [S1] | ISO 10012:2003 — Measurement management systems | Framework for metrological confirmation process. |
| [S2] | ISO 5167 — Fluid flow measurement by pressure differential devices | Orifice plate and DP metering calculations. |

## 2.3 Project Documents

| Ref. | Document |
|------|----------|
| [P1] | Metering Management Tool — Functional Specification (IS93502, OOSDOMPF550001, Rev. C1) |
| [P2] | Request for Proposal for Metering Application (Feb 2025) |
| [P3] | Product Requirements Document Template |
| [P4] | MMT Modules Description |
| [P5] | All Periodic Analyses — Sampling SLA Matrix |
| [P6] | Sampling Plan |
| [P7] | Metering Point + Sample Point Configuration — CDI |
| [P8] | MMT Presentation to PACE (Jan 2026) |

## 2.4 Report Templates & Appendices

| Appendix | Template | Module |
|----------|----------|--------|
| A | Offshore Proving Certificate | M2 |
| B | Valve Leak Test Report | M2 |
| C | Sampler Test Report | M3 |
| D | Equipment Change Report | M1 |

---

# 3. ABBREVIATIONS AND DEFINITIONS

## 3.1 Abbreviations

| Term | Definition | Context |
|------|-----------|---------|
| ANP | National Petroleum Agency (*Agência Nacional do Petróleo*) | Brazilian regulatory body overseeing oil & gas measurement |
| API | Application Programming Interface | All MMT functionalities exposed via REST APIs |
| BSW | Basic Sediment and Water | Water/sediment percentage in crude oil samples |
| CA | Critical Analysis | Automated report evaluation against historical data (2σ check) |
| CRO | Chromatography (*Cromatografia*) | Gas composition analysis — most frequent periodic type |
| CT | Custody Transfer | Metering classification with highest regulatory scrutiny |
| FC | Flow Computer | Calculates flow rates from raw sensor inputs |
| FPSO | Floating Production, Storage and Offloading | Offshore vessel; top level of asset hierarchy |
| IFS | CMMS — Maintenance Management Software | Enterprise system for spare parts integration |
| MA | Metering Analyst | Onshore: data analysis, compliance reporting |
| ME | Metering Engineer | Onshore: calibration planning, certificate validation, UC |
| ML | Metering Lead | Fleet-wide compliance oversight, resource allocation |
| MMT | Metering Management Tool | The application specified in this PRD |
| MT | Metering Technician | Offshore: calibration execution, sample collection |
| NFSM | Mismeasurement Notification (*Notificação de Falha do Sistema de Medição*) | Mandatory ANP notification on measurement failure |
| PVT | Pressure-Volume-Temperature | Fluid properties analysis under reservoir conditions |
| RTM | Metrological Technical Regulation | ANP/INMETRO regulation RTM 01/2013 |
| SLA | Service Level Agreement | Time-based targets per sampling workflow phase |
| SRS | Software Requirements Specification | Detailed spec to be produced by contractor |
| UAT | User Acceptance Testing | Formal validation by SBM end users |
| UC | Uncertainty Calculation | Mathematical determination of measurement uncertainty |

## 3.2 Domain Definitions

| Term | Definition |
|------|-----------|
| Metrological Confirmation | Set of operations to ensure measuring equipment conforms to requirements — calibration, verification, adjustment, repair, recalibration, and sealing (per ISO 10012:2003). |
| Critical Analysis (CA) | Automated evaluation of a report against acceptance criteria and historical data using statistical rules (e.g., 2σ deviation). Flags as Approved or Reproved. |
| Tag (Instrument Tag) | Unique identifier of a physical location on the process plant. Fixed address tied to P&ID; does not change when equipment is replaced. |
| Serial Number | Unique identifier of a physical device. Certificates are issued to serial numbers. May move between tags over its lifecycle. |
| Emergency Sample | Unscheduled sample triggered on reproval. Planned for the earlier of: 3 business days after report emission, or the next periodic date. |
| SLA Matrix | Configuration table mapping Classification × Analysis Type × Location to time-based targets for each workflow phase. |
| Override | Temporary replacement of FC reading with a calculated reference value during calibration, per Resolução ANP nº 18/2014. |
| Offloading | Transfer of produced oil from FPSO to shuttle tanker. Specific XML data required for ANP submission. |

---

# 4. CURRENT OVERVIEW & CONTEXT

## 4.1 Business Environment

SBM Offshore operates a fleet of FPSOs in Brazil under contracts with major oil companies (Petrobras, Shell). Flow measurement on these production facilities is critical across four fronts: **operational control**, **production performance**, **contractual targets**, and **environmental emission monitoring**.

For units operating under Brazilian jurisdiction, the **regulatory front** becomes the most critical. The ANP and INMETRO enforce tight metrological regulations through RTM 01/2013, with non-compliance resulting in significant financial exposure. In addition, GTD (Guarantee of Technical Development) certification requirements reference the use of management software, further motivating the need for a dedicated digital solution.

## 4.2 Operational Scale

| Metric | Value |
|--------|-------|
| FPSOs in operation | 9 (+ 3 new units: Almirante Tamandaré, Alexandre de Gusmão, Sepetiba) |
| Regulated instruments | 2,900 |
| Flow computers | 212 |
| Critical parameters evaluated daily | > 1,000,000 |
| Daily reports and parameter files | > 400 |
| Calibration certificates per month | 360+ |
| ANP XML file submissions per month | 1,000+ |
| Gas/oil analysis reports per month | 80+ |
| Uncertainty calculations per month | 120+ |

## 4.3 Team Structure

| Role | Headcount | Location | Responsibilities |
|------|-----------|----------|-----------------|
| Metering Lead (ML) | 1 | Onshore | Fleet-wide compliance oversight, resource allocation, client interface |
| Metering Engineers (ME) | 7 | Onshore | Calibration planning, certificate validation, UC calculations, ANP reporting |
| Metering Analyst (MA) | 1 | Onshore | Data analysis, report consolidation, compliance monitoring |
| Metering Technicians (MT) | 22 | Offshore | Calibration execution, equipment installations, seal management, sample collection |

## 4.4 Current Information Flow (AS-IS)

Today, metering data flows between offshore and onshore through a predominantly manual, file-based process.

**Key characteristics of the current state:**
- **File-based**: Data exchanged through shared folders and email, with no centralized database
- **Spreadsheet-driven**: Calibration schedules, sampling plans, and compliance tracking rely on manually maintained Excel workbooks
- **Fragmented tools**: In-house scripts and standalone utilities handle specific tasks without integration
- **No audit trail**: Changes to data and configurations are not systematically logged
- **Manual consolidation**: Engineers spend significant time collecting, validating, and reformatting data

## 4.5 Manual Effort Baseline

| Frequency | Effort per FPSO | Activities |
|-----------|----------------|------------|
| Daily | ~2.5 hours | Consolidating files, saving reports, generating certificates, validating FC configuration |
| Weekly | ~3 hours | Compliance checks, schedule reviews, reporting |
| Monthly | ~6 hours | ANP submissions, audit preparation, trend analysis |
| **Annual** | **~1,100 hours** | **Total manual effort per FPSO** |

With 9+ FPSOs, Region 1 dedicates approximately **10,000+ hours per year** to manual metering management activities.

## 4.6 Regulatory Exposure

| Non-conformity | Fine per event (USD) |
|----------------|---------------------|
| Serial number incorrectly changed | $30,000 |
| Incorrectly reported data | $28,000 |
| Incorrect flowmeter parametrization data | $225,000 – $250,000 |
| Calibration completed after due date | $225,000 – $250,000 |
| Calibration results implemented after due date | $225,000 |
| Sampling completed after due date | $250,000 |
| Sampling report issued after due date | $225,000 |
| Sampling results implemented after due date | $250,000 |
| Operate equipment beyond regulatory limits | $250,000 |

### Historical Fine Exposure

| FPSO | Accumulated fines (USD) |
|------|------------------------|
| Espírito Santo | $27,000,000 |
| Marlin Sul | $4,000,000 |
| Ilhabela | $3,600,000 |
| Capixaba | $1,000,000 |
| Paraty | $200,000 |
| **Total** | **$35,800,000** |

*Average: ~$2.5 million per year over 13 years.*

### 2025 Near-Misses

| FPSO | Issue | Exposure (USD) |
|------|-------|---------------|
| CDM | Gas composition updated 6 hours after deadline | $120,000 – $1,000,000 |
| ATD | Flowmeter calibration curve update 3 days late | $225,000 |
| SEP | Prover calibration results updated 3 days late | $225,000 |
| CDS | Failure notification sent after 72-hour deadline | $30,000 |
| **Total** | | **Up to $1,480,000** |

## 4.7 Gap Summary

1. **No centralized database** — Data scattered across folders, spreadsheets, and local tools
2. **No real-time SLA tracking** — Deadline compliance monitored reactively
3. **No automated critical analysis** — Certificate and lab report validation performed manually
4. **No integrated audit trail** — Regulatory audits require manual reconstruction
5. **No proactive alerting** — Teams unaware of approaching deadlines until too late
6. **No fleet-wide visibility** — No consolidated compliance view across FPSOs

---

# 5. OBJECTIVES

## 5.1 North Star

**Achieve zero ANP metering fines across the SBM Offshore Brazilian fleet by providing a centralized, regulation-aware digital platform that replaces manual metering management with automated, auditable workflows.**

## 5.2 SMART Objectives

| ID | Objective | Baseline | Target | Timeline |
|----|-----------|----------|--------|----------|
| OBJ-1 | Reduce regulatory fine exposure | ~$2.5M/year avg | > 40% risk reduction | 12 months post-deployment |
| OBJ-2 | Reduce manual metering effort | ~1,100 hrs/FPSO/year | > 40% reduction (< 660 hrs) | 12 months post-deployment |
| OBJ-3 | Ensure audit readiness | Days to produce evidence | < 1 hour (automated export) | Upon M7 delivery |
| OBJ-4 | Provide real-time SLA visibility | 0% automated alerting | 100% deadlines with ≥ 48h early warning | Upon M6 delivery |
| OBJ-5 | Centralize all metering data | Fragmented (folders, email) | 100% in single platform | Full module deployment |
| OBJ-6 | Scale to full fleet | N/A | 12 FPSOs without code changes | M11 as prerequisite |

## 5.3 PACE Alignment

| PACE Dimension | OKR | Annual Value (Fleet) |
|---|---|---|
| Risk exposure reduction | > 40% reduction in regulatory fine risk | ~$1,000,000/year avoided |
| Manpower reallocation | > 40% reduction in manual metering hours | +4,000 hours / +$450,000/year |

---

# 6. BUSINESS VALUE & DRIVERS

## 6.1 Business Drivers

| ID | Driver | Outcome |
|----|--------|---------|
| BV-1 | Regulatory compliance (ANP/INMETRO deadlines) | Fines of $28K–$250K per event avoided; $35.8M historical exposure eliminated |
| BV-2 | Near-miss prevention | Shift from reactive to preventive; $1.48M 2025 exposure addressed |
| BV-3 | Operational efficiency | +4,000 hrs / +$450K/year freed from manual work |
| BV-4 | Audit readiness | Evidence preparation reduced from days to minutes |
| BV-5 | Fleet scalability (3 new FPSOs) | New units onboarded via configuration, no custom dev |

## 6.2 KPIs

| KPI | Baseline | Target | Owner |
|-----|----------|--------|-------|
| ANP fine exposure ($/year) | ~$2.5M/year | > 40% reduction | Metering Lead |
| Manual metering hours (hrs/FPSO/year) | ~1,100 | < 660 (> 40% reduction) | Metering Lead |
| SLA deadlines with early warning | 0% | 100% at ≥ 48h | Metering Engineer |
| Audit evidence preparation time | Days | < 1 hour | Metering Analyst |
| FPSOs managed without code changes | 6 (legacy) | 12 (full fleet) | Product Owner |
| Data centralization coverage | 0% | 100% (certs, reports, UCs, FC configs) | Product Owner |

## 6.3 Value by Release

| Phase | Modules | Impact | Validation |
|-------|---------|--------|------------|
| **1 — Foundation** | M11, M12 | Digital hierarchy; role-based access; configurable parameters | 12 FPSOs modeled; admin setup verified |
| **2 — Core Compliance** | M1, M2, M3 | SLA tracking; calibration lifecycle; equipment traceability | Zero missed deadlines (pilot); audit trail active |
| **3 — Visibility** | M6, M8, M9 | Proactive alerting; planning dashboard; NFSM tracking | 100% SLA alerts; NFSM time reduced |
| **4 — Integration** | M4, M5, M7, M10 | IFS sync; ANP XML export; historical reports | Evidence in < 1h; XML validated |

---

# 7. BUSINESS INTERFACES

This section defines the business-facing interfaces that provide inputs to or consume outputs from the MMT.

---

### IF-1 — IFS (CMMS)

**Owner:** IT / Maintenance Team

**Business Event:** Spare parts procurement linked to calibration planning (M2)

**Data Flow:**
- **Input to MMT:** Spare parts availability, procurement follow-up status
- **Output from MMT:** Calibration-linked spare requirements

**Service Expectations:** ME must be able to link spare procurement items from IFS to planned calibrations. Integration method to be defined during Framing & Design.

---

### IF-2 — Power BI

**Owner:** Metering Analyst (MA) / IT

**Business Event:** Management reporting, KPI dashboards

**Data Flow:**
- **Input from MMT:** Direct database or API connection to MMT data
- **Output:** Three PBI reports: (1) Calibration KPI — lagging, (2) Calibration KPI — leading, (3) Chemical analysis KPI

**Service Expectations:** PBI native files (.pbix) delivered as part of scope. API endpoints stable and documented. Access control follows the same rules as the web interface.

---

### IF-3 — ANP (Regulatory Submissions)

**Owner:** Metering Analyst (MA)

**Business Event:** Regulatory data export (XML), failure notification submission (NFSM)

**Data Flow:**
- **Output from MMT:** XML files per Resolução ANP nº 65/2014, offloading XML per Ofício nº 906/2021, NFSM reports per Resolução nº 18/2014, ZIP export packages

**Service Expectations:** XML compliant with ANP schemas. NFSM within 72 hours of detection. Data retained ≥ 10 years.

---

### IF-4 — Third-Party Certificate Issuers

**Owner:** Metering Engineer (ME)

**Business Event:** Reception of calibration certificates issued by external labs

**Data Flow:**
- **Input to MMT:** XML and/or PDF certificate files imported by ME
- **Output from MMT:** Critical Analysis (CA) result; Uncertainty Calculation (UC)

**Service Expectations:** XML data auto-populates certificate fields. CA performed automatically after import.

---

### IF-5 — Laboratory (Chemical Analysis Reports)

**Owner:** Metering Engineer (ME)

**Business Event:** Reception of chemical analysis reports (CRO, PVT, Enxofre, Viscosity)

**Data Flow:**
- **Input to MMT:** PDF lab reports uploaded by ME
- **Output from MMT:** Parsed parameters; CA validation (Approved/Reproved); emergency sample on reproval

**Service Expectations:** Reports delivered within SLA window per analysis type. MMT capable of importing data from standard report formats.

---

### IF-6 — Client (Petrobras, Shell)

**Owner:** Metering Lead (ML)

**Business Event:** Compliance reporting, audit evidence sharing, contractual performance review

**Data Flow:**
- **Output from MMT:** Compliance dashboards, audit evidence packages (ZIP), calibration certificates, UC reports, permanent hyperlinks to stored documents

**Service Expectations:** All documents accessible via permanent URLs with role-based access. Reports available in Portuguese and English. Export follows the folder structure defined in M7.

---

### IF-7 — Microsoft Planner (Optional)

**Owner:** Product Owner / IT

**Business Event:** Unified task planning for calibrations, inspections, and samplings

**Data Flow:**
- **Output from MMT:** Planned activities pushed to Planner
- **Input to MMT:** Task completion status (if bidirectional)

**Service Expectations:** Optional, subject to SBM approval. If adopted, replaces dedicated Planning UI within MMT.

---

# 8. BUSINESS CHALLENGES & INEFFICIENCIES

The current metering management approach relies on manual processes, fragmented repositories, and spreadsheet-based tracking. This creates significant operational risk on a fleet of 9+ FPSOs handling 2,900 regulated instruments and over 1 million critical parameters daily. The challenges below represent the primary pain points that justify the need for the MMT and guide feature prioritization.

| ID | Challenge | Impact |
|----|-----------|--------|
| CH-1 | No automated deadline tracking for calibrations, sampling, and FC updates | $1.48M near-miss exposure in 2025; $2.5M/year avg in historical fines |
| CH-2 | Manual data consolidation across offshore/onshore | ~1,100 hrs/FPSO/year of low-value work |
| CH-3 | Fragmented data across shared folders, email, and local tools | No single source of truth; data inconsistencies |
| CH-4 | No systematic audit trail for configuration and status changes | Audit evidence takes days to reconstruct |
| CH-5 | No automated Critical Analysis for certificates and lab reports | Risk of undetected anomalies; delayed reproval |
| CH-6 | Equipment traceability gaps (serial numbers, tags, certificates) | Compliance risk during ANP audits |
| CH-7 | No scalable model for onboarding new FPSOs | Each new unit duplicates manual processes |
| CH-8 | No permanent hyperlinks or bilingual document support | Manual prep for client/regulator evidence sharing |

---

# 9. DATA SOURCES & DEPENDENCIES

The MMT ingests data from multiple sources across offshore operations, onshore engineering, third-party laboratories, and enterprise systems. Early visibility of these dependencies is essential to avoid late-stage blockers during integration.

Most data sources (DS-1 through DS-4, DS-6) are currently available but maintained in spreadsheets, PDF/XML files, and local repositories. Integration into the MMT will primarily occur via manual entry or file upload during initial phases, with API-based synchronization (particularly for IFS) to be defined during Framing & Design.

DS-1 (FPSO hierarchy) and DS-2 (equipment master data) represent the largest initial migration effort. A structured onboarding plan per FPSO should be defined to ensure data quality and completeness before go-live. DS-7 (holiday calendars) is required for business-day SLA calculations and must be configured per FPSO by admin.

| ID | Data Source | Owner / SME | Criticality |
|----|------------|-------------|-------------|
| DS-1 | FPSO hierarchy & metering system configuration | ME / ML | High |
| DS-2 | Equipment master data (serial numbers, tags, specs) | MT / ME | High |
| DS-3 | Calibration certificates & UC reports (PDF/XML) | ME | High |
| DS-4 | Chemical analysis lab reports (CRO, PVT, Enxofre, Viscosity) | ME | High |
| DS-5 | Spare parts & procurement status (IFS) | IT / Maintenance | Medium |
| DS-6 | Flow computer parameters & readings | MT | High |
| DS-7 | Holiday calendars (per FPSO / region) | ML / Admin | Medium |

---

# 10. ASSUMPTIONS & DEPENDENCIES

## 10.1 Assumptions

The following assumptions underpin the requirements in this document. If any proves invalid, impacted requirements must be reassessed.

1. **Data quality** — Metering data currently maintained in spreadsheets and local files is accurate and complete enough to serve as the baseline for initial migration into the MMT.

2. **SME availability** — The SBM Metering Team (ME, MA, MT) will be available as subject matter experts throughout Framing, Design, and UAT phases despite high operational workload.

3. **Regulatory stability** — ANP regulatory requirements (RTM 01/2013, Resolução 18/2014, Resolução 52/2013) will remain stable during the development period. Changes will be handled via the change control process.

4. **Common hierarchy model** — All FPSOs share a common metering hierarchy structure (FPSO → Metering System → Meter Run → Instruments) that can be modeled through a single configurable data model.

5. **Offshore connectivity** — Internet connectivity on offshore FPSOs is sufficient for web-based access to the MMT, at least for data entry and status updates by Metering Technicians.

6. **Lab report formats** — Third-party laboratories will continue delivering calibration certificates and analysis reports in PDF and/or XML formats compatible with MMT import capabilities.

7. **Holiday calendars** — Holiday calendars required for business-day SLA calculations will be provided and maintained by SBM Operations on a per-FPSO/region basis.

## 10.2 External Dependencies

| ID | Dependency | Risk if Delayed |
|----|-----------|----------------|
| D-1 | IFS (CMMS) API access for spare parts integration | M2 planning limited to manual spare tracking |
| D-2 | Product Owner assignment with metering domain knowledge | Requirement ambiguity; delayed acceptance |
| D-3 | Dedicated engineer (100%) with metering background | Knowledge gaps; increased rework cycles |
| D-4 | ANP XML schema specifications for export validation | M7 export cannot be validated against regulatory format |
| D-5 | SBM IT infrastructure (hosting, database, network) | Deployment timeline at risk |

---

# 11. CONSTRAINTS

The following limiting factors must be respected during product design and delivery.

## 11.1 Regulatory

1. **ANP compliance** — The MMT must comply with all reference documents listed in Section 2, particularly RTM 01/2013, Resolução 18/2014, Resolução 52/2013, and Resolução 65/2014. Non-compliance is not acceptable.

2. **Data retention** — All data (certificates, reports, production data, audit trail) must be stored and accessible for a minimum of 10 years.

3. **NFSM timelines** — Failure notifications must support submission within 72 hours of detection, as mandated by Resolução ANP nº 18/2014.

## 11.2 Technical

4. **No hardcoded parameters** — All parameters used in the software must be configurable by admin users, even where not explicitly specified in the Functional Specification.

5. **Bilingual documents** — All documents generated by the MMT must be available in both Portuguese and English. Templates subject to SBM approval.

6. **English UI** — The software interface language must be English.

7. **Permanent hyperlinks** — Every attachment, certificate, UC, or report stored in the MMT must have a permanent hyperlink that can be shared with other users, respecting access control rules.

8. **API-first architecture** — All functionalities must be exposed via authenticated REST APIs, enabling data access by SBM users and external integrations (Power BI, IFS).

## 11.3 Operational

9. **Filter persistence** — Applied filters on any page must be stored per user and restored on subsequent access. A clear filter button must be available, and the cleared state must also be persisted.

10. **Shareable URLs** — Each page must have its own unique link. Applied filters must be reflected in the URL so that shared links reproduce the exact same view for other authorized users.

11. **Template approval** — All document templates (certificates, reports, checklists) are subject to SBM approval prior to deployment.

## 11.4 Contractual

12. **Support period** — The contractor must provide 2 years of technical support and bug fixes after delivery.

13. **Active development** — 1 year of active development after delivery for functionality fixes.

14. **Required deliverables** — The contractor must deliver: detailed SRS, periodic project reports, project timeline with deployment and UAT dates, training material, and user manual.

---

# 12. BUSINESS & FUNCTIONAL REQUIREMENTS

This section specifies what the MMT must do to meet business needs, organized by module. Requirements are written as structured statements ("The system shall…") and grouped by capability.

Requirements marked with **[MVP]** have been validated in the current development baseline.

---

## 12.1 Configuration Module (M11)

Centralizes all parametrization used across the software. No parameter shall be hardcoded.

1. The system shall allow admin users to model the FPSO hierarchy: FPSO → Metering System → Meter Run → Instruments, with configurable properties at each level. **[MVP]**

2. The system shall support admin-configurable properties with name, description, unit of measure, and validation rules (free text, numeric range, list of values, mandatory, conditionally mandatory). **[MVP]**

3. The system shall allow admin users to create, update, and remove equipment types (primary and secondary devices), each with its own configurable properties. **[MVP]**

4. The system shall allow configuration of frequencies and intervals per FPSO (not globally), including calibration/inspection frequencies and sampling intervals.

5. The system shall support creation and management of wells, users, holiday calendars, stock locations, report types, and traffic-light thresholds.

6. The system shall allow admin users to configure SLA parameters per analysis type, classification, and location (Onshore/Offshore). **[MVP]**

---

## 12.2 Equipment Registration & Installation (M1)

Manages serial numbers, tags, and equipment lifecycle.

1. The system shall allow users to create serial numbers, selecting equipment type, filling specifications, and assigning one or more possible tags. **[MVP]**

2. The system shall track all certificates issued for a serial number and all certificates related to a tag (across all serial numbers ever installed on it). **[MVP]**

3. The system shall log installation, removal, and replacement dates for each serial number on each tag, generating an Equipment Change Report (Appendix D) with a completion checklist.

4. The system shall allow searching equipment by serial number, specification, instrument type, possible tags, current tags, or historical tags. **[MVP]**

5. The system shall display equipment datasheets with full historical data: calibration certificates, maintenance reports, and tag assignment history. **[MVP]**

6. The system shall prompt the user to set up a calibration frequency when creating new equipment, using intervals from M11 based on instrument type and system classification.

---

## 12.3 Metrological Confirmation (M2)

Manages the full calibration lifecycle per ISO 10012:2003.

1. The system shall manage all steps of the metrological confirmation process: Planning → Execution → Seal Control → Certificate Issuance → CA → UC → FC Update → Closing.

2. The system shall allow ME to plan calibrations by changing status from "pending" to "planned" and linking spare procurement items from IFS.

3. The system shall support both in-situ and ex-situ calibration modes, calculating override values per Resolução ANP nº 18/2014 when the line remains operational.

4. The system shall support temporary calibration dates with visual differentiation until definitive documentation is confirmed.

5. The system shall manage seal control: track all seals installed per instrument, issue Excel reports of seals on selected tags, and maintain seal history.

6. The system shall support certificate issuance by SBM (generated within MMT) and by third parties (XML/PDF import), with auto-population of fields from XML.

7. The system shall perform automated Critical Analysis (CA) on certificates using predefined rules and historical data comparison.

8. The system shall generate Uncertainty Calculations (UC) within the tool, support UC import, and provide on-demand UC capability.

9. The system shall export certificates and UC reports in both PDF and Excel, in Portuguese and English. Documents prior to approval shall carry a "FOR REFERENCE ONLY" stamp.

---

## 12.4 Chemical Analysis (M3)

Manages the sampling workflow from collection through flow computer update.

1. The system shall support three sampling categories: Oil from Well Test or Gas in General (with/without validation), Daily Oil Sample, and Periodic Samples. **[MVP]**

2. The system shall track samples through an 11-step pipeline: Plan → Sample → Disembark Preparation → Disembark Logistics → Warehouse → Logistics to Vendor → Deliver at Vendor → Report Issue → Report Under Validation → Report Approve/Reprove → Flow Computer Update. **[MVP]**

3. The system shall dynamically skip steps based on sample location (Offshore skips disembark/logistics/warehouse steps) and type (Enxofre/Viscosity/PVT skips FC update). **[MVP]**

4. The system shall apply SLA-based due dates at each step using the configurable SLA Matrix (classification × type × location). **[MVP]**

5. The system shall display dashboard cards with urgency indicators (overdue, due today, due tomorrow, on track) for each step group. **[MVP]**

6. The system shall support PDF lab report upload with automated parsing to extract parameters (gas composition, densities, O₂, etc.). **[MVP]**

7. The system shall perform automated Critical Analysis on lab reports using 2σ historical deviation checks and hard limits. **[MVP]**

8. The system shall schedule emergency samples on reproval using MIN(3 business days after report emission, next periodic planned date). **[MVP]**

9. The system shall auto-schedule the next periodic sample when collection is performed, based on the SLA Matrix interval. **[MVP]**

---

## 12.5 Onshore Maintenance (M4)

1. The system shall manage maintenance activities for equipment at onshore facilities, tracking work orders, maintenance dates, and outcomes.

2. The system shall link maintenance records to serial numbers and certificates.

---

## 12.6 Synchronize Data (M5)

1. The system shall be capable of ingesting data from IFS (spare parts, work orders) via API or scheduled synchronization. **[MVP — structure ready]**

2. The system shall maintain data consistency between MMT and external sources, generating alerts on sync failures. **[MVP — structure ready]**

---

## 12.7 Monitoring & Alerts (M6)

1. The system shall monitor flow computer system configuration daily: check parameters against latest certificates, UC, and lab reports. **[MVP — sampling alerts]**

2. The system shall check alarm limits based on UC, operational/legal limits, and calibration certificate data.

3. The system shall alert on parameters that should not change but did, and on parameters that should change daily but did not.

4. The system shall check document control gaps: alert when expected documents are overdue based on calibration dates.

5. The system shall track calibration/inspection frequency and alert at configurable thresholds: approaching, on expiration day, and overdue.

6. The system shall create sampling alerts for each step with configurable advance notice days.

7. The system shall alert when failure notifications are open by month-end (intermediate NFSM) and when initial NFSM exceed 240 hours (final NFSM).

8. The system shall check oil density and gas composition against latest approved lab reports and alert on inconsistencies.

---

## 12.8 Export Data (M7)

1. The system shall export all lists available in the software in Excel and PDF format. **[MVP]**

2. The system shall provide a selection window to choose: FPSO (tree selection), date interval, and file types. **[MVP]**

3. The system shall export a ZIP file with folders following the specified structure: FPSO trigram → "Metrological Confirmation" or "Chemical Analysis" → system/sample point tag → date-coded subfolders (YYYY-MM-DD with event type suffix: P, S, OP, SR, UN, AV, R).

---

## 12.9 Planning (M8)

1. The system shall provide two views (calendar and list) with tab-based switching. Calendar view shall support day, week, month, and custom period selection. **[MVP]**

2. The system shall group activities by day of expiration, with traffic-light color coding using configurable thresholds from M11.

3. The system shall support task completion via popup with required fields for each activity type.

4. The system shall allow filtering by FPSO, time period, and activity type.

5. The system shall support exporting outstanding activities to Excel or PDF (filtered or all items).

6. The system shall allow users to mark tasks as "mitigated" with attachments and a new due date, displayed in a different color and handled separately in KPIs.

---

## 12.10 Failure Notification — NFSM (M9)

1. The system shall support creation, editing, approval, and storage of failure notifications according to Resolução ANP nº 18/2014. **[MVP]**

2. The system shall manage initial (≤ 240h) and final NFSM types.

3. The system shall require ME approval for each failure notification.

4. The system shall export NFSM reports in PDF and Excel.

5. The system shall support configurable email distribution lists per FPSO for automatic notification upon ME approval.

6. The system shall store all data necessary to generate the ANP XML, though XML generation and web service submission are outside scope.

---

## 12.11 Historical Reports (M10)

1. The system shall allow users to upload files with metadata: file, date, FPSO, and report type (configurable in M11). **[MVP]**

2. The system shall support bulk upload of multiple files at once.

3. The system shall track who uploaded each file and when.

4. Each file may optionally be linked to an FPSO, a metering system, or a serial number.

---

## 12.12 User & Access Management (M12)

1. The system shall support role-based access control with at least three roles: admin, engineer, and technician.

2. The system shall implement authentication with login/password and a "forgot my password" recovery link.

3. The system shall enforce access control per FPSO: users only see data for FPSOs they are authorized to access.

4. API access control shall follow the same rules as the web interface.

5. The system shall log all user actions for audit trail purposes.

---

# 13. NON-FUNCTIONAL REQUIREMENTS

## 13.1 Usability

1. The system shall be fully web-based, accessible through a standard browser without additional software installation.

2. The user interface shall be intuitive, with logical navigation following the process flow.

3. The interface language shall be English. Generated documents shall be available in Portuguese and English.

4. All screens shall load in under 10 seconds. Registering a calibration and issuing a UC report shall take no more than 1 minute for a trained user.

## 13.2 Performance & Scalability

5. The system shall support at least 10 simultaneous users.

6. The system shall scale across the full fleet (12 FPSOs, 2,900+ instruments, 212 flow computers) without performance degradation.

7. Data must be stored and accessible for a minimum of 10 years.

## 13.3 Security & Access Control

8. Admin shall be able to create users with at least: username, name, password, email, and company.

9. Admin shall be able to create roles and configure read/write access per module and accessible FPSOs.

10. Each user may have one or more roles. API access control shall follow web interface rules.

11. A "forgot my password" link shall be available for password recovery.

12. All user actions shall be logged in an immutable audit trail.

## 13.4 Availability & Reliability

13. The system shall be available 24/7 with planned maintenance windows communicated in advance.

14. Data backups shall be performed regularly with documented recovery procedures.

15. The system shall handle offshore connectivity constraints gracefully, ensuring data integrity.

## 13.5 Deployment & Testing

16. The system shall be deployed in phases, each consisting of one or more modules.

17. The contractor shall issue a UAT document with test cases and feedback form.

18. The solution shall be delivered incrementally, allowing independent deployment and validation.

19. Module dependencies must be respected — prerequisite features implemented first.

## 13.6 Compliance

20. The system shall comply with all reference documents listed in Section 2.

21. All document templates shall be subject to SBM approval prior to deployment.

22. Every stored document shall have a permanent, shareable hyperlink with access control enforcement.

---

# 14. REQUIREMENTS TRACEABILITY MATRIX

This section maps business challenges to drivers, objectives, and the modules that address them, ensuring every requirement is traceable to a business justification.

| Challenge | Driver | Objective | Primary Modules | Phase |
|-----------|--------|-----------|-----------------|-------|
| CH-1 No deadline tracking | BV-1, BV-2 | OBJ-1, OBJ-4 | M6, M8, M3, M2 | 2, 3 |
| CH-2 Manual consolidation | BV-3 | OBJ-2 | M2, M3, M7, M8 | 2, 3, 4 |
| CH-3 Fragmented data | BV-4, BV-5 | OBJ-5 | M11, M1, M5 | 1, 2, 4 |
| CH-4 No audit trail | BV-4 | OBJ-3 | M7, M10, M12 | 1, 4 |
| CH-5 No automated CA | BV-1 | OBJ-1 | M2, M3 | 2 |
| CH-6 Traceability gaps | BV-1, BV-4 | OBJ-1, OBJ-3 | M1, M2 | 2 |
| CH-7 No fleet scalability | BV-5 | OBJ-6 | M11, M12 | 1 |
| CH-8 Document limitations | BV-4 | OBJ-3 | M2, M3, M7 | 2, 4 |
