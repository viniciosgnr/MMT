from sqlalchemy.orm import Session
from fastapi import HTTPException
from .. import models
from ..schemas.export import ExportRequest
import io
import zipfile
import os
from datetime import datetime

class ExportService:
    export_jobs = {}

    @staticmethod
    def get_suffix(equipment_type: str, event_type: str) -> str:
        et = (equipment_type or "").upper()
        evt = (event_type or "").upper()
        if evt == "REMOVAL": return "R"
        if evt == "UNAVAILABLE": return "UN"
        if evt == "AVAILABLE": return "AV"
        if "FLOWMETER" in et or "PD METER" in et or "ULTRASONIC" in et: return "P"
        if "PRESSURE" in et or "TEMPERATURE" in et or "DP" in et or "TRANSMITTER" in et: return "S"
        if "ORIFICE" in et: return "OP"
        if "STRAIGHT RUN" in et or "ZANKER" in et: return "SR"
        return ""

    @classmethod
    def generate_export_zip(cls, job_id: str, request: ExportRequest, db: Session):
        try:
            cls.export_jobs[job_id]["status"] = "PROCESSING"
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                fpso_trigram = request.fpso_name[:3].upper() if request.fpso_name else "FPSO"
                all_node_ids = set(request.fpso_nodes)
                current_level_ids = request.fpso_nodes
                
                while current_level_ids:
                    child_nodes = db.query(models.HierarchyNode.id).filter(
                        models.HierarchyNode.parent_id.in_(current_level_ids)
                    ).all()
                    child_ids = [c[0] for c in child_nodes]
                    if not child_ids: break
                    all_node_ids.update(child_ids)
                    current_level_ids = child_ids

                tags = db.query(models.InstrumentTag).filter(
                    models.InstrumentTag.hierarchy_node_id.in_(list(all_node_ids))
                ).all()

                for tag in tags:
                    results = db.query(models.CalibrationResult).join(models.CalibrationTask).filter(
                        models.CalibrationTask.tag == tag.tag_number,
                        models.CalibrationResult.created_at >= request.start_date,
                        models.CalibrationResult.created_at <= request.end_date
                    ).all()

                    for res in results:
                        suffix = cls.get_suffix(res.task.equipment.equipment_type, res.task.type)
                        date_str = res.task.exec_date.strftime("%Y-%m-%d") if res.task.exec_date else res.created_at.strftime("%Y-%m-%d")
                        folder_path = f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/{date_str} {suffix}".strip()

                        if "CERTS" in request.file_types and res.certificate_url:
                            zip_file.writestr(f"{folder_path}/Certificate_{res.id}.pdf", b"Mock PDF Content")
                        if "UNCERTAINTY" in request.file_types and res.uncertainty_report_url:
                            zip_file.writestr(f"{folder_path}/Uncertainty_{res.id}.pdf", b"Mock Uncertainty Content")
                        if "EVIDENCE" in request.file_types and res.fc_evidence_url:
                            zip_file.writestr(f"{folder_path}/FC_Evidence_{res.id}.png", b"Mock FC Evidence Content")

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
                                suffix = cls.get_suffix(None, h.reason)
                                if suffix:
                                    folder_path = f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/{date_str} {suffix}"
                                    zip_file.writestr(f"{folder_path}/Equipment_Log.txt", f"Action: {h.reason}".encode())
                            zip_file.writestr(f"{fpso_trigram}/Metrological Confirmation/{tag.tag_number}/Equipment_Change_Report.csv", content.encode())

                if "SAMPLING" in request.file_types:
                    samples_query = db.query(models.Sample).filter(
                        models.Sample.sampling_date >= request.start_date,
                        models.Sample.sampling_date <= request.end_date
                    ).all()
                    for s in samples_query:
                        date_str = s.sampling_date.strftime("%Y-%m-%d")
                        folder_path = f"{fpso_trigram}/Chemical analysis/{s.sample_point.tag_number} - {s.sample_point.name}/{date_str}"
                        if s.lab_report_url:
                            zip_file.writestr(f"{folder_path}/Lab_Report_{s.sample_id}.pdf", b"Mock Lab Report")
                        if s.notes:
                             zip_file.writestr(f"{folder_path}/Sampling_Evidence.txt", b"Mock Sampling Evidence")

            cls.export_jobs[job_id]["status"] = "COMPLETED"
            cls.export_jobs[job_id]["progress"] = 100
            file_path = f"/tmp/{job_id}.zip"
            with open(file_path, "wb") as f:
                f.write(zip_buffer.getvalue())
            cls.export_jobs[job_id]["file_path"] = file_path

        except Exception as e:
            cls.export_jobs[job_id]["status"] = "FAILED"
            cls.export_jobs[job_id]["message"] = str(e)
