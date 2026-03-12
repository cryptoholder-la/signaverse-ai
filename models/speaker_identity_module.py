"""
Speaker Identity Module for Voice Cloning and Speaker Recognition
Handles speaker embedding, voice conversion, and identity preservation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class SpeakerIdentityModule(nn.Module):
    """Speaker identity extraction and synthesis"""
    
    def __init__(self, 
                 audio_dim: int = 80,  # mel spectrogram dimension
                 embedding_dim: int = 256,
                 num_speakers: Optional[int] = None):
        super().__init__()
        self.audio_dim = audio_dim
        self.embedding_dim = embedding_dim
        self.num_speakers = num_speakers
        
        # Speaker encoder
        self.speaker_encoder = nn.Sequential(
            nn.Conv1d(audio_dim, 512, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(512, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(256, embedding_dim),
            nn.Tanh()
        )
        
        # Speaker classification (if number of speakers known)
        if num_speakers:
            self.speaker_classifier = nn.Linear(embedding_dim, num_speakers)
        else:
            self.speaker_classifier = None
        
        # Voice conversion decoder
        self.voice_decoder = nn.Sequential(
            nn.Linear(embedding_dim + audio_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 1024),
            nn.ReLU(),
            nn.Linear(1024, audio_dim),
            nn.Tanh()
        )
        
        # Attention for temporal modeling
        self.temporal_attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=8,
            dropout=0.1
        )
    
    def extract_speaker_embedding(self, audio: torch.Tensor) -> torch.Tensor:
        """Extract speaker embedding from audio"""
        # Audio shape: [batch, time, freq] or [batch, freq, time]
        if audio.dim() == 3:
            if audio.size(1) == self.audio_dim:
                audio = audio.transpose(1, 2)  # [batch, freq, time]
        
        # Extract embedding
        embedding = self.speaker_encoder(audio)
        return embedding
    
    def forward(self, 
               source_audio: torch.Tensor,
               target_embedding: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Extract source speaker embedding
        source_embedding = self.extract_speaker_embedding(source_audio)
        
        if target_embedding is not None:
            # Voice conversion mode
            combined = torch.cat([source_embedding, target_embedding], dim=-1)
            converted_audio = self.voice_decoder(combined)
            
            return {
                "source_embedding": source_embedding,
                "converted_audio": converted_audio,
                "target_embedding": target_embedding
            }
        else:
            # Speaker recognition mode
            if self.speaker_classifier:
                speaker_logits = self.speaker_classifier(source_embedding)
                speaker_probs = F.softmax(speaker_logits, dim=-1)
            else:
                speaker_probs = None
            
            return {
                "speaker_embedding": source_embedding,
                "speaker_probs": speaker_probs
            }
    
    def compute_speaker_similarity(self, 
                                embedding1: torch.Tensor, 
                                embedding2: torch.Tensor) -> torch.Tensor:
        """Compute cosine similarity between speaker embeddings"""
        return F.cosine_similarity(embedding1, embedding2, dim=-1)


class MultiScaleSpeakerEncoder(nn.Module):
    """Multi-scale speaker encoder for robust identity extraction"""
    
    def __init__(self, audio_dim: int = 80, embedding_dim: int = 256):
        super().__init__()
        self.audio_dim = audio_dim
        self.embedding_dim = embedding_dim
        
        # Multi-scale convolutional layers
        self.conv_scales = nn.ModuleList([
            nn.Sequential(
                nn.Conv1d(audio_dim, 128, kernel_size=k, padding=k//2),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.MaxPool1d(2)
            ) for k in [3, 5, 7, 9]
        ])
        
        # Scale fusion
        self.scale_fusion = nn.Sequential(
            nn.Conv1d(128 * 4, 256, kernel_size=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(256, embedding_dim),
            nn.Tanh()
        )
        
        # Residual connections
        self.residual_proj = nn.Linear(audio_dim, embedding_dim)
    
    def forward(self, audio: torch.Tensor) -> torch.Tensor:
        """Forward pass with multi-scale processing"""
        if audio.dim() == 3:
            audio = audio.transpose(1, 2)  # [batch, freq, time]
        
        # Multi-scale feature extraction
        scale_features = []
        for conv in self.conv_scales:
            scale_features.append(conv(audio))
        
        # Concatenate scales
        concatenated = torch.cat(scale_features, dim=1)
        
        # Fuse scales
        fused = self.scale_fusion(concatenated)
        
        # Add residual connection
        if audio.size(-1) > 1:
            pooled = F.adaptive_avg_pool1d(audio, 1).squeeze(-1)
            residual = self.residual_proj(pooled)
            fused = fused + residual
        
        return fused


class VoiceConversionModule(nn.Module):
    """Voice conversion with content-style separation"""
    
    def __init__(self, 
                 content_dim: int = 256,
                 style_dim: int = 256,
                 audio_dim: int = 80):
        super().__init__()
        self.content_dim = content_dim
        self.style_dim = style_dim
        self.audio_dim = audio_dim
        
        # Content encoder
        self.content_encoder = nn.Sequential(
            nn.Conv1d(audio_dim, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(256, content_dim, kernel_size=3, padding=1),
            nn.ReLU()
        )
        
        # Style encoder (speaker identity)
        self.style_encoder = nn.Sequential(
            nn.Conv1d(audio_dim, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(256, style_dim, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten()
        )
        
        # Decoder with style injection
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(content_dim, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.ConvTranspose1d(256, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.ConvTranspose1d(128, audio_dim, kernel_size=3, padding=1),
            nn.Tanh()
        )
        
        # Style modulation
        self.style_modulation = nn.Sequential(
            nn.Linear(style_dim, content_dim),
            nn.Tanh()
        )
    
    def forward(self, 
               source_audio: torch.Tensor,
               target_style: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass for voice conversion"""
        if source_audio.dim() == 3:
            source_audio = source_audio.transpose(1, 2)
        
        # Extract content and style
        content = self.content_encoder(source_audio)
        source_style = self.style_encoder(source_audio)
        
        # Apply target style modulation
        style_modulation = self.style_modulation(target_style)
        modulated_content = content * style_modulation.unsqueeze(-1)
        
        # Decode
        converted_audio = self.decoder(modulated_content)
        
        return {
            "converted_audio": converted_audio.transpose(1, 2),
            "content_features": content,
            "source_style": source_style,
            "target_style": target_style
        }


class SpeakerDiarizationModule(nn.Module):
    """Speaker diarization for multi-speaker audio"""
    
    def __init__(self, 
                 embedding_dim: int = 256,
                 num_speakers: int = 2,
                 segment_length: int = 16000):  # 1 second at 16kHz
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_speakers = num_speakers
        self.segment_length = segment_length
        
        # Speaker embedding extractor
        self.speaker_encoder = MultiScaleSpeakerEncoder(
            audio_dim=80, embedding_dim=embedding_dim
        )
        
        # Clustering layer
        self.clustering_layer = nn.Parameter(
            torch.randn(num_speakers, embedding_dim)
        )
        
        # Temporal smoothing
        self.temporal_smoother = nn.Conv1d(
            num_speakers, num_speakers, kernel_size=5, padding=2
        )
    
    def forward(self, audio: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass for speaker diarization"""
        batch_size, time_steps, freq_dim = audio.size()
        
        # Segment audio
        num_segments = time_steps // self.segment_length
        segments = []
        
        for i in range(num_segments):
            start = i * self.segment_length
            end = start + self.segment_length
            segment = audio[:, start:end, :]
            segments.append(segment)
        
        if not segments:
            # Handle short audio
            segments = [audio]
        
        # Extract embeddings for each segment
        segment_embeddings = []
        for segment in segments:
            embedding = self.speaker_encoder(segment)
            segment_embeddings.append(embedding)
        
        segment_embeddings = torch.stack(segment_embeddings, dim=1)
        
        # Compute speaker probabilities
        speaker_probs = []
        for embedding in segment_embeddings:
            similarities = F.cosine_similarity(
                embedding.unsqueeze(1), 
                self.clustering_layer.unsqueeze(0), 
                dim=-1
            )
            speaker_probs.append(F.softmax(similarities, dim=-1))
        
        speaker_probs = torch.stack(speaker_probs, dim=1)
        
        # Temporal smoothing
        smoothed_probs = self.temporal_smoother(speaker_probs.transpose(1, 2)).transpose(1, 2)
        
        return {
            "speaker_probabilities": smoothed_probs,
            "segment_embeddings": segment_embeddings,
            "speaker_centers": self.clustering_layer
        }
