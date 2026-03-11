"""
Distributed Dataset Protocol
Advanced dataset management for federated AI training
"""

import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class DatasetType(Enum):
    """Types of datasets"""
    SIGN_VIDEO = "sign_video"
    TRANSLATION = "translation"
    ANNOTATION = "annotation"
    MULTIMODAL = "multimodal"
    SYNTHETIC = "synthetic"


class DatasetQuality(Enum):
    """Quality levels for datasets"""
    RAW = "raw"
    CLEANED = "cleaned"
    VALIDATED = "validated"
    CURATED = "curated"
    GOLD_STANDARD = "gold_standard"


@dataclass
class DatasetEntry:
    """Individual entry in a dataset"""
    def __init__(self, entry_id: str, entry_type: DatasetType, 
                 data: Dict[str, Any], metadata: Dict[str, Any] = None):
        self.entry_id = entry_id
        self.entry_type = entry_type
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.contributors: List[str] = []
        self.quality_score: float = 0.0
        self.validation_status: str = "pending"
        self.annotations: List[Dict[str, Any]] = []
        self.license: str = "CC-BY-SA"
        self.tags: Set[str] = set()
        self.size_bytes: int = 0
        self.checksum: str = ""
        self.version: int = 1
    
    def add_contributor(self, contributor: str):
        """Add a contributor to this entry"""
        if contributor not in self.contributors:
            self.contributors.append(contributor)
    
    def add_annotation(self, annotation: Dict[str, Any]):
        """Add an annotation to this entry"""
        self.annotations.append(annotation)
    
    def add_tag(self, tag: str):
        """Add a tag to this entry"""
        self.tags.add(tag)
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for entry data"""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type.value,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "contributors": self.contributors,
            "quality_score": self.quality_score,
            "validation_status": self.validation_status,
            "annotations": self.annotations,
            "license": self.license,
            "tags": list(self.tags),
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "version": self.version
        }


@dataclass
class Dataset:
    """Collection of dataset entries"""
    def __init__(self, dataset_id: str, name: str, description: str,
                 dataset_type: DatasetType, creator: str):
        self.dataset_id = dataset_id
        self.name = name
        self.description = description
        self.dataset_type = dataset_type
        self.creator = creator
        self.entries: Dict[str, DatasetEntry] = {}
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.version: int = 1
        self.quality_level: DatasetQuality = DatasetQuality.RAW
        self.total_size: int = 0
        self.download_count: int = 0
        self.usage_count: int = 0
        self.access_control: Dict[str, Any] = {}
        self.federated_nodes: Set[str] = set()
        self.training_metrics: Dict[str, Any] = {}
        self.license: str = "CC-BY-SA"
        self.tags: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    def add_entry(self, entry: DatasetEntry) -> bool:
        """Add an entry to the dataset"""
        if entry.entry_id in self.entries:
            return False
        
        # Calculate checksum
        entry.checksum = entry.calculate_checksum()
        
        # Add to dataset
        self.entries[entry.entry_id] = entry
        self.updated_at = time.time()
        self.total_size += entry.size_bytes
        
        logger.info(f"Added entry {entry.entry_id} to dataset {self.dataset_id}")
        return True
    
    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry from the dataset"""
        if entry_id not in self.entries:
            return False
        
        entry = self.entries[entry_id]
        self.total_size -= entry.size_bytes
        del self.entries[entry_id]
        self.updated_at = time.time()
        
        logger.info(f"Removed entry {entry_id} from dataset {self.dataset_id}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        entry_types = {}
        quality_scores = []
        
        for entry in self.entries.values():
            # Count by type
            entry_type = entry.entry_type.value
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
            
            # Collect quality scores
            quality_scores.append(entry.quality_score)
        
        return {
            "total_entries": len(self.entries),
            "entry_types": entry_types,
            "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "total_size_bytes": self.total_size,
            "download_count": self.download_count,
            "usage_count": self.usage_count,
            "federated_nodes": len(self.federated_nodes),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "description": self.description,
            "dataset_type": self.dataset_type.value,
            "creator": self.creator,
            "entries": {eid: entry.to_dict() for eid, entry in self.entries.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "quality_level": self.quality_level.value,
            "total_size": self.total_size,
            "download_count": self.download_count,
            "usage_count": self.usage_count,
            "access_control": self.access_control,
            "federated_nodes": list(self.federated_nodes),
            "training_metrics": self.training_metrics,
            "license": self.license,
            "tags": list(self.tags),
            "metadata": self.metadata
        }


class DatasetRegistry:
    """Registry for managing multiple datasets"""
    
    def __init__(self):
        self.datasets: Dict[str, Dataset] = {}
        self.indexes: Dict[str, Set[str]] = {
            "by_creator": {},
            "by_type": {},
            "by_tag": {},
            "by_quality": {},
            "by_license": {}
        }
        self.subscribers: List[Callable] = []
        self.federation_protocol = FederationProtocol()
        
        # Performance metrics
        self.metrics = {
            "datasets_created": 0,
            "entries_added": 0,
            "entries_removed": 0,
            "federation_requests": 0,
            "search_queries": 0
        }
    
    def subscribe(self, callback: Callable):
        """Subscribe to registry events"""
        self.subscribers.append(callback)
    
    async def create_dataset(self, name: str, description: str, dataset_type: DatasetType,
                          creator: str, license: str = "CC-BY-SA") -> str:
        """Create a new dataset"""
        dataset_id = self._generate_dataset_id()
        
        dataset = Dataset(
            dataset_id=dataset_id,
            name=name,
            description=description,
            dataset_type=dataset_type,
            creator=creator
        )
        dataset.license = license
        
        # Add to registry
        self.datasets[dataset_id] = dataset
        
        # Update indexes
        self._update_indexes(dataset, "create")
        
        # Update metrics
        self.metrics["datasets_created"] += 1
        
        # Notify subscribers
        await self._notify_subscribers("dataset_created", dataset)
        
        logger.info(f"Created dataset {dataset_id}: {name}")
        return dataset_id
    
    def _generate_dataset_id(self) -> str:
        """Generate unique dataset ID"""
        timestamp = str(time.time())
        content = f"dataset_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def add_entry(self, dataset_id: str, entry_type: DatasetType,
                      data: Dict[str, Any], contributor: str,
                      metadata: Dict[str, Any] = None) -> str:
        """Add an entry to a dataset"""
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        dataset = self.datasets[dataset_id]
        entry_id = self._generate_entry_id()
        
        entry = DatasetEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            data=data,
            metadata=metadata
        )
        entry.add_contributor(contributor)
        
        # Calculate size (mock)
        entry.size_bytes = len(json.dumps(data))
        
        if dataset.add_entry(entry):
            # Update indexes
            self._update_entry_indexes(dataset_id, entry, "add")
            
            # Update metrics
            self.metrics["entries_added"] += 1
            
            # Notify subscribers
            await self._notify_subscribers("entry_added", {
                "dataset_id": dataset_id,
                "entry": entry
            })
            
            return entry_id
        
        raise Exception("Failed to add entry to dataset")
    
    def _generate_entry_id(self) -> str:
        """Generate unique entry ID"""
        timestamp = str(time.time())
        content = f"entry_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _update_indexes(self, dataset: Dataset, operation: str):
        """Update search indexes"""
        if operation == "create":
            self._add_to_indexes(dataset)
        elif operation == "delete":
            self._remove_from_indexes(dataset)
    
    def _add_to_indexes(self, dataset: Dataset):
        """Add dataset to all relevant indexes"""
        # By creator
        if dataset.creator not in self.indexes["by_creator"]:
            self.indexes["by_creator"][dataset.creator] = set()
        self.indexes["by_creator"][dataset.creator].add(dataset.dataset_id)
        
        # By type
        dataset_type = dataset.dataset_type.value
        if dataset_type not in self.indexes["by_type"]:
            self.indexes["by_type"][dataset_type] = set()
        self.indexes["by_type"][dataset_type].add(dataset.dataset_id)
        
        # By tags
        for tag in dataset.tags:
            if tag not in self.indexes["by_tag"]:
                self.indexes["by_tag"][tag] = set()
            self.indexes["by_tag"][tag].add(dataset.dataset_id)
        
        # By quality
        quality = dataset.quality_level.value
        if quality not in self.indexes["by_quality"]:
            self.indexes["by_quality"][quality] = set()
        self.indexes["by_quality"][quality].add(dataset.dataset_id)
        
        # By license
        license_key = dataset.license
        if license_key not in self.indexes["by_license"]:
            self.indexes["by_license"][license_key] = set()
        self.indexes["by_license"][license_key].add(dataset.dataset_id)
    
    def _remove_from_indexes(self, dataset: Dataset):
        """Remove dataset from all indexes"""
        dataset_id = dataset.dataset_id
        
        # Remove from all indexes
        for index_type in self.indexes:
            if dataset_id in self.indexes[index_type]:
                self.indexes[index_type][dataset_id].remove(dataset_id)
                
                # Clean up empty sets
                if not self.indexes[index_type][dataset_id]:
                    del self.indexes[index_type][dataset_id]
    
    def _update_entry_indexes(self, dataset_id: str, entry: DatasetEntry, operation: str):
        """Update entry-specific indexes"""
        # This would handle entry-level indexing
        # For now, just log the operation
        logger.debug(f"Entry index update: {operation} for {entry.entry_id} in {dataset_id}")
    
    async def search_datasets(self, query: str, filters: Dict[str, Any] = None) -> List[Dataset]:
        """Search datasets with filters"""
        filters = filters or {}
        results = []
        
        for dataset in self.datasets.values():
            if self._matches_query(dataset, query):
                if self._matches_filters(dataset, filters):
                    results.append(dataset)
        
        # Update metrics
        self.metrics["search_queries"] += 1
        
        return results
    
    def _matches_query(self, dataset: Dataset, query: str) -> bool:
        """Check if dataset matches search query"""
        if not query:
            return True
        
        query_lower = query.lower()
        
        return (query_lower in dataset.name.lower() or
                query_lower in dataset.description.lower() or
                any(query_lower in tag.lower() for tag in dataset.tags))
    
    def _matches_filters(self, dataset: Dataset, filters: Dict[str, Any]) -> bool:
        """Check if dataset matches all filters"""
        if not filters:
            return True
        
        # Filter by creator
        if "creator" in filters:
            if dataset.creator != filters["creator"]:
                return False
        
        # Filter by type
        if "dataset_type" in filters:
            if dataset.dataset_type != filters["dataset_type"]:
                return False
        
        # Filter by quality level
        if "quality_level" in filters:
            if dataset.quality_level != filters["quality_level"]:
                return False
        
        # Filter by tags
        if "tags" in filters:
            required_tags = set(filters["tags"])
            if not required_tags.issubset(dataset.tags):
                return False
        
        return True
    
    async def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID"""
        return self.datasets.get(dataset_id)
    
    async def federate_dataset(self, dataset_id: str, target_nodes: List[str]) -> bool:
        """Federate dataset to target nodes"""
        if dataset_id not in self.datasets:
            return False
        
        dataset = self.datasets[dataset_id]
        
        # Add to federation protocol
        success = await self.federation_protocol.initiate_federation(
            dataset_id, target_nodes
        )
        
        if success:
            dataset.federated_nodes.update(target_nodes)
            logger.info(f"Federated dataset {dataset_id} to {len(target_nodes)} nodes")
        
        return success
    
    async def sync_federated_datasets(self):
        """Synchronize federated datasets"""
        await self.federation_protocol.sync_all_datasets(self.datasets)
    
    async def _notify_subscribers(self, event_type: str, data: Any):
        """Notify all subscribers of an event"""
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        dataset_stats = []
        total_entries = 0
        total_size = 0
        
        for dataset in self.datasets.values():
            stats = dataset.get_statistics()
            dataset_stats.append(stats)
            total_entries += stats["total_entries"]
            total_size += stats["total_size_bytes"]
        
        return {
            "total_datasets": len(self.datasets),
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "index_stats": {
                index_type: len(datasets) 
                for index_type, datasets in self.indexes.items()
            },
            "metrics": self.metrics,
            "dataset_breakdown": dataset_stats
        }


class FederationProtocol:
    """Protocol for federating datasets across nodes"""
    
    def __init__(self):
        self.active_federations: Dict[str, Dict[str, Any]] = {}
        self.sync_queue = asyncio.Queue()
        self.is_running = False
    
    async def initiate_federation(self, dataset_id: str, target_nodes: List[str]) -> bool:
        """Initiate federation with target nodes"""
        federation_id = self._generate_federation_id()
        
        federation_info = {
            "federation_id": federation_id,
            "dataset_id": dataset_id,
            "target_nodes": target_nodes,
            "initiated_at": time.time(),
            "status": "pending",
            "sync_progress": {}
        }
        
        self.active_federations[federation_id] = federation_info
        
        # Start federation process
        asyncio.create_task(self._process_federation(federation_id))
        
        logger.info(f"Initiated federation {federation_id} for dataset {dataset_id}")
        return True
    
    def _generate_federation_id(self) -> str:
        """Generate unique federation ID"""
        timestamp = str(time.time())
        content = f"federation_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _process_federation(self, federation_id: str):
        """Process federation synchronization"""
        federation = self.active_federations[federation_id]
        
        try:
            # Mock federation process
            for node in federation["target_nodes"]:
                # Simulate sync with each node
                await asyncio.sleep(0.5)  # Simulate network latency
                
                federation["sync_progress"][node] = {
                    "status": "syncing",
                    "progress": 0,
                    "last_sync": time.time()
                }
            
            # Mark as completed
            federation["status"] = "completed"
            federation["completed_at"] = time.time()
            
            for node in federation["target_nodes"]:
                federation["sync_progress"][node]["status"] = "completed"
                federation["sync_progress"][node]["progress"] = 100
            
            logger.info(f"Completed federation {federation_id}")
            
        except Exception as e:
            federation["status"] = "failed"
            federation["error"] = str(e)
            logger.error(f"Federation {federation_id} failed: {e}")
    
    async def sync_all_datasets(self, datasets: Dict[str, Dataset]):
        """Sync all datasets with federated nodes"""
        for dataset_id, dataset in datasets.items():
            if dataset.federated_nodes:
                await self.initiate_federation(
                    dataset_id, 
                    list(dataset.federated_nodes)
                )
    
    def get_federation_status(self, federation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a federation"""
        return self.active_federations.get(federation_id)
    
    def get_all_federations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active federations"""
        return self.active_federations.copy()
