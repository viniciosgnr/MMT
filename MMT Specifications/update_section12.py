import re

content = """# 12. BUSINESS & FUNCTIONAL REQUIREMENTS

This section specifies what the MMT must do to meet business needs, organized by module. Requirements are written as structured statements ("The system shall…") and grouped by capability. 

Detailed rules reflect both the original Functional Specification and the implemented MVP capabilities (including data extracted from *All Periodic Analyses* SLA tables). Requirements marked with **[MVP]** have been validated in the current development baseline.

---

## 12.1 Configuration Module (M11)

Centralizes all parametrization used across the software, ensuring no parameter is hardcoded.

1. The system shall allow admin users to model the complete FPSO hierarchy (FPSO → Metering System → Meter Run → Instruments) and assign specific system classifications (Custody Transfer, Allocation, Flare, etc.). **[MVP]**
2. The system shall support a dynamic property engine, allowing admins to define custom fields for any hierarchy level or equipment type with validation rules (min/max numeric ranges, required/optional, picklists, datatypes). **[MVP]**
3. The system shall allow admins to create, update, and remove Equipment Types (e.g., Coriolis, Orifice Plate, Flow Computer) and their associated dynamic property schemas. **[MVP]**
4. The system shall allow configuration of calibration and sampling frequencies specific to each FPSO and system classification, handling overlaps gracefully (lowest interval applies). **[MVP]**
5. The system shall support the configuration of a multi-dimensional SLA Matrix (Classification × Analysis Type × Location) reflecting complex SLA target days for each workflow phase (e.g., C+2 for Sampling, C+15 for FC Update). **[MVP]**
6. The system shall manage holiday calendars, shift patterns, and onshore warehouse logistics locations to calculate business days accurately.

---

## 12.2 Equipment Registration & Installation (M1)

Manages serial numbers, tags (functional locations), and the complete lifecycle of physical movement.

1. The system shall allow users to register Serial Numbers, dynamically enforcing the specification properties defined in M11 for the selected Equipment Type. **[MVP]**
2. The system shall manage Tags as fixed hierarchical locations tied to P&IDs, supporting equipment swap operations natively. **[MVP]**
3. The system shall track the complete installation history of every serial number against tags, maintaining an audit trail of installation/removal dates. **[MVP]**
4. The system shall maintain an aggregated view of all certificates, maintenance reports, and calibrations related to both the physical device (serial number) and the location (tag) over time. **[MVP]**
5. The system shall dynamically filter valid tags for a serial number during installation based on metadata compatibility (e.g., Fluid Type matching). **[MVP]**
6. The system shall auto-generate the Equipment Change Report (Appendix D layout) with a mandatory checklist upon installation or replacement.

---

## 12.3 Metrological Confirmation (M2)

Manages the full calibration lifecycle per ISO 10012:2003 and Resolução ANP nº 18/2014.

1. The system shall track calibrations through a strict workflow: Planning → Execution → Seal Control → Certificate Issuance → Critical Analysis (CA) → Uncertainty Calculation (UC) → Flow Computer (FC) Update → Closure.
2. The system shall calculate temporary Flow Computer override values per ANP regulations when a meter is removed from an operational line for ex-situ calibration.
3. The system shall manage physical seal tracking (installation, removal, and current status per tag), and generate targeted seal reports for audits.
4. The system shall support automated extraction of parameters from imported calibration certificates (XML/PDF) from 3rd-party vendors (e.g., Inmetro/RBC labs).
5. The system shall perform automated Critical Analysis (CA) using historical 2-sigma deviation logic and hard limit rules to flag certificates as Approved or Reproved.
6. The system shall flag documentation as "FOR REFERENCE ONLY" until the final FC Update step is closed and approved.

---

## 12.4 Chemical Analysis (M3)

Manages the sampling workflow from physical collection through flow computer update. 

1. The system shall support diverse sampling procedures: Well Test Oil, Daily Oil Sample (BSW/Density), and Periodic Gas/Oil Chromatography (CRO/PVT). **[MVP]**
2. The system shall track samples through up to 11 dynamic workflow steps (Plan → Sample → Logistics to Shore → Warehouse → Lab Delivery → Report Issue → CA Validation → FC Update). **[MVP]**
3. The system shall dynamically bypass irrelevant workflow steps (e.g., skipping transport steps for offshore tests, or skipping FC Update for Sulfur/Viscosity analyses that only inform operational limits). **[MVP]**
4. The system shall enforce target deadlines at every step by querying the *All Periodic Analyses* SLA matrix, evaluating business days based on location and classification. **[MVP]**
5. The system shall automatically ingest and parse PDF lab reports, extracting complex compositional data (e.g., Methane fraction, Density, O2) and verifying them against acceptance limits. **[MVP]**
6. The system shall trigger an Emergency Sample procedure upon CA reproval, scheduling it for the MIN(3 business days post-emission, next periodic date). **[MVP]**
7. The system shall auto-calculate the *next* planned periodic sample date immediately upon completion of the current cycle. **[MVP]**

---

## 12.5 Onshore Maintenance (M4)

Tracks equipment maintenance at onshore facilities.

1. The system shall manage maintenance activities for equipment returned to the onshore warehouse.
2. The system shall provide integration linkage to IFS (CMMS) Work Orders for tracking repair status and costs.
3. The system shall block installation of equipment to a CT tag if the equipment is flagged as "under maintenance".

---

## 12.6 Synchronize Data (M5)

Handles data exchange with external systems via structured APIs.

1. The system shall expose secure REST APIs for external systems to fetch approved calibration parameters and lab reports. **[MVP]**
2. The system shall fetch CMMS (IFS) spare parts inventory and equipment status incrementally or via scheduled sync. **[MVP]**
3. The system shall monitor synchronization health and flag failed API payloads in an admin dashboard.

---

## 12.7 Monitoring & Alerts (M6)

Provides proactive alerting for SLA compliance and parameter deviations.

1. The system shall continuously monitor Flow Computer configurations against the latest approved MMT Certificates and Lab Reports, raising an alarm if the FC operates out of compliance. **[MVP]**
2. The system shall generate automatic alerts for upcoming and overdue expirations on Calibration Certificates and Periodic Sampling, escalating warnings (e.g., 30 days, 15 days, day of, overdue).
3. The system shall identify anomalies in daily production parameters (e.g., unchanged daily volumes or static temperatures) using standard deviation rules.
4. The system shall trigger SLA breach alerts across any of the M3 (Sampling) or M2 (Calibration) workflow steps if the expected completion date is missed.

---

## 12.8 Export Data (M7)

Exports structured data for auditing purposes.

1. The system shall export filtered module views (M1, M2, M3, etc.) to Excel (.xlsx) and PDF formats. **[MVP]**
2. The system shall generate a structured ZIP archive for ANP audits, strictly following the folder structure: `FPSO → Category → Tag → Date_EventCode`.
3. The system shall package all associated metadata, XML files, and PDF certificates in the generated ZIP archives.

---

## 12.9 Planning (M8)

Provides a unified view of all outstanding activities.

1. The system shall provide aggregated calendar and list views of all planned calibrations, inspections, and sampling activities across the fleet. **[MVP]**
2. The system shall use a traffic-light color coding system determined by the SLA threshold configurations in M11.
3. The system shall allow users to log mitigations for overdue activities (attaching justifications and establishing a new projected target date).

---

## 12.10 Failure Notification — NFSM (M9)

Manages mismeasurement notifications per Resolução ANP nº 18/2014.

1. The system shall manage the opening, editing, and closure of Failure Notifications (NFSM), differentiating between Initial (≤ 240 hours) and Final notifications.
2. The system shall mandate Metering Engineer (ME) approval for NFSM closure.
3. The system shall structure captured data in a format perfectly compliant with the ANP XML schema, facilitating export.
4. The system shall distribute automatic PDF reports of approved NFSMs to configured FPSO stakeholder mailing lists.

---

## 12.11 Historical Reports (M10)

Stores ad-hoc reports not covered by other modules.

1. The system shall serve as an auditable repository for unstructured but related documents (e.g., general ANP Letters, Offloading logs). **[MVP]**
2. The system shall allow file linking to existing asset hierarchy nodes (FPSO, Metering System, Tag) and physical Serial Numbers.
3. The system shall preserve upload timestamps and usernames for non-repudiation.

---

## 12.12 User & Access Management (M12)

Controls authentication, authorization, and user administration.

1. The system shall support Role-Based Access Control (RBAC) with hierarchical access profiles (System Admin, Metering Engineer, Metering Technician, Auditor).
2. The system shall enforce FPSO-level isolation (users can only access and view data for their assigned vessels).
3. The system shall log every mutating user action (Create/Update/Delete) across all modules in an immutable Audit Log.
"""

with open('/home/marcosgnr/.gemini/antigravity/brain/ecff7083-a06a-44e7-92fb-f970e476c8b5/prd_section12_requirements.md', 'w') as f:
    f.write(content)

print('Updated Section 12 successfully.')
