from backend.app import models, database
from datetime import datetime

def seed_m11():
    db = database.SessionLocal()
    try:
        print("Seeding M11 data...")
        
        # Check if already seeded to avoid duplicates
        if db.query(models.Well).first():
            print("M11 data already exists.")
            return

        wells = [
            models.Well(tag="7-SEP-1H-RJS", description="Production Well 1", fpso="SEPETIBA"),
            models.Well(tag="7-SEP-2H-RJS", description="Production Well 2", fpso="SEPETIBA"),
            models.Well(tag="3-SEP-1-RJS", description="Gas Injection Well", fpso="SEPETIBA")
        ]
        db.add_all(wells)
        
        holidays = [
            models.Holiday(date=datetime(2024, 1, 1).date(), description="New Year", fpso="SEPETIBA"),
            models.Holiday(date=datetime(2024, 2, 13).date(), description="Carnival", fpso="SEPETIBA"),
            models.Holiday(date=datetime(2024, 4, 21).date(), description="Tiradentes", fpso="SEPETIBA")
        ]
        db.add_all(holidays)
        
        stocks = [
            models.StockLocation(name="Main Deck Store", description="Primary offshore storage", fpso="SEPETIBA"),
            models.StockLocation(name="Nitrogen Skid", description="Reagent storage", fpso="SEPETIBA"),
            models.StockLocation(name="Onshore Warehouse", description="Macaé Logistics Base", fpso="SEPETIBA")
        ]
        db.add_all(stocks)
        
        params = [
            models.ConfigParameter(key="pt_cal_freq", value="12", fpso="SEPETIBA", description="Pressure transmitter calibration interval"),
            models.ConfigParameter(key="flow_meter_proving_freq", value="1", fpso="SEPETIBA", description="Flow meter proving interval"),
            models.ConfigParameter(key="sampling_freq_days", value="7", fpso="SEPETIBA", description="Default sampling frequency"),
            models.ConfigParameter(key="system_name", value="FPSO SEPETIBA Fiscal Metering", fpso="SEPETIBA"),
            models.ConfigParameter(key="operator_name", value="SBM Offshore", fpso="SEPETIBA")
        ]
        db.add_all(params)
        db.commit()
        print("M11 seeding done.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_m11()
