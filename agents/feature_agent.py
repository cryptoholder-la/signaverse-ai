# feature_agent.py

class FeatureAgent:

    def extract_sign_features(self, pose_sequence):
        return pose_sequence.mean(dim=1)

    def extract_speech_features(self, mel_spec):
        return mel_spec.mean(dim=2)

    def extract_text_features(self, token_ids):
        return token_ids.float()