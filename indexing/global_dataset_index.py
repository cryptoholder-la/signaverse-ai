"""
Global Dataset Indexing Layer (Bluesky-style)
Distributed indexing and discovery of sign language datasets
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatasetLicense(Enum):
    """Dataset license types"""
    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    MIT = "MIT"
    APACHE = "Apache-2.0"
    GPL = "GPL"
    PROPRIETARY = "proprietary"
    CUSTOM = "custom"


class DatasetQuality(Enum):
    """Dataset quality levels"""
    RAW = "raw"
    CLEANED = "cleaned"
    ANNOTATED = "annotated"
    VALIDATED = "validated"
    CURATED = "curated"


class IndexingStatus(Enum):
    """Indexing status"""
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"
    UPDATED = "updated"


@dataclass
class DatasetMetadata:
    """Metadata for indexed datasets"""
    def __init__(self, dataset_id: str, name: str, description: str,
                 creator: str, license: DatasetLicense, quality: DatasetQuality,
                 size_bytes: int, num_samples: int, sign_language: str,
                 data_format: str, annotations: List[str] = None,
                 tags: List[str] = None, created_at: float = None,
                 updated_at: float = None, download_url: str = None,
                 preview_url: str = None, metadata: Dict[str, Any] = None):
        self.dataset_id = dataset_id
        self.name = name
        self.description = description
        self.creator = creator
        self.license = license
        self.quality = quality
        self.size_bytes = size_bytes
        self.num_samples = num_samples
        self.sign_language = sign_language
        self.data_format = data_format
        self.annotations = annotations or []
        self.tags = tags or []
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()
        self.download_url = download_url
        self.preview_url = preview_url
        self.metadata = metadata or {}
        
        # Indexing metrics
        self.download_count = 0
        self.rating = 0.0
        self.num_ratings = 0
        self.indexing_status = IndexingStatus.PENDING
        self.indexing_timestamp = None
        self.search_rank = 0.0
        self.relevance_score = 0.0
    
    def update_rating(self, new_rating: float):
        """Update dataset rating"""
        if self.num_ratings == 0:
            self.rating = new_rating
        else:
            self.rating = (self.rating * self.num_ratings + new_rating) / (self.num_ratings + 1)
        self.num_ratings += 1
    
    def increment_download(self):
        """Increment download count"""
        self.download_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SearchQuery:
    """Search query for datasets"""
    def __init__(self, query: str, filters: Dict[str, Any] = None,
                 sort_by: str = "relevance", limit: int = 50,
                 offset: int = 0, facets: List[str] = None):
        self.query = query.lower().strip()
        self.filters = filters or {}
        self.sort_by = sort_by
        self.limit = limit
        self.offset = offset
        self.facets = facets or ["sign_language", "quality", "license", "tags"]
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SearchResult:
    """Search result with metadata"""
    def __init__(self, dataset: DatasetMetadata, relevance_score: float,
                 match_highlights: List[str] = None):
        self.dataset = dataset
        self.relevance_score = relevance_score
        self.match_highlights = match_highlights or []
        self.rank = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dataset": self.dataset.to_dict(),
            "relevance_score": self.relevance_score,
            "match_highlights": self.match_highlights,
            "rank": self.rank
        }


class DatasetIndexer:
    """Dataset indexing and search engine"""
    
    def __init__(self, index_db_path: str = "./dataset_index.db"):
        self.index_db_path = index_db_path
        self.db_connection = None
        
        # In-memory index for fast search
        self.datasets: Dict[str, DatasetMetadata] = {}
        self.text_index: Dict[str, Set[str]] = {}  # term -> dataset_ids
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> dataset_ids
        self.language_index: Dict[str, Set[str]] = {}  # language -> dataset_ids
        self.creator_index: Dict[str, Set[str]] = {}  # creator -> dataset_ids
        
        # Search configuration
        self.search_config = {
            "min_term_length": 2,
            "max_results": 1000,
            "boost_recent": 1.2,  # Boost recent datasets
            "boost_downloads": 1.1,  # Boost popular datasets
            "boost_ratings": 1.3,  # Boost highly rated datasets
            "fuzzy_threshold": 0.8
        }
        
        # Performance metrics
        self.metrics = {
            "datasets_indexed": 0,
            "searches_performed": 0,
            "average_search_time": 0.0,
            "index_size_bytes": 0,
            "last_index_time": 0.0
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
    
    async def start(self) -> bool:
        """Start the indexing service"""
        try:
            self.is_running = True
            
            # Initialize database
            await self._init_database()
            
            # Load existing index
            await self._load_index()
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._indexing_loop()),
                asyncio.create_task(self._cleanup_loop()),
                asyncio.create_task(self._metrics_loop())
            ]
            
            logger.info("Global dataset indexer started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start dataset indexer: {e}")
            return False
    
    async def stop(self):
        """Stop the indexing service"""
        self.is_running = False
        
        # Close database
        if self.db_connection:
            self.db_connection.close()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Global dataset indexer stopped")
    
    async def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        self.db_connection = sqlite3.connect(self.index_db_path)
        
        # Create tables
        cursor = self.db_connection.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                creator TEXT NOT NULL,
                license TEXT NOT NULL,
                quality TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                num_samples INTEGER NOT NULL,
                sign_language TEXT NOT NULL,
                data_format TEXT NOT NULL,
                annotations TEXT,
                tags TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                download_url TEXT,
                preview_url TEXT,
                metadata TEXT,
                download_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                num_ratings INTEGER DEFAULT 0,
                indexing_status TEXT NOT NULL,
                indexing_timestamp REAL,
                search_rank REAL DEFAULT 0.0,
                relevance_score REAL DEFAULT 0.0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                filters TEXT,
                results_count INTEGER,
                search_time REAL,
                timestamp REAL NOT NULL
            )
        ''')
        
        self.db_connection.commit()
    
    async def _load_index(self):
        """Load existing index from database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT * FROM datasets")
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            for row in rows:
                dataset_dict = dict(zip(columns, row))
                
                # Parse JSON fields
                if dataset_dict['annotations']:
                    dataset_dict['annotations'] = json.loads(dataset_dict['annotations'])
                else:
                    dataset_dict['annotations'] = []
                
                if dataset_dict['tags']:
                    dataset_dict['tags'] = json.loads(dataset_dict['tags'])
                else:
                    dataset_dict['tags'] = []
                
                if dataset_dict['metadata']:
                    dataset_dict['metadata'] = json.loads(dataset_dict['metadata'])
                else:
                    dataset_dict['metadata'] = {}
                
                # Create DatasetMetadata object
                dataset = DatasetMetadata(
                    dataset_id=dataset_dict['dataset_id'],
                    name=dataset_dict['name'],
                    description=dataset_dict['description'],
                    creator=dataset_dict['creator'],
                    license=DatasetLicense(dataset_dict['license']),
                    quality=DatasetQuality(dataset_dict['quality']),
                    size_bytes=dataset_dict['size_bytes'],
                    num_samples=dataset_dict['num_samples'],
                    sign_language=dataset_dict['sign_language'],
                    data_format=dataset_dict['data_format'],
                    annotations=dataset_dict['annotations'],
                    tags=dataset_dict['tags'],
                    created_at=dataset_dict['created_at'],
                    updated_at=dataset_dict['updated_at'],
                    download_url=dataset_dict['download_url'],
                    preview_url=dataset_dict['preview_url'],
                    metadata=dataset_dict['metadata']
                )
                
                dataset.download_count = dataset_dict['download_count']
                dataset.rating = dataset_dict['rating']
                dataset.num_ratings = dataset_dict['num_ratings']
                dataset.indexing_status = IndexingStatus(dataset_dict['indexing_status'])
                dataset.indexing_timestamp = dataset_dict['indexing_timestamp']
                dataset.search_rank = dataset_dict['search_rank']
                dataset.relevance_score = dataset_dict['relevance_score']
                
                self.datasets[dataset.dataset_id] = dataset
                
                # Update indexes
                self._update_text_index(dataset)
                self._update_tag_index(dataset)
                self._update_language_index(dataset)
                self._update_creator_index(dataset)
            
            self.metrics["datasets_indexed"] = len(self.datasets)
            logger.info(f"Loaded {len(self.datasets)} datasets from index")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
    
    def _update_text_index(self, dataset: DatasetMetadata):
        """Update text search index"""
        # Extract searchable terms
        text_content = f"{dataset.name} {dataset.description}"
        terms = self._extract_terms(text_content)
        
        for term in terms:
            if term not in self.text_index:
                self.text_index[term] = set()
            self.text_index[term].add(dataset.dataset_id)
    
    def _update_tag_index(self, dataset: DatasetMetadata):
        """Update tag index"""
        for tag in dataset.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(dataset.dataset_id)
    
    def _update_language_index(self, dataset: DatasetMetadata):
        """Update language index"""
        if dataset.sign_language not in self.language_index:
            self.language_index[dataset.sign_language] = set()
        self.language_index[dataset.sign_language].add(dataset.dataset_id)
    
    def _update_creator_index(self, dataset: DatasetMetadata):
        """Update creator index"""
        if dataset.creator not in self.creator_index:
            self.creator_index[dataset.creator] = set()
        self.creator_index[dataset.creator].add(dataset.dataset_id)
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract searchable terms from text"""
        import re
        
        # Convert to lowercase and split
        terms = re.findall(r'\b\w+\b', text.lower())
        
        # Filter terms
        filtered_terms = []
        for term in terms:
            if len(term) >= self.search_config["min_term_length"]:
                filtered_terms.append(term)
        
        return list(set(filtered_terms))  # Remove duplicates
    
    async def index_dataset(self, dataset_metadata: DatasetMetadata) -> bool:
        """Index a new dataset"""
        try:
            # Check if dataset already exists
            if dataset_metadata.dataset_id in self.datasets:
                # Update existing dataset
                await self.update_dataset(dataset_metadata.dataset_id, dataset_metadata)
                return True
            
            # Set indexing status
            dataset_metadata.indexing_status = IndexingStatus.INDEXING
            dataset_metadata.indexing_timestamp = time.time()
            
            # Add to in-memory index
            self.datasets[dataset_metadata.dataset_id] = dataset_metadata
            self._update_text_index(dataset_metadata)
            self._update_tag_index(dataset_metadata)
            self._update_language_index(dataset_metadata)
            self._update_creator_index(dataset_metadata)
            
            # Save to database
            await self._save_dataset_to_db(dataset_metadata)
            
            # Update status
            dataset_metadata.indexing_status = IndexingStatus.INDEXED
            
            # Update metrics
            self.metrics["datasets_indexed"] += 1
            self.metrics["last_index_time"] = time.time()
            
            logger.info(f"Indexed dataset: {dataset_metadata.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index dataset {dataset_metadata.dataset_id}: {e}")
            if dataset_metadata.dataset_id in self.datasets:
                self.datasets[dataset_metadata.dataset_id].indexing_status = IndexingStatus.FAILED
            return False
    
    async def _save_dataset_to_db(self, dataset: DatasetMetadata):
        """Save dataset to database"""
        try:
            cursor = self.db_connection.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO datasets (
                    dataset_id, name, description, creator, license, quality,
                    size_bytes, num_samples, sign_language, data_format,
                    annotations, tags, created_at, updated_at,
                    download_url, preview_url, metadata, download_count,
                    rating, num_ratings, indexing_status, indexing_timestamp,
                    search_rank, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset.dataset_id, dataset.name, dataset.description,
                dataset.creator, dataset.license.value, dataset.quality.value,
                dataset.size_bytes, dataset.num_samples, dataset.sign_language,
                dataset.data_format, json.dumps(dataset.annotations),
                json.dumps(dataset.tags), dataset.created_at, dataset.updated_at,
                dataset.download_url, dataset.preview_url,
                json.dumps(dataset.metadata), dataset.download_count,
                dataset.rating, dataset.num_ratings, dataset.indexing_status.value,
                dataset.indexing_timestamp, dataset.search_rank, dataset.relevance_score
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error saving dataset to database: {e}")
    
    async def update_dataset(self, dataset_id: str, updated_metadata: DatasetMetadata) -> bool:
        """Update an existing dataset"""
        try:
            if dataset_id not in self.datasets:
                logger.error(f"Dataset {dataset_id} not found")
                return False
            
            old_metadata = self.datasets[dataset_id]
            
            # Update fields
            old_metadata.name = updated_metadata.name
            old_metadata.description = updated_metadata.description
            old_metadata.license = updated_metadata.license
            old_metadata.quality = updated_metadata.quality
            old_metadata.size_bytes = updated_metadata.size_bytes
            old_metadata.num_samples = updated_metadata.num_samples
            old_metadata.sign_language = updated_metadata.sign_language
            old_metadata.data_format = updated_metadata.data_format
            old_metadata.annotations = updated_metadata.annotations
            old_metadata.tags = updated_metadata.tags
            old_metadata.updated_at = time.time()
            old_metadata.metadata = updated_metadata.metadata
            
            # Rebuild indexes
            self._rebuild_indexes()
            
            # Save to database
            await self._save_dataset_to_db(old_metadata)
            
            logger.info(f"Updated dataset: {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update dataset {dataset_id}: {e}")
            return False
    
    def _rebuild_indexes(self):
        """Rebuild all search indexes"""
        self.text_index.clear()
        self.tag_index.clear()
        self.language_index.clear()
        self.creator_index.clear()
        
        for dataset in self.datasets.values():
            self._update_text_index(dataset)
            self._update_tag_index(dataset)
            self._update_language_index(dataset)
            self._update_creator_index(dataset)
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search for datasets"""
        try:
            start_time = time.time()
            
            # Find matching dataset IDs
            matching_ids = set()
            
            # Text search
            if query.query:
                text_matches = self._text_search(query.query)
                matching_ids.update(text_matches)
            
            # Apply filters
            if query.filters:
                filtered_ids = self._apply_filters(query.filters)
                if matching_ids:
                    matching_ids &= filtered_ids
                else:
                    matching_ids = filtered_ids
            
            # Get matching datasets
            matching_datasets = [
                self.datasets[dataset_id] 
                for dataset_id in matching_ids 
                if dataset_id in self.datasets
            ]
            
            # Calculate relevance scores
            results = []
            for dataset in matching_datasets:
                relevance_score = self._calculate_relevance_score(dataset, query)
                result = SearchResult(dataset, relevance_score)
                results.append(result)
            
            # Sort results
            if query.sort_by == "relevance":
                results.sort(key=lambda r: r.relevance_score, reverse=True)
            elif query.sort_by == "created_at":
                results.sort(key=lambda r: r.dataset.created_at, reverse=True)
            elif query.sort_by == "updated_at":
                results.sort(key=lambda r: r.dataset.updated_at, reverse=True)
            elif query.sort_by == "downloads":
                results.sort(key=lambda r: r.dataset.download_count, reverse=True)
            elif query.sort_by == "rating":
                results.sort(key=lambda r: r.dataset.rating, reverse=True)
            
            # Apply ranking
            for i, result in enumerate(results):
                result.rank = i + 1
            
            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit
            paginated_results = results[start_idx:end_idx]
            
            # Log search
            search_time = time.time() - start_time
            await self._log_search(query, len(paginated_results), search_time)
            
            # Update metrics
            self.metrics["searches_performed"] += 1
            self.metrics["average_search_time"] = (
                (self.metrics["average_search_time"] * (self.metrics["searches_performed"] - 1) + search_time) /
                self.metrics["searches_performed"]
            )
            
            logger.info(f"Search completed: {query.query} -> {len(paginated_results)} results in {search_time:.3f}s")
            return paginated_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _text_search(self, query: str) -> Set[str]:
        """Perform text search"""
        query_terms = self._extract_terms(query)
        matching_ids = set()
        
        for term in query_terms:
            if term in self.text_index:
                matching_ids.update(self.text_index[term])
        
        return matching_ids
    
    def _apply_filters(self, filters: Dict[str, Any]) -> Set[str]:
        """Apply search filters"""
        filtered_ids = set(self.datasets.keys())
        
        # Language filter
        if "sign_language" in filters:
            language = filters["sign_language"]
            if language in self.language_index:
                filtered_ids &= self.language_index[language]
            else:
                return set()  # No results if language not found
        
        # Quality filter
        if "quality" in filters:
            quality = filters["quality"]
            quality_filtered = set()
            for dataset_id in filtered_ids:
                dataset = self.datasets[dataset_id]
                if dataset.quality.value == quality:
                    quality_filtered.add(dataset_id)
            filtered_ids = quality_filtered
        
        # License filter
        if "license" in filters:
            license_type = filters["license"]
            license_filtered = set()
            for dataset_id in filtered_ids:
                dataset = self.datasets[dataset_id]
                if dataset.license.value == license_type:
                    license_filtered.add(dataset_id)
            filtered_ids = license_filtered
        
        # Creator filter
        if "creator" in filters:
            creator = filters["creator"]
            if creator in self.creator_index:
                filtered_ids &= self.creator_index[creator]
            else:
                return set()
        
        # Tags filter
        if "tags" in filters:
            required_tags = set(filters["tags"])
            tags_filtered = set()
            for dataset_id in filtered_ids:
                dataset = self.datasets[dataset_id]
                if required_tags.issubset(set(dataset.tags)):
                    tags_filtered.add(dataset_id)
            filtered_ids = tags_filtered
        
        # Size filter
        if "min_size" in filters:
            min_size = filters["min_size"]
            size_filtered = set()
            for dataset_id in filtered_ids:
                dataset = self.datasets[dataset_id]
                if dataset.size_bytes >= min_size:
                    size_filtered.add(dataset_id)
            filtered_ids = size_filtered
        
        if "max_size" in filters:
            max_size = filters["max_size"]
            size_filtered = set()
            for dataset_id in filtered_ids:
                dataset = self.datasets[dataset_id]
                if dataset.size_bytes <= max_size:
                    size_filtered.add(dataset_id)
            filtered_ids = size_filtered
        
        return filtered_ids
    
    def _calculate_relevance_score(self, dataset: DatasetMetadata, query: SearchQuery) -> float:
        """Calculate relevance score for a dataset"""
        score = 0.0
        
        # Text matching score
        if query.query:
            query_terms = set(self._extract_terms(query.query))
            dataset_terms = set(self._extract_terms(f"{dataset.name} {dataset.description}"))
            
            # Calculate term overlap
            overlap = query_terms & dataset_terms
            if overlap:
                text_score = len(overlap) / len(query_terms)
                score += text_score * 0.4
        
        # Boost factors
        current_time = time.time()
        
        # Recent boost
        days_old = (current_time - dataset.created_at) / (24 * 3600)
        if days_old < 30:  # Less than 30 days old
            score *= self.search_config["boost_recent"]
        
        # Download count boost
        if dataset.download_count > 0:
            download_boost = 1.0 + (dataset.download_count / 1000)  # Logarithmic boost
            score *= min(download_boost, self.search_config["boost_downloads"])
        
        # Rating boost
        if dataset.rating > 0:
            rating_boost = 1.0 + (dataset.rating / 5.0)  # Scale 0-5 to boost
            score *= min(rating_boost, self.search_config["boost_ratings"])
        
        return score
    
    async def _log_search(self, query: SearchQuery, results_count: int, search_time: float):
        """Log search query for analytics"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO search_logs (query, filters, results_count, search_time, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                query.query, json.dumps(query.filters), results_count,
                search_time, time.time()
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error logging search: {e}")
    
    def get_facets(self, query: SearchQuery) -> Dict[str, Dict[str, int]]:
        """Get facet counts for search results"""
        try:
            # Get matching dataset IDs
            matching_ids = set()
            
            if query.query:
                text_matches = self._text_search(query.query)
                matching_ids.update(text_matches)
            
            if query.filters:
                filtered_ids = self._apply_filters(query.filters)
                if matching_ids:
                    matching_ids &= filtered_ids
                else:
                    matching_ids = filtered_ids
            
            facets = {}
            
            # Language facet
            if "sign_language" in query.facets:
                language_counts = {}
                for dataset_id in matching_ids:
                    if dataset_id in self.datasets:
                        dataset = self.datasets[dataset_id]
                        lang = dataset.sign_language
                        language_counts[lang] = language_counts.get(lang, 0) + 1
                facets["sign_language"] = language_counts
            
            # Quality facet
            if "quality" in query.facets:
                quality_counts = {}
                for dataset_id in matching_ids:
                    if dataset_id in self.datasets:
                        dataset = self.datasets[dataset_id]
                        quality = dataset.quality.value
                        quality_counts[quality] = quality_counts.get(quality, 0) + 1
                facets["quality"] = quality_counts
            
            # License facet
            if "license" in query.facets:
                license_counts = {}
                for dataset_id in matching_ids:
                    if dataset_id in self.datasets:
                        dataset = self.datasets[dataset_id]
                        license_type = dataset.license.value
                        license_counts[license_type] = license_counts.get(license_type, 0) + 1
                facets["license"] = license_counts
            
            # Tags facet
            if "tags" in query.facets:
                tag_counts = {}
                for dataset_id in matching_ids:
                    if dataset_id in self.datasets:
                        dataset = self.datasets[dataset_id]
                        for tag in dataset.tags:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Sort by count and limit
                facets["tags"] = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20])
            
            return facets
            
        except Exception as e:
            logger.error(f"Error calculating facets: {e}")
            return {}
    
    async def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """Get dataset by ID"""
        return self.datasets.get(dataset_id)
    
    async def increment_downloads(self, dataset_id: str) -> bool:
        """Increment download count for a dataset"""
        try:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return False
            
            dataset.increment_download()
            
            # Update in database
            cursor = self.db_connection.cursor()
            cursor.execute(
                "UPDATE datasets SET download_count = ? WHERE dataset_id = ?",
                (dataset.download_count, dataset_id)
            )
            self.db_connection.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing downloads for {dataset_id}: {e}")
            return False
    
    async def rate_dataset(self, dataset_id: str, rating: float, user_id: str = None) -> bool:
        """Rate a dataset"""
        try:
            dataset = self.datasets.get(dataset_id)
            if not dataset:
                return False
            
            dataset.update_rating(rating)
            
            # Update in database
            cursor = self.db_connection.cursor()
            cursor.execute(
                "UPDATE datasets SET rating = ?, num_ratings = ? WHERE dataset_id = ?",
                (dataset.rating, dataset.num_ratings, dataset_id)
            )
            self.db_connection.commit()
            
            logger.info(f"Rated dataset {dataset_id}: {rating}")
            return True
            
        except Exception as e:
            logger.error(f"Error rating dataset {dataset_id}: {e}")
            return False
    
    async def _indexing_loop(self):
        """Background loop for indexing operations"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Process any pending indexing operations
                # This would be implemented based on a queue of indexing requests
                
            except Exception as e:
                logger.error(f"Indexing loop error: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_loop(self):
        """Background loop for cleanup operations"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                # Clean up old search logs
                cutoff_time = time.time() - (30 * 24 * 3600)  # 30 days ago
                
                cursor = self.db_connection.cursor()
                cursor.execute(
                    "DELETE FROM search_logs WHERE timestamp < ?",
                    (cutoff_time,)
                )
                self.db_connection.commit()
                
                logger.debug("Cleaned up old search logs")
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    async def _metrics_loop(self):
        """Background loop for metrics collection"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                # Calculate index size
                self.metrics["index_size_bytes"] = sum(
                    len(json.dumps(dataset.to_dict())) 
                    for dataset in self.datasets.values()
                )
                
                logger.debug(f"Dataset indexer metrics: {self.metrics}")
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(60)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get indexer metrics"""
        return {
            **self.metrics,
            "total_datasets": len(self.datasets),
            "text_index_size": len(self.text_index),
            "tag_index_size": len(self.tag_index),
            "language_index_size": len(self.language_index),
            "creator_index_size": len(self.creator_index)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get indexer status"""
        return {
            "is_running": self.is_running,
            "metrics": self.get_metrics(),
            "search_config": self.search_config
        }
