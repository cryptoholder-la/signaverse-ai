"""
Active Learning Queue for Sign Language Data Selection
Intelligently selects samples for human annotation to improve model performance
"""

import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import heapq
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Strategies for selecting samples for active learning"""
    UNCERTAINTY_SAMPLING = "uncertainty_sampling"
    DIVERSITY_SAMPLING = "diversity_sampling"
    REPRESENTATIVE_SAMPLING = "representative_sampling"
    HYBRID_SAMPLING = "hybrid_sampling"


@dataclass
class ActiveLearningSample:
    """Sample in active learning queue"""
    sample_id: str
    features: np.ndarray
    uncertainty_score: float
    diversity_score: float
    priority_score: float
    annotation_status: str = "pending"  # pending, annotated, rejected
    annotation_metadata: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0


class UncertaintySampler:
    """Samples based on model uncertainty"""
    
    def __init__(self, temperature: float = 1.0):
        self.temperature = temperature
    
    def calculate_uncertainty(self, predictions: np.ndarray) -> float:
        """Calculate prediction uncertainty"""
        # Entropy-based uncertainty
        if predictions.ndim == 1:
            # Binary classification
            prob = predictions[1] if len(predictions) > 1 else predictions[0]
            entropy = -prob * np.log(prob + 1e-8) - (1-prob) * np.log(1-prob + 1e-8)
        else:
            # Multi-class classification
            entropy = -np.sum(predictions * np.log(predictions + 1e-8))
        
        # Apply temperature scaling
        uncertainty = entropy * self.temperature
        return uncertainty
    
    def select_samples(self, 
                     features: np.ndarray,
                     predictions: np.ndarray,
                     num_samples: int) -> np.ndarray:
        """Select samples with highest uncertainty"""
        uncertainties = np.array([
            self.calculate_uncertainty(pred) for pred in predictions
        ])
        
        # Get top-k most uncertain samples
        top_indices = np.argsort(uncertainties)[-num_samples:]
        return top_indices


class DiversitySampler:
    """Samples based on diversity maximization"""
    
    def __init__(self, diversity_metric: str = "cosine"):
        self.diversity_metric = diversity_metric
    
    def calculate_diversity(self, 
                          candidate_features: np.ndarray,
                          selected_features: np.ndarray) -> float:
        """Calculate diversity score for candidate"""
        if len(selected_features) == 0:
            return 1.0
        
        # Calculate similarity to already selected samples
        if self.diversity_metric == "cosine":
            similarities = []
            for selected in selected_features:
                similarity = np.dot(candidate_features, selected) / (
                    np.linalg.norm(candidate_features) * np.linalg.norm(selected) + 1e-8
                )
                similarities.append(similarity)
            
            # Diversity = 1 - max similarity
            diversity = 1.0 - max(similarities)
        
        elif self.diversity_metric == "euclidean":
            distances = []
            for selected in selected_features:
                distance = np.linalg.norm(candidate_features - selected)
                distances.append(distance)
            
            # Diversity = min distance
            diversity = min(distances) if distances else 1.0
        
        return diversity
    
    def select_samples(self, 
                     features: np.ndarray,
                     num_samples: int) -> np.ndarray:
        """Select diverse samples using greedy algorithm"""
        selected_indices = []
        selected_features = []
        
        # Start with random sample
        first_idx = np.random.randint(len(features))
        selected_indices.append(first_idx)
        selected_features.append(features[first_idx])
        
        # Greedy selection for remaining samples
        for _ in range(num_samples - 1):
            best_idx = None
            best_score = -1
            
            for i, candidate_features in enumerate(features):
                if i in selected_indices:
                    continue
                
                diversity = self.calculate_diversity(candidate_features, selected_features)
                
                if diversity > best_score:
                    best_score = diversity
                    best_idx = i
            
            if best_idx is not None:
                selected_indices.append(best_idx)
                selected_features.append(features[best_idx])
        
        return np.array(selected_indices)


class RepresentativeSampler:
    """Samples based on representativeness"""
    
    def __init__(self, cluster_method: str = "kmeans"):
        self.cluster_method = cluster_method
    
    def cluster_samples(self, 
                      features: np.ndarray,
                      num_clusters: int) -> np.ndarray:
        """Cluster samples and select representatives"""
        if self.cluster_method == "kmeans":
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(features)
            
            # Select sample closest to each cluster center
            selected_indices = []
            for cluster_id in range(num_clusters):
                cluster_mask = cluster_labels == cluster_id
                cluster_samples = features[cluster_mask]
                cluster_indices = np.where(cluster_mask)[0]
                
                if len(cluster_samples) > 0:
                    # Find sample closest to cluster center
                    center = kmeans.cluster_centers_[cluster_id]
                    distances = np.linalg.norm(cluster_samples - center, axis=1)
                    closest_idx = cluster_indices[np.argmin(distances)]
                    selected_indices.append(closest_idx)
            
            return np.array(selected_indices)
        
        else:
            # Fallback to random sampling
            return np.random.choice(len(features), num_clusters, replace=False)
    
    def select_samples(self, 
                     features: np.ndarray,
                     num_samples: int) -> np.ndarray:
        """Select representative samples"""
        return self.cluster_samples(features, num_samples)


class ActiveLearningQueue:
    """Active learning queue for intelligent sample selection"""
    
    def __init__(self, 
                 selection_strategy: SelectionStrategy = SelectionStrategy.UNCERTAINTY_SAMPLING,
                 queue_size: int = 1000,
                 batch_size: int = 50):
        self.selection_strategy = selection_strategy
        self.queue_size = queue_size
        self.batch_size = batch_size
        
        # Queue management
        self.samples: List[ActiveLearningSample] = []
        self.sample_heap: List[Tuple[float, str]] = []  # (priority, sample_id)
        self.sample_map: Dict[str, ActiveLearningSample] = {}
        
        # Samplers
        self.uncertainty_sampler = UncertaintySampler()
        self.diversity_sampler = DiversitySampler()
        self.representative_sampler = RepresentativeSampler()
        
        # Statistics
        self.total_processed = 0
        self.total_annotated = 0
        self.total_rejected = 0
    
    def add_samples(self, 
                   sample_ids: List[str],
                   features: np.ndarray,
                   predictions: Optional[np.ndarray] = None):
        """Add samples to the queue"""
        for i, sample_id in enumerate(sample_ids):
            if len(self.samples) >= self.queue_size:
                # Remove oldest sample
                oldest = self.samples.pop(0)
                if oldest.sample_id in self.sample_map:
                    del self.sample_map[oldest.sample_id]
            
            sample_features = features[i]
            
            # Calculate scores based on strategy
            if predictions is not None:
                uncertainty_score = self.uncertainty_sampler.calculate_uncertainty(predictions[i])
            else:
                uncertainty_score = 0.5
            
            # Calculate diversity score (simplified)
            if len(self.samples) > 0:
                existing_features = np.array([s.features for s in self.samples[-10:]])
                diversity_score = self.diversity_sampler.calculate_diversity(
                    sample_features, existing_features
                )
            else:
                diversity_score = 1.0
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(
                uncertainty_score, diversity_score
            )
            
            # Create sample
            sample = ActiveLearningSample(
                sample_id=sample_id,
                features=sample_features,
                uncertainty_score=uncertainty_score,
                diversity_score=diversity_score,
                priority_score=priority_score,
                timestamp=np.time.time()
            )
            
            self.samples.append(sample)
            self.sample_map[sample_id] = sample
            
            # Add to priority queue
            heapq.heappush(self.sample_heap, (-priority_score, sample_id))
            
            self.total_processed += 1
    
    def _calculate_priority_score(self, 
                               uncertainty: float, 
                               diversity: float) -> float:
        """Calculate priority score based on strategy"""
        if self.selection_strategy == SelectionStrategy.UNCERTAINTY_SAMPLING:
            return uncertainty
        elif self.selection_strategy == SelectionStrategy.DIVERSITY_SAMPLING:
            return diversity
        elif self.selection_strategy == SelectionStrategy.HYBRID_SAMPLING:
            # Weighted combination
            return 0.6 * uncertainty + 0.4 * diversity
        else:
            # Default to uncertainty
            return uncertainty
    
    def get_next_batch(self) -> List[ActiveLearningSample]:
        """Get next batch of samples for annotation"""
        batch = []
        
        while len(batch) < self.batch_size and self.sample_heap:
            _, sample_id = heapq.heappop(self.sample_heap)
            
            if sample_id in self.sample_map:
                sample = self.sample_map[sample_id]
                if sample.annotation_status == "pending":
                    batch.append(sample)
        
        return batch
    
    def mark_annotated(self, 
                      sample_id: str, 
                      annotation_data: Dict[str, Any]):
        """Mark sample as annotated"""
        if sample_id in self.sample_map:
            sample = self.sample_map[sample_id]
            sample.annotation_status = "annotated"
            sample.annotation_metadata = annotation_data
            self.total_annotated += 1
    
    def mark_rejected(self, sample_id: str, reason: str):
        """Mark sample as rejected"""
        if sample_id in self.sample_map:
            sample = self.sample_map[sample_id]
            sample.annotation_status = "rejected"
            sample.annotation_metadata = {"rejection_reason": reason}
            self.total_rejected += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        pending_count = sum(1 for s in self.samples if s.annotation_status == "pending")
        annotated_count = sum(1 for s in self.samples if s.annotation_status == "annotated")
        rejected_count = sum(1 for s in self.samples if s.annotation_status == "rejected")
        
        return {
            "total_samples": len(self.samples),
            "pending_samples": pending_count,
            "annotated_samples": annotated_count,
            "rejected_samples": rejected_count,
            "total_processed": self.total_processed,
            "total_annotated": self.total_annotated,
            "total_rejected": self.total_rejected,
            "annotation_rate": self.total_annotated / max(self.total_processed, 1),
            "rejection_rate": self.total_rejected / max(self.total_processed, 1),
            "selection_strategy": self.selection_strategy.value
        }
    
    def get_uncertainty_distribution(self) -> Dict[str, Any]:
        """Get distribution of uncertainty scores"""
        if not self.samples:
            return {}
        
        uncertainties = [s.uncertainty_score for s in self.samples]
        
        return {
            "mean": np.mean(uncertainties),
            "std": np.std(uncertainties),
            "min": np.min(uncertainties),
            "max": np.max(uncertainties),
            "median": np.median(uncertainties),
            "percentiles": {
                "25th": np.percentile(uncertainties, 25),
                "75th": np.percentile(uncertainties, 75),
                "90th": np.percentile(uncertainties, 90)
            }
        }
    
    def export_queue_state(self, filepath: str):
        """Export queue state to file"""
        import json
        
        queue_data = {
            "samples": [
                {
                    "sample_id": s.sample_id,
                    "uncertainty_score": s.uncertainty_score,
                    "diversity_score": s.diversity_score,
                    "priority_score": s.priority_score,
                    "annotation_status": s.annotation_status,
                    "annotation_metadata": s.annotation_metadata,
                    "timestamp": s.timestamp
                }
                for s in self.samples
            ],
            "statistics": self.get_statistics(),
            "config": {
                "selection_strategy": self.selection_strategy.value,
                "queue_size": self.queue_size,
                "batch_size": self.batch_size
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(queue_data, f, indent=2)
        
        logger.info(f"Queue state exported to {filepath}")
    
    def load_queue_state(self, filepath: str):
        """Load queue state from file"""
        import json
        
        try:
            with open(filepath, 'r') as f:
                queue_data = json.load(f)
            
            # Clear current queue
            self.samples.clear()
            self.sample_heap.clear()
            self.sample_map.clear()
            
            # Load samples
            for sample_data in queue_data["samples"]:
                sample = ActiveLearningSample(
                    sample_id=sample_data["sample_id"],
                    features=np.array([]),  # Features need to be loaded separately
                    uncertainty_score=sample_data["uncertainty_score"],
                    diversity_score=sample_data["diversity_score"],
                    priority_score=sample_data["priority_score"],
                    annotation_status=sample_data["annotation_status"],
                    annotation_metadata=sample_data["annotation_metadata"],
                    timestamp=sample_data["timestamp"]
                )
                
                self.samples.append(sample)
                self.sample_map[sample.sample_id] = sample
                
                # Rebuild priority queue
                heapq.heappush(self.sample_heap, (-sample.priority_score, sample.sample_id))
            
            # Load statistics
            stats = queue_data.get("statistics", {})
            self.total_processed = stats.get("total_processed", 0)
            self.total_annotated = stats.get("total_annotated", 0)
            self.total_rejected = stats.get("total_rejected", 0)
            
            logger.info(f"Queue state loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading queue state: {e}")


class ActiveLearningManager:
    """Manages the active learning pipeline"""
    
    def __init__(self, 
                 model,
                 queue: ActiveLearningQueue,
                 data_loader):
        self.model = model
        self.queue = queue
        self.data_loader = data_loader
        
        # Performance tracking
        self.performance_history = []
    
    def update_queue_with_predictions(self, sample_ids: List[str], features: np.ndarray):
        """Update queue with model predictions"""
        self.model.eval()
        
        with torch.no_grad():
            # Get model predictions
            if isinstance(features, np.ndarray):
                features_tensor = torch.FloatTensor(features)
            else:
                features_tensor = features
            
            predictions = self.model(features_tensor)
            
            # Convert to probabilities if needed
            if hasattr(predictions, 'logits'):
                probs = torch.softmax(predictions.logits, dim=-1)
            elif hasattr(predictions, 'probabilities'):
                probs = predictions.probabilities
            else:
                probs = torch.softmax(predictions, dim=-1)
            
            predictions_np = probs.cpu().numpy()
        
        # Add to queue
        self.queue.add_samples(sample_ids, features, predictions_np)
    
    def get_annotation_batch(self) -> List[ActiveLearningSample]:
        """Get next batch for annotation"""
        return self.queue.get_next_batch()
    
    def update_model_with_annotations(self, annotated_samples: List[ActiveLearningSample]):
        """Update model with new annotations"""
        # This would integrate with the training pipeline
        # Implementation depends on specific training framework
        pass
    
    def evaluate_active_learning_performance(self) -> Dict[str, Any]:
        """Evaluate the effectiveness of active learning"""
        if not self.performance_history:
            return {}
        
        # Calculate learning efficiency
        annotation_efficiency = self.queue.total_annotated / max(self.queue.total_processed, 1)
        
        # Calculate model improvement rate
        if len(self.performance_history) > 1:
            improvement_rates = []
            for i in range(1, len(self.performance_history)):
                prev_perf = self.performance_history[i-1]
                curr_perf = self.performance_history[i]
                
                if prev_perf.get('accuracy') > 0:
                    improvement = (curr_perf['accuracy'] - prev_perf['accuracy']) / prev_perf['accuracy']
                    improvement_rates.append(improvement)
            
            avg_improvement = np.mean(improvement_rates) if improvement_rates else 0
        else:
            avg_improvement = 0
        
        return {
            "annotation_efficiency": annotation_efficiency,
            "average_improvement_rate": avg_improvement,
            "total_annotations": self.queue.total_annotated,
            "queue_utilization": len(self.queue.samples) / self.queue.queue_size
        }
