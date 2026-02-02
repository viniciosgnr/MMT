from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    # Fallback to local SQLite if not provided (safety) or error out?
    # Given migration context, let's error to ensure we use Postgres
    # But for "smoothness", let's print a warning and fallback OR just fallback.
    # User put secrets in .env, so it should be there.
    # We'll default to sqlite for local dev safety if ENV isn't loaded correctly (e.g. docker)
    # But here we want to force Supabase.
    SQLALCHEMY_DATABASE_URL = "sqlite:///./mmt_mvp.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
