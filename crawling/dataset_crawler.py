"""
Automatic Sign-Language Dataset Crawler
Web crawler for discovering and collecting sign language datasets
"""

import asyncio
import aiohttp
import json
import time
import hashlib
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Types of data sources"""
    ACADEMIC_REPOSITORIES = "academic_repositories"
    GOVERNMENT_DATASETS = "government_datasets"
    COMMUNITY_PLATFORMS = "community_platforms"
    RESEARCH_INSTITUTIONS = "research_institutions"
    OPEN_DATA_PORTALS = "open_data_portals"
    VIDEO_PLATFORMS = "video_platforms"
    SOCIAL_MEDIA = "social_media"


class CrawlStatus(Enum):
    """Crawling status"""
    PENDING = "pending"
    CRAWLING = "crawling"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class DatasetFormat(Enum):
    """Dataset formats"""
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    VIDEO_MP4 = "video/mp4"
    VIDEO_AVI = "video/avi"
    VIDEO_MOV = "video/mov"
    COMPRESSED_ZIP = "application/zip"
    COMPRESSED_TAR = "application/x-tar"
    HDF5 = "application/hdf5"
    PARQUET = "application/parquet"


@dataclass
class CrawlTarget:
    """Target for crawling"""
    def __init__(self, target_id: str, name: str, base_url: str,
                 source_type: DataSource, crawl_patterns: List[str],
                 headers: Dict[str, str] = None, rate_limit: int = 1,
                 authentication: Dict[str, Any] = None):
        self.target_id = target_id
        self.name = name
        self.base_url = base_url
        self.source_type = source_type
        self.crawl_patterns = crawl_patterns
        self.headers = headers or {}
        self.rate_limit = rate_limit  # requests per second
        self.authentication = authentication or {}
        self.last_crawl_time = 0.0
        self.total_datasets_found = 0
        self.crawl_status = CrawlStatus.PENDING
        self.error_count = 0
        self.success_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DatasetInfo:
    """Information about discovered dataset"""
    def __init__(self, dataset_id: str, title: str, description: str,
                 source_url: str, download_urls: List[str],
                 file_formats: List[DatasetFormat], file_sizes: List[int],
                 license_info: str, sign_language: str,
                 num_samples: int = None, metadata: Dict[str, Any] = None,
                 discovered_at: float = None, quality_score: float = 0.0):
        self.dataset_id = dataset_id
        self.title = title
        self.description = description
        self.source_url = source_url
        self.download_urls = download_urls
        self.file_formats = file_formats
        self.file_sizes = file_sizes
        self.license_info = license_info
        self.sign_language = sign_language
        self.num_samples = num_samples
        self.metadata = metadata or {}
        self.discovered_at = discovered_at or time.time()
        self.quality_score = quality_score
        self.validation_status = "pending"
        self.processing_status = "discovered"
        self.tags: List[str] = []
        self.authors: List[str] = []
        self.publication_date: Optional[float] = None
    
    def add_tag(self, tag: str):
        """Add a tag to the dataset"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def add_author(self, author: str):
        """Add an author to the dataset"""
        if author not in self.authors:
            self.authors.append(author)
    
    def calculate_quality_score(self):
        """Calculate quality score based on metadata"""
        score = 0.0
        
        # Base score for having metadata
        if self.title:
            score += 10
        if self.description:
            score += 10
        if self.license_info:
            score += 15
        if self.num_samples:
            score += min(20, self.num_samples / 1000)  # Up to 20 points
        
        # Format diversity bonus
        score += min(15, len(self.file_formats) * 3)
        
        # File size bonus (prefer substantial datasets)
        if self.file_sizes:
            total_size = sum(self.file_sizes)
            if total_size > 100 * 1024 * 1024:  # > 100MB
                score += 10
            elif total_size > 1000 * 1024 * 1024:  # > 1GB
                score += 20
        
        # Source type bonus
        score += 5  # Base bonus for being discovered
        
        self.quality_score = min(100, score)
        return self.quality_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DatasetCrawler:
    """Automatic dataset crawler for sign language datasets"""
    
    def __init__(self, max_concurrent_crawls: int = 10):
        self.max_concurrent_crawls = max_concurrent_crawls
        
        # Crawling state
        self.targets: Dict[str, CrawlTarget] = {}
        self.discovered_datasets: Dict[str, DatasetInfo] = {}
        self.crawl_queue: asyncio.Queue = asyncio.Queue()
        self.active_crawls: Set[str] = set()
        
        # Configuration
        self.config = {
            "user_agent": "Signaverse-Dataset-Crawler/1.0",
            "request_timeout": 30,
            "max_retries": 3,
            "retry_delay": 5,
            "max_file_size": 5 * 1024 * 1024 * 1024,  # 5GB
            "min_file_size": 1024 * 1024,  # 1MB
            "allowed_domains": [],  # Empty means all domains allowed
            "blocked_domains": [],
            "download_samples": True,
            "max_sample_size": 10 * 1024 * 1024  # 10MB
        }
        
        # Performance metrics
        self.metrics = {
            "targets_configured": 0,
            "datasets_discovered": 0,
            "total_bytes_crawled": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "average_crawl_time": 0.0,
            "crawl_rate": 0.0  # datasets per hour
        }
        
        # HTTP session
        self.session = None
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.on_dataset_discovered = None
        self.on_crawl_completed = None
        self.on_crawl_failed = None
    
    async def start(self) -> bool:
        """Start the crawler service"""
        try:
            self.is_running = True
            
            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config["request_timeout"])
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self.config["user_agent"]}
            )
            
            # Load default targets
            await self._load_default_targets()
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._crawl_scheduler()),
                asyncio.create_task(self._queue_processor()),
                asyncio.create_task(self._metrics_loop()),
                asyncio.create_task(self._cleanup_loop())
            ]
            
            logger.info("Dataset crawler started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dataset crawler: {e}")
            return False
    
    async def stop(self):
        """Stop the crawler service"""
        self.is_running = False
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Dataset crawler stopped")
    
    async def _load_default_targets(self):
        """Load default crawl targets"""
        default_targets = [
            # Academic repositories
            CrawlTarget(
                target_id="kaggle_sign_language",
                name="Kaggle Sign Language Datasets",
                base_url="https://www.kaggle.com/datasets",
                source_type=DataSource.ACADEMIC_REPOSITORIES,
                crawl_patterns=[
                    r"/datasets/[^/]+/sign[-\s]?language",
                    r"/datasets/[^/]+/asl",
                    r"/datasets/[^/]+/bsl"
                ]
            ),
            CrawlTarget(
                target_id="huggingface_sign_language",
                name="Hugging Face Sign Language Datasets",
                base_url="https://huggingface.co/datasets",
                source_type=DataSource.ACADEMIC_REPOSITORIES,
                crawl_patterns=[
                    r"/datasets/[^/]+/sign[-\s]?language",
                    r"/datasets/[^/]+/asl",
                    r"/datasets/[^/]+/gestures"
                ]
            ),
            # Government datasets
            CrawlTarget(
                target_id="data_gov",
                name="Data.gov Sign Language",
                base_url="https://catalog.data.gov",
                source_type=DataSource.GOVERNMENT_DATASETS,
                crawl_patterns=[
                    r"sign[-\s]?language",
                    r"asl",
                    r"bsl"
                ]
            ),
            # Open data portals
            CrawlTarget(
                target_id="zenodo",
                name="Zenodo Research Datasets",
                base_url="https://zenodo.org",
                source_type=DataSource.OPEN_DATA_PORTALS,
                crawl_patterns=[
                    r"sign[-\s]?language",
                    r"american[-\s]?sign[-\s]?language",
                    r"british[-\s]?sign[-\s]?language"
                ]
            ),
            # Research institutions
            CrawlTarget(
                target_id="gallaudet",
                name="Gallaudet University",
                base_url="https://www.gallaudet.edu",
                source_type=DataSource.RESEARCH_INSTITUTIONS,
                crawl_patterns=[
                    r"research",
                    r"dataset",
                    r"sign[-\s]?language"
                ]
            )
        ]
        
        for target in default_targets:
            self.targets[target.target_id] = target
            self.metrics["targets_configured"] += 1
        
        logger.info(f"Loaded {len(default_targets)} default crawl targets")
    
    async def add_target(self, target: CrawlTarget) -> bool:
        """Add a new crawl target"""
        try:
            if target.target_id in self.targets:
                logger.warning(f"Target {target.target_id} already exists")
                return False
            
            self.targets[target.target_id] = target
            self.metrics["targets_configured"] += 1
            
            logger.info(f"Added crawl target: {target.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add target {target.target_id}: {e}")
            return False
    
    async def _crawl_scheduler(self):
        """Schedule crawling tasks"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check which targets need crawling
                current_time = time.time()
                
                for target_id, target in self.targets.items():
                    # Check if target should be crawled
                    if self._should_crawl_target(target, current_time):
                        await self.crawl_queue.put(target_id)
                        target.last_crawl_time = current_time
                        target.crawl_status = CrawlStatus.PENDING
                
            except Exception as e:
                logger.error(f"Crawl scheduler error: {e}")
                await asyncio.sleep(10)
    
    def _should_crawl_target(self, target: CrawlTarget, current_time: float) -> bool:
        """Check if target should be crawled"""
        # Don't crawl if already crawling
        if target.target_id in self.active_crawls:
            return False
        
        # Check rate limiting
        time_since_last = current_time - target.last_crawl_time
        min_interval = 3600  # 1 hour minimum between crawls
        
        if time_since_last < min_interval:
            return False
        
        # Don't crawl if too many failures
        if target.error_count > 5:
            return False
        
        return True
    
    async def _queue_processor(self):
        """Process crawl queue"""
        while self.is_running:
            try:
                # Wait for crawl task
                target_id = await asyncio.wait_for(
                    self.crawl_queue.get(),
                    timeout=1.0
                )
                
                # Check concurrent crawl limit
                while len(self.active_crawls) >= self.max_concurrent_crawls:
                    await asyncio.sleep(1)
                
                # Start crawl
                if target_id not in self.active_crawls:
                    self.active_crawls.add(target_id)
                    asyncio.create_task(self._crawl_target(target_id))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(5)
    
    async def _crawl_target(self, target_id: str):
        """Crawl a specific target"""
        try:
            target = self.targets.get(target_id)
            if not target:
                logger.error(f"Target {target_id} not found")
                return
            
            target.crawl_status = CrawlStatus.CRAWLING
            start_time = time.time()
            
            logger.info(f"Starting crawl: {target.name}")
            
            # Crawl the target
            discovered_datasets = await self._crawl_website(target)
            
            # Process discovered datasets
            for dataset in discovered_datasets:
                if dataset.dataset_id not in self.discovered_datasets:
                    self.discovered_datasets[dataset.dataset_id] = dataset
                    self.metrics["datasets_discovered"] += 1
                    
                    # Notify callback
                    if self.on_dataset_discovered:
                        await self.on_dataset_discovered(dataset)
            
            # Update target status
            target.crawl_status = CrawlStatus.COMPLETED
            target.success_count += 1
            target.total_datasets_found += len(discovered_datasets)
            
            crawl_time = time.time() - start_time
            self.metrics["successful_crawls"] += 1
            
            # Update average crawl time
            total_crawls = self.metrics["successful_crawls"] + self.metrics["failed_crawls"]
            if total_crawls > 0:
                self.metrics["average_crawl_time"] = (
                    (self.metrics["average_crawl_time"] * (total_crawls - 1) + crawl_time) /
                    total_crawls
                )
            
            # Remove from active crawls
            self.active_crawls.discard(target_id)
            
            # Notify callback
            if self.on_crawl_completed:
                await self.on_crawl_completed(target, discovered_datasets)
            
            logger.info(f"Completed crawl: {target.name} - {len(discovered_datasets)} datasets found")
            
        except Exception as e:
            # Update error status
            if target_id in self.targets:
                self.targets[target_id].crawl_status = CrawlStatus.FAILED
                self.targets[target_id].error_count += 1
            
            self.metrics["failed_crawls"] += 1
            self.active_crawls.discard(target_id)
            
            logger.error(f"Failed to crawl target {target_id}: {e}")
            
            # Notify callback
            if self.on_crawl_failed:
                target = self.targets.get(target_id)
                await self.on_crawl_failed(target, str(e))
    
    async def _crawl_website(self, target: CrawlTarget) -> List[DatasetInfo]:
        """Crawl a website for datasets"""
        discovered_datasets = []
        
        try:
            # Get main page
            async with self.session.get(target.base_url, headers=target.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract dataset links based on patterns
                    dataset_links = self._extract_dataset_links(content, target)
                    
                    # Process each dataset link
                    for link in dataset_links:
                        try:
                            dataset = await self._process_dataset_page(link, target)
                            if dataset:
                                discovered_datasets.append(dataset)
                        except Exception as e:
                            logger.warning(f"Error processing dataset link {link}: {e}")
                            continue
                
                else:
                    logger.warning(f"Failed to fetch {target.base_url}: {response.status}")
            
        except Exception as e:
            logger.error(f"Error crawling {target.base_url}: {e}")
        
        return discovered_datasets
    
    def _extract_dataset_links(self, html_content: str, target: CrawlTarget) -> List[str]:
        """Extract dataset links from HTML content"""
        links = []
        
        for pattern in target.crawl_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Convert relative URLs to absolute
                if match.startswith('/'):
                    full_url = urljoin(target.base_url, match)
                elif not match.startswith(('http://', 'https://')):
                    full_url = urljoin(target.base_url, match)
                else:
                    full_url = match
                
                if full_url not in links:
                    links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    async def _process_dataset_page(self, url: str, target: CrawlTarget) -> Optional[DatasetInfo]:
        """Process a dataset page to extract information"""
        try:
            # Respect rate limiting
            await asyncio.sleep(1.0 / target.rate_limit)
            
            async with self.session.get(url, headers=target.headers) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                
                # Extract dataset information
                dataset_info = await self._extract_dataset_info(content, url, target)
                
                return dataset_info
                
        except Exception as e:
            logger.error(f"Error processing dataset page {url}: {e}")
            return None
    
    async def _extract_dataset_info(self, content: str, url: str, target: CrawlTarget) -> Optional[DatasetInfo]:
        """Extract dataset information from page content"""
        try:
            # Generate dataset ID
            dataset_id = hashlib.sha256(f"{url}_{time.time()}".encode()).hexdigest()[:16]
            
            # Extract basic information using regex patterns
            title = self._extract_title(content)
            description = self._extract_description(content)
            download_links = self._extract_download_links(content, url)
            
            if not title and not download_links:
                return None
            
            # Detect file formats
            file_formats = []
            for link in download_links:
                format = self._detect_file_format(link)
                if format and format not in file_formats:
                    file_formats.append(format)
            
            # Extract metadata
            metadata = self._extract_metadata(content)
            
            # Detect sign language
            sign_language = self._detect_sign_language(content + " " + title + " " + description)
            
            # Create dataset info
            dataset = DatasetInfo(
                dataset_id=dataset_id,
                title=title or "Untitled Dataset",
                description=description or "",
                source_url=url,
                download_urls=download_links,
                file_formats=file_formats,
                file_sizes=[],  # Would need to fetch headers to get sizes
                license_info=metadata.get("license", "Unknown"),
                sign_language=sign_language,
                num_samples=metadata.get("num_samples"),
                metadata=metadata
            )
            
            # Calculate quality score
            dataset.calculate_quality_score()
            
            # Extract tags
            tags = self._extract_tags(content)
            for tag in tags:
                dataset.add_tag(tag)
            
            # Extract authors
            authors = self._extract_authors(content)
            for author in authors:
                dataset.add_author(author)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error extracting dataset info: {e}")
            return None
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from content"""
        patterns = [
            r'<title[^>]*>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'"title":\s*"([^"]+)"',
            r'"name":\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                return self._clean_text(title)
        
        return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from content"""
        patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
            r'"description":\s*"([^"]+)"',
            r'<p[^>]*>([^<]{100,})</p>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                description = matches[0] if isinstance(matches[0], str) else matches[0][1]
                return self._clean_text(description)
        
        return None
    
    def _extract_download_links(self, content: str, base_url: str) -> List[str]:
        """Extract download links from content"""
        links = []
        
        # Common download link patterns
        patterns = [
            r'href=["\']([^"\']*\.(?:csv|json|xml|zip|tar|gz|h5|parquet)["\']',
            r'"download_url":\s*"([^"]+)"',
            r'"url":\s*"([^"]+\.(?:csv|json|xml|zip|tar|gz|h5|parquet))"',
            r'<a[^>]*href=["\']([^"\']*(?:download|dataset|file)[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                link = match if isinstance(match, str) else match[0]
                
                # Convert relative URLs to absolute
                if link.startswith('/'):
                    full_url = urljoin(base_url, link)
                elif not link.startswith(('http://', 'https://')):
                    full_url = urljoin(base_url, link)
                else:
                    full_url = link
                
                if full_url not in links:
                    links.append(full_url)
        
        return list(set(links))
    
    def _detect_file_format(self, url: str) -> Optional[DatasetFormat]:
        """Detect file format from URL"""
        format_mapping = {
            '.csv': DatasetFormat.CSV,
            '.json': DatasetFormat.JSON,
            '.xml': DatasetFormat.XML,
            '.mp4': DatasetFormat.VIDEO_MP4,
            '.avi': DatasetFormat.VIDEO_AVI,
            '.mov': DatasetFormat.VIDEO_MOV,
            '.zip': DatasetFormat.COMPRESSED_ZIP,
            '.tar': DatasetFormat.COMPRESSED_TAR,
            '.h5': DatasetFormat.HDF5,
            '.hdf5': DatasetFormat.HDF5,
            '.parquet': DatasetFormat.PARQUET
        }
        
        for ext, format_type in format_mapping.items():
            if ext.lower() in url.lower():
                return format_type
        
        return None
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from content"""
        metadata = {}
        
        # Common metadata patterns
        patterns = {
            'license': [
                r'"license":\s*"([^"]+)"',
                r'<meta[^>]*name=["\']license["\'][^>]*content=["\']([^"\']+)["\']',
                r'License:\s*([^\n\r]+)'
            ],
            'num_samples': [
                r'"num_samples":\s*(\d+)',
                r'"samples":\s*(\d+)',
                r'(\d+)\s*samples'
            ],
            'size': [
                r'"size":\s*(\d+)',
                r'"file_size":\s*(\d+)',
                r'(\d+)\s*[GM]B'
            ]
        }
        
        for key, key_patterns in patterns.items():
            for pattern in key_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    
                    # Convert to appropriate type
                    if key in ['num_samples', 'size']:
                        try:
                            value = int(value)
                        except ValueError:
                            value = 0
                    
                    metadata[key] = value
                    break
        
        return metadata
    
    def _detect_sign_language(self, text: str) -> str:
        """Detect sign language from text"""
        text_lower = text.lower()
        
        # Language detection patterns
        language_patterns = {
            'asl': ['american sign language', 'asl', 'america'],
            'bsl': ['british sign language', 'bsl', 'britain'],
            'isl': ['international sign language', 'isl'],
            'jsl': ['japanese sign language', 'jsl', 'japan'],
            'csl': ['chinese sign language', 'csl', 'china'],
            'fsl': ['french sign language', 'fsl', 'france']
        }
        
        # Count occurrences of each language pattern
        language_scores = {}
        for lang, patterns in language_patterns.items():
            score = 0
            for pattern in patterns:
                score += text_lower.count(pattern)
            language_scores[lang] = score
        
        # Return language with highest score
        if language_scores:
            best_lang = max(language_scores, key=language_scores.get)
            if language_scores[best_lang] > 0:
                return best_lang
        
        return "unknown"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content"""
        tags = []
        
        # Common tag patterns
        tag_patterns = [
            r'"tags":\s*\[([^\]]+)\]',
            r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)["\']',
            r'Keywords?:\s*([^\n\r]+)'
        ]
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                tag_str = match if isinstance(match, str) else match[0]
                
                # Split by common separators
                for tag in re.split(r'[,;|]', tag_str):
                    tag = tag.strip().strip('"\'')
                    if tag and len(tag) > 2:
                        tags.append(tag.lower())
        
        # Add common sign language related tags
        common_tags = ['sign language', 'asl', 'bsl', 'gestures', 'hands', 'deaf']
        for tag in common_tags:
            if tag in content.lower():
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_authors(self, content: str) -> List[str]:
        """Extract authors from content"""
        authors = []
        
        # Author patterns
        author_patterns = [
            r'"author":\s*"([^"]+)"',
            r'"authors":\s*\[([^\]]+)\]',
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
            r'Author[s]?:\s*([^\n\r]+)'
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                author_str = match if isinstance(match, str) else match[0]
                
                # Split by common separators
                for author in re.split(r'[,;|]', author_str):
                    author = author.strip().strip('"\'')
                    if author and len(author) > 2:
                        authors.append(author)
        
        return list(set(authors))  # Remove duplicates
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip and limit length
        return text.strip()[:500]
    
    async def _metrics_loop(self):
        """Background loop for metrics collection"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                # Calculate crawl rate
                if self.metrics["successful_crawls"] > 0:
                    uptime = time.time() - (self.metrics.get("service_start_time", time.time()))
                    self.metrics["crawl_rate"] = (self.metrics["datasets_discovered"] / max(uptime, 1)) * 3600  # per hour
                
                logger.debug(f"Dataset crawler metrics: {self.metrics}")
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Background loop for cleanup operations"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                # Remove old low-quality datasets
                current_time = time.time()
                max_age = 7 * 24 * 3600  # 7 days
                
                old_datasets = [
                    dataset_id for dataset_id, dataset in self.discovered_datasets.items()
                    if (current_time - dataset.discovered_at > max_age and 
                        dataset.quality_score < 30)
                ]
                
                for dataset_id in old_datasets:
                    del self.discovered_datasets[dataset_id]
                
                logger.debug(f"Cleaned up {len(old_datasets)} old low-quality datasets")
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    def get_discovered_datasets(self, filters: Dict[str, Any] = None) -> List[DatasetInfo]:
        """Get discovered datasets with optional filters"""
        datasets = list(self.discovered_datasets.values())
        
        if not filters:
            return datasets
        
        # Apply filters
        filtered_datasets = []
        
        for dataset in datasets:
            include = True
            
            # Quality filter
            if "min_quality" in filters:
                if dataset.quality_score < filters["min_quality"]:
                    include = False
            
            # Sign language filter
            if "sign_language" in filters:
                if dataset.sign_language != filters["sign_language"]:
                    include = False
            
            # Format filter
            if "file_formats" in filters:
                if not any(fmt in dataset.file_formats for fmt in filters["file_formats"]):
                    include = False
            
            # Tags filter
            if "tags" in filters:
                required_tags = set(filters["tags"])
                dataset_tags = set(dataset.tags)
                if not required_tags.issubset(dataset_tags):
                    include = False
            
            if include:
                filtered_datasets.append(dataset)
        
        return filtered_datasets
    
    def get_crawl_status(self) -> Dict[str, Any]:
        """Get crawl status and metrics"""
        return {
            "is_running": self.is_running,
            "targets": {
                target_id: target.to_dict()
                for target_id, target in self.targets.items()
            },
            "metrics": self.metrics,
            "active_crawls": len(self.active_crawls),
            "queue_size": self.crawl_queue.qsize(),
            "discovered_datasets": len(self.discovered_datasets)
        }
    
    def export_discovered_datasets(self) -> Dict[str, Any]:
        """Export discovered datasets"""
        return {
            "datasets": {
                dataset_id: dataset.to_dict()
                for dataset_id, dataset in self.discovered_datasets.items()
            },
            "targets": {
                target_id: target.to_dict()
                for target_id, target in self.targets.items()
            },
            "metrics": self.metrics,
            "export_timestamp": time.time()
        }
