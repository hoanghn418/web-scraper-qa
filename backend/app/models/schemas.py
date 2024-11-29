# backend/app/models/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any

class ScrapingConfigSchema(BaseModel):
    max_pages: int = 100
    rate_limit: int = 1
    respect_robots_txt: bool = True
    scrape_multiple_pages: bool = True

class ScrapingRequestSchema(BaseModel):
    url: HttpUrl
    config: Optional[ScrapingConfigSchema] = None

class ContentSchema(BaseModel):
    title: str
    headings: List[Dict[str, Any]]  # More permissive validation
    paragraphs: List[str]
    code_blocks: List[str]

class PageSchema(BaseModel):
    url: str
    content: ContentSchema

class ScrapingResultSchema(BaseModel):
    base_url: str
    pages: List[PageSchema]
    error: Optional[str] = None

    class Config:
        from_attributes = True

class QAPairSchema(BaseModel):
    question: str
    answer: str
    confidence_score: float
    category: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentSchema(BaseModel):
    content: str
    format: str

    class Config:
        from_attributes = True