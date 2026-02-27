# training/train.py

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from models.foundation_model import FoundationSignModel
from data.dataset_loader import SignDataset
from torch.optim import AdamW
from tqdm import tqdm


def train(config):

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = FoundationSignModel(**config["model"]).to(device)
    dataset = SignDataset(config["dataset"])
    loader = DataLoader(dataset, batch_size=config["batch_size"], shuffle=True)

    optimizer = AdamW(model.parameters(), lr=config["lr"])
    criterion = nn.CrossEntropyLoss()

    for epoch in range(config["epochs"]):
        model.train()
        total_loss = 0

        for batch in tqdm(loader):
            sign = batch["sign"].to(device)
            text = batch["text"].to(device)
            target = batch["label"].to(device)

            output = model(sign=sign, text=text)
            loss = criterion(output["gloss"].view(-1, 500), target.view(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch}: {total_loss/len(loader)}")

    torch.save(model.state_dict(), config["save_path"])