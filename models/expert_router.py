"""
Expert Router for Multi-Model Architecture
Routes requests to specialized expert models based on input characteristics
"""

import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class ExpertRouter(nn.Module):
    """Routes inputs to specialized expert models"""
    
    def __init__(self, input_dim: int, num_experts: int, expert_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.num_experts = num_experts
        self.expert_dim = expert_dim
        
        # Gating network for expert selection
        self.gate = nn.Sequential(
            nn.Linear(input_dim, expert_dim),
            nn.ReLU(),
            nn.Linear(expert_dim, num_experts),
            nn.Softmax(dim=-1)
        )
        
        # Expert networks (placeholder for actual expert models)
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, expert_dim),
                nn.ReLU(),
                nn.Linear(expert_dim, input_dim)
            ) for _ in range(num_experts)
        ])
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Forward pass with expert routing"""
        batch_size = x.size(0)
        
        # Get gating weights
        gate_weights = self.gate(x)
        
        # Apply experts and combine
        expert_outputs = []
        for expert in self.experts:
            expert_outputs.append(expert(x))
        
        expert_outputs = torch.stack(expert_outputs, dim=1)  # [batch, num_experts, features]
        
        # Weighted combination
        gate_weights = gate_weights.unsqueeze(-1)  # [batch, num_experts, 1]
        output = torch.sum(expert_outputs * gate_weights, dim=1)
        
        # Metadata for analysis
        metadata = {
            "expert_weights": gate_weights.detach().cpu().numpy(),
            "selected_expert": torch.argmax(gate_weights, dim=1).detach().cpu().numpy(),
            "entropy": -torch.sum(gate_weights * torch.log(gate_weights + 1e-8), dim=-1).mean().item()
        }
        
        return output, metadata
    
    def get_expert_usage_stats(self) -> Dict[str, float]:
        """Get expert usage statistics"""
        return {
            "num_experts": self.num_experts,
            "total_parameters": sum(p.numel() for p in self.parameters())
        }


class ConditionalExpertRouter(nn.Module):
    """Conditional routing based on input characteristics"""
    
    def __init__(self, input_dim: int, condition_dim: int, num_experts: int):
        super().__init__()
        self.input_dim = input_dim
        self.condition_dim = condition_dim
        self.num_experts = num_experts
        
        # Condition-based routing
        self.condition_router = nn.Sequential(
            nn.Linear(condition_dim, 128),
            nn.ReLU(),
            nn.Linear(128, num_experts),
            nn.Softmax(dim=-1)
        )
        
        # Expert networks
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, 256),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(256, input_dim)
            ) for _ in range(num_experts)
        ])
    
    def forward(self, x: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
        """Forward pass with conditional routing"""
        # Get routing weights based on condition
        route_weights = self.condition_router(condition)
        
        # Apply experts
        expert_outputs = []
        for expert in self.experts:
            expert_outputs.append(expert(x))
        
        expert_outputs = torch.stack(expert_outputs, dim=1)
        
        # Weighted combination
        route_weights = route_weights.unsqueeze(-1)
        output = torch.sum(expert_outputs * route_weights, dim=1)
        
        return output


class AdaptiveExpertRouter(nn.Module):
    """Adaptive expert routing with load balancing and performance tracking"""
    
    def __init__(self, input_dim: int, num_experts: int, expert_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.num_experts = num_experts
        self.expert_dim = expert_dim
        
        # Gating network
        self.gate = nn.Sequential(
            nn.Linear(input_dim, expert_dim),
            nn.ReLU(),
            nn.Linear(expert_dim, num_experts),
            nn.Softmax(dim=-1)
        )
        
        # Expert networks
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, expert_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(expert_dim, input_dim)
            ) for _ in range(num_experts)
        ])
        
        # Performance tracking
        self.register_buffer('expert_usage', torch.zeros(num_experts))
        self.register_buffer('expert_performance', torch.ones(num_experts))
        
        # Load balancing parameters
        self.load_balance_weight = 0.1
        self.performance_weight = 0.2
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Forward pass with adaptive routing"""
        batch_size = x.size(0)
        
        # Get initial gating weights
        gate_weights = self.gate(x)
        
        # Apply load balancing and performance adjustment
        adjusted_weights = self._adjust_weights(gate_weights)
        
        # Apply experts
        expert_outputs = []
        for expert in self.experts:
            expert_outputs.append(expert(x))
        
        expert_outputs = torch.stack(expert_outputs, dim=1)
        
        # Weighted combination
        adjusted_weights = adjusted_weights.unsqueeze(-1)
        output = torch.sum(expert_outputs * adjusted_weights, dim=1)
        
        # Update usage statistics
        selected_experts = torch.argmax(adjusted_weights.squeeze(-1), dim=1)
        for expert_id in selected_experts:
            self.expert_usage[expert_id] += 1
        
        metadata = {
            "expert_weights": adjusted_weights.detach().cpu().numpy(),
            "selected_expert": selected_experts.detach().cpu().numpy(),
            "expert_usage": self.expert_usage.detach().cpu().numpy(),
            "expert_performance": self.expert_performance.detach().cpu().numpy(),
            "load_balance_score": self._calculate_load_balance()
        }
        
        return output, metadata
    
    def _adjust_weights(self, gate_weights: torch.Tensor) -> torch.Tensor:
        """Adjust weights based on usage and performance"""
        # Normalize usage (inverse for load balancing)
        usage_penalty = self.expert_usage / (self.expert_usage.sum() + 1e-8)
        usage_adjustment = 1.0 - usage_penalty
        
        # Apply adjustments
        adjusted = gate_weights.clone()
        for i in range(self.num_experts):
            adjusted[:, i] *= (1.0 - self.load_balance_weight * usage_penalty[i])
            adjusted[:, i] *= self.performance_weight * self.expert_performance[i]
        
        # Renormalize
        adjusted = F.softmax(adjusted, dim=-1)
        return adjusted
    
    def _calculate_load_balance(self) -> float:
        """Calculate load balance score"""
        if self.expert_usage.sum() == 0:
            return 1.0
        
        usage_ratio = self.expert_usage / self.expert_usage.sum()
        entropy = -torch.sum(usage_ratio * torch.log(usage_ratio + 1e-8))
        max_entropy = torch.log(torch.tensor(self.num_experts, dtype=torch.float))
        return (entropy / max_entropy).item()
    
    def update_performance(self, expert_id: int, performance_score: float):
        """Update expert performance score"""
        # Exponential moving average
        alpha = 0.1
        self.expert_performance[expert_id] = (
            alpha * performance_score + 
            (1 - alpha) * self.expert_performance[expert_id]
        )


class HierarchicalExpertRouter(nn.Module):
    """Hierarchical expert routing for complex tasks"""
    
    def __init__(self, input_dim: int, num_levels: int, experts_per_level: List[int]):
        super().__init__()
        self.input_dim = input_dim
        self.num_levels = num_levels
        self.experts_per_level = experts_per_level
        
        # Level routers
        self.level_routers = nn.ModuleList()
        self.level_experts = nn.ModuleList()
        
        current_dim = input_dim
        
        for level in range(num_levels):
            num_experts = experts_per_level[level]
            
            # Router for this level
            router = nn.Sequential(
                nn.Linear(current_dim, 128),
                nn.ReLU(),
                nn.Linear(128, num_experts),
                nn.Softmax(dim=-1)
            )
            self.level_routers.append(router)
            
            # Experts for this level
            experts = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(current_dim, 256),
                    nn.ReLU(),
                    nn.Linear(256, current_dim)
                ) for _ in range(num_experts)
            ])
            self.level_experts.append(experts)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Forward pass through hierarchical routing"""
        current_input = x
        routing_path = []
        level_outputs = []
        
        for level in range(self.num_levels):
            # Get routing weights for current level
            route_weights = self.level_routers[level](current_input)
            
            # Apply experts at this level
            expert_outputs = []
            for expert in self.level_experts[level]:
                expert_outputs.append(expert(current_input))
            
            expert_outputs = torch.stack(expert_outputs, dim=1)
            
            # Combine outputs
            route_weights = route_weights.unsqueeze(-1)
            level_output = torch.sum(expert_outputs * route_weights, dim=1)
            
            level_outputs.append(level_output)
            routing_path.append(torch.argmax(route_weights.squeeze(-1), dim=1))
            
            # Use level output as input for next level
            current_input = level_output
        
        # Final output is the output of the last level
        final_output = level_outputs[-1]
        
        metadata = {
            "routing_path": torch.stack(routing_path).detach().cpu().numpy(),
            "level_outputs": [output.detach().cpu().numpy() for output in level_outputs],
            "num_levels": self.num_levels
        }
        
        return final_output, metadata
