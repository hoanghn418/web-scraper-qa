# backend/app/api/endpoints/jobs.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...database.crud import crud_job

router = APIRouter()

@router.get("/")
async def get_jobs(db: Session = Depends(get_db)):
    """Get list of recent jobs"""
    jobs = crud_job.get_recent_jobs(db)
    return [{"id": job.id, "url": job.url, "status": job.status, "timestamp": job.timestamp} for job in jobs]
