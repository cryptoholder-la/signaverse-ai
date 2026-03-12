"""
Advanced Distributed Cache System for Albrite Agents
High-performance, multi-tier caching with Redis, local cache, and intelligent eviction
"""

import asyncio
import logging
import json
import pickle
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
import redis.asyncio as redis
import aioredis

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels"""
    L1_LOCAL = "l1_local"      # Fast local memory cache
    L2_REDIS = "l2_redis"      # Distributed Redis cache
    L3_PERSISTENT = "l3_persistent"  # Persistent storage


class CachePolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"                # Least Recently Used
    LFU = "lfu"                # Least Frequently Used
    TTL = "ttl"                # Time To Live
    ADAPTIVE = "adaptive"       # Adaptive based on access patterns


@dataclass
class CacheItem:
    """Cache item with metadata"""
    key: str
    value: Any
    tier: CacheTier
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[timedelta] = None
    size_bytes: int = 0
    priority: int = 1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Cache statistics"""
    tier: CacheTier
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    item_count: int = 0
    hit_rate: float = 0.0
    avg_access_time: float = 0.0


class LocalCache:
    """High-performance local memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000, policy: CachePolicy = CachePolicy.LRU):
        self.max_size = max_size
        self.policy = policy
        self.cache = OrderedDict()
        self.access_times = {}
        self.access_counts = defaultdict(int)
        self.stats = CacheStats(tier=CacheTier.L1_LOCAL)
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheItem]:
        """Get item from local cache"""
        start_time = time.time()
        
        async with self.lock:
            if key in self.cache:
                item = self.cache[key]
                item.last_accessed = datetime.now()
                item.access_count += 1
                
                # Update access tracking
                self.access_times[key] = time.time()
                self.access_counts[key] += 1
                
                # Move to end for LRU
                if self.policy == CachePolicy.LRU:
                    self.cache.move_to_end(key)
                
                self.stats.hits += 1
                self.stats.avg_access_time = (
                    (self.stats.avg_access_time * (self.stats.hits - 1) + 
                     (time.time() - start_time)) / self.stats.hits
                )
                
                return item
            else:
                self.stats.misses += 1
                return None
    
    async def put(self, key: str, value: Any, ttl: Optional[timedelta] = None,
                 priority: int = 1, tags: List[str] = None,
                 metadata: Dict[str, Any] = None) -> bool:
        """Put item in local cache"""
        async with self.lock:
            # Check if eviction is needed
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict()
            
            # Create cache item
            item = CacheItem(
                key=key,
                value=value,
                tier=CacheTier.L1_LOCAL,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=ttl,
                size_bytes=len(pickle.dumps(value)),
                priority=priority,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.cache[key] = item
            self.access_times[key] = time.time()
            self.access_counts[key] = 1
            
            # Update stats
            self.stats.item_count = len(self.cache)
            self.stats.size_bytes = sum(item.size_bytes for item in self.cache.values())
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete item from local cache"""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.access_times.pop(key, None)
                self.access_counts.pop(key, None)
                
                # Update stats
                self.stats.item_count = len(self.cache)
                self.stats.size_bytes = sum(item.size_bytes for item in self.cache.values())
                
                return True
            return False
    
    async def _evict(self):
        """Evict items based on policy"""
        if not self.cache:
            return
        
        if self.policy == CachePolicy.LRU:
            # Remove least recently used item
            self.cache.popitem(last=False)
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used item
            lfu_key = min(self.access_counts.items(), key=lambda x: x[1])
            key_to_remove = lfu_key[0]
            del self.cache[key_to_remove]
            self.access_counts.pop(key_to_remove, None)
            self.access_times.pop(key_to_remove, None)
        
        self.stats.evictions += 1
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        total_requests = self.stats.hits + self.stats.misses
        self.stats.hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
        return self.stats


class RedisCache:
    """Distributed Redis cache with clustering support"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379",
                 key_prefix: str = "albrite:", ttl: timedelta = timedelta(hours=1)):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl = ttl
        self.redis_client = None
        self.stats = CacheStats(tier=CacheTier.L2_REDIS)
        self.connection_pool = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis cache")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[CacheItem]:
        """Get item from Redis cache"""
        if not self.redis_client:
            return None
        
        start_time = time.time()
        redis_key = f"{self.key_prefix}{key}"
        
        try:
            # Get cached data
            cached_data = await self.redis_client.get(redis_key)
            
            if cached_data:
                # Deserialize cache item
                item_data = pickle.loads(cached_data)
                item = CacheItem(**item_data)
                
                # Update access tracking
                item.last_accessed = datetime.now()
                item.access_count += 1
                
                # Update access time in Redis
                await self.redis_client.setex(
                    redis_key,
                    item.ttl or self.default_ttl,
                    pickle.dumps(item.__dict__)
                )
                
                self.stats.hits += 1
                self.stats.avg_access_time = (
                    (self.stats.avg_access_time * (self.stats.hits - 1) + 
                     (time.time() - start_time)) / self.stats.hits
                )
                
                return item
            else:
                self.stats.misses += 1
                return None
                
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats.misses += 1
            return None
    
    async def put(self, key: str, value: Any, ttl: Optional[timedelta] = None,
                 priority: int = 1, tags: List[str] = None,
                 metadata: Dict[str, Any] = None) -> bool:
        """Put item in Redis cache"""
        if not self.redis_client:
            return False
        
        redis_key = f"{self.key_prefix}{key}"
        
        try:
            # Create cache item
            item = CacheItem(
                key=key,
                value=value,
                tier=CacheTier.L2_REDIS,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=ttl or self.default_ttl,
                size_bytes=len(pickle.dumps(value)),
                priority=priority,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                redis_key,
                item.ttl,
                pickle.dumps(item.__dict__)
            )
            
            # Update stats
            info = await self.redis_client.info()
            self.stats.item_count = info.get("db0", {}).get("keys", 0)
            self.stats.size_bytes = info.get("used_memory", 0)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis put error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from Redis cache"""
        if not self.redis_client:
            return False
        
        redis_key = f"{self.key_prefix}{key}"
        
        try:
            result = await self.redis_client.delete(redis_key)
            
            # Update stats
            info = await self.redis_client.info()
            self.stats.item_count = info.get("db0", {}).get("keys", 0)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear_by_tags(self, tags: List[str]) -> int:
        """Clear items by tags"""
        if not self.redis_client:
            return 0
        
        try:
            # Get all keys
            keys = await self.redis_client.keys(f"{self.key_prefix}*")
            cleared_count = 0
            
            for key in keys:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    item_data = pickle.loads(cached_data)
                    item_tags = item_data.get("tags", [])
                    
                    if any(tag in item_tags for tag in tags):
                        await self.redis_client.delete(key)
                        cleared_count += 1
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Redis clear by tags error: {e}")
            return 0
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        total_requests = self.stats.hits + self.stats.misses
        self.stats.hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
        return self.stats


class DistributedCacheSystem:
    """Advanced multi-tier distributed cache system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379",
                 local_cache_size: int = 1000, redis_ttl: timedelta = timedelta(hours=1)):
        self.local_cache = LocalCache(max_size=local_cache_size)
        self.redis_cache = RedisCache(redis_url=redis_url, ttl=redis_ttl)
        self.cache_stats = defaultdict(CacheStats)
        self.access_patterns = defaultdict(list)
        self.prefetch_queue = asyncio.Queue()
        self.background_tasks = []
        
        # Start background services
        self._start_background_services()
    
    async def initialize(self):
        """Initialize cache system"""
        await self.redis_cache.connect()
        logger.info("Distributed cache system initialized")
    
    async def shutdown(self):
        """Shutdown cache system"""
        await self.redis_cache.disconnect()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        logger.info("Distributed cache system shutdown")
    
    def _start_background_services(self):
        """Start background services"""
        # Prefetch service
        self.background_tasks.append(
            asyncio.create_task(self._prefetch_service())
        )
        
        # Statistics update service
        self.background_tasks.append(
            asyncio.create_task(self._stats_update_service())
        )
        
        # Cache warming service
        self.background_tasks.append(
            asyncio.create_task(self._cache_warming_service())
        )
    
    async def get(self, key: str, use_tiers: List[CacheTier] = None) -> Optional[Any]:
        """Get value from cache with tier fallback"""
        if use_tiers is None:
            use_tiers = [CacheTier.L1_LOCAL, CacheTier.L2_REDIS]
        
        # Track access pattern
        self.access_patterns[key].append(time.time())
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-100:]
        
        # Try L1 (local) cache first
        if CacheTier.L1_LOCAL in use_tiers:
            item = await self.local_cache.get(key)
            if item:
                # Check TTL
                if item.ttl and datetime.now() - item.created_at > item.ttl:
                    await self.local_cache.delete(key)
                else:
                    return item.value
        
        # Try L2 (Redis) cache
        if CacheTier.L2_REDIS in use_tiers:
            item = await self.redis_cache.get(key)
            if item:
                # Check TTL
                if item.ttl and datetime.now() - item.created_at > item.ttl:
                    await self.redis_cache.delete(key)
                else:
                    # Promote to L1 cache
                    await self.local_cache.put(
                        key, item.value, item.ttl, item.priority,
                        item.tags, item.metadata
                    )
                    return item.value
        
        return None
    
    async def put(self, key: str, value: Any, ttl: Optional[timedelta] = None,
                 priority: int = 1, tags: List[str] = None,
                 metadata: Dict[str, Any] = None,
                 tiers: List[CacheTier] = None) -> bool:
        """Put value in cache with tier selection"""
        if tiers is None:
            tiers = [CacheTier.L1_LOCAL, CacheTier.L2_REDIS]
        
        success = True
        
        # Put in L1 (local) cache
        if CacheTier.L1_LOCAL in tiers:
            success &= await self.local_cache.put(key, value, ttl, priority, tags, metadata)
        
        # Put in L2 (Redis) cache
        if CacheTier.L2_REDIS in tiers:
            success &= await self.redis_cache.put(key, value, ttl, priority, tags, metadata)
        
        return success
    
    async def delete(self, key: str, tiers: List[CacheTier] = None) -> bool:
        """Delete from cache tiers"""
        if tiers is None:
            tiers = [CacheTier.L1_LOCAL, CacheTier.L2_REDIS]
        
        success = True
        
        # Delete from L1 (local) cache
        if CacheTier.L1_LOCAL in tiers:
            success &= await self.local_cache.delete(key)
        
        # Delete from L2 (Redis) cache
        if CacheTier.L2_REDIS in tiers:
            success &= await self.redis_cache.delete(key)
        
        return success
    
    async def clear_by_tags(self, tags: List[str]) -> int:
        """Clear items by tags across all tiers"""
        cleared_count = 0
        
        # Clear from local cache
        local_keys_to_delete = []
        for key, item in self.local_cache.cache.items():
            if any(tag in item.tags for tag in tags):
                local_keys_to_delete.append(key)
        
        for key in local_keys_to_delete:
            await self.local_cache.delete(key)
            cleared_count += 1
        
        # Clear from Redis cache
        cleared_count += await self.redis_cache.clear_by_tags(tags)
        
        return cleared_count
    
    async def get_by_tags(self, tags: List[str], limit: int = 100) -> List[CacheItem]:
        """Get items by tags"""
        results = []
        
        # Search local cache
        for item in self.local_cache.cache.values():
            if any(tag in item.tags for tag in tags):
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    async def _prefetch_service(self):
        """Background prefetch service"""
        while True:
            try:
                # Get prefetch item from queue
                key = await asyncio.wait_for(self.prefetch_queue.get(), timeout=1.0)
                
                # Prefetch from Redis to local cache
                item = await self.redis_cache.get(key)
                if item:
                    await self.local_cache.put(
                        key, item.value, item.ttl, item.priority,
                        item.tags, item.metadata
                    )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Prefetch service error: {e}")
                await asyncio.sleep(1.0)
    
    async def _stats_update_service(self):
        """Background statistics update service"""
        while True:
            try:
                # Update combined statistics
                local_stats = self.local_cache.get_stats()
                redis_stats = self.redis_cache.get_stats()
                
                self.cache_stats[CacheTier.L1_LOCAL] = local_stats
                self.cache_stats[CacheTier.L2_REDIS] = redis_stats
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Stats update service error: {e}")
                await asyncio.sleep(5.0)
    
    async def _cache_warming_service(self):
        """Background cache warming service"""
        while True:
            try:
                # Analyze access patterns and prefetch hot items
                for key, access_times in self.access_patterns.items():
                    if len(access_times) >= 5:  # Minimum accesses to consider
                        # Calculate access frequency
                        recent_accesses = [t for t in access_times if time.time() - t < 300]  # Last 5 minutes
                        
                        if len(recent_accesses) >= 3:  # High frequency
                            # Add to prefetch queue
                            await self.prefetch_queue.put(key)
                
                await asyncio.sleep(60)  # Analyze every minute
                
            except Exception as e:
                logger.error(f"Cache warming service error: {e}")
                await asyncio.sleep(30.0)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        local_stats = self.cache_stats[CacheTier.L1_LOCAL]
        redis_stats = self.cache_stats[CacheTier.L2_REDIS]
        
        total_hits = local_stats.hits + redis_stats.hits
        total_misses = local_stats.misses + redis_stats.misses
        total_requests = total_hits + total_misses
        
        return {
            "local_cache": {
                "hits": local_stats.hits,
                "misses": local_stats.misses,
                "hit_rate": local_stats.hit_rate,
                "item_count": local_stats.item_count,
                "size_bytes": local_stats.size_bytes,
                "evictions": local_stats.evictions,
                "avg_access_time": local_stats.avg_access_time
            },
            "redis_cache": {
                "hits": redis_stats.hits,
                "misses": redis_stats.misses,
                "hit_rate": redis_stats.hit_rate,
                "item_count": redis_stats.item_count,
                "size_bytes": redis_stats.size_bytes,
                "avg_access_time": redis_stats.avg_access_time
            },
            "combined": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_requests": total_requests,
                "overall_hit_rate": total_hits / total_requests if total_requests > 0 else 0,
                "total_items": local_stats.item_count + redis_stats.item_count,
                "total_size_bytes": local_stats.size_bytes + redis_stats.size_bytes
            },
            "access_patterns": {
                "tracked_keys": len(self.access_patterns),
                "prefetch_queue_size": self.prefetch_queue.qsize()
            }
        }


# Global distributed cache instance
distributed_cache = DistributedCacheSystem()
