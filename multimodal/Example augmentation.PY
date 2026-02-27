if random.random() > 0.5:
    audio = tts.synthesize(gloss)
    audio_embedding = audio_encoder(audio)
    loss += multimodal_loss(sign_features, audio_embedding)