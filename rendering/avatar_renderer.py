"""
3D Avatar Sign-Language Renderer
Real-time 3D avatar rendering for sign language translation
"""

import asyncio
import json
import time
import hashlib
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

logger = logging.getLogger(__name__)


class AvatarType(Enum):
    """Types of 3D avatars"""
    HUMANOID = "humanoid"
    CARTOON = "cartoon"
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    MINIMALIST = "minimalist"


class SignLanguage(Enum):
    """Supported sign languages"""
    ASL = "asl"  # American Sign Language
    BSL = "bsl"  # British Sign Language
    ISL = "isl"  # International Sign Language
    JSL = "jsl"  # Japanese Sign Language
    CSL = "csl"  # Chinese Sign Language
    FSL = "fsl"  # French Sign Language


class RenderingQuality(Enum):
    """Rendering quality levels"""
    LOW = "low"      # 480p, 30fps
    MEDIUM = "medium"  # 720p, 30fps
    HIGH = "high"      # 1080p, 60fps
    ULTRA = "ultra"    # 4K, 60fps


class AnimationState(Enum):
    """Animation states"""
    IDLE = "idle"
    SIGNING = "signing"
    TRANSITIONING = "transitioning"
    GESTURING = "gesturing"
    FACIAL_EXPRESSION = "facial_expression"


@dataclass
class PoseData:
    """3D pose data for avatar"""
    def __init__(self, timestamp: float, joints: Dict[str, np.ndarray],
                 facial_expressions: Dict[str, float] = None,
                 hand_shapes: Dict[str, np.ndarray] = None,
                 body_pose: np.ndarray = None):
        self.timestamp = timestamp
        self.joints = joints
        self.facial_expressions = facial_expressions or {}
        self.hand_shapes = hand_shapes or {}
        self.body_pose = body_pose
        self.confidence = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "joints": {k: v.tolist() for k, v in self.joints.items()},
            "facial_expressions": self.facial_expressions,
            "hand_shapes": {k: v.tolist() for k, v in self.hand_shapes.items()},
            "body_pose": self.body_pose.tolist() if self.body_pose is not None else None,
            "confidence": self.confidence
        }


@dataclass
class SignSequence:
    """Sequence of signs for animation"""
    def __init__(self, sequence_id: str, signs: List[str], 
                 durations: List[float], transitions: List[Dict[str, Any]] = None,
                 metadata: Dict[str, Any] = None):
        self.sequence_id = sequence_id
        self.signs = signs
        self.durations = durations
        self.transitions = transitions or []
        self.metadata = metadata or {}
        self.total_duration = sum(durations)
        self.created_at = time.time()
    
    def add_sign(self, sign: str, duration: float, transition: Dict[str, Any] = None):
        """Add a sign to the sequence"""
        self.signs.append(sign)
        self.durations.append(duration)
        if transition:
            self.transitions.append(transition)
        self.total_duration = sum(self.durations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class AvatarConfiguration:
    """Avatar rendering configuration"""
    def __init__(self, avatar_id: str, avatar_type: AvatarType,
                 sign_language: SignLanguage, quality: RenderingQuality,
                 model_path: str = None, texture_path: str = None,
                 animation_speed: float = 1.0, facial_animation: bool = True,
                 hand_detail: bool = True, body_tracking: bool = True):
        self.avatar_id = avatar_id
        self.avatar_type = avatar_type
        self.sign_language = sign_language
        self.quality = quality
        self.model_path = model_path
        self.texture_path = texture_path
        self.animation_speed = animation_speed
        self.facial_animation = facial_animation
        self.hand_detail = hand_detail
        self.body_tracking = body_tracking
        
        # Rendering parameters
        self.lighting_intensity = 1.0
        self.shadow_quality = "medium"
        self.anti_aliasing = "fxaa"
        self.background_color = [0.1, 0.1, 0.1, 1.0]  # RGBA
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class SignLanguageLibrary:
    """Library of sign language animations and poses"""
    
    def __init__(self, sign_language: SignLanguage):
        self.sign_language = sign_language
        self.signs: Dict[str, Dict[str, Any]] = {}
        self.transitions: Dict[str, Dict[str, Any]] = {}
        self.facial_expressions: Dict[str, Dict[str, Any]] = {}
        self.hand_shapes: Dict[str, Dict[str, Any]] = {}
        
        # Load default signs
        self._load_default_signs()
    
    def _load_default_signs(self):
        """Load default sign language data"""
        # Common signs with pose data
        default_signs = {
            "hello": {
                "duration": 1.5,
                "joints": {
                    "right_hand": np.array([0.3, 0.2, 0.1]),
                    "left_hand": np.array([-0.3, 0.2, 0.1]),
                    "right_elbow": np.array([0.2, 0.4, 0.0]),
                    "left_elbow": np.array([-0.2, 0.4, 0.0]),
                    "head": np.array([0.0, 0.0, 0.1])
                },
                "facial_expressions": {
                    "smile": 0.8,
                    "eye_contact": 1.0
                }
            },
            "thank_you": {
                "duration": 2.0,
                "joints": {
                    "right_hand": np.array([0.4, 0.1, 0.2]),
                    "left_hand": np.array([-0.2, 0.3, 0.1]),
                    "right_elbow": np.array([0.3, 0.5, 0.1]),
                    "left_elbow": np.array([-0.1, 0.4, 0.0]),
                    "head": np.array([0.0, 0.1, 0.0])
                },
                "facial_expressions": {
                    "smile": 0.6,
                    "eye_contact": 0.9
                }
            },
            "please": {
                "duration": 1.8,
                "joints": {
                    "right_hand": np.array([0.2, 0.3, 0.0]),
                    "left_hand": np.array([-0.1, 0.3, 0.0]),
                    "right_elbow": np.array([0.1, 0.4, 0.0]),
                    "left_elbow": np.array([-0.1, 0.4, 0.0]),
                    "head": np.array([0.0, -0.1, 0.0])
                },
                "facial_expressions": {
                    "eyebrows_raised": 0.7,
                    "eye_contact": 0.8
                }
            },
            "sorry": {
                "duration": 2.2,
                "joints": {
                    "right_hand": np.array([0.1, 0.4, 0.1]),
                    "left_hand": np.array([-0.1, 0.4, 0.1]),
                    "right_elbow": np.array([0.0, 0.5, 0.0]),
                    "left_elbow": np.array([0.0, 0.5, 0.0]),
                    "head": np.array([0.0, -0.2, 0.0])
                },
                "facial_expressions": {
                    "sad": 0.8,
                    "eye_contact": 0.6
                }
            },
            "yes": {
                "duration": 1.0,
                "joints": {
                    "right_hand": np.array([0.2, 0.1, 0.1]),
                    "left_hand": np.array([-0.2, 0.1, 0.1]),
                    "head": np.array([0.0, 0.1, 0.0])
                },
                "facial_expressions": {
                    "nod": 0.9,
                    "eye_contact": 1.0
                }
            },
            "no": {
                "duration": 1.0,
                "joints": {
                    "right_hand": np.array([0.1, 0.2, 0.0])),
                    "left_hand": np.array([-0.1, 0.2, 0.0])),
                    "head": np.array([0.0, -0.1, 0.0])
                },
                "facial_expressions": {
                    "shake": 0.9,
                    "eye_contact": 1.0
                }
            }
        }
        
        self.signs = default_signs
        
        # Load transitions
        self.transitions = {
            "hello_to_thank_you": {
                "duration": 0.5,
                "interpolation": "smooth"
            },
            "thank_you_to_please": {
                "duration": 0.3,
                "interpolation": "linear"
            }
        }
        
        # Load facial expressions
        self.facial_expressions = {
            "neutral": {"intensity": 0.0},
            "smile": {"intensity": 0.8},
            "sad": {"intensity": 0.7},
            "surprised": {"intensity": 0.6},
            "eyebrows_raised": {"intensity": 0.5},
            "nod": {"intensity": 0.9},
            "shake": {"intensity": 0.9}
        }
    
    def get_sign(self, sign_name: str) -> Optional[Dict[str, Any]]:
        """Get sign data by name"""
        return self.signs.get(sign_name)
    
    def get_transition(self, from_sign: str, to_sign: str) -> Optional[Dict[str, Any]]:
        """Get transition between two signs"""
        transition_key = f"{from_sign}_to_{to_sign}"
        return self.transitions.get(transition_key)
    
    def add_custom_sign(self, sign_name: str, sign_data: Dict[str, Any]):
        """Add a custom sign"""
        self.signs[sign_name] = sign_data
        logger.info(f"Added custom sign: {sign_name}")


class AvatarRenderer:
    """3D avatar renderer for sign language"""
    
    def __init__(self, config: AvatarConfiguration):
        self.config = config
        
        # Rendering state
        self.is_rendering = False
        self.current_animation_state = AnimationState.IDLE
        self.current_pose = None
        self.animation_queue: List[SignSequence] = []
        
        # Avatar model
        self.avatar_model = None
        self.sign_library = SignLanguageLibrary(config.sign_language)
        
        # Rendering engine
        self.render_width = self._get_resolution_width()
        self.render_height = self._get_resolution_height()
        self.fps = self._get_fps()
        self.frame_time = 1.0 / self.fps
        
        # Performance metrics
        self.metrics = {
            "frames_rendered": 0,
            "signs_rendered": 0,
            "average_render_time": 0.0,
            "dropped_frames": 0,
            "animation_transitions": 0
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.on_sign_started = None
        self.on_sign_completed = None
        self.on_animation_state_changed = None
    
    def _get_resolution_width(self) -> int:
        """Get rendering width based on quality"""
        quality_settings = {
            RenderingQuality.LOW: 854,
            RenderingQuality.MEDIUM: 1280,
            RenderingQuality.HIGH: 1920,
            RenderingQuality.ULTRA: 3840
        }
        return quality_settings.get(self.config.quality, 1280)
    
    def _get_resolution_height(self) -> int:
        """Get rendering height based on quality"""
        quality_settings = {
            RenderingQuality.LOW: 480,
            RenderingQuality.MEDIUM: 720,
            RenderingQuality.HIGH: 1080,
            RenderingQuality.ULTRA: 2160
        }
        return quality_settings.get(self.config.quality, 720)
    
    def _get_fps(self) -> int:
        """Get FPS based on quality"""
        fps_settings = {
            RenderingQuality.LOW: 30,
            RenderingQuality.MEDIUM: 30,
            RenderingQuality.HIGH: 60,
            RenderingQuality.ULTRA: 60
        }
        return fps_settings.get(self.config.quality, 30)
    
    async def start(self) -> bool:
        """Start the avatar renderer"""
        try:
            self.is_running = True
            
            # Initialize avatar model
            await self._initialize_avatar_model()
            
            # Start rendering loop
            self.background_tasks = [
                asyncio.create_task(self._rendering_loop()),
                asyncio.create_task(self._animation_loop()),
                asyncio.create_task(self._metrics_loop())
            ]
            
            logger.info(f"Avatar renderer started: {self.config.avatar_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start avatar renderer: {e}")
            return False
    
    async def stop(self):
        """Stop the avatar renderer"""
        self.is_running = False
        self.is_rendering = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Avatar renderer stopped")
    
    async def _initialize_avatar_model(self):
        """Initialize the 3D avatar model"""
        # Mock avatar model initialization
        # In real implementation, would load 3D model from file
        self.avatar_model = {
            "loaded": True,
            "joint_count": 25,
            "bone_count": 50,
            "texture_loaded": True
        }
        
        logger.info(f"Initialized avatar model: {self.config.avatar_type.value}")
    
    async def _rendering_loop(self):
        """Main rendering loop"""
        while self.is_running:
            try:
                frame_start_time = time.time()
                
                # Render frame
                frame_data = await self._render_frame()
                
                if frame_data:
                    # In real implementation, would send frame to display/output
                    self.metrics["frames_rendered"] += 1
                
                # Maintain frame rate
                frame_time = time.time() - frame_start_time
                sleep_time = max(0, self.frame_time - frame_time)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    self.metrics["dropped_frames"] += 1
                
            except Exception as e:
                logger.error(f"Rendering loop error: {e}")
                await asyncio.sleep(0.01)
    
    async def _render_frame(self) -> Optional[Dict[str, Any]]:
        """Render a single frame"""
        try:
            if not self.current_pose and not self.animation_queue:
                # Idle pose
                return await self._render_idle_pose()
            
            # Get current pose data
            pose_data = await self._get_current_pose_data()
            
            if pose_data:
                # Render pose to frame
                frame_data = {
                    "timestamp": time.time(),
                    "pose": pose_data.to_dict(),
                    "avatar_id": self.config.avatar_id,
                    "quality": self.config.quality.value,
                    "resolution": [self.render_width, self.render_height]
                }
                
                return frame_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            return None
    
    async def _render_idle_pose(self) -> Dict[str, Any]:
        """Render idle pose"""
        idle_pose = PoseData(
            timestamp=time.time(),
            joints={
                "right_hand": np.array([0.2, 0.3, 0.1]),
                "left_hand": np.array([-0.2, 0.3, 0.1]),
                "right_elbow": np.array([0.1, 0.4, 0.0]),
                "left_elbow": np.array([-0.1, 0.4, 0.0]),
                "head": np.array([0.0, 0.0, 0.0])
            },
            facial_expressions={
                "neutral": 0.5,
                "eye_contact": 0.8
            }
        )
        
        return {
            "timestamp": time.time(),
            "pose": idle_pose.to_dict(),
            "avatar_id": self.config.avatar_id,
            "state": "idle"
        }
    
    async def _get_current_pose_data(self) -> Optional[PoseData]:
        """Get current pose data for rendering"""
        if self.current_pose:
            return self.current_pose
        
        # Get pose from animation queue
        if self.animation_queue:
            return await self._process_animation_queue()
        
        return None
    
    async def _process_animation_queue(self) -> Optional[PoseData]:
        """Process animation queue and return current pose"""
        if not self.animation_queue:
            return None
        
        # Get current sequence
        current_sequence = self.animation_queue[0]
        
        # Generate pose data for current time in sequence
        elapsed_time = time.time() - current_sequence.created_at
        current_time = elapsed_time % current_sequence.total_duration
        
        # Find which sign we're currently on
        cumulative_time = 0.0
        current_sign_index = 0
        
        for i, (sign, duration) in enumerate(zip(current_sequence.signs, current_sequence.durations)):
            if cumulative_time + duration > current_time:
                current_sign_index = i
                break
            cumulative_time += duration
        
        # Get pose data for current sign
        sign_data = self.sign_library.get_sign(current_sequence.signs[current_sign_index])
        
        if sign_data:
            pose_data = PoseData(
                timestamp=time.time(),
                joints={k: np.array(v) for k, v in sign_data["joints"].items()},
                facial_expressions=sign_data.get("facial_expressions", {}),
                hand_shapes={k: np.array(v) for k, v in sign_data.get("hand_shapes", {}).items()},
                confidence=0.9
            )
            
            # Check if sequence is complete
            if elapsed_time >= current_sequence.total_duration:
                self.animation_queue.pop(0)
                self.metrics["signs_rendered"] += 1
                
                # Notify callback
                if self.on_sign_completed:
                    await self.on_sign_completed(current_sequence)
            
            return pose_data
        
        return None
    
    async def _animation_loop(self):
        """Background loop for animation state management"""
        while self.is_running:
            try:
                await asyncio.sleep(0.1)  # Check every 100ms
                
                # Update animation state
                new_state = self._determine_animation_state()
                
                if new_state != self.current_animation_state:
                    old_state = self.current_animation_state
                    self.current_animation_state = new_state
                    
                    # Notify callback
                    if self.on_animation_state_changed:
                        await self.on_animation_state_changed(old_state, new_state)
                
            except Exception as e:
                logger.error(f"Animation loop error: {e}")
                await asyncio.sleep(1)
    
    def _determine_animation_state(self) -> AnimationState:
        """Determine current animation state"""
        if self.animation_queue:
            return AnimationState.SIGNING
        elif self.current_pose:
            return AnimationState.GESTURING
        else:
            return AnimationState.IDLE
    
    async def sign_text(self, text: str) -> str:
        """Convert text to sign language sequence"""
        try:
            # Simple text-to-sign mapping
            # In real implementation, would use NLP and sign language dictionary
            words = text.lower().split()
            signs = []
            durations = []
            
            for word in words:
                sign_data = self.sign_library.get_sign(word)
                if sign_data:
                    signs.append(word)
                    durations.append(sign_data["duration"])
                else:
                    # Finger spell unknown words
                    for letter in word:
                        if self.sign_library.get_sign(letter):
                            signs.append(letter)
                            durations.append(0.5)  # Short duration for letters
                        else:
                            # Skip unknown letters
                            continue
            
            if not signs:
                logger.warning(f"No signs found for text: {text}")
                return ""
            
            # Create sign sequence
            sequence_id = hashlib.sha256(f"{text}_{time.time()}".encode()).hexdigest()[:16]
            sequence = SignSequence(
                sequence_id=sequence_id,
                signs=signs,
                durations=durations,
                metadata={"source_text": text, "auto_generated": True}
            )
            
            # Add to animation queue
            self.animation_queue.append(sequence)
            
            # Notify callback
            if self.on_sign_started:
                await self.on_sign_started(sequence)
            
            logger.info(f"Created sign sequence for: {text}")
            return sequence_id
            
        except Exception as e:
            logger.error(f"Error converting text to signs: {e}")
            return ""
    
    async def sign_sequence(self, signs: List[str], durations: List[float] = None) -> str:
        """Create sign sequence from list of signs"""
        try:
            if not signs:
                return ""
            
            # Validate all signs exist
            for sign in signs:
                if not self.sign_library.get_sign(sign):
                    logger.warning(f"Sign not found: {sign}")
                    return ""
            
            # Use default durations if not provided
            if not durations:
                durations = []
                for sign in signs:
                    sign_data = self.sign_library.get_sign(sign)
                    durations.append(sign_data["duration"] if sign_data else 1.0)
            
            # Create sign sequence
            sequence_id = hashlib.sha256(f"{signs}_{time.time()}".encode()).hexdigest()[:16]
            sequence = SignSequence(
                sequence_id=sequence_id,
                signs=signs,
                durations=durations,
                metadata={"manual_sequence": True}
            )
            
            # Add to animation queue
            self.animation_queue.append(sequence)
            
            # Notify callback
            if self.on_sign_started:
                await self.on_sign_started(sequence)
            
            logger.info(f"Created sign sequence: {signs}")
            return sequence_id
            
        except Exception as e:
            logger.error(f"Error creating sign sequence: {e}")
            return ""
    
    async def add_custom_sign(self, sign_name: str, sign_data: Dict[str, Any]) -> bool:
        """Add a custom sign to the library"""
        try:
            self.sign_library.add_custom_sign(sign_name, sign_data)
            logger.info(f"Added custom sign: {sign_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom sign {sign_name}: {e}")
            return False
    
    def clear_animation_queue(self):
        """Clear the animation queue"""
        self.animation_queue.clear()
        self.current_pose = None
        logger.info("Animation queue cleared")
    
    def pause_animation(self):
        """Pause current animation"""
        self.is_rendering = False
        logger.info("Animation paused")
    
    def resume_animation(self):
        """Resume animation"""
        self.is_rendering = True
        logger.info("Animation resumed")
    
    async def _metrics_loop(self):
        """Background loop for metrics collection"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Calculate average render time
                if self.metrics["frames_rendered"] > 0:
                    # Mock calculation - in real implementation would track actual render times
                    self.metrics["average_render_time"] = 16.67  # ~60fps
                
                logger.debug(f"Avatar renderer metrics: {self.metrics}")
                
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(10)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rendering metrics"""
        return {
            **self.metrics,
            "animation_queue_length": len(self.animation_queue),
            "current_state": self.current_animation_state.value,
            "is_rendering": self.is_rendering,
            "render_settings": {
                "resolution": [self.render_width, self.render_height],
                "fps": self.fps,
                "quality": self.config.quality.value
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get renderer status"""
        return {
            "is_running": self.is_running,
            "config": self.config.to_dict(),
            "metrics": self.get_metrics(),
            "sign_library_size": len(self.sign_library.signs)
        }
    
    def export_avatar_data(self) -> Dict[str, Any]:
        """Export avatar configuration and data"""
        return {
            "config": self.config.to_dict(),
            "sign_library": {
                "sign_language": self.sign_library.sign_language.value,
                "signs": self.sign_library.signs,
                "transitions": self.sign_library.transitions,
                "facial_expressions": self.sign_library.facial_expressions
            },
            "metrics": self.metrics,
            "export_timestamp": time.time()
        }


class AvatarRenderingService:
    """Service for managing multiple avatar renderers"""
    
    def __init__(self):
        self.renderers: Dict[str, AvatarRenderer] = {}
        self.default_config = AvatarConfiguration(
            avatar_id="default_avatar",
            avatar_type=AvatarType.HUMANOID,
            sign_language=SignLanguage.ASL,
            quality=RenderingQuality.MEDIUM
        )
        
        # Service metrics
        self.metrics = {
            "total_renderers": 0,
            "active_renderers": 0,
            "total_signs_rendered": 0,
            "service_uptime": time.time()
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
    
    async def create_renderer(self, config: AvatarConfiguration) -> str:
        """Create a new avatar renderer"""
        try:
            renderer = AvatarRenderer(config)
            await renderer.start()
            
            self.renderers[config.avatar_id] = renderer
            self.metrics["total_renderers"] += 1
            self.metrics["active_renderers"] += 1
            
            logger.info(f"Created avatar renderer: {config.avatar_id}")
            return config.avatar_id
            
        except Exception as e:
            logger.error(f"Failed to create renderer {config.avatar_id}: {e}")
            return ""
    
    async def remove_renderer(self, avatar_id: str) -> bool:
        """Remove an avatar renderer"""
        try:
            if avatar_id not in self.renderers:
                logger.error(f"Renderer {avatar_id} not found")
                return False
            
            renderer = self.renderers[avatar_id]
            await renderer.stop()
            
            del self.renderers[avatar_id]
            self.metrics["active_renderers"] -= 1
            
            logger.info(f"Removed avatar renderer: {avatar_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove renderer {avatar_id}: {e}")
            return False
    
    def get_renderer(self, avatar_id: str) -> Optional[AvatarRenderer]:
        """Get renderer by ID"""
        return self.renderers.get(avatar_id)
    
    async def sign_text_on_all(self, text: str) -> Dict[str, str]:
        """Sign text on all active renderers"""
        results = {}
        
        for avatar_id, renderer in self.renderers.items():
            sequence_id = await renderer.sign_text(text)
            results[avatar_id] = sequence_id
        
        return results
    
    async def start(self) -> bool:
        """Start the avatar rendering service"""
        try:
            self.is_running = True
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._service_metrics_loop())
            ]
            
            logger.info("Avatar rendering service started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start avatar service: {e}")
            return False
    
    async def stop(self):
        """Stop the avatar rendering service"""
        self.is_running = False
        
        # Stop all renderers
        for renderer in self.renderers.values():
            await renderer.stop()
        
        self.renderers.clear()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Avatar rendering service stopped")
    
    async def _service_metrics_loop(self):
        """Background loop for service metrics"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                # Update metrics
                total_signs = sum(
                    renderer.metrics["signs_rendered"] 
                    for renderer in self.renderers.values()
                )
                self.metrics["total_signs_rendered"] = total_signs
                
                logger.debug(f"Avatar service metrics: {self.metrics}")
                
            except Exception as e:
                logger.error(f"Service metrics loop error: {e}")
                await asyncio.sleep(60)
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            **self.metrics,
            "uptime": time.time() - self.metrics["service_uptime"],
            "renderer_details": {
                avatar_id: renderer.get_metrics()
                for avatar_id, renderer in self.renderers.items()
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "is_running": self.is_running,
            "metrics": self.get_service_metrics(),
            "available_avatar_types": [t.value for t in AvatarType],
            "available_sign_languages": [l.value for l in SignLanguage],
            "available_qualities": [q.value for q in RenderingQuality]
        }
