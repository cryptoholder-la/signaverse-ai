import torch
import torchaudio

class AudioEncoder(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.mel = torchaudio.transforms.MelSpectrogram()
        self.encoder = torch.nn.Linear(128, 512)

    def forward(self, waveform):
        mel = self.mel(waveform)
        return self.encoder(mel.mean(dim=-1))