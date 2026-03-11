"""
Content Addressed Media Storage
Inspired by IPFS with CID generation and distributed storage
"""

import hashlib
import json
import time
import asyncio
import aiofiles
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os
import base64

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content that can be stored"""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    BINARY = "binary"
    METADATA = "metadata"
    MODEL = "model"
    DATASET = "dataset"


class StorageTier(Enum):
    """Storage tiers for different performance characteristics"""
    HOT = "hot"      # Frequently accessed, fast storage
    WARM = "warm"    # Moderately accessed
    COLD = "cold"    # Infrequently accessed, cheap storage
    ARCHIVE = "archive"  # Long-term storage


@dataclass
class ContentBlock:
    """Individual block of content"""
    def __init__(self, data: bytes, block_hash: str = None):
        self.data = data
        self.size = len(data)
        self.block_hash = block_hash or self._calculate_hash()
        self.timestamp = time.time()
        self.access_count = 0
        self.storage_tier = StorageTier.WARM
        self.replication_factor = 3  # Default replication
        self.checksum = self._calculate_checksum()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block data"""
        return hashlib.sha256(self.data).hexdigest()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification"""
        return hashlib.sha256(self.data).hexdigest()[:16]
    
    def access(self):
        """Record an access to this block"""
        self.access_count += 1
        self.timestamp = time.time()
        
        # Promote to hot tier if frequently accessed
        if self.access_count > 10:
            self.storage_tier = StorageTier.HOT
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "block_hash": self.block_hash,
            "size": self.size,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "storage_tier": self.storage_tier.value,
            "replication_factor": self.replication_factor,
            "checksum": self.checksum
        }


@dataclass
class ContentAddress:
    """Content-addressed identifier with metadata"""
    def __init__(self, cid: str, content_type: ContentType, 
                 size: int, checksum: str, metadata: Dict[str, Any] = None):
        self.cid = cid
        self.content_type = content_type
        self.size = size
        self.checksum = checksum
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.block_hashes: List[str] = []
        self.replication_nodes: List[str] = []
        self.access_control: Dict[str, Any] = {}
        self.license: str = "CC-BY-SA"
        self.encryption_key: Optional[str] = None
    
    def add_block(self, block_hash: str):
        """Add a block hash to this content"""
        if block_hash not in self.block_hashes:
            self.block_hashes.append(block_hash)
    
    def add_replication_node(self, node_id: str):
        """Add a replication node"""
        if node_id not in self.replication_nodes:
            self.replication_nodes.append(node_id)
    
    def is_accessible_by(self, node_id: str) -> bool:
        """Check if node has access to this content"""
        if not self.access_control:
            return True
        
        # Check access permissions
        permissions = self.access_control.get("permissions", [])
        node_permissions = self.access_control.get("node_permissions", {})
        
        return node_id in node_permissions.get("allowed", [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cid": self.cid,
            "content_type": self.content_type.value,
            "size": self.size,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "block_hashes": self.block_hashes,
            "replication_nodes": self.replication_nodes,
            "access_control": self.access_control,
            "license": self.license,
            "encryption_key": self.encryption_key
        }


class ContentAddressedStorage:
    """Content-addressed storage system inspired by IPFS"""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = storage_path
        self.blocks: Dict[str, ContentBlock] = {}
        self.content_index: Dict[str, ContentAddress] = {}
        self.block_size_limit = 1024 * 1024  # 1MB blocks
        self.replication_factor = 3
        self.garbage_collector = GarbageCollector()
        self.pin_manager = PinManager()
        self.cache = ContentCache()
        
        # Performance metrics
        self.metrics = {
            "blocks_stored": 0,
            "content_added": 0,
            "bytes_stored": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "replications": 0
        }
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        os.makedirs(f"{storage_path}/blocks", exist_ok=True)
        os.makedirs(f"{storage_path}/content", exist_ok=True)
        os.makedirs(f"{storage_path}/cache", exist_ok=True)
    
    async def store_content(self, data: Union[bytes, str], content_type: ContentType,
                        metadata: Dict[str, Any] = None, 
                        encryption_key: Optional[str] = None) -> str:
        """Store content and return CID"""
        try:
            # Convert to bytes if necessary
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Split into blocks
            blocks = await self._split_into_blocks(data)
            
            # Store blocks
            block_hashes = []
            for block in blocks:
                await self._store_block(block)
                block_hashes.append(block.block_hash)
            
            # Generate CID
            cid = self._generate_cid(data, content_type)
            
            # Create content address
            content_address = ContentAddress(
                cid=cid,
                content_type=content_type,
                size=len(data),
                checksum=hashlib.sha256(data).hexdigest(),
                metadata=metadata,
                encryption_key=encryption_key
            )
            
            # Add block hashes
            for block_hash in block_hashes:
                content_address.add_block(block_hash)
            
            # Store content address
            await self._store_content_address(content_address)
            
            # Pin if important
            if metadata and metadata.get("pin", False):
                await self.pin_manager.pin(cid)
            
            # Update metrics
            self.metrics["content_added"] += 1
            self.metrics["bytes_stored"] += len(data)
            
            logger.info(f"Stored content {cid} ({len(data)} bytes in {len(blocks)} blocks")
            return cid
            
        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise
    
    async def _split_into_blocks(self, data: bytes) -> List[ContentBlock]:
        """Split data into blocks of maximum size"""
        blocks = []
        
        for i in range(0, len(data), self.block_size_limit):
            block_data = data[i:i + self.block_size_limit]
            block = ContentBlock(block_data)
            blocks.append(block)
        
        return blocks
    
    async def _store_block(self, block: ContentBlock) -> bool:
        """Store a single block"""
        try:
            block_path = f"{self.storage_path}/blocks/{block.block_hash}"
            
            # Check if block already exists
            if os.path.exists(block_path):
                return True
            
            # Write block to disk
            async with aiofiles.open(block_path, 'wb') as f:
                await f.write(block.data)
            
            # Add to memory index
            self.blocks[block.block_hash] = block
            
            # Update metrics
            self.metrics["blocks_stored"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing block {block.block_hash}: {e}")
            return False
    
    async def _store_content_address(self, content: ContentAddress) -> bool:
        """Store content address metadata"""
        try:
            content_path = f"{self.storage_path}/content/{content.cid}.json"
            
            # Write content address to disk
            async with aiofiles.open(content_path, 'w') as f:
                await f.write(json.dumps(content.to_dict(), indent=2))
            
            # Add to memory index
            self.content_index[content.cid] = content
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing content address {content.cid}: {e}")
            return False
    
    def _generate_cid(self, data: bytes, content_type: ContentType) -> str:
        """Generate content identifier"""
        # Use multihash format (simplified version)
        hash_input = f"{content_type.value}{len(data)}{data}"
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Format as CID
        return f"cid-{content_hash[:32]}"
    
    async def retrieve_content(self, cid: str) -> Optional[bytes]:
        """Retrieve content by CID"""
        try:
            # Check cache first
            cached_content = await self.cache.get(cid)
            if cached_content:
                self.metrics["cache_hits"] += 1
                return cached_content
            
            self.metrics["cache_misses"] += 1
            
            # Get content address
            content_address = await self._get_content_address(cid)
            if not content_address:
                return None
            
            # Retrieve all blocks
            content_parts = []
            for block_hash in content_address.block_hashes:
                block = await self._get_block(block_hash)
                if block:
                    content_parts.append(block.data)
                    block.access()  # Record access for tier management
                else:
                    logger.warning(f"Block {block_hash} not found for CID {cid}")
                    return None
            
            # Reassemble content
            content = b''.join(content_parts)
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(content).hexdigest()
            if calculated_checksum != content_address.checksum:
                logger.error(f"Checksum mismatch for CID {cid}")
                return None
            
            # Cache the result
            await self.cache.put(cid, content)
            
            logger.info(f"Retrieved content {cid} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving content {cid}: {e}")
            return None
    
    async def _get_content_address(self, cid: str) -> Optional[ContentAddress]:
        """Get content address by CID"""
        # Check memory first
        if cid in self.content_index:
            return self.content_index[cid]
        
        # Load from disk
        try:
            content_path = f"{self.storage_path}/content/{cid}.json"
            async with aiofiles.open(content_path, 'r') as f:
                data = await f.read()
                content_dict = json.loads(data)
                
            content = ContentAddress(
                cid=content_dict["cid"],
                content_type=ContentType(content_dict["content_type"]),
                size=content_dict["size"],
                checksum=content_dict["checksum"],
                metadata=content_dict.get("metadata", {}),
                encryption_key=content_dict.get("encryption_key")
            )
            
            # Add block hashes
            for block_hash in content_dict.get("block_hashes", []):
                content.add_block(block_hash)
            
            # Add replication nodes
            for node_id in content_dict.get("replication_nodes", []):
                content.add_replication_node(node_id)
            
            # Add to memory index
            self.content_index[cid] = content
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading content address {cid}: {e}")
            return None
    
    async def _get_block(self, block_hash: str) -> Optional[ContentBlock]:
        """Get block by hash"""
        # Check memory first
        if block_hash in self.blocks:
            return self.blocks[block_hash]
        
        # Load from disk
        try:
            block_path = f"{self.storage_path}/blocks/{block_hash}"
            async with aiofiles.open(block_path, 'rb') as f:
                data = await f.read()
            
            block = ContentBlock(data, block_hash)
            
            # Add to memory index
            self.blocks[block_hash] = block
            
            return block
            
        except Exception as e:
            logger.error(f"Error loading block {block_hash}: {e}")
            return None
    
    async def pin_content(self, cid: str) -> bool:
        """Pin content to prevent garbage collection"""
        return await self.pin_manager.pin(cid)
    
    async def unpin_content(self, cid: str) -> bool:
        """Unpin content"""
        return await self.pin_manager.unpin(cid)
    
    async def replicate_content(self, cid: str, target_nodes: List[str]) -> int:
        """Replicate content to target nodes"""
        content_address = await self._get_content_address(cid)
        if not content_address:
            return 0
        
        successful_replications = 0
        
        for node_id in target_nodes:
            try:
                # Mock replication - in real implementation would use network transport
                await asyncio.sleep(0.1)  # Simulate network latency
                
                content_address.add_replication_node(node_id)
                successful_replications += 1
                
                logger.debug(f"Replicated content {cid} to node {node_id}")
                
            except Exception as e:
                logger.error(f"Failed to replicate {cid} to {node_id}: {e}")
        
        # Update content address
        await self._store_content_address(content_address)
        
        # Update metrics
        self.metrics["replications"] += successful_replications
        
        return successful_replications
    
    async def garbage_collect(self, max_age_days: int = 30) -> Dict[str, Any]:
        """Perform garbage collection of old content"""
        return await self.garbage_collector.collect(
            self.content_index, 
            self.blocks,
            max_age_days
        )
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_blocks = len(self.blocks)
        total_content = len(self.content_index)
        
        # Calculate storage usage
        total_block_size = sum(block.size for block in self.blocks.values())
        total_content_size = sum(content.size for content in self.content_index.values())
        
        # Calculate tier distribution
        tier_distribution = {}
        for block in self.blocks.values():
            tier = block.storage_tier.value
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        return {
            "total_blocks": total_blocks,
            "total_content": total_content,
            "total_block_size_bytes": total_block_size,
            "total_content_size_bytes": total_content_size,
            "block_size_limit": self.block_size_limit,
            "replication_factor": self.replication_factor,
            "tier_distribution": tier_distribution,
            "cache_stats": self.cache.get_stats(),
            "pin_stats": self.pin_manager.get_stats(),
            "metrics": self.metrics
        }


class PinManager:
    """Manages pinned content that shouldn't be garbage collected"""
    
    def __init__(self):
        self.pinned_content: Dict[str, Dict[str, Any]] = {}
    
    async def pin(self, cid: str) -> bool:
        """Pin content"""
        self.pinned_content[cid] = {
            "pinned_at": time.time(),
            "pin_count": self.pinned_content.get(cid, {}).get("pin_count", 0) + 1
        }
        return True
    
    async def unpin(self, cid: str) -> bool:
        """Unpin content"""
        if cid in self.pinned_content:
            pin_count = self.pinned_content[cid]["pin_count"] - 1
            if pin_count <= 0:
                del self.pinned_content[cid]
            else:
                self.pinned_content[cid]["pin_count"] = pin_count
            return True
        return False
    
    def is_pinned(self, cid: str) -> bool:
        """Check if content is pinned"""
        return cid in self.pinned_content
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pin statistics"""
        return {
            "total_pinned": len(self.pinned_content),
            "total_pins": sum(
                pin_info["pin_count"] 
                for pin_info in self.pinned_content.values()
            )
        }


class ContentCache:
    """LRU cache for frequently accessed content"""
    
    def __init__(self, max_size: int = 100, max_memory_mb: int = 512):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, Tuple[bytes, float]] = {}
        self.current_memory_bytes = 0
        self.hits = 0
        self.misses = 0
    
    async def get(self, cid: str) -> Optional[bytes]:
        """Get content from cache"""
        if cid in self.cache:
            content, timestamp = self.cache[cid]
            # Move to end (LRU)
            del self.cache[cid]
            self.cache[cid] = (content, timestamp)
            self.hits += 1
            return content
        
        self.misses += 1
        return None
    
    async def put(self, cid: str, content: bytes) -> bool:
        """Put content in cache"""
        content_size = len(content)
        
        # Check if we have space
        if (len(self.cache) >= self.max_size or 
            self.current_memory_bytes + content_size > self.max_memory_bytes):
            await self._evict_lru()
        
        # Add to cache
        self.cache[cid] = (content, time.time())
        self.current_memory_bytes += content_size
        
        return True
    
    async def _evict_lru(self):
        """Evict least recently used content"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_cid = min(
            self.cache.items(),
            key=lambda item: item[1][1]
        )[0]
        
        # Remove it
        content, _ = self.cache[lru_cid]
        del self.cache[lru_cid]
        self.current_memory_bytes -= len(content)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "current_memory_bytes": self.current_memory_bytes,
            "max_memory_bytes": self.max_memory_bytes,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class GarbageCollector:
    """Garbage collector for old content"""
    
    def __init__(self):
        self.collection_stats = {
            "content_collected": 0,
            "blocks_collected": 0,
            "bytes_freed": 0,
            "last_collection": None
        }
    
    async def collect(self, content_index: Dict[str, ContentAddress], 
                  blocks: Dict[str, ContentBlock], 
                  max_age_days: int) -> Dict[str, Any]:
        """Collect old content"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        content_to_remove = []
        blocks_to_remove = []
        
        # Find old content
        for cid, content in content_index.items():
            age = current_time - content.timestamp
            
            # Skip if pinned
            if hasattr(content, 'is_pinned') and content.is_pinned():
                continue
            
            if age > max_age_seconds:
                content_to_remove.append(cid)
                
                # Mark blocks for removal
                for block_hash in content.block_hashes:
                    if block_hash in blocks:
                        blocks_to_remove.append(block_hash)
        
        # Remove old content
        for cid in content_to_remove:
            del content_index[cid]
            self.collection_stats["content_collected"] += 1
        
        # Remove orphaned blocks
        for block_hash in blocks_to_remove:
            if block_hash in blocks:
                block_size = blocks[block_hash].size
                del blocks[block_hash]
                self.collection_stats["blocks_collected"] += 1
                self.collection_stats["bytes_freed"] += block_size
        
        self.collection_stats["last_collection"] = current_time
        
        logger.info(f"Garbage collected: {len(content_to_remove)} content items, "
                   f"{len(blocks_to_remove)} blocks, {self.collection_stats['bytes_freed']} bytes")
        
        return self.collection_stats
