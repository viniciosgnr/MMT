from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import zipfile
import io
import os
from datetime import datetime
from .. import models, database
from ..schemas.export import ExportRequest, ExportJobStatus

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
)

# In-memory job tracking (should use Redis/DB for production)
export_jobs = {}

def get_suffix(item_type: str, category: str = None) -> str:
    """Map equipment/event types to audit suffixes."""
    type_map = {
        "FLOWMETER": "P",
        "PRESSURE": "S",
        "TEMPERATURE": "S",
        "DP": "S",
        "ORIFICE_PLATE": "OP",
        "STRAIGHT_RUN": "SR",
        "ZANKER": "SR",
        "REMOVAL": "R",
        "UNAVAILABLE": "UN",
        "AVAILABLE": "AV"
    }
    return type_map.get(item_type.upper(), "")

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

            # Step 2: Get all tags associated with ANY of these nodes
            tags = db.query(models.InstrumentTag).filter(
                models.InstrumentTag.hierarchy_node_id.in_(list(all_node_ids))
            ).all()

            for tag in tags:
                # Find the FPSO parent for the trigram
                # (Mocking trigram resolution for now based on tag area or area field)
                fpso_trigram = tag.area[:3].upper() if tag.area else "FPSO"
                
                # --- METROLOGICAL CONFIRMATION ---
                if "CERTS" in request.file_types:
                    # Get all equipments ever installed on this tag during the interval
                    installations = db.query(models.EquipmentTagInstallation).filter(
                        models.EquipmentTagInstallation.tag_id == tag.id
                    ).all()
                    
                    for inst in installations:
                        certs = db.query(models.EquipmentCertificate).filter(
                            models.EquipmentCertificate.equipment_id == inst.equipment_id,
                            models.EquipmentCertificate.issue_date >= request.start_date,
                            models.EquipmentCertificate.issue_date <= request.end_date
                        ).all()
                        
                        for cert in certs:
                            suffix = get_suffix(inst.equipment.equipment_type or "SECONDARY")
                            date_str = cert.issue_date.strftime("%Y-%m-%d")
                            folder_path = f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/{date_str} {suffix}".strip()
                            
                            # Real app would fetch cert.file_path from disk/S3
                            f_name = os.path.basename(cert.certificate_url) if cert.certificate_url else f"Cert_{cert.id}.pdf"
                            zip_file.writestr(f"{folder_path}/{f_name}", b"Mock PDF Content")

                # --- CHANGES REPORT (M6.3) ---
                if "CHANGES" in request.file_types:
                    # Export equipment change history for this tag
                    changes = db.query(models.EquipmentTagInstallation).filter(
                        models.EquipmentTagInstallation.tag_id == tag.id,
                        models.EquipmentTagInstallation.installation_date >= request.start_date,
                        models.EquipmentTagInstallation.installation_date <= request.end_date
                    ).all()
                    
                    if changes:
                        report_content = "Date,Equipment SN,Installed By,Action\n"
                        for ch in changes:
                            date_str = ch.installation_date.strftime("%Y-%m-%d")
                            report_content += f"{date_str},{ch.equipment.serial_number},{ch.installed_by},Installation\n"
                        
                        folder_path = f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}"
                        zip_file.writestr(f"{folder_path}/Equipment_Change_Report.csv", report_content.encode())

            # --- CHEMICAL ANALYSIS ---
            if "SAMPLING" in request.file_types:
                # Chemical Analysis has different hierarchy: Sample Point Tag
                # We'll fetch samples based on the FPSO name in the request
                # (Simplification: using the first selected node's FPSO if possible)
                samples = db.query(models.Sample).filter(
                    models.Sample.collection_date >= request.start_date,
                    models.Sample.collection_date <= request.end_date
                ).all()
                
                for sample in samples:
                    # Structure: FPSO / "Chemical analysis" / Sample point tag – Sample point name / YYYY-MM-DD
                    fpso_trigram = "FPSO" # Match to sample.campaign.fpso_name
                    date_str = sample.collection_date.strftime("%Y-%m-%d")
                    # location used as Tag - Name
                    folder_path = f"{fpso_trigram}/Chemical analysis/{sample.location}/{date_str}"
                    
                    if sample.lab_report_url:
                        f_name = os.path.basename(sample.lab_report_url)
                        zip_file.writestr(f"{folder_path}/{f_name}", b"Mock Chemical Report")

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
