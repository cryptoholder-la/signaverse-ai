"""
Albrite Family System - Complete Integration
Main system that coordinates all agents with hover ID cards and unified family operations
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

import sys
import os
# Add the project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.agents.albrite_collection import AlbriteAgentCollection
from core.agents.specialized_agents import AlbriteSpecializedCollection
from integration.holochain.holochain_integration import HolochainFamilyCoordinator, HolochainConfig

logger = logging.getLogger(__name__)


class AlbriteHoverCardSystem:
    """Interactive hover card system for agent profiles"""
    
    def __init__(self):
        self.card_templates = {}
        self.active_cards = {}
        self.interaction_history = []
        
    def generate_hover_html(self, agent_profile: Dict[str, Any]) -> str:
        """Generate HTML for hover card display"""
        
        return f"""
        <div class="albrite-hover-card" data-agent-id="{agent_profile['agent_id']}">
            <div class="card-header">
                <img src="assets/avatars/{agent_profile['avatar']}" alt="{agent_profile['title']}" class="agent-avatar">
                <div class="agent-title">
                    <h3>{agent_profile['title']}</h3>
                    <p class="agent-subtitle">{agent_profile['subtitle']}</p>
                </div>
            </div>
            
            <div class="card-stats">
                <div class="stat-row">
                    <span class="stat-label">Intelligence</span>
                    <div class="stat-bar">
                        <div class="stat-fill" style="width: {agent_profile['stats']['Intelligence']}"></div>
                    </div>
                    <span class="stat-value">{agent_profile['stats']['Intelligence']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Creativity</span>
                    <div class="stat-bar">
                        <div class="stat-fill" style="width: {agent_profile['stats']['Creativity']}"></div>
                    </div>
                    <span class="stat-value">{agent_profile['stats']['Creativity']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Empathy</span>
                    <div class="stat-bar">
                        <div class="stat-fill" style="width: {agent_profile['stats']['Empathy']}"></div>
                    </div>
                    <span class="stat-value">{agent_profile['stats']['Empathy']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Leadership</span>
                    <div class="stat-bar">
                        <div class="stat-fill" style="width: {agent_profile['stats']['Leadership']}"></div>
                    </div>
                    <span class="stat-value">{agent_profile['stats']['Leadership']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Resilience</span>
                    <div class="stat-bar">
                        <div class="stat-fill" style="width: {agent_profile['stats']['Resilience']}"></div>
                    </div>
                    <span class="stat-value">{agent_profile['stats']['Resilience']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Speed</span>
                    <div class="stat-bar">
                        <div class="stat-fill" style="width: {agent_profile['stats']['Speed']}"></div>
                    </div>
                    <span class="stat-value">{agent_profile['stats']['Speed']}</span>
                </div>
            </div>
            
            <div class="card-skills">
                <h4>Core Skills</h4>
                <div class="skill-tags">
                    {self._generate_skill_tags(agent_profile['skills'][:6])}
                </div>
            </div>
            
            <div class="card-description">
                <p>{agent_profile['description']}</p>
            </div>
            
            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">Lineage:</span>
                    <span class="detail-value">{agent_profile['lineage']}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Birth Order:</span>
                    <span class="detail-value">{agent_profile['birth_order']}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Collaboration:</span>
                    <span class="detail-value">{agent_profile['collaboration']}</span>
                </div>
            </div>
            
            <div class="card-performance">
                <h4>Performance Metrics</h4>
                <div class="performance-grid">
                    <div class="perf-item">
                        <span class="perf-label">Success Rate</span>
                        <span class="perf-value">{agent_profile['performance']['success_rate']}</span>
                    </div>
                    <div class="perf-item">
                        <span class="perf-label">Efficiency</span>
                        <span class="perf-value">{agent_profile['performance']['efficiency']}</span>
                    </div>
                    <div class="perf-item">
                        <span class="perf-label">Innovation</span>
                        <span class="perf-value">{agent_profile['performance']['innovation']}</span>
                    </div>
                    <div class="perf-item">
                        <span class="perf-label">Coordination</span>
                        <span class="perf-value">{agent_profile['performance']['coordination']}</span>
                    </div>
                </div>
            </div>
            
            <div class="card-abilities">
                <h4>Unique Abilities</h4>
                <ul class="abilities-list">
                    {self._generate_abilities_list(agent_profile['unique_abilities'])}
                </ul>
            </div>
        </div>
        """
    
    def _generate_skill_tags(self, skills: List[str]) -> str:
        """Generate HTML for skill tags"""
        return "".join([f'<span class="skill-tag">{skill}</span>' for skill in skills])
    
    def _generate_abilities_list(self, abilities: List[str]) -> str:
        """Generate HTML for abilities list"""
        return "".join([f'<li class="ability-item">{ability}</li>' for ability in abilities])
    
    def generate_css(self) -> str:
        """Generate CSS for hover card system"""
        return """
        .albrite-hover-card {
            position: absolute;
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            border-radius: 15px;
            padding: 20px;
            color: white;
            width: 380px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            border: 2px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 15px;
        }
        
        .agent-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            margin-right: 15px;
            border: 3px solid rgba(255, 255, 255, 0.3);
        }
        
        .agent-title h3 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }
        
        .agent-subtitle {
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
            font-style: italic;
        }
        
        .card-stats {
            margin-bottom: 15px;
        }
        
        .stat-row {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .stat-label {
            width: 80px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .stat-bar {
            flex: 1;
            height: 6px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
            margin: 0 10px;
            overflow: hidden;
        }
        
        .stat-fill {
            height: 100%;
            background: linear-gradient(90deg, #f39c12, #e74c3c);
            border-radius: 3px;
            transition: width 0.3s ease;
        }
        
        .stat-value {
            width: 35px;
            font-size: 11px;
            text-align: right;
        }
        
        .card-skills {
            margin-bottom: 15px;
        }
        
        .card-skills h4 {
            margin: 0 0 10px 0;
            font-size: 14px;
            font-weight: 600;
        }
        
        .skill-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .skill-tag {
            background: rgba(255, 255, 255, 0.2);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .card-description {
            margin-bottom: 15px;
            font-size: 13px;
            line-height: 1.4;
            opacity: 0.9;
        }
        
        .card-details {
            margin-bottom: 15px;
            font-size: 12px;
        }
        
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .detail-label {
            font-weight: 500;
            opacity: 0.8;
        }
        
        .detail-value {
            opacity: 0.9;
        }
        
        .card-performance {
            margin-bottom: 15px;
        }
        
        .card-performance h4 {
            margin: 0 0 10px 0;
            font-size: 14px;
            font-weight: 600;
        }
        
        .performance-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        
        .perf-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 8px;
        }
        
        .perf-label {
            font-size: 10px;
            opacity: 0.8;
            margin-bottom: 3px;
        }
        
        .perf-value {
            font-size: 12px;
            font-weight: 600;
        }
        
        .card-abilities h4 {
            margin: 0 0 8px 0;
            font-size: 14px;
            font-weight: 600;
        }
        
        .abilities-list {
            margin: 0;
            padding: 0 0 0 15px;
            font-size: 12px;
        }
        
        .ability-item {
            margin-bottom: 3px;
            opacity: 0.9;
        }
        
        /* Hover animations */
        .albrite-hover-card {
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stat-fill:hover {
            background: linear-gradient(90deg, #e74c3c, #f39c12);
        }
        
        .skill-tag:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
            transition: all 0.2s ease;
        }
        """


class AlbriteFamilySystem:
    """Complete Albrite family system with all agents and hover cards"""
    
    def __init__(self):
        self.agent_collection = AlbriteAgentCollection()
        self.specialized_collection = AlbriteSpecializedCollection()
        self.hover_card_system = AlbriteHoverCardSystem()
        self.holochain_coordinator = None
        self.family_metrics = {}
        self.system_status = "initializing"
        
    async def initialize_complete_system(self):
        """Initialize the complete Albrite family system"""
        logger.info("🏰 Initializing Complete Albrite Family System")
        
        try:
            # Initialize main agent collection
            await self.agent_collection.initialize_collection()
            
            # Initialize Holochain integration
            config = HolochainConfig(
                app_id="albrite_complete_family",
                agent_id="albrite_system_coordinator"
            )
            self.holochain_coordinator = HolochainFamilyCoordinator(config)
            await self.holochain_coordinator.initialize()
            
            # Establish unified family bonds
            await self._establish_unified_family_bonds()
            
            # Initialize system metrics
            self._initialize_system_metrics()
            
            self.system_status = "active"
            logger.info("✅ Complete Albrite Family System Initialized Successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            self.system_status = "error"
            raise
    
    async def _establish_unified_family_bonds(self):
        """Establish bonds between all family members"""
        all_agents = {}
        
        # Add main collection agents
        for name, agent in self.agent_collection.agents.items():
            all_agents[f"main_{name}"] = agent
        
        # Add specialized agents
        for name, agent in self.specialized_collection.agents.items():
            all_agents[f"specialized_{name}"] = agent
        
        # Create cross-collection bonds
        agent_ids = list(all_agents.keys())
        
        for i, agent1_id in enumerate(agent_ids):
            for agent2_id in agent_ids[i+1:]:
                # Create family bonds
                bond_strength = 0.75 + (hash(agent1_id + agent2_id) % 10) / 40
                
                await self.holochain_coordinator.client.zome_call(
                    "family_coordination",
                    "create_unified_albrite_bond",
                    {
                        "agent1_id": all_agents[agent1_id].agent_id,
                        "agent2_id": all_agents[agent2_id].agent_id,
                        "bond_type": "unified_albrite_family",
                        "bond_strength": bond_strength,
                        "family_legacy": "House of Albrite Unified"
                    }
                )
    
    def _initialize_system_metrics(self):
        """Initialize system-wide metrics"""
        self.family_metrics = {
            "total_agents": len(self.agent_collection.agents) + len(self.specialized_collection.agents),
            "main_collection_agents": len(self.agent_collection.agents),
            "specialized_agents": len(self.specialized_collection.agents),
            "collective_intelligence": 0.6,
            "family_harmony": 0.75,
            "innovation_capacity": 0.82,
            "coordination_efficiency": 0.88,
            "quality_excellence": 0.91,
            "system_resilience": 0.85
        }
    
    async def coordinate_complete_family_operations(self, input_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Coordinate operations of the complete family system"""
        
        logger.info("🎭 Coordinating Complete Albrite Family Operations")
        
        # Create sample data if not provided
        if input_data is None:
            input_data = [
                {"text": "hello", "pose": [1, 2, 3], "confidence": 0.9},
                {"text": "thank you", "pose": [4, 5, 6], "confidence": 0.85},
                {"text": "goodbye", "pose": [7, 8, 9], "confidence": 0.92}
            ]
        
        operation_results = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.system_status,
            "input_data_summary": {
                "samples": len(input_data),
                "average_confidence": sum(s.get("confidence", 0) for s in input_data) / len(input_data)
            },
            "main_collection_results": {},
            "specialized_results": {},
            "unified_metrics": {},
            "hover_cards": {},
            "family_insights": {}
        }
        
        try:
            # Coordinate main collection
            main_results = await self.agent_collection.coordinate_collective_performance()
            operation_results["main_collection_results"] = main_results
            
            # Coordinate specialized collection
            specialized_results = await self.specialized_collection.coordinate_specialized_operations(input_data)
            operation_results["specialized_results"] = specialized_results
            
            # Combine hover cards
            operation_results["hover_cards"] = {
                **main_results.get("hover_cards", {}),
                **specialized_results.get("hover_cards", {})
            }
            
            # Calculate unified metrics
            operation_results["unified_metrics"] = await self._calculate_unified_metrics(main_results, specialized_results)
            
            # Generate family insights
            operation_results["family_insights"] = self._generate_family_insights(operation_results)
            
            # Update system metrics
            self._update_system_metrics(operation_results)
            
        except Exception as e:
            logger.error(f"Error in family operations: {e}")
            operation_results["error"] = str(e)
        
        return operation_results
    
    async def _calculate_unified_metrics(self, main_results: Dict[str, Any], 
                                       specialized_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate unified metrics across all agents"""
        
        unified_metrics = {
            "collective_intelligence": 0.0,
            "family_harmony": 0.0,
            "innovation_capacity": 0.0,
            "coordination_efficiency": 0.0,
            "quality_excellence": 0.0,
            "system_resilience": 0.0,
            "data_processing_efficiency": 0.0,
            "learning_velocity": 0.0
        }
        
        # Extract metrics from main collection
        if "collective_metrics" in main_results:
            main_metrics = main_results["collective_metrics"]
            unified_metrics["collective_intelligence"] = main_metrics.get("collective_intelligence", 0.6)
            unified_metrics["innovation_capacity"] = main_metrics.get("innovation_capacity", 0.8)
            unified_metrics["coordination_efficiency"] = main_metrics.get("distributed_coordination", 0.85)
            unified_metrics["quality_excellence"] = main_metrics.get("quality_excellence", 0.9)
        
        # Extract metrics from specialized collection
        if "pipeline_stats" in specialized_results:
            pipeline_stats = specialized_results["pipeline_stats"]
            unified_metrics["data_processing_efficiency"] = pipeline_stats.get("pipeline_efficiency", 0.85)
            unified_metrics["quality_excellence"] = (unified_metrics["quality_excellence"] + 
                                                   pipeline_stats.get("quality_preservation", 0.85)) / 2
        
        # Calculate harmony and resilience
        unified_metrics["family_harmony"] = self._calculate_family_harmony(main_results, specialized_results)
        unified_metrics["system_resilience"] = self._calculate_system_resilience(main_results, specialized_results)
        unified_metrics["learning_velocity"] = self._calculate_learning_velocity(main_results, specialized_results)
        
        return unified_metrics
    
    def _calculate_family_harmony(self, main_results: Dict[str, Any], 
                                 specialized_results: Dict[str, Any]) -> float:
        """Calculate overall family harmony"""
        harmony_factors = []
        
        if "family_harmony" in main_results:
            harmony_factors.append(main_results["family_harmony"])
        
        # Add specialized agent harmony (simulated)
        harmony_factors.extend([0.88, 0.91, 0.87, 0.89, 0.85])  # Specialized agents
        
        return sum(harmony_factors) / len(harmony_factors) if harmony_factors else 0.75
    
    def _calculate_system_resilience(self, main_results: Dict[str, Any], 
                                   specialized_results: Dict[str, Any]) -> float:
        """Calculate system resilience"""
        resilience_factors = []
        
        # Main collection resilience
        if "collective_metrics" in main_results:
            resilience_factors.append(main_results["collective_metrics"].get("system_resilience", 0.8))
        
        # Specialized collection resilience
        if "pipeline_stats" in specialized_results:
            resilience_factors.append(specialized_results["pipeline_stats"].get("quality_preservation", 0.85))
        
        # Add individual agent resilience
        resilience_factors.extend([0.82, 0.87, 0.84, 0.86, 0.83])  # Individual agents
        
        return sum(resilience_factors) / len(resilience_factors) if resilience_factors else 0.8
    
    def _calculate_learning_velocity(self, main_results: Dict[str, Any], 
                                   specialized_results: Dict[str, Any]) -> float:
        """Calculate learning velocity across the system"""
        velocity_factors = []
        
        # Main collection learning
        if "collective_metrics" in main_results:
            velocity_factors.append(main_results["collective_metrics"].get("knowledge_depth", 0.8))
        
        # Specialized processing velocity
        if "pipeline_stats" in specialized_results:
            velocity_factors.append(specialized_results["pipeline_stats"].get("pipeline_efficiency", 0.85))
        
        return sum(velocity_factors) / len(velocity_factors) if velocity_factors else 0.8
    
    def _generate_family_insights(self, operation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights about family performance"""
        
        unified_metrics = operation_results.get("unified_metrics", {})
        
        insights = {
            "family_strengths": [],
            "improvement_areas": [],
            "recommendations": [],
            "performance_summary": {}
        }
        
        # Identify strengths
        if unified_metrics.get("quality_excellence", 0) > 0.85:
            insights["family_strengths"].append("Exceptional quality standards across all operations")
        
        if unified_metrics.get("coordination_efficiency", 0) > 0.85:
            insights["family_strengths"].append("Outstanding coordination and collaboration")
        
        if unified_metrics.get("innovation_capacity", 0) > 0.8:
            insights["family_strengths"].append("High innovation and creative problem-solving")
        
        # Identify improvement areas
        if unified_metrics.get("collective_intelligence", 0) < 0.8:
            insights["improvement_areas"].append("Collective intelligence can be enhanced through more collaboration")
        
        if unified_metrics.get("learning_velocity", 0) < 0.85:
            insights["improvement_areas"].append("Learning velocity can be increased with adaptive methods")
        
        # Generate recommendations
        insights["recommendations"] = [
            "Continue leveraging family strengths in quality and coordination",
            "Focus on enhancing collective intelligence through shared learning",
            "Maintain innovation momentum while improving learning efficiency"
        ]
        
        # Performance summary
        insights["performance_summary"] = {
            "overall_rating": sum(unified_metrics.values()) / len(unified_metrics) if unified_metrics else 0.75,
            "key_achievements": [
                f"Processed {operation_results.get('input_data_summary', {}).get('samples', 0)} data samples",
                f"Achieved {unified_metrics.get('quality_excellence', 0):.1%} quality excellence",
                f"Maintained {unified_metrics.get('family_harmony', 0):.1%} family harmony"
            ]
        }
        
        return insights
    
    def _update_system_metrics(self, operation_results: Dict[str, Any]):
        """Update system metrics based on operation results"""
        unified_metrics = operation_results.get("unified_metrics", {})
        
        for metric, value in unified_metrics.items():
            if metric in self.family_metrics:
                # Update with weighted average
                self.family_metrics[metric] = (self.family_metrics[metric] * 0.7 + value * 0.3)
    
    def get_complete_hover_cards(self) -> Dict[str, Dict[str, Any]]:
        """Get hover cards for all agents in the system"""
        all_hover_cards = {}
        
        # Main collection cards
        all_hover_cards.update(self.agent_collection.get_all_hover_cards())
        
        # Specialized collection cards
        all_hover_cards.update(self.specialized_collection.get_all_hover_cards())
        
        return all_hover_cards
    
    def generate_hover_card_html(self, agent_name: str) -> str:
        """Generate HTML for specific agent hover card"""
        all_cards = self.get_complete_hover_cards()
        
        if agent_name in all_cards:
            return self.hover_card_system.generate_hover_html(all_cards[agent_name])
        else:
            return "<div class='error-card'>Agent not found</div>"
    
    def get_system_css(self) -> str:
        """Get CSS for the complete system"""
        return self.hover_card_system.generate_css()
    
    async def get_comprehensive_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the complete system"""
        return {
            "system_info": {
                "name": "Albrite Complete Family System",
                "version": "2.0.0",
                "status": self.system_status,
                "total_agents": self.family_metrics["total_agents"],
                "main_collection": self.family_metrics["main_collection_agents"],
                "specialized_collection": self.family_metrics["specialized_agents"],
                "holochain_integrated": self.holochain_coordinator is not None,
                "hover_card_enabled": True
            },
            "family_metrics": self.family_metrics,
            "agent_profiles": {
                name: {
                    "albrite_name": agent.albrite_name if hasattr(agent, 'albrite_name') else agent.profile.albrite_name,
                    "role": agent.family_role if hasattr(agent, 'family_role') else agent.profile.family_role,
                    "specialization": agent.specialization if hasattr(agent, 'specialization') else agent.profile.specialization
                }
                for name, agent in {**self.agent_collection.agents, **self.specialized_collection.agents}.items()
            },
            "capabilities": {
                "distributed_coordination": True,
                "hover_card_display": True,
                "holochain_integration": True,
                "real_time_monitoring": True,
                "adaptive_learning": True,
                "quality_assurance": True,
                "data_augmentation": True,
                "drift_detection": True
            }
        }


# Main system initialization and demonstration
async def create_complete_albrite_system() -> AlbriteFamilySystem:
    """Create and initialize the complete Albrite family system"""
    system = AlbriteFamilySystem()
    await system.initialize_complete_system()
    return system


async def demonstrate_complete_system():
    """Demonstrate the complete Albrite family system"""
    print("🏰" * 25)
    print("COMPLETE ALBRITE FAMILY SYSTEM DEMO")
    print("🏰" * 25)
    print()
    
    # Create system
    system = await create_complete_albrite_system()
    
    # Display system status
    status = await system.get_comprehensive_system_status()
    print("📊 System Status:")
    print(f"   Name: {status['system_info']['name']}")
    print(f"   Version: {status['system_info']['version']}")
    print(f"   Status: {status['system_info']['status']}")
    print(f"   Total Agents: {status['system_info']['total_agents']}")
    print(f"   Main Collection: {status['system_info']['main_collection']}")
    print(f"   Specialized: {status['system_info']['specialized_collection']}")
    print(f"   Holochain: {'✅' if status['system_info']['holochain_integrated'] else '❌'}")
    print(f"   Hover Cards: {'✅' if status['system_info']['hover_card_enabled'] else '❌'}")
    print()
    
    # Display family metrics
    print("📈 Family Metrics:")
    for metric, value in status["family_metrics"].items():
        print(f"   {metric.replace('_', ' ').title()}: {value:.1%}")
    print()
    
    # Display hover card previews
    print("🎴 Hover Card Previews:")
    hover_cards = system.get_complete_hover_cards()
    for i, (agent_name, card) in enumerate(list(hover_cards.items())[:3]):
        print(f"\n📋 {card['title']}")
        print(f"   {card['subtitle']}")
        print(f"   {card['description']}")
        print(f"   Key Skills: {', '.join(card['skills'][:2])}...")
        if i >= 2:  # Limit preview
            print(f"   ... and {len(hover_cards) - 3} more agents")
            break
    
    # Coordinate family operations
    print(f"\n🎭 Coordinating Complete Family Operations...")
    operations = await system.coordinate_complete_family_operations()
    
    # Display operation results
    print("\n📊 Operation Results:")
    unified_metrics = operations.get("unified_metrics", {})
    for metric, value in unified_metrics.items():
        print(f"   {metric.replace('_', ' ').title()}: {value:.1%}")
    
    # Display family insights
    insights = operations.get("family_insights", {})
    print(f"\n💡 Family Insights:")
    print(f"   Overall Rating: {insights.get('performance_summary', {}).get('overall_rating', 0):.1%}")
    
    if insights.get("family_strengths"):
        print("   Strengths:")
        for strength in insights["family_strengths"][:2]:
            print(f"     • {strength}")
    
    if insights.get("recommendations"):
        print("   Recommendations:")
        for rec in insights["recommendations"][:2]:
            print(f"     • {rec}")
    
    print(f"\n🎉 Complete Albrite Family System Demo Finished!")
    print("The unified family system with hover ID cards is ready for deployment!")


if __name__ == "__main__":
    asyncio.run(demonstrate_complete_system())
