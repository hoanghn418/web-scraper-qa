# backend/app/api/endpoints/qa_generator.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...database.crud import crud_job, crud_qa
from ...services.qa_generator import QAGenerator, QAGeneratorConfig
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{job_id}")
async def get_qa_pairs(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Q&A pairs for a specific job.
    """
    try:
        # Get Q&A pairs from database
        qa_pairs = crud_qa.get_by_job_id(db, job_id)
        if not qa_pairs:
            raise HTTPException(status_code=404, detail="No Q&A pairs found")
        
        return qa_pairs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/{job_id}")
async def generate_qa_pairs(
    job_id: int,
    num_pairs: Optional[int] = 10,
    min_confidence: Optional[float] = 0.7,
    db: Session = Depends(get_db)
):
    try:
        # Get job from database
        job = crud_job.get_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify content exists
        if not job.content:
            raise HTTPException(status_code=400, detail="No content found for this job")
        
        logger.info(f"Generating QA pairs for job {job_id}")
        
        # Generate Q&A pairs
        generator = QAGenerator(
            QAGeneratorConfig(
                num_questions_per_chunk=num_pairs,
                minimum_confidence_score=min_confidence
            )
        )
        
        qa_pairs = await generator.generate_qa_pairs(job.content)
        
        if not qa_pairs:
            logger.warning(f"No QA pairs generated for job {job_id}")
            return {"message": "No Q&A pairs could be generated", "qa_pairs": []}
        
        # Store in database
        crud_qa.create_many(db, job_id=job_id, qa_pairs=qa_pairs)
        
        return {
            "message": "Q&A generation completed",
            "qa_pairs": qa_pairs
        }
        
    except Exception as e:
        logger.error(f"Error generating QA pairs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{job_id}")
async def export_qa_pairs(
    job_id: int,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Export Q&A pairs in specified format (json or csv).
    """
    try:
        # Get Q&A pairs from database
        qa_pairs = crud_qa.get_by_job_id(db, job_id)
        if not qa_pairs:
            raise HTTPException(status_code=404, detail="No Q&A pairs found")
        
        if format.lower() == "json":
            return {
                "qa_pairs": [
                    {
                        "question": qa.question,
                        "answer": qa.answer,
                        "confidence_score": qa.confidence_score,
                        "category": qa.category
                    }
                    for qa in qa_pairs
                ]
            }
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["question", "answer", "confidence_score", "category"])
            
            for qa in qa_pairs:
                writer.writerow([
                    qa.question,
                    qa.answer,
                    qa.confidence_score,
                    qa.category
                ])
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=qa_pairs_{job_id}.csv"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
