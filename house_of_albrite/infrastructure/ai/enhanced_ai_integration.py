"""
Enhanced AI Integration for Albrite Agents
Centralized AI integration with advanced features and optimizations
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import numpy as np

from .centralized_model_manager import (
    centralized_model_manager, ModelRequest, ModelResponse, 
    ModelType, ModelProvider, RequestPriority
)

logger = logging.getLogger(__name__)


class AIIntegrationMode(Enum):
    """AI integration modes"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BATCH = "batch"
    STREAMING = "streaming"
    HYBRID = "hybrid"


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    VERY_COMPLEX = 4
    EXTREME = 5


@dataclass
class TaskRequest:
    """Enhanced task request structure"""
    task_id: str
    task_type: str
    description: str
    input_data: Any
    complexity: TaskComplexity
    priority: RequestPriority
    requesting_agent: str
    model_preferences: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResponse:
    """Enhanced task response structure"""
    task_id: str
    success: bool
    result: Any
    execution_time: float
    model_used: str
    provider_used: ModelProvider
    tokens_consumed: int
    cost: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class ModelSelector:
    """Intelligent model selection system"""
    
    def __init__(self):
        self.model_capabilities = {}  # model_name -> capabilities
        self.model_performance = {}   # model_name -> performance metrics
        self.task_model_mapping = {}  # task_type -> preferred models
        self.cost_thresholds = {}     # agent_id -> max_cost_per_task
        self.performance_weights = {
            "accuracy": 0.4,
            "speed": 0.3,
            "cost": 0.2,
            "reliability": 0.1
        }
    
    def register_model_capability(self, model_name: str, capabilities: Dict[str, Any]):
        """Register model capabilities"""
        self.model_capabilities[model_name] = capabilities
    
    def update_model_performance(self, model_name: str, performance_metrics: Dict[str, float]):
        """Update model performance metrics"""
        self.model_performance[model_name] = performance_metrics
    
    def set_task_model_mapping(self, task_type: str, models: List[str]):
        """Set preferred models for task type"""
        self.task_model_mapping[task_type] = models
    
    def set_cost_threshold(self, agent_id: str, max_cost: float):
        """Set cost threshold for agent"""
        self.cost_thresholds[agent_id] = max_cost
    
    def select_best_model(self, task_request: TaskRequest) -> tuple[str, ModelProvider]:
        """Select best model for task"""
        # Get candidate models
        candidate_models = self.task_model_mapping.get(task_request.task_type, [])
        
        if not candidate_models:
            # Use default models based on task complexity
            candidate_models = self._get_default_models(task_request.complexity)
        
        # Filter by preferences
        if task_request.model_preferences:
            candidate_models = [m for m in candidate_models if m in task_request.model_preferences]
        
        # Score models
        scored_models = []
        for model_name in candidate_models:
            score = self._score_model(model_name, task_request)
            scored_models.append((model_name, score))
        
        # Select best model
        if scored_models:
            best_model = max(scored_models, key=lambda x: x[1])
            model_name = best_model[0]
            provider = self._get_provider_for_model(model_name)
            return model_name, provider
        
        # Fallback
        return "gpt-3.5-turbo", ModelProvider.OPENAI
    
    def _get_default_models(self, complexity: TaskComplexity) -> List[str]:
        """Get default models based on complexity"""
        complexity_models = {
            TaskComplexity.SIMPLE: ["gpt-3.5-turbo", "claude-instant"],
            TaskComplexity.MODERATE: ["gpt-4", "claude-sonnet"],
            TaskComplexity.COMPLEX: ["gpt-4-turbo", "claude-opus"],
            TaskComplexity.VERY_COMPLEX: ["gpt-4-turbo", "claude-opus"],
            TaskComplexity.EXTREME: ["gpt-4-turbo", "claude-opus"]
        }
        return complexity_models.get(complexity, ["gpt-4"])
    
    def _score_model(self, model_name: str, task_request: TaskRequest) -> float:
        """Score model for task"""
        score = 0.0
        
        # Performance score
        if model_name in self.model_performance:
            perf = self.model_performance[model_name]
            score += perf.get("accuracy", 0.5) * self.performance_weights["accuracy"]
            score += (1.0 / (1.0 + perf.get("response_time", 1.0))) * self.performance_weights["speed"]
            score += (1.0 - perf.get("cost_per_token", 0.01)) * self.performance_weights["cost"]
            score += perf.get("success_rate", 0.95) * self.performance_weights["reliability"]
        else:
            # Default score for unknown models
            score = 0.5
        
        # Capability match
        if model_name in self.model_capabilities:
            capabilities = self.model_capabilities[model_name]
            task_requirements = self._get_task_requirements(task_request.task_type)
            
            match_score = 0.0
            for req in task_requirements:
                if capabilities.get(req, False):
                    match_score += 1.0 / len(task_requirements)
            
            score += match_score * 0.3
        
        # Cost threshold
        agent_threshold = self.cost_thresholds.get(task_request.requesting_agent, float('inf'))
        if model_name in self.model_performance:
            estimated_cost = self.model_performance[model_name].get("cost_per_token", 0.01) * 1000  # Estimate 1000 tokens
            if estimated_cost > agent_threshold:
                score *= 0.5  # Penalize expensive models
        
        return score
    
    def _get_task_requirements(self, task_type: str) -> List[str]:
        """Get requirements for task type"""
        task_requirements = {
            "text_generation": ["text_completion", "creativity"],
            "classification": ["text_classification", "accuracy"],
            "translation": ["multilingual", "accuracy"],
            "summarization": ["text_compression", "accuracy"],
            "code_generation": ["code_completion", "syntax_understanding"],
            "embedding": ["text_embedding", "semantic_understanding"],
            "image_generation": ["image_creation", "creativity"]
        }
        return task_requirements.get(task_type, ["general"])
    
    def _get_provider_for_model(self, model_name: str) -> ModelProvider:
        """Get provider for model"""
        if model_name.startswith("gpt"):
            return ModelProvider.OPENAI
        elif model_name.startswith("claude"):
            return ModelProvider.ANTHROPIC
        elif "huggingface" in model_name.lower():
            return ModelProvider.HUGGINGFACE
        else:
            return ModelProvider.LOCAL


class TaskDecomposer:
    """Advanced task decomposition system"""
    
    def __init__(self):
        self.decomposition_rules = {}  # task_type -> decomposition strategy
        self.subtask_templates = {}  # subtask_type -> template
        self.max_depth = 3
        self.complexity_thresholds = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 3,
            TaskComplexity.COMPLEX: 5,
            TaskComplexity.VERY_COMPLEX: 8,
            TaskComplexity.EXTREME: 12
        }
    
    def register_decomposition_rule(self, task_type: str, rule: Callable):
        """Register decomposition rule for task type"""
        self.decomposition_rules[task_type] = rule
    
    def register_subtask_template(self, subtask_type: str, template: Dict[str, Any]):
        """Register subtask template"""
        self.subtask_templates[subtask_type] = template
    
    def decompose_task(self, task_request: TaskRequest, depth: int = 0) -> List[TaskRequest]:
        """Decompose task into subtasks"""
        if depth >= self.max_depth:
            return [task_request]
        
        # Check if task should be decomposed
        max_subtasks = self.complexity_thresholds.get(task_request.complexity, 3)
        
        # Get decomposition rule
        rule = self.decomposition_rules.get(task_request.task_type)
        if not rule:
            return [task_request]
        
        # Apply decomposition rule
        try:
            subtask_specs = rule(task_request)
            if not subtask_specs:
                return [task_request]
            
            # Limit number of subtasks
            subtask_specs = subtask_specs[:max_subtasks]
            
            # Create subtask requests
            subtasks = []
            for i, spec in enumerate(subtask_specs):
                subtask = TaskRequest(
                    task_id=f"{task_request.task_id}_sub_{i}",
                    task_type=spec.get("type", "general"),
                    description=spec.get("description", f"Subtask {i}"),
                    input_data=spec.get("input_data", task_request.input_data),
                    complexity=spec.get("complexity", TaskComplexity.SIMPLE),
                    priority=task_request.priority,
                    requesting_agent=task_request.requesting_agent,
                    model_preferences=task_request.model_preferences,
                    timeout=task_request.timeout,
                    metadata={**task_request.metadata, "parent_task": task_request.task_id}
                )
                
                # Recursively decompose if needed
                if subtask.complexity in [TaskComplexity.VERY_COMPLEX, TaskComplexity.EXTREME]:
                    subsubtasks = self.decompose_task(subtask, depth + 1)
                    subtasks.extend(subsubtasks)
                else:
                    subtasks.append(subtask)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Task decomposition error: {e}")
            return [task_request]


class ResponseAggregator:
    """Advanced response aggregation system"""
    
    def __init__(self):
        self.aggregation_strategies = {}  # task_type -> aggregation strategy
        self.confidence_thresholds = {}  # agent_id -> confidence_threshold
        self.conflict_resolution = "majority_vote"  # or "weighted_vote", "best_confidence"
    
    def register_aggregation_strategy(self, task_type: str, strategy: Callable):
        """Register aggregation strategy for task type"""
        self.aggregation_strategies[task_type] = strategy
    
    def set_confidence_threshold(self, agent_id: str, threshold: float):
        """Set confidence threshold for agent"""
        self.confidence_thresholds[agent_id] = threshold
    
    def aggregate_responses(self, task_request: TaskRequest, responses: List[TaskResponse]) -> TaskResponse:
        """Aggregate multiple responses into final result"""
        if not responses:
            return TaskResponse(
                task_id=task_request.task_id,
                success=False,
                result=None,
                execution_time=0.0,
                model_used="none",
                provider_used=ModelProvider.LOCAL,
                tokens_consumed=0,
                cost=0.0,
                error_message="No responses to aggregate"
            )
        
        if len(responses) == 1:
            return responses[0]
        
        # Get aggregation strategy
        strategy = self.aggregation_strategies.get(task_request.task_type)
        if strategy:
            try:
                return strategy(task_request, responses)
            except Exception as e:
                logger.error(f"Aggregation strategy error: {e}")
        
        # Default aggregation
        return self._default_aggregation(task_request, responses)
    
    def _default_aggregation(self, task_request: TaskRequest, responses: List[TaskResponse]) -> TaskResponse:
        """Default aggregation strategy"""
        # Filter successful responses
        successful_responses = [r for r in responses if r.success]
        
        if not successful_responses:
            return TaskResponse(
                task_id=task_request.task_id,
                success=False,
                result=None,
                execution_time=sum(r.execution_time for r in responses),
                model_used="none",
                provider_used=ModelProvider.LOCAL,
                tokens_consumed=sum(r.tokens_consumed for r in responses),
                cost=sum(r.cost for r in responses),
                error_message="All subtasks failed"
            )
        
        # For now, use the first successful response
        # In a real implementation, this would be more sophisticated
        best_response = successful_responses[0]
        
        # Aggregate metrics
        total_execution_time = sum(r.execution_time for r in responses)
        total_tokens = sum(r.tokens_consumed for r in responses)
        total_cost = sum(r.cost for r in responses)
        
        return TaskResponse(
            task_id=task_request.task_id,
            success=True,
            result=best_response.result,
            execution_time=total_execution_time,
            model_used=best_response.model_used,
            provider_used=best_response.provider_used,
            tokens_consumed=total_tokens,
            cost=total_cost,
            metadata={"aggregated_from": len(responses), "best_model": best_response.model_used}
        )


class EnhancedAIIntegration:
    """Enhanced AI integration system with advanced features"""
    
    def __init__(self):
        self.model_selector = ModelSelector()
        self.task_decomposer = TaskDecomposer()
        self.response_aggregator = ResponseAggregator()
        self.active_tasks = {}  # task_id -> TaskRequest
        self.task_history = defaultdict(list)  # agent_id -> TaskResponse
        self.batch_queue = asyncio.Queue()
        self.integration_mode = AIIntegrationMode.HYBRID
        self.performance_metrics = defaultdict(dict)
        
        # Initialize default configurations
        self._initialize_default_configurations()
    
    def _initialize_default_configurations(self):
        """Initialize default model configurations and mappings"""
        
        # Register model capabilities
        self.model_selector.register_model_capability("gpt-3.5-turbo", {
            "text_completion": True,
            "creativity": 0.7,
            "accuracy": 0.8,
            "speed": 0.9,
            "cost_efficiency": 0.9
        })
        
        self.model_selector.register_model_capability("gpt-4", {
            "text_completion": True,
            "creativity": 0.9,
            "accuracy": 0.95,
            "speed": 0.6,
            "cost_efficiency": 0.5
        })
        
        self.model_selector.register_model_capability("gpt-4-turbo", {
            "text_completion": True,
            "creativity": 0.95,
            "accuracy": 0.98,
            "speed": 0.8,
            "cost_efficiency": 0.7
        })
        
        self.model_selector.register_model_capability("claude-instant", {
            "text_completion": True,
            "creativity": 0.6,
            "accuracy": 0.75,
            "speed": 0.9,
            "cost_efficiency": 0.8
        })
        
        self.model_selector.register_model_capability("claude-sonnet", {
            "text_completion": True,
            "creativity": 0.85,
            "accuracy": 0.9,
            "speed": 0.7,
            "cost_efficiency": 0.6
        })
        
        self.model_selector.register_model_capability("claude-opus", {
            "text_completion": True,
            "creativity": 0.95,
            "accuracy": 0.98,
            "speed": 0.5,
            "cost_efficiency": 0.4
        })
        
        # Register task-model mappings
        self.model_selector.set_task_model_mapping("text_generation", ["gpt-4-turbo", "claude-opus", "gpt-4"])
        self.model_selector.set_task_model_mapping("classification", ["gpt-4", "claude-sonnet"])
        self.model_selector.set_task_model_mapping("translation", ["gpt-4-turbo", "claude-opus"])
        self.model_selector.set_task_model_mapping("summarization", ["gpt-4", "claude-sonnet"])
        self.model_selector.set_task_model_mapping("code_generation", ["gpt-4-turbo", "claude-opus"])
        self.model_selector.set_task_model_mapping("embedding", ["text-embedding-ada-002"])
        
        # Register decomposition rules
        self.task_decomposer.register_decomposition_rule("complex_analysis", self._decompose_complex_analysis)
        self.task_decomposer.register_decomposition_rule("multi_step_reasoning", self._decompose_multi_step_reasoning)
        self.task_decomposer.register_decomposition_rule("data_processing", self._decompose_data_processing)
        
        # Register aggregation strategies
        self.response_aggregator.register_aggregation_strategy("classification", self._aggregate_classification)
        self.response_aggregator.register_aggregation_strategy("text_generation", self._aggregate_text_generation)
        self.response_aggregator.register_aggregation_strategy("data_analysis", self._aggregate_data_analysis)
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute AI task with enhanced integration"""
        start_time = time.time()
        
        try:
            # Store active task
            self.active_tasks[task_request.task_id] = task_request
            
            # Decompose task if needed
            if task_request.complexity in [TaskComplexity.VERY_COMPLEX, TaskComplexity.EXTREME]:
                subtasks = self.task_decomposer.decompose_task(task_request)
                
                if len(subtasks) > 1:
                    # Execute subtasks
                    subtask_responses = []
                    for subtask in subtasks:
                        response = await self._execute_single_task(subtask)
                        subtask_responses.append(response)
                    
                    # Aggregate responses
                    final_response = self.response_aggregator.aggregate_responses(task_request, subtask_responses)
                else:
                    final_response = await self._execute_single_task(task_request)
            else:
                final_response = await self._execute_single_task(task_request)
            
            # Record task history
            self.task_history[task_request.requesting_agent].append(final_response)
            
            # Update performance metrics
            self._update_performance_metrics(task_request, final_response)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return TaskResponse(
                task_id=task_request.task_id,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                model_used="none",
                provider_used=ModelProvider.LOCAL,
                tokens_consumed=0,
                cost=0.0,
                error_message=str(e)
            )
        finally:
            # Clean up active task
            self.active_tasks.pop(task_request.task_id, None)
    
    async def _execute_single_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute single task"""
        # Select best model
        model_name, provider = self.model_selector.select_best_model(task_request)
        
        # Create model request
        model_request = ModelRequest(
            request_id=task_request.task_id,
            model_type=self._get_model_type(task_request.task_type),
            model_name=model_name,
            provider=provider,
            parameters={
                "prompt": task_request.description,
                "input_data": task_request.input_data,
                "max_tokens": task_request.metadata.get("max_tokens", 1000),
                "temperature": task_request.metadata.get("temperature", 0.7)
            },
            requesting_agent=task_request.requesting_agent,
            priority=task_request.priority,
            timeout=task_request.timeout
        )
        
        # Execute model request
        model_response = await centralized_model_manager.execute_model_request(model_request)
        
        # Convert to task response
        return TaskResponse(
            task_id=task_request.task_id,
            success=model_response.success,
            result=model_response.response_data,
            execution_time=model_response.execution_time,
            model_used=model_response.model_name,
            provider_used=model_response.provider,
            tokens_consumed=model_response.tokens_used,
            cost=model_response.cost,
            error_message=model_response.error_message
        )
    
    def _get_model_type(self, task_type: str) -> ModelType:
        """Get model type for task type"""
        type_mapping = {
            "text_generation": ModelType.TEXT_GENERATION,
            "classification": ModelType.CLASSIFICATION,
            "translation": ModelType.TRANSLATION,
            "summarization": ModelType.SUMMARIZATION,
            "code_generation": ModelType.CODE_GENERATION,
            "embedding": ModelType.TEXT_EMBEDDING
        }
        return type_mapping.get(task_type, ModelType.TEXT_GENERATION)
    
    def _update_performance_metrics(self, task_request: TaskRequest, response: TaskResponse):
        """Update performance metrics"""
        agent_id = task_request.requesting_agent
        task_type = task_request.task_type
        
        if task_type not in self.performance_metrics[agent_id]:
            self.performance_metrics[agent_id][task_type] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "average_execution_time": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0.0
            }
        
        metrics = self.performance_metrics[agent_id][task_type]
        metrics["total_tasks"] += 1
        
        if response.success:
            metrics["successful_tasks"] += 1
            metrics["total_cost"] += response.cost
            metrics["total_tokens"] += response.tokens_consumed
            
            # Update average execution time
            total_time = metrics["average_execution_time"] * (metrics["total_tasks"] - 1) + response.execution_time
            metrics["average_execution_time"] = total_time / metrics["total_tasks"]
        else:
            metrics["failed_tasks"] += 1
    
    # Decomposition strategies
    def _decompose_complex_analysis(self, task_request: TaskRequest) -> List[Dict[str, Any]]:
        """Decompose complex analysis task"""
        return [
            {
                "type": "data_preprocessing",
                "description": "Preprocess input data for analysis",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            },
            {
                "type": "feature_extraction",
                "description": "Extract relevant features from data",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            },
            {
                "type": "pattern_analysis",
                "description": "Analyze patterns in extracted features",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.COMPLEX
            },
            {
                "type": "result_synthesis",
                "description": "Synthesize analysis results",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            }
        ]
    
    def _decompose_multi_step_reasoning(self, task_request: TaskRequest) -> List[Dict[str, Any]]:
        """Decompose multi-step reasoning task"""
        return [
            {
                "type": "problem_understanding",
                "description": "Understand the problem context",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            },
            {
                "type": "hypothesis_generation",
                "description": "Generate initial hypotheses",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.COMPLEX
            },
            {
                "type": "evidence_evaluation",
                "description": "Evaluate evidence for hypotheses",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.COMPLEX
            },
            {
                "type": "conclusion_synthesis",
                "description": "Synthesize final conclusion",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            }
        ]
    
    def _decompose_data_processing(self, task_request: TaskRequest) -> List[Dict[str, Any]]:
        """Decompose data processing task"""
        return [
            {
                "type": "data_validation",
                "description": "Validate input data",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.SIMPLE
            },
            {
                "type": "data_cleaning",
                "description": "Clean and normalize data",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            },
            {
                "type": "data_transformation",
                "description": "Transform data format",
                "input_data": task_request.input_data,
                "complexity": TaskComplexity.MODERATE
            }
        ]
    
    # Aggregation strategies
    def _aggregate_classification(self, task_request: TaskRequest, responses: List[TaskResponse]) -> TaskResponse:
        """Aggregate classification responses"""
        successful_responses = [r for r in responses if r.success]
        
        if not successful_responses:
            return responses[0]  # Return first failed response
        
        # Count votes for each class
        votes = defaultdict(int)
        for response in successful_responses:
            if isinstance(response.result, dict) and "class" in response.result:
                votes[response.result["class"]] += 1
        
        # Find majority vote
        if votes:
            best_class = max(votes.items(), key=lambda x: x[1])[0]
            confidence = votes[best_class] / len(successful_responses)
        else:
            best_class = None
            confidence = 0.0
        
        result = {
            "class": best_class,
            "confidence": confidence,
            "votes": dict(votes),
            "num_responses": len(successful_responses)
        }
        
        return TaskResponse(
            task_id=task_request.task_id,
            success=True,
            result=result,
            execution_time=sum(r.execution_time for r in responses),
            model_used="aggregated",
            provider_used=ModelProvider.LOCAL,
            tokens_consumed=sum(r.tokens_consumed for r in responses),
            cost=sum(r.cost for r in responses)
        )
    
    def _aggregate_text_generation(self, task_request: TaskRequest, responses: List[TaskResponse]) -> TaskResponse:
        """Aggregate text generation responses"""
        successful_responses = [r for r in responses if r.success]
        
        if not successful_responses:
            return responses[0]
        
        # For now, return the longest response (could be more sophisticated)
        best_response = max(successful_responses, key=lambda r: len(str(r.result)))
        
        return TaskResponse(
            task_id=task_request.task_id,
            success=True,
            result=best_response.result,
            execution_time=sum(r.execution_time for r in responses),
            model_used=best_response.model_used,
            provider_used=best_response.provider_used,
            tokens_consumed=sum(r.tokens_consumed for r in responses),
            cost=sum(r.cost for r in responses),
            metadata={"aggregated_from": len(responses)}
        )
    
    def _aggregate_data_analysis(self, task_request: TaskRequest, responses: List[TaskResponse]) -> TaskResponse:
        """Aggregate data analysis responses"""
        successful_responses = [r for r in responses if r.success]
        
        if not successful_responses:
            return responses[0]
        
        # Combine analysis results
        combined_result = {
            "analyses": [r.result for r in successful_responses],
            "summary": f"Combined analysis from {len(successful_responses)} models",
            "confidence": sum(r.result.get("confidence", 0.5) for r in successful_responses) / len(successful_responses)
        }
        
        return TaskResponse(
            task_id=task_request.task_id,
            success=True,
            result=combined_result,
            execution_time=sum(r.execution_time for r in responses),
            model_used="aggregated",
            provider_used=ModelProvider.LOCAL,
            tokens_consumed=sum(r.tokens_consumed for r in responses),
            cost=sum(r.cost for r in responses)
        )
    
    def get_performance_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for agent"""
        return self.performance_metrics.get(agent_id, {})
    
    def get_task_history(self, agent_id: str, limit: int = 10) -> List[TaskResponse]:
        """Get task history for agent"""
        history = self.task_history.get(agent_id, [])
        return history[-limit:] if history else []
    
    def set_integration_mode(self, mode: AIIntegrationMode):
        """Set integration mode"""
        self.integration_mode = mode
    
    async def shutdown(self):
        """Shutdown enhanced AI integration"""
        logger.info("Enhanced AI Integration shutdown complete")


# Global enhanced AI integration instance
enhanced_ai_integration = EnhancedAIIntegration()
