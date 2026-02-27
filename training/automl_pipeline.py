# training/automl_pipeline.py

from ray import tune
from ray.train import ScalingConfig
from ray.train.torch import TorchTrainer
from training.ray_trainer import train_loop_per_worker


search_space = {
    "lr": tune.loguniform(1e-5, 1e-3),
    "batch_size": tune.choice([16, 32, 64]),
    "model": {
        "dim": tune.choice([512, 768, 1024]),
        "num_layers": tune.choice([6, 8, 12])
    }
}


def run_automl():

    tuner = tune.Tuner(
        TorchTrainer,
        param_space={
            "train_loop_per_worker": train_loop_per_worker,
            "train_loop_config": search_space,
            "scaling_config": ScalingConfig(num_workers=2, use_gpu=True)
        },
        tune_config=tune.TuneConfig(
            metric="loss",
            mode="min",
            num_samples=20
        )
    )

    results = tuner.fit()
    print("Best config:", results.get_best_result().config)