"""
Enhanced Albrite Base Agent v2 - With Centralized AI Integration
Common base class for all Albrite agents with advanced capabilities
"""

import asyncio
import logging
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import pickle
from collections import defaultdict, deque

# Import centralized AI systems
from ...infrastructure.ai.centralized_model_manager import (
    centralized_model_manager, ModelRequest, ModelResponse, 
    ModelType, ModelProvider, RequestPriority
)
from ...infrastructure.ai.enhanced_ai_integration import (
    enhanced_ai_integration, TaskRequest, TaskResponse, 
    TaskComplexity, AIIntegrationMode
)
from ...infrastructure.caching.distributed_cache_system import distributed_cache
from ...infrastructure.memory.advanced_memory_system import (
    advanced_memory, MemoryType as AdvancedMemoryType, MemoryModality
)

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory storage"""
    SHORT_TERM = "short_term"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass
class MemoryItem:
    """Memory item for agent cognitive processes"""
    id: str
    content: Any
    memory_type: MemoryType
    timestamp: datetime
    importance: float = 0.5
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    related_agents: List[str] = field(default_factory=list)


@dataclass
class CacheItem:
    """Cached function result"""
    key: str
    value: Any
    timestamp: datetime
    access_count: int = 0
    ttl: Optional[timedelta] = None
    size_bytes: int = 0


class ModelCallType(Enum):
    """Types of AI model calls"""
    TEXT_GENERATION = "text_generation"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    ANALYSIS = "analysis"
    PREDICTION = "prediction"
    VISION = "vision"
    AUDIO = "audio"


@dataclass
class ModelRequest:
    """AI model request definition"""
    model_type: ModelCallType
    model_name: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: float = 30.0
    retry_count: int = 3


class AIModelManager:
    """Centralized AI model manager for efficient compute usage"""
    
    def __init__(self):
        self.model_cache = {}
        self.request_queue = asyncio.Queue()
        self.active_requests = {}
        self.request_history = deque(maxlen=1000)
        self.model_stats = defaultdict(lambda: {"calls": 0, "success": 0, "errors": 0})
        self.rate_limits = {}
        
    async def execute_model_request(self, request: ModelRequest) -> Any:
        """Execute model request with caching and rate limiting"""
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache first
        if cache_key in self.model_cache:
            cache_item = self.model_cache[cache_key]
            if not cache_item.ttl or datetime.now() < cache_item.timestamp + cache_item.ttl:
                cache_item.access_count += 1
                logger.debug(f"Cache hit for {request.model_type.value}")
                return cache_item.value
            else:
                del self.model_cache[cache_key]
        
        # Check rate limiting
        if not await self._check_rate_limit(request):
            await asyncio.sleep(1.0)  # Rate limit delay
        
        # Execute request
        try:
            result = await self._execute_request(request)
            
            # Cache result
            cache_item = CacheItem(
                key=cache_key,
                value=result,
                timestamp=datetime.now(),
                ttl=timedelta(minutes=30),  # 30 minute TTL
                size_bytes=len(pickle.dumps(result))
            )
            self.model_cache[cache_key] = cache_item
            
            # Update stats
            self.model_stats[request.model_type.value]["calls"] += 1
            self.model_stats[request.model_type.value]["success"] += 1
            
            # Log request
            self.request_history.append({
                "timestamp": datetime.now(),
                "model_type": request.model_type.value,
                "model_name": request.model_name,
                "success": True,
                "cache_hit": False
            })
            
            return result
            
        except Exception as e:
            self.model_stats[request.model_type.value]["errors"] += 1
            self.request_history.append({
                "timestamp": datetime.now(),
                "model_type": request.model_type.value,
                "model_name": request.model_name,
                "success": False,
                "error": str(e)
            })
            logger.error(f"Model request failed: {e}")
            raise
    
    def _generate_cache_key(self, request: ModelRequest) -> str:
        """Generate cache key for request"""
        key_data = f"{request.model_type.value}:{request.model_name}:{json.dumps(request.parameters, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _check_rate_limit(self, request: ModelRequest) -> bool:
        """Check if request is within rate limits"""
        model_key = f"{request.model_type.value}:{request.model_name}"
        now = datetime.now()
        
        if model_key not in self.rate_limits:
            self.rate_limits[model_key] = deque(maxlen=100)
        
        # Clean old requests (older than 1 minute)
        self.rate_limits[model_key] = deque(
            [req_time for req_time in self.rate_limits[model_key] 
             if now - req_time < timedelta(minutes=1)],
            maxlen=100
        )
        
        # Check if under limit (10 requests per minute per model)
        return len(self.rate_limits[model_key]) < 10
    
    async def _execute_request(self, request: ModelRequest) -> Any:
        """Execute the actual model request"""
        # Simulate model execution - replace with actual model calls
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Mock different model responses
        if request.model_type == ModelCallType.TEXT_GENERATION:
            return f"Generated text for {request.parameters.get('prompt', 'unknown')}"
        elif request.model_type == ModelCallType.CLASSIFICATION:
            return {"label": "positive", "confidence": 0.85}
        elif request.model_type == ModelCallType.EMBEDDING:
            return [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock embedding
        elif request.model_type == ModelCallType.SUMMARIZATION:
            return f"Summary of {request.parameters.get('text', 'unknown')}"
        else:
            return f"Result for {request.model_type.value}"
    
    def get_top_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top 10 most used models"""
        sorted_models = sorted(
            self.model_stats.items(),
            key=lambda x: x[1]["calls"],
            reverse=True
        )[:limit]
        
        return [
            {
                "model": model_type,
                "calls": stats["calls"],
                "success_rate": stats["success"] / max(stats["calls"], 1),
                "error_rate": stats["errors"] / max(stats["calls"], 1)
            }
            for model_type, stats in sorted_models
        ]


# Global AI model manager instance
ai_model_manager = AIModelManager()


def cache_function(ttl: timedelta = timedelta(minutes=5), max_size: int = 100):
    """Decorator for caching function results"""
    def decorator(func):
        cache = {}
        access_times = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            if cache_key in cache:
                cache_item = cache[cache_key]
                if datetime.now() - cache_item["timestamp"] < ttl:
                    cache_item["access_count"] += 1
                    return cache_item["value"]
                else:
                    del cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Clean cache if too large
            if len(cache) >= max_size:
                oldest_key = min(access_times.keys(), key=lambda k: access_times[k])
                del cache[oldest_key]
                del access_times[oldest_key]
            
            # Cache result
            cache[cache_key] = {
                "value": result,
                "timestamp": datetime.now(),
                "access_count": 1
            }
            access_times[cache_key] = datetime.now()
            
            return result
        
        return wrapper
    return decorator


class AlbriteBaseAgentV2:
    """Enhanced base agent with memory, caching, and AI model integration"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        
        # Memory systems
        self.short_term_memory = deque(maxlen=100)  # Last 100 items
        self.working_memory = {}  # Current task context
        self.episodic_memory = []  # Important experiences
        self.semantic_memory = {}  # Learned knowledge
        
        # Performance tracking
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "memory_usage": 0,
            "cache_hit_rate": 0.0
        }
        
        # Agent relationships
        self.related_agents = set()
        self.collaboration_history = []
        
        # Model usage tracking
        self.model_usage = defaultdict(int)
        self.favorite_models = {}
        
        # Initialize agent-specific attributes
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize agent-specific attributes - override in subclasses"""
        self.specialization = "general"
        self.core_skills = ["communication", "coordination"]
        self.genetic_traits = {}
        self.toggle_settings = {
            "enhanced_mode": True,
            "memory_enabled": True,
            "caching_enabled": True,
            "ai_models_enabled": True
        }
    
    async def add_memory(self, content: Any, memory_type: MemoryType = MemoryType.SHORT_TERM,
                       importance: float = 0.5, tags: List[str] = None,
                       related_agents: List[str] = None, expires_in: timedelta = None) -> str:
        """Add memory item to agent's memory systems"""
        memory_id = hashlib.md5(f"{self.agent_id}:{datetime.now().isoformat()}:{str(content)}".encode()).hexdigest()[:12]
        
        memory_item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            tags=tags or [],
            expires_at=datetime.now() + expires_in if expires_in else None,
            related_agents=related_agents or []
        )
        
        # Store in appropriate memory system
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term_memory.append(memory_item)
        elif memory_type == MemoryType.WORKING:
            self.working_memory[memory_id] = memory_item
        elif memory_type == MemoryType.EPISODIC:
            self.episodic_memory.append(memory_item)
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic_memory[memory_id] = memory_item
        
        # Update related agents
        if related_agents:
            self.related_agents.update(related_agents)
        
        return memory_id
    
    async def retrieve_memory(self, query: str = None, memory_type: MemoryType = None,
                           tags: List[str] = None, limit: int = 10) -> List[MemoryItem]:
        """Retrieve memories based on criteria"""
        all_memories = []
        
        # Collect memories from all systems
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            all_memories.extend(list(self.short_term_memory))
        if memory_type is None or memory_type == MemoryType.WORKING:
            all_memories.extend(list(self.working_memory.values()))
        if memory_type is None or memory_type == MemoryType.EPISODIC:
            all_memories.extend(self.episodic_memory)
        if memory_type is None or memory_type == MemoryType.SEMANTIC:
            all_memories.extend(list(self.semantic_memory.values()))
        
        # Filter memories
        filtered_memories = []
        for memory in all_memories:
            # Check expiration
            if memory.expires_at and datetime.now() > memory.expires_at:
                continue
            
            # Check query match
            if query:
                content_str = str(memory.content).lower()
                if query.lower() not in content_str:
                    continue
            
            # Check tags
            if tags and not any(tag in memory.tags for tag in tags):
                continue
            
            filtered_memories.append(memory)
        
        # Sort by importance and recency
        filtered_memories.sort(
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )
        
        return filtered_memories[:limit]
    
    async def call_ai_model(self, model_type: ModelType, model_name: str,
                          parameters: Dict[str, Any], priority: RequestPriority = RequestPriority.NORMAL) -> Any:
        """Call AI model with centralized management"""
        if not self.toggle_settings.get("ai_models_enabled", True):
            raise ValueError("AI models are disabled for this agent")
        
        # Track usage
        self.model_usage[f"{model_type.value}:{model_name}"] += 1
        
        # Create model request
        request = ModelRequest(
            request_id=f"{self.agent_id}:{datetime.now().isoformat()}",
            model_type=model_type,
            model_name=model_name,
            provider=self._get_provider_for_model(model_name),
            parameters=parameters,
            requesting_agent=self.agent_id,
            priority=priority,
            timeout=self.toggle_settings.get("model_timeout", 30.0)
        )
        
        # Execute through centralized manager
        response = await centralized_model_manager.execute_model_request(request)
        
        # Store in advanced memory system
        await advanced_memory.add_memory(
            content={
                "request": {
                    "model_type": model_type.value,
                    "model_name": model_name,
                    "parameters": parameters
                },
                "response": response.response_data if response.success else None,
                "success": response.success,
                "execution_time": response.execution_time,
                "cost": response.cost
            },
            memory_type=AdvancedMemoryType.EPISODIC,
            modality=MemoryModality.STRUCTURED,
            importance=0.6,
            tags=["ai_model", "computation", model_type.value],
            metadata={"agent": self.agent_id}
        )
        
        if not response.success:
            raise RuntimeError(f"AI model call failed: {response.error_message}")
        
        return response.response_data
    
    def _get_provider_for_model(self, model_name: str) -> ModelProvider:
        """Get provider for model name"""
        if model_name.startswith("gpt"):
            return ModelProvider.OPENAI
        elif model_name.startswith("claude"):
            return ModelProvider.ANTHROPIC
        elif "huggingface" in model_name.lower():
            return ModelProvider.HUGGINGFACE
        else:
            return ModelProvider.LOCAL
    
    async def execute_ai_task(self, task_type: str, description: str, input_data: Any,
                            complexity: TaskComplexity = TaskComplexity.MODERATE,
                            model_preferences: List[str] = None,
                            max_retries: int = 3) -> TaskResponse:
        """Execute AI task with enhanced integration"""
        # Create task request
        task_request = TaskRequest(
            task_id=f"{self.agent_id}:{task_type}:{datetime.now().isoformat()}",
            task_type=task_type,
            description=description,
            input_data=input_data,
            complexity=complexity,
            priority=RequestPriority.NORMAL,
            requesting_agent=self.agent_id,
            model_preferences=model_preferences or [],
            timeout=self.toggle_settings.get("task_timeout", 60.0),
            max_retries=max_retries,
            metadata={"agent": self.agent_id, "specialization": self.specialization}
        )
        
        # Execute through enhanced integration
        response = await enhanced_ai_integration.execute_task(task_request)
        
        # Store in advanced memory
        await advanced_memory.add_memory(
            content={
                "task": {
                    "type": task_type,
                    "description": description,
                    "complexity": complexity.value
                },
                "result": response.result if response.success else None,
                "success": response.success,
                "execution_time": response.execution_time,
                "cost": response.cost,
                "model_used": response.model_used
            },
            memory_type=AdvancedMemoryType.PROCEDURAL,
            modality=MemoryModality.STRUCTURED,
            importance=0.7,
            tags=["ai_task", "computation", task_type],
            metadata={"agent": self.agent_id}
        )
        
        return response
    
    async def add_memory(self, content: Any, memory_type: MemoryType = MemoryType.SHORT_TERM,
                       importance: float = 0.5, tags: List[str] = None,
                       related_agents: List[str] = None, expires_in: timedelta = None) -> str:
        """Add memory item using advanced memory system"""
        # Map legacy memory types to advanced memory types
        memory_type_mapping = {
            MemoryType.SHORT_TERM: AdvancedMemoryType.WORKING,
            MemoryType.WORKING: AdvancedMemoryType.WORKING,
            MemoryType.EPISODIC: AdvancedMemoryType.EPISODIC,
            MemoryType.SEMANTIC: AdvancedMemoryType.SEMANTIC
        }
        
        advanced_type = memory_type_mapping.get(memory_type, AdvancedMemoryType.WORKING)
        
        # Add to advanced memory system
        memory_id = await advanced_memory.add_memory(
            content=content,
            memory_type=advanced_type,
            modality=MemoryModality.TEXT if isinstance(content, str) else MemoryModality.STRUCTURED,
            importance=importance,
            tags=tags or [],
            related_memories=related_agents or [],
            metadata={"agent": self.agent_id, "legacy_type": memory_type.value}
        )
        
        # Also store in legacy system for backward compatibility
        legacy_memory_id = hashlib.md5(f"{self.agent_id}:{datetime.now().isoformat()}:{str(content)}".encode()).hexdigest()[:12]
        
        memory_item = MemoryItem(
            id=legacy_memory_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            tags=tags or [],
            expires_at=datetime.now() + expires_in if expires_in else None,
            related_agents=related_agents or []
        )
        
        # Store in appropriate legacy memory system
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term_memory.append(memory_item)
        elif memory_type == MemoryType.WORKING:
            self.working_memory[legacy_memory_id] = memory_item
        elif memory_type == MemoryType.EPISODIC:
            self.episodic_memory.append(memory_item)
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic_memory[legacy_memory_id] = memory_item
        
        # Update related agents
        if related_agents:
            self.related_agents.update(related_agents)
        
        return memory_id
    
    async def retrieve_memory(self, query: str = None, memory_type: MemoryType = None,
                           tags: List[str] = None, limit: int = 10) -> List[MemoryItem]:
        """Retrieve memories using advanced memory system"""
        # Map legacy memory types to advanced memory types
        memory_type_mapping = {
            MemoryType.SHORT_TERM: AdvancedMemoryType.WORKING,
            MemoryType.WORKING: AdvancedMemoryType.WORKING,
            MemoryType.EPISODIC: AdvancedMemoryType.EPISODIC,
            MemoryType.SEMANTIC: AdvancedMemoryType.SEMANTIC
        }
        
        advanced_type = memory_type_mapping.get(memory_type) if memory_type else None
        
        # Retrieve from advanced memory system
        advanced_memories = await advanced_memory.retrieve_memory(
            query=query,
            memory_type=advanced_type,
            tags=tags,
            importance_threshold=0.0,
            limit=limit
        )
        
        # Convert advanced memories to legacy format for backward compatibility
        legacy_memories = []
        for adv_memory in advanced_memories:
            # Reverse map memory type
            reverse_mapping = {
                AdvancedMemoryType.WORKING: MemoryType.WORKING,
                AdvancedMemoryType.EPISODIC: MemoryType.EPISODIC,
                AdvancedMemoryType.SEMANTIC: MemoryType.SEMANTIC,
                AdvancedMemoryType.PROCEDURAL: MemoryType.WORKING,
                AdvancedMemoryType.LONG_TERM: MemoryType.SEMANTIC
            }
            
            legacy_type = reverse_mapping.get(adv_memory.memory_type, MemoryType.WORKING)
            
            legacy_memory = MemoryItem(
                id=adv_memory.id,
                content=adv_memory.content,
                memory_type=legacy_type,
                timestamp=adv_memory.created_at,
                importance=adv_memory.importance,
                access_count=adv_memory.access_count,
                tags=adv_memory.tags,
                expires_at=adv_memory.expires_at,
                related_agents=adv_memory.related_memories
            )
            
            legacy_memories.append(legacy_memory)
        
        return legacy_memories
    
    async def analyze_data(self, data: Any, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze data with centralized AI integration"""
        # Use distributed cache first
        cache_key = f"analysis:{self.agent_id}:{hashlib.md5(str(data).encode()).hexdigest()}"
        cached_result = await distributed_cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Execute through enhanced AI integration
        response = await self.execute_ai_task(
            task_type="data_analysis",
            description=f"Analyze data of type: {analysis_type}",
            input_data={"data": data, "type": analysis_type},
            complexity=TaskComplexity.MODERATE
        )
        
        if not response.success:
            raise RuntimeError(f"Data analysis failed: {response.error_message}")
        
        result = {
            "analysis": response.result,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.85,
            "model_used": response.model_used,
            "execution_time": response.execution_time
        }
        
        # Cache result
        await distributed_cache.put(cache_key, result, ttl=timedelta(minutes=10))
        
        return result
    
    async def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """Generate text with centralized AI integration"""
        # Use distributed cache first
        cache_key = f"text_gen:{self.agent_id}:{hashlib.md5(prompt.encode()).hexdigest()}"
        cached_result = await distributed_cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Execute through enhanced AI integration
        response = await self.execute_ai_task(
            task_type="text_generation",
            description=f"Generate text based on prompt",
            input_data={"prompt": prompt, "max_length": max_length},
            complexity=TaskComplexity.SIMPLE
        )
        
        if not response.success:
            raise RuntimeError(f"Text generation failed: {response.error_message}")
        
        result = response.result
        
        # Cache result
        await distributed_cache.put(cache_key, result, ttl=timedelta(minutes=15))
        
        return result
    
    async def classify_content(self, content: Any, classes: List[str]) -> Dict[str, Any]:
        """Classify content with centralized AI integration"""
        # Use distributed cache first
        content_hash = hashlib.md5(str(content).encode()).hexdigest()
        classes_hash = hashlib.md5("|".join(classes).encode()).hexdigest()
        cache_key = f"classify:{self.agent_id}:{content_hash}:{classes_hash}"
        
        cached_result = await distributed_cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Execute through enhanced AI integration
        response = await self.execute_ai_task(
            task_type="classification",
            description=f"Classify content into categories",
            input_data={"content": content, "classes": classes},
            complexity=TaskComplexity.MODERATE
        )
        
        if not response.success:
            raise RuntimeError(f"Content classification failed: {response.error_message}")
        
        result = {
            "classification": response.result,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.85,
            "model_used": response.model_used
        }
        
        # Cache result
        await distributed_cache.put(cache_key, result, ttl=timedelta(minutes=5))
        
        return result
    
    async def coordinate_with_agent(self, agent_id: str, task: Dict[str, Any]) -> Any:
        """Coordinate with related agent"""
        if agent_id not in self.related_agents:
            logger.warning(f"Agent {agent_id} not in related agents list")
        
        # Add to collaboration history
        self.collaboration_history.append({
            "agent_id": agent_id,
            "task": task,
            "timestamp": datetime.now(),
            "status": "initiated"
        })
        
        # Add to memory
        await self.add_memory(
            content={"collaboration": {"agent": agent_id, "task": task}},
            memory_type=MemoryType.EPISODIC,
            importance=0.7,
            tags=["collaboration", "coordination"],
            related_agents=[agent_id]
        )
        
        # In a real implementation, this would communicate with the other agent
        # For now, return a mock response
        return {
            "status": "coordinated",
            "agent": agent_id,
            "result": f"Task coordinated with {agent_id}"
        }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with memory and caching"""
        start_time = time.time()
        
        # Add task to working memory
        await self.add_memory(
            content={"task": task, "status": "started"},
            memory_type=MemoryType.WORKING,
            importance=0.8,
            tags=["task", "execution"]
        )
        
        try:
            # Execute task based on type
            task_type = task.get("type", "general")
            
            if task_type == "analysis":
                result = await self.analyze_data(task.get("data"), task.get("analysis_type"))
            elif task_type == "generation":
                result = await self.generate_text(task.get("prompt"), task.get("max_length", 100))
            elif task_type == "classification":
                result = await self.classify_content(task.get("content"), task.get("classes"))
            elif task_type == "collaboration":
                result = await self.coordinate_with_agent(task.get("target_agent"), task.get("collaboration_task"))
            else:
                result = await self.execute_specialized_task(task)
            
            # Update working memory
            await self.add_memory(
                content={"task": task, "result": result, "status": "completed"},
                memory_type=MemoryType.WORKING,
                importance=0.8,
                tags=["task", "completed"]
            )
            
            # Update metrics
            execution_time = time.time() - start_time
            self.performance_metrics["tasks_completed"] += 1
            self.performance_metrics["average_response_time"] = (
                (self.performance_metrics["average_response_time"] * (self.performance_metrics["tasks_completed"] - 1) + execution_time) /
                self.performance_metrics["tasks_completed"]
            )
            
            return {
                "success": True,
                "result": result,
                "agent": self.agent_name,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Add error to memory
            await self.add_memory(
                content={"task": task, "error": str(e), "status": "failed"},
                memory_type=MemoryType.EPISODIC,
                importance=0.6,
                tags=["task", "error"]
            )
            
            logger.error(f"Task execution failed for {self.agent_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_specialized_task(self, task: Dict[str, Any]) -> Any:
        """Execute specialized task - override in subclasses"""
        return await self.analyze_data(task.get("data"), "specialized")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of agent's memory systems"""
        return {
            "short_term_count": len(self.short_term_memory),
            "working_memory_count": len(self.working_memory),
            "episodic_memory_count": len(self.episodic_memory),
            "semantic_memory_count": len(self.semantic_memory),
            "total_memories": len(self.short_term_memory) + len(self.working_memory) + len(self.episodic_memory) + len(self.semantic_memory),
            "related_agents": list(self.related_agents),
            "collaboration_count": len(self.collaboration_history)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            **self.performance_metrics,
            "model_usage": dict(self.model_usage),
            "top_models": sorted(self.model_usage.items(), key=lambda x: x[1], reverse=True)[:5],
            "memory_summary": self.get_memory_summary()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "specialization": self.specialization,
            "core_skills": self.core_skills,
            "genetic_traits": self.genetic_traits,
            "toggle_settings": self.toggle_settings,
            "performance_metrics": self.get_performance_metrics(),
            "related_agents": list(self.related_agents),
            "timestamp": datetime.now().isoformat()
        }
