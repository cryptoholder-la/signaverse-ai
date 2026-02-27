# emotion_aware_tts.py

import torch
import torchaudio
from typing import Dict

class EmotionAwareTTS(torch.nn.Module):

    def __init__(self, base_tts_model):
        super().__init__()
        self.tts = base_tts_model
        self.emotion_embedding = torch.nn.Embedding(8, 128)

    def forward(self, text_tensor, emotion_label):
        emotion_vec = self.emotion_embedding(emotion_label)
        audio = self.tts(text_tensor, conditioning=emotion_vec)
        return audio

    def synthesize(self, text_tensor, emotion_label):
        with torch.no_grad():
            return self.forward(text_tensor, emotion_label)