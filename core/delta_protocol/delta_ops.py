"""
Delta Protocol Operations
Defines standardized delta operations for collaborative editing
Inspired by JSON Patch and Operational Transform
"""

import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DeltaType(Enum):
    """Supported delta operation types"""
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"
    COPY = "copy"
    REPLACE = "replace"


@dataclass
class DeltaOperation:
    """Standardized delta operation"""
    op: DeltaType
    path: str
    value: Any = None
    old_value: Any = None
    position: Optional[int] = None
    from_path: Optional[str] = None  # For move/copy operations
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "op": self.op.value,
            "path": self.path
        }
        
        if self.value is not None:
            result["value"] = self.value
        if self.old_value is not None:
            result["oldValue"] = self.old_value
        if self.position is not None:
            result["position"] = self.position
        if self.from_path is not None:
            result["from"] = self.from_path
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeltaOperation':
        """Create from dictionary representation"""
        return cls(
            op=DeltaType(data["op"]),
            path=data["path"],
            value=data.get("value"),
            old_value=data.get("oldValue"),
            position=data.get("position"),
            from_path=data.get("from"),
            metadata=data.get("metadata", {})
        )


class DeltaProtocol:
    """Protocol for creating, validating, and applying delta operations"""
    
    @staticmethod
    def insert(path: str, value: Any, position: Optional[int] = None, 
               metadata: Dict[str, Any] = None) -> DeltaOperation:
        """Create an insert delta operation"""
        return DeltaOperation(
            op=DeltaType.INSERT,
            path=path,
            value=value,
            position=position,
            metadata=metadata or {}
        )
    
    @staticmethod
    def delete(path: str, position: Optional[int] = None,
               metadata: Dict[str, Any] = None) -> DeltaOperation:
        """Create a delete delta operation"""
        return DeltaOperation(
            op=DeltaType.DELETE,
            path=path,
            position=position,
            metadata=metadata or {}
        )
    
    @staticmethod
    def update(path: str, value: Any, old_value: Any = None,
               position: Optional[int] = None, metadata: Dict[str, Any] = None) -> DeltaOperation:
        """Create an update delta operation"""
        return DeltaOperation(
            op=DeltaType.UPDATE,
            path=path,
            value=value,
            old_value=old_value,
            position=position,
            metadata=metadata or {}
        )
    
    @staticmethod
    def move(from_path: str, to_path: str, position: Optional[int] = None,
              metadata: Dict[str, Any] = None) -> DeltaOperation:
        """Create a move delta operation"""
        return DeltaOperation(
            op=DeltaType.MOVE,
            path=to_path,
            from_path=from_path,
            position=position,
            metadata=metadata or {}
        )
    
    @staticmethod
    def copy(from_path: str, to_path: str, position: Optional[int] = None,
              metadata: Dict[str, Any] = None) -> DeltaOperation:
        """Create a copy delta operation"""
        return DeltaOperation(
            op=DeltaType.COPY,
            path=to_path,
            from_path=from_path,
            position=position,
            metadata=metadata or {}
        )
    
    @staticmethod
    def replace(path: str, old_value: Any, new_value: Any,
                metadata: Dict[str, Any] = None) -> DeltaOperation:
        """Create a replace delta operation (atomic update)"""
        return DeltaOperation(
            op=DeltaType.REPLACE,
            path=path,
            value=new_value,
            old_value=old_value,
            metadata=metadata or {}
        )
    
    @staticmethod
    def validate_delta(delta: DeltaOperation) -> bool:
        """Validate delta operation structure"""
        if not delta.path:
            return False
        
        if delta.op == DeltaType.INSERT and delta.value is None:
            return False
        
        if delta.op == DeltaType.DELETE:
            return True  # Delete operations don't need values
        
        if delta.op in [DeltaType.UPDATE, DeltaType.REPLACE] and delta.value is None:
            return False
        
        if delta.op in [DeltaType.MOVE, DeltaType.COPY] and not delta.from_path:
            return False
        
        return True
    
    @staticmethod
    def apply_delta(state: Dict[str, Any], delta: DeltaOperation) -> Dict[str, Any]:
        """Apply a single delta operation to state"""
        new_state = json.loads(json.dumps(state))  # Deep copy
        
        try:
            if delta.op == DeltaType.INSERT:
                DeltaProtocol._apply_insert(new_state, delta)
            elif delta.op == DeltaType.DELETE:
                DeltaProtocol._apply_delete(new_state, delta)
            elif delta.op == DeltaType.UPDATE:
                DeltaProtocol._apply_update(new_state, delta)
            elif delta.op == DeltaType.MOVE:
                DeltaProtocol._apply_move(new_state, delta)
            elif delta.op == DeltaType.COPY:
                DeltaProtocol._apply_copy(new_state, delta)
            elif delta.op == DeltaType.REPLACE:
                DeltaProtocol._apply_replace(new_state, delta)
        except (KeyError, IndexError, TypeError):
            # Delta application failed - return original state
            return state
        
        return new_state
    
    @staticmethod
    def _navigate_to_target(state: Dict[str, Any], path: str) -> tuple:
        """Navigate to target location in state"""
        path_parts = path.strip('/').split('/')
        current = state
        
        # Navigate to parent of target
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        target_key = path_parts[-1] if path_parts else ""
        return current, target_key
    
    @staticmethod
    def _apply_insert(state: Dict[str, Any], delta: DeltaOperation):
        """Apply insert operation"""
        current, target_key = DeltaProtocol._navigate_to_target(state, delta.path)
        
        if delta.position is not None and isinstance(current.get(target_key), list):
            current[target_key].insert(delta.position, delta.value)
        else:
            current[target_key] = delta.value
    
    @staticmethod
    def _apply_delete(state: Dict[str, Any], delta: DeltaOperation):
        """Apply delete operation"""
        current, target_key = DeltaProtocol._navigate_to_target(state, delta.path)
        
        if target_key in current:
            if delta.position is not None and isinstance(current[target_key], list):
                del current[target_key][delta.position]
            else:
                del current[target_key]
    
    @staticmethod
    def _apply_update(state: Dict[str, Any], delta: DeltaOperation):
        """Apply update operation"""
        current, target_key = DeltaProtocol._navigate_to_target(state, delta.path)
        
        if target_key in current:
            if delta.position is not None and isinstance(current[target_key], list):
                current[target_key][delta.position] = delta.value
            else:
                current[target_key] = delta.value
    
    @staticmethod
    def _apply_move(state: Dict[str, Any], delta: DeltaOperation):
        """Apply move operation"""
        # Get source value
        source_current, source_key = DeltaProtocol._navigate_to_target(state, delta.from_path)
        
        if source_key in source_current:
            value = source_current[source_key]
            
            # Remove from source
            del source_current[source_key]
            
            # Insert at destination
            DeltaProtocol._apply_insert(state, DeltaOperation(
                op=DeltaType.INSERT,
                path=delta.path,
                value=value,
                position=delta.position
            ))
    
    @staticmethod
    def _apply_copy(state: Dict[str, Any], delta: DeltaOperation):
        """Apply copy operation"""
        # Get source value
        source_current, source_key = DeltaProtocol._navigate_to_target(state, delta.from_path)
        
        if source_key in source_current:
            value = source_current[source_key]
            
            # Insert copy at destination
            DeltaProtocol._apply_insert(state, DeltaOperation(
                op=DeltaType.INSERT,
                path=delta.path,
                value=value,
                position=delta.position
            ))
    
    @staticmethod
    def _apply_replace(state: Dict[str, Any], delta: DeltaOperation):
        """Apply replace operation (atomic)"""
        current, target_key = DeltaProtocol._navigate_to_target(state, delta.path)
        
        # Only replace if current value matches old_value
        if target_key in current and current[target_key] == delta.old_value:
            current[target_key] = delta.value
    
    @staticmethod
    def transform_deltas(delta1: DeltaOperation, delta2: DeltaOperation) -> tuple:
        """
        Transform two concurrent deltas to resolve conflicts
        Returns transformed deltas that can be applied in sequence
        """
        # Simplified operational transform
        # In a real implementation, this would be more sophisticated
        
        if delta1.path == delta2.path:
            # Same path - need to resolve conflict
            if delta1.op == DeltaType.INSERT and delta2.op == DeltaType.INSERT:
                # Both inserting at same location - order by timestamp
                if delta1.metadata.get('timestamp', 0) < delta2.metadata.get('timestamp', 0):
                    delta2.position = (delta2.position or 0) + 1
                else:
                    delta1.position = (delta1.position or 0) + 1
        
        return delta1, delta2
    
    @staticmethod
    def compress_deltas(deltas: List[DeltaOperation]) -> List[DeltaOperation]:
        """Compress a list of deltas by merging compatible operations"""
        if not deltas:
            return []
        
        compressed = [deltas[0]]
        
        for delta in deltas[1:]:
            last = compressed[-1]
            
            # Try to merge with last delta
            if (delta.op == last.op and 
                delta.path == last.path and
                delta.op in [DeltaType.UPDATE, DeltaType.REPLACE]):
                # Merge update operations
                last.value = delta.value
                last.old_value = delta.old_value
            else:
                compressed.append(delta)
        
        return compressed
