# realtime_sign_to_text.py

import torch
import asyncio

class RealTimeSignToText:

    def __init__(self, model):
        self.model = model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    async def stream_inference(self, video_stream):
        async for frame_batch in video_stream:
            frame_batch = frame_batch.to(self.device)

            with torch.no_grad():
                logits = self.model(frame_batch)

            decoded = self.decode(logits)
            yield decoded

    def decode(self, logits):
        pred_ids = torch.argmax(logits, dim=-1)
        return pred_ids