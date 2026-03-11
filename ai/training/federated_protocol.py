"""
Federated AI Learning Protocol
Manages federated learning across distributed nodes
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FederatedRole(Enum):
    """Roles in federated learning"""
    COORDINATOR = "coordinator"
    CLIENT = "client"
    AGGREGATOR = "aggregator"


class AggregationMethod(Enum):
    """Methods for aggregating model updates"""
    FED_AVG = "fed_avg"
    FED_PROX = "fed_prox"
    FED_TRIMMED_MEAN = "fed_trimmed_mean"
    SECURE_AGGREGATION = "secure_aggregation"
    WEIGHTED_AVERAGING = "weighted_averaging"


class PrivacyMechanism(Enum):
    """Privacy mechanisms for federated learning"""
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    SECURE_AGGREGATION = "secure_aggregation"
    HOMOMORPHIC_ENCRYPTION = "homomorphic_encryption"
    ADDITIVE_NOISE = "additive_noise"


@dataclass
class ClientInfo:
    """Information about a federated client"""
    def __init__(self, client_id: str, endpoint: str, capabilities: List[str],
                 data_size: int, bandwidth: float, reputation: float = 50.0):
        self.client_id = client_id
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.data_size = data_size
        self.bandwidth = bandwidth
        self.reputation = reputation
        self.last_active = time.time()
        self.contribution_count = 0
        self.selected_rounds: Set[int] = set()
        self.performance_metrics: Dict[str, Any] = {}
        self.privacy_budget = 1.0
    
    def update_activity(self):
        """Update client activity timestamp"""
        self.last_active = time.time()
    
    def add_contribution(self):
        """Increment contribution count"""
        self.contribution_count += 1
    
    def update_reputation(self, delta: float):
        """Update client reputation"""
        self.reputation = max(0, min(100, self.reputation + delta))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class FederatedRound:
    """Information about a federated learning round"""
    def __init__(self, round_id: int, start_time: float, end_time: Optional[float] = None,
                 participating_clients: List[str] = None, selected_clients: List[str] = None,
                 aggregation_method: AggregationMethod = AggregationMethod.FED_AVG,
                 privacy_mechanism: PrivacyMechanism = DIFFERENTIAL_PRIVACY,
                 min_clients: int = 2, max_clients: int = 10,
                 target_accuracy: float = 0.95, timeout: float = 300.0):
        self.round_id = round_id
        self.start_time = start_time
        self.end_time = end_time
        self.participating_clients = participating_clients or []
        self.selected_clients = selected_clients or []
        self.aggregation_method = aggregation_method
        self.privacy_mechanism = privacy_mechanism
        self.min_clients = min_clients
        self.max_clients = max_clients
        self.target_accuracy = target_accuracy
        self.timeout = timeout
        self.status = "pending"
        self.results: List[Dict[str, Any]] = []
        self.aggregation_time: Optional[float] = None
        self.communication_overhead: float = 0.0
    
    def add_participant(self, client_id: str):
        """Add participant to round"""
        if client_id not in self.participating_clients:
            self.participating_clients.append(client_id)
    
    def select_clients(self, client_infos: Dict[str, ClientInfo]):
        """Select clients for this round"""
        available_clients = [
            client_id for client_id, info in client_infos.items()
            if info.last_active > time.time() - 300  # Active in last 5 minutes
        ]
        
        if len(available_clients) < self.min_clients:
            self.selected_clients = available_clients
            return
        
        # Client selection strategies
        if self.max_clients >= len(available_clients):
            if len(available_clients) == self.max_clients:
                self.selected_clients = available_clients
            else:
                # Sample based on strategy
                if hasattr(self, '_select_clients_' + self.aggregation_method.value):
                    method = getattr(self, f'_select_clients_{self.aggregation_method.value}')
                    self.selected_clients = method(client_infos)
                else:
                    # Default random sampling
                    import random
                    self.selected_clients = random.sample(
                        available_clients,
                        min(self.max_clients, len(available_clients))
                    )
        else:
            # Select all available clients
            self.selected_clients = available_clients
        
        self.participating_clients = self.selected_clients.copy()
    
    def complete_round(self, results: List[Dict[str, Any]]):
        """Complete the federated round"""
        self.end_time = time.time()
        self.status = "completed"
        self.results = results
        self.communication_overhead = time.time() - self.start_time


class FederatedProtocol:
    """Federated learning protocol implementation"""
    
    def __init__(self, node_id: str, role: FederatedRole = FederatedRole.CLIENT):
        self.node_id = node_id
        self.role = role
        
        # Protocol state
        self.current_round: Optional[FederatedRound] = None
        self.round_history: List[FederatedRound] = []
        self.client_info: Dict[str, ClientInfo] = {}
        
        # Configuration
        self.config = {
            "max_rounds": 100,
            "round_timeout": 300.0,
            "aggregation_frequency": 30.0,
            "client_timeout": 60.0,
            "min_participants": 2,
            "max_participants": 50,
            "privacy_budget": 1.0,
            "enable_secure_aggregation": True,
            "enable_differential_privacy": True
        }
        
        # Performance metrics
        self.metrics = {
            "rounds_completed": 0,
            "total_clients_served": 0,
            "total_models_aggregated": 0,
            "communication_bytes": 0,
            "average_round_time": 0.0,
            "privacy_costs": []
        }
        
        # Network communication
        self.network_clients = {}
        self.message_handlers = {}
        
        # Privacy and security
        self.encryption_keys: Dict[str, str] = {}
        self.aggregation_secrets: Dict[str, str] = {}
        
        # Background tasks
        self.is_running = False
    
    def register_client(self, client_info: ClientInfo):
        """Register a client for federated learning"""
        self.client_info[client_info.client_id] = client_info
        logger.info(f"Registered client {client_info.client_id}")
    
    def unregister_client(self, client_id: str):
        """Unregister a client"""
        if client_id in self.client_info:
            del self.client_info[client_id]
            logger.info(f"Unregistered client {client_id}")
    
    async def start_coordinator(self) -> bool:
        """Start as federated learning coordinator"""
        try:
            self.role = FederatedRole.COORDINATOR
            self.is_running = True
            
            logger.info(f"Starting federated coordinator {self.node_id}")
            
            # Start coordination loop
            await self._coordination_loop()
            
        except Exception as e:
            logger.error(f"Failed to start coordinator: {e}")
            return False
    
    async def start_client(self, coordinator_endpoint: str) -> bool:
        """Start as federated learning client"""
        try:
            self.role = FederatedRole.CLIENT
            self.is_running = True
            
            logger.info(f"Starting federated client {self.node_id}")
            
            # Connect to coordinator
            # In real implementation, would establish network connection
            self.network_clients["coordinator"] = {
                "endpoint": coordinator_endpoint,
                "connected": True,
                "last_contact": time.time()
            }
            
            # Start client loop
            await self._client_loop()
            
        except Exception as e:
            logger.error(f"Failed to start client: {e}")
            return False
    
    async def _coordination_loop(self):
        """Main coordination loop for federated learning"""
        round_id = 0
        
        while self.is_running and round_id < self.config["max_rounds"]:
            try:
                # Start new round
                round_config = FederatedRound(
                    round_id=round_id,
                    start_time=time.time()
                )
                
                # Select clients for this round
                round_config.select_clients(self.client_info)
                
                if not round_config.selected_clients:
                    logger.warning(f"Round {round_id}: No available clients")
                    await asyncio.sleep(self.config["aggregation_frequency"])
                    round_id += 1
                    continue
                
                logger.info(f"Starting round {round_id} with {len(round_config.selected_clients)} clients")
                
                # Send training request to clients
                await self._send_training_requests(round_config)
                
                # Wait for responses or timeout
                responses = await self._collect_client_responses(round_config)
                
                if responses:
                    # Aggregate results
                    aggregated_result = await self._aggregate_results(responses, round_config)
                    
                    # Update global model
                    await self._update_global_model(aggregated_result)
                    
                    # Send aggregated model back to clients
                    await self._broadcast_aggregated_model(aggregated_result, round_config)
                    
                    # Complete round
                    round_config.complete_round(responses)
                    
                    # Update client metrics
                    await self._update_client_metrics(responses, round_config)
                
                else:
                    logger.warning(f"Round {round_id} timed out")
                
                # Update metrics
                self.metrics.rounds_completed += 1
                self.metrics.total_clients_served += len(round_config.selected_clients)
                
                round_id += 1
                
                # Wait before next round
                await asyncio.sleep(self.config["aggregation_frequency"])
                
            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
                await asyncio.sleep(10)
    
    async def _client_loop(self):
        """Main client loop for federated learning"""
        while self.is_running:
            try:
                # Wait for training request from coordinator
                training_request = await self._wait_for_training_request()
                
                if training_request:
                    # Process training request
                    await self._process_training_request(training_request)
                    
                    # Send results back to coordinator
                    await self._send_training_results(training_request)
                    
                    # Update activity
                    if training_request["round_id"] in self.client_info.get(training_request["client_id"], {}).get("selected_rounds", set()):
                        client_info = self.client_info[training_request["client_id"]]
                        client_info.selected_rounds.add(training_request["round_id"])
                        client_info.update_activity()
                
                else:
                    await asyncio.sleep(5)  # Wait for next request
                    
            except Exception as e:
                logger.error(f"Client loop error: {e}")
                await asyncio.sleep(10)
    
    async def _send_training_requests(self, round_config: FederatedRound):
        """Send training requests to selected clients"""
        for client_id in round_config.selected_clients:
            if client_id in self.client_info:
                client = self.client_info[client_id]
                
                request = {
                    "round_id": round_config.round_id,
                    "coordinator_id": self.node_id,
                    "training_config": {
                        "model_type": "sign_transformer",
                        "epochs": 5,
                        "batch_size": 32,
                        "learning_rate": 0.001,
                        "privacy_budget": client.privacy_budget
                    },
                    "timeout": round_config.timeout,
                    "timestamp": time.time()
                }
                
                # In real implementation, would send over network
                # For now, simulate
                await asyncio.sleep(0.1)
                
                logger.debug(f"Sent training request to client {client_id}")
    
    async def _collect_client_responses(self, round_config: FederatedRound) -> List[Dict[str, Any]]:
        """Collect responses from clients"""
        responses = []
        remaining_time = round_config.timeout
        
        while remaining_time > 0 and len(responses) < len(round_config.selected_clients):
            # Check for completed responses
            for client_id in round_config.selected_clients:
                if client_id in self.client_info:
                    client = self.client_info[client_id]
                    
                    # Check if client has completed this round
                    if (round_config.round_id in client.selected_rounds and
                        hasattr(client, 'training_results') and
                        round_config.round_id in client.training_results):
                        
                        result = client.training_results[round_config.round_id]
                        responses.append(result)
                        logger.debug(f"Received response from client {client_id}")
            
            # Wait a bit before checking again
            await asyncio.sleep(2)
            remaining_time -= 2
        
        return responses
    
    async def _aggregate_results(self, responses: List[Dict[str, Any]], 
                            round_config: FederatedRound) -> Dict[str, Any]:
        """Aggregate results from clients"""
        start_time = time.time()
        
        if round_config.aggregation_method == AggregationMethod.FED_AVG:
            aggregated = await self._federated_averaging(responses)
        elif round_config.aggregation_method == AggregationMethod.FED_PROX:
            aggregated = await self._federated_prox(responses)
        elif round_config.aggregation_method == AggregationMethod.FED_TRIMMED_MEAN:
            aggregated = await self._federated_trimmed_mean(responses)
        elif round_config.aggregation_method == AggregationMethod.WEIGHTED_AVERAGING:
            aggregated = await self._weighted_averaging(responses, round_config)
        elif round_config.aggregation_method == AggregationMethod.SECURE_AGGREGATION:
            aggregated = await self._secure_aggregation(responses, round_config)
        else:
            # Default to federated averaging
            aggregated = await self._federated_averaging(responses)
        
        round_config.aggregation_time = time.time() - start_time
        
        return aggregated
    
    async def _federated_averaging(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Federated averaging aggregation"""
        if not responses:
            return {}
        
        # Extract model weights from responses
        all_weights = []
        total_samples = 0
        
        for response in responses:
            model_state = response.get("model_state", {})
            weights = model_state.get("weights", [])
            
            if weights:
                all_weights.append(weights)
                total_samples += response.get("num_samples", 1)
        
        if not all_weights:
            return {}
        
        # Compute weighted average
        num_clients = len(all_weights)
        if num_clients == 0:
            return {}
        
        # Simple equal weighting
        averaged_weights = []
        
        for i in range(len(all_weights[0])):
            layer_weights = []
            for client_weights in all_weights:
                layer_weights.append(client_weights[i])
            
            # Average across clients
            avg_layer = sum(layer_weights) / len(layer_weights)
            averaged_weights.append(avg_layer)
        
        return {
            "aggregated_weights": averaged_weights,
            "num_samples": total_samples,
            "num_clients": num_clients,
            "aggregation_method": "federated_averaging"
        }
    
    async def _federated_prox(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Federated Proximal aggregation"""
        # Simplified Proximal aggregation
        return await self._federated_averaging(responses)
    
    async def _federated_trimmed_mean(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Federated trimmed mean aggregation"""
        if not responses:
            return {}
        
        # Trim extreme values and average
        all_weights = []
        
        for response in responses:
            model_state = response.get("model_state", {})
            weights = model_state.get("weights", [])
            
            if weights:
                # Trim extreme values
                trimmed_weights = []
                for weight in weights:
                    # Clip values to reasonable range
                    trimmed_weight = torch.clamp(weight, -10, 10)
                    trimmed_weights.append(trimmed_weight)
                
                all_weights.append(trimmed_weights)
        
        # Compute trimmed mean
        if all_weights:
            averaged_weights = []
            for i in range(len(all_weights[0])):
                layer_weights = [client_weights[i] for client_weights in all_weights]
                avg_layer = sum(layer_weights) / len(layer_weights)
                averaged_weights.append(avg_layer)
            
            return {
                "aggregated_weights": averaged_weights,
                "aggregation_method": "federated_trimmed_mean"
            }
    
    async def _weighted_averaging(self, responses: List[Dict[str, Any]], 
                           round_config: FederatedRound) -> Dict[str, Any]:
        """Weighted federated averaging"""
        if not responses:
            return {}
        
        # Calculate weights based on client data size or reputation
        weights = []
        
        for response in responses:
            client_id = response.get("client_id")
            client_info = self.client_info.get(client_id)
            
            # Weight by data size (larger datasets get more weight)
            data_weight = min(1.0, client_info.data_size / 1000000)  # Normalize by MB
            
            # Weight by reputation
            reputation_weight = client_info.reputation / 100.0
            
            # Combined weight
            combined_weight = (data_weight + reputation_weight) / 2
            
            weights.append(combined_weight)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Apply weights to model aggregation
        return await self._apply_weights_to_aggregation(responses, weights)
    
    async def _apply_weights_to_aggregation(self, responses: List[Dict[str, Any]], 
                                       weights: List[float]) -> Dict[str, Any]:
        """Apply weights to aggregation"""
        # This would modify the aggregation algorithm to use weights
        # For now, return regular federated averaging
        return await self._federated_averaging(responses)
    
    async def _secure_aggregation(self, responses: List[Dict[str, Any]], 
                              round_config: FederatedRound) -> Dict[str, Any]:
        """Secure aggregation with encryption"""
        if not responses:
            return {}
        
        # Generate aggregation secret for this round
        aggregation_secret = hashlib.sha256(
            f"{round_config.round_id}_{self.node_id}_{time.time()}".encode()
        ).hexdigest()[:32]
        
        # Encrypt model updates before aggregation
        encrypted_responses = []
        
        for response in responses:
            model_state = response.get("model_state", {})
            
            # Encrypt model state
            encrypted_state = self._encrypt_model_state(model_state, aggregation_secret)
            
            encrypted_responses.append({
                "client_id": response["client_id"],
                "round_id": round_config.round_id,
                "encrypted_model_state": encrypted_state,
                "timestamp": response.get("timestamp")
            })
        
        # Perform aggregation on encrypted data
        # In real implementation, would use homomorphic encryption
        # For now, return regular aggregation
        return await self._federated_averaging(responses)
    
    def _encrypt_model_state(self, model_state: Dict[str, Any], secret: str) -> str:
        """Encrypt model state"""
        # Mock encryption
        state_json = json.dumps(model_state, sort_keys=True)
        encrypted = hashlib.sha256(f"{state_json}{secret}".encode()).hexdigest()
        return encrypted
    
    async def _update_global_model(self, aggregated_result: Dict[str, Any]):
        """Update global model with aggregated result"""
        # In real implementation, would store in distributed storage
        logger.info(f"Updated global model with aggregated results from {len(aggregated_result.get('aggregated_weights', []))} clients")
        
        # Update metrics
        self.metrics.total_models_aggregated += 1
        self.metrics.communication_bytes += json.dumps(aggregated_result).__len__()
    
    async def _broadcast_aggregated_model(self, aggregated_result: Dict[str, Any], 
                                       round_config: FederatedRound):
        """Broadcast aggregated model back to clients"""
        for client_id in round_config.selected_clients:
            if client_id in self.client_info:
                # In real implementation, would send over network
                logger.debug(f"Broadcasting aggregated model to client {client_id}")
                
                # Update client metrics
                client = self.client_info[client_id]
                client.add_contribution()
                client.update_reputation(0.1)  # Small reward for contribution
    
    async def _update_client_metrics(self, responses: List[Dict[str, Any]], 
                                round_config: FederatedRound):
        """Update client performance metrics"""
        for response in responses:
            client_id = response.get("client_id")
            if client_id in self.client_info:
                client = self.client_info[client_id]
                
                # Update performance metrics
                metrics = response.get("metrics", {})
                
                # Update based on metrics
                if "training_time" in metrics:
                    client.performance_metrics["avg_training_time"] = (
                        client.performance_metrics.get("avg_training_time", 0) * 0.9 + 
                        metrics["training_time"] * 0.1
                    )
                
                if "accuracy" in metrics:
                    client.performance_metrics["avg_accuracy"] = (
                        client.performance_metrics.get("avg_accuracy", 0) * 0.9 + 
                        metrics["accuracy"] * 0.1
                    )
                
                # Update contribution count
                client.contribution_count += 1
    
    async def _wait_for_training_request(self) -> Optional[Dict[str, Any]]:
        """Wait for training request (client only)"""
        if self.role != FederatedRole.CLIENT:
            return None
        
        # In real implementation, would listen for network messages
        # For now, simulate receiving a request
        
        # Check if coordinator is available
        if "coordinator" not in self.network_clients:
            return None
        
        # Simulate receiving request after some delay
        await asyncio.sleep(5)
        
        # Mock training request
        return {
            "round_id": 1,
            "coordinator_id": "coordinator_001",
            "client_id": self.node_id,
            "training_config": {
                "model_type": "sign_transformer",
                "epochs": 3,
                "batch_size": 16
            },
            "timestamp": time.time()
        }
    
    async def _process_training_request(self, training_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process training request (client only)"""
        round_id = training_request["round_id"]
        training_config = training_request["training_config"]
        
        # Mock local training
        await asyncio.sleep(2)  # Simulate training time
        
        # Generate mock model state
        model_state = {
            "weights": [torch.randn(1000) for _ in range(10)],  # 10 layers
            "epoch": training_config["epochs"],
            "loss": 0.5,
            "accuracy": 0.85,
            "num_samples": 100,
            "privacy_cost": 0.1
        }
        
        # Apply differential privacy if enabled
        if training_config.get("privacy_budget", 1.0) > 0:
            model_state = self._apply_differential_privacy(model_state)
        
        # Store results
        if "training_results" not in self.client_info:
            self.client_info[self.node_id] = {"training_results": {}}
        
        self.client_info[self.node_id]["training_results"][round_id] = {
            "model_state": model_state,
            "metrics": {
                "training_time": 2.0,
                "accuracy": 0.85,
                "privacy_cost": model_state.get("privacy_cost", 0.0)
            },
            "timestamp": time.time()
        }
        
        logger.info(f"Completed training request round {round_id}")
        
        return {
            "client_id": self.node_id,
            "round_id": round_id,
            "coordinator_id": training_request["coordinator_id"],
            "model_state": model_state,
            "metrics": {
                "training_time": 2.0,
                "accuracy": 0.85,
                "privacy_cost": model_state.get("privacy_cost", 0.0)
            },
            "timestamp": time.time()
        }
    
    def _apply_differential_privacy(self, model_state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply differential privacy to model state"""
        if "noise_multiplier" not in self.config:
            return model_state
        
        noise_multiplier = self.config.get("noise_multiplier", 1.1)
        privacy_budget = self.config.get("privacy_budget", 1.0)
        
        # Add noise to weights
        noisy_weights = []
        for weight in model_state.get("weights", []):
            noise = torch.randn_like(weight) * noise_multiplier
            noisy_weight = weight + noise
            noisy_weights.append(noisy_weight)
        
        model_state["weights"] = noisy_weights
        model_state["privacy_cost"] = min(privacy_budget, 
                                        model_state.get("privacy_cost", 0.0) + noise_multiplier * 0.01)
        
        return model_state
    
    def stop(self):
        """Stop federated learning"""
        self.is_running = False
        logger.info(f"Federated learning stopped for node {self.node_id} (role: {self.role.value})")
    
    def get_status(self) -> Dict[str, Any]:
        """Get federated learning status"""
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "is_running": self.is_running,
            "current_round": self.current_round.round_id if self.current_round else None,
            "registered_clients": len(self.client_info),
            "config": self.config,
            "metrics": self.metrics,
            "network_status": {
                "coordinator_connected": "coordinator" in self.network_clients,
                "active_clients": len([c for c in self.client_info.values() 
                                     if time.time() - c.last_active < 300])
            }
        }
    
    def get_client_status(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific client"""
        return self.client_info.get(client_id)
