# training/federated_client.py

import torch
from models.foundation_model import FoundationSignModel


class FederatedClient:

    def __init__(self, config):
        self.model = FoundationSignModel(**config["model"])

    def local_train(self, dataset):

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4)
        criterion = torch.nn.CrossEntropyLoss()

        for batch in dataset:
            output = self.model(sign=batch["sign"])
            loss = criterion(output["gloss"], batch["label"])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        return self.model.state_dict()