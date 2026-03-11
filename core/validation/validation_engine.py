"""
Validation Engine
Centralized validation for commits, deltas, and agent capabilities
"""

import json
import time
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    REQUIRES_CAPABILITY = "requires_capability"


@dataclass
class ValidationResult:
    """Result of validation operation"""
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ValidationRule:
    """Base validation rule class"""
    
    def __init__(self, rule_id: str, name: str, description: str):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.enabled = True
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Validate data against this rule"""
        raise NotImplementedError


class CommitValidationRule(ValidationRule):
    """Validation rule for commits"""
    
    def __init__(self):
        super().__init__("commit_validation", "Commit Validation", "Validates commit structure and content")
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Validate commit data"""
        required_fields = ["commit_id", "author", "timestamp", "deltas", "signature"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return ValidationResult(
                    ValidationStatus.INVALID,
                    f"Missing required field: {field}",
                    {"missing_field": field}
                )
        
        # Validate commit ID format
        commit_id = data["commit_id"]
        if not isinstance(commit_id, str) or len(commit_id) != 64:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Invalid commit ID format",
                {"commit_id": commit_id}
            )
        
        # Validate timestamp
        timestamp = data["timestamp"]
        if not isinstance(timestamp, (int, float)) or timestamp <= 0:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Invalid timestamp",
                {"timestamp": timestamp}
            )
        
        # Validate deltas
        deltas = data["deltas"]
        if not isinstance(deltas, list):
            return ValidationResult(
                ValidationStatus.INVALID,
                "Deltas must be a list",
                {"deltas_type": type(deltas).__name__}
            )
        
        if len(deltas) == 0:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Commit must contain at least one delta",
                {"deltas_count": 0}
            )
        
        # Validate each delta
        for i, delta in enumerate(deltas):
            delta_result = self._validate_delta(delta)
            if delta_result.status != ValidationStatus.VALID:
                return ValidationResult(
                    ValidationStatus.INVALID,
                    f"Invalid delta at index {i}: {delta_result.message}",
                    {"delta_index": i, "delta_error": delta_result.details}
                )
        
        return ValidationResult(ValidationStatus.VALID, "Commit validation passed")
    
    def _validate_delta(self, delta: Dict[str, Any]) -> ValidationResult:
        """Validate individual delta"""
        required_fields = ["op", "path"]
        
        for field in required_fields:
            if field not in delta:
                return ValidationResult(
                    ValidationStatus.INVALID,
                    f"Missing required delta field: {field}",
                    {"missing_field": field}
                )
        
        # Validate operation
        valid_ops = ["insert", "delete", "update", "move", "copy", "replace"]
        if delta["op"] not in valid_ops:
            return ValidationResult(
                ValidationStatus.INVALID,
                f"Invalid operation: {delta['op']}",
                {"operation": delta["op"], "valid_operations": valid_ops}
            )
        
        # Validate path
        path = delta["path"]
        if not isinstance(path, str) or not path.startswith("/"):
            return ValidationResult(
                ValidationStatus.INVALID,
                "Invalid path format",
                {"path": path}
            )
        
        # Operation-specific validation
        op = delta["op"]
        if op in ["insert", "update", "replace"] and "value" not in delta:
            return ValidationResult(
                ValidationStatus.INVALID,
                f"Operation {op} requires value field",
                {"operation": op}
            )
        
        if op in ["move", "copy"] and "from" not in delta:
            return ValidationResult(
                ValidationStatus.INVALID,
                f"Operation {op} requires from field",
                {"operation": op}
            )
        
        return ValidationResult(ValidationStatus.VALID, "Delta validation passed")


class SignatureValidationRule(ValidationRule):
    """Validation rule for cryptographic signatures"""
    
    def __init__(self):
        super().__init__("signature_validation", "Signature Validation", "Validates cryptographic signatures")
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Validate signature"""
        if "signature" not in data or "author" not in data:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Missing signature or author field",
                {"missing_fields": ["signature", "author"]}
            )
        
        # In a real implementation, this would verify the cryptographic signature
        # For now, we'll do basic format validation
        signature = data["signature"]
        author = data["author"]
        
        if not isinstance(signature, str) or len(signature) < 10:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Invalid signature format",
                {"signature_length": len(signature)}
            )
        
        if not isinstance(author, str) or len(author) < 10:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Invalid author format",
                {"author_length": len(author)}
            )
        
        return ValidationResult(ValidationStatus.VALID, "Signature validation passed")


class CapabilityValidationRule(ValidationRule):
    """Validation rule for agent capabilities"""
    
    def __init__(self):
        super().__init__("capability_validation", "Capability Validation", "Validates agent capabilities")
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Validate agent capabilities"""
        if "author" not in data:
            return ValidationResult(
                ValidationStatus.INVALID,
                "Missing author field",
                {"missing_field": "author"}
            )
        
        author = data["author"]
        capabilities = context.get("capabilities", {})
        
        if author not in capabilities:
            return ValidationResult(
                ValidationStatus.REQUIRES_CAPABILITY,
                f"Agent {author} has no registered capabilities",
                {"author": author}
            )
        
        agent_caps = capabilities[author]
        
        # Check if agent has required capabilities for the operation
        required_capability = self._get_required_capability(data)
        if required_capability and required_capability not in agent_caps:
            return ValidationResult(
                ValidationStatus.REQUIRES_CAPABILITY,
                f"Agent {author} lacks required capability: {required_capability}",
                {"author": author, "required_capability": required_capability}
            )
        
        return ValidationResult(ValidationStatus.VALID, "Capability validation passed")
    
    def _get_required_capability(self, data: Dict[str, Any]) -> Optional[str]:
        """Get required capability for the data type"""
        if "deltas" in data:
            return "create_commit"
        elif data.get("type") == "sign_video":
            return "upload_video"
        elif data.get("type") == "translation":
            return "create_translation"
        
        return None


class ValidationEngine:
    """Central validation engine"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self.capabilities: Dict[str, Set[str]] = {}
        self.validation_cache: Dict[str, ValidationResult] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Register default rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default validation rules"""
        self.register_rule(CommitValidationRule())
        self.register_rule(SignatureValidationRule())
        self.register_rule(CapabilityValidationRule())
    
    def register_rule(self, rule: ValidationRule):
        """Register a validation rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Registered validation rule: {rule.rule_id}")
    
    def unregister_rule(self, rule_id: str):
        """Unregister a validation rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Unregistered validation rule: {rule_id}")
    
    def grant_capability(self, agent_pubkey: str, capability: str):
        """Grant a capability to an agent"""
        if agent_pubkey not in self.capabilities:
            self.capabilities[agent_pubkey] = set()
        self.capabilities[agent_pubkey].add(capability)
        logger.info(f"Granted capability {capability} to agent {agent_pubkey}")
    
    def revoke_capability(self, agent_pubkey: str, capability: str):
        """Revoke a capability from an agent"""
        if agent_pubkey in self.capabilities:
            self.capabilities[agent_pubkey].discard(capability)
            logger.info(f"Revoked capability {capability} from agent {agent_pubkey}")
    
    def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate data against all registered rules"""
        if context is None:
            context = {}
        
        # Add capabilities to context
        context["capabilities"] = self.capabilities
        
        # Check cache first
        data_hash = self._hash_data(data)
        cache_key = f"{data_hash}_{hash(str(sorted(context.items())))}"
        
        if cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            if time.time() - cached_result.details.get("cached_at", 0) < self.cache_ttl:
                return cached_result
        
        # Run validation rules
        results = []
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            try:
                result = rule.validate(data, context)
                results.append(result)
                
                # Early exit on invalid result
                if result.status == ValidationStatus.INVALID:
                    break
            except Exception as e:
                logger.error(f"Validation rule {rule.rule_id} failed: {e}")
                results.append(ValidationResult(
                    ValidationStatus.INVALID,
                    f"Validation rule {rule.rule_id} failed: {str(e)}",
                    {"rule_id": rule.rule_id, "error": str(e)}
                ))
                break
        
        # Combine results
        final_result = self._combine_results(results)
        
        # Cache result
        final_result.details["cached_at"] = time.time()
        self.validation_cache[cache_key] = final_result
        
        return final_result
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Generate hash for data caching"""
        data_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_json.encode()).hexdigest()
    
    def _combine_results(self, results: List[ValidationResult]) -> ValidationResult:
        """Combine multiple validation results"""
        if not results:
            return ValidationResult(ValidationStatus.VALID, "No validation rules applied")
        
        # Check for invalid results
        for result in results:
            if result.status == ValidationStatus.INVALID:
                return result
        
        # Check for capability requirements
        for result in results:
            if result.status == ValidationStatus.REQUIRES_CAPABILITY:
                return result
        
        # All valid
        return ValidationResult(ValidationStatus.VALID, "All validation rules passed")
    
    def validate_commit(self, commit_data: Dict[str, Any]) -> ValidationResult:
        """Validate a specific commit"""
        return self.validate(commit_data)
    
    def validate_delta(self, delta_data: Dict[str, Any]) -> ValidationResult:
        """Validate a specific delta"""
        return self.validate(delta_data)
    
    def validate_agent_capability(self, agent_pubkey: str, required_capability: str) -> ValidationResult:
        """Validate if agent has required capability"""
        if agent_pubkey not in self.capabilities:
            return ValidationResult(
                ValidationStatus.REQUIRES_CAPABILITY,
                f"Agent {agent_pubkey} has no capabilities",
                {"agent": agent_pubkey}
            )
        
        if required_capability not in self.capabilities[agent_pubkey]:
            return ValidationResult(
                ValidationStatus.REQUIRES_CAPABILITY,
                f"Agent {agent_pubkey} lacks capability {required_capability}",
                {"agent": agent_pubkey, "required_capability": required_capability}
            )
        
        return ValidationResult(ValidationStatus.VALID, "Agent has required capability")
    
    def get_agent_capabilities(self, agent_pubkey: str) -> Set[str]:
        """Get capabilities for an agent"""
        return self.capabilities.get(agent_pubkey, set())
    
    def clear_cache(self):
        """Clear validation cache"""
        self.validation_cache.clear()
        logger.info("Validation cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation engine statistics"""
        return {
            "rules_count": len(self.rules),
            "agents_count": len(self.capabilities),
            "cache_size": len(self.validation_cache),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled)
        }
