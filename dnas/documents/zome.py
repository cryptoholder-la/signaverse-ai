"""
Document Collaboration DNA Zome
Holochain zome for real-time document collaboration
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib

from core.network_layer.holochain_dna import DocumentDNA, EntryType
from core.commit_engine.commit import Commit, Delta
from core.delta_protocol.delta_ops import DeltaProtocol, DeltaOperation


@dataclass
class Document:
    """Document data structure"""
    doc_id: str
    title: str
    content: Dict[str, Any]  # Nested document structure
    author: str
    created_at: float
    updated_at: float
    version: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": self.metadata
        }


@dataclass
class Comment:
    """Comment on document content"""
    comment_id: str
    doc_id: str
    path: str  # JSON path to commented content
    content: str
    author: str
    created_at: float
    resolved: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "doc_id": self.doc_id,
            "path": self.path,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at,
            "resolved": self.resolved,
            "metadata": self.metadata
        }


@dataclass
class DocumentShare:
    """Document sharing permissions"""
    share_id: str
    doc_id: str
    owner: str
    shared_with: str
    permissions: List[str]  # ["read", "write", "comment", "admin"]
    created_at: float
    expires_at: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "share_id": self.share_id,
            "doc_id": self.doc_id,
            "owner": self.owner,
            "shared_with": self.shared_with,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "expires_at": self.expires_at
        }


class DocumentZome(DocumentDNA):
    """Document collaboration zome"""
    
    def __init__(self, agent_pubkey: str):
        super().__init__(agent_pubkey)
        self.documents: Dict[str, Document] = {}
        self.comments: Dict[str, List[Comment]] = {}
        self.shares: Dict[str, DocumentShare] = {}
        self.active_sessions: Dict[str, List[str]] = {}  # doc_id -> list of active agents
        
    def create_document(self, title: str, initial_content: Dict[str, Any], 
                       metadata: Dict[str, Any] = None) -> str:
        """Create a new document"""
        doc_id = self._generate_doc_id()
        
        document = Document(
            doc_id=doc_id,
            title=title,
            content=initial_content,
            author=self.agent_pubkey,
            created_at=time.time(),
            updated_at=time.time(),
            version=1,
            metadata=metadata or {}
        )
        
        # Store locally
        self.documents[doc_id] = document
        
        # Create Holochain entry
        entry = self.create_document_entry(document.to_dict())
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return doc_id
    
    def update_document(self, doc_id: str, deltas: List[DeltaOperation], 
                       message: str = "") -> str:
        """Update document with delta operations"""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")
        
        document = self.documents[doc_id]
        
        # Apply deltas to document content
        new_content = document.content.copy()
        for delta in deltas:
            new_content = DeltaProtocol.apply_delta(new_content, delta)
        
        # Create commit
        commit_data = {
            "doc_id": doc_id,
            "deltas": [delta.to_dict() for delta in deltas],
            "parent": document.metadata.get("last_commit"),
            "message": message,
            "timestamp": time.time()
        }
        
        # Update document
        document.content = new_content
        document.updated_at = time.time()
        document.version += 1
        
        # Store commit hash in metadata
        commit_hash = self._hash_commit_data(commit_data)
        document.metadata["last_commit"] = commit_hash
        
        # Create Holochain entries
        doc_entry = self.create_document_entry(document.to_dict())
        commit_entry = self.create_entry(EntryType.COMMIT, commit_data)
        
        # Publish to DHT
        self.publish_to_dht(doc_entry)
        self.publish_to_dht(commit_entry)
        
        return commit_hash
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID"""
        # Check local storage first
        if doc_id in self.documents:
            return self.documents[doc_id]
        
        # Try to fetch from DHT
        entries = self.query_entries(EntryType.APP_STATE)
        for entry in entries:
            if entry.data.get("type") == "document":
                doc_data = entry.data["document_data"]
                if doc_data.get("doc_id") == doc_id:
                    document = Document(
                        doc_id=doc_data["doc_id"],
                        title=doc_data["title"],
                        content=doc_data["content"],
                        author=doc_data["author"],
                        created_at=doc_data["created_at"],
                        updated_at=doc_data["updated_at"],
                        version=doc_data["version"],
                        metadata=doc_data.get("metadata", {})
                    )
                    self.documents[doc_id] = document
                    return document
        
        return None
    
    def add_comment(self, doc_id: str, path: str, content: str, 
                   metadata: Dict[str, Any] = None) -> str:
        """Add a comment to document content"""
        comment_id = self._generate_comment_id()
        
        comment = Comment(
            comment_id=comment_id,
            doc_id=doc_id,
            path=path,
            content=content,
            author=self.agent_pubkey,
            created_at=time.time(),
            resolved=False,
            metadata=metadata or {}
        )
        
        # Store locally
        if doc_id not in self.comments:
            self.comments[doc_id] = []
        self.comments[doc_id].append(comment)
        
        # Create Holochain entry
        entry = self.create_comment_entry(comment.to_dict())
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return comment_id
    
    def resolve_comment(self, comment_id: str) -> bool:
        """Resolve a comment"""
        # Find comment
        comment = None
        for doc_comments in self.comments.values():
            for c in doc_comments:
                if c.comment_id == comment_id:
                    comment = c
                    break
        
        if not comment:
            return False
        
        # Update comment
        comment.resolved = True
        
        # Create Holochain entry
        entry = self.create_comment_entry(comment.to_dict())
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return True
    
    def share_document(self, doc_id: str, shared_with: str, 
                      permissions: List[str], expires_at: Optional[float] = None) -> str:
        """Share document with another agent"""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")
        
        document = self.documents[doc_id]
        
        # Check if current user is owner or has admin permissions
        if document.author != self.agent_pubkey:
            # Check existing permissions
            existing_share = self.get_document_share(doc_id, self.agent_pubkey)
            if not existing_share or "admin" not in existing_share.permissions:
                raise PermissionError("Insufficient permissions to share document")
        
        share_id = self._generate_share_id()
        
        share = DocumentShare(
            share_id=share_id,
            doc_id=doc_id,
            owner=document.author,
            shared_with=shared_with,
            permissions=permissions,
            created_at=time.time(),
            expires_at=expires_at
        )
        
        # Store locally
        self.shares[share_id] = share
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "document_share",
            "share_data": share.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return share_id
    
    def get_document_share(self, doc_id: str, agent: str) -> Optional[DocumentShare]:
        """Get document share for agent"""
        for share in self.shares.values():
            if share.doc_id == doc_id and share.shared_with == agent:
                # Check if share hasn't expired
                if share.expires_at is None or share.expires_at > time.time():
                    return share
        
        return None
    
    def has_permission(self, doc_id: str, agent: str, required_permission: str) -> bool:
        """Check if agent has permission for document"""
        document = self.get_document(doc_id)
        if not document:
            return False
        
        # Owner has all permissions
        if document.author == agent:
            return True
        
        # Check shares
        share = self.get_document_share(doc_id, agent)
        if share and required_permission in share.permissions:
            return True
        
        return False
    
    def join_collaborative_session(self, doc_id: str) -> bool:
        """Join a collaborative editing session"""
        if not self.has_permission(doc_id, self.agent_pubkey, "read"):
            return False
        
        if doc_id not in self.active_sessions:
            self.active_sessions[doc_id] = []
        
        if self.agent_pubkey not in self.active_sessions[doc_id]:
            self.active_sessions[doc_id].append(self.agent_pubkey)
        
        return True
    
    def leave_collaborative_session(self, doc_id: str) -> bool:
        """Leave a collaborative editing session"""
        if doc_id in self.active_sessions and self.agent_pubkey in self.active_sessions[doc_id]:
            self.active_sessions[doc_id].remove(self.agent_pubkey)
            
            # Clean up empty sessions
            if not self.active_sessions[doc_id]:
                del self.active_sessions[doc_id]
            
            return True
        
        return False
    
    def get_active_sessions(self, doc_id: str) -> List[str]:
        """Get list of active agents in document session"""
        return self.active_sessions.get(doc_id, [])
    
    def get_document_history(self, doc_id: str) -> List[Dict]:
        """Get document edit history"""
        commits = []
        
        # Query commit entries
        entries = self.query_entries(EntryType.COMMIT)
        for entry in entries:
            if entry.data.get("doc_id") == doc_id:
                commits.append(entry.data)
        
        # Sort by timestamp
        commits.sort(key=lambda x: x.get("timestamp", 0))
        
        return commits
    
    def search_documents(self, query: str, author: Optional[str] = None) -> List[Document]:
        """Search documents by content or title"""
        results = []
        
        for document in self.documents.values():
            # Author filter
            if author and document.author != author:
                continue
            
            # Text search (simplified)
            if (query.lower() in document.title.lower() or 
                self._content_contains_query(document.content, query.lower())):
                results.append(document)
        
        return results
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics"""
        total_docs = len(self.documents)
        total_comments = sum(len(comments) for comments in self.comments.values())
        total_shares = len(self.shares)
        active_sessions = len(self.active_sessions)
        
        return {
            "total_documents": total_docs,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "active_sessions": active_sessions,
            "owned_documents": sum(1 for doc in self.documents.values() 
                                 if doc.author == self.agent_pubkey)
        }
    
    def _generate_doc_id(self) -> str:
        """Generate unique document ID"""
        timestamp = str(time.time())
        agent_suffix = self.agent_pubkey[:8]
        return hashlib.sha256(f"{timestamp}_{agent_suffix}".encode()).hexdigest()[:16]
    
    def _generate_comment_id(self) -> str:
        """Generate unique comment ID"""
        timestamp = str(time.time())
        agent_suffix = self.agent_pubkey[:8]
        return hashlib.sha256(f"comment_{timestamp}_{agent_suffix}".encode()).hexdigest()[:16]
    
    def _generate_share_id(self) -> str:
        """Generate unique share ID"""
        timestamp = str(time.time())
        agent_suffix = self.agent_pubkey[:8]
        return hashlib.sha256(f"share_{timestamp}_{agent_suffix}".encode()).hexdigest()[:16]
    
    def _hash_commit_data(self, commit_data: Dict[str, Any]) -> str:
        """Generate hash for commit data"""
        commit_json = json.dumps(commit_data, sort_keys=True)
        return hashlib.sha256(commit_json.encode()).hexdigest()
    
    def _content_contains_query(self, content: Dict[str, Any], query: str) -> bool:
        """Check if content contains query string"""
        content_str = json.dumps(content).lower()
        return query in content_str
