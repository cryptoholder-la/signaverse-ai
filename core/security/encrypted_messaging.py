"""
Encrypted Messaging Layer
Secure messaging with end-to-end encryption and authentication
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64

logger = logging.getLogger(__name__)


class EncryptionType(Enum):
    """Types of encryption"""
    AES256_GCM = "aes256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    AES256_CBC = "aes256_cbc"
    RSA_OAEP = "rsa_oaep"


class MessageType(Enum):
    """Types of encrypted messages"""
    DIRECT_MESSAGE = "direct_message"
    BROADCAST_MESSAGE = "broadcast_message"
    GROUP_MESSAGE = "group_message"
    FILE_TRANSFER = "file_transfer"
    VOICE_CALL = "voice_call"
    VIDEO_CALL = "video_call"


class SecurityLevel(Enum):
    """Security levels for messaging"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class EncryptionKey:
    """Encryption key information"""
    def __init__(self, key_id: str, key_data: bytes, key_type: EncryptionType,
                 created_at: float, expires_at: Optional[float] = None,
                 algorithm: str = "AES-256"):
        self.key_id = key_id
        self.key_data = key_data
        self.key_type = key_type
        self.created_at = created_at
        self.expires_at = expires_at
        self.algorithm = algorithm
        self.usage_count = 0
        self.last_used = None
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def mark_used(self):
        """Mark key as used"""
        self.usage_count += 1
        self.last_used = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without sensitive data)"""
        return {
            "key_id": self.key_id,
            "key_type": self.key_type.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "algorithm": self.algorithm,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "is_expired": self.is_expired()
        }


@dataclass
class EncryptedMessage:
    """Encrypted message with metadata"""
    def __init__(self, message_id: str, sender: str, recipient: str,
                 message_type: MessageType, encrypted_data: bytes,
                 nonce: bytes, tag: bytes, key_id: str,
                 timestamp: float, metadata: Dict[str, Any] = None):
        self.message_id = message_id
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.encrypted_data = encrypted_data
        self.nonce = nonce
        self.tag = tag
        self.key_id = key_id
        self.timestamp = timestamp
        self.metadata = metadata or {}
        self.security_level = SecurityLevel.MEDIUM
        self.ttl = 3600  # 1 hour
        self.hop_count = 0
        self.signature: Optional[bytes] = None
    
    def add_hop(self):
        """Add a hop to the message"""
        self.hop_count += 1
        self.ttl = max(0, self.ttl - 60)  # Subtract 1 minute per hop
    
    def is_expired(self) -> bool:
        """Check if message is expired"""
        return time.time() > (self.timestamp + self.ttl)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without encrypted data)"""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "key_id": self.key_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "security_level": self.security_level.value,
            "ttl": self.ttl,
            "hop_count": self.hop_count,
            "is_expired": self.is_expired(),
            "encrypted": True
        }


class KeyManager:
    """Manages encryption keys"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.keys: Dict[str, EncryptionKey] = {}
        self.key_rotation_interval = 86400  # 24 hours
        self.max_key_age = 604800  # 7 days
        self.key_derivation_salt = os.urandom(32)
        
        # Performance metrics
        self.metrics = {
            "keys_generated": 0,
            "keys_rotated": 0,
            "encryptions_performed": 0,
            "decryptions_performed": 0,
            "key_expirations": 0
        }
    
    def generate_key(self, key_type: EncryptionType = EncryptionType.AES256_GCM,
                 expires_in: Optional[float] = None) -> str:
        """Generate new encryption key"""
        try:
            if key_type == EncryptionType.AES256_GCM:
                key_data = Fernet.generate_key()
            elif key_type == EncryptionType.CHACHA20_POLY1305:
                # Generate 32-byte key for ChaCha20
                key_data = os.urandom(32)
            else:
                # Default to Fernet (AES-256-CBC)
                key_data = Fernet.generate_key()
                key_type = EncryptionType.AES256_CBC
            
            key_id = hashlib.sha256(f"{self.node_id}_{time.time()}".encode()).hexdigest()[:16]
            
            expires_at = None
            if expires_in:
                expires_at = time.time() + expires_in
            else:
                expires_at = time.time() + self.max_key_age
            
            key = EncryptionKey(
                key_id=key_id,
                key_data=key_data,
                key_type=key_type,
                created_at=time.time(),
                expires_at=expires_at
            )
            
            self.keys[key_id] = key
            self.metrics["keys_generated"] += 1
            
            logger.info(f"Generated encryption key {key_id} ({key_type.value})")
            return key_id
            
        except Exception as e:
            logger.error(f"Failed to generate encryption key: {e}")
            raise
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get encryption key by ID"""
        return self.keys.get(key_id)
    
    def rotate_key(self, key_id: str, new_key_type: EncryptionType = None) -> Optional[str]:
        """Rotate an existing key"""
        if key_id not in self.keys:
            return None
        
        old_key = self.keys[key_id]
        
        # Generate new key
        new_key_id = self.generate_key(new_key_type or old_key.key_type)
        
        # Mark old key as expired
        old_key.expires_at = time.time()
        
        self.metrics["keys_rotated"] += 1
        logger.info(f"Rotated key {key_id} -> {new_key_id}")
        
        return new_key_id
    
    def cleanup_expired_keys(self):
        """Remove expired keys"""
        current_time = time.time()
        expired_keys = []
        
        for key_id, key in self.keys.items():
            if key.is_expired():
                expired_keys.append(key_id)
                self.metrics["key_expirations"] += 1
        
        for key_id in expired_keys:
            del self.keys[key_id]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired keys")
    
    def get_key_stats(self) -> Dict[str, Any]:
        """Get key management statistics"""
        active_keys = len([k for k in self.keys.values() if not k.is_expired()])
        expired_keys = len([k for k in self.keys.values() if k.is_expired()])
        
        return {
            "total_keys": len(self.keys),
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "keys_by_type": {
                key_type.value: len([k for k in self.keys.values() if k.key_type == key_type])
                for key_type in EncryptionType
            },
            "metrics": self.metrics
        }


class EncryptedMessenger:
    """Secure messaging with encryption and authentication"""
    
    def __init__(self, node_id: str, key_manager: KeyManager = None):
        self.node_id = node_id
        self.key_manager = key_manager or KeyManager(node_id)
        
        # Encryption backends
        self.encryptors = {
            EncryptionType.AES256_GCM: self._create_aes_gcm_encryptor,
            EncryptionType.CHACHA20_POLY1305: self._create_chacha20_encryptor,
            EncryptionType.AES256_CBC: self._create_aes_cbc_encryptor
        }
        
        self.decryptors = {
            EncryptionType.AES256_GCM: self._create_aes_gcm_decryptor,
            EncryptionType.CHACHA20_POLY1305: self._create_chacha20_decryptor,
            EncryptionType.AES256_CBC: self._create_aes_cbc_decryptor
        }
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        
        # Performance metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "encryptions_performed": 0,
            "decryptions_performed": 0,
            "encryption_failures": 0,
            "decryption_failures": 0,
            "bytes_transferred": 0
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
    
    def _create_aes_gcm_encryptor(self, key_data: bytes) -> Fernet:
        """Create AES-GCM encryptor"""
        # Fernet uses AES-256-CBC, for GCM we'd need custom implementation
        # For now, use Fernet as fallback
        return Fernet(key_data)
    
    def _create_chacha20_encryptor(self, key_data: bytes):
        """Create ChaCha20-Poly1305 encryptor"""
        # Custom implementation would go here
        # For now, return None (not implemented)
        return None
    
    def _create_aes_cbc_encryptor(self, key_data: bytes) -> Fernet:
        """Create AES-CBC encryptor"""
        return Fernet(key_data)
    
    def _create_aes_gcm_decryptor(self, key_data: bytes) -> Fernet:
        """Create AES-GCM decryptor"""
        return Fernet(key_data)
    
    def _create_chacha20_decryptor(self, key_data: bytes):
        """Create ChaCha20-Poly1305 decryptor"""
        # Custom implementation would go here
        # For now, return None (not implemented)
        return None
    
    def _create_aes_cbc_decryptor(self, key_data: bytes) -> Fernet:
        """Create AES-CBC decryptor"""
        return Fernet(key_data)
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register handler for message type"""
        self.message_handlers[message_type.value] = handler
        logger.info(f"Registered handler for {message_type.value}")
    
    async def start(self):
        """Start encrypted messaging service"""
        try:
            self.is_running = True
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._key_rotation_loop()),
                asyncio.create_task(self._key_cleanup_loop()),
                asyncio.create_task(self._message_processing_loop())
            ]
            
            logger.info(f"Encrypted messaging service started for node {self.node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start encrypted messaging: {e}")
            return False
    
    async def stop(self):
        """Stop encrypted messaging service"""
        self.is_running = False
        
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Encrypted messaging service stopped")
    
    async def _key_rotation_loop(self):
        """Background loop for key rotation"""
        while self.is_running:
            try:
                await asyncio.sleep(self.key_manager.key_rotation_interval)
                
                # Rotate keys that are approaching expiration
                current_time = time.time()
                rotation_threshold = 86400  # 24 hours before expiration
                
                for key_id, key in list(self.key_manager.keys.items()):
                    if (key.expires_at and 
                        key.expires_at - current_time < rotation_threshold and
                        not key.is_expired()):
                        
                        new_key_id = self.key_manager.rotate_key(key_id)
                        if new_key_id:
                            logger.info(f"Rotated key {key_id} -> {new_key_id}")
                
            except Exception as e:
                logger.error(f"Key rotation error: {e}")
                await asyncio.sleep(60)
    
    async def _key_cleanup_loop(self):
        """Background loop for key cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                self.key_manager.cleanup_expired_keys()
                
            except Exception as e:
                logger.error(f"Key cleanup error: {e}")
                await asyncio.sleep(300)
    
    async def _message_processing_loop(self):
        """Background loop for message processing"""
        while self.is_running:
            try:
                await asyncio.sleep(1)  # Process messages as they arrive
                
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await asyncio.sleep(10)
    
    async def send_message(self, recipient: str, message_type: MessageType,
                        payload: Dict[str, Any], security_level: SecurityLevel = SecurityLevel.MEDIUM,
                        key_id: Optional[str] = None, ttl: int = 3600) -> bool:
        """Send encrypted message"""
        try:
            # Get or generate key
            if key_id is None:
                key_id = self.key_manager.generate_key()
            
            key = self.key_manager.get_key(key_id)
            if not key:
                logger.error(f"Key {key_id} not found")
                return False
            
            # Check key type and get encryptor
            encryptor = self.encryptors.get(key.key_type)
            if not encryptor:
                logger.error(f"No encryptor for key type {key.key_type}")
                return False
            
            # Mark key as used
            key.mark_used()
            
            # Create message
            message_id = hashlib.sha256(f"{self.node_id}_{recipient}_{time.time()}".encode()).hexdigest()[:16]
            timestamp = time.time()
            
            # Serialize payload
            payload_json = json.dumps(payload, separators=(',', ':'))
            payload_bytes = payload_json.encode('utf-8')
            
            # Encrypt message
            encrypted_data = encryptor.encrypt(payload_bytes)
            
            # Extract nonce and tag (for Fernet)
            if hasattr(encryptor, 'encrypt'):
                # Fernet includes nonce in the encrypted data
                nonce = b''  # Fernet handles nonce internally
                tag = b''   # Fernet includes tag in the encrypted data
            else:
                # Generate random nonce and tag for other encryption types
                nonce = os.urandom(12)
                tag = b''  # Would be computed by encryption algorithm
            
            # Create encrypted message
            encrypted_message = EncryptedMessage(
                message_id=message_id,
                sender=self.node_id,
                recipient=recipient,
                message_type=message_type,
                encrypted_data=encrypted_data,
                nonce=nonce,
                tag=tag,
                key_id=key_id,
                timestamp=timestamp,
                metadata={
                    "security_level": security_level.value,
                    "ttl": ttl,
                    "encryption_type": key.key_type.value
                }
            )
            
            # Send message (in real implementation, would send over network)
            await self._send_encrypted_message(encrypted_message)
            
            # Update metrics
            self.metrics["messages_sent"] += 1
            self.metrics["encryptions_performed"] += 1
            self.metrics["bytes_transferred"] += len(encrypted_data)
            
            logger.info(f"Sent encrypted message {message_id} to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send encrypted message: {e}")
            self.metrics["encryption_failures"] += 1
            return False
    
    async def _send_encrypted_message(self, message: EncryptedMessage):
        """Send encrypted message over network"""
        # In real implementation, would send over P2P network
        # For now, just log the message
        logger.debug(f"Sending encrypted message: {message.message_id}")
        
        # Simulate network send
        await asyncio.sleep(0.1)
    
    async def receive_message(self, encrypted_message_data: Dict[str, Any]) -> bool:
        """Receive and decrypt encrypted message"""
        try:
            # Create encrypted message object
            message = EncryptedMessage(
                message_id=encrypted_message_data.get("message_id", ""),
                sender=encrypted_message_data.get("sender", ""),
                recipient=encrypted_message_data.get("recipient", ""),
                message_type=MessageType(encrypted_message_data.get("message_type", "direct_message")),
                encrypted_data=encrypted_message_data.get("encrypted_data", b""),
                nonce=encrypted_message_data.get("nonce", b""),
                tag=encrypted_message_data.get("tag", b""),
                key_id=encrypted_message_data.get("key_id", ""),
                timestamp=encrypted_message_data.get("timestamp", time.time()),
                metadata=encrypted_message_data.get("metadata", {})
            )
            
            # Check if message is expired
            if message.is_expired():
                logger.warning(f"Received expired message {message.message_id}")
                return False
            
            # Add hop
            message.add_hop()
            
            # Get key
            key = self.key_manager.get_key(message.key_id)
            if not key:
                logger.error(f"Decryption key {message.key_id} not found")
                return False
            
            # Check key type and get decryptor
            decryptor = self.decryptors.get(key.key_type)
            if not decryptor:
                logger.error(f"No decryptor for key type {key.key_type}")
                return False
            
            # Decrypt message
            try:
                decrypted_data = decryptor.decrypt(message.encrypted_data)
                
                # Parse payload
                payload = json.loads(decrypted_data.decode('utf-8'))
                
                # Call message handler
                handler = self.message_handlers.get(message.message_type.value)
                if handler:
                    await handler(message.sender, payload, message.metadata)
                
                # Update metrics
                self.metrics["messages_received"] += 1
                self.metrics["decryptions_performed"] += 1
                
                logger.info(f"Received and decrypted message {message.message_id} from {message.sender}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to decrypt message {message.message_id}: {e}")
                self.metrics["decryption_failures"] += 1
                return False
            
        except Exception as e:
            logger.error(f"Failed to receive encrypted message: {e}")
            return False
    
    async def broadcast_message(self, message_type: MessageType, payload: Dict[str, Any],
                           security_level: SecurityLevel = SecurityLevel.MEDIUM,
                           key_id: Optional[str] = None, ttl: int = 3600) -> int:
        """Broadcast encrypted message to all known nodes"""
        try:
            # Get or generate key
            if key_id is None:
                key_id = self.key_manager.generate_key()
            
            key = self.key_manager.get_key(key_id)
            if not key:
                logger.error(f"Key {key_id} not found")
                return 0
            
            # Mark key as used
            key.mark_used()
            
            # Create broadcast message
            message_id = hashlib.sha256(f"{self.node_id}_broadcast_{time.time()}".encode()).hexdigest()[:16]
            timestamp = time.time()
            
            # Serialize payload
            payload_json = json.dumps(payload, separators=(',', ':'))
            payload_bytes = payload_json.encode('utf-8')
            
            # Encrypt message
            encryptor = self.encryptors.get(key.key_type)
            if not encryptor:
                logger.error(f"No encryptor for key type {key.key_type}")
                return 0
            
            encrypted_data = encryptor.encrypt(payload_bytes)
            
            # Create encrypted message
            encrypted_message = EncryptedMessage(
                message_id=message_id,
                sender=self.node_id,
                recipient="broadcast",
                message_type=message_type,
                encrypted_data=encrypted_data,
                nonce=b'',  # Fernet handles nonce
                tag=b'',   # Fernet handles tag
                key_id=key_id,
                timestamp=timestamp,
                metadata={
                    "security_level": security_level.value,
                    "ttl": ttl,
                    "encryption_type": key.key_type.value,
                    "broadcast": True
                }
            )
            
            # Broadcast message (in real implementation, would send to all peers)
            sent_count = await self._broadcast_encrypted_message(encrypted_message)
            
            # Update metrics
            self.metrics["messages_sent"] += sent_count
            self.metrics["encryptions_performed"] += sent_count
            self.metrics["bytes_transferred"] += len(encrypted_data) * sent_count
            
            logger.info(f"Broadcast encrypted message {message_id} to {sent_count} recipients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast encrypted message: {e}")
            self.metrics["encryption_failures"] += 1
            return 0
    
    async def _broadcast_encrypted_message(self, message: EncryptedMessage) -> int:
        """Broadcast encrypted message to network"""
        # In real implementation, would send to all connected peers
        # For now, simulate broadcasting to 5 peers
        peer_count = 5
        
        for i in range(peer_count):
            # Simulate sending to each peer
            await asyncio.sleep(0.05)
        
        return peer_count
    
    async def send_file(self, recipient: str, file_path: str, 
                    security_level: SecurityLevel = SecurityLevel.HIGH,
                    key_id: Optional[str] = None) -> bool:
        """Send encrypted file"""
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Get or generate key
            if key_id is None:
                key_id = self.key_manager.generate_key()
            
            key = self.key_manager.get_key(key_id)
            if not key:
                logger.error(f"Key {key_id} not found")
                return False
            
            # Mark key as used
            key.mark_used()
            
            # Create file message
            message_id = hashlib.sha256(f"{self.node_id}_{recipient}_{file_path}_{time.time()}".encode()).hexdigest()[:16]
            timestamp = time.time()
            
            # Create file payload
            payload = {
                "file_name": os.path.basename(file_path),
                "file_size": len(file_data),
                "file_hash": hashlib.sha256(file_data).hexdigest(),
                "file_data": base64.b64encode(file_data).decode('utf-8')
            }
            
            # Encrypt file data
            encryptor = self.encryptors.get(key.key_type)
            if not encryptor:
                logger.error(f"No encryptor for key type {key.key_type}")
                return False
            
            encrypted_data = encryptor.encrypt(json.dumps(payload).encode('utf-8'))
            
            # Create encrypted message
            encrypted_message = EncryptedMessage(
                message_id=message_id,
                sender=self.node_id,
                recipient=recipient,
                message_type=MessageType.FILE_TRANSFER,
                encrypted_data=encrypted_data,
                nonce=b'',  # Fernet handles nonce
                tag=b'',   # Fernet handles tag
                key_id=key_id,
                timestamp=timestamp,
                metadata={
                    "security_level": security_level.value,
                    "encryption_type": key.key_type.value,
                    "file_transfer": True
                }
            )
            
            # Send file message
            await self._send_encrypted_message(encrypted_message)
            
            # Update metrics
            self.metrics["messages_sent"] += 1
            self.metrics["encryptions_performed"] += 1
            self.metrics["bytes_transferred"] += len(file_data)
            
            logger.info(f"Sent encrypted file {message_id} ({len(file_data)} bytes) to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send encrypted file: {e}")
            self.metrics["encryption_failures"] += 1
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get messaging metrics"""
        return {
            **self.metrics,
            "key_stats": self.key_manager.get_key_stats(),
            "supported_encryption_types": [et.value for et in EncryptionType],
            "node_id": self.node_id,
            "is_running": self.is_running
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get messenger status"""
        return {
            "is_running": self.is_running,
            "metrics": self.metrics,
            "key_manager_status": self.key_manager.get_key_stats(),
            "active_handlers": list(self.message_handlers.keys()),
            "supported_encryption": list(self.encryptors.keys())
        }
