"""
Centralized Model Manager for Albrite Agents
Advanced model request handling, response caching, performance tracking, and rate limiting
"""

import asyncio
import logging
import json
import time
import hashlib
import statistics
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import aiohttp
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Model type categories"""
    TEXT_GENERATION = "text_generation"
    TEXT_EMBEDDING = "text_embedding"
    IMAGE_GENERATION = "image_generation"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    CUSTOM = "custom"


class ModelProvider(Enum):
    """Model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    AZURE = "azure"
    GOOGLE = "google"
    CUSTOM = "custom"


class RequestPriority(Enum):
    """Request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class ModelRequest:
    """Model request structure"""
    request_id: str
    model_type: ModelType
    model_name: str
    provider: ModelProvider
    parameters: Dict[str, Any]
    requesting_agent: str
    priority: RequestPriority = RequestPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Model response structure"""
    request_id: str
    model_name: str
    provider: ModelProvider
    response_data: Any
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    cached: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    model_name: str
    provider: ModelProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_percentage: float = 100.0
    performance_score: float = 0.0


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    tokens_per_minute: int = 10000
    cost_per_hour: float = 10.0
    concurrent_requests: int = 10


class ResponseCache:
    """Advanced response caching system"""
    
    def __init__(self, max_size: int = 10000, ttl_minutes: int = 60):
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache = {}  # key -> (response, timestamp)
        self.access_times = {}  # key -> last access time
        self.hit_count = 0
        self.miss_count = 0
        self.lock = asyncio.Lock()
    
    def _generate_cache_key(self, request: ModelRequest) -> str:
        """Generate cache key from request"""
        key_data = {
            "model_type": request.model_type.value,
            "model_name": request.model_name,
            "provider": request.provider.value,
            "parameters": request.parameters
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    async def get(self, request: ModelRequest) -> Optional[ModelResponse]:
        """Get cached response"""
        cache_key = self._generate_cache_key(request)
        
        async with self.lock:
            if cache_key in self.cache:
                response, timestamp = self.cache[cache_key]
                
                # Check TTL
                if datetime.now() - timestamp > self.ttl:
                    del self.cache[cache_key]
                    self.access_times.pop(cache_key, None)
                    self.miss_count += 1
                    return None
                
                # Update access time
                self.access_times[cache_key] = datetime.now()
                self.hit_count += 1
                
                # Return cached response
                cached_response = ModelResponse(**response.__dict__)
                cached_response.cached = True
                return cached_response
            
            self.miss_count += 1
            return None
    
    async def put(self, request: ModelRequest, response: ModelResponse) -> bool:
        """Cache response"""
        cache_key = self._generate_cache_key(request)
        
        async with self.lock:
            # Check if eviction is needed
            if len(self.cache) >= self.max_size and cache_key not in self.cache:
                await self._evict()
            
            # Store response
            self.cache[cache_key] = (response, datetime.now())
            self.access_times[cache_key] = datetime.now()
            
            return True
    
    async def _evict(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        
        # Remove from cache
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "ttl_minutes": self.ttl.total_seconds() / 60
        }


class RateLimiter:
    """Advanced rate limiting system"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_history = defaultdict(deque)  # agent_id -> deque of timestamps
        self.token_history = defaultdict(deque)  # agent_id -> deque of (timestamp, tokens)
        self.cost_history = defaultdict(deque)   # agent_id -> deque of (timestamp, cost)
        self.concurrent_requests = defaultdict(int)  # agent_id -> concurrent count
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, agent_id: str, tokens: int = 0, cost: float = 0.0) -> tuple[bool, str]:
        """Check if request is within rate limits"""
        async with self.lock:
            now = datetime.now()
            current_time = now.timestamp()
            
            # Check concurrent requests
            if self.concurrent_requests[agent_id] >= self.config.concurrent_requests:
                return False, f"Concurrent request limit exceeded ({self.config.concurrent_requests})"
            
            # Clean old entries
            await self._clean_old_entries(agent_id, now)
            
            # Check requests per minute
            minute_ago = now - timedelta(minutes=1)
            recent_requests = [t for t in self.request_history[agent_id] if t > minute_ago]
            if len(recent_requests) >= self.config.requests_per_minute:
                return False, f"Requests per minute limit exceeded ({self.config.requests_per_minute})"
            
            # Check requests per hour
            hour_ago = now - timedelta(hours=1)
            recent_hour_requests = [t for t in self.request_history[agent_id] if t > hour_ago]
            if len(recent_hour_requests) >= self.config.requests_per_hour:
                return False, f"Requests per hour limit exceeded ({self.config.requests_per_hour})"
            
            # Check requests per day
            day_ago = now - timedelta(days=1)
            recent_day_requests = [t for t in self.request_history[agent_id] if t > day_ago]
            if len(recent_day_requests) >= self.config.requests_per_day:
                return False, f"Requests per day limit exceeded ({self.config.requests_per_day})"
            
            # Check tokens per minute
            minute_ago = now - timedelta(minutes=1)
            recent_tokens = [(t, tok) for t, tok in self.token_history[agent_id] if t > minute_ago]
            total_tokens = sum(tok for t, tok in recent_tokens)
            if total_tokens + tokens > self.config.tokens_per_minute:
                return False, f"Tokens per minute limit exceeded ({self.config.tokens_per_minute})"
            
            # Check cost per hour
            hour_ago = now - timedelta(hours=1)
            recent_costs = [(t, c) for t, c in self.cost_history[agent_id] if t > hour_ago]
            total_cost = sum(c for t, c in recent_costs)
            if total_cost + cost > self.config.cost_per_hour:
                return False, f"Cost per hour limit exceeded (${self.config.cost_per_hour})"
            
            # Record this request
            self.request_history[agent_id].append(now)
            self.token_history[agent_id].append((now, tokens))
            self.cost_history[agent_id].append((now, cost))
            self.concurrent_requests[agent_id] += 1
            
            return True, "Request allowed"
    
    async def release_request(self, agent_id: str):
        """Release concurrent request count"""
        async with self.lock:
            if self.concurrent_requests[agent_id] > 0:
                self.concurrent_requests[agent_id] -= 1
    
    async def _clean_old_entries(self, agent_id: str, now: datetime):
        """Clean old entries from history"""
        # Clean request history
        day_ago = now - timedelta(days=1)
        self.request_history[agent_id] = deque(
            [t for t in self.request_history[agent_id] if t > day_ago]
        )
        
        # Clean token history
        minute_ago = now - timedelta(minutes=1)
        self.token_history[agent_id] = deque(
            [(t, tok) for t, tok in self.token_history[agent_id] if t > minute_ago]
        )
        
        # Clean cost history
        hour_ago = now - timedelta(hours=1)
        self.cost_history[agent_id] = deque(
            [(t, c) for t, c in self.cost_history[agent_id] if t > hour_ago]
        )
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get rate limiting statistics for agent"""
        now = datetime.now()
        
        # Calculate current usage
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        requests_minute = len([t for t in self.request_history[agent_id] if t > minute_ago])
        requests_hour = len([t for t in self.request_history[agent_id] if t > hour_ago])
        requests_day = len([t for t in self.request_history[agent_id] if t > day_ago])
        
        tokens_minute = sum(tok for t, tok in self.token_history[agent_id] if t > minute_ago)
        cost_hour = sum(c for t, c in self.cost_history[agent_id] if t > hour_ago)
        
        return {
            "concurrent_requests": self.concurrent_requests[agent_id],
            "requests_per_minute": requests_minute,
            "requests_per_hour": requests_hour,
            "requests_per_day": requests_day,
            "tokens_per_minute": tokens_minute,
            "cost_per_hour": cost_hour,
            "limits": {
                "requests_per_minute": self.config.requests_per_minute,
                "requests_per_hour": self.config.requests_per_hour,
                "requests_per_day": self.config.requests_per_day,
                "tokens_per_minute": self.config.tokens_per_minute,
                "cost_per_hour": self.config.cost_per_hour,
                "concurrent_requests": self.config.concurrent_requests
            }
        }


class PerformanceTracker:
    """Advanced performance tracking system"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.request_history = defaultdict(lambda: deque(maxlen=history_size))
        self.response_times = defaultdict(lambda: deque(maxlen=history_size))
        self.error_history = defaultdict(lambda: deque(maxlen=history_size))
        self.cost_history = defaultdict(lambda: deque(maxlen=history_size))
        self.token_history = defaultdict(lambda: deque(maxlen=history_size))
        self.model_metrics = {}  # model_name -> ModelMetrics
        self.agent_metrics = defaultdict(dict)  # agent_id -> model_name -> metrics
        self.lock = asyncio.Lock()
    
    async def record_request(self, request: ModelRequest):
        """Record model request"""
        async with self.lock:
            self.request_history[request.model_name].append({
                "timestamp": request.created_at,
                "agent": request.requesting_agent,
                "priority": request.priority.value,
                "parameters": request.parameters
            })
    
    async def record_response(self, response: ModelResponse):
        """Record model response"""
        async with self.lock:
            # Record response time
            self.response_times[response.model_name].append(response.execution_time)
            
            # Record error if any
            if not response.success:
                self.error_history[response.model_name].append({
                    "timestamp": response.created_at,
                    "error": response.error_message
                })
            
            # Record cost and tokens
            self.cost_history[response.model_name].append(response.cost)
            self.token_history[response.model_name].append(response.tokens_used)
            
            # Update model metrics
            await self._update_model_metrics(response)
    
    async def _update_model_metrics(self, response: ModelResponse):
        """Update model performance metrics"""
        model_key = f"{response.model_name}:{response.provider.value}"
        
        if model_key not in self.model_metrics:
            self.model_metrics[model_key] = ModelMetrics(
                model_name=response.model_name,
                provider=response.provider
            )
        
        metrics = self.model_metrics[model_key]
        
        # Update basic counters
        metrics.total_requests += 1
        if response.success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update response time
        if self.response_times[response.model_name]:
            metrics.average_response_time = statistics.mean(self.response_times[response.model_name])
        
        # Update tokens and cost
        metrics.total_tokens_used += response.tokens_used
        metrics.total_cost += response.cost
        
        # Update rates
        metrics.error_rate = metrics.failed_requests / metrics.total_requests
        metrics.last_request_time = response.created_at
        
        # Calculate performance score
        metrics.performance_score = self._calculate_performance_score(metrics)
    
    def _calculate_performance_score(self, metrics: ModelMetrics) -> float:
        """Calculate overall performance score (0-100)"""
        # Success rate component (40%)
        success_rate = (metrics.successful_requests / metrics.total_requests) * 100 if metrics.total_requests > 0 else 0
        success_score = min(success_rate, 100) * 0.4
        
        # Response time component (30%) - lower is better
        avg_time = metrics.average_response_time
        time_score = max(0, (10 - avg_time) / 10 * 100) * 0.3 if avg_time > 0 else 30
        
        # Cost efficiency component (20%) - lower cost per request is better
        avg_cost = metrics.total_cost / metrics.total_requests if metrics.total_requests > 0 else 0
        cost_score = max(0, (0.1 - avg_cost) / 0.1 * 100) * 0.2 if avg_cost > 0 else 20
        
        # Uptime component (10%)
        uptime_score = metrics.uptime_percentage * 0.1
        
        return success_score + time_score + cost_score + uptime_score
    
    def get_model_metrics(self, model_name: str, provider: ModelProvider) -> Optional[ModelMetrics]:
        """Get metrics for specific model"""
        model_key = f"{model_name}:{provider.value}"
        return self.model_metrics.get(model_key)
    
    def get_all_metrics(self) -> Dict[str, ModelMetrics]:
        """Get all model metrics"""
        return self.model_metrics.copy()
    
    def get_top_models(self, limit: int = 10, sort_by: str = "performance_score") -> List[ModelMetrics]:
        """Get top performing models"""
        all_metrics = list(self.model_metrics.values())
        
        if sort_by == "performance_score":
            all_metrics.sort(key=lambda m: m.performance_score, reverse=True)
        elif sort_by == "total_requests":
            all_metrics.sort(key=lambda m: m.total_requests, reverse=True)
        elif sort_by == "success_rate":
            all_metrics.sort(key=lambda m: m.successful_requests / m.total_requests if m.total_requests > 0 else 0, reverse=True)
        elif sort_by == "average_response_time":
            all_metrics.sort(key=lambda m: m.average_response_time)
        elif sort_by == "total_cost":
            all_metrics.sort(key=lambda m: m.total_cost)
        
        return all_metrics[:limit]
    
    def get_agent_usage(self, agent_id: str) -> Dict[str, Any]:
        """Get usage statistics for specific agent"""
        agent_requests = []
        
        for model_name, requests in self.request_history.items():
            for request in requests:
                if request["agent"] == agent_id:
                    agent_requests.append({
                        "model": model_name,
                        "timestamp": request["timestamp"],
                        "priority": request["priority"]
                    })
        
        return {
            "total_requests": len(agent_requests),
            "requests_by_model": defaultdict(int),
            "requests_by_priority": defaultdict(int),
            "recent_activity": sorted(agent_requests, key=lambda x: x["timestamp"], reverse=True)[:10]
        }


class CentralizedModelManager:
    """Centralized model request handling and management"""
    
    def __init__(self, cache_size: int = 10000, cache_ttl_minutes: int = 60):
        self.cache = ResponseCache(max_size=cache_size, ttl_minutes=cache_ttl_minutes)
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.performance_tracker = PerformanceTracker()
        self.request_queue = asyncio.Queue()
        self.active_requests = {}  # request_id -> ModelRequest
        self.model_configs = {}  # model_name -> configuration
        self.provider_configs = {}  # provider -> configuration
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.background_tasks = []
        
        # Start background services
        self._start_background_services()
    
    def _start_background_services(self):
        """Start background services"""
        # Request processor
        self.background_tasks.append(
            asyncio.create_task(self._request_processor())
        )
        
        # Metrics updater
        self.background_tasks.append(
            asyncio.create_task(self._metrics_updater())
        )
        
        # Cache cleanup
        self.background_tasks.append(
            asyncio.create_task(self._cache_cleanup())
        )
    
    async def execute_model_request(self, request: ModelRequest) -> ModelResponse:
        """Execute model request with caching and rate limiting"""
        # Check cache first
        cached_response = await self.cache.get(request)
        if cached_response:
            await self.performance_tracker.record_request(request)
            await self.performance_tracker.record_response(cached_response)
            return cached_response
        
        # Check rate limits
        allowed, message = await self.rate_limiter.check_rate_limit(
            request.requesting_agent,
            tokens=request.parameters.get("max_tokens", 100),
            cost=request.parameters.get("estimated_cost", 0.01)
        )
        
        if not allowed:
            return ModelResponse(
                request_id=request.request_id,
                model_name=request.model_name,
                provider=request.provider,
                response_data=None,
                success=False,
                error_message=f"Rate limit exceeded: {message}"
            )
        
        # Record request
        await self.performance_tracker.record_request(request)
        
        # Execute request
        response = await self._execute_request(request)
        
        # Cache response if successful
        if response.success:
            await self.cache.put(request, response)
        
        # Record response
        await self.performance_tracker.record_response(response)
        
        # Release rate limit
        await self.rate_limiter.release_request(request.requesting_agent)
        
        return response
    
    async def _execute_request(self, request: ModelRequest) -> ModelResponse:
        """Execute actual model request"""
        start_time = time.time()
        
        try:
            # Get model configuration
            model_config = self.model_configs.get(request.model_name)
            if not model_config:
                raise ValueError(f"Model configuration not found: {request.model_name}")
            
            # Execute based on provider
            if request.provider == ModelProvider.OPENAI:
                response_data = await self._execute_openai_request(request, model_config)
            elif request.provider == ModelProvider.ANTHROPIC:
                response_data = await self._execute_anthropic_request(request, model_config)
            elif request.provider == ModelProvider.HUGGINGFACE:
                response_data = await self._execute_huggingface_request(request, model_config)
            elif request.provider == ModelProvider.LOCAL:
                response_data = await self._execute_local_request(request, model_config)
            else:
                raise ValueError(f"Unsupported provider: {request.provider}")
            
            execution_time = time.time() - start_time
            
            return ModelResponse(
                request_id=request.request_id,
                model_name=request.model_name,
                provider=request.provider,
                response_data=response_data,
                success=True,
                execution_time=execution_time,
                tokens_used=response_data.get("usage", {}).get("total_tokens", 0),
                cost=response_data.get("cost", 0.0)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return ModelResponse(
                request_id=request.request_id,
                model_name=request.model_name,
                provider=request.provider,
                response_data=None,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def _execute_openai_request(self, request: ModelRequest, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OpenAI API request"""
        # Mock implementation - replace with actual OpenAI API call
        await asyncio.sleep(0.5)  # Simulate API latency
        
        return {
            "text": f"OpenAI response for {request.model_name}",
            "usage": {"total_tokens": 150},
            "cost": 0.002
        }
    
    async def _execute_anthropic_request(self, request: ModelRequest, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Anthropic API request"""
        # Mock implementation - replace with actual Anthropic API call
        await asyncio.sleep(0.6)
        
        return {
            "text": f"Anthropic response for {request.model_name}",
            "usage": {"total_tokens": 200},
            "cost": 0.003
        }
    
    async def _execute_huggingface_request(self, request: ModelRequest, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HuggingFace API request"""
        # Mock implementation - replace with actual HuggingFace API call
        await asyncio.sleep(0.8)
        
        return {
            "text": f"HuggingFace response for {request.model_name}",
            "usage": {"total_tokens": 100},
            "cost": 0.001
        }
    
    async def _execute_local_request(self, request: ModelRequest, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute local model request"""
        # Mock implementation - replace with actual local model execution
        await asyncio.sleep(0.3)
        
        return {
            "text": f"Local model response for {request.model_name}",
            "usage": {"total_tokens": 80},
            "cost": 0.0005
        }
    
    async def _request_processor(self):
        """Background request processor"""
        while True:
            try:
                # Process requests from queue
                request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                
                # Execute request
                response = await self.execute_model_request(request)
                
                # Handle response (callback, etc.)
                await self._handle_response(request, response)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Request processor error: {e}")
                await asyncio.sleep(1.0)
    
    async def _metrics_updater(self):
        """Background metrics updater"""
        while True:
            try:
                # Update performance metrics
                await self._update_performance_metrics()
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Metrics updater error: {e}")
                await asyncio.sleep(30)
    
    async def _cache_cleanup(self):
        """Background cache cleanup"""
        while True:
            try:
                # Clean expired cache entries
                await self._cleanup_expired_cache()
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _handle_response(self, request: ModelRequest, response: ModelResponse):
        """Handle model response"""
        # This could include callbacks, logging, etc.
        if response.success:
            logger.info(f"Model request completed: {request.model_name} in {response.execution_time:.2f}s")
        else:
            logger.error(f"Model request failed: {request.model_name} - {response.error_message}")
    
    async def _update_performance_metrics(self):
        """Update performance metrics"""
        # This could include additional calculations, aggregations, etc.
        pass
    
    async def _cleanup_expired_cache(self):
        """Clean expired cache entries"""
        # Response cache handles TTL automatically
        pass
    
    def register_model_config(self, model_name: str, config: Dict[str, Any]):
        """Register model configuration"""
        self.model_configs[model_name] = config
    
    def register_provider_config(self, provider: ModelProvider, config: Dict[str, Any]):
        """Register provider configuration"""
        self.provider_configs[provider] = config
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
    
    def get_rate_limit_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get rate limiting statistics for agent"""
        return self.rate_limiter.get_agent_stats(agent_id)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "model_metrics": self.performance_tracker.get_all_metrics(),
            "top_models": self.performance_tracker.get_top_models(),
            "cache_stats": self.get_cache_stats()
        }
    
    async def shutdown(self):
        """Shutdown the model manager"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        logger.info("Centralized Model Manager shutdown complete")


# Global model manager instance
centralized_model_manager = CentralizedModelManager()
