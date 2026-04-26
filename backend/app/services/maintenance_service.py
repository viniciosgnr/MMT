from sqlalchemy.orm import Session
from fastapi import HTTPException
from .. import models
from ..schemas import schemas

class MaintenanceService:
    @staticmethod
    def create_card(db: Session, card: schemas.MaintenanceCardCreate, user_fpso: str = None):
        if user_fpso and card.fpso != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only create cards for your current FPSO.")
            
        card_data = card.model_dump(exclude={"label_ids", "connected_card_ids", "equipment_ids", "tag_ids"})
        db_card = models.MaintenanceCard(**card_data)
        
        if card.label_ids:
            labels = db.query(models.MaintenanceLabel).filter(models.MaintenanceLabel.id.in_(card.label_ids)).all()
            db_card.labels = labels
            
        if card.equipment_ids:
            equipments = db.query(models.Equipment).filter(models.Equipment.id.in_(card.equipment_ids)).all()
            db_card.linked_equipments = equipments
            
        if card.tag_ids:
            tags = db.query(models.InstrumentTag).filter(models.InstrumentTag.id.in_(card.tag_ids)).all()
            db_card.linked_tags = tags
            
        if card.connected_card_ids:
            connections = db.query(models.MaintenanceCard).filter(models.MaintenanceCard.id.in_(card.connected_card_ids)).all()
            db_card.connections = connections

        db.add(db_card)
        db.commit()
        db.refresh(db_card)
        return db_card

    @staticmethod
    def update_card(db: Session, card_id: int, card_update: dict, user_fpso: str = None):
        db_card = db.query(models.MaintenanceCard).filter(models.MaintenanceCard.id == card_id).first()
        if not db_card:
            raise HTTPException(status_code=404, detail="Card not found")
        if user_fpso and db_card.fpso != user_fpso:
            raise HTTPException(status_code=403, detail="Forbidden: You can only update cards for your current FPSO.")
        
        for key, value in card_update.items():
            if key == "label_ids":
                labels = db.query(models.MaintenanceLabel).filter(models.MaintenanceLabel.id.in_(value)).all()
                db_card.labels = labels
            elif key == "equipment_ids":
                equipments = db.query(models.Equipment).filter(models.Equipment.id.in_(value)).all()
                db_card.linked_equipments = equipments
            elif key == "tag_ids":
                tags = db.query(models.InstrumentTag).filter(models.InstrumentTag.id.in_(value)).all()
                db_card.linked_tags = tags
            elif key == "connected_card_ids":
                connections = db.query(models.MaintenanceCard).filter(models.MaintenanceCard.id.in_(value)).all()
                db_card.connections = connections
            else:
                setattr(db_card, key, value)
                
        db.commit()
        db.refresh(db_card)
        return db_card
