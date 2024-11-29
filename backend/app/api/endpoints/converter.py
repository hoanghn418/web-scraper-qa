# backend/app/api/endpoints/converter.py
from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...database.crud import crud_job, crud_document
from ...services.converter import DocumentConverter, DocumentManager
from typing import List
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/convert/{job_id}")
async def convert_job_content(
    job_id: int,
    formats: List[str] = Body(...),  # This ensures formats is properly validated as a list
    db: Session = Depends(get_db)
):
    try:
        # Get job from database
        job = crud_job.get_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Add debug logging
        logger.info(f"Converting job {job_id} to formats: {formats}")
        
        # Initialize converter
        converter = DocumentManager()
        
        # Process documents
        results = converter.process_scraped_data(job.content, formats)
        
        # Store in database
        for format_type, content in results.items():
            crud_document.create(db, job_id=job_id, content=content, format=format_type)
        
        return {"message": "Conversion completed", "formats": formats}
    except Exception as e:
        logger.error(f"Error converting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{job_id}/{format}")
async def download_document(
    job_id: int,
    format: str,
    db: Session = Depends(get_db)
):
    """
    Download converted document in specified format.
    """
    try:
        # Get document from database
        document = crud_document.get_by_job_and_format(db, job_id, format)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Prepare content for download
        if format == 'markdown':
            content = document.content.encode('utf-8')
            media_type = 'text/markdown'
            filename = f"document_{job_id}.md"
        else:  # PDF
            content = document.content
            media_type = 'application/pdf'
            filename = f"document_{job_id}.pdf"
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
