"""
Core Commit Engine for Distributed Collaborative Platform
Git-inspired commit system with Holochain integration
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


@dataclass
class Delta:
    """Represents a single delta operation"""
    op: str  # "insert", "delete", "update", "move"
    path: str  # JSON path to the target
    value: Any = None  # New value for insert/update
    old_value: Any = None  # Previous value for update
    position: Optional[int] = None  # Position for insert/move


@dataclass
class Commit:
    """Git-inspired commit structure for distributed collaboration"""
    commit_id: str
    parent: Optional[str]  # Previous commit hash
    author: str  # Agent public key
    timestamp: float
    deltas: List[Delta]
    signature: str
    message: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CommitEngine:
    """Core engine for creating, validating, and managing commits"""
    
    def __init__(self, agent_private_key: Optional[rsa.RSAPrivateKey] = None):
        self.agent_private_key = agent_private_key or self._generate_key_pair()
        self.agent_public_key = self.agent_private_key.public_key()
        self.local_chain = []  # Local source chain
        
    def _generate_key_pair(self) -> rsa.RSAPrivateKey:
        """Generate RSA key pair for agent identity"""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
    
    def _hash_commit(self, commit_data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of commit data"""
        commit_json = json.dumps(commit_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(commit_json.encode()).hexdigest()
    
    def _sign_commit(self, commit_hash: str) -> str:
        """Sign commit hash with private key"""
        signature = self.agent_private_key.sign(
            commit_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()
    
    def create_commit(self, deltas: List[Delta], parent: Optional[str] = None, 
                     message: str = "", metadata: Dict[str, Any] = None) -> Commit:
        """Create a new commit with delta operations"""
        if not self.local_chain and parent is not None:
            raise ValueError("Cannot specify parent for first commit")
        
        if self.local_chain and parent is None:
            parent = self.local_chain[-1].commit_id
        
        # Prepare commit data for hashing
        commit_data = {
            "parent": parent,
            "author": self.agent_public_key.public_numbers().n.__str__(),  # Simplified for demo
            "timestamp": time.time(),
            "deltas": [asdict(delta) for delta in deltas],
            "message": message,
            "metadata": metadata or {}
        }
        
        commit_hash = self._hash_commit(commit_data)
        signature = self._sign_commit(commit_hash)
        
        commit = Commit(
            commit_id=commit_hash,
            parent=parent,
            author=commit_data["author"],
            timestamp=commit_data["timestamp"],
            deltas=deltas,
            signature=signature,
            message=message,
            metadata=metadata or {}
        )
        
        self.local_chain.append(commit)
        return commit
    
    def verify_commit(self, commit: Commit, public_key: rsa.RSAPublicKey) -> bool:
        """Verify commit signature and integrity"""
        try:
            # Reconstruct commit data for verification
            commit_data = {
                "parent": commit.parent,
                "author": commit.author,
                "timestamp": commit.timestamp,
                "deltas": [asdict(delta) for delta in commit.deltas],
                "message": commit.message,
                "metadata": commit.metadata
            }
            
            expected_hash = self._hash_commit(commit_data)
            
            # Verify signature
            public_key.verify(
                bytes.fromhex(commit.signature),
                expected_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return commit.commit_id == expected_hash
        except Exception:
            return False
    
    def apply_deltas(self, state: Dict[str, Any], deltas: List[Delta]) -> Dict[str, Any]:
        """Apply delta operations to current state"""
        new_state = json.loads(json.dumps(state))  # Deep copy
        
        for delta in deltas:
            self._apply_single_delta(new_state, delta)
        
        return new_state
    
    def _apply_single_delta(self, state: Dict[str, Any], delta: Delta):
        """Apply a single delta operation"""
        path_parts = delta.path.strip('/').split('/')
        current = state
        
        # Navigate to parent of target
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        target_key = path_parts[-1] if path_parts else ""
        
        if delta.op == "insert":
            if delta.position is not None and isinstance(current.get(target_key), list):
                current[target_key].insert(delta.position, delta.value)
            else:
                current[target_key] = delta.value
                
        elif delta.op == "delete":
            if target_key in current:
                if delta.position is not None and isinstance(current[target_key], list):
                    del current[target_key][delta.position]
                else:
                    del current[target_key]
                    
        elif delta.op == "update":
            if target_key in current:
                if delta.position is not None and isinstance(current[target_key], list):
                    current[target_key][delta.position] = delta.value
                else:
                    current[target_key] = delta.value
                    
        elif delta.op == "move":
            # Simplified move operation
            if target_key in current and delta.position is not None:
                value = current[target_key]
                del current[target_key]
                current[target_key] = value
    
    def get_commit_history(self, limit: Optional[int] = None) -> List[Commit]:
        """Get commit history from local chain"""
        if limit:
            return self.local_chain[-limit:]
        return self.local_chain
    
    def rebuild_state(self, from_commit: Optional[str] = None) -> Dict[str, Any]:
        """Rebuild state by applying commits from a starting point"""
        state = {}
        start_index = 0
        
        if from_commit:
            for i, commit in enumerate(self.local_chain):
                if commit.commit_id == from_commit:
                    start_index = i + 1
                    break
        
        for commit in self.local_chain[start_index:]:
            state = self.apply_deltas(state, commit.deltas)
        
        return state
