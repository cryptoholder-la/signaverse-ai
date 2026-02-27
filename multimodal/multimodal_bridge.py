class MultimodalBridge:

    def __init__(self, sign_model, tts_service):
        self.sign_model = sign_model
        self.tts = tts_service

    def sign_to_audio(self, sign_input):
        gloss = self.sign_model.predict(sign_input)
        audio_path = self.tts.synthesize(gloss)
        return gloss, audio_path

    def text_to_sign_and_audio(self, text):
        gloss = text_to_gloss(text)
        audio_path = self.tts.synthesize(gloss)
        return gloss, audio_path