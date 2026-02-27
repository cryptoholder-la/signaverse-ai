import torch.nn as nn

class ExpertHead(nn.Module):
    def __init__(self, model_dim=512, num_classes=500):
        super().__init__()
        self.fc = nn.Linear(model_dim, num_classes)

    def forward(self, x):
        return self.fc(x)