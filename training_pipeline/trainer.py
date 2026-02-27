import torch
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.cuda.amp import GradScaler, autocast
from models.transformer_model import SignLanguageModel
from checkpointing import save_checkpoint
import mlflow

class Trainer:
    def __init__(self, config):
        self.device = self._get_device()
        self.model = SignLanguageModel().to(self.device)

        if torch.distributed.is_initialized():
            self.model = DDP(self.model, device_ids=[self.device])

        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config["lr"]
        )

        self.scaler = GradScaler()
        self.criterion = torch.nn.CTCLoss()

    def _get_device(self):
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0

        for batch in dataloader:
            inputs, targets = batch
            inputs = inputs.to(self.device)

            with autocast():
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
            self.optimizer.zero_grad()

            total_loss += loss.item()

        return total_loss / len(dataloader)
    
    def multimodal_loss(sign_embed, audio_embed):
    return torch.nn.functional.cosine_embedding_loss(
        sign_embed,
        audio_embed,
        torch.ones(sign_embed.size(0))
    )

    def train(self, dataloader, epochs):
        with mlflow.start_run():
            for epoch in range(epochs):
                loss = self.train_epoch(dataloader)
                mlflow.log_metric("loss", loss, step=epoch)
                save_checkpoint(self.model, epoch)