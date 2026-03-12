"""
Albrite Mindmap System - Advanced Knowledge Repository with ID-based Access
Hash-based agent identification system for comprehensive knowledge mapping
"""

import asyncio
import logging
import hashlib
import json
import pickle
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

# Import Albrite agents
from ..home_folder.albrite_comprehensive_orchestrator import AlbriteComprehensiveOrchestrator
from ..military_branch.albrite_military_command import GeneralAlbriteMilitaryCommand

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge in the mindmap"""
    SKILL = "skill"
    EXPERIENCE = "experience"
    MEMORY = "memory"
    RELATIONSHIP = "relationship"
    COLLABORATION = "collaboration"
    INSIGHT = "insight"
    PATTERN = "pattern"
    SOLUTION = "solution"
    METRIC = "metric"
    THREAT = "threat"
    DEFENSE = "defense"


class ConnectionType(Enum):
    """Types of connections between knowledge nodes"""
    PARENT_CHILD = "parent_child"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    INFLUENCE = "influence"
    DEPENDENCY = "dependency"
    GENETIC = "genetic"
    TEMPORAL = "temporal"
    CAUSAL = "causal"


@dataclass
class KnowledgeNode:
    """Knowledge node in the mindmap"""
    id: str
    agent_id: str
    agent_name: str
    knowledge_type: KnowledgeType
    title: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    importance_score: float = 0.5
    tags: List[str] = None
    connections: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.connections is None:
            self.connections = []


@dataclass
class AgentMindmapProfile:
    """Complete mindmap profile for an agent"""
    agent_id: str
    agent_name: str
    tree_address: str  # Hash-based address
    knowledge_nodes: List[KnowledgeNode]
    total_knowledge: int
    expertise_areas: List[str]
    collaboration_network: List[str]
    genetic_traits: Dict[str, float]
    performance_metrics: Dict[str, float]
    last_updated: datetime


class AlbriteMindmapSystem:
    """Advanced mindmap system with hash-based ID generation and knowledge repository"""
    
    def __init__(self, mindmap_path: str = None):
        self.mindmap_path = Path(mindmap_path) if mindmap_path else Path(__file__).parent
        self.mindmap_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.agent_profiles = {}
        self.knowledge_index = {}  # ID-based knowledge lookup
        self.tag_index = {}  # Tag-based knowledge lookup
        self.connection_graph = {}  # Connection relationships
        self.access_logs = []  # Knowledge access tracking
        
        # Initialize orchestrator and military command
        self.orchestrator = AlbriteComprehensiveOrchestrator()
        self.military_command = GeneralAlbriteMilitaryCommand()
        
        # Mindmap database files
        self.profiles_file = self.mindmap_path / "agent_profiles.json"
        self.knowledge_file = self.mindmap_path / "knowledge_nodes.json"
        self.index_file = self.mindmap_path / "knowledge_index.json"
        self.connections_file = self.mindmap_path / "connections.json"
        
        # Load existing data
        self._load_mindmap_data()
        
        logger.info("🧠 Albrite Mindmap System initialized with hash-based ID system")
    
    def generate_agent_tree_address(self, agent_id: str, agent_name: str) -> str:
        """Generate unique tree address for agent using hash"""
        # Combine agent information with timestamp for uniqueness
        agent_data = f"{agent_id}:{agent_name}:{datetime.now().isoformat()}"
        
        # Generate SHA-256 hash
        hash_object = hashlib.sha256(agent_data.encode())
        hash_hex = hash_object.hexdigest()
        
        # Create tree address format
        tree_address = f"albrite://{agent_id}/{hash_hex[:16]}"
        
        return tree_address
    
    def generate_knowledge_id(self, agent_id: str, knowledge_type: str, title: str) -> str:
        """Generate unique ID for knowledge node"""
        # Combine knowledge information
        knowledge_data = f"{agent_id}:{knowledge_type}:{title}:{datetime.now().isoformat()}"
        
        # Generate hash
        hash_object = hashlib.sha256(knowledge_data.encode())
        hash_hex = hash_object.hexdigest()
        
        # Create knowledge ID format
        knowledge_id = f"km_{hash_hex[:12]}"
        
        return knowledge_id
    
    async def create_agent_profile(self, agent_id: str, agent_name: str, 
                              genetic_traits: Dict[str, float] = None) -> str:
        """Create mindmap profile for an agent"""
        # Generate tree address
        tree_address = self.generate_agent_tree_address(agent_id, agent_name)
        
        # Create agent profile
        profile = AgentMindmapProfile(
            agent_id=agent_id,
            agent_name=agent_name,
            tree_address=tree_address,
            knowledge_nodes=[],
            total_knowledge=0,
            expertise_areas=[],
            collaboration_network=[],
            genetic_traits=genetic_traits or {},
            performance_metrics={},
            last_updated=datetime.now()
        )
        
        # Store profile
        self.agent_profiles[tree_address] = profile
        
        # Save to disk
        await self._save_profiles()
        
        logger.info(f"🌳 Created mindmap profile for {agent_name} at {tree_address}")
        
        return tree_address
    
    async def add_knowledge_node(self, agent_tree_address: str, 
                            knowledge_type: KnowledgeType,
                            title: str, 
                            content: str,
                            metadata: Dict[str, Any] = None,
                            tags: List[str] = None,
                            connections: List[str] = None) -> str:
        """Add knowledge node to agent's mindmap"""
        # Validate agent exists
        if agent_tree_address not in self.agent_profiles:
            raise ValueError(f"Agent profile not found: {agent_tree_address}")
        
        profile = self.agent_profiles[agent_tree_address]
        
        # Generate knowledge ID
        knowledge_id = self.generate_knowledge_id(
            profile.agent_id, 
            knowledge_type.value, 
            title
        )
        
        # Create knowledge node
        node = KnowledgeNode(
            id=knowledge_id,
            agent_id=profile.agent_id,
            agent_name=profile.agent_name,
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags or [],
            connections=connections or []
        )
        
        # Add to profile
        profile.knowledge_nodes.append(node)
        profile.total_knowledge += 1
        profile.last_updated = datetime.now()
        
        # Update indexes
        self.knowledge_index[knowledge_id] = node
        
        # Update tag index
        for tag in node.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(knowledge_id)
        
        # Update connection graph
        if connections:
            self.connection_graph[knowledge_id] = connections
        
        # Update expertise areas
        if knowledge_type == KnowledgeType.SKILL:
            if title not in profile.expertise_areas:
                profile.expertise_areas.append(title)
        
        # Save to disk
        await self._save_all_data()
        
        logger.info(f"📚 Added knowledge node {knowledge_id} to {profile.agent_name}")
        
        return knowledge_id
    
    async def create_family_connections(self, connections: List[Tuple[str, str, ConnectionType]]):
        """Create connections between agents in the mindmap"""
        for source_addr, target_addr, connection_type in connections:
            if source_addr in self.agent_profiles and target_addr in self.agent_profiles:
                source_profile = self.agent_profiles[source_addr]
                target_profile = self.agent_profiles[target_addr]
                
                # Add to collaboration networks
                if target_addr not in source_profile.collaboration_network:
                    source_profile.collaboration_network.append(target_addr)
                if source_addr not in target_profile.collaboration_network:
                    target_profile.collaboration_network.append(source_addr)
                
                # Create connection knowledge nodes
                await self.add_knowledge_node(
                    source_addr,
                    KnowledgeType.RELATIONSHIP,
                    f"Connection to {target_profile.agent_name}",
                    f"Connected to {target_profile.agent_name} via {connection_type.value}",
                    {"connection_type": connection_type.value, "target": target_addr},
                    ["connection", "collaboration"],
                    [target_addr]
                )
        
        await self._save_profiles()
        logger.info(f"🔗 Created {len(connections)} family connections")
    
    async def access_knowledge(self, knowledge_id: str) -> Optional[KnowledgeNode]:
        """Access knowledge node by ID"""
        if knowledge_id not in self.knowledge_index:
            return None
        
        node = self.knowledge_index[knowledge_id]
        node.access_count += 1
        
        # Log access
        access_log = {
            "knowledge_id": knowledge_id,
            "accessed_at": datetime.now().isoformat(),
            "agent": node.agent_name
        }
        self.access_logs.append(access_log)
        
        # Save
        await self._save_all_data()
        
        return node
    
    async def search_knowledge(self, query: str, agent_filter: str = None, 
                           knowledge_type: KnowledgeType = None,
                           tags: List[str] = None) -> List[KnowledgeNode]:
        """Search knowledge nodes"""
        results = []
        
        for node in self.knowledge_index.values():
            # Apply filters
            if agent_filter and node.agent_id != agent_filter:
                continue
            if knowledge_type and node.knowledge_type != knowledge_type:
                continue
            if tags and not any(tag in node.tags for tag in tags):
                continue
            
            # Search in title and content
            if query.lower() in node.title.lower() or query.lower() in node.content.lower():
                results.append(node)
        
        # Sort by relevance (access count and importance)
        results.sort(key=lambda x: (x.access_count, x.importance_score), reverse=True)
        
        return results
    
    async def get_agent_knowledge_graph(self, agent_tree_address: str) -> Dict[str, Any]:
        """Get complete knowledge graph for an agent"""
        if agent_tree_address not in self.agent_profiles:
            return {}
        
        profile = self.agent_profiles[agent_tree_address]
        
        # Build knowledge graph
        graph = {
            "agent_info": {
                "id": profile.agent_id,
                "name": profile.agent_name,
                "tree_address": agent_tree_address,
                "total_knowledge": profile.total_knowledge,
                "expertise_areas": profile.expertise_areas,
                "collaboration_network": profile.collaboration_network,
                "genetic_traits": profile.genetic_traits,
                "performance_metrics": profile.performance_metrics
            },
            "knowledge_nodes": [],
            "connections": {},
            "knowledge_types": {},
            "tag_cloud": {}
        }
        
        # Add knowledge nodes
        for node in profile.knowledge_nodes:
            node_data = {
                "id": node.id,
                "type": node.knowledge_type.value,
                "title": node.title,
                "content": node.content,
                "metadata": node.metadata,
                "created_at": node.created_at.isoformat(),
                "updated_at": node.updated_at.isoformat(),
                "access_count": node.access_count,
                "importance_score": node.importance_score,
                "tags": node.tags,
                "connections": node.connections
            }
            graph["knowledge_nodes"].append(node_data)
            
            # Update knowledge types count
            ktype = node.knowledge_type.value
            if ktype not in graph["knowledge_types"]:
                graph["knowledge_types"][ktype] = 0
            graph["knowledge_types"][ktype] += 1
            
            # Update tag cloud
            for tag in node.tags:
                if tag not in graph["tag_cloud"]:
                    graph["tag_cloud"][tag] = 0
                graph["tag_cloud"][tag] += 1
        
        # Add connections
        for node_id, connections in self.connection_graph.items():
            if any(n.agent_id == profile.agent_id for n in [self.knowledge_index.get(node_id)] if n):
                graph["connections"][node_id] = connections
        
        return graph
    
    async def commit_agent_knowledge(self, agent_tree_address: str, 
                                 commit_message: str = None) -> str:
        """Commit agent knowledge to repository with version control"""
        if agent_tree_address not in self.agent_profiles:
            raise ValueError(f"Agent profile not found: {agent_tree_address}")
        
        profile = self.agent_profiles[agent_tree_address]
        
        # Create commit
        commit_id = hashlib.sha256(
            f"{agent_tree_address}:{datetime.now().isoformat()}:{commit_message or 'Auto-commit'}"
            .encode()
        ).hexdigest()[:16]
        
        commit_data = {
            "commit_id": commit_id,
            "agent_tree_address": agent_tree_address,
            "agent_name": profile.agent_name,
            "commit_message": commit_message or "Auto-commit",
            "timestamp": datetime.now().isoformat(),
            "knowledge_count": profile.total_knowledge,
            "profile_snapshot": asdict(profile)
        }
        
        # Save commit
        commit_file = self.mindmap_path / f"commits_{profile.agent_id}.json"
        
        # Load existing commits
        commits = []
        if commit_file.exists():
            with open(commit_file, 'r') as f:
                commits = json.load(f)
        
        commits.append(commit_data)
        
        # Save commits
        with open(commit_file, 'w') as f:
            json.dump(commits, f, indent=2, default=str)
        
        logger.info(f"💾 Committed knowledge for {profile.agent_name} with ID {commit_id}")
        
        return commit_id
    
    async def initialize_family_mindmap(self) -> Dict[str, str]:
        """Initialize mindmap for all Albrite family agents"""
        agent_addresses = {}
        
        # Get all agents from orchestrator
        family_agents = self.orchestrator.family_agents
        
        # Create profiles for all agents
        for agent_id, agent in family_agents.items():
            tree_address = await self.create_agent_profile(
                agent_id,
                agent.albrite_name,
                agent.genetic_code.traits
            )
            agent_addresses[agent_id] = tree_address
            
            # Add initial knowledge nodes
            await self._add_initial_knowledge(tree_address, agent)
        
        # Add military commanders
        military_agents = {
            "general": self.military_command,
            "rex": self.military_command.military_branches.get("blockchain"),
            "nova": self.military_command.military_branches.get("web"),
            "stratus": self.military_command.military_branches.get("cloud"),
            "cognita": self.military_command.military_branches.get("ai_models"),
            "agentis": self.military_command.military_branches.get("agents")
        }
        
        for agent_id, agent in military_agents.items():
            if agent:
                tree_address = await self.create_agent_profile(
                    agent_id,
                    agent.albrite_name,
                    agent.genetic_code.traits
                )
                agent_addresses[agent_id] = tree_address
                
                # Add initial knowledge
                await self._add_initial_knowledge(tree_address, agent)
        
        # Create family connections
        await self._create_family_connections(agent_addresses)
        
        # Commit initial state
        for tree_address in agent_addresses.values():
            await self.commit_agent_knowledge(tree_address, "Initial mindmap creation")
        
        logger.info(f"🧠 Initialized family mindmap with {len(agent_addresses)} agents")
        
        return agent_addresses
    
    async def _add_initial_knowledge(self, tree_address: str, agent):
        """Add initial knowledge nodes for an agent"""
        # Add skills knowledge
        for skill in agent.get_core_skills():
            await self.add_knowledge_node(
                tree_address,
                KnowledgeType.SKILL,
                skill,
                f"Core skill: {skill}",
                {"category": "core_skill", "proficiency": 0.9},
                ["skill", "core"],
                []
            )
        
        # Add unique abilities
        for ability in agent.get_unique_abilities():
            await self.add_knowledge_node(
                tree_address,
                KnowledgeType.SKILL,
                ability,
                f"Unique ability: {ability}",
                {"category": "unique_ability", "proficiency": 0.95},
                ["skill", "unique"],
                []
            )
        
        # Add bio as memory
        await self.add_knowledge_node(
            tree_address,
            KnowledgeType.MEMORY,
            "Agent Biography",
            agent.get_bio(),
            {"category": "biography", "source": "agent_profile"},
            ["bio", "identity"],
            []
        )
        
        # Add collaboration style
        await self.add_knowledge_node(
            tree_address,
            KnowledgeType.COLLABORATION,
            "Collaboration Style",
            agent.get_collaboration_style(),
            {"category": "collaboration", "style": agent.get_collaboration_style()},
            ["collaboration", "style"],
            []
        )
    
    async def _create_family_connections(self, agent_addresses: Dict[str, str]):
        """Create initial family connections"""
        connections = []
        
        # Core family connections
        core_agents = ["seraphina", "alexander", "isabella", "marcus", "victoria", "aurora"]
        
        for i, agent1 in enumerate(core_agents):
            for agent2 in core_agents[i+1:]:
                if agent1 in agent_addresses and agent2 in agent_addresses:
                    connections.append((
                        agent_addresses[agent1],
                        agent_addresses[agent2],
                        ConnectionType.COLLABORATION
                    ))
        
        # Enhanced agents connections to core
        enhanced_agents = ["benjamin", "charlotte", "daniel", "elena", "felix", "george", "henry"]
        
        for enhanced in enhanced_agents:
            if enhanced in agent_addresses:
                # Connect to relevant core agents
                if enhanced in ["benjamin", "alexander"]:  # Data scouts
                    connections.append((
                        agent_addresses[enhanced],
                        agent_addresses["seraphina"],
                        ConnectionType.COLLABORATION
                    ))
                elif enhanced in ["charlotte", "daniel"]:  # Data processors
                    connections.append((
                        agent_addresses[enhanced],
                        agent_addresses["aurora"],
                        ConnectionType.COLLABORATION
                    ))
                elif enhanced in ["elena", "isabella"]:  # Quality experts
                    connections.append((
                        agent_addresses[enhanced],
                        agent_addresses["isabella"],
                        ConnectionType.LEARNING
                    ))
        
        # Military connections
        military_agents = ["general", "rex", "nova", "stratus", "cognita", "agentis"]
        
        for i, agent1 in enumerate(military_agents):
            for agent2 in military_agents[i+1:]:
                if agent1 in agent_addresses and agent2 in agent_addresses:
                    connections.append((
                        agent_addresses[agent1],
                        agent_addresses[agent2],
                        ConnectionType.COLLABORATION
                    ))
        
        await self.create_family_connections(connections)
    
    async def get_mindmap_statistics(self) -> Dict[str, Any]:
        """Get comprehensive mindmap statistics"""
        total_agents = len(self.agent_profiles)
        total_knowledge = sum(profile.total_knowledge for profile in self.agent_profiles.values())
        total_connections = len(self.connection_graph)
        total_tags = len(self.tag_index)
        
        # Knowledge type distribution
        knowledge_types = {}
        for node in self.knowledge_index.values():
            ktype = node.knowledge_type.value
            knowledge_types[ktype] = knowledge_types.get(ktype, 0) + 1
        
        # Most accessed knowledge
        most_accessed = sorted(
            self.knowledge_index.values(),
            key=lambda x: x.access_count,
            reverse=True
        )[:10]
        
        # Agent with most knowledge
        agent_knowledge = {
            profile.agent_name: profile.total_knowledge 
            for profile in self.agent_profiles.values()
        }
        
        return {
            "total_agents": total_agents,
            "total_knowledge": total_knowledge,
            "total_connections": total_connections,
            "total_tags": total_tags,
            "knowledge_types": knowledge_types,
            "most_accessed": [
                {
                    "id": node.id,
                    "title": node.title,
                    "agent": node.agent_name,
                    "access_count": node.access_count
                }
                for node in most_accessed
            ],
            "agent_knowledge": agent_knowledge,
            "average_knowledge_per_agent": total_knowledge / total_agents if total_agents > 0 else 0,
            "total_accesses": sum(node.access_count for node in self.knowledge_index.values())
        }
    
    async def _load_mindmap_data(self):
        """Load existing mindmap data from disk"""
        try:
            # Load profiles
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r') as f:
                    profiles_data = json.load(f)
                    for addr, data in profiles_data.items():
                        # Convert to AgentMindmapProfile
                        profile = AgentMindmapProfile(
                            agent_id=data["agent_id"],
                            agent_name=data["agent_name"],
                            tree_address=data["tree_address"],
                            knowledge_nodes=[],
                            total_knowledge=data["total_knowledge"],
                            expertise_areas=data["expertise_areas"],
                            collaboration_network=data["collaboration_network"],
                            genetic_traits=data["genetic_traits"],
                            performance_metrics=data["performance_metrics"],
                            last_updated=datetime.fromisoformat(data["last_updated"])
                        )
                        self.agent_profiles[addr] = profile
            
            # Load knowledge nodes
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'r') as f:
                    nodes_data = json.load(f)
                    for node_id, data in nodes_data.items():
                        node = KnowledgeNode(
                            id=data["id"],
                            agent_id=data["agent_id"],
                            agent_name=data["agent_name"],
                            knowledge_type=KnowledgeType(data["knowledge_type"]),
                            title=data["title"],
                            content=data["content"],
                            metadata=data["metadata"],
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]),
                            access_count=data["access_count"],
                            importance_score=data["importance_score"],
                            tags=data["tags"],
                            connections=data["connections"]
                        )
                        self.knowledge_index[node_id] = node
            
            # Load connections
            if self.connections_file.exists():
                with open(self.connections_file, 'r') as f:
                    self.connection_graph = json.load(f)
            
            logger.info("📁 Loaded existing mindmap data")
            
        except Exception as e:
            logger.warning(f"Could not load mindmap data: {e}")
    
    async def _save_profiles(self):
        """Save agent profiles to disk"""
        profiles_data = {}
        for addr, profile in self.agent_profiles.items():
            profiles_data[addr] = asdict(profile)
        
        with open(self.profiles_file, 'w') as f:
            json.dump(profiles_data, f, indent=2, default=str)
    
    async def _save_knowledge_nodes(self):
        """Save knowledge nodes to disk"""
        nodes_data = {}
        for node_id, node in self.knowledge_index.items():
            nodes_data[node_id] = asdict(node)
        
        with open(self.knowledge_file, 'w') as f:
            json.dump(nodes_data, f, indent=2, default=str)
    
    async def _save_connections(self):
        """Save connections to disk"""
        with open(self.connections_file, 'w') as f:
            json.dump(self.connection_graph, f, indent=2, default=str)
    
    async def _save_all_data(self):
        """Save all mindmap data to disk"""
        await self._save_profiles()
        await self._save_knowledge_nodes()
        await self._save_connections()


# Demonstration function
async def demonstrate_mindmap_system():
    """Demonstrate the mindmap system"""
    print("🧠 Albrite Mindmap System Demonstration")
    print("=" * 50)
    
    # Initialize mindmap system
    mindmap = AlbriteMindmapSystem()
    
    # Initialize family mindmap
    agent_addresses = await mindmap.initialize_family_mindmap()
    
    print(f"✅ Initialized mindmap with {len(agent_addresses)} agents")
    
    # Get statistics
    stats = await mindmap.get_mindmap_statistics()
    print(f"📊 Mindmap Statistics:")
    print(f"   Total Agents: {stats['total_agents']}")
    print(f"   Total Knowledge: {stats['total_knowledge']}")
    print(f"   Total Connections: {stats['total_connections']}")
    print(f"   Total Tags: {stats['total_tags']}")
    
    # Search example
    search_results = await mindmap.search_knowledge("security")
    print(f"🔍 Found {len(search_results)} knowledge nodes for 'security'")
    
    # Access knowledge example
    if search_results:
        accessed_node = await mindmap.access_knowledge(search_results[0].id)
        print(f"📖 Accessed: {accessed_node.title}")
    
    # Get agent graph example
    if agent_addresses:
        first_agent = list(agent_addresses.values())[0]
        agent_graph = await mindmap.get_agent_knowledge_graph(first_agent)
        print(f"🌳 Agent Graph: {agent_graph['agent_info']['name']} - {agent_graph['agent_info']['total_knowledge']} knowledge nodes")
    
    print("\n🎉 Mindmap system demonstration completed!")


if __name__ == "__main__":
    asyncio.run(demonstrate_mindmap_system())
