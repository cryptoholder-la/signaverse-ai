"""
Distributed GPU Compute Marketplace
Decentralized marketplace for GPU compute resources and AI training
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ComputeResourceType(Enum):
    """Types of compute resources"""
    GPU = "gpu"
    CPU = "cpu"
    TPUS = "tpu"
    MEMORY = "memory"
    STORAGE = "storage"


class TaskStatus(Enum):
    """Status of compute tasks"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class PricingModel(Enum):
    """Pricing models for compute resources"""
    PER_HOUR = "per_hour"
    PER_MINUTE = "per_minute"
    PER_TOKEN = "per_token"
    PER_DATASET = "per_dataset"
    BID = "bid"


@dataclass
class GPUResource:
    """GPU resource specification"""
    def __init__(self, resource_id: str, provider_id: str, gpu_type: str,
                 memory_gb: float, cuda_cores: int, tensor_cores: bool,
                 bandwidth_gbps: float, price_per_hour: float,
                 availability: float = 1.0, location: str = None,
                 metadata: Dict[str, Any] = None):
        self.resource_id = resource_id
        self.provider_id = provider_id
        self.gpu_type = gpu_type
        self.memory_gb = memory_gb
        self.cuda_cores = cuda_cores
        self.tensor_cores = tensor_cores
        self.bandwidth_gbps = bandwidth_gbps
        self.price_per_hour = price_per_hour
        self.availability = availability
        self.location = location
        self.metadata = metadata or {}
        self.is_available = True
        self.current_task_id: Optional[str] = None
        self.performance_score = 100.0
        self.reputation_score = 50.0
    
    def update_performance(self, task_success: bool, execution_time: float):
        """Update performance score based on task execution"""
        if task_success:
            # Reward for successful completion
            self.performance_score = min(100, self.performance_score + 5)
        else:
            # Penalize for failure
            self.performance_score = max(0, self.performance_score - 10)
        
        # Consider execution time
        if execution_time < 3600:  # Less than 1 hour
            self.performance_score = min(100, self.performance_score + 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ComputeTask:
    """Compute task specification"""
    def __init__(self, task_id: str, requester_id: str, task_type: str,
                 requirements: Dict[str, Any], dataset_path: str = None,
                 model_path: str = None, script_path: str = None,
                 max_price: float = None, max_duration: int = 3600,
                 priority: int = 5, metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.requester_id = requester_id
        self.task_type = task_type
        self.requirements = requirements
        self.dataset_path = dataset_path
        self.model_path = model_path
        self.script_path = script_path
        self.max_price = max_price
        self.max_duration = max_duration
        self.priority = priority
        self.metadata = metadata or {}
        
        # Execution state
        self.status = TaskStatus.PENDING
        self.assigned_resource_id: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.execution_time: Optional[float] = None
        self.cost: Optional[float] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.logs: List[str] = []
        
        # Bidding
        self.bids: List[Dict[str, Any]] = []
        self.selected_bid: Optional[Dict[str, Any]] = None
    
    def add_bid(self, resource_id: str, provider_id: str, price: float,
               estimated_time: int, confidence: float = 0.8):
        """Add a bid for this task"""
        bid = {
            "bid_id": str(uuid.uuid4()),
            "resource_id": resource_id,
            "provider_id": provider_id,
            "price": price,
            "estimated_time": estimated_time,
            "confidence": confidence,
            "timestamp": time.time()
        }
        self.bids.append(bid)
    
    def select_bid(self, bid_id: str):
        """Select a bid for execution"""
        for bid in self.bids:
            if bid["bid_id"] == bid_id:
                self.selected_bid = bid
                self.assigned_resource_id = bid["resource_id"]
                self.cost = bid["price"]
                return True
        return False
    
    def start_execution(self, resource_id: str):
        """Start task execution"""
        self.status = TaskStatus.RUNNING
        self.assigned_resource_id = resource_id
        self.start_time = time.time()
    
    def complete_execution(self, result: Dict[str, Any], cost: float):
        """Complete task execution"""
        self.status = TaskStatus.COMPLETED
        self.end_time = time.time()
        self.result = result
        self.cost = cost
        
        if self.start_time:
            self.execution_time = self.end_time - self.start_time
    
    def fail_execution(self, error_message: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.end_time = time.time()
        self.error_message = error_message
        
        if self.start_time:
            self.execution_time = self.end_time - self.start_time
    
    def add_log(self, log_message: str):
        """Add execution log"""
        log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {log_message}"
        self.logs.append(log_entry)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ProviderProfile:
    """Compute provider profile"""
    def __init__(self, provider_id: str, name: str, description: str,
                 resources: List[GPUResource], reputation_score: float = 50.0,
                 total_tasks_completed: int = 0, total_earnings: float = 0.0,
                 verification_status: str = "pending"):
        self.provider_id = provider_id
        self.name = name
        self.description = description
        self.resources = resources
        self.reputation_score = reputation_score
        self.total_tasks_completed = total_tasks_completed
        self.total_earnings = total_earnings
        self.verification_status = verification_status
        self.created_at = time.time()
        self.last_active = time.time()
        
        # Performance metrics
        self.average_completion_time = 0.0
        self.success_rate = 1.0
        self.customer_ratings: List[Dict[str, Any]] = []
    
    def update_reputation(self, task_success: bool, rating: float = None):
        """Update provider reputation"""
        self.total_tasks_completed += 1
        
        if task_success:
            self.reputation_score = min(100, self.reputation_score + 2)
        else:
            self.reputation_score = max(0, self.reputation_score - 5)
        
        if rating is not None:
            self.customer_ratings.append({
                "rating": rating,
                "timestamp": time.time()
            })
        
        # Update success rate
        if self.total_tasks_completed > 0:
            successful_tasks = sum(1 for r in self.customer_ratings if r.get("rating", 0) > 3)
            self.success_rate = successful_tasks / len(self.customer_ratings)
    
    def get_average_rating(self) -> float:
        """Get average customer rating"""
        if not self.customer_ratings:
            return 0.0
        
        ratings = [r["rating"] for r in self.customer_ratings if "rating" in r]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class GPUComputeMarketplace:
    """Distributed GPU compute marketplace"""
    
    def __init__(self, marketplace_id: str = "signaverse-gpu-market"):
        self.marketplace_id = marketplace_id
        
        # Marketplace state
        self.providers: Dict[str, ProviderProfile] = {}
        self.resources: Dict[str, GPUResource] = {}
        self.tasks: Dict[str, ComputeTask] = {}
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
        # Matching engine
        self.matching_algorithm = "reputation_weighted"
        self.min_reputation_threshold = 30.0
        
        # Configuration
        self.config = {
            "max_task_duration": 24 * 3600,  # 24 hours
            "min_bid_price": 0.01,  # Minimum $0.01
            "marketplace_fee": 0.05,  # 5% fee
            "dispute_resolution_time": 7 * 24 * 3600,  # 7 days
            "auto_match_threshold": 0.8,  # Confidence threshold for auto-matching
            "max_concurrent_tasks_per_provider": 10
        }
        
        # Performance metrics
        self.metrics = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_revenue": 0.0,
            "average_task_price": 0.0,
            "average_execution_time": 0.0,
            "active_providers": 0,
            "available_resources": 0
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.on_task_created = None
        self.on_task_assigned = None
        self.on_task_completed = None
        self.on_provider_registered = None
    
    def register_provider(self, provider_profile: ProviderProfile) -> bool:
        """Register a new compute provider"""
        try:
            if provider_profile.provider_id in self.providers:
                logger.warning(f"Provider {provider_profile.provider_id} already registered")
                return False
            
            # Validate provider
            if not self._validate_provider(provider_profile):
                logger.error(f"Provider validation failed for {provider_profile.provider_id}")
                return False
            
            self.providers[provider_profile.provider_id] = provider_profile
            
            # Register resources
            for resource in provider_profile.resources:
                self.resources[resource.resource_id] = resource
            
            self.metrics["active_providers"] += 1
            
            # Notify callback
            if self.on_provider_registered:
                self.on_provider_registered(provider_profile)
            
            logger.info(f"Registered provider: {provider_profile.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register provider: {e}")
            return False
    
    def _validate_provider(self, provider: ProviderProfile) -> bool:
        """Validate provider profile"""
        if not provider.name or not provider.resources:
            return False
        
        # Check resource specifications
        for resource in provider.resources:
            if not resource.gpu_type or resource.memory_gb <= 0:
                return False
        
        return True
    
    def create_task(self, requester_id: str, task_type: str, requirements: Dict[str, Any],
                   dataset_path: str = None, model_path: str = None,
                   script_path: str = None, max_price: float = None,
                   max_duration: int = 3600, priority: int = 5,
                   metadata: Dict[str, Any] = None) -> str:
        """Create a new compute task"""
        try:
            task_id = str(uuid.uuid4())
            
            task = ComputeTask(
                task_id=task_id,
                requester_id=requester_id,
                task_type=task_type,
                requirements=requirements,
                dataset_path=dataset_path,
                model_path=model_path,
                script_path=script_path,
                max_price=max_price,
                max_duration=max_duration,
                priority=priority,
                metadata=metadata
            )
            
            self.tasks[task_id] = task
            self.metrics["total_tasks_created"] += 1
            
            # Auto-match with providers
            asyncio.create_task(self._auto_match_task(task_id))
            
            # Notify callback
            if self.on_task_created:
                self.on_task_created(task)
            
            logger.info(f"Created compute task {task_id} for {requester_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return ""
    
    async def _auto_match_task(self, task_id: str):
        """Automatically match task with suitable providers"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            # Find suitable resources
            suitable_resources = self._find_suitable_resources(task)
            
            if not suitable_resources:
                logger.info(f"No suitable resources found for task {task_id}")
                return
            
            # Generate bids from suitable providers
            for resource in suitable_resources[:5]:  # Top 5 resources
                provider = self.providers.get(resource.provider_id)
                if provider and provider.reputation_score >= self.min_reputation_threshold:
                    # Calculate bid price
                    base_price = resource.price_per_hour
                    estimated_time = self._estimate_execution_time(task, resource)
                    bid_price = base_price * (estimated_time / 3600)  # Convert to hours
                    
                    # Apply reputation discount
                    reputation_discount = 1.0 - (provider.reputation_score / 1000)  # Up to 10% discount
                    bid_price *= reputation_discount
                    
                    # Add bid
                    task.add_bid(
                        resource_id=resource.resource_id,
                        provider_id=resource.provider_id,
                        price=bid_price,
                        estimated_time=estimated_time,
                        confidence=min(1.0, provider.reputation_score / 100)
                    )
            
            # Auto-select best bid if confidence is high
            if task.bids:
                best_bid = max(task.bids, key=lambda b: b["confidence"] * (1.0 / max(b["price"], 0.01)))
                
                if best_bid["confidence"] >= self.config["auto_match_threshold"]:
                    task.select_bid(best_bid["bid_id"])
                    await self._assign_task(task_id, best_bid["resource_id"])
            
        except Exception as e:
            logger.error(f"Error auto-matching task {task_id}: {e}")
    
    def _find_suitable_resources(self, task: ComputeTask) -> List[GPUResource]:
        """Find resources suitable for the task"""
        suitable = []
        requirements = task.requirements
        
        for resource in self.resources.values():
            if not resource.is_available:
                continue
            
            # Check GPU requirements
            if "gpu_memory" in requirements:
                if resource.memory_gb < requirements["gpu_memory"]:
                    continue
            
            if "cuda_cores" in requirements:
                if resource.cuda_cores < requirements["cuda_cores"]:
                    continue
            
            if "tensor_cores" in requirements:
                if requirements["tensor_cores"] and not resource.tensor_cores:
                    continue
            
            # Check price constraints
            if task.max_price:
                estimated_hours = task.max_duration / 3600
                estimated_cost = resource.price_per_hour * estimated_hours
                if estimated_cost > task.max_price:
                    continue
            
            # Check provider reputation
            provider = self.providers.get(resource.provider_id)
            if provider and provider.reputation_score < self.min_reputation_threshold:
                continue
            
            suitable.append(resource)
        
        # Sort by performance score and price
        suitable.sort(key=lambda r: (r.performance_score, -r.price_per_hour), reverse=True)
        return suitable
    
    def _estimate_execution_time(self, task: ComputeTask, resource: GPUResource) -> int:
        """Estimate task execution time on a resource"""
        # Simplified estimation based on resource capabilities
        base_time = task.requirements.get("estimated_time", 3600)  # Default 1 hour
        
        # Adjust based on GPU performance
        performance_factor = resource.performance_score / 100.0
        adjusted_time = base_time / performance_factor
        
        # Adjust based on memory
        if "gpu_memory" in task.requirements:
            memory_factor = min(1.0, resource.memory_gb / task.requirements["gpu_memory"])
            adjusted_time /= memory_factor
        
        return int(adjusted_time)
    
    async def _assign_task(self, task_id: str, resource_id: str):
        """Assign task to a resource"""
        try:
            task = self.tasks.get(task_id)
            resource = self.resources.get(resource_id)
            
            if not task or not resource:
                return
            
            # Mark resource as busy
            resource.is_available = False
            resource.current_task_id = task_id
            
            # Start task execution
            task.start_execution(resource_id)
            
            # Track execution
            self.active_executions[task_id] = {
                "task": task,
                "resource": resource,
                "start_time": time.time()
            }
            
            # Notify callback
            if self.on_task_assigned:
                self.on_task_assigned(task, resource)
            
            # Start execution simulation
            asyncio.create_task(self._execute_task(task_id))
            
            logger.info(f"Assigned task {task_id} to resource {resource_id}")
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_id}: {e}")
    
    async def _execute_task(self, task_id: str):
        """Simulate task execution"""
        try:
            execution = self.active_executions.get(task_id)
            if not execution:
                return
            
            task = execution["task"]
            resource = execution["resource"]
            provider = self.providers.get(resource.provider_id)
            
            # Simulate execution time
            estimated_time = self._estimate_execution_time(task, resource)
            await asyncio.sleep(min(estimated_time, 60))  # Max 60 seconds for demo
            
            # Simulate task completion
            success_rate = provider.reputation_score / 100.0 if provider else 0.5
            task_success = success_rate > 0.7  # 70% success rate threshold
            
            if task_success:
                # Generate mock result
                result = {
                    "status": "completed",
                    "accuracy": 0.85 + (success_rate * 0.1),
                    "loss": 0.15 - (success_rate * 0.1),
                    "training_time": estimated_time,
                    "model_path": f"/models/{task_id}_trained.pt",
                    "metrics": {
                        "precision": 0.82,
                        "recall": 0.88,
                        "f1_score": 0.85
                    }
                }
                
                # Calculate cost
                cost = resource.price_per_hour * (estimated_time / 3600)
                task.complete_execution(result, cost)
                
                # Update provider metrics
                if provider:
                    provider.update_reputation(True)
                    provider.total_earnings += cost * (1 - self.config["marketplace_fee"])
                    resource.update_performance(True, estimated_time)
                
                # Update marketplace metrics
                self.metrics["total_tasks_completed"] += 1
                self.metrics["total_revenue"] += cost * self.config["marketplace_fee"]
                
            else:
                # Task failed
                error_msg = "Task execution failed due to resource constraints"
                task.fail_execution(error_msg)
                
                # Update provider metrics
                if provider:
                    provider.update_reputation(False)
                    resource.update_performance(False, estimated_time)
            
            # Mark resource as available
            resource.is_available = True
            resource.current_task_id = None
            
            # Clean up execution tracking
            if task_id in self.active_executions:
                del self.active_executions[task_id]
            
            # Notify callback
            if self.on_task_completed:
                self.on_task_completed(task)
            
            logger.info(f"Completed task {task_id}: {task.status.value}")
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
    
    def submit_bid(self, task_id: str, resource_id: str, provider_id: str,
                 price: float, estimated_time: int, confidence: float = 0.8) -> bool:
        """Submit a bid for a task"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            resource = self.resources.get(resource_id)
            provider = self.providers.get(provider_id)
            
            if not resource or not provider:
                logger.error(f"Resource {resource_id} or provider {provider_id} not found")
                return False
            
            # Validate bid
            if price < self.config["min_bid_price"]:
                logger.error(f"Bid price {price} below minimum {self.config['min_bid_price']}")
                return False
            
            if provider.reputation_score < self.min_reputation_threshold:
                logger.error(f"Provider {provider_id} reputation below threshold")
                return False
            
            # Add bid
            task.add_bid(resource_id, provider_id, price, estimated_time, confidence)
            
            logger.info(f"Submitted bid for task {task_id}: ${price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit bid: {e}")
            return False
    
    async def select_bid(self, task_id: str, bid_id: str, requester_id: str) -> bool:
        """Select a bid for task execution"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            if task.requester_id != requester_id:
                logger.error(f"Unauthorized bid selection for task {task_id}")
                return False
            
            # Select bid
            if task.select_bid(bid_id):
                selected_bid = task.selected_bid
                await self._assign_task(task_id, selected_bid["resource_id"])
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to select bid: {e}")
            return False
    
    def get_available_resources(self, filters: Dict[str, Any] = None) -> List[GPUResource]:
        """Get available compute resources"""
        resources = []
        
        for resource in self.resources.values():
            if not resource.is_available:
                continue
            
            # Apply filters
            if filters:
                if "min_memory" in filters and resource.memory_gb < filters["min_memory"]:
                    continue
                if "gpu_type" in filters and resource.gpu_type != filters["gpu_type"]:
                    continue
                if "max_price" in filters and resource.price_per_hour > filters["max_price"]:
                    continue
                if "tensor_cores" in filters and filters["tensor_cores"] and not resource.tensor_cores:
                    continue
            
            resources.append(resource)
        
        return resources
    
    def get_provider_tasks(self, provider_id: str) -> List[ComputeTask]:
        """Get tasks for a specific provider"""
        provider_tasks = []
        
        for task in self.tasks.values():
            if task.assigned_resource_id:
                resource = self.resources.get(task.assigned_resource_id)
                if resource and resource.provider_id == provider_id:
                    provider_tasks.append(task)
        
        return provider_tasks
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        # Update metrics
        self.metrics["available_resources"] = len([r for r in self.resources.values() if r.is_available])
        
        # Calculate average prices
        if self.resources:
            prices = [r.price_per_hour for r in self.resources.values()]
            self.metrics["average_gpu_price"] = sum(prices) / len(prices)
        
        # Calculate average execution time
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED and t.execution_time]
        if completed_tasks:
            self.metrics["average_execution_time"] = sum(t.execution_time for t in completed_tasks) / len(completed_tasks)
        
        return {
            "metrics": self.metrics,
            "total_providers": len(self.providers),
            "total_resources": len(self.resources),
            "active_tasks": len(self.active_executions),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        }
    
    async def start(self) -> bool:
        """Start the marketplace"""
        try:
            self.is_running = True
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._cleanup_loop()),
                asyncio.create_task(self._metrics_loop()),
                asyncio.create_task(self._resource_monitoring_loop())
            ]
            
            logger.info(f"GPU compute marketplace started: {self.marketplace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start marketplace: {e}")
            return False
    
    async def stop(self):
        """Stop the marketplace"""
        self.is_running = False
        
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("GPU compute marketplace stopped")
    
    async def _cleanup_loop(self):
        """Background loop for cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                current_time = time.time()
                
                # Clean up old completed tasks
                max_age = 7 * 24 * 3600  # 7 days
                old_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and
                        task.end_time and current_time - task.end_time > max_age)
                ]
                
                for task_id in old_tasks:
                    del self.tasks[task_id]
                
                # Clean up inactive providers
                inactive_providers = [
                    provider_id for provider_id, provider in self.providers.items()
                    if current_time - provider.last_active > 30 * 24 * 3600  # 30 days
                ]
                
                for provider_id in inactive_providers:
                    del self.providers[provider_id]
                    # Also remove their resources
                    self.resources = {
                        rid: resource for rid, resource in self.resources.items()
                        if resource.provider_id != provider_id
                    }
                
                logger.debug(f"Cleaned up {len(old_tasks)} old tasks and {len(inactive_providers)} inactive providers")
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    async def _resource_monitoring_loop(self):
        """Background loop for resource monitoring"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Update resource availability
                for resource in self.resources.values():
                    # Simulate resource availability changes
                    if resource.current_task_id:
                        # Check if task is still running
                        execution = self.active_executions.get(resource.current_task_id)
                        if not execution:
                            # Task completed, free resource
                            resource.is_available = True
                            resource.current_task_id = None
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _metrics_loop(self):
        """Background loop for metrics collection"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                stats = self.get_marketplace_stats()
                logger.debug(f"Marketplace metrics: {stats}")
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(60)
    
    def export_marketplace_data(self) -> Dict[str, Any]:
        """Export marketplace data for backup"""
        return {
            "marketplace_id": self.marketplace_id,
            "providers": {pid: provider.to_dict() for pid, provider in self.providers.items()},
            "resources": {rid: resource.to_dict() for rid, resource in self.resources.items()},
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "metrics": self.metrics,
            "config": self.config,
            "export_timestamp": time.time()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get marketplace status"""
        return {
            "is_running": self.is_running,
            "marketplace_id": self.marketplace_id,
            "stats": self.get_marketplace_stats(),
            "config": self.config
        }
