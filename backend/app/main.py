# backend/app/main.py
from fastapi import FastAPI
from app.database.init_db import init_db
from app.api.endpoints import scraper, converter, qa_generator, jobs

app = FastAPI(title="Web Scraper and Q&A Generator API")

@app.on_event("startup")
async def startup_event():
    init_db()

# Include routers
#app.include_router(scraper.router, prefix="/api/v1", tags=["scraper"])
app.include_router(scraper.router, prefix="/api/v1/scrape", tags=["scraper"])
app.include_router(converter.router, prefix="/api/v1/documents", tags=["converter"])
app.include_router(qa_generator.router, prefix="/api/v1/qa", tags=["qa-generator"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])  

@app.get("/")
async def root():
    return {"message": "Web Scraper and Q&A Generator API"}
