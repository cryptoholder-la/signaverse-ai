"""
Albrite Family Orchestrator - Main System Controller
Coordinates all family agents with toggle controls and hover card management
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import sys

# Add the home_folder to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.seraphina_data_guardian import SeraphinaDataGuardian
from agents.alexander_content_curator import AlexanderContentCurator
from agents.isabella_quality_oracle import IsabellaQualityOracle
from agents.marcus_knowledge_keeper import MarcusKnowledgeKeeper
from agents.victory_innovation_architect import VictoriaInnovationArchitect
from agents.aurora_data_purifier import AuroraDataPurifier

logger = logging.getLogger(__name__)


class AlbriteFamilyOrchestrator:
    """Main orchestrator for the Albrite family system"""
    
    def __init__(self):
        self.family_agents = {}
        self.agent_status = {}
        self.system_metrics = {}
        self.hover_card_registry = {}
        self.toggle_registry = {}
        
        # Initialize the family
        self._initialize_family_agents()
        self._setup_agent_relationships()
        self._initialize_system_metrics()
        
        logger.info("🏰 Albrite Family Orchestrator initialized")
    
    def _initialize_family_agents(self):
        """Initialize all family agents"""
        # Main collection agents
        self.family_agents["seraphina"] = SeraphinaDataGuardian()
        self.family_agents["alexander"] = AlexanderContentCurator()
        self.family_agents["isabella"] = IsabellaQualityOracle()
        self.family_agents["marcus"] = MarcusKnowledgeKeeper()
        self.family_agents["victoria"] = VictoriaInnovationArchitect()
        
        # Specialized agents
        self.family_agents["aurora"] = AuroraDataPurifier()
        
        # Initialize agent status
        for agent_id, agent in self.family_agents.items():
            self.agent_status[agent_id] = {
                "name": agent.albrite_name,
                "role": agent.family_role,
                "active": True,
                "last_activity": datetime.now().isoformat(),
                "tasks_completed": 0,
                "success_rate": 0.8
            }
            
            # Register hover card
            self.hover_card_registry[agent_id] = {
                "agent": agent,
                "html": agent.get_hover_card_html(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Register toggle settings
            self.toggle_registry[agent_id] = agent.toggle_settings.copy()
        
        logger.info(f"✅ Initialized {len(self.family_agents)} family agents")
    
    def _setup_agent_relationships(self):
        """Setup family relationships and bonds"""
        # Define family relationships
        relationships = {
            "seraphina": {"siblings": ["alexander", "isabella", "marcus", "victoria"], "collaborators": ["aurora"]},
            "alexander": {"siblings": ["seraphina", "isabella", "marcus", "victoria"], "collaborators": ["aurora"]},
            "isabella": {"siblings": ["seraphina", "alexander", "marcus", "victoria"], "collaborators": ["aurora"]},
            "marcus": {"siblings": ["seraphina", "alexander", "isabella", "victoria"], "collaborators": ["aurora"]},
            "victoria": {"siblings": ["seraphina", "alexander", "isabella", "marcus"], "collaborators": ["aurora"]},
            "aurora": {"collaborators": ["seraphina", "alexander", "isabella", "marcus", "victoria"]}
        }
        
        # Store relationships for agent use
        for agent_id, agent in self.family_agents.items():
            if agent_id in relationships:
                agent.family_members.update(relationships[agent_id].get("siblings", []))
                agent.trusted_family.update(relationships[agent_id].get("collaborators", []))
    
    def _initialize_system_metrics(self):
        """Initialize system-wide metrics"""
        self.system_metrics = {
            "collective_intelligence": 0.0,
            "family_harmony": 0.0,
            "coordination_efficiency": 0.0,
            "innovation_capacity": 0.0,
            "quality_excellence": 0.0,
            "learning_velocity": 0.0,
            "system_resilience": 0.0,
            "active_agents": len(self.family_agents),
            "total_tasks_completed": 0,
            "average_success_rate": 0.0
        }
        
        self._update_system_metrics()
    
    def _update_system_metrics(self):
        """Update system metrics based on agent performance"""
        if not self.family_agents:
            return
        
        # Calculate collective intelligence
        intelligence_scores = []
        for agent in self.family_agents.values():
            if AlbriteTrait.INTELLIGENCE in agent.genetic_code.traits:
                intelligence_scores.append(agent.genetic_code.traits[AlbriteTrait.INTELLIGENCE])
        
        if intelligence_scores:
            self.system_metrics["collective_intelligence"] = sum(intelligence_scores) / len(intelligence_scores)
        
        # Calculate family harmony (average emotional state)
        harmony_scores = []
        for agent in self.family_agents.values():
            harmony_scores.append(agent.emotional_state.get("happiness", 0.7))
        
        if harmony_scores:
            self.system_metrics["family_harmony"] = sum(harmony_scores) / len(harmony_scores)
        
        # Calculate average success rate
        success_rates = []
        for status in self.agent_status.values():
            success_rates.append(status.get("success_rate", 0.8))
        
        if success_rates:
            self.system_metrics["average_success_rate"] = sum(success_rates) / len(success_rates)
        
        # Update other metrics
        self.system_metrics["active_agents"] = len([a for a in self.family_agents.values() if a.is_active])
        self.system_metrics["total_tasks_completed"] = sum(s.get("tasks_completed", 0) for s in self.agent_status.values())
    
    async def coordinate_family_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate task execution across family agents"""
        task_type = task.get("type", "unknown")
        target_agent = task.get("target_agent", "auto")
        
        logger.info(f"🎭 Coordinating family task: {task_type}")
        
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
        """Select best agent for task type"""
        # Agent specialization mapping
        task_agent_mapping = {
            "data_health_assessment": "seraphina",
            "data_purification": "aurora",
            "source_discovery": "alexander",
            "content_scraping": "alexander",
            "quality_assessment": "isabella",
            "bias_detection": "isabella",
            "knowledge_transfer": "marcus",
            "skill_development": "marcus",
            "system_augmentation": "victoria",
            "innovation_creation": "victoria",
            "low_quality_removal": "aurora",
            "quality_filtering": "aurora"
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
                "agent_name": agent.albrite_name
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
                "agent_name": agent.albrite_name
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
                    "specialization": agent.specialization
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
        
        logger.info(f"🤝 Coordinating family collaboration: {task_type}")
        
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
                    "agent_name": agent.albrite_name
                }
                
                # Update agent status
                self.agent_status[agent_id]["last_activity"] = datetime.now().isoformat()
                
            except Exception as e:
                collaboration_results[agent_id] = {
                    "success": False,
                    "error": str(e),
                    "agent_name": agent.albrite_name
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
        """Generate data for dashboard display"""
        dashboard_data = {
            "system_overview": {
                "total_agents": len(self.family_agents),
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
        """Run a demonstration of the system capabilities"""
        logger.info("🎭 Running Albrite Family System Demonstration")
        
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
            {"type": "system_augmentation", "target_system": "demo_system"}
        ]
        
        for task in demo_tasks:
            result = await self.coordinate_family_task(task)
            demonstration_results["demonstration_tasks"].append(result)
        
        # Demonstrate collaboration
        collab_task = {
            "type": "family_coordination",
            "agents": ["seraphina", "alexander", "isabella"],
            "goal": "coordinate_data_processing"
        }
        
        collab_result = await self.coordinate_family_collaboration(collab_task)
        demonstration_results["collaboration_demo"] = collab_result
        
        # Demonstrate toggle functionality
        toggle_demo = self.toggle_agent_override("seraphina", "enhanced_mode", False)
        demonstration_results["toggle_demo"] = toggle_demo
        
        # Reset toggle
        self.toggle_agent_override("seraphina", "enhanced_mode", True)
        
        logger.info("✅ System demonstration completed")
        
        return demonstration_results


# Global orchestrator instance
albrite_orchestrator = AlbriteFamilyOrchestrator()


# JavaScript toggle function for hover cards
def generate_toggle_javascript() -> str:
    """Generate JavaScript for toggle controls"""
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
            console.log(`Toggled ${overrideName} for ${data.agent_name}: ${value}`);
            // Update UI if needed
            updateAgentCard(agentId);
        } else {
            console.error('Toggle failed:', data.error);
        }
    })
    .catch(error => {
        console.error('Error toggling override:', error);
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
</script>
"""


# Flask API endpoints (for web interface)
def create_flask_app():
    """Create Flask app for web interface"""
    from flask import Flask, request, jsonify, render_template_string
    
    app = Flask(__name__)
    
    @app.route('/')
    def dashboard():
        """Main dashboard"""
        dashboard_data = albrite_orchestrator.generate_dashboard_data()
        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Albrite Family Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .agent-card { border: 1px solid #ddd; margin: 10px; padding: 15px; border-radius: 8px; background: white; }
        .agent-name { font-weight: bold; color: #2c3e50; }
        .agent-role { color: #7f8c8d; font-style: italic; }
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
    <h1>🏰 Albrite Family Dashboard</h1>
    
    <div class="system-overview">
        <h2>System Overview</h2>
        <p>Total Agents: {{ dashboard.agents|length }}</p>
        <p>Active Agents: {{ dashboard.system_overview.active_agents }}</p>
        <p>Collective Intelligence: {{ "%.2f"|format(dashboard.system_overview.system_metrics.collective_intelligence) }}</p>
    </div>
    
    <div class="agents">
        <h2>Family Agents</h2>
        {% for agent in dashboard.agents %}
        <div class="agent-card" id="agent-{{ agent.agent_id }}">
            <div class="agent-name">{{ agent.albrite_name }}</div>
            <div class="agent-role">{{ agent.family_role }} - {{ agent.specialization }}</div>
            
            <div class="metrics">
                {% for metric, value in agent.performance_metrics.items() %}
                <span class="metric">{{ metric }}: {{ "%.1f"|format(value*100) }}%</span>
                {% endfor %}
            </div>
            
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
        """, dashboard=dashboard_data, toggle_js=generate_toggle_javascript())
    
    @app.route('/api/toggle_override', methods=['POST'])
    def toggle_override():
        """Toggle agent override"""
        data = request.json
        result = albrite_orchestrator.toggle_agent_override(
            data['agent_id'],
            data['override_name'],
            data['value']
        )
        return jsonify(result)
    
    @app.route('/api/agent_hover_card/<agent_id>')
    def agent_hover_card(agent_id):
        """Get agent hover card HTML"""
        html = albrite_orchestrator.get_agent_hover_card(agent_id)
        return html or "<div>Agent not found</div>"
    
    @app.route('/api/family_status')
    def family_status():
        """Get family status"""
        return jsonify(albrite_orchestrator.get_family_status())
    
    @app.route('/api/coordinate_task', methods=['POST'])
    def coordinate_task():
        """Coordinate family task"""
        task = request.json
        result = asyncio.run(albrite_orchestrator.coordinate_family_task(task))
        return jsonify(result)
    
    return app


if __name__ == "__main__":
    # Run demonstration
    async def demo():
        results = await albrite_orchestrator.run_system_demonstration()
        print("🎉 Albrite Family System Demo Results:")
        print(json.dumps(results, indent=2, default=str))
    
    asyncio.run(demo())
