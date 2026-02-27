self.speaker_embedding = nn.Embedding(num_speakers, dim)

speaker_embedding = self.speaker_embedding(speaker_ids)
x = torch.cat([x, speaker_embedding], dim=1)

x = self.transformer(x)

return self.fc(x)



# During inference

voice_id = speaker_embedding(user_id)
tts.generate(text, speaker=voice_id)