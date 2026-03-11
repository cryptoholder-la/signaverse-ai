"""
P2P Networking Layer
Handles peer discovery, WebRTC connections, and distributed communication
Inspired by Freenet, libp2p, and WebRTC implementations
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import websockets
import aiohttp

logger = logging.getLogger(__name__)


class PeerStatus(Enum):
    """Peer connection status"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class PeerInfo:
    """Information about a network peer"""
    peer_id: str
    endpoint: str
    status: PeerStatus
    last_seen: float
    capabilities: List[str]
    reputation: float = 50.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NetworkMessage:
    """Message sent between peers"""
    message_id: str
    sender: str
    recipient: Optional[str]  # None for broadcast
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    ttl: int = 3  # Time to live in hops
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        return cls(**data)


class P2PNetwork:
    """P2P network implementation with WebRTC and libp2p-like functionality"""
    
    def __init__(self, local_peer_id: str, bootstrap_peers: List[str] = None):
        self.local_peer_id = local_peer_id
        self.bootstrap_peers = bootstrap_peers or []
        
        # Peer management
        self.peers: Dict[str, PeerInfo] = {}
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.connection_handlers: Dict[str, Callable] = {}
        
        # Message handling
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue = asyncio.Queue()
        
        # Network state
        self.is_running = False
        self.discovered_peers: Set[str] = set()
        self.network_stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_transferred": 0,
            "active_connections": 0
        }
        
        # WebRTC signaling
        self.signaling_server = None
        self.webrtc_connections: Dict[str, Any] = {}
        
        # DHT-like functionality
        self.dht_storage: Dict[str, Any] = {}
        self.dht_replicas: Dict[str, Set[str]] = {}  # key -> set of peer IDs
        
        # Register default handlers
        self._register_default_handlers()
    
    async def start(self, port: int = 8765):
        """Start the P2P network node"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"Starting P2P network node {self.local_peer_id} on port {port}")
        
        # Start WebSocket server for signaling
        self.signaling_server = await websockets.serve(
            self._handle_websocket_connection,
            "0.0.0.0",
            port
        )
        
        # Start background tasks
        asyncio.create_task(self._message_processor())
        asyncio.create_task(self._peer_discovery())
        asyncio.create_task(self._connection_maintenance())
        asyncio.create_task(self._dht_replication())
        
        # Connect to bootstrap peers
        await self._connect_to_bootstrap_peers()
        
        logger.info("P2P network node started successfully")
    
    async def stop(self):
        """Stop the P2P network node"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Close all connections
        for peer_id, connection in self.active_connections.items():
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing connection to {peer_id}: {e}")
        
        # Close signaling server
        if self.signaling_server:
            self.signaling_server.close()
            await self.signaling_server.wait_closed()
        
        logger.info("P2P network node stopped")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def register_connection_handler(self, event: str, handler: Callable):
        """Register handler for connection events"""
        self.connection_handlers[event] = handler
    
    async def send_message(self, recipient: str, message_type: str, 
                        payload: Dict[str, Any], broadcast: bool = False) -> bool:
        """Send message to peer or broadcast to all"""
        message = NetworkMessage(
            message_id=self._generate_message_id(),
            sender=self.local_peer_id,
            recipient=None if broadcast else recipient,
            message_type=message_type,
            payload=payload,
            timestamp=time.time()
        )
        
        if broadcast:
            return await self._broadcast_message(message)
        else:
            return await self._send_to_peer(recipient, message)
    
    async def _send_to_peer(self, peer_id: str, message: NetworkMessage) -> bool:
        """Send message to specific peer"""
        if peer_id not in self.active_connections:
            logger.warning(f"No active connection to peer {peer_id}")
            return False
        
        try:
            connection = self.active_connections[peer_id]
            await connection.send(json.dumps(message.to_dict()))
            
            self.network_stats["messages_sent"] += 1
            self.network_stats["bytes_transferred"] += len(json.dumps(message.to_dict()))
            
            return True
        except Exception as e:
            logger.error(f"Error sending message to {peer_id}: {e}")
            await self._handle_connection_error(peer_id, e)
            return False
    
    async def _broadcast_message(self, message: NetworkMessage) -> bool:
        """Broadcast message to all connected peers"""
        success_count = 0
        
        for peer_id in list(self.active_connections.keys()):
            if await self._send_to_peer(peer_id, message):
                success_count += 1
        
        return success_count > 0
    
    async def _handle_websocket_connection(self, websocket, path):
        """Handle incoming WebSocket connection"""
        peer_id = None
        
        try:
            # Wait for handshake
            handshake = await websocket.recv()
            handshake_data = json.loads(handshake)
            
            peer_id = handshake_data.get("peer_id")
            if not peer_id:
                await websocket.close(1008, "Missing peer_id in handshake")
                return
            
            # Add connection
            self.active_connections[peer_id] = websocket
            
            # Update peer info
            if peer_id in self.peers:
                self.peers[peer_id].status = PeerStatus.CONNECTED
                self.peers[peer_id].last_seen = time.time()
            else:
                self.peers[peer_id] = PeerInfo(
                    peer_id=peer_id,
                    endpoint=str(websocket.remote_address),
                    status=PeerStatus.CONNECTED,
                    last_seen=time.time(),
                    capabilities=handshake_data.get("capabilities", [])
                )
            
            self.network_stats["active_connections"] = len(self.active_connections)
            
            # Send acknowledgment
            await websocket.send(json.dumps({
                "type": "handshake_ack",
                "peer_id": self.local_peer_id,
                "capabilities": ["sign_video", "translation", "annotation"]
            }))
            
            # Notify handlers
            if "peer_connected" in self.connection_handlers:
                await self.connection_handlers["peer_connected"](peer_id)
            
            # Handle messages
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    network_message = NetworkMessage.from_dict(message_data)
                    await self.message_queue.put(network_message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from {peer_id}")
                except Exception as e:
                    logger.error(f"Error processing message from {peer_id}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Peer {peer_id} disconnected")
        except Exception as e:
            logger.error(f"Error in connection with {peer_id}: {e}")
        finally:
            # Cleanup
            if peer_id and peer_id in self.active_connections:
                del self.active_connections[peer_id]
            
            if peer_id and peer_id in self.peers:
                self.peers[peer_id].status = PeerStatus.DISCONNECTED
            
            self.network_stats["active_connections"] = len(self.active_connections)
            
            # Notify handlers
            if peer_id and "peer_disconnected" in self.connection_handlers:
                await self.connection_handlers["peer_disconnected"](peer_id)
    
    async def _connect_to_peer(self, endpoint: str) -> bool:
        """Connect to a peer endpoint"""
        try:
            async with websockets.connect(endpoint) as websocket:
                # Send handshake
                handshake = {
                    "peer_id": self.local_peer_id,
                    "capabilities": ["sign_video", "translation", "annotation"]
                }
                await websocket.send(json.dumps(handshake))
                
                # Wait for acknowledgment
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "handshake_ack":
                    peer_id = response_data["peer_id"]
                    
                    # Store peer info
                    self.peers[peer_id] = PeerInfo(
                        peer_id=peer_id,
                        endpoint=endpoint,
                        status=PeerStatus.CONNECTED,
                        last_seen=time.time(),
                        capabilities=response_data.get("capabilities", [])
                    )
                    
                    logger.info(f"Connected to peer {peer_id} at {endpoint}")
                    return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {endpoint}: {e}")
            return False
        
        return False
    
    async def _connect_to_bootstrap_peers(self):
        """Connect to bootstrap peers"""
        for peer_endpoint in self.bootstrap_peers:
            await self._connect_to_peer(peer_endpoint)
            await asyncio.sleep(1)  # Small delay between connections
    
    async def _peer_discovery(self):
        """Discover new peers through various methods"""
        while self.is_running:
            try:
                # LAN discovery (simplified mDNS-like)
                await self._discover_lan_peers()
                
                # DHT peer exchange
                await self._exchange_peer_lists()
                
                await asyncio.sleep(30)  # Discovery interval
            except Exception as e:
                logger.error(f"Peer discovery error: {e}")
                await asyncio.sleep(5)
    
    async def _discover_lan_peers(self):
        """Discover peers on local network"""
        # Simplified LAN discovery - in real implementation would use mDNS
        lan_ports = [8765, 8766, 8767, 8768, 8769]
        
        for port in lan_ports:
            if port == 8765:  # Skip our own port
                continue
            
            endpoint = f"ws://localhost:{port}"
            await self._connect_to_peer(endpoint)
    
    async def _exchange_peer_lists(self):
        """Exchange peer lists with connected peers"""
        if not self.active_connections:
            return
        
        # Send our peer list
        peer_list = {
            "peers": [
                {
                    "peer_id": peer_id,
                    "endpoint": peer.endpoint,
                    "capabilities": peer.capabilities
                }
                for peer_id, peer in self.peers.items()
                if peer_id != self.local_peer_id
            ]
        }
        
        await self.send_message(None, "peer_exchange", peer_list, broadcast=True)
    
    async def _connection_maintenance(self):
        """Maintain connections and handle timeouts"""
        while self.is_running:
            try:
                current_time = time.time()
                timeout = 300  # 5 minutes
                
                # Check for inactive peers
                for peer_id, peer in list(self.peers.items()):
                    if current_time - peer.last_seen > timeout:
                        if peer_id in self.active_connections:
                            await self.active_connections[peer_id].close()
                        peer.status = PeerStatus.DISCONNECTED
                
                # Reconnect to disconnected important peers
                for peer_id, peer in self.peers.items():
                    if (peer.status == PeerStatus.DISCONNECTED and 
                        peer.reputation > 70 and  # Only reconnect to high-reputation peers
                        peer_id not in self.active_connections):
                        await self._connect_to_peer(peer.endpoint)
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Connection maintenance error: {e}")
                await asyncio.sleep(10)
    
    async def _message_processor(self):
        """Process messages from queue"""
        while self.is_running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                # Update stats
                self.network_stats["messages_received"] += 1
                
                # Handle message based on type
                handler = self.message_handlers.get(message.message_type)
                if handler:
                    await handler(message)
                else:
                    logger.warning(f"No handler for message type: {message.message_type}")
                
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
    
    async def _dht_replication(self):
        """Replicate DHT data to peers"""
        while self.is_running:
            try:
                # Replicate stored data to random peers
                if self.dht_storage and self.active_connections:
                    # Select random subset of peers
                    peer_ids = list(self.active_connections.keys())
                    if len(peer_ids) > 3:
                        import random
                        sample_peers = random.sample(peer_ids, min(3, len(peer_ids)))
                        
                        for key, value in list(self.dht_storage.items())[-10:]:  # Last 10 items
                            for peer_id in sample_peers:
                                await self.send_message(
                                    peer_id, 
                                    "dht_store", 
                                    {"key": key, "value": value}
                                )
                
                await asyncio.sleep(300)  # Replicate every 5 minutes
            except Exception as e:
                logger.error(f"DHT replication error: {e}")
                await asyncio.sleep(30)
    
    async def _handle_connection_error(self, peer_id: str, error: Exception):
        """Handle connection error"""
        if peer_id in self.peers:
            self.peers[peer_id].status = PeerStatus.ERROR
        
        if peer_id in self.active_connections:
            del self.active_connections[peer_id]
        
        self.network_stats["active_connections"] = len(self.active_connections)
        
        # Notify handlers
        if "peer_error" in self.connection_handlers:
            await self.connection_handlers["peer_error"](peer_id, error)
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_message_handler("peer_exchange", self._handle_peer_exchange)
        self.register_message_handler("dht_store", self._handle_dht_store)
        self.register_message_handler("dht_get", self._handle_dht_get)
        self.register_message_handler("ping", self._handle_ping)
        self.register_message_handler("pong", self._handle_pong)
    
    async def _handle_peer_exchange(self, message: NetworkMessage):
        """Handle peer list exchange"""
        peer_data = message.payload.get("peers", [])
        
        for peer_info in peer_data:
            peer_id = peer_info["peer_id"]
            
            if peer_id != self.local_peer_id and peer_id not in self.peers:
                # Try to connect to new peer
                await self._connect_to_peer(peer_info["endpoint"])
    
    async def _handle_dht_store(self, message: NetworkMessage):
        """Handle DHT store operation"""
        key = message.payload["key"]
        value = message.payload["value"]
        
        # Store locally
        self.dht_storage[key] = value
        
        # Track replication
        if key not in self.dht_replicas:
            self.dht_replicas[key] = set()
        self.dht_replicas[key].add(message.sender)
        
        logger.debug(f"Stored DHT key {key} from {message.sender}")
    
    async def _handle_dht_get(self, message: NetworkMessage):
        """Handle DHT get operation"""
        key = message.payload["key"]
        
        if key in self.dht_storage:
            # Send back the value
            await self.send_message(
                message.sender,
                "dht_response",
                {
                    "key": key,
                    "value": self.dht_storage[key],
                    "request_id": message.payload.get("request_id")
                }
            )
    
    async def _handle_ping(self, message: NetworkMessage):
        """Handle ping message"""
        await self.send_message(
            message.sender,
            "pong",
            {
                "timestamp": time.time(),
                "original_timestamp": message.payload.get("timestamp")
            }
        )
    
    async def _handle_pong(self, message: NetworkMessage):
        """Handle pong response"""
        if message.sender in self.peers:
            self.peers[message.sender].last_seen = time.time()
            
            # Calculate round-trip time
            original_timestamp = message.payload.get("original_timestamp")
            if original_timestamp:
                rtt = time.time() - original_timestamp
                logger.debug(f"RTT to {message.sender}: {rtt:.3f}s")
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = str(time.time())
        return hashlib.sha256(f"{self.local_peer_id}_{timestamp}".encode()).hexdigest()[:16]
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        return {
            **self.network_stats,
            "total_peers": len(self.peers),
            "connected_peers": len(self.active_connections),
            "dht_entries": len(self.dht_storage),
            "is_running": self.is_running
        }
    
    def get_peer_list(self) -> List[PeerInfo]:
        """Get list of all known peers"""
        return list(self.peers.values())
    
    async def store_dht_value(self, key: str, value: Any) -> bool:
        """Store value in DHT"""
        try:
            self.dht_storage[key] = value
            
            # Replicate to connected peers
            if self.active_connections:
                await self.send_message(
                    None,
                    "dht_store",
                    {"key": key, "value": value},
                    broadcast=True
                )
            
            return True
        except Exception as e:
            logger.error(f"Error storing DHT value: {e}")
            return False
    
    async def get_dht_value(self, key: str) -> Optional[Any]:
        """Get value from DHT"""
        # Check local storage first
        if key in self.dht_storage:
            return self.dht_storage[key]
        
        # Request from peers
        request_id = self._generate_message_id()
        await self.send_message(
            None,
            "dht_get",
            {"key": key, "request_id": request_id},
            broadcast=True
        )
        
        # In real implementation, would wait for response
        # For now, return None
        return None
