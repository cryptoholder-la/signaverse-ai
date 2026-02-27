import torch
import soundfile as sf
from pathlib import Path

class KittenTTSService:

    def __init__(self, model_path="models/kitten_tts.pt"):
        self.device = (
            "cuda" if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available()
            else "cpu"
        )
        self.model = torch.load(model_path, map_location=self.device)
        self.model.eval()

    def synthesize(self, text, output_path="output.wav"):
        with torch.no_grad():
            audio = self.model.generate(text)

        sf.write(output_path, audio.cpu().numpy(), 22050)
        return output_path