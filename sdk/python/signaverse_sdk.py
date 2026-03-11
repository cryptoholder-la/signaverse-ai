"""
Signaverse Python SDK
Developer SDK for building distributed collaborative applications
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
import logging

# Import core components
from core.commit_engine.commit import CommitEngine, Delta
from core.delta_protocol.delta_ops import DeltaProtocol, DeltaOperation
from core.sync_engine.distributed_sync import DistributedSyncEngine
from core.validation.validation_engine import ValidationEngine
from core.network_layer.holochain_dna import SignLanguageDNA, DocumentDNA, MessagingDNA

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration"""
    app_name: str
    app_id: str
    agent_pubkey: str
    holochain_conductor_url: str = "ws://localhost:8888"
    bootstrap_peers: List[str] = None
    
    def __post_init__(self):
        if self.bootstrap_peers is None:
            self.bootstrap_peers = []


class SignaverseApp:
    """Main application class for Signaverse distributed apps"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.agent_pubkey = config.agent_pubkey
        
        # Initialize core components
        self.commit_engine = CommitEngine()
        self.sync_engine = DistributedSyncEngine(self.agent_pubkey)
        self.validation_engine = ValidationEngine()
        
        # Initialize DNA modules
        self.sign_language_dna = SignLanguageDNA(self.agent_pubkey)
        self.document_dna = DocumentDNA(self.agent_pubkey)
        self.messaging_dna = MessagingDNA(self.agent_pubkey)
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Runtime state
        self.is_running = False
        
        # Setup integration between components
        self._setup_integrations()
    
    def _setup_integrations(self):
        """Setup integrations between core components"""
        # Register validation handlers
        self.sync_engine.register_sync_handler("validate_commit", 
                                                self._handle_commit_validation)
        
        # Setup sync handlers for DNA modules
        self.sync_engine.register_sync_handler("sign_video_uploaded", 
                                                self._handle_sign_video_sync)
        self.sync_engine.register_sync_handler("document_updated", 
                                                self._handle_document_sync)
        self.sync_engine.register_sync_handler("message_received", 
                                                self._handle_message_sync)
    
    async def start(self):
        """Start the application"""
        if self.is_running:
            return
        
        logger.info(f"Starting Signaverse app: {self.config.app_name}")
        
        # Start core components
        await self.sync_engine.start()
        
        # Grant basic capabilities to self
        self.validation_engine.grant_capability(self.agent_pubkey, "create_commit")
        self.validation_engine.grant_capability(self.agent_pubkey, "upload_video")
        self.validation_engine.grant_capability(self.agent_pubkey, "create_translation")
        
        self.is_running = True
        
        # Emit started event
        await self._emit_event("app_started", {
            "app_name": self.config.app_name,
            "agent_pubkey": self.agent_pubkey
        })
        
        logger.info("Signaverse app started successfully")
    
    async def stop(self):
        """Stop the application"""
        if not self.is_running:
            return
        
        logger.info("Stopping Signaverse app...")
        
        # Stop core components
        await self.sync_engine.stop()
        
        self.is_running = False
        
        # Emit stopped event
        await self._emit_event("app_stopped", {
            "app_name": self.config.app_name,
            "agent_pubkey": self.agent_pubkey
        })
        
        logger.info("Signaverse app stopped")
    
    def on_event(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
    
    # Sign Language Methods
    async def upload_sign_video(self, video_data: Dict[str, Any]) -> str:
        """Upload a sign language video"""
        # Validate capabilities
        validation_result = self.validation_engine.validate_agent_capability(
            self.agent_pubkey, "upload_video"
        )
        if validation_result.status.value != "valid":
            raise PermissionError(validation_result.message)
        
        # Upload via DNA
        video_hash = self.sign_language_dna.upload_sign_video(video_data)
        
        # Create commit
        deltas = [
            DeltaProtocol.insert("/videos", video_hash)
        ]
        commit = self.commit_engine.create_commit(deltas, message="Upload sign video")
        
        # Publish to network
        await self.sync_engine.publish_commit({
            "type": "sign_video_upload",
            "video_hash": video_hash,
            "commit_id": commit.commit_id
        })
        
        # Emit event
        await self._emit_event("sign_video_uploaded", {
            "video_hash": video_hash,
            "video_data": video_data
        })
        
        return video_hash
    
    async def create_translation(self, source_hash: str, target_language: str, 
                               translation_data: Dict[str, Any]) -> str:
        """Create a translation"""
        # Validate capabilities
        validation_result = self.validation_engine.validate_agent_capability(
            self.agent_pubkey, "create_translation"
        )
        if validation_result.status.value != "valid":
            raise PermissionError(validation_result.message)
        
        # Prepare translation data
        translation_input = {
            "source_type": "sign",
            "target_type": "text",
            "source_content": source_hash,
            "target_content": translation_data.get("target_text", ""),
            "source_language": translation_data.get("source_language", "ASL"),
            "target_language": target_language,
            "confidence": translation_data.get("confidence", 0.0)
        }
        
        # Create translation via DNA
        translation_hash = self.sign_language_dna.create_translation(translation_input)
        
        # Create commit
        deltas = [
            DeltaProtocol.insert("/translations", translation_hash)
        ]
        commit = self.commit_engine.create_commit(deltas, message="Create translation")
        
        # Publish to network
        await self.sync_engine.publish_commit({
            "type": "translation_created",
            "translation_hash": translation_hash,
            "source_hash": source_hash,
            "target_language": target_language
        })
        
        # Emit event
        await self._emit_event("translation_created", {
            "translation_hash": translation_hash,
            "source_hash": source_hash,
            "target_language": target_language
        })
        
        return translation_hash
    
    # Document Methods
    async def create_document(self, title: str, content: Dict[str, Any], 
                           metadata: Dict[str, Any] = None) -> str:
        """Create a new document"""
        # Create document via DNA
        doc_id = self.document_dna.create_document(title, content, metadata)
        
        # Create commit
        deltas = [
            DeltaProtocol.insert("/documents", doc_id)
        ]
        commit = self.commit_engine.create_commit(deltas, message=f"Create document: {title}")
        
        # Publish to network
        await self.sync_engine.publish_commit({
            "type": "document_created",
            "doc_id": doc_id,
            "title": title
        })
        
        # Emit event
        await self._emit_event("document_created", {
            "doc_id": doc_id,
            "title": title
        })
        
        return doc_id
    
    async def update_document(self, doc_id: str, deltas: List[DeltaOperation], 
                            message: str = "") -> str:
        """Update document with deltas"""
        # Check permissions
        if not self.document_dna.has_permission(doc_id, self.agent_pubkey, "write"):
            raise PermissionError("No write permission for document")
        
        # Update document via DNA
        commit_hash = self.document_dna.update_document(doc_id, deltas, message)
        
        # Publish to network
        await self.sync_engine.publish_commit({
            "type": "document_updated",
            "doc_id": doc_id,
            "commit_hash": commit_hash
        })
        
        # Emit event
        await self._emit_event("document_updated", {
            "doc_id": doc_id,
            "commit_hash": commit_hash
        })
        
        return commit_hash
    
    # Messaging Methods
    async def send_message(self, recipient: str, content: str, 
                          message_type: str = "text") -> str:
        """Send a message"""
        from dnas.messaging.zome import MessageType
        
        msg_type = MessageType(message_type)
        
        # Send message via DNA
        message_id = self.messaging_dna.send_message(
            recipient, content, msg_type
        )
        
        # Publish to network
        await self.sync_engine.publish_commit({
            "type": "message_sent",
            "message_id": message_id,
            "recipient": recipient
        })
        
        # Emit event
        await self._emit_event("message_sent", {
            "message_id": message_id,
            "recipient": recipient,
            "content": content
        })
        
        return message_id
    
    async def create_channel(self, name: str, description: str, 
                           members: List[str], is_private: bool = False) -> str:
        """Create a messaging channel"""
        # Create channel via DNA
        channel_id = self.messaging_dna.create_channel(
            name, description, members, is_private
        )
        
        # Emit event
        await self._emit_event("channel_created", {
            "channel_id": channel_id,
            "name": name
        })
        
        return channel_id
    
    # Query Methods
    async def get_sign_video(self, video_hash: str) -> Optional[Dict[str, Any]]:
        """Get sign video data"""
        video = self.sign_language_dna.get_video(video_hash)
        return video.to_dict() if video else None
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document data"""
        document = self.document_dna.get_document(doc_id)
        return document.to_dict() if document else None
    
    async def get_messages(self, recipient: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for recipient"""
        messages = self.messaging_dna.get_messages(recipient, limit)
        return [msg.to_dict() for msg in messages]
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """Get user's channels"""
        channels = self.messaging_dna.get_channels()
        return [channel.to_dict() for channel in channels]
    
    # Sync and Network Methods
    async def sync_with_network(self):
        """Manually trigger sync with network"""
        commits = await self.sync_engine.request_commits(limit=100)
        
        for commit in commits:
            await self._process_network_commit(commit)
        
        await self._emit_event("sync_completed", {
            "commits_processed": len(commits)
        })
    
    async def _process_network_commit(self, commit: Dict[str, Any]):
        """Process commit from network"""
        commit_type = commit.get("type")
        
        if commit_type == "sign_video_upload":
            await self._emit_event("network_sign_video", commit)
        elif commit_type == "document_updated":
            await self._emit_event("network_document_update", commit)
        elif commit_type == "message_sent":
            await self._emit_event("network_message", commit)
    
    # Event Handlers
    async def _handle_commit_validation(self, commit_data: Dict[str, Any]):
        """Handle commit validation from sync engine"""
        validation_result = self.validation_engine.validate(commit_data)
        
        if validation_result.status.value != "valid":
            logger.warning(f"Invalid commit received: {validation_result.message}")
    
    async def _handle_sign_video_sync(self, event_data: Dict[str, Any]):
        """Handle sign video sync event"""
        await self._emit_event("sign_video_sync", event_data)
    
    async def _handle_document_sync(self, event_data: Dict[str, Any]):
        """Handle document sync event"""
        await self._emit_event("document_sync", event_data)
    
    async def _handle_message_sync(self, event_data: Dict[str, Any]):
        """Handle message sync event"""
        await self._emit_event("message_sync", event_data)
    
    # Utility Methods
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        return {
            "sync_stats": self.sync_engine.get_network_stats(),
            "validation_stats": self.validation_engine.get_stats(),
            "sign_language_stats": self.sign_language_dna.get_chain_state(),
            "document_stats": self.document_dna.get_chain_state()
        }
    
    async def grant_capability(self, agent_pubkey: str, capability: str):
        """Grant capability to another agent"""
        self.validation_engine.grant_capability(agent_pubkey, capability)
        
        await self._emit_event("capability_granted", {
            "agent": agent_pubkey,
            "capability": capability
        })
    
    async def revoke_capability(self, agent_pubkey: str, capability: str):
        """Revoke capability from another agent"""
        self.validation_engine.revoke_capability(agent_pubkey, capability)
        
        await self._emit_event("capability_revoked", {
            "agent": agent_pubkey,
            "capability": capability
        })


# Utility Functions
def create_app_config(app_name: str, agent_pubkey: str, 
                     holochain_url: str = "ws://localhost:8888") -> AppConfig:
    """Create application configuration"""
    import hashlib
    app_id = hashlib.sha256(f"{app_name}_{agent_pubkey}".encode()).hexdigest()[:16]
    
    return AppConfig(
        app_name=app_name,
        app_id=app_id,
        agent_pubkey=agent_pubkey,
        holochain_conductor_url=holochain_url
    )


# Example Usage
async def example_usage():
    """Example of using the Signaverse SDK"""
    # Create configuration
    config = create_app_config(
        "My Sign Language App",
        "agent_pubkey_12345"
    )
    
    # Create and start app
    app = SignaverseApp(config)
    await app.start()
    
    # Register event handler
    @app.on_event("sign_video_uploaded")
    async def handle_video_upload(data):
        print(f"New video uploaded: {data['video_hash']}")
    
    try:
        # Upload a sign video
        video_data = {
            "video_hash": "video_123",
            "signer_id": "signer_456",
            "language": "ASL",
            "duration": 5.2,
            "resolution": "1920x1080",
            "format": "mp4"
        }
        
        video_hash = await app.upload_sign_video(video_data)
        print(f"Uploaded video: {video_hash}")
        
        # Create translation
        translation_hash = await app.create_translation(
            video_hash, 
            "en",
            {
                "target_text": "Hello, how are you?",
                "source_language": "ASL",
                "confidence": 0.95
            }
        )
        print(f"Created translation: {translation_hash}")
        
        # Create document
        doc_id = await app.create_document(
            "Sign Language Notes",
            {"content": "My sign language learning notes"},
            {"category": "education"}
        )
        print(f"Created document: {doc_id}")
        
        # Send message
        message_id = await app.send_message(
            "channel_789",
            "Check out this new sign video!"
        )
        print(f"Sent message: {message_id}")
        
        # Sync with network
        await app.sync_with_network()
        
        # Get stats
        stats = app.get_network_stats()
        print(f"Network stats: {stats}")
        
    finally:
        await app.stop()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
