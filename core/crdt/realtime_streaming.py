"""
Real-time CRDT Streaming for Live Collaboration
WebRTC-based streaming with operational transforms and conflict resolution
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import uuid

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of streaming events"""
    OPERATION = "operation"
    CURSOR_MOVE = "cursor_move"
    SELECTION_CHANGE = "selection_change"
    PRESENCE_UPDATE = "presence_update"
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    STATE_SYNC = "state_sync"


class ConflictResolutionStrategy(Enum):
    """Real-time conflict resolution strategies"""
    OPERATIONAL_TRANSFORM = "operational_transform"
    LAST_WRITER_WINS = "last_writer_wins"
    MERGE = "merge"
    VOTING = "voting"


@dataclass
class StreamOperation:
    """Real-time CRDT operation"""
    def __init__(self, op_id: str, client_id: str, operation_type: str,
                 path: str, value: Any = None, old_value: Any = None,
                 cursor_position: int = None, timestamp: float = None,
                 metadata: Dict[str, Any] = None):
        self.op_id = op_id
        self.client_id = client_id
        self.operation_type = operation_type
        self.path = path
        self.value = value
        self.old_value = old_value
        self.cursor_position = cursor_position
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
        self.dependencies: Set[str] = set()
        self.transformed = False
    
    def add_dependency(self, dependency_id: str):
        """Add operation dependency"""
        self.dependencies.add(dependency_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "op_id": self.op_id,
            "client_id": self.client_id,
            "operation_type": self.operation_type,
            "path": self.path,
            "value": self.value,
            "old_value": self.old_value,
            "cursor_position": self.cursor_position,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "dependencies": list(self.dependencies),
            "transformed": self.transformed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamOperation':
        """Create from dictionary"""
        return cls(
            op_id=data["op_id"],
            client_id=data["client_id"],
            operation_type=data["operation_type"],
            path=data["path"],
            value=data.get("value"),
            old_value=data.get("old_value"),
            cursor_position=data.get("cursor_position"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
            dependencies=set(data.get("dependencies", []))
        )


@dataclass
class ClientPresence:
    """Client presence information"""
    def __init__(self, client_id: str, username: str, cursor_position: int = 0,
                 selection_start: int = 0, selection_end: int = 0,
                 color: str = "#007ACC", last_seen: float = None):
        self.client_id = client_id
        self.username = username
        self.cursor_position = cursor_position
        self.selection_start = selection_start
        self.selection_end = selection_end
        self.color = color
        self.last_seen = last_seen or time.time()
        self.is_active = True
    
    def update_cursor(self, position: int):
        """Update cursor position"""
        self.cursor_position = position
        self.last_seen = time.time()
    
    def update_selection(self, start: int, end: int):
        """Update text selection"""
        self.selection_start = start
        self.selection_end = end
        self.last_seen = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class OperationalTransform:
    """Operational transform engine for real-time collaboration"""
    
    def __init__(self):
        self.transform_functions = {
            "insert": self._transform_insert,
            "delete": self._transform_delete,
            "retain": self._transform_retain,
            "format": self._transform_format
        }
    
    def transform(self, op1: StreamOperation, op2: StreamOperation) -> Tuple[StreamOperation, StreamOperation]:
        """Transform two concurrent operations"""
        if op1.operation_type == "insert" and op2.operation_type == "insert":
            return self._transform_insert_insert(op1, op2)
        elif op1.operation_type == "insert" and op2.operation_type == "delete":
            return self._transform_insert_delete(op1, op2)
        elif op1.operation_type == "delete" and op2.operation_type == "insert":
            op2_prime, op1_prime = self._transform_insert_delete(op2, op1)
            return op1_prime, op2_prime
        elif op1.operation_type == "delete" and op2.operation_type == "delete":
            return self._transform_delete_delete(op1, op2)
        else:
            # Default: no transformation needed
            return op1, op2
    
    def _transform_insert_insert(self, op1: StreamOperation, op2: StreamOperation) -> Tuple[StreamOperation, StreamOperation]:
        """Transform two insert operations"""
        if op1.path == op2.path:
            if op1.timestamp <= op2.timestamp:
                # op1 came first, op2 needs to be adjusted
                op2_prime = StreamOperation(
                    op_id=op2.op_id + "_transformed",
                    client_id=op2.client_id,
                    operation_type=op2.operation_type,
                    path=op2.path,
                    value=op2.value,
                    cursor_position=op2.cursor_position + len(op1.value) if op2.cursor_position else None,
                    timestamp=op2.timestamp
                )
                return op1, op2_prime
            else:
                # op2 came first, op1 needs to be adjusted
                op1_prime = StreamOperation(
                    op_id=op1.op_id + "_transformed",
                    client_id=op1.client_id,
                    operation_type=op1.operation_type,
                    path=op1.path,
                    value=op1.value,
                    cursor_position=op1.cursor_position + len(op2.value) if op1.cursor_position else None,
                    timestamp=op1.timestamp
                )
                return op1_prime, op2
        return op1, op2
    
    def _transform_insert_delete(self, insert_op: StreamOperation, delete_op: StreamOperation) -> Tuple[StreamOperation, StreamOperation]:
        """Transform insert and delete operations"""
        if insert_op.path == delete_op.path:
            # Adjust delete position based on insert
            if delete_op.cursor_position is not None and insert_op.cursor_position is not None:
                if insert_op.cursor_position <= delete_op.cursor_position:
                    delete_prime = StreamOperation(
                        op_id=delete_op.op_id + "_transformed",
                        client_id=delete_op.client_id,
                        operation_type=delete_op.operation_type,
                        path=delete_op.path,
                        value=delete_op.value,
                        cursor_position=delete_op.cursor_position + len(insert_op.value),
                        timestamp=delete_op.timestamp
                    )
                    return insert_op, delete_prime
        
        return insert_op, delete_op
    
    def _transform_delete_delete(self, op1: StreamOperation, op2: StreamOperation) -> Tuple[StreamOperation, StreamOperation]:
        """Transform two delete operations"""
        if op1.path == op2.path:
            # Handle overlapping deletes
            if op1.timestamp <= op2.timestamp:
                # op1 came first, op2 might be redundant
                if (op1.cursor_position and op2.cursor_position and
                    op2.cursor_position >= op1.cursor_position):
                    # op2 is trying to delete something already deleted by op1
                    op2_prime = StreamOperation(
                        op_id=op2.op_id + "_transformed",
                        client_id=op2.client_id,
                        operation_type="noop",  # No-op
                        path=op2.path,
                        timestamp=op2.timestamp
                    )
                    return op1, op2_prime
        
        return op1, op2
    
    def _transform_insert(self, op: StreamOperation) -> StreamOperation:
        """Transform insert operation"""
        return op
    
    def _transform_delete(self, op: StreamOperation) -> StreamOperation:
        """Transform delete operation"""
        return op
    
    def _transform_retain(self, op: StreamOperation) -> StreamOperation:
        """Transform retain operation"""
        return op
    
    def _transform_format(self, op: StreamOperation) -> StreamOperation:
        """Transform format operation"""
        return op


class RealtimeCRDTStream:
    """Real-time CRDT streaming server"""
    
    def __init__(self, room_id: str, max_clients: int = 100):
        self.room_id = room_id
        self.max_clients = max_clients
        
        # Client management
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.client_presence: Dict[str, ClientPresence] = {}
        
        # CRDT state
        self.document_state: str = ""
        self.operations: List[StreamOperation] = []
        self.operation_buffer: Dict[str, StreamOperation] = {}
        
        # Transform engine
        self.transform_engine = OperationalTransform()
        
        # Conflict resolution
        self.conflict_resolver = ConflictResolutionStrategy.OPERATIONAL_TRANSFORM
        self.pending_conflicts: List[Tuple[StreamOperation, StreamOperation]] = []
        
        # Configuration
        self.config = {
            "max_buffer_size": 1000,
            "sync_interval": 0.1,  # 100ms
            "conflict_timeout": 5.0,
            "presence_timeout": 30.0,
            "enable_conflict_resolution": True
        }
        
        # Performance metrics
        self.metrics = {
            "operations_processed": 0,
            "conflicts_resolved": 0,
            "clients_connected": 0,
            "messages_sent": 0,
            "average_latency": 0.0
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.on_client_connected = None
        self.on_client_disconnected = None
        self.on_operation_applied = None
        self.on_conflict_detected = None
    
    async def start_server(self, host: str = "localhost", port: int = 8765) -> bool:
        """Start the WebSocket server"""
        try:
            self.is_running = True
            
            # Start WebSocket server
            server = await websockets.serve(
                self.handle_client_connection,
                host,
                port,
                max_size=10**7,  # 10MB
                ping_interval=20,
                ping_timeout=10
            )
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._sync_loop()),
                asyncio.create_task(self._presence_loop()),
                asyncio.create_task(self._conflict_resolution_loop()),
                asyncio.create_task(self._cleanup_loop()),
                asyncio.create_task(self._metrics_loop())
            ]
            
            logger.info(f"Real-time CRDT stream started on {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start CRDT stream server: {e}")
            return False
    
    async def stop(self):
        """Stop the streaming server"""
        self.is_running = False
        
        # Close all client connections
        for client_id, websocket in self.clients.items():
            try:
                await websocket.close()
            except:
                pass
        
        self.clients.clear()
        self.client_presence.clear()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Real-time CRDT stream stopped")
    
    async def handle_client_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle new client connection"""
        try:
            # Generate client ID
            client_id = str(uuid.uuid4())
            
            # Add client
            self.clients[client_id] = websocket
            self.metrics["clients_connected"] += 1
            
            # Send initial state
            await self.send_initial_state(client_id)
            
            # Handle messages
            async for message in websocket:
                await self.handle_client_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            await self.handle_client_disconnection(client_id)
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            await self.handle_client_disconnection(client_id)
    
    async def send_initial_state(self, client_id: str):
        """Send initial state to new client"""
        try:
            initial_state = {
                "type": StreamEventType.STATE_SYNC.value,
                "room_id": self.room_id,
                "document": self.document_state,
                "operations": [op.to_dict() for op in self.operations[-100:]],  # Last 100 ops
                "presence": [presence.to_dict() for presence in self.client_presence.values()],
                "timestamp": time.time()
            }
            
            websocket = self.clients.get(client_id)
            if websocket:
                await websocket.send(json.dumps(initial_state))
                
        except Exception as e:
            logger.error(f"Failed to send initial state to {client_id}: {e}")
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == StreamEventType.OPERATION.value:
                await self.handle_operation(client_id, data)
            elif message_type == StreamEventType.CURSOR_MOVE.value:
                await self.handle_cursor_move(client_id, data)
            elif message_type == StreamEventType.SELECTION_CHANGE.value:
                await self.handle_selection_change(client_id, data)
            elif message_type == StreamEventType.PRESENCE_UPDATE.value:
                await self.handle_presence_update(client_id, data)
            
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
    
    async def handle_operation(self, client_id: str, data: Dict[str, Any]):
        """Handle CRDT operation from client"""
        try:
            op_data = data.get("operation", {})
            
            operation = StreamOperation(
                op_id=op_data.get("op_id", str(uuid.uuid4())),
                client_id=client_id,
                operation_type=op_data.get("operation_type"),
                path=op_data.get("path"),
                value=op_data.get("value"),
                old_value=op_data.get("old_value"),
                cursor_position=op_data.get("cursor_position"),
                timestamp=op_data.get("timestamp", time.time()),
                metadata=op_data.get("metadata", {})
            )
            
            # Check for conflicts with pending operations
            conflicts = self._detect_conflicts(operation)
            
            if conflicts:
                # Apply operational transforms
                transformed_op = operation
                for conflict_op in conflicts:
                    transformed_op, _ = self.transform_engine.transform(transformed_op, conflict_op)
                
                operation = transformed_op
            
            # Apply operation to document state
            await self.apply_operation(operation)
            
            # Broadcast to other clients
            await self.broadcast_operation(operation, exclude_client=client_id)
            
            self.metrics["operations_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error handling operation from {client_id}: {e}")
    
    async def handle_cursor_move(self, client_id: str, data: Dict[str, Any]):
        """Handle cursor movement"""
        try:
            position = data.get("position", 0)
            
            if client_id in self.client_presence:
                self.client_presence[client_id].update_cursor(position)
                
                # Broadcast cursor update
                cursor_update = {
                    "type": StreamEventType.CURSOR_MOVE.value,
                    "client_id": client_id,
                    "position": position,
                    "timestamp": time.time()
                }
                
                await self.broadcast_message(cursor_update, exclude_client=client_id)
                
        except Exception as e:
            logger.error(f"Error handling cursor move from {client_id}: {e}")
    
    async def handle_selection_change(self, client_id: str, data: Dict[str, Any]):
        """Handle text selection change"""
        try:
            start = data.get("start", 0)
            end = data.get("end", 0)
            
            if client_id in self.client_presence:
                self.client_presence[client_id].update_selection(start, end)
                
                # Broadcast selection update
                selection_update = {
                    "type": StreamEventType.SELECTION_CHANGE.value,
                    "client_id": client_id,
                    "start": start,
                    "end": end,
                    "timestamp": time.time()
                }
                
                await self.broadcast_message(selection_update, exclude_client=client_id)
                
        except Exception as e:
            logger.error(f"Error handling selection change from {client_id}: {e}")
    
    async def handle_presence_update(self, client_id: str, data: Dict[str, Any]):
        """Handle presence update"""
        try:
            username = data.get("username", f"User_{client_id[:8]}")
            color = data.get("color", "#007ACC")
            
            if client_id not in self.client_presence:
                self.client_presence[client_id] = ClientPresence(
                    client_id=client_id,
                    username=username,
                    color=color
                )
                
                # Notify callback
                if self.on_client_connected:
                    self.on_client_connected(client_id, username)
            
            # Broadcast presence update
            presence_update = {
                "type": StreamEventType.PRESENCE_UPDATE.value,
                "client_id": client_id,
                "username": username,
                "color": color,
                "timestamp": time.time()
            }
            
            await self.broadcast_message(presence_update)
            
        except Exception as e:
            logger.error(f"Error handling presence update from {client_id}: {e}")
    
    async def handle_client_disconnection(self, client_id: str):
        """Handle client disconnection"""
        try:
            # Remove client
            if client_id in self.clients:
                del self.clients[client_id]
            
            # Remove presence
            if client_id in self.client_presence:
                username = self.client_presence[client_id].username
                del self.client_presence[client_id]
                
                # Broadcast presence removal
                presence_removal = {
                    "type": StreamEventType.PRESENCE_UPDATE.value,
                    "client_id": client_id,
                    "disconnected": True,
                    "timestamp": time.time()
                }
                
                await self.broadcast_message(presence_removal)
                
                # Notify callback
                if self.on_client_disconnected:
                    self.on_client_disconnected(client_id, username)
            
            logger.info(f"Client {client_id} disconnected")
            
        except Exception as e:
            logger.error(f"Error handling client disconnection {client_id}: {e}")
    
    def _detect_conflicts(self, operation: StreamOperation) -> List[StreamOperation]:
        """Detect conflicts with pending operations"""
        conflicts = []
        
        for pending_op in self.operations:
            if (pending_op.path == operation.path and
                pending_op.client_id != operation.client_id and
                abs(pending_op.timestamp - operation.timestamp) < self.config["conflict_timeout"]):
                conflicts.append(pending_op)
        
        return conflicts
    
    async def apply_operation(self, operation: StreamOperation):
        """Apply operation to document state"""
        try:
            if operation.operation_type == "insert":
                if operation.cursor_position is not None:
                    self.document_state = (
                        self.document_state[:operation.cursor_position] +
                        str(operation.value) +
                        self.document_state[operation.cursor_position:]
                    )
                else:
                    self.document_state += str(operation.value)
                    
            elif operation.operation_type == "delete":
                if operation.cursor_position is not None:
                    delete_length = len(str(operation.value)) if operation.value else 1
                    self.document_state = (
                        self.document_state[:operation.cursor_position] +
                        self.document_state[operation.cursor_position + delete_length:]
                    )
                elif operation.path in self.document_state:
                    self.document_state = self.document_state.replace(operation.path, "")
                    
            elif operation.operation_type == "format":
                # Handle formatting operations
                pass
            
            # Add to operations history
            self.operations.append(operation)
            
            # Limit operations history
            if len(self.operations) > self.config["max_buffer_size"]:
                self.operations = self.operations[-self.config["max_buffer_size"]:]
            
            # Notify callback
            if self.on_operation_applied:
                self.on_operation_applied(operation)
                
        except Exception as e:
            logger.error(f"Error applying operation {operation.op_id}: {e}")
    
    async def broadcast_operation(self, operation: StreamOperation, exclude_client: str = None):
        """Broadcast operation to all clients"""
        message = {
            "type": StreamEventType.OPERATION.value,
            "operation": operation.to_dict(),
            "timestamp": time.time()
        }
        
        await self.broadcast_message(message, exclude_client)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude_client: str = None):
        """Broadcast message to all clients"""
        message_str = json.dumps(message)
        
        for client_id, websocket in self.clients.items():
            if client_id != exclude_client:
                try:
                    await websocket.send(message_str)
                    self.metrics["messages_sent"] += 1
                except Exception as e:
                    logger.error(f"Failed to send message to {client_id}: {e}")
    
    async def _sync_loop(self):
        """Background loop for periodic synchronization"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config["sync_interval"])
                
                # Send periodic sync messages
                sync_message = {
                    "type": StreamEventType.STATE_SYNC.value,
                    "document": self.document_state,
                    "timestamp": time.time()
                }
                
                await self.broadcast_message(sync_message)
                
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(1)
    
    async def _presence_loop(self):
        """Background loop for presence management"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                current_time = time.time()
                timeout = self.config["presence_timeout"]
                
                # Remove inactive clients
                inactive_clients = []
                for client_id, presence in self.client_presence.items():
                    if current_time - presence.last_seen > timeout:
                        inactive_clients.append(client_id)
                
                for client_id in inactive_clients:
                    await self.handle_client_disconnection(client_id)
                
            except Exception as e:
                logger.error(f"Presence loop error: {e}")
                await asyncio.sleep(5)
    
    async def _conflict_resolution_loop(self):
        """Background loop for conflict resolution"""
        while self.is_running:
            try:
                await asyncio.sleep(1)  # Check every second
                
                # Process pending conflicts
                if self.pending_conflicts and self.config["enable_conflict_resolution"]:
                    await self._resolve_pending_conflicts()
                
            except Exception as e:
                logger.error(f"Conflict resolution loop error: {e}")
                await asyncio.sleep(5)
    
    async def _resolve_pending_conflicts(self):
        """Resolve pending conflicts"""
        while self.pending_conflicts:
            conflict = self.pending_conflicts.pop(0)
            op1, op2 = conflict
            
            # Apply operational transform
            op1_prime, op2_prime = self.transform_engine.transform(op1, op2)
            
            # Apply resolved operations
            await self.apply_operation(op1_prime)
            await self.apply_operation(op2_prime)
            
            self.metrics["conflicts_resolved"] += 1
            
            # Notify about conflict resolution
            if self.on_conflict_detected:
                self.on_conflict_detected(conflict, (op1_prime, op2_prime))
    
    async def _cleanup_loop(self):
        """Background loop for cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
                # Clean up old operations
                current_time = time.time()
                max_age = 3600  # 1 hour
                
                self.operations = [
                    op for op in self.operations
                    if current_time - op.timestamp < max_age
                ]
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_loop(self):
        """Background loop for metrics collection"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                logger.debug(f"CRDT stream metrics: {self.metrics}")
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(10)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics"""
        return {
            **self.metrics,
            "active_clients": len(self.clients),
            "document_length": len(self.document_state),
            "operations_buffer_size": len(self.operations),
            "pending_conflicts": len(self.pending_conflicts)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get stream status"""
        return {
            "is_running": self.is_running,
            "room_id": self.room_id,
            "metrics": self.get_metrics(),
            "config": self.config
        }
