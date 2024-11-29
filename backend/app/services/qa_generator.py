# backend/app/services/qa_generator.py
from openai import AsyncOpenAI
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import json
import tiktoken
import numpy as np

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QAGeneratorConfig:
    """Configuration for Q&A generation."""
    model: str = "gpt-4o"  # Changed to more reliable model
    max_tokens: int = 4000
    temperature: float = 0.7
    chunk_size: int = 2000
    num_questions_per_chunk: int = 5
    minimum_confidence_score: float = 0.7

class QAGenerator:
    """Service for generating Q&A pairs using OpenAI."""
    
    def __init__(self, config: Optional[QAGeneratorConfig] = None):
        self.config = config or QAGeneratorConfig()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.encoding = tiktoken.encoding_for_model(self.config.model)
    
    def _chunk_content(self, text: str) -> List[str]:
        """Split content into chunks based on token limit."""
        if not text:
            return []
            
        tokens = self.encoding.encode(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for token in tokens:
            if current_length + 1 <= self.config.chunk_size:
                current_chunk.append(token)
                current_length += 1
            else:
                chunks.append(self.encoding.decode(current_chunk))
                current_chunk = [token]
                current_length = 1
        
        if current_chunk:
            chunks.append(self.encoding.decode(current_chunk))
        
        return chunks

    def _generate_qa_prompt(self, content: str) -> str:
        """Generate prompt for Q&A generation."""
        return (
            f"Based on the following content, create {self.config.num_questions_per_chunk} question-answer pairs. "
            f"Return only a pure JSON object without any markdown formatting or code blocks, using this exact structure:\n"
            f'{{"qa_pairs": [\n'
            f'    {{"question": "<question text>",\n'
            f'     "answer": "<answer text>",\n'
            f'     "confidence_score": 0.95,\n'
            f'     "category": "<category>"}}\n'
            f"]}}\n\n"
            f"Content:\n{content}"
        )

    def _clean_json_response(self, content: str) -> str:
        """Clean the API response to ensure valid JSON."""
        # Remove markdown code blocks if present
        lines = content.split('\n')
        if any(line.strip().startswith('```') for line in lines):
            # Remove the first and last lines if they contain ```
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            if lines[-1].strip().startswith('```'):
                lines = lines[:-1]
            # Remove any remaining ``` lines
            lines = [line for line in lines if not line.strip().startswith('```')]
        
        # Join lines back together
        content = '\n'.join(lines)
        
        # Remove any "json" language identifier
        if content.strip().startswith('json'):
            content = content[4:].strip()
        
        return content.strip()

    async def _generate_qa_for_chunk(self, chunk: str) -> List[Dict]:
        """Generate Q&A pairs for a single chunk of content."""
        try:
            logger.info(f"Generating Q&A pairs for chunk of length {len(chunk)}")
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at creating question-answer pairs. Always respond with a pure JSON object, without any markdown formatting or code blocks."
                    },
                    {"role": "user", "content": self._generate_qa_prompt(chunk)}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Get and clean the content
            content = response.choices[0].message.content
            logger.info(f"Raw API response: {content}")
            
            cleaned_content = self._clean_json_response(content)
            logger.info(f"Cleaned content: {cleaned_content}")
            
            try:
                qa_data = json.loads(cleaned_content)
                if not isinstance(qa_data, dict) or 'qa_pairs' not in qa_data:
                    logger.warning(f"Invalid response structure: {qa_data}")
                    return []
                
                # Filter out low confidence Q&As and validate structure
                qa_pairs = [
                    qa for qa in qa_data['qa_pairs']
                    if isinstance(qa, dict) and 
                    all(key in qa for key in ['question', 'answer', 'confidence_score', 'category']) and
                    qa['confidence_score'] >= self.config.minimum_confidence_score and
                    QAValidator.validate_qa_pair(qa)
                ]
                
                return qa_pairs
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}\nCleaned Content: {cleaned_content}")
                return []
            
        except Exception as e:
            logger.error(f"Error in _generate_qa_for_chunk: {str(e)}")
            return []

    def _extract_text_from_page(self, page: Dict) -> str:
        """Extract relevant text content from a page."""
        try:
            content = []
            
            if isinstance(page, dict) and 'content' in page:
                page_content = page['content']
                
                # Extract title
                if isinstance(page_content.get('title'), str):
                    content.append(page_content['title'])
                
                # Extract headings
                if isinstance(page_content.get('headings'), list):
                    for heading in page_content['headings']:
                        if isinstance(heading, dict) and 'text' in heading:
                            content.append(heading['text'])
                
                # Extract paragraphs
                if isinstance(page_content.get('paragraphs'), list):
                    content.extend([p for p in page_content['paragraphs'] if isinstance(p, str)])
            
            return "\n\n".join(content)
            
        except Exception as e:
            logger.error(f"Error extracting text from page: {e}")
            return ""

    async def generate_qa_pairs(self, scraped_data: Dict) -> List[Dict]:
        """Generate Q&A pairs from scraped content."""
        all_qa_pairs = []
        
        try:
            if not isinstance(scraped_data, dict) or 'pages' not in scraped_data:
                logger.error(f"Invalid scraped_data format: {scraped_data}")
                return []
            
            for page in scraped_data['pages']:
                try:
                    # Extract text content
                    text_content = self._extract_text_from_page(page)
                    if not text_content.strip():
                        continue
                    
                    # Split into chunks
                    chunks = self._chunk_content(text_content)
                    
                    # Generate Q&A pairs for each chunk
                    for chunk in chunks:
                        try:
                            qa_pairs = await self._generate_qa_for_chunk(chunk)
                            if qa_pairs:  # Only add if we got valid pairs
                                # Add source URL to each Q&A pair
                                for qa_pair in qa_pairs:
                                    qa_pair['source_url'] = page.get('url', '')
                                all_qa_pairs.extend(qa_pairs)
                        except Exception as chunk_error:
                            logger.error(f"Error processing chunk: {chunk_error}")
                            continue  # Skip this chunk and continue with next
                
                except Exception as page_error:
                    logger.error(f"Error processing page: {page_error}")
                    continue  # Skip this page and continue with next
            
            # Remove duplicate questions
            seen_questions = set()
            unique_qa_pairs = []
            
            for qa_pair in all_qa_pairs:
                if isinstance(qa_pair, dict) and 'question' in qa_pair:
                    question = qa_pair['question'].lower()
                    if question not in seen_questions:
                        seen_questions.add(question)
                        unique_qa_pairs.append(qa_pair)
            
            return unique_qa_pairs
            
        except Exception as e:
            logger.error(f"Error in generate_qa_pairs: {e}")
            return []

class QAValidator:
    """Validator for generated Q&A pairs."""
    
    @staticmethod
    def validate_qa_pair(qa_pair: Dict) -> bool:
        """
        Validate a single Q&A pair.
        Returns True if valid, False otherwise.
        """
        try:
            # Check required fields
            required_fields = ['question', 'answer', 'confidence_score']
            if not all(field in qa_pair for field in required_fields):
                return False
            
            # Validate question length
            if len(qa_pair['question'].split()) < 3:
                return False
            
            # Validate answer length
            if len(qa_pair['answer'].split()) < 5:
                return False
            
            # Validate confidence score
            if not (0 <= qa_pair['confidence_score'] <= 1):
                return False
            
            return True
            
        except Exception:
            return False