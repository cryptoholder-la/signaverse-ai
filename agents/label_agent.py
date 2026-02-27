# label_agent.py

import torch

class LabelAgent:

    def auto_label(self, model, data):
        with torch.no_grad():
            logits = model(data)
            probs = torch.softmax(logits, dim=-1)
            confidence, labels = torch.max(probs, dim=-1)

        return labels, confidence

    def filter_low_confidence(self, labels, confidence, threshold=0.85):
        mask = confidence > threshold
        return labels[mask]