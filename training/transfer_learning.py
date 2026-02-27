# training/transfer_learning.py

import torch
from models.foundation_model import FoundationSignModel


def fine_tune(base_model_path, new_dataset, config):

    model = FoundationSignModel(**config["model"])
    model.load_state_dict(torch.load(base_model_path))

    # Freeze lower layers
    for name, param in model.named_parameters():
        if "transformer.layers.0" in name:
            param.requires_grad = False

    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=1e-5
    )

    criterion = torch.nn.CrossEntropyLoss()

    for batch in new_dataset:
        output = model(sign=batch["sign"])
        loss = criterion(output["gloss"], batch["label"])

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    torch.save(model.state_dict(), "fine_tuned_model.pt")