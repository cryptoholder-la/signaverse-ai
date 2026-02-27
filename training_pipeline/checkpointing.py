import torch
import os

def save_checkpoint(model, epoch):
    os.makedirs("experiments/checkpoints", exist_ok=True)
    torch.save(
        model.state_dict(),
        f"experiments/checkpoints/model_epoch_{epoch}.pt"
    )