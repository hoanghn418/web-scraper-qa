# backend/app/api/endpoints/scraper.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ...database.database import get_db
from ...database.crud import crud_job
from ...models.schemas import ScrapingRequestSchema, ScrapingResultSchema
from ...services.scraper import WebScraper, ScrapingConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/")
async def scrape_url(
    request: ScrapingRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Scrape content from the provided URL.
    """
    try:
        # Create scraping job in database
        config = request.config.dict() if request.config else ScrapingConfig().__dict__
        job = crud_job.create(db, url=str(request.url), config=config)
        
        # Initialize scraper with config
        scraper_config = ScrapingConfig(**config)
        scraper = WebScraper(scraper_config)
        
        # Update job status to running
        crud_job.update_status(db, job_id=job.id, status="running")
        
        # Perform scraping
        result = scraper.scrape(str(request.url))
        
        # Update job with content and status
        status = "failed" if result.get('error') else "completed"
        crud_job.update_job(
            db, 
            job_id=job.id, 
            status=status,
            content=result
        )
        
        # Return response with job_id
        return {"job_id": job.id, **result}
    
    except Exception as e:
        logger.error(f"Error in scrape_url: {str(e)}")
        # Update job status to failed if exists
        if 'job' in locals():
            crud_job.update_status(db, job_id=job.id, status="failed")
        raise HTTPException(status_code=500, detail=str(e))