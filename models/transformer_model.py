import torch
import torch.nn as nn

class SignTransformer(nn.Module):
    def __init__(self, input_dim=258, num_classes=500):
        super().__init__()
        
        self.embedding = nn.Linear(input_dim, 512)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=1024,
            dropout=0.1
        )
        
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=6
        )
        
        self.fc = nn.Linear(512, num_classes)
        
    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)
        return self.fc(x)