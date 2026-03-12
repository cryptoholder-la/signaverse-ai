"""
Albrite Centralized AI Manager - Top 10 Model Request Management
Centralized system for managing AI model calls, reducing compute overhead and optimizing performance
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import hashlib

logger = logging.getLogger(__name__)


class ModelPriority(Enum):
    """Priority levels for model requests"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ModelRequest:
    """Enhanced model request with comprehensive metadata"""
    request_id: str
    model_type: str
    model_name: str
    parameters: Dict[str, Any]
    priority: ModelPriority
    requesting_agent: str
    timestamp: datetime
    timeout: float = 30.0
    retry_count: int = 3
    estimated_tokens: int = 0
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Enhanced model response with performance metrics"""
    request_id: str
    model_type: str
    model_name: str
    result: Any
    execution_time: float
    tokens_used: int
    cache_hit: bool
    success: bool
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelStats:
    """Comprehensive model statistics"""
    model_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time: float = 0.0
    total_tokens_used: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    cache_hit_rate: float = 0.0
    last_used: Optional[datetime] = None
    peak_usage_time: Optional[datetime] = None
    peak_concurrent_requests: int = 0


class AlbriteCentralizedAIManager:
    """Centralized AI model management system with advanced optimization"""
    
    def __init__(self, max_concurrent_requests: int = 10, cache_ttl: timedelta = timedelta(minutes=30)):
        self.max_concurrent_requests = max_concurrent_requests
        self.cache_ttl = cache_ttl
        
        # Request management
        self.request_queue = asyncio.PriorityQueue()
        self.active_requests = {}
        self.completed_requests = deque(maxlen=10000)
        
        # Caching system
        self.response_cache = {}
        self.cache_access_patterns = defaultdict(int)
        
        # Model statistics and tracking
        self.model_stats = defaultdict(ModelStats)
        self.top_models = []
        self.agent_usage = defaultdict(lambda: defaultdict(int))
        
        # Performance monitoring
        self.performance_metrics = {
            "total_requests": 0,
            "total_cache_hits": 0,
            "total_cache_misses": 0,
            "average_response_time": 0.0,
            "requests_per_second": 0.0,
            "concurrent_requests": 0
        }
        
        # Rate limiting and quotas
        self.rate_limits = defaultdict(deque)
        self.agent_quotas = defaultdict(lambda: {"requests": 0, "tokens": 0, "window_start": datetime.now()})
        
        # Top 10 model tracking
        self.model_rankings = defaultdict(lambda: {"score": 0.0, "usage": 0, "performance": 0.0})
        
        # Start background tasks
        self._background_tasks = []
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Cache cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cache_cleanup_task())
        )
        
        # Statistics update task
        self._background_tasks.append(
            asyncio.create_task(self._statistics_update_task())
        )
        
        # Performance monitoring task
        self._background_tasks.append(
            asyncio.create_task(self._performance_monitoring_task())
        )
    
    async def execute_model_request(self, model_type: str, model_name: str, parameters: Dict[str, Any],
                                 requesting_agent: str, priority: ModelPriority = ModelPriority.MEDIUM,
                                 **kwargs) -> ModelResponse:
        """Execute model request with centralized management"""
        # Generate request ID
        request_id = hashlib.md5(
            f"{model_type}:{model_name}:{str(parameters)}:{requesting_agent}:{datetime.now().isoformat()}"
            .encode()
        ).hexdigest()[:16]
        
        # Create request object
        request = ModelRequest(
            request_id=request_id,
            model_type=model_type,
            model_name=model_name,
            parameters=parameters,
            priority=priority,
            requesting_agent=requesting_agent,
            timestamp=datetime.now(),
            **kwargs
        )
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            cached_response.cache_hit = True
            self._update_cache_stats(model_name, hit=True)
            return cached_response
        
        # Check rate limits and quotas
        if not await self._check_rate_limit(request):
            raise Exception(f"Rate limit exceeded for agent {requesting_agent}")
        
        if not await self._check_quota(request):
            raise Exception(f"Quota exceeded for agent {requesting_agent}")
        
        # Add to queue
        await self.request_queue.put((priority.value, request.timestamp.timestamp(), request))
        
        # Wait for completion
        response = await self._wait_for_completion(request_id)
        
        # Update statistics
        self._update_model_stats(request, response)
        self._update_agent_usage(requesting_agent, model_name, response)
        self._update_top_models(model_name, response)
        
        return response
    
    async def _wait_for_completion(self, request_id: str, timeout: float = 60.0) -> ModelResponse:
        """Wait for request completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if request_id in self.completed_requests:
                response = self.completed_requests[request_id]
                del self.completed_requests[request_id]
                return response
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"Request {request_id} timed out")
    
    async def _process_requests(self):
        """Process requests from queue"""
        while True:
            try:
                # Check if we can accept more requests
                if len(self.active_requests) >= self.max_concurrent_requests:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get next request
                try:
                    priority, timestamp, request = await asyncio.wait_for(
                        self.request_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Execute request
                asyncio.create_task(self._execute_single_request(request))
                
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_single_request(self, request: ModelRequest) -> ModelResponse:
        """Execute a single model request"""
        start_time = time.time()
        
        try:
            # Add to active requests
            self.active_requests[request.request_id] = request
            self.performance_metrics["concurrent_requests"] = len(self.active_requests)
            
            # Execute the actual model call
            result = await self._call_model(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create response
            response = ModelResponse(
                request_id=request.request_id,
                model_type=request.model_type,
                model_name=request.model_name,
                result=result,
                execution_time=execution_time,
                tokens_used=self._estimate_tokens(request, result),
                cache_hit=False,
                success=True,
                performance_metrics={
                    "priority": request.priority.value,
                    "agent": request.requesting_agent,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Cache response
            cache_key = self._generate_cache_key(request)
            self._cache_response(cache_key, response)
            
        except Exception as e:
            execution_time = time.time() - start_time
            response = ModelResponse(
                request_id=request.request_id,
                model_type=request.model_type,
                model_name=request.model_name,
                result=None,
                execution_time=execution_time,
                tokens_used=0,
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
        
        # Remove from active requests
        if request.request_id in self.active_requests:
            del self.active_requests[request.request_id]
        
        # Add to completed requests
        self.completed_requests[request.request_id] = response
        
        return response
    
    async def _call_model(self, request: ModelRequest) -> Any:
        """Call the actual model - replace with real model implementations"""
        # Simulate model execution
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Mock different model responses based on type
        if request.model_type == "text_generation":
            return f"Generated text for: {request.parameters.get('prompt', 'unknown prompt')}"
        elif request.model_type == "classification":
            return {"label": "positive", "confidence": 0.85}
        elif request.model_type == "embedding":
            return [0.1, 0.2, 0.3, 0.4, 0.5] * 128  # Mock embedding
        elif request.model_type == "summarization":
            return f"Summary of: {request.parameters.get('text', 'unknown text')[:100]}..."
        elif request.model_type == "analysis":
            return {"analysis": "comprehensive analysis result", "confidence": 0.9}
        elif request.model_type == "translation":
            return f"Translated: {request.parameters.get('text', 'unknown text')}"
        else:
            return f"Result for {request.model_type} model"
    
    def _generate_cache_key(self, request: ModelRequest) -> str:
        """Generate cache key for request"""
        key_data = f"{request.model_type}:{request.model_name}:{json.dumps(request.parameters, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[ModelResponse]:
        """Get cached response if valid"""
        if cache_key not in self.response_cache:
            return None
        
        cached_item = self.response_cache[cache_key]
        if datetime.now() - cached_item["timestamp"] > self.cache_ttl:
            del self.response_cache[cache_key]
            return None
        
        self.cache_access_patterns[cache_key] += 1
        return cached_item["response"]
    
    def _cache_response(self, cache_key: str, response: ModelResponse):
        """Cache response"""
        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }
    
    async def _check_rate_limit(self, request: ModelRequest) -> bool:
        """Check if request is within rate limits"""
        agent_key = f"{request.requesting_agent}:{request.model_name}"
        now = datetime.now()
        
        # Clean old requests (older than 1 minute)
        self.rate_limits[agent_key] = deque(
            [req_time for req_time in self.rate_limits[agent_key]
             if now - req_time < timedelta(minutes=1)],
            maxlen=100
        )
        
        # Check if under limit (20 requests per minute per agent per model)
        if len(self.rate_limits[agent_key]) >= 20:
            return False
        
        # Add current request
        self.rate_limits[agent_key].append(now)
        return True
    
    async def _check_quota(self, request: ModelRequest) -> bool:
        """Check if request is within agent quota"""
        agent_quota = self.agent_quotas[request.requesting_agent]
        now = datetime.now()
        
        # Reset quota window if needed (hourly)
        if now - agent_quota["window_start"] > timedelta(hours=1):
            agent_quota["requests"] = 0
            agent_quota["tokens"] = 0
            agent_quota["window_start"] = now
        
        # Check quotas (1000 requests, 100000 tokens per hour)
        if agent_quota["requests"] >= 1000 or agent_quota["tokens"] >= 100000:
            return False
        
        # Update quota usage
        agent_quota["requests"] += 1
        agent_quota["tokens"] += request.estimated_tokens or self._estimate_tokens(request, None)
        
        return True
    
    def _estimate_tokens(self, request: ModelRequest, result: Any) -> int:
        """Estimate token usage"""
        # Simple estimation - replace with actual token counting
        if request.model_type == "text_generation":
            return len(str(result).split()) if result else 0
        elif request.model_type == "embedding":
            return len(request.parameters.get("text", "").split())
        else:
            return 100  # Default estimate
    
    def _update_model_stats(self, request: ModelRequest, response: ModelResponse):
        """Update model statistics"""
        stats = self.model_stats[request.model_name]
        stats.total_requests += 1
        stats.total_execution_time += response.execution_time
        stats.total_tokens_used += response.tokens_used
        stats.last_used = datetime.now()
        
        if response.success:
            stats.successful_requests += 1
        else:
            stats.failed_requests += 1
        
        if response.cache_hit:
            stats.cache_hits += 1
        else:
            stats.cache_misses += 1
        
        # Update calculated metrics
        stats.average_response_time = stats.total_execution_time / stats.total_requests
        stats.success_rate = stats.successful_requests / stats.total_requests
        stats.cache_hit_rate = stats.cache_hits / (stats.cache_hits + stats.cache_misses) if (stats.cache_hits + stats.cache_misses) > 0 else 0
    
    def _update_agent_usage(self, agent: str, model: str, response: ModelResponse):
        """Update agent usage statistics"""
        self.agent_usage[agent][model] += 1
    
    def _update_top_models(self, model_name: str, response: ModelResponse):
        """Update top models ranking"""
        ranking = self.model_rankings[model_name]
        
        # Calculate score based on usage, performance, and success rate
        usage_score = self.model_stats[model_name].total_requests
        performance_score = 1.0 / (self.model_stats[model_name].average_response_time + 0.001)
        success_score = self.model_stats[model_name].success_rate
        
        ranking["score"] = (usage_score * 0.4) + (performance_score * 0.3) + (success_score * 0.3)
        ranking["usage"] = usage_score
        ranking["performance"] = performance_score
        
        # Update top models list
        self.top_models = sorted(
            self.model_rankings.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:10]
    
    def _update_cache_stats(self, model_name: str, hit: bool):
        """Update cache statistics"""
        if hit:
            self.performance_metrics["total_cache_hits"] += 1
        else:
            self.performance_metrics["total_cache_misses"] += 1
    
    async def _cache_cleanup_task(self):
        """Background task to clean expired cache entries"""
        while True:
            try:
                now = datetime.now()
                expired_keys = [
                    key for key, item in self.response_cache.items()
                    if now - item["timestamp"] > self.cache_ttl
                ]
                
                for key in expired_keys:
                    del self.response_cache[key]
                
                if expired_keys:
                    logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _statistics_update_task(self):
        """Background task to update statistics"""
        while True:
            try:
                # Update performance metrics
                total_requests = sum(stats.total_requests for stats in self.model_stats.values())
                successful_requests = sum(stats.successful_requests for stats in self.model_stats.values())
                
                self.performance_metrics["total_requests"] = total_requests
                self.performance_metrics["average_response_time"] = (
                    sum(stats.total_execution_time for stats in self.model_stats.values()) /
                    max(total_requests, 1)
                )
                self.performance_metrics["requests_per_second"] = total_requests / 3600  # Per hour
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Statistics update error: {e}")
                await asyncio.sleep(30)
    
    async def _performance_monitoring_task(self):
        """Background task for performance monitoring"""
        while True:
            try:
                # Monitor peak concurrent requests
                current_concurrent = len(self.active_requests)
                if current_concurrent > self.performance_metrics.get("peak_concurrent_requests", 0):
                    self.performance_metrics["peak_concurrent_requests"] = current_concurrent
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    def get_top_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top models by usage and performance"""
        return [
            {
                "model_name": model_name,
                "score": ranking["score"],
                "usage": ranking["usage"],
                "performance": ranking["performance"],
                "stats": {
                    "total_requests": self.model_stats[model_name].total_requests,
                    "success_rate": self.model_stats[model_name].success_rate,
                    "average_response_time": self.model_stats[model_name].average_response_time,
                    "cache_hit_rate": self.model_stats[model_name].cache_hit_rate
                }
            }
            for model_name, ranking in self.top_models[:limit]
        ]
    
    def get_agent_usage_report(self, agent: str) -> Dict[str, Any]:
        """Get detailed usage report for an agent"""
        agent_stats = self.agent_usage.get(agent, {})
        quota_info = self.agent_quotas.get(agent, {})
        
        return {
            "agent": agent,
            "model_usage": dict(agent_stats),
            "total_requests": sum(agent_stats.values()),
            "quota_used": quota_info.get("requests", 0),
            "quota_remaining": max(0, 1000 - quota_info.get("requests", 0)),
            "tokens_used": quota_info.get("tokens", 0),
            "tokens_remaining": max(0, 100000 - quota_info.get("tokens", 0)),
            "quota_window_start": quota_info.get("window_start", datetime.now()).isoformat()
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        return {
            "performance_metrics": self.performance_metrics,
            "cache_metrics": {
                "cache_size": len(self.response_cache),
                "cache_hit_rate": (
                    self.performance_metrics["total_cache_hits"] /
                    (self.performance_metrics["total_cache_hits"] + self.performance_metrics["total_cache_misses"])
                    if (self.performance_metrics["total_cache_hits"] + self.performance_metrics["total_cache_misses"]) > 0 else 0
                )
            },
            "queue_metrics": {
                "queue_size": self.request_queue.qsize(),
                "active_requests": len(self.active_requests),
                "max_concurrent": self.max_concurrent_requests
            },
            "model_count": len(self.model_stats),
            "top_models": self.get_top_models(5),
            "agent_count": len(self.agent_usage)
        }
    
    async def start_request_processor(self):
        """Start the request processor"""
        await self._process_requests()


# Global instance
albrite_ai_manager = AlbriteCentralizedAIManager()
