# backend/app/models/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class ScrapingJob(Base):
    """Model for storing scraping job information."""
    __tablename__ = "scraping_jobs"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String)  # pending, running, completed, failed
    config = Column(JSON)  # Store scraping configuration
    content = Column(JSON)  # Add this column to store scraped content
    
    # Relationships
    qa_pairs = relationship("QAPair", back_populates="job")
    documents = relationship("Document", back_populates="job")

class QAPair(Base):
    """Model for storing generated Q&A pairs."""
    __tablename__ = "qa_pairs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scraping_jobs.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    confidence_score = Column(Float)
    category = Column(String)
    
    # Relationship back to job
    job = relationship("ScrapingJob", back_populates="qa_pairs")

class Document(Base):
    """Model for storing generated documents (markdown, PDF)."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scraping_jobs.id"))
    content = Column(Text)
    format = Column(String)  # markdown, pdf
    
    # Relationship back to job
    job = relationship("ScrapingJob", back_populates="documents")