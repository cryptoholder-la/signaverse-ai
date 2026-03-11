"""
Sign Language DNA Zome
Holochain zome for sign language collaboration
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib

from core.network_layer.holochain_dna import SignLanguageDNA, EntryType
from core.commit_engine.commit import Commit, Delta
from core.delta_protocol.delta_ops import DeltaProtocol, DeltaOperation


@dataclass
class SignVideo:
    """Sign language video data structure"""
    video_hash: str
    signer_id: str
    language: str
    duration: float
    resolution: str
    format: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_hash": self.video_hash,
            "signer_id": self.signer_id,
            "language": self.language,
            "duration": self.duration,
            "resolution": self.resolution,
            "format": self.format,
            "metadata": self.metadata
        }


@dataclass
class Translation:
    """Translation data structure"""
    source_type: str  # "sign" or "text"
    target_type: str  # "sign" or "text"
    source_content: str
    target_content: str
    source_language: str
    target_language: str
    confidence: float
    translator_agent: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "target_type": self.target_type,
            "source_content": self.source_content,
            "target_content": self.target_content,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "confidence": self.confidence,
            "translator_agent": self.translator_agent,
            "timestamp": self.timestamp
        }


@dataclass
class Annotation:
    """Annotation for sign language content"""
    target_hash: str  # Hash of the content being annotated
    annotation_type: str  # "timing", "meaning", "grammar", "regional"
    content: str
    annotator: str
    timestamp: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_hash": self.target_hash,
            "annotation_type": self.annotation_type,
            "content": self.content,
            "annotator": self.annotator,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class SignLanguageZome(SignLanguageDNA):
    """Sign language collaboration zome"""
    
    def __init__(self, agent_pubkey: str):
        super().__init__(agent_pubkey)
        self.videos: Dict[str, SignVideo] = {}
        self.translations: Dict[str, Translation] = {}
        self.annotations: Dict[str, List[Annotation]] = {}
        
    def upload_sign_video(self, video_data: Dict[str, Any]) -> str:
        """Upload a sign language video"""
        # Create sign video object
        video = SignVideo(
            video_hash=video_data["video_hash"],
            signer_id=video_data["signer_id"],
            language=video_data["language"],
            duration=video_data["duration"],
            resolution=video_data.get("resolution", "1920x1080"),
            format=video_data.get("format", "mp4"),
            metadata=video_data.get("metadata", {})
        )
        
        # Store locally
        self.videos[video.video_hash] = video
        
        # Create Holochain entry
        entry = self.create_sign_video_entry(video.to_dict())
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return video.video_hash
    
    def create_translation(self, translation_data: Dict[str, Any]) -> str:
        """Create a translation entry"""
        translation = Translation(
            source_type=translation_data["source_type"],
            target_type=translation_data["target_type"],
            source_content=translation_data["source_content"],
            target_content=translation_data["target_content"],
            source_language=translation_data["source_language"],
            target_language=translation_data["target_language"],
            confidence=translation_data.get("confidence", 0.0),
            translator_agent=self.agent_pubkey,
            timestamp=time.time()
        )
        
        # Generate translation hash
        translation_hash = self._hash_translation(translation)
        
        # Store locally
        self.translations[translation_hash] = translation
        
        # Create Holochain entry
        entry = self.create_translation_entry(translation.to_dict())
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return translation_hash
    
    def add_annotation(self, annotation_data: Dict[str, Any]) -> str:
        """Add an annotation to content"""
        annotation = Annotation(
            target_hash=annotation_data["target_hash"],
            annotation_type=annotation_data["annotation_type"],
            content=annotation_data["content"],
            annotator=self.agent_pubkey,
            timestamp=time.time(),
            metadata=annotation_data.get("metadata", {})
        )
        
        # Generate annotation hash
        annotation_hash = self._hash_annotation(annotation)
        
        # Store locally
        if annotation.target_hash not in self.annotations:
            self.annotations[annotation.target_hash] = []
        self.annotations[annotation.target_hash].append(annotation)
        
        # Create Holochain entry
        entry = self.create_annotation_entry(annotation.to_dict())
        
        # Publish to DHT
        self.publish_to_dht(entry)
        
        return annotation_hash
    
    def get_video(self, video_hash: str) -> Optional[SignVideo]:
        """Get video by hash"""
        # Check local storage first
        if video_hash in self.videos:
            return self.videos[video_hash]
        
        # Try to fetch from DHT
        entry = self.fetch_from_dht(video_hash)
        if entry and entry.entry_type == EntryType.APP_STATE:
            data = entry.data
            if data.get("type") == "sign_video":
                video_data = data["video_data"]
                video = SignVideo(
                    video_hash=video_data["video_hash"],
                    signer_id=video_data["signer_id"],
                    language=video_data["language"],
                    duration=video_data["duration"],
                    resolution=video_data.get("resolution"),
                    format=video_data.get("format"),
                    metadata=video_data.get("metadata", {})
                )
                self.videos[video_hash] = video
                return video
        
        return None
    
    def get_translations(self, source_hash: str, target_language: Optional[str] = None) -> List[Translation]:
        """Get translations for a source"""
        translations = []
        
        # Check local storage
        for translation in self.translations.values():
            if (translation.source_content == source_hash or 
                self._content_matches_source(translation.source_content, source_hash)):
                if target_language is None or translation.target_language == target_language:
                    translations.append(translation)
        
        # Query DHT for additional translations
        entries = self.query_entries(EntryType.APP_STATE)
        for entry in entries:
            if entry.data.get("type") == "translation":
                translation_data = entry.data["translation_data"]
                if (translation_data["source_content"] == source_hash or
                    self._content_matches_source(translation_data["source_content"], source_hash)):
                    if target_language is None or translation_data["target_language"] == target_language:
                        translation = Translation(
                            source_type=translation_data["source_type"],
                            target_type=translation_data["target_type"],
                            source_content=translation_data["source_content"],
                            target_content=translation_data["target_content"],
                            source_language=translation_data["source_language"],
                            target_language=translation_data["target_language"],
                            confidence=translation_data.get("confidence", 0.0),
                            translator_agent=translation_data["translator_agent"],
                            timestamp=translation_data["timestamp"]
                        )
                        translations.append(translation)
        
        return translations
    
    def get_annotations(self, target_hash: str, annotation_type: Optional[str] = None) -> List[Annotation]:
        """Get annotations for content"""
        annotations = []
        
        # Check local storage
        if target_hash in self.annotations:
            for annotation in self.annotations[target_hash]:
                if annotation_type is None or annotation.annotation_type == annotation_type:
                    annotations.append(annotation)
        
        # Query DHT for additional annotations
        entries = self.query_entries(EntryType.APP_STATE)
        for entry in entries:
            if entry.data.get("type") == "annotation":
                annotation_data = entry.data["annotation_data"]
                if annotation_data["target_hash"] == target_hash:
                    if annotation_type is None or annotation_data["annotation_type"] == annotation_type:
                        annotation = Annotation(
                            target_hash=annotation_data["target_hash"],
                            annotation_type=annotation_data["annotation_type"],
                            content=annotation_data["content"],
                            annotator=annotation_data["annotator"],
                            timestamp=annotation_data["timestamp"],
                            metadata=annotation_data.get("metadata", {})
                        )
                        annotations.append(annotation)
        
        return annotations
    
    def search_videos(self, language: Optional[str] = None, 
                      signer_id: Optional[str] = None,
                      min_duration: Optional[float] = None,
                      max_duration: Optional[float] = None) -> List[SignVideo]:
        """Search for videos with filters"""
        results = []
        
        for video in self.videos.values():
            if language and video.language != language:
                continue
            if signer_id and video.signer_id != signer_id:
                continue
            if min_duration and video.duration < min_duration:
                continue
            if max_duration and video.duration > max_duration:
                continue
            
            results.append(video)
        
        return results
    
    def get_language_stats(self) -> Dict[str, int]:
        """Get statistics by language"""
        stats = {}
        
        for video in self.videos.values():
            lang = video.language
            stats[lang] = stats.get(lang, 0) + 1
        
        return stats
    
    def _hash_translation(self, translation: Translation) -> str:
        """Generate hash for translation"""
        translation_data = {
            "source_type": translation.source_type,
            "target_type": translation.target_type,
            "source_content": translation.source_content,
            "target_content": translation.target_content,
            "source_language": translation.source_language,
            "target_language": translation.target_language,
            "translator_agent": translation.translator_agent,
            "timestamp": translation.timestamp
        }
        translation_json = json.dumps(translation_data, sort_keys=True)
        return hashlib.sha256(translation_json.encode()).hexdigest()
    
    def _hash_annotation(self, annotation: Annotation) -> str:
        """Generate hash for annotation"""
        annotation_data = {
            "target_hash": annotation.target_hash,
            "annotation_type": annotation.annotation_type,
            "content": annotation.content,
            "annotator": annotation.annotator,
            "timestamp": annotation.timestamp
        }
        annotation_json = json.dumps(annotation_data, sort_keys=True)
        return hashlib.sha256(annotation_json.encode()).hexdigest()
    
    def _content_matches_source(self, content: str, source_hash: str) -> bool:
        """Check if content matches source hash"""
        # This is a simplified check
        # In a real implementation, this would be more sophisticated
        return content == source_hash or content.endswith(source_hash)
    
    def create_collaborative_session(self, session_data: Dict[str, Any]) -> str:
        """Create a collaborative translation session"""
        session_entry = self.create_entry(EntryType.APP_STATE, {
            "type": "collaborative_session",
            "session_data": session_data
        })
        
        self.publish_to_dht(session_entry)
        return session_entry.entry_hash
    
    def join_session(self, session_hash: str, participant_data: Dict[str, Any]) -> bool:
        """Join a collaborative session"""
        session_entry = self.get_entry(session_hash)
        if not session_entry or session_entry.data.get("type") != "collaborative_session":
            return False
        
        # Add participant to session
        session_data = session_entry.data["session_data"]
        if "participants" not in session_data:
            session_data["participants"] = []
        
        participant_data["agent_pubkey"] = self.agent_pubkey
        participant_data["joined_at"] = time.time()
        session_data["participants"].append(participant_data)
        
        # Update session entry
        updated_entry = self.create_entry(EntryType.APP_STATE, {
            "type": "collaborative_session",
            "session_data": session_data,
            "parent_session": session_hash
        })
        
        self.publish_to_dht(updated_entry)
        return True
