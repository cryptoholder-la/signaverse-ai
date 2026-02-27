self.translation_head = nn.Linear(dim, vocab_size_lang)
self.gloss_head = nn.Linear(dim, vocab_size_gloss)
self.emotion_head = nn.Linear(dim, vocab_size_emotion)
self.lang_head = nn.Linear(dim, vocab_size_lang)
