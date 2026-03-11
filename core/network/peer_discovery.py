"""
Peer Discovery + NAT Traversal
Advanced peer discovery with STUN, UPnP, and mDNS support
"""

import asyncio
import socket
import json
import time
import hashlib
import struct
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DiscoveryMethod(Enum):
    """Methods for peer discovery"""
    STUN = "stun"
    UPNP = "upnp"
    MDNS = "mdns"
    BOOTSTRAP = "bootstrap"
    DIRECT = "direct"
    RELAY = "relay"


class NATType(Enum):
    """Types of NAT traversal"""
    NONE = "none"
    FULL_CONE = "full_cone"
    RESTRICTED = "restricted"
    PORT_RESTRICTED = "port_restricted"
    SYMMETRIC = "symmetric"


@dataclass
class PeerEndpoint:
    """Represents a peer endpoint"""
    def __init__(self, address: str, port: int, node_id: str = None,
                 capabilities: List[str] = None, last_seen: float = 0.0,
                 latency: float = 0.0, is_direct: bool = False):
        self.address = address
        self.port = port
        self.node_id = node_id
        self.capabilities = capabilities or []
        self.last_seen = last_seen
        self.latency = latency
        self.is_direct = is_direct
        self.endpoint = f"{address}:{port}"
        self.reputation = 50.0
        self.connection_attempts = 0
        self.successful_connections = 0
    
    def update_latency(self, latency: float):
        """Update latency measurement"""
        self.latency = (self.latency * 0.8) + (latency * 0.2)
        self.last_seen = time.time()
    
    def update_reputation(self, success: bool):
        """Update peer reputation"""
        self.connection_attempts += 1
        
        if success:
            self.successful_connections += 1
            self.reputation = min(100, self.reputation + 2)
        else:
            self.reputation = max(0, self.reputation - 5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class NATInfo:
    """Information about NAT configuration"""
    def __init__(self):
        self.nat_type = NATType.NONE
        self.external_ip = None
        self.external_port = None
        self.internal_ip = None
        self.internal_port = None
        self.upnp_available = False
        self.stun_available = False
        self.public_endpoint = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class STUNClient:
    """STUN client for NAT discovery"""
    
    def __init__(self):
        self.stun_servers = [
            "stun.l.google.com:19302",
            "stun1.l.google.com:19302",
            "stun2.l.google.com:19302",
            "stun.stunprotocol.org:3478",
            "stun.ekiga.net:3478"
        ]
        self.timeout = 5.0
    
    async def discover_public_endpoint(self, local_port: int) -> Optional[PeerEndpoint]:
        """Discover public endpoint using STUN"""
        for stun_server in self.stun_servers:
            try:
                endpoint = await self._stun_request(stun_server, local_port)
                if endpoint:
                    logger.info(f"STUN discovered public endpoint via {stun_server}: {endpoint.endpoint}")
                    return endpoint
            except Exception as e:
                logger.warning(f"STUN request to {stun_server} failed: {e}")
                continue
        
        logger.warning("All STUN servers failed")
        return None
    
    async def _stun_request(self, stun_server: str, local_port: int) -> Optional[PeerEndpoint]:
        """Make STUN request to discover public endpoint"""
        try:
            # Parse STUN server address
            server_host, server_port = stun_server.split(':')
            server_port = int(server_port)
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Bind to local port
            sock.bind(('', local_port))
            
            # STUN binding request
            transaction_id = int(time.time() * 1000) % 65536
            
            # STUN message format (simplified)
            # Message Type: 0x0001 (Binding Request)
            # Message Length: 0x0000 (no additional attributes)
            # Magic Cookie: 0x2112A442 (STUN magic cookie)
            # Transaction ID: 16 bytes
            stun_message = bytearray()
            stun_message.extend([0x00, 0x01])  # Message Type and Length
            stun_message.extend([0x21, 0x12, 0xA4, 0x42])  # Magic Cookie
            stun_message.extend(struct.pack('>H', transaction_id))  # Transaction ID
            stun_message.extend([0x00, 0x00])  # Address family and port
            
            # Send STUN request
            sock.sendto(bytes(stun_message), (server_host, server_port))
            
            # Wait for response
            try:
                data, addr = sock.recvfrom(1024)
                
                if len(data) >= 20:  # Minimum STUN response size
                    # Parse STUN response
                    response = self._parse_stun_response(data)
                    
                    if response and response.get('mapped_address'):
                        mapped_ip, mapped_port = response['mapped_address']
                        
                        # Test connectivity
                        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        test_socket.bind(('', local_port))
                        
                        # Send test packet
                        test_socket.sendto(b'test', (mapped_ip, mapped_port))
                        
                        # Clean up
                        test_socket.close()
                        
                        return PeerEndpoint(
                            address=mapped_ip,
                            port=mapped_port,
                            is_direct=True
                        )
                
            except socket.timeout:
                logger.warning(f"STUN request to {stun_server} timed out")
            
            sock.close()
            
        except Exception as e:
            logger.error(f"STUN request failed: {e}")
        
        return None
    
    def _parse_stun_response(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse STUN response"""
        try:
            if len(data) < 20:
                return None
            
            # Check magic cookie
            if data[4:8] != b'\x21\x12\xa4\x42':
                return None
            
            # Get message type (should be 0x0101 for binding response)
            message_type = struct.unpack('>H', data[0:2])[0]
            
            if message_type != 0x0101:
                return None
            
            # Parse XOR-MAPPED-ADDRESS attribute
            # This is a simplified parser
            offset = 20
            
            while offset < len(data):
                if offset + 4 > len(data):
                    break
                
                # Attribute type
                attr_type = struct.unpack('>H', data[offset:offset+2])[0]
                attr_length = struct.unpack('>H', data[offset+2:offset+4])[0]
                
                if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
                    if attr_length >= 8 and offset + 8 <= len(data):
                        # Parse mapped address
                        family = data[offset+4]
                        port = struct.unpack('>H', data[offset+6:offset+8])[0]
                        
                        if family == 0x01:  # IPv4
                            if offset + 8 + 4 <= len(data):
                                ip_bytes = data[offset+8:offset+12]
                                ip = '.'.join(str(b) for b in ip_bytes)
                                
                                return {
                                    'mapped_address': (ip, port),
                                    'family': family,
                                    'attr_type': attr_type
                                }
                
                offset += 4 + attr_length
            
        except Exception as e:
            logger.error(f"Failed to parse STUN response: {e}")
            return None


class UPnPClient:
    """UPnP client for port mapping"""
    
    def __init__(self):
        self.timeout = 10.0
        self.upnp_devices = []
    
    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover UPnP devices"""
        try:
            # Create SSDP discovery message
            ssdp_request = (
                'M-SEARCH * HTTP/1.1\r\n'
                'HOST: 239.255.255.250:1900\r\n'
                'MAN: "ssdp:discover"\r\n'
                'MX: 3\r\n'
                'ST: upnp:rootdevice\r\n'
                '\r\n'
            ).encode()
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Send discovery request
            sock.sendto(ssdp_request, ('239.255.255.250', 1900))
            
            # Wait for responses
            devices = []
            start_time = time.time()
            
            while time.time() - start_time < 5.0:
                try:
                    data, addr = sock.recvfrom(2048)
                    response = data.decode('utf-8', errors='ignore')
                    
                    if 'upnp:rootdevice' in response:
                        device = self._parse_upnp_response(response, addr[0])
                        if device:
                            devices.append(device)
                
                except socket.timeout:
                    break
            
            sock.close()
            return devices
            
        except Exception as e:
            logger.error(f"UPnP discovery failed: {e}")
            return []
    
    def _parse_upnp_response(self, response: str, addr: str) -> Optional[Dict[str, Any]]:
        """Parse UPnP device response"""
        try:
            # Extract location URL
            lines = response.split('\r\n')
            location = None
            
            for line in lines:
                if line.startswith('LOCATION:'):
                    location = line.split(':', 1)[1].strip()
                    break
            
            if not location:
                return None
            
            # Extract device information
            return {
                'location': location,
                'address': addr,
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Failed to parse UPnP response: {e}")
            return None
    
    async def setup_port_mapping(self, internal_port: int, external_port: int) -> bool:
        """Setup UPnP port mapping"""
        try:
            # Discover UPnP devices
            devices = await self.discover_devices()
            
            if not devices:
                logger.warning("No UPnP devices found")
                return False
            
            # Try to setup port mapping on each device
            for device in devices:
                success = await self._add_port_mapping(device, internal_port, external_port)
                if success:
                    logger.info(f"UPnP port mapping successful: {internal_port} -> {external_port}")
                    return True
            
            logger.warning("Failed to setup UPnP port mapping on all devices")
            return False
            
        except Exception as e:
            logger.error(f"UPnP port mapping failed: {e}")
            return False
    
    async def _add_port_mapping(self, device: Dict[str, Any], internal_port: int, 
                            external_port: int) -> bool:
        """Add port mapping to UPnP device"""
        try:
            # Get control URL
            location = device.get('location')
            if not location:
                return False
            
            # Extract base URL
            base_url = location.rsplit('/', 1)[0]
            
            # Get control URL
            control_url = f"{base_url}/control"
            
            # Create SOAP request for port mapping
            soap_request = self._create_port_mapping_request(internal_port, external_port)
            
            # Send SOAP request
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(control_url, data=soap_request, headers={
                    'Content-Type': 'text/xml; charset="utf-8"',
                    'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#AddPortMapping"'
                }) as response:
                    if response.status == 200:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"UPnP port mapping request failed: {e}")
            return False
    
    def _create_port_mapping_request(self, internal_port: int, external_port: int) -> str:
        """Create SOAP request for port mapping"""
        return f'''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
      <NewRemoteHost></NewRemoteHost>
      <NewExternalPort>{external_port}</NewExternalPort>
      <NewProtocol>TCP</NewProtocol>
      <NewInternalPort>{internal_port}</NewInternalPort>
      <NewLeaseDuration>3600</NewLeaseDuration>
    </u:AddPortMapping>
  </s:Body>
</s:Envelope>'''


class mDNSClient:
    """mDNS client for local peer discovery"""
    
    def __init__(self):
        self.service_name = "_signaverse._tcp.local"
        self.discovered_peers: Set[str] = set()
        self.is_running = False
    
    async def start_discovery(self) -> bool:
        """Start mDNS discovery"""
        try:
            self.is_running = True
            
            # Create mDNS responder
            import socket
            
            # Create UDP socket for mDNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', 5353))
            
            # Join multicast group
            mcast_group = ('224.0.0.251', 5353)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, 
                         socket.inet_aton(mcast_group[0]) + socket.inet_aton('224.0.0.251'))
            
            # Start discovery loop
            asyncio.create_task(self._discovery_loop(sock))
            
            logger.info("mDNS discovery started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start mDNS discovery: {e}")
            return False
    
    async def _discovery_loop(self, sock: socket.socket):
        """mDNS discovery loop"""
        while self.is_running:
            try:
                # Listen for mDNS responses
                data, addr = sock.recvfrom(1024)
                
                # Parse mDNS response
                peer = self._parse_mdns_response(data, addr[0])
                if peer:
                    self.discovered_peers.add(peer.endpoint)
                    logger.info(f"mDNS discovered peer: {peer.endpoint}")
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"mDNS discovery error: {e}")
                await asyncio.sleep(1)
    
    def _parse_mdns_response(self, data: bytes, addr: str) -> Optional[PeerEndpoint]:
        """Parse mDNS response"""
        try:
            # Simplified mDNS parsing
            response = data.decode('utf-8', errors='ignore')
            
            if self.service_name in response:
                # Extract service information
                # This is a simplified parser
                # In real implementation, would properly parse DNS records
                
                # Extract port from response
                lines = response.split('\n')
                port = 4242  # Default port
                
                for line in lines:
                    if 'port=' in line.lower():
                        port = int(line.split('=')[1].strip())
                        break
                
                return PeerEndpoint(
                    address=addr,
                    port=port,
                    is_direct=True
                )
            
        except Exception as e:
            logger.error(f"Failed to parse mDNS response: {e}")
            return None
    
    def stop_discovery(self):
        """Stop mDNS discovery"""
        self.is_running = False
        logger.info("mDNS discovery stopped")


class PeerDiscovery:
    """Advanced peer discovery with multiple methods"""
    
    def __init__(self, node_id: str, port: int = 4242):
        self.node_id = node_id
        self.port = port
        self.local_ip = self._get_local_ip()
        self.nat_info = NATInfo()
        
        # Discovery clients
        self.stun_client = STUNClient()
        self.upnp_client = UPnPClient()
        self.mdns_client = mDNSClient()
        
        # Discovered peers
        self.discovered_peers: Dict[str, PeerEndpoint] = {}
        self.bootstrap_peers: List[str] = []
        
        # Configuration
        self.config = {
            "discovery_interval": 60,  # seconds
            "max_peers": 100,
            "enable_stun": True,
            "enable_upnp": True,
            "enable_mdns": True,
            "enable_bootstrap": True,
            "peer_timeout": 300,  # seconds
            "connection_timeout": 10  # seconds
        }
        
        # Background tasks
        self.is_running = False
        self.discovery_tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.on_peer_discovered = None
        self.on_peer_lost = None
        self.on_nat_discovered = None
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Connect to external service to get local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def set_bootstrap_peers(self, peers: List[str]):
        """Set bootstrap peers"""
        self.bootstrap_peers = peers
        logger.info(f"Set {len(peers)} bootstrap peers")
    
    def set_peer_discovered_callback(self, callback):
        """Set callback for peer discovery"""
        self.on_peer_discovered = callback
    
    def set_peer_lost_callback(self, callback):
        """Set callback for peer lost"""
        self.on_peer_lost = callback
    
    def set_nat_discovered_callback(self, callback):
        """Set callback for NAT discovery"""
        self.on_nat_discovered = callback
    
    async def start(self) -> bool:
        """Start peer discovery"""
        try:
            logger.info(f"Starting peer discovery for node {self.node_id}")
            
            self.is_running = True
            
            # Start NAT discovery
            nat_task = asyncio.create_task(self._discover_nat())
            
            # Start discovery methods
            discovery_tasks = []
            
            if self.config["enable_stun"]:
                discovery_tasks.append(asyncio.create_task(self._stun_discovery()))
            
            if self.config["enable_upnp"]:
                discovery_tasks.append(asyncio.create_task(self._upnp_discovery()))
            
            if self.config["enable_mdns"]:
                discovery_tasks.append(asyncio.create_task(self._mdns_discovery()))
            
            if self.config["enable_bootstrap"]:
                discovery_tasks.append(asyncio.create_task(self._bootstrap_discovery()))
            
            self.discovery_tasks = discovery_tasks + [nat_task]
            
            # Start peer monitoring
            self.discovery_tasks.append(asyncio.create_task(self._peer_monitoring()))
            
            logger.info("Peer discovery started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start peer discovery: {e}")
            return False
    
    async def stop(self):
        """Stop peer discovery"""
        self.is_running = False
        
        # Cancel all tasks
        for task in self.discovery_tasks:
            task.cancel()
        
        self.discovery_tasks.clear()
        
        # Stop mDNS client
        self.mdns_client.stop_discovery()
        
        logger.info("Peer discovery stopped")
    
    async def _discover_nat(self):
        """Discover NAT configuration"""
        try:
            # Test connectivity
            nat_type = await self._test_nat_type()
            self.nat_info.nat_type = nat_type
            
            # Try STUN if available
            if self.config["enable_stun"] and nat_type != NATType.NONE:
                endpoint = await self.stun_client.discover_public_endpoint(self.port)
                if endpoint:
                    self.nat_info.external_ip = endpoint.address
                    self.nat_info.external_port = endpoint.port
                    self.nat_info.public_endpoint = endpoint
                    self.nat_info.stun_available = True
            
            # Try UPnP if available
            if self.config["enable_upnp"]:
                upnp_success = await self.upnp_client.setup_port_mapping(
                    self.port, self.port
                )
                if upnp_success:
                    self.nat_info.upnp_available = True
                    self.nat_info.external_ip = self.local_ip
                    self.nat_info.external_port = self.port
                    self.nat_info.public_endpoint = PeerEndpoint(
                        address=self.local_ip,
                        port=self.port,
                        is_direct=False
                    )
            
            # Notify NAT discovery
            if self.on_nat_discovered:
                await self.on_nat_discovered(self.nat_info)
            
            logger.info(f"NAT discovery complete: {self.nat_info.to_dict()}")
            
        except Exception as e:
            logger.error(f"NAT discovery failed: {e}")
    
    async def _test_nat_type(self) -> NATType:
        """Test NAT type"""
        try:
            # Create test sockets
            test_socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind to local port
            test_socket1.bind(('', self.port))
            test_socket2.bind(('', self.port + 1))
            
            # Try to connect to external address
            try:
                test_socket1.connect(("8.8.8.8", 80))
                test_socket2.connect(("8.8.8.8", 80))
                
                # If both succeed, likely no NAT or symmetric NAT
                test_socket1.close()
                test_socket2.close()
                return NATType.SYMMETRIC
                
            except Exception:
                # If connection fails, likely NAT
                test_socket1.close()
                test_socket2.close()
                return NATType.FULL_CONE
                
        except Exception as e:
            logger.error(f"NAT type test failed: {e}")
            return NATType.NONE
    
    async def _stun_discovery(self):
        """STUN-based discovery"""
        while self.is_running:
            try:
                endpoint = await self.stun_client.discover_public_endpoint(self.port)
                
                if endpoint and endpoint.endpoint not in self.discovered_peers:
                    self.discovered_peers[endpoint.endpoint] = endpoint
                    
                    if self.on_peer_discovered:
                        await self.on_peer_discovered(endpoint)
                
                await asyncio.sleep(self.config["discovery_interval"])
                
            except Exception as e:
                logger.error(f"STUN discovery error: {e}")
                await asyncio.sleep(10)
    
    async def _upnp_discovery(self):
        """UPnP-based discovery"""
        while self.is_running:
            try:
                devices = await self.upnp_client.discover_devices()
                
                for device in devices:
                    address = device.get('address')
                    if address and address not in self.discovered_peers:
                        endpoint = PeerEndpoint(
                            address=address,
                            port=self.port,
                            is_direct=False
                        )
                        
                        self.discovered_peers[address] = endpoint
                        
                        if self.on_peer_discovered:
                            await self.on_peer_discovered(endpoint)
                
                await asyncio.sleep(self.config["discovery_interval"])
                
            except Exception as e:
                logger.error(f"UPnP discovery error: {e}")
                await asyncio.sleep(10)
    
    async def _mdns_discovery(self):
        """mDNS-based discovery"""
        await self.mdns_client.start_discovery()
        
        # Monitor discovered peers
        while self.is_running:
            await asyncio.sleep(5)
            
            # Check for new peers
            for peer_endpoint in list(self.mdns_client.discovered_peers):
                if peer_endpoint not in self.discovered_peers:
                    self.discovered_peers[peer_endpoint] = PeerEndpoint(
                        address=peer_endpoint,
                        port=self.port,
                        is_direct=True
                    )
                    
                    if self.on_peer_discovered:
                        await self.on_peer_discovered(self.discovered_peers[peer_endpoint])
    
    async def _bootstrap_discovery(self):
        """Bootstrap-based discovery"""
        while self.is_running:
            try:
                for bootstrap_peer in self.bootstrap_peers:
                    # Try to connect to bootstrap peer
                    success = await self._test_peer_connectivity(bootstrap_peer)
                    
                    if success and bootstrap_peer not in self.discovered_peers:
                        endpoint = PeerEndpoint(
                            address=bootstrap_peer.split(':')[0],
                            port=int(bootstrap_peer.split(':')[1]),
                            is_direct=False
                        )
                        
                        self.discovered_peers[bootstrap_peer] = endpoint
                        
                        if self.on_peer_discovered:
                            await self.on_peer_discovered(endpoint)
                
                await asyncio.sleep(self.config["discovery_interval"])
                
            except Exception as e:
                logger.error(f"Bootstrap discovery error: {e}")
                await asyncio.sleep(10)
    
    async def _test_peer_connectivity(self, peer_endpoint: str) -> bool:
        """Test connectivity to a peer"""
        try:
            # Create test socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config["connection_timeout"])
            
            # Try to connect
            sock.connect((peer_endpoint.split(':')[0], int(peer_endpoint.split(':')[1])))
            
            # Send test message
            sock.send(b'ping')
            
            # Wait for response
            response = sock.recv(1024)
            
            sock.close()
            return response == b'pong'
            
        except Exception:
            return False
    
    async def _peer_monitoring(self):
        """Monitor discovered peers for connectivity"""
        while self.is_running:
            try:
                current_time = time.time()
                peers_to_remove = []
                
                # Check peer connectivity
                for endpoint, peer in list(self.discovered_peers.items()):
                    if current_time - peer.last_seen > self.config["peer_timeout"]:
                        # Test connectivity
                        still_connected = await self._test_peer_connectivity(peer.endpoint)
                        
                        if not still_connected:
                            peers_to_remove.append(endpoint)
                            
                            if self.on_peer_lost:
                                await self.on_peer_lost(peer)
                
                # Remove inactive peers
                for endpoint in peers_to_remove:
                    if endpoint in self.discovered_peers:
                        del self.discovered_peers[endpoint]
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Peer monitoring error: {e}")
                await asyncio.sleep(10)
    
    def get_discovered_peers(self) -> Dict[str, PeerEndpoint]:
        """Get all discovered peers"""
        return self.discovered_peers.copy()
    
    def get_nat_info(self) -> NATInfo:
        """Get NAT information"""
        return self.nat_info
    
    def get_status(self) -> Dict[str, Any]:
        """Get discovery status"""
        return {
            "is_running": self.is_running,
            "discovered_peers": len(self.discovered_peers),
            "nat_info": self.nat_info.to_dict(),
            "config": self.config,
            "local_ip": self.local_ip,
            "bootstrap_peers": len(self.bootstrap_peers)
        }
