# training/distributed_train.py

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler
from models.foundation_model import FoundationSignModel
from data.dataset_loader import SignDataset


def setup():
    dist.init_process_group("nccl")


def train_ddp(rank, world_size, config):

    setup()
    torch.cuda.set_device(rank)

    model = FoundationSignModel(**config["model"]).cuda(rank)
    model = DDP(model, device_ids=[rank])

    dataset = SignDataset(config["dataset"])
    sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank)
    loader = DataLoader(dataset, batch_size=config["batch_size"], sampler=sampler)

    optimizer = torch.optim.AdamW(model.parameters(), lr=config["lr"])
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(config["epochs"]):
        sampler.set_epoch(epoch)

        for batch in loader:
            sign = batch["sign"].cuda(rank)
            target = batch["label"].cuda(rank)

            output = model(sign=sign)
            loss = criterion(output["gloss"].view(-1, 500), target.view(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    if rank == 0:
        torch.save(model.module.state_dict(), config["save_path"])