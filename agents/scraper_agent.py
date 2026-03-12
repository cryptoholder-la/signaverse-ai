"""
Web Scraper Agent for Sign Language Data Collection
Automated collection of sign language videos and metadata from various sources
"""

import asyncio
import aiohttp
import beautifulsoup4 as bs4
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import os
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Content scraped from web sources"""
    url: str
    title: str
    description: str
    video_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    content_hash: str = ""
    timestamp: float = 0.0


class ScraperAgent:
    """Web scraper for sign language content"""
    
    def __init__(self, 
                 max_concurrent_requests: int = 10,
                 request_delay: float = 1.0,
                 user_agent: str = "SignVerse-AI-Scraper/1.0"):
        self.max_concurrent_requests = max_concurrent_requests
        self.request_delay = request_delay
        self.user_agent = user_agent
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Scraped content storage
        self.scraped_content: List[ScrapedContent] = []
        self.visited_urls: set = set()
        self.failed_urls: List[str] = []
        
        # Rate limiting
        self.last_request_time = 0.0
        
        # Content filters
        self.content_filters = {
            'video_formats': ['.mp4', '.avi', '.mov', '.webm'],
            'image_formats': ['.jpg', '.jpeg', '.png', '.gif'],
            'text_keywords': ['sign language', 'asl', 'bsl', 'signing'],
            'min_duration': 2.0,  # seconds
            'max_duration': 300.0  # seconds
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=30)
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_sign_videos(self, source: str) -> List[ScrapedContent]:
        """Scrape sign language videos from various sources"""
        if not self.session:
            raise RuntimeError("ScraperAgent must be used as async context manager")
        
        # Handle different source types
        if source.startswith('http'):
            # Single URL
            return await self._scrape_url(source)
        elif source.endswith('.txt'):
            # List of URLs from file
            urls = self._load_urls_from_file(source)
            return await self._scrape_urls(urls)
        else:
            # Predefined source
            return await self._scrape_predefined_source(source)
    
    async def _scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content from a single URL"""
        if url in self.visited_urls:
            return None
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
        
        try:
            async with self.semaphore:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return await self._parse_content(url, content, response.headers)
                    else:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        self.failed_urls.append(url)
                        return None
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.failed_urls.append(url)
            return None
        finally:
            self.visited_urls.add(url)
    
    async def _scrape_urls(self, urls: List[str]) -> List[ScrapedContent]:
        """Scrape multiple URLs concurrently"""
        tasks = [self._scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        scraped_content = []
        for result in results:
            if isinstance(result, ScrapedContent):
                scraped_content.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping error: {result}")
        
        self.scraped_content.extend(scraped_content)
        
        logger.info(f"Successfully scraped {len(scraped_content)} out of {len(urls)} URLs")
        return scraped_content
    
    async def _scrape_predefined_source(self, source_name: str) -> List[ScrapedContent]:
        """Scrape from predefined sources"""
        source_configs = {
            'youtube': {
                'base_url': 'https://www.youtube.com/results',
                'search_params': {'search_query': 'sign language lessons'},
                'requires_api': True
            },
            'lifeprint': {
                'base_url': 'https://www.lifeprint.com',
                'start_paths': ['/asl/', '/dictionary/'],
                'requires_api': False
            },
            'handspeak': {
                'base_url': 'https://www.handspeak.com',
                'start_paths': ['/word/', '/alphabet/'],
                'requires_api': False
            },
            'signlanguageforum': {
                'base_url': 'https://www.signlanguageforum.com',
                'start_paths': ['/resources/', '/videos/'],
                'requires_api': False
            }
        }
        
        if source_name not in source_configs:
            logger.error(f"Unknown source: {source_name}")
            return []
        
        config = source_configs[source_name]
        
        if config['requires_api']:
            return await self._scrape_with_api(source_name, config)
        else:
            return await self._scrape_website(config)
    
    async def _scrape_with_api(self, source_name: str, config: Dict[str, Any]) -> List[ScrapedContent]:
        """Scrape using API (e.g., YouTube)"""
        if source_name == 'youtube':
            return await self._scrape_youtube(config)
        else:
            logger.warning(f"API scraping not implemented for {source_name}")
            return []
    
    async def _scrape_youtube(self, config: Dict[str, Any]) -> List[ScrapedContent]:
        """Scrape YouTube videos (requires API key)"""
        # This would require YouTube Data API key
        # For now, return mock implementation
        logger.info("YouTube scraping requires API key - returning mock data")
        
        mock_content = [
            ScrapedContent(
                url="https://youtube.com/watch?v=mock1",
                title="ASL Alphabet",
                description="Learn the ASL alphabet",
                video_url="https://youtube.com/watch?v=mock1",
                metadata={"source": "youtube", "duration": 120},
                content_hash="mock1_hash",
                timestamp=time.time()
            )
        ]
        
        return mock_content
    
    async def _scrape_website(self, config: Dict[str, Any]) -> List[ScrapedContent]:
        """Scrape website content"""
        base_url = config['base_url']
        start_paths = config.get('start_paths', ['/'])
        
        all_urls = []
        
        # Discover URLs from start paths
        for path in start_paths:
            start_url = urljoin(base_url, path)
            discovered_urls = await self._discover_links(start_url, max_depth=2)
            all_urls.extend(discovered_urls)
        
        # Scrape discovered URLs
        return await self._scrape_urls(all_urls)
    
    async def _discover_links(self, start_url: str, max_depth: int = 2) -> List[str]:
        """Discover links from starting URL"""
        discovered_urls = []
        urls_to_visit = [(start_url, 0)]
        visited = set()
        
        while urls_to_visit:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            
            try:
                async with self.semaphore:
                    async with self.session.get(current_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            soup = bs4.BeautifulSoup(content, 'html.parser')
                            
                            # Extract links
                            links = soup.find_all('a', href=True)
                            for link in links:
                                href = link.get('href')
                                if href:
                                    absolute_url = urljoin(current_url, href)
                                    
                                    # Filter relevant links
                                    if self._is_relevant_link(absolute_url):
                                        discovered_urls.append(absolute_url)
                                        
                                        # Add to visit queue if within depth limit
                                        if depth < max_depth:
                                            urls_to_visit.append((absolute_url, depth + 1))
            
            except Exception as e:
                logger.error(f"Error discovering links from {current_url}: {e}")
        
        # Remove duplicates and visited URLs
        unique_urls = list(set(discovered_urls) - visited)
        return unique_urls
    
    def _is_relevant_link(self, url: str) -> bool:
        """Check if URL is relevant for sign language content"""
        # Domain-based filtering
        relevant_domains = [
            'youtube.com', 'vimeo.com', 'dailymotion.com',
            'signlanguageforum.com', 'lifeprint.com', 'handspeak.com'
        ]
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain is relevant
        if any(relevant in domain for relevant in relevant_domains):
            return True
        
        # Check path for relevant keywords
        path = parsed.path.lower()
        relevant_keywords = ['sign', 'asl', 'bsl', 'deaf', 'language']
        if any(keyword in path for keyword in relevant_keywords):
            return True
        
        return False
    
    async def _parse_content(self, 
                           url: str, 
                           content: str, 
                           headers: Dict[str, str]) -> Optional[ScrapedContent]:
        """Parse HTML content and extract relevant information"""
        try:
            soup = bs4.BeautifulSoup(content, 'html.parser')
            
            # Extract basic metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            
            # Extract video URLs
            video_urls = self._extract_video_urls(soup, url)
            
            # Extract additional metadata
            metadata = self._extract_metadata(soup, headers)
            
            # Filter content
            if not self._passes_filters(title, description, metadata):
                logger.debug(f"Content filtered out: {url}")
                return None
            
            # Create content object
            scraped = ScrapedContent(
                url=url,
                title=title,
                description=description,
                video_url=video_urls[0] if video_urls else None,
                metadata=metadata,
                content_hash=self._generate_content_hash(url, title, description),
                timestamp=time.time()
            )
            
            return scraped
        
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {e}")
            return None
    
    def _extract_title(self, soup: bs4.BeautifulSoup) -> str:
        """Extract page title"""
        title_tags = [
            soup.find('title'),
            soup.find('h1'),
            soup.find('meta', property='og:title'),
            soup.find('meta', attrs={'name': 'title'})
        ]
        
        for tag in title_tags:
            if tag:
                if tag.name == 'meta':
                    return tag.get('content', '').strip()
                else:
                    return tag.get_text().strip()
        
        return "Unknown Title"
    
    def _extract_description(self, soup: bs4.BeautifulSoup) -> str:
        """Extract page description"""
        desc_selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            'meta[name="twitter:description"]',
            '.description',
            '.summary'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return ""
    
    def _extract_video_urls(self, soup: bs4.BeautifulSoup, base_url: str) -> List[str]:
        """Extract video URLs from page"""
        video_urls = []
        
        # Video tags
        video_tags = soup.find_all(['video', 'source'])
        for tag in video_tags:
            src = tag.get('src')
            if src:
                video_url = urljoin(base_url, src)
                if self._is_video_url(video_url):
                    video_urls.append(video_url)
        
        # Embed tags and iframes
        embed_tags = soup.find_all(['embed', 'iframe'])
        for tag in embed_tags:
            src = tag.get('src')
            if src:
                video_url = urljoin(base_url, src)
                if self._is_video_url(video_url):
                    video_urls.append(video_url)
        
        # Links to video files
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href:
                video_url = urljoin(base_url, href)
                if self._is_video_url(video_url):
                    video_urls.append(video_url)
        
        return list(set(video_urls))  # Remove duplicates
    
    def _extract_metadata(self, soup: bs4.BeautifulSoup, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from page"""
        metadata = {}
        
        # Basic meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[name] = content
        
        # Response headers
        metadata['response_headers'] = dict(headers)
        
        # Language detection
        html_tag = soup.find('html')
        if html_tag:
            metadata['page_language'] = html_tag.get('lang', 'unknown')
        
        # Structured data
        structured_data = self._extract_structured_data(soup)
        if structured_data:
            metadata['structured_data'] = structured_data
        
        return metadata
    
    def _extract_structured_data(self, soup: bs4.BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract JSON-LD structured data"""
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _is_video_url(self, url: str) -> bool:
        """Check if URL points to a video file"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check file extension
        for ext in self.content_filters['video_formats']:
            if path.endswith(ext):
                return True
        
        # Check common video hosting domains
        video_domains = ['youtube.com', 'vimeo.com', 'dailymotion.com']
        if any(domain in parsed.netloc.lower() for domain in video_domains):
            return True
        
        return False
    
    def _passes_filters(self, 
                     title: str, 
                     description: str, 
                     metadata: Dict[str, Any]) -> bool:
        """Check if content passes filtering criteria"""
        # Text content filter
        text_content = f"{title} {description}".lower()
        if not any(keyword in text_content for keyword in self.content_filters['text_keywords']):
            return False
        
        # Duration filter (if available)
        duration = metadata.get('duration')
        if duration:
            if duration < self.content_filters['min_duration'] or \
               duration > self.content_filters['max_duration']:
                return False
        
        # Quality filter (basic)
        if len(title) < 5 or len(description) < 10:
            return False
        
        return True
    
    def _generate_content_hash(self, url: str, title: str, description: str) -> str:
        """Generate unique hash for content"""
        content_str = f"{url}{title}{description}"
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _load_urls_from_file(self, filepath: str) -> List[str]:
        """Load URLs from text file"""
        urls = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and url.startswith('http'):
                        urls.append(url)
        except Exception as e:
            logger.error(f"Error loading URLs from {filepath}: {e}")
        
        return urls
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get statistics about scraping session"""
        return {
            'total_scraped': len(self.scraped_content),
            'unique_domains': len(set(urlparse(content.url).netloc for content in self.scraped_content)),
            'failed_urls': len(self.failed_urls),
            'visited_urls': len(self.visited_urls),
            'success_rate': len(self.scraped_content) / max(len(self.visited_urls), 1),
            'content_types': self._analyze_content_types()
        }
    
    def _analyze_content_types(self) -> Dict[str, int]:
        """Analyze types of scraped content"""
        content_types = {
            'with_video': 0,
            'with_metadata': 0,
            'with_structured_data': 0
        }
        
        for content in self.scraped_content:
            if content.video_url:
                content_types['with_video'] += 1
            if content.metadata and len(content.metadata) > 2:
                content_types['with_metadata'] += 1
            if content.metadata and 'structured_data' in content.metadata:
                content_types['with_structured_data'] += 1
        
        return content_types
    
    def export_scraped_data(self, filepath: str, format: str = 'json'):
        """Export scraped data to file"""
        data = [content.__dict__ for content in self.scraped_content]
        
        if format.lower() == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            import csv
            if data:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        logger.info(f"Exported {len(data)} items to {filepath}")
    
    def clear_data(self):
        """Clear all scraped data"""
        self.scraped_content.clear()
        self.visited_urls.clear()
        self.failed_urls.clear()
        logger.info("Scraped data cleared")


# Example usage
async def main():
    """Example usage of scraper agent"""
    async with ScraperAgent() as scraper:
        # Scrape from predefined source
        scraped_content = await scraper.scrape_sign_videos('lifeprint')
        
        # Print statistics
        stats = scraper.get_scraping_statistics()
        print(f"Scraping Statistics: {json.dumps(stats, indent=2)}")
        
        # Export data
        scraper.export_scraped_data("scraped_sign_language_data.json")


if __name__ == "__main__":
    asyncio.run(main())