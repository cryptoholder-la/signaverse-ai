# multimodal_encoder.py

import torch
import torch.nn as nn

class MultimodalEncoder(nn.Module):

    def __init__(self, text_dim=768, sign_dim=512, speech_dim=512, hidden_dim=1024):
        super().__init__()

        self.text_proj = nn.Linear(text_dim, hidden_dim)
        self.sign_proj = nn.Linear(sign_dim, hidden_dim)
        self.speech_proj = nn.Linear(speech_dim, hidden_dim)

        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=8,
                dim_feedforward=2048
            ),
            num_layers=6
        )

    def forward(self, text_emb=None, sign_emb=None, speech_emb=None):
        embeddings = []

        if text_emb is not None:
            embeddings.append(self.text_proj(text_emb))

        if sign_emb is not None:
            embeddings.append(self.sign_proj(sign_emb))

        if speech_emb is not None:
            embeddings.append(self.speech_proj(speech_emb))

        combined = torch.cat(embeddings, dim=1)
        encoded = self.transformer(combined)

        return encoded