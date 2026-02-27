# speech_to_sign.py

import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration

class SpeechToSign:

    def __init__(self, sign_model):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.processor = WhisperProcessor.from_pretrained("openai/whisper-base")
        self.speech_model = WhisperForConditionalGeneration.from_pretrained(
            "openai/whisper-base"
        ).to(self.device)

        self.sign_model = sign_model

    def transcribe(self, audio):
        inputs = self.processor(audio, return_tensors="pt").to(self.device)
        predicted_ids = self.speech_model.generate(**inputs)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription

    def text_to_sign(self, text_tensor):
        return self.sign_model.generate(text_tensor)

    def speech_to_sign(self, audio):
        text = self.transcribe(audio)
        return self.text_to_sign(text)