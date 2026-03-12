"""
Advanced Memory System for Albrite Agents
Multi-modal memory with vector stores, graph databases, and intelligent retrieval
"""

import asyncio
import logging
import json
import pickle
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import faiss  # For vector similarity search
import networkx as nx  # For graph operations

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory storage"""
    EPISODIC = "episodic"      # Personal experiences and events
    SEMANTIC = "semantic"      # General knowledge and facts
    PROCEDURAL = "procedural"  # Skills and procedures
    WORKING = "working"        # Current task context
    LONG_TERM = "long_term"    # Persistent important memories


class MemoryModality(Enum):
    """Memory modalities"""
    TEXT = "text"
    VISUAL = "visual"
    AUDIO = "audio"
    STRUCTURED = "structured"
    EMBEDDING = "embedding"


@dataclass
class MemoryItem:
    """Enhanced memory item with multi-modal support"""
    id: str
    content: Any
    memory_type: MemoryType
    modality: MemoryModality
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    importance: float = 0.5
    emotional_valence: float = 0.0  # -1 (negative) to 1 (positive)
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None


@dataclass
class MemoryRelationship:
    """Relationship between memories"""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorMemoryStore:
    """Vector-based memory store for similarity search"""
    
    def __init__(self, dimension: int = 768, max_items: int = 10000):
        self.dimension = dimension
        self.max_items = max_items
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.memories = {}  # id -> MemoryItem
        self.embeddings = {}  # id -> embedding
        self.current_size = 0
    
    def add_memory(self, memory: MemoryItem, embedding: np.ndarray):
        """Add memory with embedding"""
        if self.current_size >= self.max_items:
            # Remove least important memory
            self._evict_least_important()
        
        # Normalize embedding for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        # Add to index
        self.index.add(embedding.reshape(1, -1))
        
        # Store memory and embedding
        self.memories[memory.id] = memory
        self.embeddings[memory.id] = embedding
        self.current_size += 1
    
    def search_similar(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[MemoryItem, float]]:
        """Search for similar memories"""
        if self.current_size == 0:
            return []
        
        # Normalize query embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search
        similarities, indices = self.index.search(query_embedding.reshape(1, -1), min(k, self.current_size))
        
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx >= 0:  # Valid index
                memory_id = list(self.memories.keys())[idx]
                memory = self.memories[memory_id]
                results.append((memory, float(similarity)))
        
        return results
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get memory by ID"""
        return self.memories.get(memory_id)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory (requires index rebuild)"""
        if memory_id not in self.memories:
            return False
        
        # Remove from storage
        del self.memories[memory_id]
        del self.embeddings[memory_id]
        self.current_size -= 1
        
        # Rebuild index
        self._rebuild_index()
        return True
    
    def _evict_least_important(self):
        """Evict least important memory"""
        if not self.memories:
            return
        
        # Find least important memory
        least_important = min(
            self.memories.items(),
            key=lambda x: x[1].importance
        )
        
        memory_id = least_important[0]
        del self.memories[memory_id]
        del self.embeddings[memory_id]
        self.current_size -= 1
    
    def _rebuild_index(self):
        """Rebuild FAISS index"""
        self.index = faiss.IndexFlatIP(self.dimension)
        
        if self.embeddings:
            embeddings_array = np.array(list(self.embeddings.values()))
            self.index.add(embeddings_array)


class GraphMemoryStore:
    """Graph-based memory store for relationships"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.memories = {}  # id -> MemoryItem
        self.relationships = {}  # (source, target) -> MemoryRelationship
    
    def add_memory(self, memory: MemoryItem):
        """Add memory to graph"""
        self.memories[memory.id] = memory
        self.graph.add_node(memory.id, **memory.__dict__)
    
    def add_relationship(self, relationship: MemoryRelationship):
        """Add relationship between memories"""
        self.relationships[(relationship.source_id, relationship.target_id)] = relationship
        self.graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            weight=relationship.strength,
            type=relationship.relationship_type,
            **relationship.metadata
        )
    
    def get_related_memories(self, memory_id: str, relationship_type: str = None,
                           max_depth: int = 2) -> List[Tuple[MemoryItem, float, str]]:
        """Get related memories"""
        if memory_id not in self.memories:
            return []
        
        related = []
        
        # Get neighbors
        for neighbor in self.graph.neighbors(memory_id):
            edge_data = self.graph[memory_id][neighbor]
            strength = edge_data.get('weight', 0.0)
            rel_type = edge_data.get('type', 'related')
            
            if relationship_type is None or rel_type == relationship_type:
                neighbor_memory = self.memories[neighbor]
                related.append((neighbor_memory, strength, rel_type))
        
        # Sort by strength
        related.sort(key=lambda x: x[1], reverse=True)
        
        return related
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find path between memories"""
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_memory_clusters(self, min_cluster_size: int = 3) -> List[List[str]]:
        """Get memory clusters using community detection"""
        try:
            # Use connected components for clustering
            clusters = list(nx.connected_components(self.graph.to_undirected()))
            return [list(cluster) for cluster in clusters if len(cluster) >= min_cluster_size]
        except:
            return []


class TimeSeriesMemoryStore:
    """Time-series memory store for temporal patterns"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.time_series = defaultdict(deque)  # memory_type -> deque of (timestamp, memory_id)
        self.memories = {}  # id -> MemoryItem
        self.temporal_index = {}  # (timestamp, memory_id) -> memory
    
    def add_memory(self, memory: MemoryItem):
        """Add memory with timestamp"""
        self.memories[memory.id] = memory
        
        # Add to time series
        timestamp = memory.created_at.timestamp()
        self.time_series[memory.memory_type].append((timestamp, memory.id))
        self.temporal_index[(timestamp, memory.id)] = memory
        
        # Maintain size limit
        if len(self.time_series[memory.memory_type]) > self.max_size:
            old_timestamp, old_memory_id = self.time_series[memory.memory_type].popleft()
            del self.temporal_index[(old_timestamp, old_memory_id)]
    
    def get_memories_in_range(self, memory_type: MemoryType, start_time: datetime,
                            end_time: datetime) -> List[MemoryItem]:
        """Get memories in time range"""
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()
        
        memories = []
        for timestamp, memory_id in self.time_series[memory_type]:
            if start_ts <= timestamp <= end_ts:
                memory = self.memories.get(memory_id)
                if memory:
                    memories.append(memory)
        
        return sorted(memories, key=lambda m: m.created_at)
    
    def get_temporal_patterns(self, memory_type: MemoryType, window_hours: int = 24) -> Dict[str, Any]:
        """Analyze temporal patterns"""
        if memory_type not in self.time_series:
            return {}
        
        # Get recent memories
        recent_time = datetime.now() - timedelta(hours=window_hours)
        recent_memories = self.get_memories_in_range(memory_type, recent_time, datetime.now())
        
        if not recent_memories:
            return {}
        
        # Analyze patterns
        hourly_counts = defaultdict(int)
        importance_trend = []
        
        for memory in recent_memories:
            hour = memory.created_at.hour
            hourly_counts[hour] += 1
            importance_trend.append((memory.created_at, memory.importance))
        
        return {
            "total_memories": len(recent_memories),
            "hourly_distribution": dict(hourly_counts),
            "average_importance": np.mean([m.importance for m in recent_memories]),
            "importance_trend": importance_trend
        }


class AdvancedMemorySystem:
    """Advanced multi-modal memory system"""
    
    def __init__(self, embedding_dimension: int = 768):
        self.vector_store = VectorMemoryStore(dimension=embedding_dimension)
        self.graph_store = GraphMemoryStore()
        self.time_series_store = TimeSeriesMemoryStore()
        self.working_memory = {}  # Current task context
        self.memory_stats = defaultdict(int)
        self.access_patterns = defaultdict(list)
        
        # Memory consolidation settings
        self.consolidation_threshold = 0.8
        self.consolidation_interval = timedelta(hours=6)
        self.last_consolidation = datetime.now()
    
    async def add_memory(self, content: Any, memory_type: MemoryType,
                        modality: MemoryModality = MemoryModality.TEXT,
                        importance: float = 0.5, emotional_valence: float = 0.0,
                        tags: List[str] = None, related_memories: List[str] = None,
                        metadata: Dict[str, Any] = None,
                        embedding: Optional[np.ndarray] = None) -> str:
        """Add memory to system"""
        # Generate memory ID
        memory_id = hashlib.md5(
            f"{memory_type.value}:{modality.value}:{str(content)}:{datetime.now().isoformat()}"
            .encode()
        ).hexdigest()[:16]
        
        # Create memory item
        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            modality=modality,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            importance=importance,
            emotional_valence=emotional_valence,
            tags=tags or [],
            related_memories=related_memories or [],
            embedding=embedding,
            metadata=metadata or {}
        )
        
        # Add to appropriate stores
        if memory_type == MemoryType.WORKING:
            self.working_memory[memory_id] = memory
        else:
            self.vector_store.add_memory(memory, embedding or self._generate_embedding(content))
            self.graph_store.add_memory(memory)
            self.time_series_store.add_memory(memory)
        
        # Create relationships
        if related_memories:
            for related_id in related_memories:
                relationship = MemoryRelationship(
                    source_id=memory_id,
                    target_id=related_id,
                    relationship_type="related",
                    strength=0.5,
                    created_at=datetime.now()
                )
                self.graph_store.add_relationship(relationship)
        
        # Update stats
        self.memory_stats[memory_type.value] += 1
        
        return memory_id
    
    async def retrieve_memory(self, query: str = None, memory_type: MemoryType = None,
                            modality: MemoryModality = None, tags: List[str] = None,
                            importance_threshold: float = 0.0,
                            limit: int = 10) -> List[MemoryItem]:
        """Retrieve memories with advanced filtering"""
        results = []
        
        # Generate query embedding if provided
        query_embedding = None
        if query:
            query_embedding = self._generate_embedding(query)
        
        # Search vector store
        if query_embedding:
            similar_memories = self.vector_store.search_similar(query_embedding, k=limit * 2)
            for memory, similarity in similar_memories:
                if self._matches_filters(memory, memory_type, modality, tags, importance_threshold):
                    results.append(memory)
        
        # If no query or insufficient results, search by type
        if not query_embedding or len(results) < limit:
            type_memories = []
            
            if memory_type == MemoryType.WORKING:
                type_memories = list(self.working_memory.values())
            else:
                # Get from time series store
                all_memories = self.time_series_store.memories.values()
                type_memories = [m for m in all_memories if m.memory_type == memory_type]
            
            for memory in type_memories:
                if self._matches_filters(memory, memory_type, modality, tags, importance_threshold):
                    if memory not in results:
                        results.append(memory)
        
        # Sort by importance and recency
        results.sort(key=lambda m: (m.importance, m.created_at), reverse=True)
        
        # Update access tracking
        for memory in results[:limit]:
            memory.last_accessed = datetime.now()
            memory.access_count += 1
            self.access_patterns[memory.id].append(datetime.now().timestamp())
        
        return results[:limit]
    
    async def get_related_memories(self, memory_id: str, relationship_type: str = None,
                                 max_depth: int = 2) -> List[Tuple[MemoryItem, float, str]]:
        """Get related memories through graph relationships"""
        return self.graph_store.get_related_memories(memory_id, relationship_type, max_depth)
    
    async def find_memory_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find path between memories"""
        return self.graph_store.find_path(source_id, target_id)
    
    async def get_temporal_memories(self, memory_type: MemoryType, start_time: datetime,
                                  end_time: datetime) -> List[MemoryItem]:
        """Get memories in time range"""
        return self.time_series_store.get_memories_in_range(memory_type, start_time, end_time)
    
    async def consolidate_memories(self) -> Dict[str, Any]:
        """Consolidate and optimize memory storage"""
        consolidation_results = {
            "consolidated_memories": 0,
            "removed_memories": 0,
            "new_relationships": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if consolidation is needed
        if datetime.now() - self.last_consolidation < self.consolidation_interval:
            return consolidation_results
        
        # Consolidate similar memories
        all_memories = list(self.vector_store.memories.values())
        
        for i, memory1 in enumerate(all_memories):
            for memory2 in all_memories[i+1:]:
                # Check for similarity
                if memory1.embedding is not None and memory2.embedding is not None:
                    similarity = np.dot(memory1.embedding, memory2.embedding)
                    
                    if similarity > self.consolidation_threshold:
                        # Consolidate memories
                        await self._consolidate_memory_pair(memory1, memory2)
                        consolidation_results["consolidated_memories"] += 1
        
        # Remove expired memories
        current_time = datetime.now()
        expired_memories = []
        
        for memory in all_memories:
            if memory.expires_at and current_time > memory.expires_at:
                expired_memories.append(memory.id)
        
        for memory_id in expired_memories:
            await self.delete_memory(memory_id)
            consolidation_results["removed_memories"] += 1
        
        # Update last consolidation time
        self.last_consolidation = datetime.now()
        
        return consolidation_results
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from all stores"""
        success = True
        
        # Remove from working memory
        if memory_id in self.working_memory:
            del self.working_memory[memory_id]
        
        # Remove from vector store
        success &= self.vector_store.delete_memory(memory_id)
        
        # Remove from graph store
        if memory_id in self.graph_store.memories:
            del self.graph_store.memories[memory_id]
            if memory_id in self.graph_store.graph:
                self.graph_store.graph.remove_node(memory_id)
        
        # Remove from time series
        if memory_id in self.time_series_store.memories:
            del self.time_series_store.memories[memory_id]
        
        return success
    
    def _generate_embedding(self, content: Any) -> np.ndarray:
        """Generate embedding for content (mock implementation)"""
        # In real implementation, use actual embedding model
        content_str = str(content)
        # Generate mock embedding
        embedding = np.random.randn(768)
        return embedding / np.linalg.norm(embedding)
    
    def _matches_filters(self, memory: MemoryItem, memory_type: MemoryType = None,
                        modality: MemoryModality = None, tags: List[str] = None,
                        importance_threshold: float = 0.0) -> bool:
        """Check if memory matches filters"""
        if memory_type and memory.memory_type != memory_type:
            return False
        
        if modality and memory.modality != modality:
            return False
        
        if tags and not any(tag in memory.tags for tag in tags):
            return False
        
        if memory.importance < importance_threshold:
            return False
        
        return True
    
    async def _consolidate_memory_pair(self, memory1: MemoryItem, memory2: MemoryItem):
        """Consolidate two similar memories"""
        # Create consolidated memory
        consolidated_content = {
            "original_1": memory1.content,
            "original_2": memory2.content,
            "consolidation_date": datetime.now().isoformat()
        }
        
        # Higher importance
        consolidated_importance = max(memory1.importance, memory2.importance)
        
        # Combined tags
        consolidated_tags = list(set(memory1.tags + memory2.tags))
        
        # Create new consolidated memory
        await self.add_memory(
            content=consolidated_content,
            memory_type=memory1.memory_type,
            modality=memory1.modality,
            importance=consolidated_importance,
            tags=consolidated_tags,
            related_memories=[memory1.id, memory2.id],
            metadata={"consolidated": True}
        )
        
        # Delete original memories
        await self.delete_memory(memory1.id)
        await self.delete_memory(memory2.id)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "memory_counts": dict(self.memory_stats),
            "working_memory_size": len(self.working_memory),
            "vector_store_size": self.vector_store.current_size,
            "graph_nodes": len(self.graph_store.memories),
            "graph_edges": len(self.graph_store.relationships),
            "time_series_types": len(self.time_series_store.time_series),
            "last_consolidation": self.last_consolidation.isoformat(),
            "access_patterns": {
                "tracked_memories": len(self.access_patterns),
                "total_accesses": sum(len(patterns) for patterns in self.access_patterns.values())
            }
        }


# Global advanced memory system instance
advanced_memory = AdvancedMemorySystem()
