# backend/app/database/migrate_db.py
from sqlalchemy import create_engine
from ..models.models import Base
from .database import SQLALCHEMY_DATABASE_URL
import os

def migrate_db():
    """Recreate all tables in the database."""
    # Check if database file exists and delete it
    db_file = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # Create new database with updated schema
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    print("Database migrated successfully!")

if __name__ == "__main__":
    migrate_db()
