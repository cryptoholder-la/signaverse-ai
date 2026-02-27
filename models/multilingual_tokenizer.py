# multilingual_tokenizer.py

import torch
from transformers import AutoTokenizer
from typing import Dict, List

class MultilingualTokenizer:

    def __init__(self, model_name="xlm-roberta-base"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.special_tokens = {
            "SIGN": "<sign>",
            "SPEECH": "<speech>",
            "EMOTION": "<emotion>"
        }
        self.tokenizer.add_tokens(list(self.special_tokens.values()))

    def encode_text(self, text: str, language: str = "en"):
        tokens = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        return tokens

    def encode_sign_sequence(self, pose_sequence: torch.Tensor):
        # Converts sign pose tensor into token-aligned embeddings
        return pose_sequence.float()

    def encode_emotion(self, emotion_label: int):
        return torch.tensor([emotion_label])

    def decode(self, token_ids):
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)