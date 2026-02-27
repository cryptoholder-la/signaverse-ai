# training/ray_trainer.py

import ray
from ray import train
from ray.train.torch import TorchTrainer
from models.foundation_model import FoundationSignModel


def train_loop_per_worker(config):

    import torch
    from data.dataset_loader import SignDataset
    from torch.utils.data import DataLoader

    model = FoundationSignModel(**config["model"])
    model = train.torch.prepare_model(model)

    dataset = SignDataset(config["dataset"])
    loader = DataLoader(dataset, batch_size=config["batch_size"])

    optimizer = torch.optim.AdamW(model.parameters(), lr=config["lr"])
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(config["epochs"]):
        for batch in loader:
            output = model(sign=batch["sign"])
            loss = criterion(output["gloss"], batch["label"])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        train.report({"loss": loss.item()})


def run_ray_training(config):

    ray.init()

    trainer = TorchTrainer(
        train_loop_per_worker,
        train_loop_config=config,
        scaling_config=train.ScalingConfig(num_workers=4, use_gpu=True)
    )

    result = trainer.fit()
    print(result)