# Multi-API News Search System for Hackathon
# Quick implementation focusing on getting it working fast
import os
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import time
from dotenv import load_dotenv
load_dotenv()
class NewsSearcher:
    def __init__(self, news_api_key=None, google_api_key=None, google_search_engine_id=None):
        """
        Initialize with API keys. Add keys as you get them.
        """
        self.news_api_key = os.getenv('news_api_key', news_api_key)
        self.google_api_key = os.getenv('google_api_key', google_api_key)
        self.google_search_engine_id = os.getenv('google_search_engine_id', google_search_engine_id)
        self.timeout = 5
        self.max_results = 20  # Increase default
        
        # Simple cache to avoid duplicate API calls during demo
        self._cache = {}
    
    def search_news_api(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search using News API - usually the easiest to get started with
        """
        if not self.news_api_key:
            return []
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': self.news_api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': min(max_results, 20)  # API limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for article in data.get('articles', []):
                # Skip articles without title (common issue)
                if not article.get('title'):
                    continue
                    
                results.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'snippet': article.get('description', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'api_source': 'news_api'
                })
            
            return results
            
        except Exception as e:
            print(f"News API error: {e}")
            return []
    
    def search_google_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search using Google Custom Search API - excellent quality results
        Note: Google API limit is 10 results per request, but we can make multiple requests
        """
        if not self.google_api_key or not self.google_search_engine_id:
            return []
        
        all_results = []
        requests_needed = (max_results + 9) // 10  # Calculate how many requests we need
        
        for request_num in range(requests_needed):
            start_index = request_num * 10 + 1  # Google uses 1-based indexing
            current_request_limit = min(10, max_results - len(all_results))
            
            if current_request_limit <= 0:
                break
                
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_search_engine_id,
                'q': f"{query} news",  # Add 'news' to focus on news articles
                'num': current_request_limit,
                'start': start_index,
                'sort': 'date'  # Sort by date for recent news
            }
            
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:  # No more results available
                    break
                
                for item in items:
                    # Extract source from display URL
                    source = item.get('displayLink', 'Unknown')
                    if '.' in source:
                        source = source.split('.')[0].title()
                    
                    all_results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': source,
                        'published_at': '',  # Google Custom Search doesn't provide publish date
                        'api_source': 'google_search'
                    })
                
                # Add delay between requests to be nice to Google
                if request_num < requests_needed - 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Google Search API error on request {request_num + 1}: {e}")
                break  # Stop making more requests if one fails
        
        return all_results
    
    def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """
        Simple duplicate removal by URL - good enough for hackathon
        """
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def search(self, query: str, max_results: int = None) -> List[Dict]:
        """
        Main search function - tries multiple APIs and combines results
        """
        if max_results is None:
            max_results = self.max_results
        
        # Simple caching for demo purposes
        cache_key = f"{query}_{max_results}"
        if cache_key in self._cache:
            print("Using cached results...")
            return self._cache[cache_key]
        
        all_results = []
        
        # Try News API first (usually most reliable)
        print("Searching News API...")
        news_results = self.search_news_api(query, max_results // 2)  # Get half from News API
        all_results.extend(news_results)
        
        # Add small delay to be nice to APIs
        time.sleep(0.5)
        
        # Try Google Search if we have the key and need more results
        remaining_needed = max_results - len(all_results)
        if remaining_needed > 0 and self.google_api_key and self.google_search_engine_id:
            print("Searching Google Custom Search...")
            google_results = self.search_google_news(query, remaining_needed)
            all_results.extend(google_results)
        
        # Remove duplicates and limit results
        unique_results = self.remove_duplicates(all_results)[:max_results]
        
        # Cache for demo
        self._cache[cache_key] = unique_results
        
        return unique_results
    
    def get_available_apis(self) -> List[str]:
        """
        Check which APIs are configured
        """
        apis = []
        if self.news_api_key:
            apis.append("News API")
        if self.google_api_key and self.google_search_engine_id:
            apis.append("Google Custom Search")
        return apis


# Example usage and testing
def main():
    """
    Example usage - replace with your actual API keys
    """
    # ADD YOUR API KEYS HERE
    NEWS_API_KEY = os.getenv('news_api_key')# Get from newsapi.org
    GOOGLE_API_KEY = os.getenv('google_api_key')  # Get from Google Cloud Console
    GOOGLE_SEARCH_ENGINE_ID = os.getenv('google_search_engine_id') # Custom Search Engine ID
    
    # Initialize searcher
    searcher = NewsSearcher(
        news_api_key=NEWS_API_KEY if NEWS_API_KEY != "your_news_api_key_here" else None,
        google_api_key=GOOGLE_API_KEY if GOOGLE_API_KEY != "your_google_api_key_here" else None,
        google_search_engine_id=GOOGLE_SEARCH_ENGINE_ID if GOOGLE_SEARCH_ENGINE_ID != "your_search_engine_id_here" else None
    )
    
    # Check what APIs are available
    available_apis = searcher.get_available_apis()
    print(f"Available APIs: {available_apis}")
    
    if not available_apis:
        print("No API keys configured! Add your keys to test.")
        return
def get_info(query):
    NEWS_API_KEY = os.getenv('news_api_key')
    GOOGLE_API_KEY = os.getenv('google_api_key')
    GOOGLE_SEARCH_ENGINE_ID = os.getenv('google_search_engine_id')

    # Initialize searcher
    searcher = NewsSearcher(
        news_api_key=NEWS_API_KEY if NEWS_API_KEY != "your_news_api_key_here" else None,
        google_api_key=GOOGLE_API_KEY if GOOGLE_API_KEY != "your_google_api_key_here" else None,
        google_search_engine_id=GOOGLE_SEARCH_ENGINE_ID if GOOGLE_SEARCH_ENGINE_ID != "your_search_engine_id_here" else None
    )

    # Check what APIs are available
    available_apis = searcher.get_available_apis()
    print(f"Available APIs: {available_apis}")

    if not available_apis:
        print("No API keys configured! Add your keys to test.")
        return []

    # Get news results
    results = searcher.search(query, max_results=15)
    if not results:
        print("No news results found!")
        return []

    # Prepare url-metadata pairs for scraping
    url_data = []
    for r in results:
        url_data.append({
            'url': r['url'],
            'metadata': {
                'search_query': query,
                'source': r.get('source', ''),
                'api_source': r.get('api_source', ''),
                'relevance_score': 1.0  # Placeholder, can be improved
            }
        })

    # Scrape the URLs
    agent = WebScrapingAgent(delay=1.0)
    scraped_results = agent.scrape_multiple_urls(url_data)

    # Return as list of dicts
    return [asdict(res) for res in scraped_results] if scraped_results else []
    




import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedContent:
    """Data class to structure scraped content"""
    url: str
    title: str
    content: str
    author: Optional[str]
    publish_date: Optional[str]
    description: str
    keywords: List[str]
    images: List[str]
    links: List[str]
    source_domain: str
    word_count: int
    scrape_timestamp: str
    metadata: Dict[str, Any]
    content_hash: str

class WebScrapingAgent:
    """Advanced web scraping agent for news content analysis"""
    
    def __init__(self, delay=1.0, timeout=30, max_retries=3):
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
        
        # Common selectors for different content types
        self.content_selectors = [
            'article', '.article-content', '.post-content', 
            '.entry-content', '.content', '.story-body',
            '[data-testid="article-body"]', '.article-body',
            '.post-body', '.news-content', 'main'
        ]
        
        self.title_selectors = [
            'h1', '.headline', '.title', '.post-title',
            '.article-title', '[data-testid="headline"]'
        ]
        
        self.author_selectors = [
            '.author', '.byline', '[rel="author"]',
            '.article-author', '.post-author', '.writer'
        ]
        
        self.date_selectors = [
            'time', '.date', '.publish-date', '.timestamp',
            '.article-date', '.post-date', '[datetime]'
        ]

    def _create_session(self):
        """Create a robust requests session with retry strategy"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session

    def scrape_url(self, url: str, metadata: Dict = None) -> Optional[ScrapedContent]:
        """Scrape a single URL and return structured content"""
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Rate limiting
            time.sleep(self.delay)
            
            # Fetch the page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content
            scraped_data = ScrapedContent(
                url=url,
                title=self._extract_title(soup),
                content=self._extract_content(soup),
                author=self._extract_author(soup),
                publish_date=self._extract_date(soup),
                description=self._extract_description(soup),
                keywords=self._extract_keywords(soup),
                images=self._extract_images(soup, url),
                links=self._extract_links(soup, url),
                source_domain=urlparse(url).netloc,
                word_count=0,  # Will be calculated
                scrape_timestamp=datetime.now().isoformat(),
                metadata=metadata or {},
                content_hash=""  # Will be calculated
            )
            
            # Calculate word count and content hash
            scraped_data.word_count = len(scraped_data.content.split())
            scraped_data.content_hash = hashlib.md5(
                scraped_data.content.encode('utf-8')
            ).hexdigest()
            
            logger.info(f"Successfully scraped: {url}")
            return scraped_data
            
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from the page"""
        # Try meta title first
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        # Try title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Try various title selectors
        for selector in self.title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "No title found"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", 
                            "aside", ".advertisement", ".ad", ".sidebar"]):
            element.decompose()
        
        # Try various content selectors
        for selector in self.content_selectors:
            elements = soup.select(selector)
            if elements:
                content_parts = []
                for element in elements:
                    text = element.get_text(separator='\n', strip=True)
                    if len(text) > 100:  # Only consider substantial content
                        content_parts.append(text)
                
                if content_parts:
                    return '\n\n'.join(content_parts)
        
        # Fallback: extract from body
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return soup.get_text(separator='\n', strip=True)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author information"""
        # Try meta author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()
        
        # Try various author selectors
        for selector in self.author_selectors:
            element = soup.select_one(selector)
            if element:
                author_text = element.get_text().strip()
                # Clean up common author prefixes
                author_text = re.sub(r'^(by|author:|written by)\s*', '', author_text, flags=re.IGNORECASE)
                if author_text:
                    return author_text
        
        return None

    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date"""
        # Try meta date properties
        date_properties = ['article:published_time', 'article:modified_time', 'datePublished']
        for prop in date_properties:
            meta_date = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
            if meta_date and meta_date.get('content'):
                return meta_date['content'].strip()
        
        # Try time elements with datetime attribute
        time_elem = soup.find('time', datetime=True)
        if time_elem:
            return time_elem['datetime']
        
        # Try various date selectors
        for selector in self.date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text().strip()
                if date_text:
                    return date_text
        
        return None

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                   soup.find('meta', property='og:description')
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Fallback: first paragraph of content
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:300] + "..."
        
        return ""

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from the page"""
        keywords = []
        
        # Try meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        # Extract from meta tags
        tags = soup.find_all('meta', attrs={'property': 'article:tag'})
        for tag in tags:
            if tag.get('content'):
                keywords.append(tag['content'].strip())
        
        return list(set(keywords))  # Remove duplicates

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs"""
        images = []
        
        # Try featured image from meta
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.append(urljoin(base_url, og_image['content']))
        
        # Extract from img tags
        img_tags = soup.find_all('img', src=True)
        for img in img_tags:
            src = img['src']
            if src:
                full_url = urljoin(base_url, src)
                if full_url not in images:
                    images.append(full_url)
        
        return images[:10]  # Limit to first 10 images

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract internal and external links"""
        links = []
        
        link_tags = soup.find_all('a', href=True)
        for link in link_tags:
            href = link['href']
            if href:
                full_url = urljoin(base_url, href)
                if full_url not in links and full_url != base_url:
                    links.append(full_url)
        
        return links[:50]  # Limit to first 50 links

    def scrape_multiple_urls(self, url_metadata_pairs: List[Dict]) -> List[ScrapedContent]:
        """Scrape multiple URLs with their metadata"""
        results = []
        
        for item in url_metadata_pairs:
            url = item.get('url')
            metadata = item.get('metadata', {})
            
            if not url:
                logger.warning("Skipping item without URL")
                continue
            
            scraped_content = self.scrape_url(url, metadata)
            if scraped_content:
                results.append(scraped_content)
        
        logger.info(f"Successfully scraped {len(results)} out of {len(url_metadata_pairs)} URLs")
        return results

    def save_results(self, results: List[ScrapedContent], filename: str):
        """Save scraping results to JSON file"""
        data = [asdict(result) for result in results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filename}")

    def get_content_statistics(self, results: List[ScrapedContent]) -> Dict:
        """Generate statistics about scraped content"""
        if not results:
            return {}
        
        total_articles = len(results)
        total_words = sum(result.word_count for result in results)
        avg_words = total_words / total_articles if total_articles > 0 else 0
        
        domains = {}
        for result in results:
            domain = result.source_domain
            domains[domain] = domains.get(domain, 0) + 1
        
        return {
            'total_articles': total_articles,
            'total_words': total_words,
            'average_words_per_article': avg_words,
            'domains_scraped': domains,
            'unique_domains': len(domains)
        }

# Example usage
def test_wedscreaper():
    """Example usage of the WebScrapingAgent"""
    
    # Initialize the agent
    agent = WebScrapingAgent(delay=1.0)
    
    # Example URL data (replace with your actual data)
    url_data = [
        {
            'url': 'https://example-news-site.com/article1',
            'metadata': {
                'search_query': 'climate change',
                'source': 'search_engine_api',
                'relevance_score': 0.95
            }
        },
        {
            'url': 'https://another-news-site.com/article2',
            'metadata': {
                'search_query': 'climate change',
                'source': 'search_engine_api',
                'relevance_score': 0.87
            }
        }
    ]
    
    # Scrape the URLs
    results = agent.scrape_multiple_urls(url_data)
    
    # Save results
    if results:
        agent.save_results(results, 'scraped_news_data.json')
        
        # Print statistics
        stats = agent.get_content_statistics(results)
        print("Scraping Statistics:")
        print(json.dumps(stats, indent=2))
        
        # Print sample result
        if results:
            print("\nSample scraped content:")
            sample = results[0]
            print(f"Title: {sample.title}")
            print(f"Author: {sample.author}")
            print(f"Word Count: {sample.word_count}")
            print(f"Content Preview: {sample.content[:200]}...")
def main():
    result = get_info("air india plan crash")
    print(result)

if __name__ == "__main__":
    # Run main function for testing
    main()
    
    # Uncomment below for quick test without API keys
    # quick_test()