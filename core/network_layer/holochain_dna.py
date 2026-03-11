"""
Holochain DNA Layer
Core Holochain integration for distributed application logic
"""

import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import time


class EntryType(Enum):
    """Holochain entry types"""
    AGENT = "agent"
    COMMIT = "commit"
    DELTA = "delta"
    VALIDATION_RULE = "validation_rule"
    CAPABILITY = "capability"
    APP_STATE = "app_state"


@dataclass
class HolochainEntry:
    """Base Holochain entry structure"""
    entry_hash: str
    entry_type: EntryType
    data: Dict[str, Any]
    author: str
    timestamp: float
    signature: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "entry_hash": self.entry_hash,
            "entry_type": self.entry_type.value,
            "data": self.data,
            "author": self.author,
            "timestamp": self.timestamp,
            "signature": self.signature
        }


@dataclass
class ValidationRule:
    """Validation rule for entries"""
    rule_id: str
    entry_type: EntryType
    validation_fn: str  # Function name or WASM reference
    parameters: Dict[str, Any]
    author: str
    timestamp: float


class HolochainDNA:
    """Core Holochain DNA implementation for collaborative platform"""
    
    def __init__(self, zome_name: str, agent_pubkey: str):
        self.zome_name = zome_name
        self.agent_pubkey = agent_pubkey
        self.local_source_chain: List[HolochainEntry] = []
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.capabilities: Dict[str, Dict] = {}
        self.dht_cache: Dict[str, HolochainEntry] = {}
        
    def create_entry(self, entry_type: EntryType, data: Dict[str, Any], 
                    signature: str = "") -> HolochainEntry:
        """Create a new Holochain entry"""
        entry_data = {
            "entry_type": entry_type.value,
            "data": data,
            "author": self.agent_pubkey,
            "timestamp": time.time()
        }
        
        entry_hash = self._hash_entry(entry_data)
        
        entry = HolochainEntry(
            entry_hash=entry_hash,
            entry_type=entry_type,
            data=data,
            author=self.agent_pubkey,
            timestamp=entry_data["timestamp"],
            signature=signature
        )
        
        # Validate entry before adding to source chain
        if self.validate_entry(entry):
            self.local_source_chain.append(entry)
            return entry
        else:
            raise ValueError(f"Entry validation failed for type {entry_type.value}")
    
    def _hash_entry(self, entry_data: Dict[str, Any]) -> str:
        """Generate hash for entry"""
        entry_json = json.dumps(entry_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(entry_json.encode()).hexdigest()
    
    def validate_entry(self, entry: HolochainEntry) -> bool:
        """Validate entry against registered rules"""
        rules = [rule for rule in self.validation_rules.values() 
                if rule.entry_type == entry.entry_type]
        
        for rule in rules:
            if not self._apply_validation_rule(rule, entry):
                return False
        
        return True
    
    def _apply_validation_rule(self, rule: ValidationRule, entry: HolochainEntry) -> bool:
        """Apply a specific validation rule"""
        # Simplified validation logic
        # In a real implementation, this would call WASM validation functions
        
        if rule.rule_id == "basic_commit_validation":
            return self._validate_commit_entry(entry)
        elif rule.rule_id == "basic_delta_validation":
            return self._validate_delta_entry(entry)
        elif rule.rule_id == "agent_capability_check":
            return self._validate_agent_capability(entry)
        
        return True
    
    def _validate_commit_entry(self, entry: HolochainEntry) -> bool:
        """Validate commit entry"""
        data = entry.data
        
        # Check required fields
        required_fields = ["commit_id", "author", "timestamp", "deltas"]
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate deltas
        deltas = data.get("deltas", [])
        if not isinstance(deltas, list):
            return False
        
        return True
    
    def _validate_delta_entry(self, entry: HolochainEntry) -> bool:
        """Validate delta entry"""
        data = entry.data
        
        # Check required fields
        required_fields = ["op", "path"]
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate operation type
        valid_ops = ["insert", "delete", "update", "move", "copy", "replace"]
        if data["op"] not in valid_ops:
            return False
        
        return True
    
    def _validate_agent_capability(self, entry: HolochainEntry) -> bool:
        """Validate agent has required capabilities"""
        # Check if author has required capabilities
        return entry.author in self.capabilities
    
    def register_validation_rule(self, rule: ValidationRule):
        """Register a validation rule"""
        self.validation_rules[rule.rule_id] = rule
    
    def grant_capability(self, agent_pubkey: str, capabilities: Dict[str, Any]):
        """Grant capabilities to an agent"""
        self.capabilities[agent_pubkey] = capabilities
    
    def revoke_capability(self, agent_pubkey: str):
        """Revoke capabilities from an agent"""
        if agent_pubkey in self.capabilities:
            del self.capabilities[agent_pubkey]
    
    def get_entry(self, entry_hash: str) -> Optional[HolochainEntry]:
        """Get entry by hash"""
        # Check local source chain first
        for entry in self.local_source_chain:
            if entry.entry_hash == entry_hash:
                return entry
        
        # Check DHT cache
        if entry_hash in self.dht_cache:
            return self.dht_cache[entry_hash]
        
        return None
    
    def query_entries(self, entry_type: Optional[EntryType] = None,
                     author: Optional[str] = None,
                     limit: Optional[int] = None) -> List[HolochainEntry]:
        """Query entries from local source chain"""
        entries = self.local_source_chain
        
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        
        if author:
            entries = [e for e in entries if e.author == author]
        
        if limit:
            entries = entries[:limit]
        
        return entries
    
    def publish_to_dht(self, entry: HolochainEntry):
        """Publish entry to DHT"""
        # In a real implementation, this would use Holochain's DHT API
        self.dht_cache[entry.entry_hash] = entry
    
    def fetch_from_dht(self, entry_hash: str) -> Optional[HolochainEntry]:
        """Fetch entry from DHT"""
        # In a real implementation, this would query Holochain's DHT
        return self.dht_cache.get(entry_hash)
    
    def get_source_chain_tip(self) -> Optional[HolochainEntry]:
        """Get the latest entry in source chain"""
        if not self.local_source_chain:
            return None
        return self.local_source_chain[-1]
    
    def get_chain_state(self) -> Dict[str, Any]:
        """Get current chain state"""
        return {
            "zome_name": self.zome_name,
            "agent_pubkey": self.agent_pubkey,
            "chain_length": len(self.local_source_chain),
            "validation_rules": len(self.validation_rules),
            "capabilities": len(self.capabilities),
            "dht_cache_size": len(self.dht_cache)
        }


class SignLanguageDNA(HolochainDNA):
    """Specialized DNA for sign language collaboration"""
    
    def __init__(self, agent_pubkey: str):
        super().__init__("sign_language", agent_pubkey)
        self._setup_sign_language_validation()
    
    def _setup_sign_language_validation(self):
        """Setup validation rules specific to sign language"""
        # Sign video validation
        sign_video_rule = ValidationRule(
            rule_id="sign_video_validation",
            entry_type=EntryType.APP_STATE,
            validation_fn="validate_sign_video",
            parameters={
                "max_video_size": 100 * 1024 * 1024,  # 100MB
                "supported_formats": ["mp4", "webm", "mov"],
                "required_metadata": ["signer_id", "language", "duration"]
            },
            author=self.agent_pubkey,
            timestamp=time.time()
        )
        
        # Translation validation
        translation_rule = ValidationRule(
            rule_id="translation_validation",
            entry_type=EntryType.APP_STATE,
            validation_fn="validate_translation",
            parameters={
                "max_text_length": 10000,
                "supported_languages": ["en", "es", "fr", "de", "asl", "bsl"],
                "required_fields": ["source_text", "target_text", "source_lang", "target_lang"]
            },
            author=self.agent_pubkey,
            timestamp=time.time()
        )
        
        self.register_validation_rule(sign_video_rule)
        self.register_validation_rule(translation_rule)
    
    def create_sign_video_entry(self, video_data: Dict[str, Any]) -> HolochainEntry:
        """Create a sign language video entry"""
        return self.create_entry(EntryType.APP_STATE, {
            "type": "sign_video",
            "video_data": video_data
        })
    
    def create_translation_entry(self, translation_data: Dict[str, Any]) -> HolochainEntry:
        """Create a translation entry"""
        return self.create_entry(EntryType.APP_STATE, {
            "type": "translation",
            "translation_data": translation_data
        })
    
    def create_annotation_entry(self, annotation_data: Dict[str, Any]) -> HolochainEntry:
        """Create an annotation entry"""
        return self.create_entry(EntryType.APP_STATE, {
            "type": "annotation",
            "annotation_data": annotation_data
        })


class DocumentDNA(HolochainDNA):
    """Specialized DNA for document collaboration"""
    
    def __init__(self, agent_pubkey: str):
        super().__init__("documents", agent_pubkey)
        self._setup_document_validation()
    
    def _setup_document_validation(self):
        """Setup validation rules for documents"""
        document_rule = ValidationRule(
            rule_id="document_validation",
            entry_type=EntryType.APP_STATE,
            validation_fn="validate_document",
            parameters={
                "max_document_size": 10 * 1024 * 1024,  # 10MB
                "supported_formats": ["md", "txt", "json"],
                "required_metadata": ["title", "author"]
            },
            author=self.agent_pubkey,
            timestamp=time.time()
        )
        
        self.register_validation_rule(document_rule)
    
    def create_document_entry(self, document_data: Dict[str, Any]) -> HolochainEntry:
        """Create a document entry"""
        return self.create_entry(EntryType.APP_STATE, {
            "type": "document",
            "document_data": document_data
        })
    
    def create_comment_entry(self, comment_data: Dict[str, Any]) -> HolochainEntry:
        """Create a comment entry"""
        return self.create_entry(EntryType.APP_STATE, {
            "type": "comment",
            "comment_data": comment_data
        })
