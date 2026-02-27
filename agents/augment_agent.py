# augment_agent.py

import torch

class AugmentAgent:

    def temporal_shift(self, pose_seq):
        return torch.roll(pose_seq, shifts=1, dims=1)

    def noise_injection(self, pose_seq, scale=0.01):
        noise = torch.randn_like(pose_seq) * scale
        return pose_seq + noise