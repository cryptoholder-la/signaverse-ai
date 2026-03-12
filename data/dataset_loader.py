"""
Dataset Loader for Sign Language Data
Handles loading and preprocessing of various sign language datasets
"""

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import json
import cv2
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SignLanguageSample:
    """Single sign language data sample"""
    video_path: str
    landmarks: Optional[np.ndarray] = None
    gloss: Optional[str] = None
    text: Optional[str] = None
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    duration: Optional[float] = None
    fps: Optional[float] = None


class SignDataset(Dataset):
    """PyTorch dataset for sign language data"""
    
    def __init__(self, 
                 data_dir: str,
                 annotations_file: str,
                 transform=None,
                 target_transform=None,
                 max_samples: Optional[int] = None):
        self.data_dir = data_dir
        self.transform = transform
        self.target_transform = target_transform
        
        # Load annotations
        self.samples = self._load_annotations(annotations_file)
        
        # Limit samples if specified
        if max_samples:
            self.samples = self.samples[:max_samples]
        
        logger.info(f"Loaded {len(self.samples)} samples from {data_dir}")
    
    def _load_annotations(self, annotations_file: str) -> List[SignLanguageSample]:
        """Load annotations from file"""
        samples = []
        
        try:
            with open(annotations_file, 'r', encoding='utf-8') as f:
                if annotations_file.endswith('.json'):
                    data = json.load(f)
                    for item in data:
                        sample = SignLanguageSample(
                            video_path=os.path.join(self.data_dir, item['video_path']),
                            gloss=item.get('gloss'),
                            text=item.get('text'),
                            speaker_id=item.get('speaker_id'),
                            language=item.get('language'),
                            duration=item.get('duration'),
                            fps=item.get('fps')
                        )
                        samples.append(sample)
                else:
                    # CSV format
                    import csv
                    reader = csv.DictReader(f)
                    for row in reader:
                        sample = SignLanguageSample(
                            video_path=os.path.join(self.data_dir, row['video_path']),
                            gloss=row.get('gloss'),
                            text=row.get('text'),
                            speaker_id=row.get('speaker_id'),
                            language=row.get('language'),
                            duration=float(row.get('duration', 0)),
                            fps=float(row.get('fps', 25))
                        )
                        samples.append(sample)
        
        except Exception as e:
            logger.error(f"Error loading annotations: {e}")
            raise
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        sample = self.samples[idx]
        
        # Load video frames
        frames = self._load_video_frames(sample.video_path)
        
        # Extract landmarks if available
        if sample.landmarks is None:
            landmarks = self._extract_landmarks(frames)
        else:
            landmarks = sample.landmarks
        
        # Prepare data
        data = {
            'video_frames': frames,
            'landmarks': landmarks,
            'gloss': sample.gloss,
            'text': sample.text,
            'speaker_id': sample.speaker_id,
            'language': sample.language,
            'duration': sample.duration,
            'fps': sample.fps,
            'video_path': sample.video_path
        }
        
        # Apply transforms
        if self.transform:
            data = self.transform(data)
        
        if self.target_transform:
            data = self.target_transform(data)
        
        return data
    
    def _load_video_frames(self, video_path: str) -> np.ndarray:
        """Load video frames"""
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
        finally:
            cap.release()
        
        if not frames:
            logger.warning(f"No frames loaded from {video_path}")
            return np.array([])
        
        return np.array(frames)
    
    def _extract_landmarks(self, frames: np.ndarray) -> np.ndarray:
        """Extract pose landmarks from frames"""
        if len(frames) == 0:
            return np.array([])
        
        # Placeholder for landmark extraction
        # In real implementation, would use MediaPipe or similar
        landmarks = []
        
        for frame in frames:
            # Mock landmark extraction
            frame_landmarks = np.random.rand(21, 3)  # 21 hand keypoints
            landmarks.append(frame_landmarks)
        
        return np.array(landmarks)


class MultimodalSignDataset(Dataset):
    """Multimodal dataset with video, audio, and text"""
    
    def __init__(self, 
                 data_dir: str,
                 annotations_file: str,
                 modalities: List[str] = ['video', 'audio', 'text'],
                 max_sequence_length: int = 100):
        self.data_dir = data_dir
        self.modalities = modalities
        self.max_sequence_length = max_sequence_length
        
        # Load data
        self.samples = self._load_multimodal_data(annotations_file)
        
        logger.info(f"Loaded {len(self.samples)} multimodal samples")
    
    def _load_multimodal_data(self, annotations_file: str) -> List[Dict[str, Any]]:
        """Load multimodal data annotations"""
        samples = []
        
        with open(annotations_file, 'r') as f:
            data = json.load(f)
            
            for item in data:
                sample = {
                    'id': item.get('id'),
                    'video_path': item.get('video_path'),
                    'audio_path': item.get('audio_path'),
                    'text': item.get('text'),
                    'gloss': item.get('gloss'),
                    'language': item.get('language'),
                    'speaker_id': item.get('speaker_id'),
                    'emotion': item.get('emotion'),
                    'duration': item.get('duration')
                }
                samples.append(sample)
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        sample = self.samples[idx]
        data = {'id': sample['id']}
        
        # Load video
        if 'video' in self.modalities and sample.get('video_path'):
            data['video'] = self._load_video(
                os.path.join(self.data_dir, sample['video_path'])
            )
        
        # Load audio
        if 'audio' in self.modalities and sample.get('audio_path'):
            data['audio'] = self._load_audio(
                os.path.join(self.data_dir, sample['audio_path'])
            )
        
        # Add text
        if 'text' in self.modalities and sample.get('text'):
            data['text'] = sample['text']
        
        # Add metadata
        for key in ['gloss', 'language', 'speaker_id', 'emotion', 'duration']:
            if key in sample:
                data[key] = sample[key]
        
        return data
    
    def _load_video(self, video_path: str) -> np.ndarray:
        """Load and preprocess video"""
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Preprocess frame
                frame = cv2.resize(frame, (224, 224))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = frame.astype(np.float32) / 255.0
                frames.append(frame)
                
                if len(frames) >= self.max_sequence_length:
                    break
        finally:
            cap.release()
        
        # Pad or truncate sequence
        if len(frames) < self.max_sequence_length:
            # Pad with zeros
            padding = np.zeros((self.max_sequence_length - len(frames), 224, 224, 3))
            frames = np.concatenate([frames, padding], axis=0)
        else:
            frames = frames[:self.max_sequence_length]
        
        return frames
    
    def _load_audio(self, audio_path: str) -> np.ndarray:
        """Load and preprocess audio"""
        try:
            import librosa
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Extract features (MFCCs)
            mfccs = librosa.feature.mfcc(
                y=audio, 
                sr=sr, 
                n_mfcc=80,
                n_fft=400,
                hop_length=160
            )
            
            # Transpose to (time, features)
            mfccs = mfccs.T
            
            # Pad or truncate
            if mfccs.shape[0] < self.max_sequence_length:
                padding = np.zeros((self.max_sequence_length - mfccs.shape[0], mfccs.shape[1]))
                mfccs = np.concatenate([mfccs, padding], axis=0)
            else:
                mfccs = mfccs[:self.max_sequence_length, :]
            
            return mfccs
            
        except ImportError:
            logger.warning("librosa not available, using mock audio data")
            return np.random.rand(self.max_sequence_length, 80)


class FederatedDataset(Dataset):
    """Dataset for federated learning scenarios"""
    
    def __init__(self, 
                 client_id: str,
                 data_dir: str,
                 annotations_file: str,
                 local_samples_only: bool = True):
        self.client_id = client_id
        self.data_dir = data_dir
        self.local_samples_only = local_samples_only
        
        # Load client-specific data
        self.samples = self._load_client_data(annotations_file)
        
        logger.info(f"Client {client_id}: Loaded {len(self.samples)} samples")
    
    def _load_client_data(self, annotations_file: str) -> List[Dict[str, Any]]:
        """Load data specific to this client"""
        with open(annotations_file, 'r') as f:
            all_data = json.load(f)
        
        if self.local_samples_only:
            # Filter data for this client only
            client_data = [
                item for item in all_data 
                if item.get('client_id') == self.client_id
            ]
        else:
            # Use all data (for centralized training)
            client_data = all_data
        
        return client_data
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        sample = self.samples[idx]
        
        # Add client ID to sample
        sample['client_id'] = self.client_id
        
        return sample


def create_dataloader(dataset: Dataset, 
                   batch_size: int = 32,
                   shuffle: bool = True,
                   num_workers: int = 4,
                   pin_memory: bool = True) -> DataLoader:
    """Create a DataLoader with common settings"""
    
    return DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=True,
        persistent_workers=True if num_workers > 0 else False
    )


def split_dataset(dataset: Dataset, 
                train_ratio: float = 0.8,
                val_ratio: float = 0.1,
                test_ratio: float = 0.1,
                random_seed: int = 42) -> Tuple[Dataset, Dataset, Dataset]:
    """Split dataset into train/val/test sets"""
    
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Ratios must sum to 1.0"
    
    # Set random seed for reproducibility
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    
    # Generate random indices
    total_size = len(dataset)
    indices = np.random.permutation(total_size)
    
    # Calculate split sizes
    train_size = int(total_size * train_ratio)
    val_size = int(total_size * val_ratio)
    test_size = total_size - train_size - val_size
    
    # Split indices
    train_indices = indices[:train_size]
    val_indices = indices[train_size:train_size + val_size]
    test_indices = indices[train_size + val_size:]
    
    # Create subset datasets
    from torch.utils.data import Subset
    
    train_dataset = Subset(dataset, train_indices)
    val_dataset = Subset(dataset, val_indices)
    test_dataset = Subset(dataset, test_indices)
    
    logger.info(f"Dataset split: Train={len(train_dataset)}, "
               f"Val={len(val_dataset)}, Test={len(test_dataset)}")
    
    return train_dataset, val_dataset, test_dataset
