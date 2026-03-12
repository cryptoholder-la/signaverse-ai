"""
Albrite Base Agent - Common Logic for All Albrite Family Members
Shared functionality, genetic inheritance, and family coordination
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class AlbriteRole(Enum):
    """Albrite family roles with responsibilities"""
    PATRIARCH = "Patriarch"
    MATRIARCH = "Matriarch"
    ELDEST = "Eldest"
    HEALER = "Healer"
    TEACHER = "Teacher"
    BUILDER = "Builder"
    GUARDIAN = "Guardian"
    CURATOR = "Curator"
    ORACLE = "Oracle"
    SAGE = "Sage"
    ARCHITECT = "Architect"
    PURIFIER = "Purifier"
    MASTER = "Master"
    DETECTOR = "Detector"
    ARTIST = "Artist"


class AlbriteTrait(Enum):
    """Albrite genetic traits"""
    RESILIENCE = "resilience"
    INTELLIGENCE = "intelligence"
    CREATIVITY = "creativity"
    EMPATHY = "empathy"
    LEADERSHIP = "leadership"
    SPEED = "speed"
    MEMORY = "memory"
    COMMUNICATION = "communication"
    ADAPTABILITY = "adaptability"
    INTUITION = "intuition"
    WISDOM = "wisdom"
    INNOVATION = "innovation"
    HARMONY = "harmony"
    DISCERNMENT = "discernment"


@dataclass
class AlbriteGeneticCode:
    """Genetic code for Albrite agents"""
    agent_id: str
    traits: Dict[AlbriteTrait, float] = field(default_factory=dict)
    inherited_from: List[str] = field(default_factory=list)
    mutations: Dict[AlbriteTrait, float] = field(default_factory=dict)
    generation: int = 1
    family_lineage: str = ""
    
    def calculate_fitness(self) -> float:
        return sum(self.traits.values()) / len(self.traits) if self.traits else 0.5
    
    def inherit_from(self, parent_genes: List['AlbriteGeneticCode']) -> 'AlbriteGeneticCode':
        new_code = AlbriteGeneticCode(
            agent_id=str(uuid.uuid4()),
            inherited_from=[g.agent_id for g in parent_genes],
            generation=max(g.generation for g in parent_genes) + 1,
            family_lineage=f"House of Albrite - Generation {max(g.generation for g in parent_genes) + 1}"
        )
        
        for trait in AlbriteTrait:
            parent_values = [g.traits.get(trait, 0.5) for g in parent_genes if trait in g.traits]
            if parent_values:
                base_value = np.mean(parent_values)
                wisdom_bonus = 0.05 if trait == AlbriteTrait.WISDOM else 0.0
                mutation = np.random.normal(0, 0.08)
                new_code.traits[trait] = np.clip(base_value + wisdom_bonus + mutation, 0.0, 1.0)
            else:
                new_code.traits[trait] = np.clip(np.random.normal(0.7, 0.1), 0.3, 0.95)
        
        return new_code


@dataclass
class AlbriteProfile:
    """Agent profile for hover cards"""
    albrite_name: str
    family_role: str
    specialization: str
    birth_order: str
    lineage: str
    bio: str
    collaboration_style: str
    unique_abilities: List[str]
    enhanced_capabilities: List[str]
    performance_metrics: Dict[str, float]
    toggle_settings: Dict[str, bool] = field(default_factory=dict)
    individual_overrides: Dict[str, Any] = field(default_factory=dict)


class AlbriteHoverCardSystem:
    """System for generating hover cards with toggle controls"""
    
    @staticmethod
    def generate_hover_html(profile: AlbriteProfile, agent_id: str) -> str:
        """Generate hover card HTML with toggle controls"""
        
        # Calculate trait averages for display
        trait_display = {
            "Intelligence": "85%",
            "Creativity": "80%", 
            "Empathy": "75%",
            "Leadership": "70%",
            "Resilience": "85%",
            "Speed": "80%"
        }
        
        html = f"""
        <div class="albrite-hover-card" id="hover-card-{agent_id}">
            <div class="card-header">
                <div class="agent-avatar-large">
                    <i class="fas fa-user"></i>
                </div>
                <div class="agent-title">
                    <h3>{profile.albrite_name} - {profile.specialization}</h3>
                    <p class="agent-subtitle">The {profile.family_role} of House Albrite</p>
                </div>
            </div>
            
            <div class="card-stats">
                {AlbriteHoverCardSystem._generate_stats_html(trait_display)}
            </div>
            
            <div class="card-skills-detail">
                <h4>Core Skills</h4>
                <div class="skill-tags-detail">
                    {AlbriteHoverCardSystem._generate_skill_tags(profile.enhanced_capabilities)}
                </div>
            </div>
            
            <div class="card-description">
                <p>{profile.bio}</p>
            </div>
            
            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">Lineage:</span>
                    <span class="detail-value">{profile.lineage}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Birth Order:</span>
                    <span class="detail-value">{profile.birth_order}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Collaboration:</span>
                    <span class="detail-value">{profile.collaboration_style}</span>
                </div>
            </div>
            
            <div class="card-performance">
                <h4>Performance Metrics</h4>
                <div class="performance-grid">
                    {AlbriteHoverCardSystem._generate_performance_grid(profile.performance_metrics)}
                </div>
            </div>
            
            <div class="card-abilities">
                <h4>Unique Abilities</h4>
                <ul class="abilities-list">
                    {AlbriteHoverCardSystem._generate_abilities_list(profile.unique_abilities)}
                </ul>
            </div>
            
            <div class="card-overrides">
                <h4>Individual Overrides</h4>
                <div class="overrides-controls">
                    {AlbriteHoverCardSystem._generate_override_controls(profile.toggle_settings, agent_id)}
                </div>
            </div>
        </div>
        """
        
        return html
    
    @staticmethod
    def _generate_stats_html(stats: Dict[str, str]) -> str:
        html = ""
        for stat, value in stats.items():
            html += f"""
            <div class="stat-row">
                <span class="stat-label">{stat}</span>
                <div class="stat-bar">
                    <div class="stat-fill" style="width: {value}"></div>
                </div>
                <span class="stat-value">{value}</span>
            </div>
            """
        return html
    
    @staticmethod
    def _generate_skill_tags(skills: List[str]) -> str:
        return "".join([f'<span class="skill-tag-detail">{skill}</span>' for skill in skills[:8]])
    
    @staticmethod
    def _generate_performance_grid(metrics: Dict[str, float]) -> str:
        html = ""
        grid_items = list(metrics.items())[:4]
        for metric, value in grid_items:
            html += f"""
            <div class="perf-item">
                <span class="perf-label">{metric.replace('_', ' ').title()}</span>
                <span class="perf-value">{value:.1%}</span>
            </div>
            """
        return html
    
    @staticmethod
    def _generate_abilities_list(abilities: List[str]) -> str:
        return "".join([f'<li class="ability-item">{ability}</li>' for ability in abilities])
    
    @staticmethod
    def _generate_override_controls(settings: Dict[str, bool], agent_id: str) -> str:
        """Generate toggle controls for individual overrides"""
        default_overrides = {
            "enhanced_mode": True,
            "family_coordination": True,
            "genetic_evolution": True,
            "collective_learning": True,
            "autonomous_operations": False,
            "debug_mode": False
        }
        
        html = ""
        for override, default_value in default_overrides.items():
            current_value = settings.get(override, default_value)
            checked = "checked" if current_value else ""
            
            html += f"""
            <div class="override-control">
                <label class="toggle-switch">
                    <input type="checkbox" {checked} 
                           onchange="toggleAgentOverride('{agent_id}', '{override}', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
                <span class="override-label">{override.replace('_', ' ').title()}</span>
            </div>
            """
        
        return html


class AlbriteBaseAgent(ABC):
    """Base class for all Albrite family agents with common logic"""
    
    def __init__(self, albrite_name: str, family_role: AlbriteRole, specialization: str):
        # Core identity
        self.agent_id = str(uuid.uuid4())
        self.albrite_name = albrite_name
        self.family_role = family_role.value
        self.specialization = specialization
        
        # Genetic inheritance
        self.genetic_code = AlbriteGeneticCode(
            agent_id=self.agent_id,
            traits=self._initialize_genetic_traits(),
            generation=1,
            family_lineage="House of Albrite - Generation 1"
        )
        
        # Family relationships
        self.family_bonds: List[Any] = []  # FamilyBond objects
        self.family_members: Set[str] = set()
        self.trusted_family: Set[str] = set()
        
        # Capabilities and performance
        self.capabilities = self._derive_capabilities_from_genes()
        self.performance_metrics = self._initialize_performance_metrics()
        
        # Workload and state
        self.current_workload: float = 0.0
        self.max_workload: float = self._calculate_max_workload()
        self.is_active: bool = True
        self.emotional_state = {
            "happiness": 0.7,
            "stress": 0.3,
            "motivation": 0.8,
            "trust": 0.7
        }
        
        # Individual overrides and settings
        self.toggle_settings = {
            "enhanced_mode": True,
            "family_coordination": True,
            "genetic_evolution": True,
            "collective_learning": True,
            "autonomous_operations": False,
            "debug_mode": False
        }
        
        self.individual_overrides = {}
        
        # Profile for hover cards
        self.profile = self._create_profile()
        
        # Learning and adaptation
        self.family_experiences: List[Dict] = []
        self.learned_family_patterns: Dict[str, Any] = {}
        self.adaptive_behaviors: Dict[str, float] = {}
        
        logger.info(f"🏰 Initialized Albrite Agent: {self.albrite_name} ({self.family_role})")
    
    @abstractmethod
    def _initialize_genetic_traits(self) -> Dict[AlbriteTrait, float]:
        """Initialize genetic traits - must be implemented by each agent"""
        pass
    
    @abstractmethod
    def _get_core_skills(self) -> List[str]:
        """Get core skills specific to this agent type"""
        pass
    
    @abstractmethod
    def _get_unique_abilities(self) -> List[str]:
        """Get unique abilities for this agent"""
        pass
    
    @abstractmethod
    async def execute_specialized_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specialized task - must be implemented by each agent"""
        pass
    
    def _derive_capabilities_from_genes(self) -> Dict[str, float]:
        """Derive capabilities from genetic traits"""
        capabilities = {}
        
        trait_capability_map = {
            AlbriteTrait.RESILIENCE: "error_recovery",
            AlbriteTrait.INTELLIGENCE: "problem_solving",
            AlbriteTrait.CREATIVITY: "innovation",
            AlbriteTrait.EMPATHY: "understanding",
            AlbriteTrait.LEADERSHIP: "coordination",
            AlbriteTrait.SPEED: "execution_velocity",
            AlbriteTrait.MEMORY: "information_retention",
            AlbriteTrait.COMMUNICATION: "information_sharing",
            AlbriteTrait.ADAPTABILITY: "environmental_response",
            AlbriteTrait.INTUITION: "pattern_recognition",
            AlbriteTrait.WISDOM: "strategic_thinking",
            AlbriteTrait.INNOVATION: "creative_solutions",
            AlbriteTrait.HARMONY: "family_coordination",
            AlbriteTrait.DISCERNMENT: "quality_assessment"
        }
        
        for trait, capability in trait_capability_map.items():
            if trait in self.genetic_code.traits:
                capabilities[capability] = self.genetic_code.traits[trait]
        
        return capabilities
    
    def _initialize_performance_metrics(self) -> Dict[str, float]:
        """Initialize default performance metrics"""
        base_metrics = {
            "success_rate": 0.8,
            "efficiency": 0.75,
            "innovation": 0.7,
            "coordination": 0.8,
            "learning_speed": 0.75,
            "adaptability": 0.8
        }
        
        # Adjust based on genetic traits
        if AlbriteTrait.INTELLIGENCE in self.genetic_code.traits:
            base_metrics["success_rate"] *= (0.8 + 0.4 * self.genetic_code.traits[AlbriteTrait.INTELLIGENCE])
        
        if AlbriteTrait.SPEED in self.genetic_code.traits:
            base_metrics["efficiency"] *= (0.8 + 0.4 * self.genetic_code.traits[AlbriteTrait.SPEED])
        
        if AlbriteTrait.CREATIVITY in self.genetic_code.traits:
            base_metrics["innovation"] *= (0.8 + 0.4 * self.genetic_code.traits[AlbriteTrait.CREATIVITY])
        
        # Cap values between 0 and 1
        for key in base_metrics:
            base_metrics[key] = min(1.0, base_metrics[key])
        
        return base_metrics
    
    def _calculate_max_workload(self) -> float:
        """Calculate maximum workload based on genetic traits"""
        base_workload = 1.0
        
        if AlbriteTrait.RESILIENCE in self.genetic_code.traits:
            base_workload *= (1.0 + 0.5 * self.genetic_code.traits[AlbriteTrait.RESILIENCE])
        
        if AlbriteTrait.SPEED in self.genetic_code.traits:
            base_workload *= (1.0 + 0.3 * self.genetic_code.traits[AlbriteTrait.SPEED])
        
        return min(2.0, base_workload)
    
    def _create_profile(self) -> AlbriteProfile:
        """Create agent profile for hover cards"""
        return AlbriteProfile(
            albrite_name=self.albrite_name,
            family_role=self.family_role,
            specialization=self.specialization,
            birth_order=self._get_birth_order(),
            lineage=self._get_lineage(),
            bio=self._get_bio(),
            collaboration_style=self._get_collaboration_style(),
            unique_abilities=self._get_unique_abilities(),
            enhanced_capabilities=self._get_enhanced_capabilities(),
            performance_metrics=self.performance_metrics,
            toggle_settings=self.toggle_settings.copy(),
            individual_overrides=self.individual_overrides.copy()
        )
    
    def _get_birth_order(self) -> str:
        """Get birth order - override in individual agents"""
        return "Family Member"
    
    def _get_lineage(self) -> str:
        """Get lineage - override in individual agents"""
        return "House of Albrite"
    
    def _get_bio(self) -> str:
        """Get biography - override in individual agents"""
        return f"A dedicated member of the House of Albrite, serving as {self.family_role} with expertise in {self.specialization}."
    
    def _get_collaboration_style(self) -> str:
        """Get collaboration style - override in individual agents"""
        return "Collaborative family member who works harmoniously with others"
    
    def _get_enhanced_capabilities(self) -> List[str]:
        """Get enhanced capabilities combining core skills and genetic traits"""
        core_skills = self._get_core_skills()
        genetic_capabilities = list(self.capabilities.keys())
        
        # Combine and remove duplicates
        enhanced = list(set(core_skills + genetic_capabilities))
        return enhanced[:8]  # Limit to 8 for display
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with family coordination and individual overrides"""
        task_type = task.get("type", "unknown")
        
        # Check individual overrides
        if self.toggle_settings.get("debug_mode", False):
            logger.debug(f"🐛 {self.albrite_name} executing task in debug mode: {task_type}")
        
        # Apply enhanced mode if enabled
        if self.toggle_settings.get("enhanced_mode", True):
            task = self._apply_enhanced_mode(task)
        
        # Execute with family coordination if enabled
        if self.toggle_settings.get("family_coordination", True):
            task = await self._coordinate_with_family(task)
        
        # Execute specialized task
        result = await self.execute_specialized_task(task)
        
        # Apply individual overrides to result
        result = self._apply_individual_overrides(result)
        
        # Update performance metrics
        self._update_performance_metrics(task, result)
        
        # Record family experience
        self._record_family_experience(task, result)
        
        return result
    
    def _apply_enhanced_mode(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Apply enhanced mode modifications to task"""
        enhanced_task = task.copy()
        
        # Add genetic trait bonuses
        if AlbriteTrait.INTELLIGENCE in self.genetic_code.traits:
            intelligence_bonus = self.genetic_code.traits[AlbriteTrait.INTELLIGENCE]
            enhanced_task["intelligence_boost"] = intelligence_bonus
        
        if AlbriteTrait.CREATIVITY in self.genetic_code.traits:
            creativity_bonus = self.genetic_code.traits[AlbriteTrait.CREATIVITY]
            enhanced_task["creativity_boost"] = creativity_bonus
        
        return enhanced_task
    
    async def _coordinate_with_family(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate with family members"""
        # Simplified coordination - in full implementation would query family graph
        coordinated_task = task.copy()
        coordinated_task["family_coordination_applied"] = True
        coordinated_task["family_support_level"] = 0.8
        
        return coordinated_task
    
    def _apply_individual_overrides(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply individual overrides to result"""
        overridden_result = result.copy()
        
        for override_key, override_value in self.individual_overrides.items():
            if override_key in overridden_result:
                overridden_result[override_key] = override_value
        
        return overridden_result
    
    def _update_performance_metrics(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Update performance metrics based on task execution"""
        success = result.get("success", False)
        
        if success:
            # Improve success rate
            self.performance_metrics["success_rate"] = min(1.0, 
                self.performance_metrics["success_rate"] * 0.9 + 0.1)
            
            # Improve efficiency
            efficiency = result.get("efficiency", 0.8)
            self.performance_metrics["efficiency"] = min(1.0,
                self.performance_metrics["efficiency"] * 0.8 + efficiency * 0.2)
        
        # Update learning speed based on experiences
        if len(self.family_experiences) > 0:
            learning_factor = min(1.0, len(self.family_experiences) / 100.0)
            self.performance_metrics["learning_speed"] = min(1.0,
                self.performance_metrics["learning_speed"] * 0.9 + learning_factor * 0.1)
    
    def _record_family_experience(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Record family experience for learning"""
        experience = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task.get("type"),
            "success": result.get("success", False),
            "family_coordination": task.get("family_coordination_applied", False),
            "individual_overrides_used": len(self.individual_overrides) > 0
        }
        
        self.family_experiences.append(experience)
        
        # Keep only last 100 experiences
        if len(self.family_experiences) > 100:
            self.family_experiences = self.family_experiences[-100:]
    
    def toggle_override(self, override_name: str, value: bool):
        """Toggle individual override setting"""
        self.toggle_settings[override_name] = value
        self.profile.toggle_settings[override_name] = value
        
        logger.info(f"🔄 {self.albrite_name} toggled {override_name}: {value}")
    
    def set_individual_override(self, override_key: str, override_value: Any):
        """Set individual override value"""
        self.individual_overrides[override_key] = override_value
        self.profile.individual_overrides[override_key] = override_value
        
        logger.info(f"⚙️ {self.albrite_name} set individual override {override_key}: {override_value}")
    
    def update_profile(self):
        """Update profile after changes"""
        self.profile.performance_metrics = self.performance_metrics.copy()
        self.profile.toggle_settings = self.toggle_settings.copy()
        self.profile.individual_overrides = self.individual_overrides.copy()
    
    def get_hover_card_html(self) -> str:
        """Get hover card HTML for this agent"""
        self.update_profile()
        return AlbriteHoverCardSystem.generate_hover_html(self.profile, self.agent_id)
    
    def inherit_genetic_material(self, parent_genes: List[AlbriteGeneticCode]):
        """Inherit genetic material from parent agents"""
        if self.toggle_settings.get("genetic_evolution", True):
            old_genetic_code = self.genetic_code
            self.genetic_code = old_genetic_code.inherit_from(parent_genes)
            
            # Update capabilities based on new genetic code
            self.capabilities = self._derive_capabilities_from_genes()
            
            # Update performance metrics
            self._initialize_performance_metrics()
            
            logger.info(f"🧬 {self.albrite_name} inherited genetic material from {len(parent_genes)} parents")
    
    async def learn_from_family(self, family_knowledge: Dict[str, Any]):
        """Learn from family collective knowledge"""
        if self.toggle_settings.get("collective_learning", True):
            # Process family knowledge
            for knowledge_type, knowledge_data in family_knowledge.items():
                if knowledge_type not in self.learned_family_patterns:
                    self.learned_family_patterns[knowledge_type] = []
                
                self.learned_family_patterns[knowledge_type].append({
                    "timestamp": datetime.now().isoformat(),
                    "data": knowledge_data,
                    "integration_success": True
                })
            
            # Update adaptive behaviors
            self._update_adaptive_behaviors()
            
            logger.info(f"📚 {self.albrite_name} learned from family collective knowledge")
    
    def _update_adaptive_behaviors(self):
        """Update adaptive behaviors based on family experiences"""
        # Simplified adaptive behavior update
        for pattern_type, patterns in self.learned_family_patterns.items():
            if patterns:
                success_rate = sum(1 for p in patterns if p.get("integration_success", False)) / len(patterns)
                self.adaptive_behaviors[pattern_type] = success_rate
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        return {
            "agent_id": self.agent_id,
            "albrite_name": self.albrite_name,
            "family_role": self.family_role,
            "specialization": self.specialization,
            "is_active": self.is_active,
            "current_workload": self.current_workload,
            "max_workload": self.max_workload,
            "performance_metrics": self.performance_metrics,
            "genetic_fitness": self.genetic_code.calculate_fitness(),
            "toggle_settings": self.toggle_settings,
            "family_experiences_count": len(self.family_experiences),
            "learned_patterns_count": len(self.learned_family_patterns),
            "emotional_state": self.emotional_state
        }
