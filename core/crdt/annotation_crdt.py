"""
CRDT Collaborative Annotation Engine
Allows multiple peers to edit sign language annotations simultaneously without conflicts
"""

import uuid
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class AnnotationOperationType(Enum):
    """Types of annotation operations"""
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"
    MERGE = "merge"
    RESOLVE = "resolve"


@dataclass
class AnnotationOperation:
    """CRDT operation for annotations"""
    def __init__(self, id: str, agent: str, op: AnnotationOperationType,
                 key: str, value: Any = None, old_value: Any = None,
                 timestamp: float = None, metadata: Dict[str, Any] = None):
        self.id = id
        self.agent = agent
        self.op = op
        self.key = key
        self.value = value
        self.old_value = old_value
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
        self.vector_clock = 1  # Logical timestamp for conflict resolution
        self.dependencies: Set[str] = set()  # Dependencies for causal consistency
    
    def add_dependency(self, dependency_id: str):
        """Add dependency for causal consistency"""
        self.dependencies.add(dependency_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "agent": self.agent,
            "op": self.op.value,
            "key": self.key,
            "value": self.value,
            "old_value": self.old_value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "vector_clock": self.vector_clock,
            "dependencies": list(self.dependencies)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnnotationOperation':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            agent=data["agent"],
            op=AnnotationOperationType(data["op"]),
            key=data["key"],
            value=data.get("value"),
            old_value=data.get("old_value"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
            vector_clock=data.get("vector_clock", 1),
            dependencies=set(data.get("dependencies", []))
        )


@dataclass
class AnnotationState:
    """State of an annotation with CRDT metadata"""
    def __init__(self, content: Any, created_by: str, created_at: float,
                 last_modified: float, version: int = 1,
                 metadata: Dict[str, Any] = None):
        self.content = content
        self.created_by = created_by
        self.created_at = created_at
        self.last_modified = last_modified
        self.version = version
        self.metadata = metadata or {}
        self.vector_clocks: Dict[str, int] = {}  # agent -> vector clock
        self.tombstones: Set[str] = set()  # Deleted annotation IDs
        self.conflicts: List[str] = []  # Conflict tracking
        self.merge_history: List[Dict[str, Any]] = []  # Merge history for debugging
    
    def update_vector_clock(self, agent: str, clock_value: int):
        """Update vector clock for agent"""
        current_clock = self.vector_clocks.get(agent, 0)
        self.vector_clocks[agent] = max(current_clock, clock_value)
    
    def get_max_vector_clock(self) -> int:
        """Get maximum vector clock across all agents"""
        if not self.vector_clocks:
            return 0
        return max(self.vector_clocks.values())
    
    def add_conflict(self, conflict_id: str):
        """Add conflict to tracking"""
        if conflict_id not in self.conflicts:
            self.conflicts.append(conflict_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "version": self.version,
            "metadata": self.metadata,
            "vector_clocks": self.vector_clocks,
            "tombstones": list(self.tombstones),
            "conflicts": self.conflicts,
            "merge_history": self.merge_history
        }


class ConflictResolutionStrategy:
    """Strategies for resolving annotation conflicts"""
    
    @staticmethod
    async def last_writer_wins(operations: List[AnnotationOperation]) -> List[AnnotationOperation]:
        """Last writer wins - keep the latest operation"""
        if not operations:
            return []
        
        # Sort by timestamp, then by vector clock
        sorted_ops = sorted(
            operations,
            key=lambda op: (op.timestamp, op.vector_clock)
        )
        
        return [sorted_ops[-1]]  # Return only the latest operation
    
    @staticmethod
    async def merge_content(operations: List[AnnotationOperation]) -> List[AnnotationOperation]:
        """Merge conflicting content"""
        if not operations:
            return []
        
        # Group operations by key
        ops_by_key = {}
        for op in operations:
            if op.key not in ops_by_key:
                ops_by_key[op.key] = []
            ops_by_key[op.key].append(op)
        
        resolved_ops = []
        
        for key, key_ops in ops_by_key.items():
            if len(key_ops) == 1:
                resolved_ops.extend(key_ops)
            else:
                # Merge operations for this key
                merged_value = ConflictResolutionStrategy._merge_values(key_ops)
                merge_op = AnnotationOperation(
                    id=str(uuid.uuid4()),
                    agent="conflict_resolver",
                    op=AnnotationOperationType.MERGE,
                    key=key,
                    value=merged_value,
                    metadata={"merged_from": [op.id for op in key_ops]}
                )
                resolved_ops.append(merge_op)
        
        return resolved_ops
    
    @staticmethod
    def _merge_values(operations: List[AnnotationOperation]) -> Any:
        """Merge values from conflicting operations"""
        # For annotations, we'll merge based on operation type
        add_ops = [op for op in operations if op.op == AnnotationOperationType.ADD]
        update_ops = [op for op in operations if op.op == AnnotationOperationType.UPDATE]
        delete_ops = [op for op in operations if op.op == AnnotationOperationType.DELETE]
        
        # If there's a delete, it takes precedence
        if delete_ops:
            return None  # Delete wins
        
        # Merge adds and updates
        merged_content = {}
        
        for op in add_ops:
            if isinstance(op.value, dict):
                merged_content.update(op.value)
            else:
                # Handle scalar values
                merged_content[op.key] = op.value
        
        for op in update_ops:
            if isinstance(op.value, dict):
                if op.key in merged_content:
                    merged_content[op.key].update(op.value)
                else:
                    merged_content[op.key] = op.value
            else:
                merged_content[op.key] = op.value
        
        return merged_content
    
    @staticmethod
    async def operational_transform(operations: List[AnnotationOperation]) -> List[AnnotationOperation]:
        """Operational transform to resolve conflicts"""
        if not operations:
            return []
        
        # Transform operations based on type
        transformed_ops = []
        
        # Sort by timestamp and vector clock
        sorted_ops = sorted(
            operations,
            key=lambda op: (op.timestamp, op.vector_clock)
        )
        
        for op in sorted_ops:
            transformed_op = ConflictResolutionStrategy._transform_operation(op, transformed_ops)
            transformed_ops.append(transformed_op)
        
        return transformed_ops
    
    @staticmethod
    def _transform_operation(op: AnnotationOperation, previous_ops: List[AnnotationOperation]) -> AnnotationOperation:
        """Transform a single operation based on previous operations"""
        transformed_op = AnnotationOperation(
            id=op.id,
            agent=op.agent,
            op=op.op,
            key=op.key,
            value=op.value,
            old_value=op.old_value,
            timestamp=op.timestamp,
            metadata=op.metadata.copy()
        )
        
        # Adjust based on previous operations
        for prev_op in previous_ops:
            if prev_op.key == op.key:
                if prev_op.op == AnnotationOperationType.DELETE and op.op == AnnotationOperationType.UPDATE:
                    # Delete followed by update - the update should be ignored
                    transformed_op.metadata["transformed"] = "ignored_due_to_delete"
                elif prev_op.op == AnnotationOperationType.ADD and op.op == AnnotationOperationType.ADD:
                    # Two adds to same key - transform second add to update
                    if isinstance(prev_op.value, dict) and isinstance(op.value, dict):
                        transformed_op.op = AnnotationOperationType.UPDATE
                        transformed_op.value = {**prev_op.value, **op.value}
                        transformed_op.old_value = prev_op.value
                        transformed_op.metadata["transformed"] = "add_to_update"
        
        return transformed_op


class AnnotationCRDT:
    """CRDT engine for collaborative annotations"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.states: Dict[str, AnnotationState] = {}  # annotation_id -> state
        self.operations: List[AnnotationOperation] = []
        self.subscribers: List[Callable] = []
        
        # Conflict resolution
        self.conflict_resolver = ConflictResolutionStrategy()
        
        # Performance metrics
        self.metrics = {
            "operations_processed": 0,
            "conflicts_resolved": 0,
            "states_created": 0,
            "merges_performed": 0
        }
    
    def subscribe(self, callback: Callable):
        """Subscribe to CRDT events"""
        self.subscribers.append(callback)
    
    async def create_annotation(self, agent: str, key: str, value: Any,
                           metadata: Dict[str, Any] = None) -> str:
        """Create a new annotation"""
        annotation_id = str(uuid.uuid4())
        
        # Create initial state
        state = AnnotationState(
            content=value,
            created_by=agent,
            created_at=time.time(),
            last_modified=time.time(),
            version=1,
            metadata=metadata
        )
        
        # Create operation
        operation = AnnotationOperation(
            id=str(uuid.uuid4()),
            agent=agent,
            op=AnnotationOperationType.ADD,
            key=key,
            value=value,
            metadata=metadata
        )
        
        # Apply operation
        await self._apply_operation(annotation_id, operation)
        
        logger.info(f"Created annotation {annotation_id} by {agent}")
        return annotation_id
    
    async def update_annotation(self, agent: str, annotation_id: str, 
                           new_value: Any, metadata: Dict[str, Any] = None) -> bool:
        """Update an existing annotation"""
        if annotation_id not in self.states:
            logger.warning(f"Annotation {annotation_id} not found")
            return False
        
        state = self.states[annotation_id]
        old_value = state.content
        
        # Create operation
        operation = AnnotationOperation(
            id=str(uuid.uuid4()),
            agent=agent,
            op=AnnotationOperationType.UPDATE,
            key=annotation_id,
            value=new_value,
            old_value=old_value,
            metadata=metadata
        )
        
        # Apply operation
        await self._apply_operation(annotation_id, operation)
        
        logger.info(f"Updated annotation {annotation_id} by {agent}")
        return True
    
    async def delete_annotation(self, agent: str, annotation_id: str,
                           metadata: Dict[str, Any] = None) -> bool:
        """Delete an annotation"""
        if annotation_id not in self.states:
            logger.warning(f"Annotation {annotation_id} not found")
            return False
        
        # Create operation
        operation = AnnotationOperation(
            id=str(uuid.uuid4()),
            agent=agent,
            op=AnnotationOperationType.DELETE,
            key=annotation_id,
            metadata=metadata
        )
        
        # Apply operation
        await self._apply_operation(annotation_id, operation)
        
        logger.info(f"Deleted annotation {annotation_id} by {agent}")
        return True
    
    async def _apply_operation(self, annotation_id: str, operation: AnnotationOperation):
        """Apply an operation to the CRDT state"""
        try:
            if annotation_id not in self.states:
                # Create new state for new annotation
                if operation.op == AnnotationOperationType.ADD:
                    state = AnnotationState(
                        content=operation.value,
                        created_by=operation.agent,
                        created_at=operation.timestamp,
                        last_modified=operation.timestamp,
                        version=1,
                        metadata=operation.metadata
                    )
                    self.states[annotation_id] = state
                    self.metrics["states_created"] += 1
                else:
                    logger.error(f"Cannot apply {operation.op} to non-existent annotation {annotation_id}")
                    return
            
            state = self.states[annotation_id]
            
            # Check for conflicts
            conflicts = await self._detect_conflicts(annotation_id, operation)
            
            if conflicts:
                # Resolve conflicts
                resolved_ops = await self.conflict_resolver.operational_transform(conflicts)
                self.metrics["conflicts_resolved"] += len(conflicts)
                self.metrics["merges_performed"] += 1
                
                # Apply resolved operations
                for resolved_op in resolved_ops:
                    await self._apply_resolved_operation(annotation_id, resolved_op, state)
            else:
                # Apply operation directly
                await self._apply_direct_operation(annotation_id, operation, state)
            
            # Add to operation history
            self.operations.append(operation)
            self.metrics["operations_processed"] += 1
            
            # Notify subscribers
            await self._notify_subscribers("operation_applied", {
                "annotation_id": annotation_id,
                "operation": operation.to_dict(),
                "state": state.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Error applying operation: {e}")
    
    async def _detect_conflicts(self, annotation_id: str, 
                              new_operation: AnnotationOperation) -> List[AnnotationOperation]:
        """Detect conflicts with existing operations"""
        conflicts = []
        state = self.states[annotation_id]
        
        if not state:
            return conflicts
        
        # Check for concurrent operations on same annotation
        for op in self.operations:
            if (op.key == annotation_id and 
                op.timestamp > state.last_modified and
                op.agent != new_operation.agent):
                
                # Check for conflicting operations
                if self._operations_conflict(op, new_operation):
                    conflicts.append(op)
        
        return conflicts
    
    def _operations_conflict(self, op1: AnnotationOperation, 
                            op2: AnnotationOperation) -> bool:
        """Check if two operations conflict"""
        # Same operation type on same key
        if op1.key == op2.key and op1.op == op2.op:
            # Both add operations
            if op1.op == AnnotationOperationType.ADD:
                return True  # Two adds to same key conflict
            
            # Both delete operations
            if op1.op == AnnotationOperationType.DELETE:
                return False  # Multiple deletes are fine
            
            # Both update operations
            if op1.op == AnnotationOperationType.UPDATE:
                return True  # Two updates might conflict
        
        # Add and update on same key
        if ((op1.op == AnnotationOperationType.ADD and op2.op == AnnotationOperationType.UPDATE) or
            (op1.op == AnnotationOperationType.UPDATE and op2.op == AnnotationOperationType.ADD)):
            return True
        
        return False
    
    async def _apply_direct_operation(self, annotation_id: str, operation: AnnotationOperation,
                                  state: AnnotationState):
        """Apply operation directly without conflict resolution"""
        if operation.op == AnnotationOperationType.ADD:
            state.content = operation.value
            state.last_modified = operation.timestamp
            state.version += 1
            
        elif operation.op == AnnotationOperationType.UPDATE:
            state.content = operation.value
            state.last_modified = operation.timestamp
            state.version += 1
            
        elif operation.op == AnnotationOperationType.DELETE:
            state.content = None
            state.last_modified = operation.timestamp
            state.version += 1
            state.tombstones.add(operation.id)
        
        # Update vector clock
        state.update_vector_clock(operation.agent, operation.vector_clock)
        
        # Update merge history
        state.merge_history.append({
            "operation": operation.to_dict(),
            "timestamp": time.time(),
            "version": state.version
        })
    
    async def _apply_resolved_operation(self, annotation_id: str, resolved_op: AnnotationOperation,
                                    state: AnnotationState):
        """Apply a resolved conflict operation"""
        if resolved_op.op == AnnotationOperationType.MERGE:
            # Apply merged value
            state.content = resolved_op.value
            state.last_modified = resolved_op.timestamp
            state.version += 1
            
            # Update vector clock with max clock
            max_clock = max(op.vector_clock for op in self.operations)
            state.update_vector_clock(resolved_op.agent, max_clock)
            
            # Add conflict resolution to merge history
            state.merge_history.append({
                "conflict_resolved": True,
                "operation": resolved_op.to_dict(),
                "timestamp": time.time(),
                "version": state.version
            })
        else:
            # Apply other resolved operations directly
            await self._apply_direct_operation(annotation_id, resolved_op, state)
    
    async def sync_annotations(self, remote_operations: List[AnnotationOperation]) -> List[AnnotationOperation]:
        """Synchronize with remote operations"""
        local_ops = self.operations.copy()
        
        # Merge remote operations with local operations
        all_operations = local_ops + remote_operations
        
        # Group by annotation and key
        ops_by_annotation_key = {}
        for op in all_operations:
            key = f"{op.key}" if op.key != op.id else op.id
            if key not in ops_by_annotation_key:
                ops_by_annotation_key[key] = []
            ops_by_annotation_key[key].append(op)
        
        # Resolve conflicts for each annotation/key
        resolved_ops = []
        for key, key_ops in ops_by_annotation_key.items():
            if len(key_ops) == 1:
                resolved_ops.extend(key_ops)
            else:
                # Resolve conflicts
                resolved_key_ops = await self.conflict_resolver.merge_content(key_ops)
                resolved_ops.extend(resolved_key_ops)
        
        # Apply resolved operations
        for op in resolved_ops:
            if op.key != op.id:  # Regular operation
                await self._apply_operation(op.key, op)
            else:  # Operation on annotation itself
                await self._apply_operation(op.id, op)
        
        return resolved_ops
    
    async def get_annotation(self, annotation_id: str) -> Optional[AnnotationState]:
        """Get annotation state by ID"""
        return self.states.get(annotation_id)
    
    async def get_annotations_by_agent(self, agent: str) -> List[Tuple[str, AnnotationState]]:
        """Get all annotations created by an agent"""
        annotations = []
        
        for annotation_id, state in self.states.items():
            if state.created_by == agent:
                annotations.append((annotation_id, state))
        
        return annotations
    
    async def get_annotation_history(self, annotation_id: str) -> List[Dict[str, Any]]:
        """Get operation history for an annotation"""
        state = self.states.get(annotation_id)
        if not state:
            return []
        
        return state.merge_history
    
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
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get CRDT metrics"""
        return {
            **self.metrics,
            "total_annotations": len(self.states),
            "total_operations": len(self.operations),
            "average_conflicts_per_operation": (
                self.metrics["conflicts_resolved"] / max(1, self.metrics["operations_processed"])
                if self.metrics["operations_processed"] > 0 else 0
            )
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export entire CRDT state"""
        return {
            "node_id": self.node_id,
            "states": {aid: state.to_dict() for aid, state in self.states.items()},
            "operations": [op.to_dict() for op in self.operations],
            "metrics": self.metrics,
            "export_timestamp": time.time()
        }
    
    def import_state(self, export_data: Dict[str, Any]) -> bool:
        """Import CRDT state from export"""
        try:
            # Import states
            for annotation_id, state_data in export_data["states"].items():
                state = AnnotationState(
                    content=state_data["content"],
                    created_by=state_data["created_by"],
                    created_at=state_data["created_at"],
                    last_modified=state_data["last_modified"],
                    version=state_data["version"],
                    metadata=state_data.get("metadata", {}),
                    vector_clocks=state_data.get("vector_clocks", {}),
                    tombstones=set(state_data.get("tombstones", []))
                )
                
                # Import merge history
                for merge_data in state_data.get("merge_history", []):
                    state.merge_history.append(merge_data)
                
                self.states[annotation_id] = state
            
            # Import operations
            for op_data in export_data["operations"]:
                operation = AnnotationOperation.from_dict(op_data)
                self.operations.append(operation)
            
            # Import metrics
            self.metrics = export_data.get("metrics", {})
            
            logger.info(f"Imported CRDT state with {len(self.states)} annotations")
            return True
            
        except Exception as e:
            logger.error(f"Error importing CRDT state: {e}")
            return False
