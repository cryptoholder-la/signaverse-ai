# cross_lingual_translation.py

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class CrossLingualTranslator:

    def __init__(self, model_name="facebook/nllb-200-distilled-600M"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)

    def translate(self, text, src_lang="eng_Latn", tgt_lang="spa_Latn"):
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        translated_tokens = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_lang]
        )
        return self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]