from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ExportRequest(BaseModel):
    fpso_nodes: List[int] # Hierarchy Node IDs (FPSO, Systems, or Tags)
    start_date: datetime
    end_date: datetime
    file_types: List[str] # ["CERTS", "UNCERTAINTY", "EVIDENCE", "SAMPLING", "CHANGES"]
    format: str # "ZIP", "EXCEL", "PDF"

class ExportJobStatus(BaseModel):
    job_id: str
    status: str # "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    download_url: Optional[str] = None
    progress: int = 0
    message: Optional[str] = None
