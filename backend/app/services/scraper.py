# backend/app/services/scraper.py
import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import validators
from ratelimit import limits, sleep_and_retry
import logging
from dataclasses import dataclass
import robotexclusionrulesparser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Configuration for web scraping."""
    max_pages: int = 100
    rate_limit: int = 1  # requests per second
    respect_robots_txt: bool = True
    scrape_multiple_pages: bool = True

class RobotsTxtChecker:
    """Handle robots.txt parsing and checking."""
    
    def __init__(self):
        self.parser = robotexclusionrulesparser.RobotExclusionRulesParser()
        self.cache = {}
    
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            domain = urlparse(url).netloc
            if domain not in self.cache:
                robots_url = urljoin(f"https://{domain}", "/robots.txt")
                response = requests.get(robots_url, timeout=5)
                self.parser.parse(response.text)
                self.cache[domain] = self.parser
            
            return self.cache[domain].is_allowed(user_agent, url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True

class WebScraper:
    """Service for scraping web content."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.robots_checker = RobotsTxtChecker()
        self.visited_urls = set()
    
    @sleep_and_retry
    @limits(calls=1, period=1)  # Rate limit: 1 request per second
    def _fetch_url(self, url: str) -> Optional[requests.Response]:
        """Fetch URL content with rate limiting."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        return validators.url(url) is True

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from the page that belong to the same domain."""
        base_domain = urlparse(base_url).netloc
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            if (urlparse(full_url).netloc == base_domain and 
                full_url not in self.visited_urls and
                not full_url.endswith(('.pdf', '.zip', '.png', '.jpg'))):
                links.append(full_url)
        
        return links

    def _extract_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract relevant content from the page."""
        content = {
            'title': '',
            'headings': [],
            'paragraphs': [],
            'code_blocks': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            content['title'] = title_tag.text.strip()
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            content['headings'].append({
                'level': int(heading.name[1]),
                'text': heading.text.strip()
            })
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.text.strip()
            if text:
                content['paragraphs'].append(text)
        
        # Extract code blocks
        for code in soup.find_all('code'):
            text = code.text.strip()
            if text:
                content['code_blocks'].append(text)
        
        return content

    def scrape(self, url: str) -> Dict:
        """
        Scrape content from the provided URL.
        Returns a dictionary containing scraped content and metadata.
        """
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        if self.config.respect_robots_txt and not self.robots_checker.can_fetch(url):
            raise PermissionError(f"robots.txt disallows scraping: {url}")
        
        results = {
            'base_url': url,
            'pages': [],
            'error': None
        }
        
        try:
            # Scrape main page
            main_response = self._fetch_url(url)
            if not main_response:
                raise Exception(f"Failed to fetch main URL: {url}")
            
            main_soup = BeautifulSoup(main_response.text, 'html.parser')
            self.visited_urls.add(url)
            results['pages'].append({
                'url': url,
                'content': self._extract_content(main_soup)
            })
            
            # Scrape additional pages if configured
            if self.config.scrape_multiple_pages:
                links_to_scrape = self._extract_links(main_soup, url)
                links_to_scrape = links_to_scrape[:self.config.max_pages - 1]
                
                for link in links_to_scrape:
                    if len(self.visited_urls) >= self.config.max_pages:
                        break
                    
                    if link not in self.visited_urls:
                        logger.info(f"Scraping: {link}")
                        response = self._fetch_url(link)
                        
                        if response:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            self.visited_urls.add(link)
                            results['pages'].append({
                                'url': link,
                                'content': self._extract_content(soup)
                            })
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            results['error'] = str(e)
        
        return results

# Example usage
if __name__ == "__main__":
    config = ScrapingConfig(
        max_pages=5,
        rate_limit=1,
        respect_robots_txt=True,
        scrape_multiple_pages=True
    )
    
    scraper = WebScraper(config)
    result = scraper.scrape("https://fastapi.tiangolo.com/")
    print(f"Scraped {len(result['pages'])} pages")
