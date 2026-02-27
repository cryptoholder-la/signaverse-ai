import torch
from models.transformer_model import SignTransformer

model = SignTransformer()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
criterion = torch.nn.CTCLoss()

def train_step(batch):
    inputs, targets = batch
    
    outputs = model(inputs)
    
    loss = criterion(
        outputs.log_softmax(2),
        targets,
        input_lengths,
        target_lengths
    )
    
    loss.backward()
    optimizer.step()
    
    return loss.item()