from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timedelta
from .. import models, database
from ..schemas import schemas
from ..dependencies import get_current_user_fpso
from ..services.maintenance_service import MaintenanceService

router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"],
)

# --- Columns ---
@router.post("/columns", response_model=schemas.MaintenanceColumn)
def create_column(column: schemas.MaintenanceColumnCreate, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    db_col = models.MaintenanceColumn(**column.model_dump())
    db.add(db_col)
    db.commit()
    db.refresh(db_col)
    return db_col

@router.get("/columns", response_model=List[schemas.MaintenanceColumn])
def read_columns(db: Session = Depends(database.get_db)):
    return db.query(models.MaintenanceColumn).order_by(models.MaintenanceColumn.order).all()

# --- Labels ---
@router.post("/labels", response_model=schemas.MaintenanceLabel)
def create_label(label: schemas.MaintenanceLabelCreate, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    db_label = models.MaintenanceLabel(**label.model_dump())
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label

@router.get("/labels", response_model=List[schemas.MaintenanceLabel])
def read_labels(db: Session = Depends(database.get_db)):
    return db.query(models.MaintenanceLabel).all()

# --- Cards ---
@router.post("/cards", response_model=schemas.MaintenanceCard)
def create_card(card: schemas.MaintenanceCardCreate, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    return MaintenanceService.create_card(db, card, current_user_data["fpso_name"])

@router.get("/cards", response_model=List[schemas.MaintenanceCard])
def read_cards(
    column_id: Optional[int] = None,
    status: Optional[str] = None,
    fpso: Optional[str] = None,
    equipment_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    responsible: Optional[str] = None,
    search: Optional[str] = None,
    due_filter: Optional[str] = None, 
    db: Session = Depends(database.get_db),
    current_user_data = Depends(get_current_user_fpso)
):
    query = db.query(models.MaintenanceCard)
    
    if column_id:
        query = query.filter(models.MaintenanceCard.column_id == column_id)
    if status:
        query = query.filter(models.MaintenanceCard.status == status)
        
    filter_fpso = current_user_data["fpso_name"] if current_user_data["fpso_name"] else fpso
    if filter_fpso:
        query = query.filter(models.MaintenanceCard.fpso == filter_fpso)
        
    if responsible:
        query = query.filter(models.MaintenanceCard.responsible.ilike(f"%{responsible}%"))
        
    if equipment_id:
        query = query.filter(models.MaintenanceCard.linked_equipments.any(models.Equipment.id == equipment_id))
    if tag_id:
        query = query.filter(models.MaintenanceCard.linked_tags.any(models.InstrumentTag.id == tag_id))

    if search:
        search_filter = or_(
            models.MaintenanceCard.title.ilike(f"%{search}%"),
            models.MaintenanceCard.description.ilike(f"%{search}%"),
            models.MaintenanceCard.comments.any(models.MaintenanceComment.text.ilike(f"%{search}%"))
        )
        query = query.filter(search_filter)
        
    if due_filter:
        now = datetime.utcnow()
        if due_filter == "overdue":
            query = query.filter(models.MaintenanceCard.due_date < now, models.MaintenanceCard.status != "Completed")
        elif due_filter == "tomorrow":
            tomorrow = now + timedelta(days=1)
            query = query.filter(models.MaintenanceCard.due_date >= now, models.MaintenanceCard.due_date <= tomorrow)
        elif due_filter == "next_week":
            next_week = now + timedelta(days=7)
            query = query.filter(models.MaintenanceCard.due_date >= now, models.MaintenanceCard.due_date <= next_week)

    return query.all()

@router.get("/cards/{card_id}", response_model=schemas.MaintenanceCard)
def read_card(card_id: int, db: Session = Depends(database.get_db)):
    db_card = db.query(models.MaintenanceCard).filter(models.MaintenanceCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Card not found")
    return db_card

@router.patch("/cards/{card_id}", response_model=schemas.MaintenanceCard)
def update_card(card_id: int, card_update: dict, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    return MaintenanceService.update_card(db, card_id, card_update, current_user_data["fpso_name"])

# --- Comments ---
@router.post("/cards/{card_id}/comments", response_model=schemas.MaintenanceComment)
def create_comment(card_id: int, comment: schemas.MaintenanceCommentCreate, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    db_comment = models.MaintenanceComment(**comment.model_dump(), card_id=card_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    db_comment = db.query(models.MaintenanceComment).filter(models.MaintenanceComment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(db_comment)
    db.commit()
    return {"status": "success"}

# --- Attachments ---
@router.post("/cards/{card_id}/attachments", response_model=schemas.MaintenanceAttachment)
async def create_attachment(card_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user_data = Depends(get_current_user_fpso)):
    # In a real app, we'd save the file to S3 or local disk. 
    # For this MVP, we'll just record the file name and a placeholder path.
    file_path = f"/uploads/maintenance/{card_id}/{file.filename}"
    db_attachment = models.MaintenanceAttachment(
        card_id=card_id,
        file_name=file.filename,
        file_path=file_path
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment
