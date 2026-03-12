"""
Albrite Holochain SDK - Advanced Integration for Family-Based Agent Architecture
Enterprise-grade SDK for Holochain distributed coordination with genetic family systems
"""

import asyncio
import json
import logging
import time
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import aiohttp
import websockets

logger = logging.getLogger(__name__)


class HolochainNetworkType(Enum):
    """Holochain network types"""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    CUSTOM = "custom"


class HolochainLogLevel(Enum):
    """Holochain logging levels"""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class HolochainRole(Enum):
    """Holochain node roles"""
    VALIDATOR = "validator"
    WITNESS = "witness"
    PARTICIPANT = "participant"
    COORDINATOR = "coordinator"


class FamilyRole(Enum):
    """Albrite family roles in Holochain"""
    PATRIARCH = "patriarch"
    MATRIARCH = "matriarch"
    ELDEST_CHILD = "eldest_child"
    YOUNGER_CHILD = "younger_child"
    MILITARY_COMMANDER = "military_commander"


@dataclass
class HolochainConfig:
    """Holochain configuration"""
    network_type: HolochainNetworkType = HolochainNetworkType.LOCAL
    conductor_endpoint: str = "ws://localhost:9001"
    admin_port: int = 9001
    app_interface_port: int = 9002
    dna_path: Optional[str] = None
    agent_key: Optional[str] = None
    log_level: HolochainLogLevel = HolochainLogLevel.INFO
    max_retries: int = 3
    timeout: float = 30.0
    enable_encryption: bool = True
    enable_persistence: bool = True


@dataclass
class FamilyMember:
    """Family member in Holochain"""
    agent_id: str
    name: str
    role: FamilyRole
    genetic_code: Dict[str, float]
    public_key: str
    created_at: datetime
    last_active: datetime
    reputation_score: float = 0.0
    family_bonds: List[str] = field(default_factory=list)
    contributions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HolochainTransaction:
    """Holochain transaction structure"""
    transaction_id: str
    author: str
    timestamp: datetime
    entry_type: str
    entry_data: Dict[str, Any]
    signature: Optional[str] = None
    witnesses: List[str] = field(default_factory=list)
    validation_status: str = "pending"


@dataclass
class GeneticInheritance:
    """Genetic inheritance record"""
    inheritance_id: str
    parent_ids: List[str]
    child_id: str
    inherited_traits: Dict[str, float]
    mutations: Dict[str, float]
    timestamp: datetime


class AlbriteHolochainSDK:
    """Advanced Holochain SDK for Albrite Family System"""
    
    def __init__(self, config: HolochainConfig = None):
        self.config = config or HolochainConfig()
        self.session = None
        self.websocket = None
        self.agent_id = None
        self.app_id = None
        self.dna_hash = None
        self.family_members = {}
        self.active_transactions = {}
        self.event_handlers = {}
        self.is_connected = False
        
        # Performance metrics
        self.metrics = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "average_response_time": 0.0,
            "network_health": 1.0,
            "family_size": 0
        }
        
        logger.info("Albrite Holochain SDK initialized")
    
    async def connect(self) -> bool:
        """Connect to Holochain conductor"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                self.config.conductor_endpoint,
                timeout=self.config.timeout
            )
            
            # Authenticate and get agent info
            await self._authenticate()
            
            # Load DNA if specified
            if self.config.dna_path:
                await self._load_dna()
            
            self.is_connected = True
            logger.info("Connected to Holochain conductor")
            
            # Start event listener
            asyncio.create_task(self._event_listener())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Holochain: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Holochain conductor"""
        try:
            if self.websocket:
                await self.websocket.close()
            if self.session:
                await self.session.close()
            
            self.is_connected = False
            logger.info("Disconnected from Holochain conductor")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def _authenticate(self):
        """Authenticate with Holochain conductor"""
        try:
            # Generate or use provided agent key
            if not self.config.agent_key:
                self.config.agent_key = self._generate_agent_key()
            
            # Authenticate request
            auth_request = {
                "id": str(uuid.uuid4()),
                "type": "agent_info",
                "data": {
                    "agent_key": self.config.agent_key,
                    "name": f"Albrite-Agent-{self.config.agent_key[:8]}"
                }
            }
            
            await self.websocket.send(json.dumps(auth_request))
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("type") == "agent_info_response":
                self.agent_id = auth_response["data"]["agent_id"]
                logger.info(f"Authenticated as agent: {self.agent_id}")
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    async def _load_dna(self):
        """Load DNA into Holochain"""
        try:
            with open(self.config.dna_path, 'rb') as f:
                dna_content = f.read()
            
            dna_hash = hashlib.sha256(dna_content).hexdigest()
            
            # Install DNA request
            install_request = {
                "id": str(uuid.uuid4()),
                "type": "install_app",
                "data": {
                    "app_id": "albrite_family",
                    "dna": {
                        "path": self.config.dna_path,
                        "hash": dna_hash
                    },
                    "agent_key": self.config.agent_key
                }
            }
            
            await self.websocket.send(json.dumps(install_request))
            response = await self.websocket.recv()
            install_response = json.loads(response)
            
            if install_response.get("type") == "install_app_response":
                self.app_id = install_response["data"]["app_id"]
                self.dna_hash = dna_hash
                logger.info(f"DNA loaded successfully: {self.app_id}")
            else:
                raise Exception("DNA installation failed")
                
        except Exception as e:
            logger.error(f"DNA loading error: {e}")
            raise
    
    async def _event_listener(self):
        """Listen for Holochain events"""
        try:
            while self.is_connected:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    event = json.loads(message)
                    await self._handle_event(event)
                    
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
                    
        except Exception as e:
            logger.error(f"Event listener error: {e}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle incoming Holochain events"""
        event_type = event.get("type")
        
        if event_type in self.event_handlers:
            handler = self.event_handlers[event_type]
            await handler(event)
        
        # Handle specific event types
        if event_type == "signal":
            await self._handle_signal(event)
        elif event_type == "new_transaction":
            await self._handle_new_transaction(event)
        elif event_type == "family_update":
            await self._handle_family_update(event)
    
    async def _handle_signal(self, event: Dict[str, Any]):
        """Handle Holochain signals"""
        signal_data = event.get("data", {})
        logger.info(f"Received signal: {signal_data}")
    
    async def _handle_new_transaction(self, event: Dict[str, Any]):
        """Handle new transaction events"""
        tx_data = event.get("data", {})
        self.metrics["total_transactions"] += 1
        
        if tx_data.get("validation_status") == "validated":
            self.metrics["successful_transactions"] += 1
        else:
            self.metrics["failed_transactions"] += 1
        
        logger.info(f"New transaction: {tx_data.get('transaction_id')}")
    
    async def _handle_family_update(self, event: Dict[str, Any]):
        """Handle family update events"""
        family_data = event.get("data", {})
        logger.info(f"Family update: {family_data}")
    
    def _generate_agent_key(self) -> str:
        """Generate new agent key"""
        import secrets
        return secrets.token_hex(32)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    # Family Management Methods
    async def register_family_member(self, member: FamilyMember) -> str:
        """Register a family member in Holochain"""
        try:
            transaction = HolochainTransaction(
                transaction_id=str(uuid.uuid4()),
                author=self.agent_id,
                timestamp=datetime.now(),
                entry_type="family_member",
                entry_data={
                    "agent_id": member.agent_id,
                    "name": member.name,
                    "role": member.role.value,
                    "genetic_code": member.genetic_code,
                    "public_key": member.public_key,
                    "created_at": member.created_at.isoformat(),
                    "last_active": member.last_active.isoformat(),
                    "reputation_score": member.reputation_score,
                    "family_bonds": member.family_bonds,
                    "contributions": member.contributions
                }
            )
            
            # Submit transaction
            result = await self._submit_transaction(transaction)
            
            if result["success"]:
                self.family_members[member.agent_id] = member
                self.metrics["family_size"] = len(self.family_members)
                logger.info(f"Family member registered: {member.name}")
            
            return result["transaction_id"]
            
        except Exception as e:
            logger.error(f"Failed to register family member: {e}")
            raise
    
    async def update_genetic_inheritance(self, inheritance: GeneticInheritance) -> str:
        """Record genetic inheritance in Holochain"""
        try:
            transaction = HolochainTransaction(
                transaction_id=str(uuid.uuid4()),
                author=self.agent_id,
                timestamp=datetime.now(),
                entry_type="genetic_inheritance",
                entry_data={
                    "inheritance_id": inheritance.inheritance_id,
                    "parent_ids": inheritance.parent_ids,
                    "child_id": inheritance.child_id,
                    "inherited_traits": inheritance.inherited_traits,
                    "mutations": inheritance.mutations,
                    "timestamp": inheritance.timestamp.isoformat()
                }
            )
            
            result = await self._submit_transaction(transaction)
            
            if result["success"]:
                logger.info(f"Genetic inheritance recorded: {inheritance.inheritance_id}")
            
            return result["transaction_id"]
            
        except Exception as e:
            logger.error(f"Failed to record genetic inheritance: {e}")
            raise
    
    async def create_family_bond(self, agent_id_1: str, agent_id_2: str, 
                               bond_strength: float, bond_type: str = "family") -> str:
        """Create family bond between two agents"""
        try:
            transaction = HolochainTransaction(
                transaction_id=str(uuid.uuid4()),
                author=self.agent_id,
                timestamp=datetime.now(),
                entry_type="family_bond",
                entry_data={
                    "agent_id_1": agent_id_1,
                    "agent_id_2": agent_id_2,
                    "bond_strength": bond_strength,
                    "bond_type": bond_type,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            result = await self._submit_transaction(transaction)
            
            if result["success"]:
                # Update local family members
                if agent_id_1 in self.family_members:
                    if agent_id_2 not in self.family_members[agent_id_1].family_bonds:
                        self.family_members[agent_id_1].family_bonds.append(agent_id_2)
                
                if agent_id_2 in self.family_members:
                    if agent_id_1 not in self.family_members[agent_id_2].family_bonds:
                        self.family_members[agent_id_2].family_bonds.append(agent_id_1)
                
                logger.info(f"Family bond created: {agent_id_1} <-> {agent_id_2}")
            
            return result["transaction_id"]
            
        except Exception as e:
            logger.error(f"Failed to create family bond: {e}")
            raise
    
    async def record_contribution(self, agent_id: str, contribution_type: str, 
                               value: float, description: str) -> str:
        """Record agent contribution in family ledger"""
        try:
            contribution = {
                "contribution_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "type": contribution_type,
                "value": value,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "recorded_by": self.agent_id
            }
            
            transaction = HolochainTransaction(
                transaction_id=str(uuid.uuid4()),
                author=self.agent_id,
                timestamp=datetime.now(),
                entry_type="contribution",
                entry_data=contribution
            )
            
            result = await self._submit_transaction(transaction)
            
            if result["success"]:
                # Update local family member
                if agent_id in self.family_members:
                    self.family_members[agent_id].contributions.append(contribution)
                
                logger.info(f"Contribution recorded: {agent_id} - {contribution_type}")
            
            return result["transaction_id"]
            
        except Exception as e:
            logger.error(f"Failed to record contribution: {e}")
            raise
    
    async def _submit_transaction(self, transaction: HolochainTransaction) -> Dict[str, Any]:
        """Submit transaction to Holochain"""
        try:
            start_time = time.time()
            
            # Sign transaction if encryption is enabled
            if self.config.enable_encryption:
                transaction.signature = self._sign_transaction(transaction)
            
            # Submit request
            submit_request = {
                "id": str(uuid.uuid4()),
                "type": "call_zome",
                "data": {
                    "app_id": self.app_id,
                    "zome": "family",
                    "function": "create_entry",
                    "args": {
                        "entry": {
                            "entry_type": transaction.entry_type,
                            "data": transaction.entry_data,
                            "timestamp": transaction.timestamp.isoformat(),
                            "author": transaction.author,
                            "signature": transaction.signature
                        }
                    }
                }
            }
            
            await self.websocket.send(json.dumps(submit_request))
            response = await self.websocket.recv()
            submit_response = json.loads(response)
            
            # Calculate response time
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            if submit_response.get("type") == "call_zome_response":
                return {
                    "success": True,
                    "transaction_id": transaction.transaction_id,
                    "response_time": response_time
                }
            else:
                error_msg = submit_response.get("data", {}).get("error", "Unknown error")
                return {
                    "success": False,
                    "error": error_msg,
                    "response_time": response_time
                }
                
        except Exception as e:
            logger.error(f"Transaction submission error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": 0.0
            }
    
    def _sign_transaction(self, transaction: HolochainTransaction) -> str:
        """Sign transaction with agent key"""
        # Simplified signing - in production, use proper cryptographic signing
        data_to_sign = f"{transaction.transaction_id}{transaction.author}{transaction.timestamp.isoformat()}"
        signature = hashlib.sha256((data_to_sign + self.config.agent_key).encode()).hexdigest()
        return signature
    
    def _update_response_time(self, response_time: float):
        """Update average response time metric"""
        total = self.metrics["total_transactions"]
        if total == 0:
            self.metrics["average_response_time"] = response_time
        else:
            current_avg = self.metrics["average_response_time"]
            self.metrics["average_response_time"] = (current_avg * (total - 1) + response_time) / total
    
    # Query Methods
    async def get_family_member(self, agent_id: str) -> Optional[FamilyMember]:
        """Get family member by ID"""
        try:
            query_request = {
                "id": str(uuid.uuid4()),
                "type": "call_zome",
                "data": {
                    "app_id": self.app_id,
                    "zome": "family",
                    "function": "get_family_member",
                    "args": {"agent_id": agent_id}
                }
            }
            
            await self.websocket.send(json.dumps(query_request))
            response = await self.websocket.recv()
            query_response = json.loads(response)
            
            if query_response.get("type") == "call_zome_response":
                member_data = query_response.get("data", {})
                if member_data:
                    return FamilyMember(
                        agent_id=member_data["agent_id"],
                        name=member_data["name"],
                        role=FamilyRole(member_data["role"]),
                        genetic_code=member_data["genetic_code"],
                        public_key=member_data["public_key"],
                        created_at=datetime.fromisoformat(member_data["created_at"]),
                        last_active=datetime.fromisoformat(member_data["last_active"]),
                        reputation_score=member_data.get("reputation_score", 0.0),
                        family_bonds=member_data.get("family_bonds", []),
                        contributions=member_data.get("contributions", [])
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get family member: {e}")
            return None
    
    async def get_family_tree(self, root_agent_id: str = None) -> Dict[str, Any]:
        """Get complete family tree"""
        try:
            query_request = {
                "id": str(uuid.uuid4()),
                "type": "call_zome",
                "data": {
                    "app_id": self.app_id,
                    "zome": "family",
                    "function": "get_family_tree",
                    "args": {"root_agent_id": root_agent_id}
                }
            }
            
            await self.websocket.send(json.dumps(query_request))
            response = await self.websocket.recv()
            query_response = json.loads(response)
            
            if query_response.get("type") == "call_zome_response":
                return query_response.get("data", {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get family tree: {e}")
            return {}
    
    async def get_genetic_lineage(self, agent_id: str) -> List[GeneticInheritance]:
        """Get genetic lineage for an agent"""
        try:
            query_request = {
                "id": str(uuid.uuid4()),
                "type": "call_zome",
                "data": {
                    "app_id": self.app_id,
                    "zome": "family",
                    "function": "get_genetic_lineage",
                    "args": {"agent_id": agent_id}
                }
            }
            
            await self.websocket.send(json.dumps(query_request))
            response = await self.websocket.recv()
            query_response = json.loads(response)
            
            lineage = []
            if query_response.get("type") == "call_zome_response":
                inheritance_data = query_response.get("data", [])
                for data in inheritance_data:
                    lineage.append(GeneticInheritance(
                        inheritance_id=data["inheritance_id"],
                        parent_ids=data["parent_ids"],
                        child_id=data["child_id"],
                        inherited_traits=data["inherited_traits"],
                        mutations=data["mutations"],
                        timestamp=datetime.fromisoformat(data["timestamp"])
                    ))
            
            return lineage
            
        except Exception as e:
            logger.error(f"Failed to get genetic lineage: {e}")
            return []
    
    async def get_contributions(self, agent_id: str = None, 
                             start_time: datetime = None, 
                             end_time: datetime = None) -> List[Dict[str, Any]]:
        """Get contributions with optional filters"""
        try:
            query_request = {
                "id": str(uuid.uuid4()),
                "type": "call_zome",
                "data": {
                    "app_id": self.app_id,
                    "zome": "family",
                    "function": "get_contributions",
                    "args": {
                        "agent_id": agent_id,
                        "start_time": start_time.isoformat() if start_time else None,
                        "end_time": end_time.isoformat() if end_time else None
                    }
                }
            }
            
            await self.websocket.send(json.dumps(query_request))
            response = await self.websocket.recv()
            query_response = json.loads(response)
            
            if query_response.get("type") == "call_zome_response":
                return query_response.get("data", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get contributions: {e}")
            return []
    
    # Network Management
    async def get_network_status(self) -> Dict[str, Any]:
        """Get Holochain network status"""
        try:
            status_request = {
                "id": str(uuid.uuid4()),
                "type": "network_info",
                "data": {}
            }
            
            await self.websocket.send(json.dumps(status_request))
            response = await self.websocket.recv()
            status_response = json.loads(response)
            
            if status_response.get("type") == "network_info_response":
                network_data = status_response.get("data", {})
                self.metrics["network_health"] = network_data.get("health", 1.0)
                return network_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get network status: {e}")
            return {}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get SDK performance metrics"""
        return {
            "sdk_metrics": self.metrics.copy(),
            "network_status": await self.get_network_status(),
            "family_size": len(self.family_members),
            "active_transactions": len(self.active_transactions),
            "connection_status": self.is_connected,
            "uptime": time.time() if self.is_connected else 0
        }
    
    # Advanced Features
    async def create_family_consensus(self, proposal: Dict[str, Any], 
                                  voting_period: timedelta = timedelta(hours=24)) -> str:
        """Create family consensus proposal"""
        try:
            consensus_data = {
                "consensus_id": str(uuid.uuid4()),
                "proposal": proposal,
                "created_by": self.agent_id,
                "created_at": datetime.now().isoformat(),
                "voting_period": voting_period.total_seconds(),
                "votes": {},
                "status": "active"
            }
            
            transaction = HolochainTransaction(
                transaction_id=str(uuid.uuid4()),
                author=self.agent_id,
                timestamp=datetime.now(),
                entry_type="family_consensus",
                entry_data=consensus_data
            )
            
            result = await self._submit_transaction(transaction)
            
            if result["success"]:
                logger.info(f"Family consensus created: {consensus_data['consensus_id']}")
            
            return result["transaction_id"]
            
        except Exception as e:
            logger.error(f"Failed to create family consensus: {e}")
            raise
    
    async def vote_on_consensus(self, consensus_id: str, vote: str, 
                              reason: str = None) -> str:
        """Vote on family consensus proposal"""
        try:
            vote_data = {
                "consensus_id": consensus_id,
                "voter": self.agent_id,
                "vote": vote,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            
            transaction = HolochainTransaction(
                transaction_id=str(uuid.uuid4()),
                author=self.agent_id,
                timestamp=datetime.now(),
                entry_type="consensus_vote",
                entry_data=vote_data
            )
            
            result = await self._submit_transaction(transaction)
            
            if result["success"]:
                logger.info(f"Vote cast on consensus: {consensus_id}")
            
            return result["transaction_id"]
            
        except Exception as e:
            logger.error(f"Failed to vote on consensus: {e}")
            raise
    
    async def get_family_reputation(self, agent_id: str) -> float:
        """Calculate family member reputation based on contributions and interactions"""
        try:
            contributions = await self.get_contributions(agent_id)
            
            if not contributions:
                return 0.0
            
            # Calculate reputation based on contribution value and recency
            total_value = 0.0
            now = datetime.now()
            
            for contribution in contributions:
                value = contribution.get("value", 0.0)
                timestamp = datetime.fromisoformat(contribution["timestamp"])
                
                # Apply time decay (older contributions have less weight)
                days_old = (now - timestamp).days
                time_weight = max(0.1, 1.0 - (days_old / 365.0))  # 1 year decay
                
                total_value += value * time_weight
            
            # Normalize reputation score
            reputation = min(1.0, total_value / 1000.0)  # Normalize to 0-1 range
            
            return reputation
            
        except Exception as e:
            logger.error(f"Failed to calculate reputation: {e}")
            return 0.0
    
    # Utility Methods
    async def backup_family_data(self, backup_path: str) -> bool:
        """Backup all family data to file"""
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "family_members": {
                    agent_id: {
                        "agent_id": member.agent_id,
                        "name": member.name,
                        "role": member.role.value,
                        "genetic_code": member.genetic_code,
                        "public_key": member.public_key,
                        "created_at": member.created_at.isoformat(),
                        "last_active": member.last_active.isoformat(),
                        "reputation_score": member.reputation_score,
                        "family_bonds": member.family_bonds,
                        "contributions": member.contributions
                    }
                    for agent_id, member in self.family_members.items()
                },
                "metrics": self.metrics,
                "config": {
                    "network_type": self.config.network_type.value,
                    "app_id": self.app_id,
                    "dna_hash": self.dna_hash
                }
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Family data backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup family data: {e}")
            return False
    
    async def restore_family_data(self, backup_path: str) -> bool:
        """Restore family data from backup file"""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            # Restore family members
            for agent_id, member_data in backup_data["family_members"].items():
                member = FamilyMember(
                    agent_id=member_data["agent_id"],
                    name=member_data["name"],
                    role=FamilyRole(member_data["role"]),
                    genetic_code=member_data["genetic_code"],
                    public_key=member_data["public_key"],
                    created_at=datetime.fromisoformat(member_data["created_at"]),
                    last_active=datetime.fromisoformat(member_data["last_active"]),
                    reputation_score=member_data.get("reputation_score", 0.0),
                    family_bonds=member_data.get("family_bonds", []),
                    contributions=member_data.get("contributions", [])
                )
                self.family_members[agent_id] = member
            
            # Restore metrics
            self.metrics.update(backup_data.get("metrics", {}))
            
            logger.info(f"Family data restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore family data: {e}")
            return False


# Convenience Functions
async def create_albrite_holochain_sdk(network_type: HolochainNetworkType = HolochainNetworkType.LOCAL,
                                      conductor_endpoint: str = None,
                                      dna_path: str = None) -> AlbriteHolochainSDK:
    """Create and initialize Albrite Holochain SDK"""
    
    config = HolochainConfig(
        network_type=network_type,
        conductor_endpoint=conductor_endpoint or "ws://localhost:9001",
        dna_path=dna_path
    )
    
    sdk = AlbriteHolochainSDK(config)
    success = await sdk.connect()
    
    if not success:
        raise Exception("Failed to connect to Holochain conductor")
    
    return sdk


# Example Usage
async def example_usage():
    """Example usage of Albrite Holochain SDK"""
    
    # Create SDK instance
    sdk = await create_albrite_holochain_sdk(
        network_type=HolochainNetworkType.LOCAL,
        dna_path="path/to/albrite_family.dna"
    )
    
    try:
        # Register family members
        patriarch = FamilyMember(
            agent_id="patriarch_001",
            name="General Albrite",
            role=FamilyRole.PATRIARCH,
            genetic_code={
                "resilience": 0.95,
                "intelligence": 0.92,
                "creativity": 0.88,
                "empathy": 0.85,
                "leadership": 0.98,
                "speed": 0.87,
                "memory": 0.91,
                "communication": 0.94,
                "adaptability": 0.89,
                "intuition": 0.86
            },
            public_key="patriarch_public_key",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        await sdk.register_family_member(patriarch)
        
        # Create family bonds
        await sdk.create_family_bond("patriarch_001", "matriarch_001", 0.95)
        
        # Record contributions
        await sdk.record_contribution(
            "patriarch_001", 
            "strategic_planning", 
            100.0, 
            "Developed family strategic plan"
        )
        
        # Get family tree
        family_tree = await sdk.get_family_tree("patriarch_001")
        print(f"Family tree: {family_tree}")
        
        # Get metrics
        metrics = await sdk.get_metrics()
        print(f"SDK metrics: {metrics}")
        
        # Backup data
        await sdk.backup_family_data("family_backup.json")
        
    finally:
        await sdk.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
