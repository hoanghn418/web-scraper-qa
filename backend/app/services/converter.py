# backend/app/services/converter.py
import markdown2
from typing import Dict, List, Optional
import tempfile
from pathlib import Path
import logging
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversionConfig:
    """Configuration for document conversion."""
    include_code_blocks: bool = True
    include_headings: bool = True
    include_title: bool = True

class DocumentConverter:
    """Service for converting scraped content to different formats."""
    
    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()
    
    def _create_markdown_content(self, page_data: Dict) -> str:
        """Convert page content to markdown format."""
        markdown_content = []
        
        # Add title
        if self.config.include_title and page_data['content']['title']:
            markdown_content.append(f"# {page_data['content']['title']}\n")
        
        # Add URL reference
        markdown_content.append(f"*Source: {page_data['url']}*\n")
        
        # Add headings and their content
        if self.config.include_headings:
            for heading in page_data['content']['headings']:
                level = '#' * heading['level']
                markdown_content.append(f"\n{level} {heading['text']}\n")
        
        # Add paragraphs
        for paragraph in page_data['content']['paragraphs']:
            markdown_content.append(f"\n{paragraph}\n")
        
        # Add code blocks
        if self.config.include_code_blocks:
            for code_block in page_data['content']['code_blocks']:
                markdown_content.append(f"\n```\n{code_block}\n```\n")
        
        return '\n'.join(markdown_content)
    
    def create_markdown(self, scraped_data: Dict) -> str:
        """
        Convert scraped data to markdown format.
        Returns markdown string.
        """
        try:
            all_markdown = []
            
            for page in scraped_data['pages']:
                markdown_content = self._create_markdown_content(page)
                all_markdown.append(markdown_content)
                all_markdown.append("\n---\n")  # Page separator
            
            return '\n'.join(all_markdown)
            
        except Exception as e:
            logger.error(f"Error converting to markdown: {e}")
            raise

class DocumentManager:
    """Manager class for handling document conversions and storage."""
    
    def __init__(self, converter: Optional[DocumentConverter] = None):
        self.converter = converter or DocumentConverter()
    
    def process_scraped_data(
        self, 
        scraped_data: Dict,
        formats: List[str] = ['markdown']
    ) -> Dict[str, bytes]:
        """
        Process scraped data into requested formats.
        Returns dictionary with format as key and content as value.
        """
        results = {}
        
        try:
            if 'markdown' in formats:
                markdown_content = self.converter.create_markdown(scraped_data)
                results['markdown'] = markdown_content.encode('utf-8')
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            raise