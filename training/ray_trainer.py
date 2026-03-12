# training/ray_trainer.py

import ray
from ray import train
from ray.train.torch import TorchTrainer
from models.foundation_model import FoundationSignModel
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


def train_loop_per_worker(config):
    """Training loop for Ray distributed training"""
    import torch
    from data.dataset_loader import SignDataset
    from torch.utils.data import DataLoader
    import os

    # Set up device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Initialize model
    model = FoundationSignModel(**config["model"])
    model = train.torch.prepare_model(model)
    model.to(device)
    
    # Load dataset
    dataset = SignDataset(config["dataset"]["data_dir"], config["dataset"]["annotations"])
    
    # Split dataset
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    # Data loaders
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config["batch_size"], 
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=config["batch_size"], 
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )
    
    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=config["lr"],
        weight_decay=config.get("weight_decay", 1e-4)
    )
    
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, 
        T_max=config["epochs"],
        eta_min=config.get("min_lr", 1e-6)
    )
    
    # Loss function
    criterion = torch.nn.CrossEntropyLoss()
    
    # Training metrics
    best_val_loss = float('inf')
    patience_counter = 0
    max_patience = config.get("early_stopping_patience", 10)
    
    for epoch in range(config["epochs"]):
        model.train()
        train_loss = 0.0
        num_batches = 0
        
        # Training loop
        for batch_idx, batch in enumerate(train_loader):
            # Move data to device
            if isinstance(batch, dict):
                # Handle batch dictionary
                if "sign" in batch:
                    signs = batch["sign"].to(device)
                elif "video_frames" in batch:
                    signs = batch["video_frames"].to(device)
                else:
                    signs = batch["landmarks"].to(device)
                
                labels = batch["label"].to(device)
            else:
                # Handle tuple/list batch
                signs, labels = batch
                signs = signs.to(device)
                labels = labels.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            
            try:
                output = model(signs)
                
                # Handle different output formats
                if isinstance(output, dict):
                    if "gloss" in output:
                        logits = output["gloss"]
                    elif "logits" in output:
                        logits = output["logits"]
                    else:
                        # Use first tensor value
                        logits = next(v for v in output.values() if torch.is_tensor(v))
                else:
                    logits = output
                
                loss = criterion(logits, labels)
                
                # Backward pass
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                optimizer.step()
                
                train_loss += loss.item()
                num_batches += 1
                
                # Log progress
                if batch_idx % 10 == 0:
                    logger.info(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
                    
            except Exception as e:
                logger.error(f"Error in batch {batch_idx}: {e}")
                continue
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for batch in val_loader:
                # Move data to device
                if isinstance(batch, dict):
                    if "sign" in batch:
                        signs = batch["sign"].to(device)
                    elif "video_frames" in batch:
                        signs = batch["video_frames"].to(device)
                    else:
                        signs = batch["landmarks"].to(device)
                    
                    labels = batch["label"].to(device)
                else:
                    signs, labels = batch
                    signs = signs.to(device)
                    labels = labels.to(device)
                
                # Forward pass
                try:
                    output = model(signs)
                    
                    if isinstance(output, dict):
                        if "gloss" in output:
                            logits = output["gloss"]
                        elif "logits" in output:
                            logits = output["logits"]
                        else:
                            logits = next(v for v in output.values() if torch.is_tensor(v))
                    else:
                        logits = output
                    
                    loss = criterion(logits, labels)
                    val_loss += loss.item()
                    
                    # Calculate accuracy
                    _, predicted = torch.max(logits, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()
                    
                except Exception as e:
                    logger.error(f"Error in validation batch: {e}")
                    continue
        
        # Calculate metrics
        avg_train_loss = train_loss / max(num_batches, 1)
        avg_val_loss = val_loss / max(len(val_loader), 1)
        val_accuracy = val_correct / max(val_total, 1)
        
        # Learning rate scheduling
        scheduler.step()
        
        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            
            # Save best model
            if train.get_checkpoint():
                with train.get_checkpoint().as_directory() as checkpoint_dir:
                    torch.save(
                        {
                            'epoch': epoch,
                            'model_state_dict': model.state_dict(),
                            'optimizer_state_dict': optimizer.state_dict(),
                            'scheduler_state_dict': scheduler.state_dict(),
                            'best_val_loss': best_val_loss,
                        },
                        os.path.join(checkpoint_dir, 'best_model.pt')
                    )
        else:
            patience_counter += 1
        
        # Report metrics
        metrics = {
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_loss": avg_val_loss,
            "val_accuracy": val_accuracy,
            "learning_rate": optimizer.param_groups[0]['lr'],
            "patience_counter": patience_counter
        }
        
        train.report(metrics)
        
        # Check early stopping
        if patience_counter >= max_patience:
            logger.info(f"Early stopping at epoch {epoch}")
            break
        
        logger.info(f"Epoch {epoch}: Train Loss: {avg_train_loss:.4f}, "
                   f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_accuracy:.4f}")


def run_ray_training(config):
    """Run Ray distributed training"""
    # Initialize Ray
    if not ray.is_initialized():
        ray.init(
            num_cpus=config.get("num_cpus", 8),
            num_gpus=config.get("num_gpus", 1)
        )
    
    # Configure scaling
    scaling_config = train.ScalingConfig(
        num_workers=config.get("num_workers", 4),
        use_gpu=config.get("use_gpu", True),
        resources_per_worker={
            "CPU": config.get("cpus_per_worker", 2),
            "GPU": config.get("gpus_per_worker", 0.25)
        }
    )
    
    # Configure checkpointing
    checkpoint_config = train.CheckpointConfig(
        checkpoint_score_attribute="val_loss",
        checkpoint_score_order="min",
        num_to_keep=3,
        checkpoint_frequency=1
    )
    
    # Create trainer
    trainer = TorchTrainer(
        train_loop_per_worker,
        train_loop_config=config,
        scaling_config=scaling_config,
        checkpoint_config=checkpoint_config,
        run_config=train.RunConfig(
            name="sign_language_training",
            storage_path=config.get("checkpoint_dir", "./ray_results"),
            verbose=2
        )
    )
    
    # Start training
    logger.info("Starting Ray distributed training...")
    result = trainer.fit()
    
    # Print results
    logger.info(f"Training completed. Best checkpoint: {result.checkpoint}")
    logger.info(f"Final metrics: {result.metrics}")
    
    return result


def create_ray_config(dataset_config: Dict[str, Any],
                    model_config: Dict[str, Any],
                    training_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create Ray training configuration"""
    config = {
        "dataset": dataset_config,
        "model": model_config,
        "batch_size": training_config.get("batch_size", 32),
        "lr": training_config.get("learning_rate", 1e-4),
        "epochs": training_config.get("epochs", 100),
        "weight_decay": training_config.get("weight_decay", 1e-4),
        "min_lr": training_config.get("min_learning_rate", 1e-6),
        "early_stopping_patience": training_config.get("early_stopping_patience", 10),
        "num_workers": training_config.get("num_workers", 4),
        "use_gpu": training_config.get("use_gpu", True),
        "num_cpus": training_config.get("num_cpus", 8),
        "num_gpus": training_config.get("num_gpus", 1),
        "cpus_per_worker": training_config.get("cpus_per_worker", 2),
        "gpus_per_worker": training_config.get("gpus_per_worker", 0.25),
        "checkpoint_dir": training_config.get("checkpoint_dir", "./ray_results")
    }
    
    return config


if __name__ == "__main__":
    # Example configuration
    dataset_config = {
        "data_dir": "./data",
        "annotations": "./data/annotations.json"
    }
    
    model_config = {
        "input_dim": 256,
        "hidden_dim": 512,
        "num_classes": 100,
        "num_layers": 6
    }
    
    training_config = {
        "batch_size": 32,
        "learning_rate": 1e-4,
        "epochs": 100,
        "weight_decay": 1e-4,
        "early_stopping_patience": 10,
        "num_workers": 4,
        "use_gpu": True
    }
    
    # Create and run configuration
    config = create_ray_config(dataset_config, model_config, training_config)
    result = run_ray_training(config)
    
    print("Training completed successfully!")