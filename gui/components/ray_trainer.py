import ray
from ray import train
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig

def train_func(config):
    from trainer import Trainer
    trainer = Trainer(config)
    trainer.train()

def launch_ray_training(config):

    scaling = ScalingConfig(
        num_workers=4,
        use_gpu=True
    )

    trainer = TorchTrainer(
        train_func,
        scaling_config=scaling
    )

    result = trainer.fit()
    return result