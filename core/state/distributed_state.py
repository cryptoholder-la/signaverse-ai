"""
Distributed State Management
Handles state reconstruction and synchronization across the network
Inspired by Holochain Syn and CRDT systems
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from core.delta_protocol.delta_ops import DeltaProtocol, DeltaOperation

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of distributed state"""
    SIGN_MEDIA = "sign_media"
    TRANSLATIONS = "translations"
    ANNOTATIONS = "annotations"
    REPUTATION = "reputation"
    DATASETS = "datasets"


@dataclass
class StateSnapshot:
    """Snapshot of distributed state at a point in time"""
    timestamp: float
    state_hash: str
    state_data: Dict[str, Any]
    commit_hashes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DistributedState:
    """Manages distributed state reconstruction and CRDT operations"""
    
    def __init__(self):
        self.commits: List[Dict[str, Any]] = []
        self.state: Dict[str, Any] = {
            StateType.SIGN_MEDIA.value: {},
            StateType.TRANSLATIONS.value: {},
            StateType.ANNOTATIONS.value: {},
            StateType.REPUTATION.value: {},
            StateType.DATASETS.value: {}
        }
        self.snapshots: List[StateSnapshot] = []
        self.conflict_resolver = ConflictResolver()
        self.crdt_engine = CRDTEngine()
        
    async def apply_commit(self, commit: Dict[str, Any]) -> bool:
        """Apply a commit to the distributed state"""
        try:
            # Validate commit structure
            if not self._validate_commit(commit):
                logger.warning(f"Invalid commit structure: {commit.get('commit_id', 'unknown')}")
                return False
            
            # Check for conflicts
            conflicts = await self._detect_conflicts(commit)
            if conflicts:
                resolved_commit = await self.conflict_resolver.resolve(commit, conflicts, self.state)
                if not resolved_commit:
                    logger.warning(f"Could not resolve conflicts for commit {commit.get('commit_id')}")
                    return False
                commit = resolved_commit
            
            # Apply deltas
            for delta in commit.get("deltas", []):
                await self._apply_delta(delta)
            
            # Add to commit history
            self.commits.append(commit)
            
            # Create snapshot if needed
            if len(self.commits) % 10 == 0:  # Snapshot every 10 commits
                await self._create_snapshot()
            
            logger.info(f"Applied commit {commit.get('commit_id')} to distributed state")
            return True
            
        except Exception as e:
            logger.error(f"Error applying commit: {e}")
            return False
    
    async def _apply_delta(self, delta: Dict[str, Any]):
        """Apply a single delta operation"""
        op = delta.get("op")
        
        if op == "add_sign_video":
            await self._add_sign_video(delta)
        elif op == "add_translation":
            await self._add_translation(delta)
        elif op == "add_annotation":
            await self._add_annotation(delta)
        elif op == "update_reputation":
            await self._update_reputation(delta)
        elif op == "add_dataset_entry":
            await self._add_dataset_entry(delta)
        elif op == "update_translation":
            await self._update_translation(delta)
        elif op == "delete_entry":
            await self._delete_entry(delta)
        else:
            # Handle generic CRDT operations
            await self.crdt_engine.apply_operation(delta, self.state)
    
    async def _add_sign_video(self, delta: Dict[str, Any]):
        """Add a sign video entry"""
        video_hash = delta["video_hash"]
        video_data = {
            "id": video_hash,
            "uploader": delta.get("uploader", ""),
            "language": delta.get("language", "ASL"),
            "video_hash": video_hash,
            "timestamp": delta.get("timestamp", time.time()),
            "metadata": delta.get("metadata", {}),
            "annotations": [],
            "translations": []
        }
        
        self.state[StateType.SIGN_MEDIA.value][video_hash] = video_data
        
        # Update dataset if specified
        if "dataset_id" in delta:
            await self._add_to_dataset(delta["dataset_id"], video_hash, "sign_video")
    
    async def _add_translation(self, delta: Dict[str, Any]):
        """Add a translation entry"""
        translation_id = delta.get("translation_id") or f"trans_{int(time.time())}"
        translation_data = {
            "id": translation_id,
            "video_hash": delta["video_hash"],
            "text": delta["text"],
            "language": delta.get("language", "en"),
            "translator": delta.get("translator", ""),
            "confidence": delta.get("confidence", 0.0),
            "timestamp": delta.get("timestamp", time.time()),
            "annotations": [],
            "verified": False
        }
        
        self.state[StateType.TRANSLATIONS.value][translation_id] = translation_data
        
        # Link to sign video
        video_hash = delta["video_hash"]
        if video_hash in self.state[StateType.SIGN_MEDIA.value]:
            self.state[StateType.SIGN_MEDIA.value][video_hash]["translations"].append(translation_id)
        
        # Update dataset if specified
        if "dataset_id" in delta:
            await self._add_to_dataset(delta["dataset_id"], translation_id, "translation")
    
    async def _add_annotation(self, delta: Dict[str, Any]):
        """Add an annotation entry"""
        annotation_id = delta.get("annotation_id") or f"annot_{int(time.time())}"
        annotation_data = {
            "id": annotation_id,
            "target_id": delta["target_id"],  # Can be video or translation ID
            "target_type": delta.get("target_type", "translation"),
            "reviewer": delta.get("reviewer", ""),
            "correction": delta.get("correction", ""),
            "rating": delta.get("rating", 0),
            "timestamp": delta.get("timestamp", time.time()),
            "metadata": delta.get("metadata", {})
        }
        
        self.state[StateType.ANNOTATIONS.value][annotation_id] = annotation_data
        
        # Link to target
        target_id = delta["target_id"]
        if delta.get("target_type") == "translation" and target_id in self.state[StateType.TRANSLATIONS.value]:
            self.state[StateType.TRANSLATIONS.value][target_id]["annotations"].append(annotation_id)
    
    async def _update_reputation(self, delta: Dict[str, Any]):
        """Update reputation scores"""
        agent = delta["agent"]
        if agent not in self.state[StateType.REPUTATION.value]:
            self.state[StateType.REPUTATION.value][agent] = {
                "trust": 50.0,  # Start at neutral
                "contributions": 0,
                "verified_translations": 0,
                "helpful_annotations": 0,
                "last_updated": time.time()
            }
        
        rep = self.state[StateType.REPUTATION.value][agent]
        
        if "trust_delta" in delta:
            rep["trust"] = max(0, min(100, rep["trust"] + delta["trust_delta"]))
        
        if "contribution_type" in delta:
            rep["contributions"] += 1
            if delta["contribution_type"] == "verified_translation":
                rep["verified_translations"] += 1
            elif delta["contribution_type"] == "helpful_annotation":
                rep["helpful_annotations"] += 1
        
        rep["last_updated"] = time.time()
    
    async def _add_dataset_entry(self, delta: Dict[str, Any]):
        """Add entry to training dataset"""
        dataset_id = delta["dataset_id"]
        if dataset_id not in self.state[StateType.DATASETS.value]:
            self.state[StateType.DATASETS.value][dataset_id] = {
                "id": dataset_id,
                "name": delta.get("dataset_name", f"Dataset {dataset_id}"),
                "entries": [],
                "created_at": time.time(),
                "metadata": delta.get("dataset_metadata", {})
            }
        
        entry = {
            "id": delta["entry_id"],
            "type": delta["entry_type"],  # "sign_video" or "translation"
            "data": delta["entry_data"],
            "added_at": time.time(),
            "quality_score": delta.get("quality_score", 0.0)
        }
        
        self.state[StateType.DATASETS.value][dataset_id]["entries"].append(entry)
    
    async def _add_to_dataset(self, dataset_id: str, entry_id: str, entry_type: str):
        """Helper to add entry to dataset"""
        if dataset_id not in self.state[StateType.DATASETS.value]:
            self.state[StateType.DATASETS.value][dataset_id] = {
                "id": dataset_id,
                "name": f"Dataset {dataset_id}",
                "entries": [],
                "created_at": time.time(),
                "metadata": {}
            }
        
        entry = {
            "id": entry_id,
            "type": entry_type,
            "added_at": time.time()
        }
        
        self.state[StateType.DATASETS.value][dataset_id]["entries"].append(entry)
    
    async def _update_translation(self, delta: Dict[str, Any]):
        """Update existing translation"""
        translation_id = delta["translation_id"]
        if translation_id in self.state[StateType.TRANSLATIONS.value]:
            translation = self.state[StateType.TRANSLATIONS.value][translation_id]
            
            if "text" in delta:
                translation["text"] = delta["text"]
            if "confidence" in delta:
                translation["confidence"] = delta["confidence"]
            if "verified" in delta:
                translation["verified"] = delta["verified"]
            
            translation["last_updated"] = time.time()
    
    async def _delete_entry(self, delta: Dict[str, Any]):
        """Delete an entry from state"""
        entry_type = delta["entry_type"]
        entry_id = delta["entry_id"]
        
        if entry_type == "sign_video" and entry_id in self.state[StateType.SIGN_MEDIA.value]:
            del self.state[StateType.SIGN_MEDIA.value][entry_id]
        elif entry_type == "translation" and entry_id in self.state[StateType.TRANSLATIONS.value]:
            del self.state[StateType.TRANSLATIONS.value][entry_id]
        elif entry_type == "annotation" and entry_id in self.state[StateType.ANNOTATIONS.value]:
            del self.state[StateType.ANNOTATIONS.value][entry_id]
    
    async def _detect_conflicts(self, new_commit: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential conflicts with existing state"""
        conflicts = []
        
        for delta in new_commit.get("deltas", []):
            op = delta.get("op")
            
            if op in ["add_translation", "update_translation"]:
                video_hash = delta.get("video_hash")
                existing_translations = [
                    trans for trans in self.state[StateType.TRANSLATIONS.value].values()
                    if trans.get("video_hash") == video_hash
                ]
                
                if existing_translations:
                    conflicts.append({
                        "type": "translation_conflict",
                        "delta": delta,
                        "existing": existing_translations
                    })
        
        return conflicts
    
    def _validate_commit(self, commit: Dict[str, Any]) -> bool:
        """Validate commit structure"""
        required_fields = ["commit_id", "author", "timestamp", "deltas"]
        
        for field in required_fields:
            if field not in commit:
                return False
        
        # Validate deltas
        deltas = commit["deltas"]
        if not isinstance(deltas, list) or len(deltas) == 0:
            return False
        
        return True
    
    async def _create_snapshot(self):
        """Create a snapshot of current state"""
        import hashlib
        
        state_json = json.dumps(self.state, sort_keys=True)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()
        
        snapshot = StateSnapshot(
            timestamp=time.time(),
            state_hash=state_hash,
            state_data=json.loads(state_json),
            commit_hashes=[c.get("commit_id") for c in self.commits[-10:]]
        )
        
        self.snapshots.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]
        
        logger.info(f"Created state snapshot {state_hash}")
    
    def get_state(self, state_type: Optional[StateType] = None) -> Dict[str, Any]:
        """Get current state or specific state type"""
        if state_type:
            return self.state.get(state_type.value, {})
        return self.state.copy()
    
    def get_commits(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get commit history"""
        if limit:
            return self.commits[-limit:]
        return self.commits.copy()
    
    def get_snapshots(self, limit: Optional[int] = None) -> List[StateSnapshot]:
        """Get state snapshots"""
        if limit:
            return self.snapshots[-limit:]
        return self.snapshots.copy()
    
    async def rebuild_from_commits(self, commits: List[Dict[str, Any]]):
        """Rebuild state from commit history"""
        self.state = {
            StateType.SIGN_MEDIA.value: {},
            StateType.TRANSLATIONS.value: {},
            StateType.ANNOTATIONS.value: {},
            StateType.REPUTATION.value: {},
            StateType.DATASETS.value: {}
        }
        self.commits = []
        
        for commit in commits:
            await self.apply_commit(commit)
        
        logger.info(f"Rebuilt state from {len(commits)} commits")


class ConflictResolver:
    """Resolves conflicts in distributed state"""
    
    async def resolve(self, commit: Dict[str, Any], conflicts: List[Dict[str, Any]], 
                    current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Resolve conflicts and return modified commit"""
        resolved_commit = commit.copy()
        resolved_deltas = []
        
        for conflict in conflicts:
            if conflict["type"] == "translation_conflict":
                resolved_delta = await self._resolve_translation_conflict(
                    conflict["delta"], conflict["existing"], current_state
                )
                if resolved_delta:
                    resolved_deltas.append(resolved_delta)
        
        if resolved_deltas:
            resolved_commit["deltas"].extend(resolved_deltas)
            resolved_commit["conflicts_resolved"] = True
        
        return resolved_commit
    
    async def _resolve_translation_conflict(self, new_delta: Dict[str, Any], 
                                       existing_translations: List[Dict[str, Any]],
                                       current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Resolve translation conflicts by choosing highest confidence"""
        if not existing_translations:
            return new_delta
        
        # Find existing translation with highest confidence
        best_existing = max(existing_translations, key=lambda t: t.get("confidence", 0))
        new_confidence = new_delta.get("confidence", 0)
        
        if new_confidence > best_existing.get("confidence", 0):
            # New translation is better
            return {
                "op": "update_translation",
                "translation_id": best_existing["id"],
                "text": new_delta["text"],
                "confidence": new_confidence,
                "reason": "higher_confidence"
            }
        else:
            # Keep existing, but add as alternative
            return {
                "op": "add_annotation",
                "target_id": best_existing["id"],
                "target_type": "translation",
                "reviewer": new_delta.get("translator", ""),
                "correction": f"Alternative: {new_delta['text']}",
                "rating": new_confidence
            }


class CRDTEngine:
    """CRDT operations for distributed state"""
    
    def __init__(self):
        self.lww_registers = {}  # Last-Writer-Wins registers
        self.or_sets = {}  # Observed-Removed sets
    
    async def apply_operation(self, delta: Dict[str, Any], state: Dict[str, Any]):
        """Apply CRDT operation"""
        op = delta.get("op")
        
        if op == "crdt_set":
            await self._apply_lww_register(delta, state)
        elif op == "crdt_add_to_set":
            await self._apply_or_set_add(delta, state)
        elif op == "crdt_remove_from_set":
            await self._apply_or_set_remove(delta, state)
    
    async def _apply_lww_register(self, delta: Dict[str, Any], state: Dict[str, Any]):
        """Apply Last-Writer-Wins register operation"""
        key = delta["key"]
        value = delta["value"]
        timestamp = delta.get("timestamp", time.time())
        
        if key not in self.lww_registers or timestamp > self.lww_registers[key]["timestamp"]:
            self.lww_registers[key] = {
                "value": value,
                "timestamp": timestamp
            }
            
            # Apply to state
            key_parts = key.split(".")
            current = state
            for part in key_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[key_parts[-1]] = value
    
    async def _apply_or_set_add(self, delta: Dict[str, Any], state: Dict[str, Any]):
        """Add element to Observed-Removed set"""
        set_key = delta["set_key"]
        element = delta["element"]
        unique_id = delta.get("unique_id", f"{element}_{time.time()}")
        
        if set_key not in self.or_sets:
            self.or_sets[set_key] = {"added": {}, "removed": {}}
        
        self.or_sets[set_key]["added"][unique_id] = {
            "element": element,
            "timestamp": delta.get("timestamp", time.time())
        }
        
        # Apply to state
        if set_key not in state:
            state[set_key] = []
        
        if element not in state[set_key]:
            state[set_key].append(element)
    
    async def _apply_or_set_remove(self, delta: Dict[str, Any], state: Dict[str, Any]):
        """Remove element from Observed-Removed set"""
        set_key = delta["set_key"]
        element = delta["element"]
        unique_id = delta.get("unique_id", f"{element}_{time.time()}")
        
        if set_key not in self.or_sets:
            self.or_sets[set_key] = {"added": {}, "removed": {}}
        
        self.or_sets[set_key]["removed"][unique_id] = {
            "element": element,
            "timestamp": delta.get("timestamp", time.time())
        }
        
        # Apply to state
        if set_key in state and element in state[set_key]:
            state[set_key].remove(element)
