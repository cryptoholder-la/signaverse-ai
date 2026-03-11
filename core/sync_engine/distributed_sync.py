"""
Distributed Synchronization Engine
Handles peer-to-peer sync via Holochain DHT and gossip protocols
"""

import asyncio
import json
import time
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, asdict
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class PeerInfo:
    """Information about a network peer"""
    agent_pubkey: str
    endpoint: str
    last_seen: float
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class SyncRequest:
    """Request for syncing commits between peers"""
    request_id: str
    requester: str
    target_peer: str
    from_commit: Optional[str] = None
    to_commit: Optional[str] = None
    filters: Dict[str, any] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


@dataclass
class SyncResponse:
    """Response containing commits for sync"""
    request_id: str
    commits: List[Dict]  # Serialized commits
    has_more: bool
    next_cursor: Optional[str] = None


class DistributedSyncEngine:
    """Core synchronization engine for distributed collaboration"""
    
    def __init__(self, local_agent_pubkey: str):
        self.local_agent_pubkey = local_agent_pubkey
        self.peers: Dict[str, PeerInfo] = {}
        self.sync_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.sync_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """Start the sync engine"""
        self.is_running = True
        asyncio.create_task(self._sync_worker())
        asyncio.create_task(self._peer_discovery())
        asyncio.create_task(self._gossip_loop())
        logger.info("Distributed sync engine started")
    
    async def stop(self):
        """Stop the sync engine"""
        self.is_running = False
        logger.info("Distributed sync engine stopped")
    
    def register_peer(self, peer_info: PeerInfo):
        """Register a new peer"""
        self.peers[peer_info.agent_pubkey] = peer_info
        logger.info(f"Registered peer: {peer_info.agent_pubkey}")
    
    def unregister_peer(self, agent_pubkey: str):
        """Unregister a peer"""
        if agent_pubkey in self.peers:
            del self.peers[agent_pubkey]
            logger.info(f"Unregistered peer: {agent_pubkey}")
    
    async def _peer_discovery(self):
        """Discover peers via multiple strategies"""
        while self.is_running:
            try:
                # Bootstrap nodes
                await self._discover_bootstrap_peers()
                
                # LAN discovery
                await self._discover_lan_peers()
                
                # DHT gossip
                await self._discover_dht_peers()
                
                await asyncio.sleep(30)  # Discovery interval
            except Exception as e:
                logger.error(f"Peer discovery error: {e}")
                await asyncio.sleep(5)
    
    async def _discover_bootstrap_peers(self):
        """Connect to bootstrap nodes"""
        # In a real implementation, this would connect to known bootstrap nodes
        bootstrap_nodes = [
            "bootstrap1.signaverse.network:4242",
            "bootstrap2.signaverse.network:4242"
        ]
        
        for endpoint in bootstrap_nodes:
            try:
                # Simulate peer discovery
                peer_pubkey = hashlib.sha256(endpoint.encode()).hexdigest()
                peer_info = PeerInfo(
                    agent_pubkey=peer_pubkey,
                    endpoint=endpoint,
                    last_seen=time.time(),
                    capabilities=["sync", "validate"]
                )
                self.register_peer(peer_info)
            except Exception as e:
                logger.debug(f"Failed to connect to bootstrap {endpoint}: {e}")
    
    async def _discover_lan_peers(self):
        """Discover peers on local network"""
        # In a real implementation, this would use mDNS or similar
        pass
    
    async def _discover_dht_peers(self):
        """Discover peers via DHT gossip"""
        # In a real implementation, this would query Holochain DHT
        pass
    
    async def _gossip_loop(self):
        """Main gossip loop for sharing commits"""
        while self.is_running:
            try:
                await self._gossip_commits()
                await asyncio.sleep(10)  # Gossip interval
            except Exception as e:
                logger.error(f"Gossip loop error: {e}")
                await asyncio.sleep(5)
    
    async def _gossip_commits(self):
        """Share commits with random peers"""
        if not self.peers:
            return
        
        # Select random subset of peers
        available_peers = list(self.peers.values())
        sample_size = min(3, len(available_peers))
        
        # In a real implementation, this would use proper random selection
        for peer in available_peers[:sample_size]:
            try:
                await self._sync_with_peer(peer.agent_pubkey)
            except Exception as e:
                logger.debug(f"Failed to sync with peer {peer.agent_pubkey}: {e}")
    
    async def _sync_with_peer(self, peer_pubkey: str) -> Optional[SyncResponse]:
        """Sync with a specific peer"""
        if peer_pubkey not in self.peers:
            return None
        
        peer = self.peers[peer_pubkey]
        
        # Create sync request
        request = SyncRequest(
            request_id=hashlib.sha256(f"{self.local_agent_pubkey}_{time.time()}".encode()).hexdigest(),
            requester=self.local_agent_pubkey,
            target_peer=peer_pubkey,
            filters={"limit": 100}  # Limit batch size
        )
        
        try:
            # Send request (simulated)
            response = await self._send_sync_request(peer.endpoint, request)
            return response
        except Exception as e:
            logger.error(f"Sync request failed: {e}")
            return None
    
    async def _send_sync_request(self, endpoint: str, request: SyncRequest) -> SyncResponse:
        """Send sync request to peer endpoint"""
        # Simulate network request
        await asyncio.sleep(0.1)  # Network latency
        
        # Mock response
        return SyncResponse(
            request_id=request.request_id,
            commits=[],
            has_more=False
        )
    
    async def _sync_worker(self):
        """Process sync queue"""
        while self.is_running:
            try:
                sync_task = await self.sync_queue.get()
                await self._process_sync_task(sync_task)
                self.sync_queue.task_done()
            except Exception as e:
                logger.error(f"Sync worker error: {e}")
    
    async def _process_sync_task(self, sync_task: Dict):
        """Process individual sync task"""
        task_type = sync_task.get("type")
        
        if task_type == "publish_commit":
            await self._publish_commit(sync_task["commit"])
        elif task_type == "request_sync":
            await self._handle_sync_request(sync_task["request"])
        elif task_type == "validate_commit":
            await self._validate_commit(sync_task["commit"])
    
    async def publish_commit(self, commit_data: Dict):
        """Publish a commit to the network"""
        await self.sync_queue.put({
            "type": "publish_commit",
            "commit": commit_data
        })
    
    async def _publish_commit(self, commit_data: Dict):
        """Publish commit to DHT and gossip to peers"""
        try:
            # Publish to DHT
            await self._publish_to_dht(commit_data)
            
            # Gossip to peers
            await self._gossip_commit(commit_data)
            
            logger.info(f"Published commit: {commit_data.get('commit_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to publish commit: {e}")
    
    async def _publish_to_dht(self, commit_data: Dict):
        """Publish commit to Holochain DHT"""
        # In a real implementation, this would use Holochain API
        commit_hash = commit_data.get("commit_id")
        if commit_hash:
            # Store in DHT with commit hash as key
            pass
    
    async def _gossip_commit(self, commit_data: Dict):
        """Gossip commit to connected peers"""
        for peer_pubkey, peer_info in self.peers.items():
            try:
                await self._send_commit_to_peer(peer_info.endpoint, commit_data)
            except Exception as e:
                logger.debug(f"Failed to gossip commit to {peer_pubkey}: {e}")
    
    async def _send_commit_to_peer(self, endpoint: str, commit_data: Dict):
        """Send commit to specific peer"""
        # Simulate network send
        await asyncio.sleep(0.05)
    
    async def request_commits(self, from_commit: Optional[str] = None, 
                            limit: int = 100) -> List[Dict]:
        """Request commits from network"""
        commits = []
        
        for peer_pubkey in self.peers:
            response = await self._sync_with_peer(peer_pubkey)
            if response and response.commits:
                commits.extend(response.commits)
                if len(commits) >= limit:
                    break
        
        return commits[:limit]
    
    def register_sync_handler(self, event_type: str, handler: Callable):
        """Register handler for sync events"""
        self.sync_handlers[event_type] = handler
    
    async def _handle_sync_request(self, request: SyncRequest):
        """Handle incoming sync request"""
        if "sync_request" in self.sync_handlers:
            await self.sync_handlers["sync_request"](request)
    
    async def _validate_commit(self, commit_data: Dict):
        """Validate received commit"""
        if "validate_commit" in self.sync_handlers:
            await self.sync_handlers["validate_commit"](commit_data)
    
    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        return {
            "connected_peers": len(self.peers),
            "pending_requests": len(self.pending_requests),
            "sync_queue_size": self.sync_queue.qsize(),
            "is_running": self.is_running
        }
    
    def get_peer_list(self) -> List[PeerInfo]:
        """Get list of connected peers"""
        return list(self.peers.values())


class ConflictResolver:
    """Resolves conflicts in distributed commits"""
    
    @staticmethod
    def resolve_commit_conflict(commits: List[Dict]) -> List[Dict]:
        """Resolve conflicts between conflicting commits"""
        if len(commits) <= 1:
            return commits
        
        # Sort by timestamp
        sorted_commits = sorted(commits, key=lambda c: c.get("timestamp", 0))
        
        # Apply conflict resolution rules
        resolved = []
        for commit in sorted_commits:
            if ConflictResolver._is_commit_valid(commit, resolved):
                resolved.append(commit)
        
        return resolved
    
    @staticmethod
    def _is_commit_valid(commit: Dict, previous_commits: List[Dict]) -> bool:
        """Check if commit is valid given previous commits"""
        # Simplified validation
        # In a real implementation, this would check for conflicts
        return True
    
    @staticmethod
    def merge_deltas(deltas1: List[Dict], deltas2: List[Dict]) -> List[Dict]:
        """Merge two sets of deltas"""
        # Simplified merge
        # In a real implementation, this would use operational transform
        return deltas1 + deltas2
