from sqlalchemy import inspect
from app.database import engine

def check():
    insp = inspect(engine)
    print("Tasks columns:", [c['name'] for c in insp.get_columns('calibration_tasks')])
    print("Results columns:", [c['name'] for c in insp.get_columns('calibration_results')])
    print("SealHistory exists:", insp.has_table('seal_history'))
    if insp.has_table('seal_history'):
         print("SealHistory columns:", [c['name'] for c in insp.get_columns('seal_history')])

if __name__ == "__main__":
    check()
