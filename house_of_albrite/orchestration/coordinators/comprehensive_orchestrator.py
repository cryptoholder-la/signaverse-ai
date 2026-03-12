"""
Albrite Comprehensive Family Orchestrator - Complete System Controller
Coordinates all 13 elite agents with toggle controls and hover card management
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import sys

# Add the project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Note: Using consolidated agent system for now
# TODO: Replace with individual agent imports when they are organized in new structure
from core.agents.albrite_collection import AlbriteAgentCollection
from core.agents.expert_agents import create_house_of_albrite, AlbriteFamilySystem

logger = logging.getLogger(__name__)


class AlbriteComprehensiveOrchestrator:
    """Comprehensive orchestrator for the complete Albrite family system"""
    
    def __init__(self):
        self.family_agents = {}
        self.agent_status = {}
        self.system_metrics = {}
        self.hover_card_registry = {}
        self.toggle_registry = {}
        
        # Initialize the complete family using consolidated agent system
        self._initialize_consolidated_family()
        self._setup_agent_relationships()
        self._initialize_system_metrics()
        
        logger.info("🏰 Albrite Comprehensive Orchestrator initialized with 13 elite agents")
    
    def _initialize_consolidated_family(self):
        """Initialize family using consolidated agent system"""
        # Create the consolidated family system
        self.albrite_family_system = create_house_of_albrite()
        
        # Get all agents from the consolidated system
        self.family_agents = self.albrite_family_system.family_agents
        
        # Initialize agent status for all agents
        for agent_id, agent in self.family_agents.items():
            self.agent_status[agent_id] = {
                "name": agent.albrite_name,
                "role": agent.family_role,
                "specialization": agent.specialization,
                "active": True,
                "last_activity": datetime.now().isoformat(),
                "tasks_completed": 0,
                "success_rate": agent.performance_metrics.get("success_rate", 0.85),
                "elite_status": "enhanced" if hasattr(agent, 'enhanced_capabilities') else "original"
            }
            
            # Register hover card
            self.hover_card_registry[agent_id] = {
                "agent": agent,
                "html": agent.get_hover_card_html() if hasattr(agent, 'get_hover_card_html') else f"<div>Hover card for {agent.albrite_name}</div>",
                "last_updated": datetime.now().isoformat()
            }
            
            # Register toggle settings
            self.toggle_registry[agent_id] = {
                "enhanced_mode": True,
                "ai_optimization": True,
                "collaboration_mode": True
            }
        
        logger.info(f"✅ Initialized {len(self.family_agents)} agents from consolidated family system")
    
    def _setup_agent_relationships(self):
        """Setup comprehensive family relationships and bonds"""
        # Define family relationships
        relationships = {
            # Core family relationships
            "seraphina": {"siblings": ["alexander", "isabella", "marcus", "victoria"], "collaborators": ["aurora", "benjamin", "charlotte"]},
            "alexander": {"siblings": ["seraphina", "isabella", "marcus", "victoria"], "collaborators": ["aurora", "benjamin", "henry"]},
            "isabella": {"siblings": ["seraphina", "alexander", "marcus", "victoria"], "collaborators": ["aurora", "daniel", "elena"]},
            "marcus": {"siblings": ["seraphina", "alexander", "isabella", "victoria"], "collaborators": ["aurora", "charlotte", "felix"]},
            "victoria": {"siblings": ["seraphina", "alexander", "isabella", "marcus"], "collaborators": ["aurora", "felix", "henry"]},
            "aurora": {"collaborators": ["seraphina", "alexander", "isabella", "marcus", "victoria", "henry"]},
            
            # Enhanced agent relationships
            "benjamin": {"collaborators": ["seraphina", "alexander", "henry", "charlotte"]},
            "charlotte": {"collaborators": ["seraphina", "marcus", "benjamin", "daniel"]},
            "daniel": {"collaborators": ["isabella", "marcus", "charlotte", "elena"]},
            "elena": {"collaborators": ["isabella", "daniel", "felix", "george"]},
            "felix": {"collaborators": ["victoria", "marcus", "elena", "george"]},
            "george": {"collaborators": ["victoria", "felix", "elena", "henry"]},
            "henry": {"collaborators": ["alexander", "victoria", "benjamin", "george"]}
        }
        
        # Store relationships for agent use
        for agent_id, agent in self.family_agents.items():
            if agent_id in relationships:
                agent.family_members.update(relationships[agent_id].get("siblings", []))
                agent.trusted_family.update(relationships[agent_id].get("collaborators", []))
    
    def _initialize_system_metrics(self):
        """Initialize comprehensive system-wide metrics"""
        self.system_metrics = {
            "collective_intelligence": 0.0,
            "family_harmony": 0.0,
            "coordination_efficiency": 0.0,
            "innovation_capacity": 0.0,
            "quality_excellence": 0.0,
            "learning_velocity": 0.0,
            "system_resilience": 0.0,
            "adaptability_score": 0.0,
            "creative_potential": 0.0,
            "active_agents": len(self.family_agents),
            "elite_agents": len([a for a in self.family_agents.values() if hasattr(a, 'augmentation_engine')]),
            "total_tasks_completed": 0,
            "average_success_rate": 0.0
        }
        
        self._update_system_metrics()
    
    def _update_system_metrics(self):
        """Update comprehensive system metrics based on agent performance"""
        if not self.family_agents:
            return
        
        # Calculate collective intelligence
        intelligence_scores = []
        for agent in self.family_agents.values():
            if hasattr(agent, 'genetic_code') and hasattr(agent.genetic_code, 'traits'):
                for trait, value in agent.genetic_code.traits.items():
                    if trait.value == "intelligence":
                        intelligence_scores.append(value)
                        break
        
        if intelligence_scores:
            self.system_metrics["collective_intelligence"] = sum(intelligence_scores) / len(intelligence_scores)
        
        # Calculate family harmony (average emotional state)
        harmony_scores = []
        for agent in self.family_agents.values():
            if hasattr(agent, 'emotional_state'):
                harmony_scores.append(agent.emotional_state.get("happiness", 0.7))
        
        if harmony_scores:
            self.system_metrics["family_harmony"] = sum(harmony_scores) / len(harmony_scores)
        
        # Calculate innovation capacity
        innovation_scores = []
        for agent in self.family_agents.values():
            if hasattr(agent, 'genetic_code') and hasattr(agent.genetic_code, 'traits'):
                for trait, value in agent.genetic_code.traits.items():
                    if trait.value == "innovation":
                        innovation_scores.append(value)
                        break
        
        if innovation_scores:
            self.system_metrics["innovation_capacity"] = sum(innovation_scores) / len(innovation_scores)
        
        # Calculate quality excellence
        quality_scores = []
        for agent in self.family_agents.values():
            if hasattr(agent, 'genetic_code') and hasattr(agent.genetic_code, 'traits'):
                for trait, value in agent.genetic_code.traits.items():
                    if trait.value == "discernment" or trait.value == "wisdom":
                        quality_scores.append(value)
        
        if quality_scores:
            self.system_metrics["quality_excellence"] = sum(quality_scores) / len(quality_scores)
        
        # Calculate adaptability score
        adaptability_scores = []
        for agent in self.family_agents.values():
            if hasattr(agent, 'genetic_code') and hasattr(agent.genetic_code, 'traits'):
                for trait, value in agent.genetic_code.traits.items():
                    if trait.value == "adaptability":
                        adaptability_scores.append(value)
                        break
        
        if adaptability_scores:
            self.system_metrics["adaptability_score"] = sum(adaptability_scores) / len(adaptability_scores)
        
        # Calculate creative potential
        creativity_scores = []
        for agent in self.family_agents.values():
            if hasattr(agent, 'genetic_code') and hasattr(agent.genetic_code, 'traits'):
                for trait, value in agent.genetic_code.traits.items():
                    if trait.value == "creativity":
                        creativity_scores.append(value)
                        break
        
        if creativity_scores:
            self.system_metrics["creative_potential"] = sum(creativity_scores) / len(creativity_scores)
        
        # Update other metrics
        self.system_metrics["active_agents"] = len([a for a in self.family_agents.values() if a.is_active])
        self.system_metrics["elite_agents"] = len([a for a in self.family_agents.values() if hasattr(a, 'augmentation_engine')])
        self.system_metrics["total_tasks_completed"] = sum(s.get("tasks_completed", 0) for s in self.agent_status.values())
        
        # Calculate average success rate
        success_rates = []
        for status in self.agent_status.values():
            success_rates.append(status.get("success_rate", 0.8))
        
        if success_rates:
            self.system_metrics["average_success_rate"] = sum(success_rates) / len(success_rates)
        
        # Calculate coordination efficiency
        self.system_metrics["coordination_efficiency"] = (
            self.system_metrics["collective_intelligence"] * 0.3 +
            self.system_metrics["family_harmony"] * 0.3 +
            self.system_metrics["adaptability_score"] * 0.4
        )
        
        # Calculate learning velocity
        self.system_metrics["learning_velocity"] = (
            self.system_metrics["innovation_capacity"] * 0.4 +
            self.system_metrics["creative_potential"] * 0.3 +
            self.system_metrics["adaptability_score"] * 0.3
        )
        
        # Calculate system resilience
        self.system_metrics["system_resilience"] = (
            self.system_metrics["quality_excellence"] * 0.3 +
            self.system_metrics["adaptability_score"] * 0.4 +
            self.system_metrics["family_harmony"] * 0.3
        )
    
    async def coordinate_family_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate task execution across family agents"""
        task_type = task.get("type", "unknown")
        target_agent = task.get("target_agent", "auto")
        
        logger.info(f"🎭 Coordinating comprehensive family task: {task_type}")
        
        # Determine best agent for task
        if target_agent == "auto":
            target_agent = self._select_best_agent(task_type)
        
        if target_agent not in self.family_agents:
            return {
                "success": False,
                "error": f"Agent {target_agent} not found",
                "available_agents": list(self.family_agents.keys())
            }
        
        # Execute task with selected agent
        agent = self.family_agents[target_agent]
        
        try:
            # Update agent status
            self.agent_status[target_agent]["last_activity"] = datetime.now().isoformat()
            
            # Execute task
            result = await agent.execute_task(task)
            
            # Update agent metrics
            if result.get("success", False):
                self.agent_status[target_agent]["tasks_completed"] += 1
                
                # Update success rate
                tasks_completed = self.agent_status[target_agent]["tasks_completed"]
                current_success_rate = self.agent_status[target_agent]["success_rate"]
                new_success_rate = (current_success_rate * (tasks_completed - 1) + 1.0) / tasks_completed
                self.agent_status[target_agent]["success_rate"] = new_success_rate
            
            # Update system metrics
            self._update_system_metrics()
            
            # Update hover card if needed
            self._update_hover_card(target_agent)
            
            return {
                "success": True,
                "task_type": task_type,
                "executed_by": target_agent,
                "agent_name": agent.albrite_name,
                "agent_specialization": agent.specialization,
                "elite_status": self.agent_status[target_agent]["elite_status"],
                "result": result,
                "system_metrics": self.system_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type,
                "executed_by": target_agent
            }
    
    def _select_best_agent(self, task_type: str) -> str:
        """Select best agent for task type with comprehensive mapping"""
        # Comprehensive agent specialization mapping
        task_agent_mapping = {
            # Core data tasks
            "data_health_assessment": "seraphina",
            "data_purification": "aurora",
            "source_discovery": "alexander",
            "elite_scraping": "benjamin",
            "content_scraping": "alexander",
            "quality_assessment": "isabella",
            "bias_detection": "elena",
            "knowledge_transfer": "marcus",
            "skill_development": "marcus",
            "system_augmentation": "victoria",
            "innovation_creation": "victoria",
            
            # Enhanced agent tasks
            "elite_formatting": "charlotte",
            "schema_evolution": "charlotte",
            "elite_labeling": "daniel",
            "confidence_assessment": "daniel",
            "advanced_bias_detection": "elena",
            "fairness_analysis": "elena",
            "elite_feature_discovery": "felix",
            "pattern_recognition": "felix",
            "elite_drift_detection": "george",
            "distribution_analysis": "george",
            "elite_augmentation": "henry",
            "advanced_synthesis": "henry",
            
            # General tasks
            "low_quality_removal": "aurora",
            "quality_filtering": "aurora",
            "format_sample": "charlotte",
            "validate_schema": "charlotte",
            "auto_label": "daniel",
            "filter_low_confidence": "daniel",
            "evaluate_predictions": "elena",
            "detect_bias": "elena",
            "extract_sign_features": "felix",
            "detect_distribution_shift": "george",
            "temporal_shift": "henry",
            "noise_injection": "henry"
        }
        
        return task_agent_mapping.get(task_type, "seraphina")  # Default to Seraphina
    
    def get_agent_hover_card(self, agent_id: str) -> Optional[str]:
        """Get hover card HTML for agent"""
        if agent_id in self.hover_card_registry:
            return self.hover_card_registry[agent_id]["html"]
        return None
    
    def _update_hover_card(self, agent_id: str):
        """Update hover card for agent"""
        if agent_id in self.family_agents:
            agent = self.family_agents[agent_id]
            self.hover_card_registry[agent_id] = {
                "agent": agent,
                "html": agent.get_hover_card_html(),
                "last_updated": datetime.now().isoformat()
            }
    
    def toggle_agent_override(self, agent_id: str, override_name: str, value: bool):
        """Toggle agent override setting"""
        if agent_id in self.family_agents:
            agent = self.family_agents[agent_id]
            agent.toggle_override(override_name, value)
            self.toggle_registry[agent_id][override_name] = value
            
            # Update hover card
            self._update_hover_card(agent_id)
            
            logger.info(f"🔄 Toggled {override_name} for {agent.albrite_name}: {value}")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "override_name": override_name,
                "value": value,
                "agent_name": agent.albrite_name,
                "elite_status": self.agent_status[agent_id]["elite_status"]
            }
        
        return {
            "success": False,
            "error": f"Agent {agent_id} not found"
        }
    
    def set_agent_individual_override(self, agent_id: str, override_key: str, override_value: Any):
        """Set individual override for agent"""
        if agent_id in self.family_agents:
            agent = self.family_agents[agent_id]
            agent.set_individual_override(override_key, override_value)
            
            # Update hover card
            self._update_hover_card(agent_id)
            
            logger.info(f"⚙️ Set individual override {override_key} for {agent.albrite_name}: {override_value}")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "override_key": override_key,
                "override_value": override_value,
                "agent_name": agent.albrite_name,
                "elite_status": self.agent_status[agent_id]["elite_status"]
            }
        
        return {
            "success": False,
            "error": f"Agent {agent_id} not found"
        }
    
    def get_family_status(self) -> Dict[str, Any]:
        """Get comprehensive family status"""
        return {
            "system_metrics": self.system_metrics,
            "agent_count": len(self.family_agents),
            "elite_agents": self.system_metrics["elite_agents"],
            "active_agents": len([a for a in self.family_agents.values() if a.is_active]),
            "agent_status": self.agent_status,
            "toggle_settings": self.toggle_registry,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about specific agent"""
        if agent_id in self.family_agents:
            agent = self.family_agents[agent_id]
            
            return {
                "basic_info": {
                    "agent_id": agent.agent_id,
                    "albrite_name": agent.albrite_name,
                    "family_role": agent.family_role,
                    "specialization": agent.specialization,
                    "elite_status": self.agent_status[agent_id]["elite_status"]
                },
                "genetic_traits": {
                    trait.value: value for trait, value in agent.genetic_code.traits.items()
                },
                "performance_metrics": agent.performance_metrics,
                "toggle_settings": agent.toggle_settings,
                "individual_overrides": agent.individual_overrides,
                "status": self.agent_status.get(agent_id, {}),
                "hover_card_available": agent_id in self.hover_card_registry
            }
        
        return None
    
    async def coordinate_family_collaboration(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate collaboration between multiple family agents"""
        task_type = task.get("type", "collaboration")
        participating_agents = task.get("agents", ["seraphina", "alexander", "isabella"])
        
        logger.info(f"🤝 Coordinating comprehensive family collaboration: {task_type}")
        
        # Filter valid agents
        valid_agents = [agent_id for agent_id in participating_agents if agent_id in self.family_agents]
        
        if not valid_agents:
            return {
                "success": False,
                "error": "No valid agents for collaboration",
                "requested_agents": participating_agents,
                "available_agents": list(self.family_agents.keys())
            }
        
        # Execute collaborative task
        collaboration_results = {}
        
        for agent_id in valid_agents:
            agent = self.family_agents[agent_id]
            
            # Create agent-specific subtask
            subtask = {
                **task,
                "collaboration_role": agent_id,
                "family_coordination": True,
                "collaborative_context": {
                    "participating_agents": valid_agents,
                    "collaboration_id": str(uuid.uuid4())
                }
            }
            
            try:
                result = await agent.execute_task(subtask)
                collaboration_results[agent_id] = {
                    "success": True,
                    "result": result,
                    "agent_name": agent.albrite_name,
                    "elite_status": self.agent_status[agent_id]["elite_status"]
                }
                
                # Update agent status
                self.agent_status[agent_id]["last_activity"] = datetime.now().isoformat()
                
            except Exception as e:
                collaboration_results[agent_id] = {
                    "success": False,
                    "error": str(e),
                    "agent_name": agent.albrite_name,
                    "elite_status": self.agent_status[agent_id]["elite_status"]
                }
        
        # Calculate collaboration success
        successful_agents = [agent_id for agent_id, result in collaboration_results.items() if result["success"]]
        collaboration_success = len(successful_agents) / len(valid_agents)
        
        # Update system metrics
        self._update_system_metrics()
        
        return {
            "success": True,
            "task_type": task_type,
            "participating_agents": valid_agents,
            "collaboration_success": collaboration_success,
            "successful_agents": successful_agents,
            "results": collaboration_results,
            "system_metrics": self.system_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        dashboard_data = {
            "system_overview": {
                "total_agents": len(self.family_agents),
                "elite_agents": self.system_metrics["elite_agents"],
                "active_agents": len([a for a in self.family_agents.values() if a.is_active]),
                "system_metrics": self.system_metrics
            },
            "agents": []
        }
        
        # Add agent data for dashboard
        for agent_id, agent in self.family_agents.items():
            agent_data = {
                "agent_id": agent_id,
                "albrite_name": agent.albrite_name,
                "family_role": agent.family_role,
                "specialization": agent.specialization,
                "elite_status": self.agent_status[agent_id]["elite_status"],
                "is_active": agent.is_active,
                "performance_metrics": agent.performance_metrics,
                "toggle_settings": agent.toggle_settings,
                "genetic_fitness": agent.genetic_code.calculate_fitness(),
                "hover_card_html": self.get_agent_hover_card(agent_id),
                "status": self.agent_status.get(agent_id, {})
            }
            dashboard_data["agents"].append(agent_data)
        
        return dashboard_data
    
    async def run_system_demonstration(self) -> Dict[str, Any]:
        """Run a comprehensive demonstration of the system capabilities"""
        logger.info("🎭 Running Albrite Comprehensive Family System Demonstration")
        
        demonstration_results = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.get_family_status(),
            "demonstration_tasks": []
        }
        
        # Demonstrate individual agent capabilities
        demo_tasks = [
            {"type": "data_health_assessment", "dataset_id": "demo_dataset"},
            {"type": "source_discovery", "domain": "demo_domain"},
            {"type": "quality_assessment", "assessment_type": "comprehensive"},
            {"type": "knowledge_transfer", "domain": "demo_knowledge"},
            {"type": "system_augmentation", "target_system": "demo_system"},
            
            # Enhanced agent demonstrations
            {"type": "elite_scraping", "sources": ["demo_source_1", "demo_source_2"]},
            {"type": "elite_formatting", "sample": {"text": "demo", "pose": []}},
            {"type": "elite_labeling", "data": [{"id": 1}, {"id": 2}]},
            {"type": "advanced_bias_detection", "data": {"samples": []}},
            {"type": "elite_feature_discovery", "data": {"features": []}},
            {"type": "elite_drift_detection", "baseline_data": {}, "current_data": {}},
            {"type": "elite_augmentation", "data": [{"id": 1}]}
        ]
        
        for task in demo_tasks:
            result = await self.coordinate_family_task(task)
            demonstration_results["demonstration_tasks"].append(result)
        
        # Demonstrate collaboration
        collab_task = {
            "type": "family_coordination",
            "agents": ["seraphina", "alexander", "isabella", "benjamin", "charlotte"],
            "goal": "coordinate_comprehensive_data_processing"
        }
        
        collab_result = await self.coordinate_family_collaboration(collab_task)
        demonstration_results["collaboration_demo"] = collab_result
        
        # Demonstrate toggle functionality
        toggle_demo = self.toggle_agent_override("seraphina", "enhanced_mode", False)
        demonstration_results["toggle_demo"] = toggle_demo
        
        # Reset toggle
        self.toggle_agent_override("seraphina", "enhanced_mode", True)
        
        logger.info("✅ Comprehensive system demonstration completed")
        
        return demonstration_results


# Global comprehensive orchestrator instance
albrite_comprehensive_orchestrator = AlbriteComprehensiveOrchestrator()


# JavaScript toggle function for hover cards
def generate_comprehensive_toggle_javascript() -> str:
    """Generate comprehensive JavaScript for toggle controls"""
    return """
<script>
function toggleAgentOverride(agentId, overrideName, value) {
    // Send toggle request to orchestrator
    fetch('/api/toggle_override', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            agent_id: agentId,
            override_name: overrideName,
            value: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Toggled ${overrideName} for ${data.agent_name} (${data.elite_status}): ${value}`);
            // Update UI if needed
            updateAgentCard(agentId);
            showNotification(`${data.agent_name}: ${overrideName.replace('_', ' ').title()} ${value ? 'enabled' : 'disabled'}`, 'success');
        } else {
            console.error('Toggle failed:', data.error);
            showNotification(`Toggle failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling override:', error);
        showNotification('Error toggling override', 'error');
    });
}

function updateAgentCard(agentId) {
    // Refresh agent hover card
    fetch(`/api/agent_hover_card/${agentId}`)
    .then(response => response.text())
    .then(html => {
        const cardElement = document.getElementById(`hover-card-${agentId}`);
        if (cardElement) {
            cardElement.outerHTML = html;
        }
    })
    .catch(error => {
        console.error('Error updating agent card:', error);
    });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}
</script>
"""


# Flask API endpoints (for web interface)
def create_comprehensive_flask_app():
    """Create comprehensive Flask app for web interface"""
    from flask import Flask, request, jsonify, render_template_string
    
    app = Flask(__name__)
    
    @app.route('/')
    def dashboard():
        """Main comprehensive dashboard"""
        dashboard_data = albrite_comprehensive_orchestrator.generate_dashboard_data()
        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Albrite Comprehensive Family Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .agent-card { border: 1px solid #ddd; margin: 10px; padding: 15px; border-radius: 8px; background: white; }
        .agent-name { font-weight: bold; color: #2c3e50; }
        .agent-role { color: #7f8c8d; font-style: italic; }
        .elite-badge { background: #f39c12; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
        .metrics { margin-top: 10px; }
        .metric { display: inline-block; margin: 5px; padding: 3px 8px; background: #ecf0f1; border-radius: 4px; font-size: 12px; }
        .toggle-controls { margin-top: 10px; }
        .toggle-switch { position: relative; display: inline-block; width: 50px; height: 24px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 24px; }
        .toggle-slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .toggle-slider { background-color: #2196F3; }
        input:checked + .toggle-slider:before { transform: translateX(26px); }
    </style>
    {{ toggle_js|safe }}
</head>
<body>
    <h1>🏰 Albrite Comprehensive Family Dashboard</h1>
    
    <div class="system-overview">
        <h2>System Overview</h2>
        <p>Total Agents: {{ dashboard.agents|length }}</p>
        <p>Elite Agents: {{ dashboard.system_overview.elite_agents }}</p>
        <p>Active Agents: {{ dashboard.system_overview.active_agents }}</p>
        <p>Collective Intelligence: {{ "%.2f"|format(dashboard.system_overview.system_metrics.collective_intelligence) }}</p>
        <p>Innovation Capacity: {{ "%.2f"|format(dashboard.system_overview.system_metrics.innovation_capacity) }}</p>
        <p>Quality Excellence: {{ "%.2f"|format(dashboard.system_overview.system_metrics.quality_excellence) }}</p>
    </div>
    
    <div class="agents">
        <h2>Comprehensive Family Agents</h2>
        {% for agent in dashboard.agents %}
        <div class="agent-card" id="agent-{{ agent.agent_id }}">
            <div class="agent-name">
                {{ agent.albrite_name }}
                {% if agent.elite_status == 'enhanced' %}
                <span class="elite-badge">ELITE</span>
                {% endif %}
            </div>
            <div class="agent-role">{{ agent.family_role }} - {{ agent.specialization }}</div>
            
            <div class="metrics">
                {% for metric, value in agent.performance_metrics.items() %}
                <span class="metric">{{ metric }}: {{ "%.1f"|format(value*100) }}%</span>
                {% endfor %}
            </div>
            
            <span class="agent-status status-active">{{ 'Active' if agent.is_active else 'Inactive' }}</span>
            
            <div class="toggle-controls">
                {% for toggle, value in agent.toggle_settings.items() %}
                <div style="margin: 5px 0;">
                    <label class="toggle-switch">
                        <input type="checkbox" {{ 'checked' if value else '' }} 
                               onchange="toggleAgentOverride('{{ agent.agent_id }}', '{{ toggle }}', this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                    <span style="margin-left: 10px;">{{ toggle.replace('_', ' ').title() }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """, dashboard=dashboard_data, toggle_js=generate_comprehensive_toggle_javascript())
    
    @app.route('/api/toggle_override', methods=['POST'])
    def toggle_override():
        """Toggle agent override"""
        data = request.json
        result = albrite_comprehensive_orchestrator.toggle_agent_override(
            data['agent_id'],
            data['override_name'],
            data['value']
        )
        return jsonify(result)
    
    @app.route('/api/agent_hover_card/<agent_id>')
    def agent_hover_card(agent_id):
        """Get agent hover card HTML"""
        html = albrite_comprehensive_orchestrator.get_agent_hover_card(agent_id)
        return html or "<div>Agent not found</div>"
    
    @app.route('/api/family_status')
    def family_status():
        """Get comprehensive family status"""
        return jsonify(albrite_comprehensive_orchestrator.get_family_status())
    
    @app.route('/api/coordinate_task', methods=['POST'])
    def coordinate_task():
        """Coordinate comprehensive family task"""
        task = request.json
        result = asyncio.run(albrite_comprehensive_orchestrator.coordinate_family_task(task))
        return jsonify(result)
    
    return app


if __name__ == "__main__":
    # Run comprehensive demonstration
    async def demo():
        results = await albrite_comprehensive_orchestrator.run_system_demonstration()
        print("🎉 Albrite Comprehensive Family System Demo Results:")
        print(json.dumps(results, indent=2, default=str))
    
    asyncio.run(demo())
