"""
Translation Head for Cross-Lingual Sign Language Translation
Handles translation between different sign languages and spoken languages
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class TranslationHead(nn.Module):
    """Neural machine translation head"""
    
    def __init__(self, 
                 input_dim: int,
                 vocab_size: int,
                 target_vocab_size: int,
                 hidden_dim: int = 512,
                 num_layers: int = 6,
                 num_heads: int = 8,
                 dropout: float = 0.1):
        super().__init__()
        self.input_dim = input_dim
        self.vocab_size = vocab_size
        self.target_vocab_size = target_vocab_size
        self.hidden_dim = hidden_dim
        
        # Input projection
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        
        # Transformer encoder-decoder
        self.transformer = nn.Transformer(
            d_model=hidden_dim,
            nhead=num_heads,
            num_encoder_layers=num_layers,
            num_decoder_layers=num_layers,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        
        # Output projection
        self.output_projection = nn.Linear(hidden_dim, target_vocab_size)
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(hidden_dim, dropout)
        
        # Language embeddings
        self.source_lang_embedding = nn.Embedding(vocab_size, hidden_dim)
        self.target_lang_embedding = nn.Embedding(target_vocab_size, hidden_dim)
    
    def forward(self, 
               source: torch.Tensor, 
               source_mask: Optional[torch.Tensor] = None,
               target: Optional[torch.Tensor] = None,
               target_mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        batch_size, seq_len = source.size()
        
        # Project input
        if source.dim() == 2:
            source = self.input_projection(source)
        else:
            source = source
        
        # Add positional encoding
        source = self.pos_encoding(source)
        
        if target is not None:
            # Training mode with target sequence
            target = self.pos_encoding(target)
            
            # Transformer forward
            output = self.transformer(
                src=source,
                tgt=target,
                src_mask=source_mask,
                tgt_mask=target_mask
            )
        else:
            # Inference mode
            output = self.transformer.encoder(source, mask=source_mask)
        
        # Project to vocabulary
        logits = self.output_projection(output)
        
        return {
            "logits": logits,
            "probabilities": F.softmax(logits, dim=-1)
        }


class SignToTextTranslationHead(nn.Module):
    """Specialized head for sign-to-text translation"""
    
    def __init__(self, 
                 gesture_dim: int,
                 vocab_size: int,
                 hidden_dim: int = 512,
                 num_layers: int = 4):
        super().__init__()
        self.gesture_dim = gesture_dim
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        
        # Gesture encoder
        self.gesture_encoder = nn.LSTM(
            input_size=gesture_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        
        # Text decoder
        self.text_decoder = nn.LSTM(
            input_size=hidden_dim * 2,  # bidirectional
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        # Output projection
        self.output_projection = nn.Linear(hidden_dim, vocab_size)
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,
            num_heads=8,
            dropout=0.1
        )
    
    def forward(self, 
               gestures: torch.Tensor,
               text_input: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Encode gestures
        encoded, (hidden, cell) = self.gesture_encoder(gestures)
        
        if text_input is not None:
            # Training with teacher forcing
            decoded, _ = self.text_decoder(text_input, (hidden, cell))
        else:
            # Inference mode
            decoded, _ = self.text_decoder(encoded, (hidden, cell))
        
        # Apply attention
        attended, attention_weights = self.attention(decoded, encoded, encoded)
        
        # Project to vocabulary
        logits = self.output_projection(attended)
        
        return {
            "logits": logits,
            "probabilities": F.softmax(logits, dim=-1),
            "attention_weights": attention_weights
        }


class MultilingualTranslationHead(nn.Module):
    """Multilingual translation with language identification"""
    
    def __init__(self, 
                 input_dim: int,
                 num_languages: int,
                 vocab_size_per_lang: List[int],
                 hidden_dim: int = 512):
        super().__init__()
        self.num_languages = num_languages
        self.vocab_size_per_lang = vocab_size_per_lang
        
        # Language identification
        self.lang_classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_languages),
            nn.Softmax(dim=-1)
        )
        
        # Language-specific decoders
        self.decoders = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, vocab_size)
            ) for vocab_size in vocab_size_per_lang
        ])
        
        # Shared encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, input_dim)
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Encode input
        encoded = self.encoder(x)
        
        # Identify language
        lang_probs = self.lang_classifier(encoded.mean(dim=1))
        predicted_lang = torch.argmax(lang_probs, dim=-1)
        
        # Decode with appropriate language model
        outputs = []
        for decoder in self.decoders:
            outputs.append(decoder(encoded))
        
        # Select outputs based on language prediction
        batch_size = x.size(0)
        selected_outputs = torch.stack([
            outputs[predicted_lang[i]][i] for i in range(batch_size)
        ])
        
        return {
            "outputs": selected_outputs,
            "language_probs": lang_probs,
            "predicted_language": predicted_lang,
            "all_outputs": outputs
        }


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer models"""
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class CrossLingualAlignmentHead(nn.Module):
    """Cross-lingual alignment for sign language translation"""
    
    def __init__(self, 
                 source_dim: int,
                 target_dim: int,
                 alignment_dim: int = 256):
        super().__init__()
        self.alignment_dim = alignment_dim
        
        # Projection to common space
        self.source_proj = nn.Linear(source_dim, alignment_dim)
        self.target_proj = nn.Linear(target_dim, alignment_dim)
        
        # Alignment scoring
        self.alignment_scorer = nn.Sequential(
            nn.Linear(alignment_dim * 2, alignment_dim),
            nn.ReLU(),
            nn.Linear(alignment_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, 
               source: torch.Tensor, 
               target: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass"""
        # Project to common space
        source_proj = self.source_proj(source)
        target_proj = self.target_proj(target)
        
        # Compute alignment scores
        batch_size, source_len, _ = source_proj.size()
        _, target_len, _ = target_proj.size()
        
        # Expand for pairwise comparison
        source_expanded = source_proj.unsqueeze(2).expand(-1, -1, target_len, -1)
        target_expanded = target_proj.unsqueeze(1).expand(-1, source_len, -1, -1)
        
        # Concatenate and score
        alignment_input = torch.cat([source_expanded, target_expanded], dim=-1)
        alignment_scores = self.alignment_scorer(alignment_input).squeeze(-1)
        
        return {
            "alignment_scores": alignment_scores,
            "source_projected": source_proj,
            "target_projected": target_proj
        }
