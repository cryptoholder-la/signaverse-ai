"""
Distributed Model Training Engine
Nodes collaboratively train models using shared datasets
"""

import asyncio
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class TrainingMode(Enum):
    """Types of distributed training"""
    FEDERATED_AVERAGING = "federated_averaging"
    FEDERATED_SGD = "federated_sgd"
    DECENTRALIZED = "decentralized"
    COLLABORATIVE = "collaborative"


class ModelArchitecture(Enum):
    """Model architectures supported"""
    SIGN_TRANSFORMER = "sign_transformer"
    MULTIMODAL_ENCODER = "multimodal_encoder"
    TRANSLATION_TRANSFORMER = "translation_transformer"
    GESTURE_RECOGNIZER = "gesture_recognizer"


@dataclass
class TrainingConfig:
    """Configuration for distributed training"""
    def __init__(self, model_type: ModelArchitecture, training_mode: TrainingMode,
                 learning_rate: float = 0.001, batch_size: int = 32,
                 epochs: int = 100, local_epochs: int = 5,
                 aggregation_frequency: int = 10, privacy_budget: float = 1.0,
                 model_save_path: str = "./models"):
        self.model_type = model_type
        self.training_mode = training_mode
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.local_epochs = local_epochs
        self.aggregation_frequency = aggregation_frequency
        self.privacy_budget = privacy_budget
        self.model_save_path = model_save_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Advanced training parameters
        self.use_mixed_precision = True
        self.gradient_clipping = 1.0
        self.weight_decay = 1e-4
        self.scheduler_type = "cosine"
        self.early_stopping_patience = 10
        
        # Federated learning specific
        self.min_clients_per_round = 2
        self.max_clients_per_round = 10
        self.client_selection_strategy = "random"  # random, uniform, weighted
        
        # Privacy settings
        self.use_differential_privacy = True
        self.noise_multiplier = 1.1
        self.max_grad_norm = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ModelUpdate:
    """Model update from federated learning"""
    def __init__(self, round_num: int, client_id: str, model_state: Dict[str, Any],
                 timestamp: float, metadata: Dict[str, Any] = None):
        self.round_num = round_num
        self.client_id = client_id
        self.model_state = model_state
        self.timestamp = timestamp
        self.metadata = metadata or {}
        self.update_id = hashlib.sha256(f"{round_num}_{client_id}_{timestamp}".encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class TrainingMetrics:
    """Metrics for training performance"""
    def __init__(self):
        self.loss_history: List[float] = []
        self.accuracy_history: List[float] = []
        self.gradient_norms: List[float] = []
        self.learning_rates: List[float] = []
        self.batch_times: List[float] = []
        self.communication_overhead: List[float] = []
        self.round_times: List[float] = []
        self.client_contributions: Dict[str, int] = {}
        
        # Federated learning specific
        self.client_selections: List[str] = []
        self.aggregation_times: List[float] = []
        self.privacy_costs: List[float] = []
    
    def update_loss(self, loss: float):
        """Update loss history"""
        self.loss_history.append(loss)
        if len(self.loss_history) > 1000:
            self.loss_history = self.loss_history[-1000:]
    
    def update_accuracy(self, accuracy: float):
        """Update accuracy history"""
        self.accuracy_history.append(accuracy)
        if len(self.accuracy_history) > 1000:
            self.accuracy_history = self.accuracy_history[-1000:]
    
    def update_gradient_norm(self, grad_norm: float):
        """Update gradient norm history"""
        self.gradient_norms.append(grad_norm)
        if len(self.gradient_norms) > 1000:
            self.gradient_norms = self.gradient_norms[-1000:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "avg_loss": np.mean(self.loss_history) if self.loss_history else 0,
            "final_loss": self.loss_history[-1] if self.loss_history else 0,
            "avg_accuracy": np.mean(self.accuracy_history) if self.accuracy_history else 0,
            "final_accuracy": self.accuracy_history[-1] if self.accuracy_history else 0,
            "avg_gradient_norm": np.mean(self.gradient_norms) if self.gradient_norms else 0,
            "total_rounds": len(self.round_times),
            "avg_round_time": np.mean(self.round_times) if self.round_times else 0,
            "total_clients": len(self.client_contributions),
            "avg_communication_overhead": np.mean(self.communication_overhead) if self.communication_overhead else 0
        }


class DistributedTrainer:
    """Advanced distributed model trainer"""
    
    def __init__(self, node_id: str, config: TrainingConfig):
        self.node_id = node_id
        self.config = config
        self.metrics = TrainingMetrics()
        self.model = None
        self.optimizer = None
        self.scheduler = None
        
        # Distributed state
        self.is_coordinator = False
        self.clients: List[str] = []
        self.current_round = 0
        self.global_model_state: Dict[str, Any] = {}
        self.client_models: Dict[str, Dict[str, Any]] = {}
        
        # Privacy and security
        self.encryption_key = self._generate_encryption_key()
        self.secure_aggregation = True
        self._cipher_suite = self._create_cipher_suite()
        
        # Performance optimization
        self.use_amp = config.use_mixed_precision and config.device.type == "cuda"
        self.gradient_accumulation_steps = 1
        
        # Background tasks
        self.training_tasks: List[asyncio.Task] = []
        self.is_training = False
    
    def _generate_encryption_key(self) -> str:
        """Generate encryption key for secure aggregation"""
        return hashlib.sha256(f"{self.node_id}_{time.time()}".encode()).hexdigest()[:32]
    
    def _create_cipher_suite(self) -> Fernet:
        """Create Fernet cipher suite for encryption/decryption"""
        # Derive a proper encryption key from the generated key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.node_id.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
        return Fernet(key)
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using the cipher suite"""
        if not self.secure_aggregation:
            return data
        try:
            return self._cipher_suite.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data  # Fallback to unencrypted
    
    def _decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using the cipher suite"""
        if not self.secure_aggregation:
            return encrypted_data
        try:
            return self._cipher_suite.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data  # Fallback to encrypted data
    
    def exchange_encryption_keys(self, client_id: str) -> str:
        """Exchange encryption keys with a client"""
        # In a real implementation, this would use a secure key exchange protocol
        # For now, return the public key fingerprint
        key_fingerprint = hashlib.sha256(self.encryption_key.encode()).hexdigest()[:16]
        logger.info(f"Exchanged encryption keys with client {client_id}, fingerprint: {key_fingerprint}")
        return key_fingerprint
    
    def verify_client_encryption(self, client_id: str, key_fingerprint: str) -> bool:
        """Verify client's encryption capability"""
        # In a real implementation, this would verify the client's key
        # For now, just log and return True
        logger.info(f"Verified encryption capability for client {client_id}")
        return True
    
    def _encrypt_model_state(self, model_state: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive parts of model state"""
        if not self.secure_aggregation:
            return model_state
        
        encrypted_state = model_state.copy()
        
        # Encrypt model weights
        if "weights" in encrypted_state and encrypted_state["weights"] is not None:
            if isinstance(encrypted_state["weights"], torch.Tensor):
                # Serialize tensor to bytes
                weights_bytes = torch.save(encrypted_state["weights"]).numpy().tobytes()
                encrypted_weights = self._encrypt_data(weights_bytes)
                encrypted_state["weights"] = base64.b64encode(encrypted_weights).decode('utf-8')
                encrypted_state["weights_encrypted"] = True
            elif isinstance(encrypted_state["weights"], list):
                # Handle list of tensors
                encrypted_weights_list = []
                for tensor in encrypted_state["weights"]:
                    if isinstance(tensor, torch.Tensor):
                        weights_bytes = torch.save(tensor).numpy().tobytes()
                        encrypted_weights = self._encrypt_data(weights_bytes)
                        encrypted_weights_list.append(base64.b64encode(encrypted_weights).decode('utf-8'))
                    else:
                        encrypted_weights_list.append(tensor)
                encrypted_state["weights"] = encrypted_weights_list
                encrypted_state["weights_encrypted"] = True
        
        return encrypted_state
    
    def _decrypt_model_state(self, encrypted_state: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive parts of model state"""
        if not self.secure_aggregation or not encrypted_state.get("weights_encrypted", False):
            return encrypted_state
        
        decrypted_state = encrypted_state.copy()
        
        # Decrypt model weights
        if "weights" in decrypted_state and decrypted_state["weights"] is not None:
            if isinstance(decrypted_state["weights"], str):
                # Single encrypted tensor
                encrypted_weights = base64.b64decode(decrypted_state["weights"].encode('utf-8'))
                decrypted_weights_bytes = self._decrypt_data(encrypted_weights)
                # Reconstruct tensor from bytes
                decrypted_state["weights"] = torch.from_numpy(np.frombuffer(decrypted_weights_bytes, dtype=np.float32))
                del decrypted_state["weights_encrypted"]
            elif isinstance(decrypted_state["weights"], list):
                # List of encrypted tensors
                decrypted_weights_list = []
                for weight_data in decrypted_state["weights"]:
                    if isinstance(weight_data, str):
                        encrypted_weights = base64.b64decode(weight_data.encode('utf-8'))
                        decrypted_weights_bytes = self._decrypt_data(encrypted_weights)
                        decrypted_weights_list.append(torch.from_numpy(np.frombuffer(decrypted_weights_bytes, dtype=np.float32)))
                    else:
                        decrypted_weights_list.append(weight_data)
                decrypted_state["weights"] = decrypted_weights_list
                del decrypted_state["weights_encrypted"]
        
        return decrypted_state
    
    def _create_model(self) -> nn.Module:
        """Create model based on configuration"""
        if self.config.model_type == ModelArchitecture.SIGN_TRANSFORMER:
            return self._create_sign_transformer()
        elif self.config.model_type == ModelArchitecture.MULTIMODAL_ENCODER:
            return self._create_multimodal_encoder()
        elif self.config.model_type == ModelArchitecture.TRANSLATION_TRANSFORMER:
            return self._create_translation_transformer()
        elif self.config.model_type == ModelArchitecture.GESTURE_RECOGNIZER:
            return self._create_gesture_recognizer()
        else:
            raise ValueError(f"Unsupported model type: {self.config.model_type}")
    
    def _create_sign_transformer(self) -> nn.Module:
        """Create sign language transformer model"""
        class SignTransformer(nn.Module):
            def __init__(self, vocab_size=1000, d_model=512, nhead=8, num_layers=6):
                super().__init__()
                self.d_model = d_model
                self.nhead = nhead
                self.num_layers = num_layers
                
                self.embedding = nn.Embedding(vocab_size, d_model)
                self.pos_encoding = nn.PositionalEncoding(d_model, max_len=500)
                
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model, nhead, dim_feedforward=2048, dropout=0.1
                )
                
                self.transformer_encoder = nn.TransformerEncoder(
                    encoder_layer, num_layers
                )
                
                self.fc_out = nn.Linear(d_model, vocab_size)
                self.dropout = nn.Dropout(0.1)
            
            def forward(self, x, mask=None):
                x = self.embedding(x) * math.sqrt(self.d_model)
                x = self.pos_encoding(x)
                x = self.transformer_encoder(x, mask)
                x = self.dropout(x)
                return self.fc_out(x)
        
        return SignTransformer()
    
    def _create_multimodal_encoder(self) -> nn.Module:
        """Create multimodal encoder model"""
        class MultimodalEncoder(nn.Module):
            def __init__(self, video_dim=512, text_dim=512, sign_dim=512, d_model=512):
                super().__init__()
                self.d_model = d_model
                
                # Modal encoders
                self.video_encoder = nn.Sequential(
                    nn.Linear(video_dim, d_model),
                    nn.ReLU(),
                    nn.Linear(d_model, d_model)
                )
                
                self.text_encoder = nn.Sequential(
                    nn.Embedding(10000, text_dim),
                    nn.LSTM(text_dim, d_model, batch_first=True)
                )
                
                self.sign_encoder = nn.Sequential(
                    nn.Linear(sign_dim, d_model),
                    nn.ReLU(),
                    nn.Linear(d_model, d_model)
                )
                
                # Fusion layer
                self.fusion = nn.MultiheadAttention(d_model, num_heads=8)
                
                # Output layers
                self.output = nn.Sequential(
                    nn.Linear(d_model, d_model),
                    nn.ReLU(),
                    nn.Linear(d_model, 256)  # Output dimension
                )
            
            def forward(self, video=None, text=None, sign=None):
                embeddings = []
                
                if video is not None:
                    video_emb = self.video_encoder(video)
                    embeddings.append(video_emb)
                
                if text is not None:
                    text_emb = self.text_encoder(text)
                    embeddings.append(text_emb)
                
                if sign is not None:
                    sign_emb = self.sign_encoder(sign)
                    embeddings.append(sign_emb)
                
                if embeddings:
                    # Stack embeddings and apply attention
                    x = torch.stack(embeddings, dim=1)
                    x = x.permute(1, 0, 2)  # (seq, batch, features)
                    attn_output, _ = self.fusion(x, x, x)
                    
                    # Use first token's output
                    fused = attn_output[:, 0, :]
                else:
                    fused = torch.zeros(1, self.d_model)
                
                return self.output(fused)
        
        return MultimodalEncoder()
    
    def _create_translation_transformer(self) -> nn.Module:
        """Create translation transformer model"""
        class TranslationTransformer(nn.Module):
            def __init__(self, src_vocab=10000, tgt_vocab=10000, d_model=512):
                super().__init__()
                self.d_model = d_model
                
                self.src_embedding = nn.Embedding(src_vocab, d_model)
                self.tgt_embedding = nn.Embedding(tgt_vocab, d_model)
                
                self.positional_encoding = nn.PositionalEncoding(d_model, max_len=500)
                
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model, nhead=8, dim_feedforward=2048, dropout=0.1
                )
                
                self.transformer_encoder = nn.TransformerEncoder(
                    encoder_layer, num_layers=6
                )
                
                decoder_layer = nn.TransformerDecoderLayer(
                    d_model, nhead=8, dim_feedforward=2048, dropout=0.1
                )
                
                self.transformer_decoder = nn.TransformerDecoder(
                    decoder_layer, num_layers=6
                )
                
                self.generator = nn.Linear(d_model, tgt_vocab)
            
            def forward(self, src, tgt):
                src_emb = self.src_embedding(src) * math.sqrt(self.d_model)
                src_emb = self.positional_encoding(src_emb)
                
                tgt_emb = self.tgt_embedding(tgt) * math.sqrt(self.d_model)
                tgt_emb = self.positional_encoding(tgt_emb)
                
                memory = self.transformer_encoder(src_emb)
                output = self.transformer_decoder(tgt_emb, memory)
                
                return self.generator(output)
        
        return TranslationTransformer()
    
    def _create_gesture_recognizer(self) -> nn.Module:
        """Create gesture recognition model"""
        class GestureRecognizer(nn.Module):
            def __init__(self, input_dim=166, hidden_dim=512, num_classes=100):
                super().__init__()
                
                # CNN for spatial features
                self.conv1 = nn.Conv2d(1, 3, 7, 1, stride=1, padding=3)
                self.bn1 = nn.BatchNorm2d(64)
                self.relu1 = nn.ReLU()
                self.pool1 = nn.MaxPool2d(2, 2)
                
                self.conv2 = nn.Conv2d(64, 3, 5, 1, stride=1, padding=2)
                self.bn2 = nn.BatchNorm2d(128)
                self.relu2 = nn.ReLU()
                self.pool2 = nn.MaxPool2d(2, 2)
                
                # LSTM for temporal features
                self.lstm = nn.LSTM(128, hidden_dim, batch_first=True)
                
                # Fully connected layers
                self.fc1 = nn.Linear(128, 256)
                self.fc2 = nn.Linear(256, 128)
                self.fc3 = nn.Linear(128, num_classes)
                self.dropout = nn.Dropout(0.5)
            
            def forward(self, x):
                # CNN layers
                x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
                x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
                
                # Reshape for LSTM
                batch_size, seq_len, features = x.size()
                x = x.permute(0, 2, 1)  # (batch, seq, features) -> (seq, batch, features)
                x = x.contiguous()
                
                # LSTM
                lstm_out, (h_n, c_n) = self.lstm(x)
                
                # Use last output
                x = lstm_out[:, -1, :]
                
                # Fully connected layers
                x = self.dropout(F.relu(self.fc1(x)))
                x = self.dropout(F.relu(self.fc2(x)))
                x = self.fc3(x)
                
                return F.log_softmax(x, dim=1)
        
        return GestureRecognizer()
    
    def _setup_training(self):
        """Setup training components"""
        self.model = self._create_model()
        self.model.to(self.config.device)
        
        # Optimizer
        if self.config.model_type in [ModelArchitecture.SIGN_TRANSFORMER, ModelArchitecture.MULTIMODAL_ENCODER]:
            self.optimizer = optim.AdamW(
                self.model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        else:
            self.optimizer = optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate
            )
        
        # Learning rate scheduler
        if self.config.scheduler_type == "cosine":
            self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=self.config.learning_rate,
                T_min=self.config.learning_rate * 0.1
            )
        
        # Mixed precision
        if self.use_amp:
            self.scaler = torch.cuda.amp.GradScaler()
    
    async def start_federated_training(self, client_data: List[Dict[str, Any]], 
                                     is_coordinator: bool = False) -> bool:
        """Start federated training"""
        try:
            self._setup_training()
            self.is_training = True
            self.is_coordinator = is_coordinator
            
            if is_coordinator:
                await self._coordinate_federated_training(client_data)
            else:
                await self._participate_in_federated_training(client_data)
            
            logger.info(f"Started federated training as {'coordinator' if is_coordinator else 'client'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start federated training: {e}")
            return False
    
    async def _coordinate_federated_training(self, client_data: List[Dict[str, Any]]):
        """Coordinate federated training as coordinator"""
        self.current_round = 0
        
        while self.current_round < self.config.epochs:
            round_start_time = time.time()
            
            # Select clients for this round
            selected_clients = self._select_clients(client_data)
            
            if not selected_clients:
                logger.warning("No clients available for training round")
                break
            
            logger.info(f"Round {self.current_round + 1}: Training with {len(selected_clients)} clients")
            
            # Collect model updates from clients
            client_updates = []
            for client_info in selected_clients:
                update = await self._request_client_update(client_info)
                if update:
                    client_updates.append(update)
                    self.metrics.client_contributions[client_info["client_id"]] = 1
            
            # Aggregate updates
            if client_updates:
                aggregated_state = await self._aggregate_client_updates(client_updates)
                
                # Update global model
                await self._update_global_model(aggregated_state)
                
                # Send updated model back to clients
                await self._broadcast_model_update(aggregated_state)
            
            # Update metrics
            round_time = time.time() - round_start_time
            self.metrics.round_times.append(round_time)
            self.metrics.client_selections.extend([c["client_id"] for c in selected_clients])
            
            self.current_round += 1
            
            # Save checkpoint
            if self.current_round % 10 == 0:
                await self._save_model_checkpoint()
            
            # Early stopping check
            if self._should_early_stop():
                logger.info("Early stopping triggered")
                break
    
    async def _participate_in_federated_training(self, client_data: Dict[str, Any]):
        """Participate in federated training as client"""
        local_epochs = self.config.local_epochs
        
        for epoch in range(local_epochs):
            epoch_start_time = time.time()
            
            # Train locally
            await self._train_local_epoch(epoch)
            
            # Send update to coordinator
            model_state = self._get_model_state()
            encrypted_state = self._encrypt_model_state(model_state)
            update = ModelUpdate(
                round_num=0,  # Will be updated by coordinator
                client_id=self.node_id,
                model_state=encrypted_state,
                timestamp=time.time()
            )
            
            # In real implementation, would send to coordinator
            logger.info(f"Completed local epoch {epoch + 1}/{local_epochs}")
            
            epoch_time = time.time() - epoch_start_time
            self.metrics.batch_times.append(epoch_time)
    
    async def _train_local_epoch(self, epoch: int):
        """Train one local epoch"""
        self.model.train()
        
        # Mock training loop
        for batch_idx in range(100):  # Mock 100 batches
            # Generate mock data
            if self.config.model_type == ModelArchitecture.GESTURE_RECOGNIZER:
                x = torch.randn(32, 166, 20, 50)  # (batch, seq, joints, frames, features)
                y = torch.randint(0, 100, (32,))
            else:
                x = torch.randn(32, 100)  # Mock sequence data
                y = torch.randint(0, 100, (32,))
            
            # Forward pass
            if self.use_amp:
                with torch.cuda.amp.autocast():
                    output = self.model(x)
                    loss = self._compute_loss(output, y)
                    self.scaler.scale(loss)
                    loss.backward()
                    self.scaler.unscale_(self.optimizer)
            else:
                output = self.model(x)
                loss = self._compute_loss(output, y)
                loss.backward()
            
            # Backward pass
            self.optimizer.step()
            
            # Update metrics
            if batch_idx % 10 == 0:
                self.metrics.update_loss(loss.item())
                self.metrics.update_gradient_norm(
                    torch.nn.utils.clip_grad_norm_(self.model.parameters()).item()
                )
    
    def _compute_loss(self, output, target):
        """Compute training loss"""
        if self.config.model_type == ModelArchitecture.GESTURE_RECOGNIZER:
            return nn.CrossEntropyLoss()(output, target)
        else:
            # Mock loss for other models
            return torch.tensor(0.5, requires_grad=True)
    
    def _select_clients(self, client_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select clients for federated round with secure key exchange"""
        available_clients = [c for c in client_data if c["available"]]
        
        if len(available_clients) <= self.config.max_clients_per_round:
            selected_clients = available_clients
        else:
            # Random sampling with minimum constraint
            if len(available_clients) < self.config.min_clients_per_round:
                selected_clients = available_clients
            else:
                # Random sample
                import random
                selected_clients = random.sample(
                    available_clients, 
                    min(self.config.max_clients_per_round, len(available_clients))
                )
        
        # Perform key exchange with selected clients
        if self.secure_aggregation:
            secure_clients = []
            for client in selected_clients:
                try:
                    key_fingerprint = self.exchange_encryption_keys(client["client_id"])
                    if self.verify_client_encryption(client["client_id"], key_fingerprint):
                        secure_clients.append(client)
                        logger.info(f"Secure encryption established with client {client['client_id']}")
                    else:
                        logger.warning(f"Failed to establish secure encryption with client {client['client_id']}")
                except Exception as e:
                    logger.error(f"Key exchange failed with client {client['client_id']}: {e}")
            
            # Use only clients with successful key exchange
            if len(secure_clients) >= self.config.min_clients_per_round:
                return secure_clients
            else:
                logger.warning("Insufficient clients with secure encryption, falling back to all selected clients")
                return selected_clients
        
        return selected_clients
    
    async def _request_client_update(self, client_info: Dict[str, Any]) -> Optional[ModelUpdate]:
        """Request model update from client"""
        # In real implementation, would make network request
        # For now, simulate client response
        
        await asyncio.sleep(0.1)  # Simulate network latency
        
        # Mock client update with encryption
        mock_state = {"weights": torch.randn(1000), "epoch": 5}
        encrypted_state = self._encrypt_model_state(mock_state)
        update = ModelUpdate(
            round_num=self.current_round,
            client_id=client_info["client_id"],
            model_state=encrypted_state,
            timestamp=time.time()
        )
        
        return update
    
    async def _aggregate_client_updates(self, updates: List[ModelUpdate]) -> Dict[str, Any]:
        """Aggregate client model updates"""
        if not updates:
            return {}
        
        start_time = time.time()
        
        # Decrypt client updates first
        decrypted_updates = []
        for update in updates:
            decrypted_state = self._decrypt_model_state(update.model_state)
            decrypted_update = ModelUpdate(
                round_num=update.round_num,
                client_id=update.client_id,
                model_state=decrypted_state,
                timestamp=update.timestamp
            )
            decrypted_updates.append(decrypted_update)
        
        # Aggregate the decrypted updates
        if self.config.training_mode == TrainingMode.FEDERATED_AVERAGING:
            # Federated averaging
            aggregated_state = self._federated_averaging(decrypted_updates)
        elif self.config.training_mode == TrainingMode.FEDERATED_SGD:
            # Federated SGD
            aggregated_state = self._federated_sgd(decrypted_updates)
        else:
            # Simple averaging
            aggregated_state = self._simple_averaging(decrypted_updates)
        
        aggregation_time = time.time() - start_time
        self.metrics.aggregation_times.append(aggregation_time)
        
        return aggregated_state
    
    def _federated_averaging(self, updates: List[ModelUpdate]) -> Dict[str, Any]:
        """Federated averaging aggregation"""
        if not updates:
            return {}
        
        # Extract weights from all clients
        all_weights = []
        num_samples = 0
        
        for update in updates:
            weights = update.model_state.get("weights")
            if weights:
                all_weights.append(weights)
                num_samples += 1
        
        if not all_weights:
            return {}
        
        # Compute weighted average
        # In real implementation, would use client data sizes as weights
        averaged_weights = []
        
        for i in range(len(all_weights[0])):
            layer_weights = []
            for client_weights in all_weights:
                layer_weights.append(client_weights[i])
            
            # Average across clients
            avg_layer = torch.mean(torch.stack(layer_weights), dim=0)
            averaged_weights.append(avg_layer)
        
        return {
            "weights": averaged_weights,
            "num_samples": num_samples,
            "aggregation_method": "federated_averaging"
        }
    
    def _federated_sgd(self, updates: List[ModelUpdate]) -> Dict[str, Any]:
        """Federated SGD aggregation"""
        # Simplified SGD update
        # In real implementation, would compute gradients on client data
        return self._simple_averaging(updates)
    
    def _simple_averaging(self, updates: List[ModelUpdate]) -> Dict[str, Any]:
        """Simple averaging of model updates"""
        if not updates:
            return {}
        
        # Average all model states
        aggregated = {}
        
        for key in updates[0].model_state.keys():
            values = [update.model_state.get(key) for update in updates if update.model_state.get(key)]
            
            if values and all(v is not None for v in values):
                # Average tensors
                if isinstance(values[0], torch.Tensor):
                    averaged = torch.mean(torch.stack(values), dim=0)
                else:
                    # Handle non-tensor types
                    averaged = values[0]  # Use first value
                
                aggregated[key] = averaged
        
        return aggregated
    
    async def _update_global_model(self, aggregated_state: Dict[str, Any]):
        """Update global model with aggregated state"""
        if not aggregated_state:
            return
        
        # Update model with aggregated weights
        if "weights" in aggregated_state and isinstance(aggregated_state["weights"], list):
            # Update model parameters
            model_dict = self.model.state_dict()
            
            for i, (key, param) in enumerate(self.model.named_parameters()):
                if i < len(aggregated_state["weights"]):
                    param.data = aggregated_state["weights"][i]
            
            self.model.load_state_dict(model_dict)
        
        self.global_model_state = aggregated_state
        
        logger.info("Updated global model with federated aggregation")
    
    async def _broadcast_model_update(self, model_state: Dict[str, Any]):
        """Broadcast model update to all clients"""
        # Encrypt the model state before broadcasting
        encrypted_state = self._encrypt_model_state(model_state)
        
        # In real implementation, would send to all clients
        logger.info("Broadcasting encrypted model update to clients")
    
    def _get_model_state(self) -> Dict[str, Any]:
        """Get current model state"""
        if self.model is None:
            return {}
        
        state = {
            "weights": [param.data.clone() for param in self.model.parameters()],
            "optimizer_state": {
                "state_dict": self.optimizer.state_dict(),
                "param_groups": self.optimizer.param_groups
            },
            "model_config": self.config.to_dict(),
            "training_mode": self.config.training_mode
        }
        
        return state
    
    def _should_early_stop(self) -> bool:
        """Check if training should stop early"""
        if len(self.metrics.accuracy_history) < 10:
            return False
        
        # Check if loss hasn't improved in last 5 epochs
        recent_losses = self.metrics.loss_history[-5:]
        if len(recent_losses) < 5:
            return False
        
        return all(recent_losses[i] >= recent_losses[i+1] 
               for i in range(len(recent_losses)-1))
    
    async def _save_model_checkpoint(self):
        """Save model checkpoint"""
        if not self.model:
            return
        
        checkpoint = {
            "model_state": self._get_model_state(),
            "metrics": self.metrics.get_summary(),
            "round": self.current_round,
            "timestamp": time.time(),
            "node_id": self.node_id
        }
        
        checkpoint_path = f"{self.config.model_save_path}/checkpoint_round_{self.current_round}.json"
        
        try:
            import json
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            logger.info(f"Saved checkpoint to {checkpoint_path}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    async def start_decentralized_training(self, dataset_path: str) -> bool:
        """Start decentralized training with shared dataset"""
        try:
            self._setup_training()
            self.is_training = True
            
            # Load dataset (mock)
            dataset = self._load_dataset(dataset_path)
            
            for epoch in range(self.config.epochs):
                epoch_start_time = time.time()
                
                # Train on dataset
                for batch in dataset:
                    # Process batch
                    inputs, targets = batch
                    loss = self._compute_loss(self.model(inputs), targets)
                    
                    if self.use_amp:
                        with torch.cuda.amp.autocast():
                            output = self.model(inputs)
                            loss = self.scaler.scale(loss)
                            loss.backward()
                            self.scaler.unscale_(self.optimizer)
                    else:
                        output = self.model(inputs)
                        loss.backward()
                    
                    self.optimizer.step()
                    
                    # Update metrics
                    self.metrics.update_loss(loss.item())
                
                epoch_time = time.time() - epoch_start_time
                logger.info(f"Epoch {epoch + 1}/{self.config.epochs}: Loss {self.metrics.loss_history[-1]:.4f}")
                
                # Early stopping
                if self._should_early_stop():
                    logger.info("Early stopping triggered")
                    break
            
            # Save final model
            await self._save_model_checkpoint()
            
            logger.info("Completed decentralized training")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start decentralized training: {e}")
            return False
    
    def _load_dataset(self, dataset_path: str) -> List[Any]:
        """Load dataset for training"""
        # Mock dataset loading
        # In real implementation, would load from file or distributed storage
        dataset = []
        
        for i in range(1000):  # Mock 1000 samples
            if self.config.model_type == ModelArchitecture.GESTURE_RECOGNIZER:
                # Gesture recognition data
                x = torch.randn(20, 166, 50, 50)  # (batch, joints, frames, features)
                y = torch.randint(0, 100, (20,))
            else:
                # Text or sequence data
                x = torch.randint(1, 1000, (32,))
                y = torch.randint(0, 1000, (32,))
            
            dataset.append((x, y))
        
        return dataset
    
    def stop_training(self):
        """Stop training"""
        self.is_training = False
        
        # Cancel training tasks
        for task in self.training_tasks:
            task.cancel()
        
        self.training_tasks.clear()
        logger.info("Training stopped")
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            "is_training": self.is_training,
            "is_coordinator": self.is_coordinator,
            "current_round": self.current_round,
            "config": self.config.to_dict(),
            "metrics": self.metrics.get_summary(),
            "model_type": self.config.model_type.value,
            "global_model_state": self.global_model_state
        }
