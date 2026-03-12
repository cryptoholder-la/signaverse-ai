"""
Emotion Recognition Head for Multimodal Models
Detects emotions from facial expressions, gestures, and speech
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class EmotionHead(nn.Module):
    """Emotion classification head"""
    
    def __init__(self, input_dim: int, num_emotions: int = 7, dropout: float = 0.2):
        super().__init__()
        self.num_emotions = num_emotions
        
        # Emotion categories
        self.emotion_labels = [
            "neutral", "happy", "sad", "angry", 
            "surprised", "fear", "disgusted"
        ]
        
        # Emotion classification layers
        self.emotion_classifier = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_emotions)
        )
        
        # Intensity regression
        self.intensity_regressor = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
        # Valence-arousal prediction
        self.va_predictor = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 2),
            nn.Tanh()  # [-1, 1] range for valence and arousal
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Emotion classification
        emotion_logits = self.emotion_classifier(x)
        emotion_probs = F.softmax(emotion_logits, dim=-1)
        
        # Intensity prediction
        intensity = self.intensity_regressor(x)
        
        # Valence-arousal prediction
        va = self.va_predictor(x)
        valence = va[:, 0]
        arousal = va[:, 1]
        
        return {
            "emotion_logits": emotion_logits,
            "emotion_probs": emotion_probs,
            "predicted_emotion": torch.argmax(emotion_probs, dim=-1),
            "intensity": intensity,
            "valence": valence,
            "arousal": arousal
        }
    
    def get_emotion_label(self, index: int) -> str:
        """Get emotion label from index"""
        if 0 <= index < len(self.emotion_labels):
            return self.emotion_labels[index]
        return "unknown"


class MultimodalEmotionHead(nn.Module):
    """Multimodal emotion fusion head"""
    
    def __init__(self, 
                 visual_dim: int, 
                 audio_dim: int, 
                 text_dim: int,
                 num_emotions: int = 7,
                 fusion_dim: int = 256):
        super().__init__()
        self.num_emotions = num_emotions
        
        # Modality-specific encoders
        self.visual_encoder = nn.Sequential(
            nn.Linear(visual_dim, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        self.audio_encoder = nn.Sequential(
            nn.Linear(audio_dim, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        self.text_encoder = nn.Sequential(
            nn.Linear(text_dim, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Cross-modal attention
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=fusion_dim,
            num_heads=8,
            dropout=0.1
        )
        
        # Fusion and classification
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_dim * 3, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(fusion_dim, num_emotions)
        )
    
    def forward(self, 
               visual: torch.Tensor, 
               audio: torch.Tensor, 
               text: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass with multimodal fusion"""
        # Encode modalities
        visual_feat = self.visual_encoder(visual)
        audio_feat = self.audio_encoder(audio)
        text_feat = self.text_encoder(text)
        
        # Stack for cross-attention
        features = torch.stack([visual_feat, audio_feat, text_feat], dim=1)
        
        # Cross-modal attention
        attended, _ = self.cross_attention(features, features, features)
        
        # Flatten and fuse
        fused = attended.view(attended.size(0), -1)
        emotion_logits = self.fusion_layer(fused)
        emotion_probs = F.softmax(emotion_logits, dim=-1)
        
        return {
            "emotion_logits": emotion_logits,
            "emotion_probs": emotion_probs,
            "predicted_emotion": torch.argmax(emotion_probs, dim=-1),
            "attended_features": attended
        }


class EmotionCalibration(nn.Module):
    """Emotion calibration and bias correction"""
    
    def __init__(self, num_emotions: int, calibration_dim: int = 64):
        super().__init__()
        self.num_emotions = num_emotions
        
        # Calibration network
        self.calibrator = nn.Sequential(
            nn.Linear(num_emotions, calibration_dim),
            nn.ReLU(),
            nn.Linear(calibration_dim, num_emotions),
            nn.Softmax(dim=-1)
        )
        
        # Learnable temperature scaling
        self.temperature = nn.Parameter(torch.ones(1))
    
    def forward(self, emotion_probs: torch.Tensor) -> torch.Tensor:
        """Calibrate emotion probabilities"""
        # Temperature scaling
        scaled_probs = emotion_probs / self.temperature
        
        # Calibration
        calibrated = self.calibrator(scaled_probs)
        
        return calibrated


class ContinuousEmotionHead(nn.Module):
    """Continuous emotion dimension prediction"""
    
    def __init__(self, input_dim: int):
        super().__init__()
        
        # Predict continuous emotion dimensions
        self.emotion_dims = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 3)  # valence, arousal, dominance
        )
        
        # Discrete emotion classification
        self.discrete_emotions = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 7)  # 7 basic emotions
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Continuous dimensions
        continuous = self.emotion_dims(x)
        valence = continuous[:, 0]
        arousal = continuous[:, 1]
        dominance = continuous[:, 2]
        
        # Discrete emotions
        discrete_logits = self.discrete_emotions(x)
        discrete_probs = F.softmax(discrete_logits, dim=-1)
        
        return {
            "valence": torch.tanh(valence),  # [-1, 1]
            "arousal": torch.tanh(arousal),  # [-1, 1]
            "dominance": torch.tanh(dominance),  # [-1, 1]
            "discrete_logits": discrete_logits,
            "discrete_probs": discrete_probs,
            "predicted_discrete": torch.argmax(discrete_probs, dim=-1)
        }


class TemporalEmotionHead(nn.Module):
    """Temporal emotion modeling for sequences"""
    
    def __init__(self, input_dim: int, num_emotions: int = 7, hidden_dim: int = 128):
        super().__init__()
        self.num_emotions = num_emotions
        
        # Temporal modeling
        self.temporal_encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        
        # Emotion prediction
        self.emotion_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, 256),  # bidirectional
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_emotions)
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,
            num_heads=8,
            dropout=0.1
        )
        
        # Emotion change detection
        self.change_detector = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass for temporal emotion modeling"""
        # Temporal encoding
        encoded, (hidden, cell) = self.temporal_encoder(x)
        
        # Self-attention
        attended, attention_weights = self.attention(encoded, encoded, encoded)
        
        # Emotion prediction
        emotion_logits = self.emotion_predictor(attended)
        emotion_probs = F.softmax(emotion_logits, dim=-1)
        
        # Emotion change detection
        change_scores = self.change_detector(attended)
        
        return {
            "emotion_logits": emotion_logits,
            "emotion_probs": emotion_probs,
            "predicted_emotion": torch.argmax(emotion_probs, dim=-1),
            "attention_weights": attention_weights,
            "change_scores": change_scores,
            "temporal_features": attended
        }


class CrossCulturalEmotionHead(nn.Module):
    """Cross-cultural emotion recognition with cultural adaptation"""
    
    def __init__(self, input_dim: int, num_cultures: int, num_emotions: int = 7):
        super().__init__()
        self.num_cultures = num_cultures
        self.num_emotions = num_emotions
        
        # Shared emotion encoder
        self.shared_encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128)
        )
        
        # Culture-specific adapters
        self.culture_adapters = nn.ModuleList([
            nn.Sequential(
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, num_emotions)
            ) for _ in range(num_cultures)
        ])
        
        # Culture classifier
        self.culture_classifier = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, num_cultures),
            nn.Softmax(dim=-1)
        )
        
        # Cultural bias correction
        self.bias_corrector = nn.Parameter(torch.ones(num_cultures, num_emotions))
    
    def forward(self, x: torch.Tensor, culture_id: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass with cultural adaptation"""
        # Shared encoding
        shared_features = self.shared_encoder(x)
        
        # Culture classification if not provided
        if culture_id is None:
            culture_probs = self.culture_classifier(x)
            predicted_culture = torch.argmax(culture_probs, dim=-1)
        else:
            culture_probs = F.one_hot(culture_id, num_classes=self.num_cultures).float()
            predicted_culture = culture_id
        
        # Culture-specific emotion prediction
        emotion_outputs = []
        for adapter in self.culture_adapters:
            emotion_outputs.append(adapter(shared_features))
        
        emotion_outputs = torch.stack(emotion_outputs, dim=1)  # [batch, cultures, emotions]
        
        # Apply cultural bias correction
        corrected_outputs = emotion_outputs + self.bias_corrector.unsqueeze(0)
        
        # Select appropriate culture output
        batch_size = x.size(0)
        selected_outputs = corrected_outputs[torch.arange(batch_size), predicted_culture]
        
        emotion_probs = F.softmax(selected_outputs, dim=-1)
        
        return {
            "emotion_logits": selected_outputs,
            "emotion_probs": emotion_probs,
            "predicted_emotion": torch.argmax(emotion_probs, dim=-1),
            "culture_probs": culture_probs,
            "predicted_culture": predicted_culture,
            "all_emotion_outputs": corrected_outputs
        }


class EmotionEnsemble(nn.Module):
    """Ensemble of emotion recognition models"""
    
    def __init__(self, models: List[nn.Module], fusion_method: str = "weighted_average"):
        super().__init__()
        self.models = nn.ModuleList(models)
        self.fusion_method = fusion_method
        
        # Learnable weights for weighted fusion
        if fusion_method == "weighted_average":
            self.model_weights = nn.Parameter(torch.ones(len(models)) / len(models))
        elif fusion_method == "learned_fusion":
            num_emotions = models[0].num_emotions if hasattr(models[0], 'num_emotions') else 7
            self.fusion_network = nn.Sequential(
                nn.Linear(num_emotions * len(models), 128),
                nn.ReLU(),
                nn.Linear(128, num_emotions)
            )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass through ensemble"""
        model_outputs = []
        
        for model in self.models:
            output = model(x)
            if isinstance(output, dict):
                if 'emotion_probs' in output:
                    model_outputs.append(output['emotion_probs'])
                elif 'emotion_logits' in output:
                    model_outputs.append(F.softmax(output['emotion_logits'], dim=-1))
            else:
                model_outputs.append(F.softmax(output, dim=-1))
        
        # Fusion
        if self.fusion_method == "average":
            ensemble_probs = torch.stack(model_outputs, dim=0).mean(dim=0)
        elif self.fusion_method == "weighted_average":
            weights = F.softmax(self.model_weights, dim=0)
            ensemble_probs = torch.zeros_like(model_outputs[0])
            for i, output in enumerate(model_outputs):
                ensemble_probs += weights[i] * output
        elif self.fusion_method == "learned_fusion":
            concatenated = torch.cat(model_outputs, dim=-1)
            ensemble_logits = self.fusion_network(concatenated)
            ensemble_probs = F.softmax(ensemble_logits, dim=-1)
        else:
            ensemble_probs = model_outputs[0]  # fallback
        
        return {
            "ensemble_probs": ensemble_probs,
            "individual_probs": model_outputs,
            "predicted_emotion": torch.argmax(ensemble_probs, dim=-1)
        }
