import torch
import torch.nn as nn

class FoundationSignModel(nn.Module):
    def __init__(self, dim=768, num_layers=12):
        super().__init__()

        self.sign_encoder = nn.Linear(258, dim)
        self.text_encoder = nn.Embedding(32000, dim)
        self.audio_encoder = nn.Linear(128, dim)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=dim,
            nhead=12,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        self.gloss_head = nn.Linear(dim, 500)
        self.text_head = nn.Linear(dim, 32000)
        self.emotion_head = nn.Linear(dim, 6)

    def forward(self, sign=None, text=None, audio=None):

        inputs = []

        if sign is not None:
            inputs.append(self.sign_encoder(sign))

        if text is not None:
            inputs.append(self.text_encoder(text))

        if audio is not None:
            inputs.append(self.audio_encoder(audio))

        x = torch.cat(inputs, dim=1)

        features = self.transformer(x)

        return {
            "gloss": self.gloss_head(features),
            "text": self.text_head(features),
            "emotion": self.emotion_head(features)
        }