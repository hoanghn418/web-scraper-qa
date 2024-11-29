# backend/app/database/crud.py
from sqlalchemy.orm import Session
from ..models.models import ScrapingJob, QAPair, Document
from typing import List, Optional, Dict
from datetime import datetime

class CRUDScrapingJob:
    """CRUD operations for scraping jobs."""
    def __init__(self):
        self.model = ScrapingJob
    
    def get_by_id(self, db: Session, id: int):
        return db.query(self.model).filter(self.model.id == id).first()
    
    def create(self, db: Session, *, url: str, config: Dict) -> ScrapingJob:
        db_job = ScrapingJob(
            url=url,
            status="pending",
            config=config,
            content=None  # Initialize content as None
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    
    def update_status(self, db: Session, *, job_id: int, status: str) -> ScrapingJob:
        db_job = self.get_by_id(db, job_id)
        if db_job:
            db_job.status = status
            db.commit()
            db.refresh(db_job)
        return db_job
    
    def update_job(self, db: Session, *, job_id: int, status: str, content: Dict = None) -> ScrapingJob:
        db_job = self.get_by_id(db, job_id)
        if db_job:
            db_job.status = status
            if content is not None:
                db_job.content = content
            db.commit()
            db.refresh(db_job)
        return db_job
    
    def get_recent_jobs(self, db: Session, limit: int = 10) -> List[ScrapingJob]:
        return db.query(ScrapingJob).order_by(ScrapingJob.timestamp.desc()).limit(limit).all()

class CRUDQAPair:
    """CRUD operations for Q&A pairs."""
    def __init__(self):
        self.model = QAPair
    
    def get_by_id(self, db: Session, id: int):
        return db.query(self.model).filter(self.model.id == id).first()
    
    def create_many(self, db: Session, *, job_id: int, qa_pairs: List[Dict]) -> List[QAPair]:
        db_qa_pairs = [
            QAPair(
                job_id=job_id,
                question=qa["question"],
                answer=qa["answer"],
                confidence_score=qa.get("confidence_score"),
                category=qa.get("category")
            )
            for qa in qa_pairs
        ]
        db.add_all(db_qa_pairs)
        db.commit()
        return db_qa_pairs
    
    def get_by_job_id(self, db: Session, job_id: int) -> List[QAPair]:
        return db.query(QAPair).filter(QAPair.job_id == job_id).all()

class CRUDDocument:
    """CRUD operations for documents."""
    def __init__(self):
        self.model = Document
    
    def get_by_id(self, db: Session, id: int):
        return db.query(self.model).filter(self.model.id == id).first()
    
    def create(self, db: Session, *, job_id: int, content: str, format: str) -> Document:
        db_document = Document(
            job_id=job_id,
            content=content,
            format=format
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    
    def get_by_job_and_format(self, db: Session, job_id: int, format: str) -> Optional[Document]:
        return db.query(Document).filter(
            Document.job_id == job_id,
            Document.format == format
        ).first()

# Create CRUD instances
crud_job = CRUDScrapingJob()
crud_qa = CRUDQAPair()
crud_document = CRUDDocument()