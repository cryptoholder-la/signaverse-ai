"""
Lip Sync Mapper for Avatar Animation
Maps audio features to facial animation parameters for realistic lip synchronization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class LipSyncMapper(nn.Module):
    """Maps audio features to lip movement parameters"""
    
    def __init__(self, 
                 audio_dim: int = 80,
                 lip_dim: int = 50,  # Number of lip control points
                 hidden_dim: int = 256,
                 num_layers: int = 3):
        super().__init__()
        self.audio_dim = audio_dim
        self.lip_dim = lip_dim
        self.hidden_dim = hidden_dim
        
        # Audio encoder
        self.audio_encoder = nn.Sequential(
            nn.Conv1d(audio_dim, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(256, hidden_dim, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten()
        )
        
        # Temporal modeling
        self.temporal_model = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        
        # Lip parameter decoder
        self.lip_decoder = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),  # bidirectional
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, lip_dim),
            nn.Tanh()  # Normalize to [-1, 1]
        )
        
        # Viseme classification
        self.viseme_classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.ReLU(),
            nn.Linear(128, 20),  # Common viseme set
            nn.Softmax(dim=-1)
        )
    
    def forward(self, audio: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        batch_size, time_steps, freq_dim = audio.size()
        
        # Encode audio
        if audio.dim() == 3:
            audio = audio.transpose(1, 2)  # [batch, freq, time]
        
        audio_features = self.audio_encoder(audio)
        
        # Temporal modeling
        audio_features = audio_features.unsqueeze(1).expand(-1, time_steps, -1)
        temporal_out, _ = self.temporal_model(audio_features)
        
        # Decode lip parameters
        lip_params = self.lip_decoder(temporal_out)
        
        # Classify visemes
        viseme_probs = self.viseme_classifier(temporal_out)
        
        return {
            "lip_parameters": lip_params,
            "viseme_probabilities": viseme_probs,
            "predicted_visemes": torch.argmax(viseme_probs, dim=-1),
            "temporal_features": temporal_out
        }


class PhonemeLipMapper(nn.Module):
    """Phoneme-to-lip-movement mapper with linguistic awareness"""
    
    def __init__(self, 
                 phoneme_vocab_size: int = 50,
                 lip_dim: int = 50,
                 embedding_dim: int = 128):
        super().__init__()
        self.phoneme_vocab_size = phoneme_vocab_size
        self.lip_dim = lip_dim
        self.embedding_dim = embedding_dim
        
        # Phoneme embeddings
        self.phoneme_embedding = nn.Embedding(phoneme_vocab_size, embedding_dim)
        
        # Co-articulation modeling
        self.coarticulation_model = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=embedding_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.1
        )
        
        # Lip shape generator
        self.lip_generator = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Linear(256, lip_dim),
            nn.Tanh()
        )
        
        # Transition smoother
        self.transition_smoother = nn.Conv1d(
            lip_dim, lip_dim, kernel_size=5, padding=2
        )
    
    def forward(self, phonemes: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Embed phonemes
        phoneme_embeds = self.phoneme_embedding(phonemes)
        
        # Model co-articulation
        coarticulated, _ = self.coarticulation_model(phoneme_embeds)
        
        # Generate lip shapes
        lip_shapes = self.lip_generator(coarticulated)
        
        # Smooth transitions
        smoothed = self.transition_smoother(lip_shapes.transpose(1, 2)).transpose(1, 2)
        
        return {
            "lip_shapes": smoothed,
            "raw_lip_shapes": lip_shapes,
            "coarticulated_features": coarticulated
        }


class AudioDrivenLipSync(nn.Module):
    """Audio-driven lip sync with attention mechanism"""
    
    def __init__(self, 
                 audio_dim: int = 80,
                 lip_dim: int = 50,
                 attention_dim: int = 128):
        super().__init__()
        self.audio_dim = audio_dim
        self.lip_dim = lip_dim
        self.attention_dim = attention_dim
        
        # Audio feature extractor
        self.audio_extractor = nn.Sequential(
            nn.Conv1d(audio_dim, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(128, attention_dim, kernel_size=3, padding=1),
            nn.ReLU()
        )
        
        # Lip motion encoder
        self.lip_encoder = nn.Sequential(
            nn.Linear(lip_dim, attention_dim),
            nn.ReLU(),
            nn.Linear(attention_dim, attention_dim)
        )
        
        # Cross-modal attention
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=attention_dim,
            num_heads=8,
            dropout=0.1
        )
        
        # Lip parameter predictor
        self.lip_predictor = nn.Sequential(
            nn.Linear(attention_dim, 256),
            nn.ReLU(),
            nn.Linear(256, lip_dim),
            nn.Tanh()
        )
        
        # Temporal refinement
        self.temporal_refiner = nn.Conv1d(
            lip_dim, lip_dim, kernel_size=3, padding=1
        )
    
    def forward(self, 
               audio: torch.Tensor,
               previous_lip_state: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass with optional previous state"""
        batch_size, time_steps, freq_dim = audio.size()
        
        # Extract audio features
        if audio.dim() == 3:
            audio = audio.transpose(1, 2)
        
        audio_features = self.audio_extractor(audio)  # [batch, attention_dim, time]
        audio_features = audio_features.transpose(1, 2)  # [batch, time, attention_dim]
        
        # Encode previous lip state if available
        if previous_lip_state is not None:
            lip_encoded = self.lip_encoder(previous_lip_state)
            lip_encoded = lip_encoded.unsqueeze(1).expand(-1, time_steps, -1)
            
            # Cross-modal attention
            attended, attention_weights = self.cross_attention(
                audio_features, lip_encoded, lip_encoded
            )
        else:
            attended = audio_features
            attention_weights = None
        
        # Predict lip parameters
        lip_params = self.lip_predictor(attended)
        
        # Temporal refinement
        refined = self.temporal_refiner(lip_params.transpose(1, 2)).transpose(1, 2)
        
        return {
            "lip_parameters": refined,
            "raw_lip_parameters": lip_params,
            "attention_weights": attention_weights,
            "audio_features": audio_features
        }


class VisemeBlendModule(nn.Module):
    """Blends between visemes for smooth transitions"""
    
    def __init__(self, 
                 num_visemes: int = 20,
                 lip_dim: int = 50,
                 blend_dim: int = 32):
        super().__init__()
        self.num_visemes = num_visemes
        self.lip_dim = lip_dim
        
        # Viseme library (learnable parameters)
        self.viseme_library = nn.Parameter(
            torch.randn(num_visemes, lip_dim) * 0.1
        )
        
        # Blend weight predictor
        self.blend_predictor = nn.Sequential(
            nn.Linear(lip_dim, blend_dim),
            nn.ReLU(),
            nn.Linear(blend_dim, num_visemes),
            nn.Softmax(dim=-1)
        )
        
        # Smoothness regulator
        self.smoothness_regulator = nn.Sequential(
            nn.Linear(num_visemes, blend_dim),
            nn.ReLU(),
            nn.Linear(blend_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, target_viseme: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        batch_size = target_viseme.size(0)
        
        # Predict blend weights
        blend_weights = self.blend_predictor(target_viseme)
        
        # Blend visemes
        blended = torch.matmul(blend_weights, self.viseme_library)
        
        # Predict smoothness
        smoothness = self.smoothness_regulator(blend_weights)
        
        # Apply smoothness modulation
        smoothed = blended * smoothness
        
        return {
            "blended_lip_shape": smoothed,
            "blend_weights": blend_weights,
            "smoothness_factor": smoothness,
            "nearest_viseme": self.viseme_library[target_viseme.argmax(dim=-1)]
        }


class LipSyncQualityAssessor(nn.Module):
    """Assesses quality of lip synchronization"""
    
    def __init__(self, lip_dim: int = 50, audio_dim: int = 80):
        super().__init__()
        self.lip_dim = lip_dim
        self.audio_dim = audio_dim
        
        # Synchronicity analyzer
        self.sync_analyzer = nn.Sequential(
            nn.Linear(lip_dim + audio_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
        # Temporal consistency checker
        self.consistency_checker = nn.LSTM(
            input_size=lip_dim,
            hidden_size=64,
            num_layers=1,
            batch_first=True
        )
        
        # Quality scorer
        self.quality_scorer = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, 
               lip_params: torch.Tensor,
               audio_features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        batch_size, time_steps, _ = lip_params.size()
        
        # Analyze synchronicity
        sync_scores = []
        for t in range(time_steps):
            lip_t = lip_params[:, t, :]
            audio_t = audio_features[:, min(t, audio_features.size(1)-1), :]
            
            combined = torch.cat([lip_t, audio_t], dim=-1)
            sync_score = self.sync_analyzer(combined)
            sync_scores.append(sync_score)
        
        sync_scores = torch.stack(sync_scores, dim=1)
        
        # Check temporal consistency
        consistent_out, _ = self.consistency_checker(lip_params)
        
        # Score overall quality
        quality_scores = []
        for t in range(time_steps):
            quality = self.quality_scorer(consistent_out[:, t, :])
            quality_scores.append(quality)
        
        quality_scores = torch.stack(quality_scores, dim=1)
        
        return {
            "sync_scores": sync_scores,
            "quality_scores": quality_scores,
            "avg_sync_quality": sync_scores.mean(),
            "avg_overall_quality": quality_scores.mean()
        }
