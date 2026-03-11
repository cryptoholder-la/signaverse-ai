"""
Advanced P2P Node Implementation
Inspired by Iroh with QUIC transport and NAT traversal
"""

import asyncio
import json
import time
import hashlib
import socket
import struct
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import aiofiles
import ssl

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the network"""
    BOOTSTRAP = "bootstrap"
    RELAY = "relay"
    STORAGE = "storage"
    COMPUTE = "compute"
    CLIENT = "client"


class ConnectionState(Enum):
    """Connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    HANDSHAKING = "handshaking"
    ERROR = "error"


@dataclass
class PeerInfo:
    """Information about a peer"""
    def __init__(self, node_id: str, endpoint: str, node_type: NodeType,
                 capabilities: List[str] = None, metadata: Dict[str, Any] = None):
        self.node_id = node_id
        self.endpoint = endpoint
        self.node_type = node_type
        self.capabilities = capabilities or []
        self.metadata = metadata or {}
        self.connection_state = ConnectionState.DISCONNECTED
        self.last_seen = time.time()
        self.reputation = 50.0
        self.latency = 0.0
        self.bandwidth = 0.0
        self.connection_attempts = 0
        self.successful_connections = 0
        self.public_key: Optional[str] = None
        self.addresses: List[str] = []
    
    def update_connection_success(self, latency: float):
        """Update connection success metrics"""
        self.last_seen = time.time()
        self.connection_attempts += 1
        self.successful_connections += 1
        self.latency = latency
        
        # Update reputation based on success rate
        success_rate = self.successful_connections / self.connection_attempts
        self.reputation = min(100, self.reputation + (success_rate * 10))
    
    def update_connection_failure(self):
        """Update connection failure metrics"""
        self.connection_attempts += 1
        self.reputation = max(0, self.reputation - 5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "endpoint": self.endpoint,
            "node_type": self.node_type.value,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "connection_state": self.connection_state.value,
            "last_seen": self.last_seen,
            "reputation": self.reputation,
            "latency": self.latency,
            "bandwidth": self.bandwidth,
            "connection_attempts": self.connection_attempts,
            "successful_connections": self.successful_connections,
            "public_key": self.public_key,
            "addresses": self.addresses
        }


@dataclass
class NetworkMessage:
    """Message sent between nodes"""
    def __init__(self, message_id: str, sender: str, recipient: Optional[str],
                 message_type: str, payload: Dict[str, Any], ttl: int = 3,
                 priority: int = 5, encryption: bool = False):
        self.message_id = message_id
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.payload = payload
        self.ttl = ttl
        self.priority = priority
        self.encryption = encryption
        self.timestamp = time.time()
        self.hops = 0
        self.route_history: List[str] = []
    
    def add_hop(self, node_id: str):
        """Add a hop to the route history"""
        self.hops += 1
        self.route_history.append(node_id)
    
    def is_expired(self) -> bool:
        """Check if message has expired based on TTL"""
        return self.hops >= self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "payload": self.payload,
            "ttl": self.ttl,
            "priority": self.priority,
            "encryption": self.encryption,
            "timestamp": self.timestamp,
            "hops": self.hops,
            "route_history": self.route_history
        }


class NATTraversal:
    """NAT traversal utilities"""
    
    @staticmethod
    async def discover_public_endpoint() -> Optional[str]:
        """Discover public endpoint using STUN"""
        try:
            # Mock STUN request
            stun_server = "stun.l.google.com:19302"
            
            # In real implementation, would send STUN request
            # For now, return mock public endpoint
            return f"public.signaverse.ai:{4242}"
            
        except Exception as e:
            logger.error(f"STUN discovery failed: {e}")
            return None
    
    @staticmethod
    async def setup_port_mapping(internal_port: int, external_port: int) -> bool:
        """Setup UPnP port mapping"""
        try:
            # Mock UPnP setup
            # In real implementation, would use UPnP library
            logger.info(f"Setting up port mapping: {internal_port} -> {external_port}")
            return True
            
        except Exception as e:
            logger.error(f"UPnP setup failed: {e}")
            return False
    
    @staticmethod
    def get_local_addresses() -> List[str]:
        """Get all local network addresses"""
        addresses = []
        
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Get local IP addresses
            local_ip = socket.gethostbyname(hostname)
            addresses.append(f"{local_ip}:4242")
            
            # Add localhost
            addresses.append("localhost:4242")
            addresses.append("127.0.0.1:4242")
            
        except Exception as e:
            logger.error(f"Error getting local addresses: {e}")
        
        return addresses


class QUICConnection:
    """QUIC-based connection for better performance"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.is_connected = False
        self.reader = None
        self.writer = None
        self.connection_id = None
    
    async def connect(self, timeout: float = 10.0) -> bool:
        """Establish QUIC connection"""
        try:
            # Mock QUIC connection
            # In real implementation, would use aioquic or similar
            logger.info(f"Establishing QUIC connection to {self.endpoint}")
            
            # Simulate connection establishment
            await asyncio.sleep(0.1)  # Simulate handshake
            
            self.is_connected = True
            self.connection_id = hashlib.sha256(self.endpoint.encode()).hexdigest()[:16]
            
            logger.info(f"QUIC connection established to {self.endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"QUIC connection failed: {e}")
            return False
    
    async def send_message(self, message: NetworkMessage) -> bool:
        """Send message over QUIC"""
        if not self.is_connected:
            return False
        
        try:
            message_data = json.dumps(message.to_dict())
            
            # Mock QUIC send
            # In real implementation, would use QUIC stream
            logger.debug(f"Sending QUIC message to {self.endpoint}")
            
            return True
            
        except Exception as e:
            logger.error(f"QUIC send failed: {e}")
            return False
    
    async def receive_message(self) -> Optional[NetworkMessage]:
        """Receive message over QUIC"""
        if not self.is_connected:
            return None
        
        try:
            # Mock QUIC receive
            # In real implementation, would wait for QUIC stream data
            await asyncio.sleep(0.1)
            
            # Return mock message
            message_data = {
                "message_id": "mock_id",
                "sender": "remote_node",
                "message_type": "ping",
                "payload": {"timestamp": time.time()},
                "timestamp": time.time(),
                "hops": 0,
                "route_history": []
            }
            
            return NetworkMessage(**message_data)
            
        except Exception as e:
            logger.error(f"QUIC receive failed: {e}")
            return None
    
    async def close(self):
        """Close QUIC connection"""
        self.is_connected = False
        logger.info(f"QUIC connection closed to {self.endpoint}")


class P2PNode:
    """Advanced P2P node with QUIC and NAT traversal"""
    
    def __init__(self, node_id: str, port: int = 4242, 
                 node_type: NodeType = NodeType.CLIENT):
        self.node_id = node_id
        self.port = port
        self.node_type = node_type
        self.public_key = self._generate_key_pair()
        
        # Network state
        self.peers: Dict[str, PeerInfo] = {}
        self.connections: Dict[str, QUICConnection] = {}
        self.routing_table: Dict[str, List[str]] = {}  # destination -> list of next hops
        
        # Bootstrap and discovery
        self.bootstrap_peers: List[str] = []
        self.discovered_peers: Set[str] = set()
        self.nat_traversal = NATTraversal()
        
        # Message handling
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue = asyncio.Queue()
        
        # Network services
        self.dht_service = DHTService(node_id)
        self.relay_service = RelayService(node_id)
        self.discovery_service = DiscoveryService(node_id)
        
        # Performance metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_transferred": 0,
            "active_connections": 0,
            "peers_discovered": 0,
            "route_discoveries": 0,
            "nat_traversal_success": 0,
            "uptime": time.time()
        }
        
        # Configuration
        self.config = {
            "max_connections": 100,
            "max_message_size": 1024 * 1024,  # 1MB
            "heartbeat_interval": 30,  # seconds
            "discovery_interval": 60,  # seconds
            "routing_table_size": 1000,
            "enable_nat_traversal": True,
            "enable_relay": True,
            "enable_dht": True
        }
    
    def _generate_key_pair(self) -> str:
        """Generate key pair for the node"""
        # Mock key generation
        # In real implementation, would use cryptographic library
        return f"key_{hashlib.sha256(self.node_id.encode()).hexdigest()[:16]}"
    
    async def start(self) -> bool:
        """Start the P2P node"""
        try:
            logger.info(f"Starting P2P node {self.node_id} on port {self.port}")
            
            # Start network services
            await self._start_network_services()
            
            # Connect to bootstrap peers
            await self._connect_to_bootstrap_peers()
            
            # Start background tasks
            asyncio.create_task(self._message_processor())
            asyncio.create_task(self._connection_maintenance())
            asyncio.create_task(self._peer_discovery())
            asyncio.create_task(self._heartbeat_sender())
            asyncio.create_task(self._route_maintenance())
            
            # NAT traversal
            if self.config["enable_nat_traversal"]:
                asyncio.create_task(self._nat_traversal_worker())
            
            logger.info(f"P2P node {self.node_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start P2P node: {e}")
            return False
    
    async def stop(self):
        """Stop the P2P node"""
        logger.info(f"Stopping P2P node {self.node_id}")
        
        # Close all connections
        for connection in self.connections.values():
            await connection.close()
        
        # Stop network services
        await self.dht_service.stop()
        await self.relay_service.stop()
        await self.discovery_service.stop()
        
        logger.info(f"P2P node {self.node_id} stopped")
    
    async def _start_network_services(self):
        """Start network services"""
        await self.dht_service.start()
        await self.relay_service.start()
        await self.discovery_service.start()
    
    async def _connect_to_bootstrap_peers(self):
        """Connect to bootstrap peers"""
        for peer_endpoint in self.bootstrap_peers:
            try:
                connection = QUICConnection(peer_endpoint)
                if await connection.connect():
                    peer_id = self._extract_node_id_from_endpoint(peer_endpoint)
                    peer_info = PeerInfo(
                        node_id=peer_id,
                        endpoint=peer_endpoint,
                        node_type=NodeType.BOOTSTRAP
                    )
                    
                    self.peers[peer_id] = peer_info
                    self.connections[peer_id] = connection
                    
                    # Send handshake
                    await self._send_handshake(peer_id)
                    
                    logger.info(f"Connected to bootstrap peer {peer_id}")
                    
            except Exception as e:
                logger.error(f"Failed to connect to bootstrap {peer_endpoint}: {e}")
    
    def _extract_node_id_from_endpoint(self, endpoint: str) -> str:
        """Extract node ID from endpoint"""
        # Mock extraction
        return f"node_{hashlib.sha256(endpoint.encode()).hexdigest()[:8]}"
    
    async def _send_handshake(self, peer_id: str):
        """Send handshake to peer"""
        handshake_message = NetworkMessage(
            message_id=self._generate_message_id(),
            sender=self.node_id,
            recipient=peer_id,
            message_type="handshake",
            payload={
                "node_type": self.node_type.value,
                "capabilities": ["p2p", "relay", "dht", "quic"],
                "port": self.port,
                "public_key": self.public_key,
                "timestamp": time.time()
            }
        )
        
        await self._send_message_to_peer(peer_id, handshake_message)
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = str(time.time())
        content = f"{self.node_id}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _send_message_to_peer(self, peer_id: str, message: NetworkMessage) -> bool:
        """Send message to specific peer"""
        if peer_id not in self.connections:
            return False
        
        connection = self.connections[peer_id]
        success = await connection.send_message(message)
        
        if success:
            self.metrics["messages_sent"] += 1
            self.metrics["bytes_transferred"] += len(json.dumps(message.to_dict()))
        
        return success
    
    async def _message_processor(self):
        """Process messages from queue"""
        while True:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # Handle message
                await self._handle_message(message)
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message processor error: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: NetworkMessage):
        """Handle incoming message"""
        self.metrics["messages_received"] += 1
        
        # Check if message is expired
        if message.is_expired():
            logger.warning(f"Discarding expired message {message.message_id}")
            return
        
        # Add hop
        message.add_hop(self.node_id)
        
        # Route to destination if needed
        if message.recipient and message.recipient != self.node_id:
            await self._route_message(message)
            return
        
        # Handle local message
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
        else:
            logger.warning(f"No handler for message type: {message.message_type}")
    
    async def _route_message(self, message: NetworkMessage):
        """Route message to destination"""
        if message.recipient in self.connections:
            # Direct connection available
            await self._send_message_to_peer(message.recipient, message)
        else:
            # Use routing table
            next_hops = self.routing_table.get(message.recipient, [])
            if next_hops:
                # Send to first available next hop
                for hop in next_hops:
                    if hop in self.connections:
                        await self._send_message_to_peer(hop, message)
                        break
            else:
                # Use relay service
                await self.relay_service.relay_message(message, next_hops)
    
    async def _connection_maintenance(self):
        """Maintain connections and handle timeouts"""
        while True:
            try:
                current_time = time.time()
                timeout = 300  # 5 minutes
                
                # Check for inactive connections
                inactive_peers = []
                for peer_id, connection in self.connections.items():
                    if current_time - self.peers[peer_id].last_seen > timeout:
                        inactive_peers.append(peer_id)
                        await connection.close()
                
                # Clean up inactive connections
                for peer_id in inactive_peers:
                    if peer_id in self.connections:
                        del self.connections[peer_id]
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED
                
                self.metrics["active_connections"] = len(self.connections)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Connection maintenance error: {e}")
                await asyncio.sleep(10)
    
    async def _peer_discovery(self):
        """Discover new peers"""
        while True:
            try:
                # Use discovery service
                new_peers = await self.discovery_service.discover_peers()
                
                for peer_info in new_peers:
                    if peer_info.node_id not in self.peers:
                        self.peers[peer_info.node_id] = peer_info
                        self.discovered_peers.add(peer_info.node_id)
                        self.metrics["peers_discovered"] += 1
                        
                        # Try to connect to new peers
                        connection = QUICConnection(peer_info.endpoint)
                        if await connection.connect():
                            self.connections[peer_info.node_id] = connection
                            peer_info.connection_state = ConnectionState.CONNECTED
                            peer_info.update_connection_success(0.1)  # Mock latency
                
                await asyncio.sleep(self.config["discovery_interval"])
                
            except Exception as e:
                logger.error(f"Peer discovery error: {e}")
                await asyncio.sleep(30)
    
    async def _heartbeat_sender(self):
        """Send heartbeat to maintain connections"""
        while True:
            try:
                heartbeat_message = NetworkMessage(
                    message_id=self._generate_message_id(),
                    sender=self.node_id,
                    recipient=None,  # Broadcast
                    message_type="heartbeat",
                    payload={"timestamp": time.time()}
                )
                
                # Send to all connected peers
                for peer_id in list(self.connections.keys()):
                    await self._send_message_to_peer(peer_id, heartbeat_message)
                
                await asyncio.sleep(self.config["heartbeat_interval"])
                
            except Exception as e:
                logger.error(f"Heartbeat sender error: {e}")
                await asyncio.sleep(30)
    
    async def _route_maintenance(self):
        """Maintain routing table"""
        while True:
            try:
                # Update routing table based on peer connections
                for peer_id, peer_info in self.peers.items():
                    if peer_info.connection_state == ConnectionState.CONNECTED:
                        # Add peer as route to itself
                        if peer_id not in self.routing_table:
                            self.routing_table[peer_id] = []
                        
                        # Share routing information
                        await self._share_routing_info()
                
                # Clean up old routes
                await self._cleanup_old_routes()
                
                self.metrics["route_discoveries"] += 1
                await asyncio.sleep(120)  # Every 2 minutes
                
            except Exception as e:
                logger.error(f"Route maintenance error: {e}")
                await asyncio.sleep(30)
    
    async def _share_routing_info(self):
        """Share routing information with peers"""
        routing_info = {
            "node_id": self.node_id,
            "routes": dict(list(self.routing_table.items())[:10]),  # Share top 10 routes
            "timestamp": time.time()
        }
        
        routing_message = NetworkMessage(
            message_id=self._generate_message_id(),
            sender=self.node_id,
            recipient=None,  # Broadcast
            message_type="routing_update",
            payload=routing_info
        )
        
        # Broadcast to all peers
        for peer_id in self.connections:
            await self._send_message_to_peer(peer_id, routing_message)
    
    async def _cleanup_old_routes(self):
        """Clean up old routing entries"""
        # Simple cleanup - remove oldest entries if table is too large
        if len(self.routing_table) > self.config["routing_table_size"]:
            # Remove oldest 20% of routes
            routes_to_remove = len(self.routing_table) // 5
            sorted_routes = sorted(
                self.routing_table.items(),
                key=lambda x: len(x[1])  # Remove routes with fewest alternatives
            )
            
            for i in range(routes_to_remove):
                del self.routing_table[sorted_routes[i][0]]
    
    async def _nat_traversal_worker(self):
        """Worker for NAT traversal"""
        try:
            # Discover public endpoint
            public_endpoint = await self.nat_traversal.discover_public_endpoint()
            if public_endpoint:
                logger.info(f"Discovered public endpoint: {public_endpoint}")
                self.metrics["nat_traversal_success"] += 1
            
            # Setup port mapping
            await self.nat_traversal.setup_port_mapping(self.port, self.port)
            
        except Exception as e:
            logger.error(f"NAT traversal failed: {e}")
        
        await asyncio.sleep(300)  # Check every 5 minutes
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type}")
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        uptime = time.time() - self.metrics["uptime"]
        
        return {
            **self.metrics,
            "uptime": uptime,
            "total_peers": len(self.peers),
            "connected_peers": len(self.connections),
            "routing_table_size": len(self.routing_table),
            "discovered_peers": len(self.discovered_peers),
            "config": self.config
        }


class DHTService:
    """Distributed Hash Table service"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.dht_storage: Dict[str, Any] = {}
        self.is_running = False
    
    async def start(self):
        """Start DHT service"""
        self.is_running = True
        logger.info(f"DHT service started for node {self.node_id}")
    
    async def stop(self):
        """Stop DHT service"""
        self.is_running = False
        logger.info(f"DHT service stopped for node {self.node_id}")
    
    async def store(self, key: str, value: Any) -> bool:
        """Store key-value pair in DHT"""
        self.dht_storage[key] = value
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from DHT"""
        return self.dht_storage.get(key)


class RelayService:
    """Relay service for message forwarding"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.relayed_messages: Dict[str, int] = {}
        self.is_running = False
    
    async def start(self):
        """Start relay service"""
        self.is_running = True
        logger.info(f"Relay service started for node {self.node_id}")
    
    async def stop(self):
        """Stop relay service"""
        self.is_running = False
        logger.info(f"Relay service stopped for node {self.node_id}")
    
    async def relay_message(self, message: NetworkMessage, target_peers: List[str]) -> bool:
        """Relay message to target peers"""
        for peer_id in target_peers:
            # Mock relay
            self.relayed_messages[message.message_id] = self.relayed_messages.get(message.message_id, 0) + 1
            logger.debug(f"Relaying message {message.message_id} to {peer_id}")
        
        return True


class DiscoveryService:
    """Peer discovery service"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.discovered_peers: List[PeerInfo] = []
        self.is_running = False
    
    async def start(self):
        """Start discovery service"""
        self.is_running = True
        logger.info(f"Discovery service started for node {self.node_id}")
    
    async def stop(self):
        """Stop discovery service"""
        self.is_running = False
        logger.info(f"Discovery service stopped for node {self.node_id}")
    
    async def discover_peers(self) -> List[PeerInfo]:
        """Discover new peers"""
        # Mock discovery
        new_peers = []
        
        # Simulate discovering some peers
        for i in range(3):
            peer = PeerInfo(
                node_id=f"discovered_{i}",
                endpoint=f"192.168.1.{100+i}:4242",
                node_type=NodeType.CLIENT,
                capabilities=["p2p", "quic"]
            )
            new_peers.append(peer)
        
        self.discovered_peers.extend(new_peers)
        return new_peers
