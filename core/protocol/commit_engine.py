"""
Advanced Commit / Delta Synchronization Engine
Inspired by Syn with CRDT operations and conflict resolution
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations in commits"""
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"
    COPY = "copy"
    MERGE = "merge"
    ANNOTATE = "annotate"


@dataclass
class Delta:
    """Delta operation for collaborative editing"""
    def __init__(self, op: OperationType, path: str, value: Any = None, 
                 old_value: Any = None, position: Optional[int] = None,
                 from_path: Optional[str] = None, metadata: Dict[str, Any] = None):
        self.op = op
        self.path = path
        self.value = value
        self.old_value = old_value
        self.position = position
        self.from_path = from_path
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique delta ID"""
        content = f"{self.op.value}{self.path}{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "op": self.op.value,
            "path": self.path,
            "value": self.value,
            "old_value": self.old_value,
            "position": self.position,
            "from_path": self.from_path,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Delta':
        """Create from dictionary"""
        return cls(
            op=OperationType(data["op"]),
            path=data["path"],
            value=data.get("value"),
            old_value=data.get("old_value"),
            position=data.get("position"),
            from_path=data.get("from_path"),
            metadata=data.get("metadata", {})
        )


@dataclass
class Commit:
    """Git-style commit with advanced features"""
    def __init__(self, parent: Optional[str], author: str, deltas: List[Delta],
                 message: str = "", branch: str = "main", 
                 tags: List[str] = None, metadata: Dict[str, Any] = None):
        self.parent = parent
        self.author = author
        self.deltas = deltas
        self.message = message
        self.branch = branch
        self.tags = tags or []
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.id = self._generate_id()
        self.signature = None
    
    def _generate_id(self) -> str:
        """Generate unique commit ID"""
        content = f"{self.parent or 'root'}{self.author}{self.timestamp}{len(self.deltas)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def serialize(self) -> str:
        """Serialize commit for hashing"""
        payload = {
            "parent": self.parent,
            "author": self.author,
            "timestamp": self.timestamp,
            "deltas": [d.to_dict() for d in self.deltas],
            "message": self.message,
            "branch": self.branch,
            "tags": self.tags,
            "metadata": self.metadata
        }
        return json.dumps(payload, sort_keys=True, separators=(',', ':'))
    
    def hash(self) -> str:
        """Generate commit hash"""
        return hashlib.sha256(self.serialize().encode()).hexdigest()
    
    def sign(self, private_key) -> str:
        """Sign commit with private key"""
        commit_hash = self.hash()
        # In real implementation, would use actual cryptographic signing
        self.signature = f"signed_{commit_hash}_{private_key[:8]}"
        return self.signature
    
    def verify(self, public_key: str) -> bool:
        """Verify commit signature"""
        if not self.signature:
            return False
        # In real implementation, would verify actual signature
        expected = f"signed_{self.hash()}_{public_key[:8]}"
        return self.signature == expected


class ConflictResolver:
    """Advanced conflict resolution for CRDT operations"""
    
    def __init__(self):
        self.resolution_strategies = {
            "last_writer_wins": self._last_writer_wins,
            "merge_content": self._merge_content,
            "operational_transform": self._operational_transform,
            "voting": self._voting_resolution
        }
    
    async def resolve_conflicts(self, commits: List[Commit], 
                            current_state: Dict[str, Any]) -> List[Commit]:
        """Resolve conflicts between multiple commits"""
        if len(commits) <= 1:
            return commits
        
        # Group conflicts by path
        conflicts_by_path = self._group_conflicts_by_path(commits)
        
        resolved_commits = []
        
        for path, conflict_group in conflicts_by_path.items():
            if len(conflict_group) == 1:
                resolved_commits.extend(conflict_group)
            else:
                # Choose resolution strategy based on operation types
                strategy = self._choose_resolution_strategy(conflict_group)
                resolved = await self.resolution_strategies[strategy](conflict_group, current_state)
                resolved_commits.extend(resolved)
        
        return resolved_commits
    
    def _group_conflicts_by_path(self, commits: List[Commit]) -> Dict[str, List[Commit]]:
        """Group conflicting commits by the paths they modify"""
        conflicts = {}
        
        for commit in commits:
            for delta in commit.deltas:
                path = delta.path
                if path not in conflicts:
                    conflicts[path] = []
                conflicts[path].append(commit)
        
        return conflicts
    
    def _choose_resolution_strategy(self, conflict_group: List[Commit]) -> str:
        """Choose best resolution strategy for conflict group"""
        # Analyze operation types
        ops = [delta.op for commit in conflict_group for delta in commit.deltas]
        
        if all(op == OperationType.INSERT for op in ops):
            return "merge_content"
        elif any(op == OperationType.DELETE for op in ops):
            return "last_writer_wins"
        elif any(op == OperationType.UPDATE for op in ops):
            return "operational_transform"
        else:
            return "last_writer_wins"
    
    async def _last_writer_wins(self, conflict_group: List[Commit], 
                               current_state: Dict[str, Any]) -> List[Commit]:
        """Last writer wins resolution"""
        # Sort by timestamp
        sorted_commits = sorted(conflict_group, key=lambda c: c.timestamp, reverse=True)
        return sorted_commits[:1]  # Return only the latest commit
    
    async def _merge_content(self, conflict_group: List[Commit], 
                          current_state: Dict[str, Any]) -> List[Commit]:
        """Merge content from conflicting commits"""
        # Combine insertions and updates
        merged_content = {}
        
        for commit in conflict_group:
            for delta in commit.deltas:
                if delta.op == OperationType.INSERT:
                    if delta.path not in merged_content:
                        merged_content[delta.path] = []
                    if isinstance(merged_content[delta.path], list):
                        merged_content[delta.path].append(delta.value)
                elif delta.op == OperationType.UPDATE:
                    merged_content[delta.path] = delta.value
        
        # Create merge commit
        merge_deltas = [
            Delta(OperationType.UPDATE, path, value)
            for path, value in merged_content.items()
        ]
        
        merge_commit = Commit(
            parent=None,
            author="conflict_resolver",
            deltas=merge_deltas,
            message="Auto-merged conflicting changes",
            metadata={"auto_merge": True, "merged_from": [c.id for c in conflict_group]}
        )
        
        return [merge_commit]
    
    async def _operational_transform(self, conflict_group: List[Commit], 
                                current_state: Dict[str, Any]) -> List[Commit]:
        """Operational transform resolution"""
        # Transform operations to be concurrent-safe
        transformed_deltas = []
        
        # Sort by timestamp
        sorted_commits = sorted(conflict_group, key=lambda c: c.timestamp)
        
        for commit in sorted_commits:
            for delta in commit.deltas:
                # Transform delta based on previous operations
                transformed_delta = await self._transform_delta(delta, transformed_deltas)
                transformed_deltas.append(transformed_delta)
        
        transform_commit = Commit(
            parent=None,
            author="operational_transform",
            deltas=transformed_deltas,
            message="Operational transform applied",
            metadata={"ot_transform": True}
        )
        
        return [transform_commit]
    
    async def _transform_delta(self, delta: Delta, previous_deltas: List[Delta]) -> Delta:
        """Transform a delta based on previous operations"""
        # Simplified OT - in real implementation would be more sophisticated
        if delta.op == OperationType.INSERT and delta.position is not None:
            # Adjust position based on previous insertions
            for prev_delta in previous_deltas:
                if (prev_delta.path == delta.path and 
                    prev_delta.op == OperationType.INSERT and 
                    prev_delta.position is not None and
                    prev_delta.position <= delta.position):
                    delta.position += 1
        
        return delta
    
    async def _voting_resolution(self, conflict_group: List[Commit], 
                               current_state: Dict[str, Any]) -> List[Commit]:
        """Voting-based conflict resolution"""
        # In real implementation, would collect votes from network participants
        # For now, use timestamp as proxy for consensus
        return await self._last_writer_wins(conflict_group, current_state)


class CommitEngine:
    """Advanced commit engine with CRDT support"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.commits: List[Commit] = []
        self.branches: Dict[str, str] = {"main": None}  # branch -> latest commit hash
        self.tags: Dict[str, str] = {}  # tag -> commit hash
        self.state: Dict[str, Any] = {}
        self.conflict_resolver = ConflictResolver()
        self.subscribers: List[Callable] = []
        
        # Performance metrics
        self.metrics = {
            "commits_created": 0,
            "conflicts_resolved": 0,
            "branches_created": 0,
            "tags_created": 0
        }
    
    def subscribe(self, callback: Callable):
        """Subscribe to commit events"""
        self.subscribers.append(callback)
    
    async def create_commit(self, deltas: List[Delta], author: str, 
                        message: str = "", branch: str = "main",
                        parent: Optional[str] = None, tags: List[str] = None,
                        auto_resolve: bool = True) -> Commit:
        """Create a new commit with conflict resolution"""
        
        # Get parent commit if not specified
        if parent is None:
            parent = self.branches.get(branch)
        
        # Create commit
        commit = Commit(
            parent=parent,
            author=author,
            deltas=deltas,
            message=message,
            branch=branch,
            tags=tags,
            metadata={"node_id": self.node_id}
        )
        
        # Check for conflicts
        conflicts = await self._detect_conflicts(commit)
        
        if conflicts and auto_resolve:
            # Resolve conflicts
            resolved_commits = await self.conflict_resolver.resolve_conflicts(
                [commit] + conflicts, self.state
            )
            commit = resolved_commits[0]  # Use resolved commit
            self.metrics["conflicts_resolved"] += 1
        
        # Add to commits
        self.commits.append(commit)
        
        # Update branch pointer
        self.branches[branch] = commit.id
        
        # Apply deltas to state
        await self._apply_deltas(commit.deltas)
        
        # Update tags
        if tags:
            for tag in tags:
                self.tags[tag] = commit.id
                self.metrics["tags_created"] += 1
        
        # Update metrics
        self.metrics["commits_created"] += 1
        
        # Notify subscribers
        await self._notify_subscribers("commit_created", commit)
        
        logger.info(f"Created commit {commit.id} on branch {branch}")
        return commit
    
    async def _detect_conflicts(self, new_commit: Commit) -> List[Commit]:
        """Detect conflicts with existing commits"""
        conflicts = []
        
        if not new_commit.parent:
            return conflicts  # No conflicts for root commit
        
        # Find parent commit
        parent_commit = self._find_commit(new_commit.parent)
        if not parent_commit:
            return conflicts
        
        # Check for concurrent modifications to same paths
        parent_paths = set(delta.path for delta in parent_commit.deltas)
        new_paths = set(delta.path for delta in new_commit.deltas)
        
        # Look for commits that share parent but have different modifications
        for commit in self.commits:
            if (commit.parent == new_commit.parent and 
                commit.id != new_commit.id and
                commit.timestamp > parent_commit.timestamp):
                
                commit_paths = set(delta.path for delta in commit.deltas)
                
                # Check for overlapping paths
                if parent_paths.intersection(commit_paths) or new_paths.intersection(commit_paths):
                    conflicts.append(commit)
        
        return conflicts
    
    async def _apply_deltas(self, deltas: List[Delta]):
        """Apply deltas to current state"""
        for delta in deltas:
            await self._apply_delta(delta)
    
    async def _apply_delta(self, delta: Delta):
        """Apply a single delta to state"""
        path_parts = delta.path.strip('/').split('/')
        current = self.state
        
        # Navigate to parent
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Apply operation
        target_key = path_parts[-1] if path_parts else ""
        
        if delta.op == OperationType.INSERT:
            if delta.position is not None and isinstance(current.get(target_key), list):
                current[target_key].insert(delta.position, delta.value)
            else:
                current[target_key] = delta.value
                
        elif delta.op == OperationType.DELETE:
            if delta.position is not None and isinstance(current.get(target_key), list):
                del current[target_key][delta.position]
            else:
                current.pop(target_key, None)
                
        elif delta.op == OperationType.UPDATE:
            current[target_key] = delta.value
            
        elif delta.op == OperationType.MOVE:
            if delta.from_path:
                from_parts = delta.from_path.strip('/').split('/')
                from_current = self.state
                
                # Navigate to source
                for part in from_parts[:-1]:
                    if part not in from_current:
                        from_current[part] = {}
                    from_current = from_current[part]
                
                from_key = from_parts[-1] if from_parts else ""
                if from_key in from_current:
                    value = from_current[from_key]
                    del from_current[from_key]
                    
                    # Insert at destination
                    if delta.position is not None and isinstance(current.get(target_key), list):
                        current[target_key].insert(delta.position, value)
                    else:
                        current[target_key] = value
    
    def _find_commit(self, commit_id: str) -> Optional[Commit]:
        """Find commit by ID"""
        for commit in self.commits:
            if commit.id == commit_id:
                return commit
        return None
    
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
    
    def get_commit_history(self, branch: str = "main", limit: Optional[int] = None) -> List[Commit]:
        """Get commit history for a branch"""
        # Filter commits by branch
        branch_commits = [
            commit for commit in self.commits 
            if commit.branch == branch
        ]
        
        # Sort by timestamp
        branch_commits.sort(key=lambda c: c.timestamp, reverse=True)
        
        if limit:
            return branch_commits[:limit]
        
        return branch_commits
    
    def get_branches(self) -> Dict[str, str]:
        """Get all branches and their latest commits"""
        return self.branches.copy()
    
    def create_branch(self, branch_name: str, from_commit: Optional[str] = None) -> str:
        """Create a new branch"""
        if from_commit is None:
            from_commit = self.branches.get("main")
        
        self.branches[branch_name] = from_commit
        self.metrics["branches_created"] += 1
        
        logger.info(f"Created branch {branch_name} from commit {from_commit}")
        return from_commit
    
    def merge_branch(self, source_branch: str, target_branch: str = "main") -> Optional[str]:
        """Merge source branch into target branch"""
        source_commit = self.branches.get(source_branch)
        target_commit = self.branches.get(target_branch)
        
        if not source_commit:
            logger.error(f"Source branch {source_branch} not found")
            return None
        
        # Create merge commit
        merge_delta = Delta(
            OperationType.MERGE,
            f"/branches/{target_branch}",
            source_commit,
            metadata={"merge_from": source_branch, "merge_to": target_branch}
        )
        
        # In real implementation, would handle merge conflicts
        merge_commit = Commit(
            parent=target_commit,
            author=f"{self.node_id}_merger",
            deltas=[merge_delta],
            message=f"Merge branch '{source_branch}' into '{target_branch}'",
            branch=target_branch
        )
        
        self.commits.append(merge_commit)
        self.branches[target_branch] = merge_commit.id
        
        logger.info(f"Merged {source_branch} into {target_branch}")
        return merge_commit.id
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return self.state.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.metrics,
            "total_commits": len(self.commits),
            "total_branches": len(self.branches),
            "total_tags": len(self.tags),
            "state_size": len(str(self.state))
        }
    
    def export_state(self) -> str:
        """Export entire state for backup"""
        export_data = {
            "commits": [commit.serialize() for commit in self.commits],
            "branches": self.branches,
            "tags": self.tags,
            "state": self.state,
            "metrics": self.metrics,
            "export_timestamp": time.time(),
            "node_id": self.node_id
        }
        
        return json.dumps(export_data, indent=2)
    
    def import_state(self, export_data: str) -> bool:
        """Import state from backup"""
        try:
            data = json.loads(export_data)
            
            # Import commits
            self.commits = []
            for commit_data in data["commits"]:
                # Reconstruct commits
                deltas = [Delta.from_dict(d) for d in commit_data["deltas"]]
                commit = Commit(
                    parent=commit_data["parent"],
                    author=commit_data["author"],
                    deltas=deltas,
                    message=commit_data["message"],
                    branch=commit_data["branch"],
                    tags=commit_data.get("tags", []),
                    metadata=commit_data.get("metadata", {})
                )
                commit.id = commit_data.get("id", commit.hash())
                self.commits.append(commit)
            
            # Import branches and tags
            self.branches = data["branches"]
            self.tags = data["tags"]
            self.state = data["state"]
            self.metrics = data.get("metrics", {})
            
            logger.info(f"Imported state with {len(self.commits)} commits")
            return True
            
        except Exception as e:
            logger.error(f"Error importing state: {e}")
            return False
