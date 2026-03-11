"""
Messaging DNA Zome
Holochain zome for peer-to-peer messaging and communication
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib

from core.network_layer.holochain_dna import HolochainDNA, EntryType


class MessageType(Enum):
    """Message types"""
    TEXT = "text"
    SIGN_VIDEO = "sign_video"
    TRANSLATION = "translation"
    SYSTEM = "system"
    REACTION = "reaction"


@dataclass
class Message:
    """Message data structure"""
    message_id: str
    sender: str
    recipient: str  # Can be individual or channel
    message_type: MessageType
    content: str
    timestamp: float
    edited: bool
    edited_timestamp: Optional[float]
    reply_to: Optional[str]  # Message ID this replies to
    reactions: Dict[str, List[str]]  # emoji -> list of agent pubkeys
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "edited": self.edited,
            "edited_timestamp": self.edited_timestamp,
            "reply_to": self.reply_to,
            "reactions": self.reactions,
            "metadata": self.metadata
        }


@dataclass
class Channel:
    """Channel/group data structure"""
    channel_id: str
    name: str
    description: str
    creator: str
    members: List[str]
    admins: List[str]
    created_at: float
    is_private: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "description": self.description,
            "creator": self.creator,
            "members": self.members,
            "admins": self.admins,
            "created_at": self.created_at,
            "is_private": self.is_private,
            "metadata": self.metadata
        }


@dataclass
class DirectMessage:
    """Direct message conversation"""
    conversation_id: str
    participants: List[str]  # Exactly 2 participants
    created_at: float
    last_message: Optional[str]  # Last message ID
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "participants": self.participants,
            "created_at": self.created_at,
            "last_message": self.last_message,
            "metadata": self.metadata
        }


class MessagingZome(HolochainDNA):
    """Messaging and communication zome"""
    
    def __init__(self, agent_pubkey: str):
        super().__init__("messaging", agent_pubkey)
        self.messages: Dict[str, Message] = {}
        self.channels: Dict[str, Channel] = {}
        self.conversations: Dict[str, DirectMessage] = {}
        self.unread_counts: Dict[str, Dict[str, int]] = {}  # recipient -> sender -> count
        
    def send_message(self, recipient: str, content: str, 
                    message_type: MessageType = MessageType.TEXT,
                    reply_to: Optional[str] = None,
                    metadata: Dict[str, Any] = None) -> str:
        """Send a message to recipient (individual or channel)"""
        message_id = self._generate_message_id()
        
        message = Message(
            message_id=message_id,
            sender=self.agent_pubkey,
            recipient=recipient,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            edited=False,
            edited_timestamp=None,
            reply_to=reply_to,
            reactions={},
            metadata=metadata or {}
        )
        
        # Store locally
        self.messages[message_id] = message
        
        # Update unread counts
        self._update_unread_count(recipient, self.agent_pubkey, 1)
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "message",
            "message_data": message.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return message_id
    
    def edit_message(self, message_id: str, new_content: str) -> bool:
        """Edit an existing message"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Only sender can edit
        if message.sender != self.agent_pubkey:
            return False
        
        # Update message
        message.content = new_content
        message.edited = True
        message.edited_timestamp = time.time()
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "message",
            "message_data": message.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return True
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Only sender can delete
        if message.sender != self.agent_pubkey:
            return False
        
        # Mark as deleted (soft delete)
        message.content = "[DELETED]"
        message.metadata["deleted"] = True
        message.metadata["deleted_at"] = time.time()
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "message",
            "message_data": message.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return True
    
    def add_reaction(self, message_id: str, emoji: str) -> bool:
        """Add reaction to message"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Add reaction
        if emoji not in message.reactions:
            message.reactions[emoji] = []
        
        if self.agent_pubkey not in message.reactions[emoji]:
            message.reactions[emoji].append(self.agent_pubkey)
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "message",
            "message_data": message.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return True
    
    def remove_reaction(self, message_id: str, emoji: str) -> bool:
        """Remove reaction from message"""
        if message_id not in self.messages:
            return False
        
        message = self.messages[message_id]
        
        # Remove reaction
        if emoji in message.reactions and self.agent_pubkey in message.reactions[emoji]:
            message.reactions[emoji].remove(self.agent_pubkey)
            
            # Clean up empty reaction lists
            if not message.reactions[emoji]:
                del message.reactions[emoji]
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "message",
            "message_data": message.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return True
    
    def create_channel(self, name: str, description: str, 
                      members: List[str], is_private: bool = False,
                      metadata: Dict[str, Any] = None) -> str:
        """Create a new channel"""
        channel_id = self._generate_channel_id()
        
        # Add creator as member and admin
        all_members = list(set([self.agent_pubkey] + members))
        admins = [self.agent_pubkey]
        
        channel = Channel(
            channel_id=channel_id,
            name=name,
            description=description,
            creator=self.agent_pubkey,
            members=all_members,
            admins=admins,
            created_at=time.time(),
            is_private=is_private,
            metadata=metadata or {}
        )
        
        # Store locally
        self.channels[channel_id] = channel
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "channel",
            "channel_data": channel.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return channel_id
    
    def join_channel(self, channel_id: str) -> bool:
        """Join a channel"""
        if channel_id not in self.channels:
            return False
        
        channel = self.channels[channel_id]
        
        # Check if channel is private and user needs invitation
        if channel.is_private and self.agent_pubkey not in channel.members:
            return False
        
        # Add to members
        if self.agent_pubkey not in channel.members:
            channel.members.append(self.agent_pubkey)
            
            # Create Holochain entry
            entry = self.create_entry(EntryType.APP_STATE, {
                "type": "channel",
                "channel_data": channel.to_dict()
            })
            
            # Publish to DHT
            self.publish_to_dht(entry)
        
        return True
    
    def leave_channel(self, channel_id: str) -> bool:
        """Leave a channel"""
        if channel_id not in self.channels:
            return False
        
        channel = self.channels[channel_id]
        
        # Cannot leave if you're the creator
        if channel.creator == self.agent_pubkey:
            return False
        
        # Remove from members and admins
        if self.agent_pubkey in channel.members:
            channel.members.remove(self.agent_pubkey)
        
        if self.agent_pubkey in channel.admins:
            channel.admins.remove(self.agent_pubkey)
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "channel",
            "channel_data": channel.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return True
    
    def start_conversation(self, other_participant: str) -> str:
        """Start a direct message conversation"""
        conversation_id = self._generate_conversation_id([self.agent_pubkey, other_participant])
        
        # Check if conversation already exists
        if conversation_id in self.conversations:
            return conversation_id
        
        conversation = DirectMessage(
            conversation_id=conversation_id,
            participants=[self.agent_pubkey, other_participant],
            created_at=time.time(),
            last_message=None,
            metadata={}
        )
        
        # Store locally
        self.conversations[conversation_id] = conversation
        
        # Create Holochain entry
        entry = self.create_entry(EntryType.APP_STATE, {
            "type": "conversation",
            "conversation_data": conversation.to_dict()
        })
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return conversation_id
    
    def get_messages(self, recipient: str, limit: int = 50, 
                     before: Optional[float] = None) -> List[Message]:
        """Get messages for recipient (individual or channel)"""
        messages = []
        
        # Get from local storage
        for message in self.messages.values():
            if message.recipient == recipient:
                if before is None or message.timestamp < before:
                    messages.append(message)
        
        # Query DHT for additional messages
        entries = self.query_entries(EntryType.APP_STATE)
        for entry in entries:
            if entry.data.get("type") == "message":
                message_data = entry.data["message_data"]
                if message_data["recipient"] == recipient:
                    if before is None or message_data["timestamp"] < before:
                        message = Message(
                            message_id=message_data["message_id"],
                            sender=message_data["sender"],
                            recipient=message_data["recipient"],
                            message_type=MessageType(message_data["message_type"]),
                            content=message_data["content"],
                            timestamp=message_data["timestamp"],
                            edited=message_data["edited"],
                            edited_timestamp=message_data.get("edited_timestamp"),
                            reply_to=message_data.get("reply_to"),
                            reactions=message_data.get("reactions", {}),
                            metadata=message_data.get("metadata", {})
                        )
                        if message.message_id not in self.messages:
                            self.messages[message.message_id] = message
                        messages.append(message)
        
        # Sort by timestamp and limit
        messages.sort(key=lambda x: x.timestamp, reverse=True)
        return messages[:limit]
    
    def get_channels(self) -> List[Channel]:
        """Get channels user is member of"""
        user_channels = []
        
        for channel in self.channels.values():
            if self.agent_pubkey in channel.members:
                user_channels.append(channel)
        
        # Query DHT for additional channels
        entries = self.query_entries(EntryType.APP_STATE)
        for entry in entries:
            if entry.data.get("type") == "channel":
                channel_data = entry.data["channel_data"]
                if (self.agent_pubkey in channel_data["members"] and 
                    channel_data["channel_id"] not in self.channels):
                    channel = Channel(
                        channel_id=channel_data["channel_id"],
                        name=channel_data["name"],
                        description=channel_data["description"],
                        creator=channel_data["creator"],
                        members=channel_data["members"],
                        admins=channel_data["admins"],
                        created_at=channel_data["created_at"],
                        is_private=channel_data["is_private"],
                        metadata=channel_data.get("metadata", {})
                    )
                    self.channels[channel.channel_id] = channel
                    if self.agent_pubkey in channel.members:
                        user_channels.append(channel)
        
        return user_channels
    
    def get_conversations(self) -> List[DirectMessage]:
        """Get direct message conversations"""
        user_conversations = []
        
        for conversation in self.conversations.values():
            if self.agent_pubkey in conversation.participants:
                user_conversations.append(conversation)
        
        return user_conversations
    
    def mark_as_read(self, recipient: str, sender: str) -> bool:
        """Mark messages from sender as read"""
        if recipient not in self.unread_counts:
            self.unread_counts[recipient] = {}
        
        if sender in self.unread_counts[recipient]:
            del self.unread_counts[recipient][sender]
        
        return True
    
    def get_unread_count(self, recipient: str) -> int:
        """Get total unread count for recipient"""
        if recipient not in self.unread_counts:
            return 0
        
        return sum(self.unread_counts[recipient].values())
    
    def _update_unread_count(self, recipient: str, sender: str, count: int):
        """Update unread count"""
        if recipient not in self.unread_counts:
            self.unread_counts[recipient] = {}
        
        if sender not in self.unread_counts[recipient]:
            self.unread_counts[recipient][sender] = 0
        
        self.unread_counts[recipient][sender] += count
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = str(time.time())
        agent_suffix = self.agent_pubkey[:8]
        return hashlib.sha256(f"msg_{timestamp}_{agent_suffix}".encode()).hexdigest()[:16]
    
    def _generate_channel_id(self) -> str:
        """Generate unique channel ID"""
        timestamp = str(time.time())
        agent_suffix = self.agent_pubkey[:8]
        return hashlib.sha256(f"chan_{timestamp}_{agent_suffix}".encode()).hexdigest()[:16]
    
    def _generate_conversation_id(self, participants: List[str]) -> str:
        """Generate conversation ID from participants"""
        sorted_participants = sorted(participants)
        participants_str = "_".join(sorted_participants)
        return hashlib.sha256(participants_str.encode()).hexdigest()[:16]
