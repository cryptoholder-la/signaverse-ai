# lip_sync_engine.py

import torch
import numpy as np

PHONEME_TO_VISEME = {
    "AA": 0,
    "AE": 1,
    "B": 2,
    "CH": 3,
    "D": 4,
}

class LipSyncEngine:

    def __init__(self):
        pass

    def phonemes_to_visemes(self, phoneme_sequence):
        visemes = [PHONEME_TO_VISEME.get(p, 0) for p in phoneme_sequence]
        return torch.tensor(visemes)

    def smooth_viseme_sequence(self, viseme_tensor, window=3):
        return torch.nn.functional.avg_pool1d(
            viseme_tensor.float().unsqueeze(0).unsqueeze(0),
            kernel_size=window,
            stride=1,
            padding=window//2
        ).squeeze()

    async def stream_visemes(self, phoneme_stream):
        async for phoneme_seq in phoneme_stream:
            viseme_tensor = self.phonemes_to_visemes(phoneme_seq)
            yield self.smooth_viseme_sequence(viseme_tensor)