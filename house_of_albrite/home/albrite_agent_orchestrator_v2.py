"""
Albrite Agent Orchestrator v2 - Enhanced with Memory, Caching, and Centralized AI
Comprehensive orchestration system for all Albrite agents including military branch
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Import enhanced agents
from .agents.seraphina_data_guardian_v2 import SeraphinaDataGuardianV2
from .agents.general_albrite_military_v2 import GeneralAlbriteMilitaryV2
from .common.albrite_base_agent_v2 import AlbriteBaseAgentV2, MemoryType
from .albrite_centralized_ai_manager import albrite_ai_manager, ModelPriority

logger = logging.getLogger(__name__)


class AlbriteAgentOrchestratorV2:
    """Enhanced orchestrator for all Albrite agents with advanced capabilities"""
    
    def __init__(self):
        self.family_agents = {}
        self.military_agents = {}
        self.agent_status = {}
        self.system_metrics = {}
        self.orchestration_history = []
        
        # Initialize the complete agent ecosystem
        self._initialize_all_agents()
        self._setup_agent_relationships()
        self._initialize_system_metrics()
        
        logger.info("🏰 Albrite Enhanced Agent Orchestrator v2 initialized")
    
    def _initialize_all_agents(self):
        """Initialize all family and military agents"""
        # Core family agents
        self.family_agents = {
            "seraphina": SeraphinaDataGuardianV2("seraphina", "Seraphina Albrite"),
            # Add more family agents as they're created
        }
        
        # Military agents
        self.military_agents = {
            "general": GeneralAlbriteMilitaryV2("general", "General Albrite"),
            # Add more military agents as they're created
        }
        
        # Combine all agents
        self.all_agents = {**self.family_agents, **self.military_agents}
        
        # Initialize agent status
        for agent_id, agent in self.all_agents.items():
            self.agent_status[agent_id] = {
                "name": agent.albrite_name,
                "specialization": agent.specialization,
                "status": "active",
                "last_activity": datetime.now().isoformat(),
                "tasks_completed": 0,
                "success_rate": 0.85,
                "memory_usage": agent.get_memory_summary(),
                "performance_metrics": agent.get_performance_metrics()
            }
    
    def _setup_agent_relationships(self):
        """Setup relationships between agents"""
        # Family agent relationships
        family_relationships = {
            "seraphina": ["alexander", "aurora", "isabella", "charlotte", "daniel"],
            # Add more relationships as agents are created
        }
        
        # Military agent relationships
        military_relationships = {
            "general": ["rex", "nova", "stratus", "cognita", "agentis"],
            # Add more relationships as agents are created
        }
        
        # Apply relationships
        all_relationships = {**family_relationships, **military_relationships}
        for agent_id, related_agents in all_relationships.items():
            if agent_id in self.all_agents:
                self.all_agents[agent_id].related_agents.update(related_agents)
    
    def _initialize_system_metrics(self):
        """Initialize system-wide metrics"""
        self.system_metrics = {
            "total_agents": len(self.all_agents),
            "active_agents": len(self.all_agents),
            "total_tasks_completed": 0,
            "system_success_rate": 0.0,
            "average_response_time": 0.0,
            "total_memory_usage": 0,
            "cache_hit_rate": 0.0,
            "ai_model_usage": {},
            "orchestrator_uptime": datetime.now().isoformat()
        }
    
    async def execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task on specific agent with enhanced monitoring"""
        if agent_id not in self.all_agents:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found",
                "timestamp": datetime.now().isoformat()
            }
        
        agent = self.all_agents[agent_id]
        start_time = datetime.now()
        
        try:
            # Update agent status
            self.agent_status[agent_id]["status"] = "executing"
            self.agent_status[agent_id]["last_activity"] = start_time.isoformat()
            
            # Execute task
            result = await agent.execute_task(task)
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_system_metrics(agent_id, result, execution_time)
            
            # Add to orchestration history
            self.orchestration_history.append({
                "agent_id": agent_id,
                "task": task,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed for {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": agent_id,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            # Reset agent status
            self.agent_status[agent_id]["status"] = "active"
    
    async def coordinate_multi_agent_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate task across multiple agents"""
        coordination_id = f"coord_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target_agents = task.get("target_agents", [])
        
        if not target_agents:
            return {
                "success": False,
                "error": "No target agents specified",
                "timestamp": datetime.now().isoformat()
            }
        
        # Execute tasks concurrently
        agent_tasks = []
        for agent_id in target_agents:
            if agent_id in self.all_agents:
                agent_task = {
                    **task,
                    "coordination_id": coordination_id,
                    "agent_role": task.get("agent_roles", {}).get(agent_id, "participant")
                }
                agent_tasks.append(self.execute_agent_task(agent_id, agent_task))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            agent_id = target_agents[i]
            if isinstance(result, Exception):
                failed_results.append({"agent": agent_id, "error": str(result)})
            elif result.get("success", False):
                successful_results.append({"agent": agent_id, "result": result})
            else:
                failed_results.append({"agent": agent_id, "error": result.get("error", "Unknown error")})
        
        coordination_result = {
            "coordination_id": coordination_id,
            "target_agents": target_agents,
            "successful_results": successful_results,
            "failed_results": failed_results,
            "success_rate": len(successful_results) / len(target_agents),
            "coordinated_by": "orchestrator",
            "timestamp": datetime.now().isoformat()
        }
        
        return coordination_result
    
    async def orchestrate_family_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate comprehensive family operation"""
        operation_type = operation.get("type", "general")
        
        if operation_type == "family_coordination":
            return await self.coordinate_family_agents(operation)
        elif operation_type == "military_coordination":
            return await self.coordinate_military_agents(operation)
        elif operation_type == "cross_domain_coordination":
            return await self.coordinate_cross_domain(operation)
        elif operation_type == "system_wide_task":
            return await self.execute_system_wide_task(operation)
        else:
            return await self.execute_general_operation(operation)
    
    async def coordinate_family_agents(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate family agents for specific operation"""
        family_agents = list(self.family_agents.keys())
        operation_goal = operation.get("goal", "collaboration")
        
        # Create family-specific tasks
        family_tasks = []
        for agent_id in family_agents:
            agent = self.family_agents[agent_id]
            
            # Create task based on agent specialization
            if agent.specialization == "data_guardian":
                task = {
                    "type": "health_assessment",
                    "dataset_id": operation.get("dataset_id", "family_dataset"),
                    "data_sample": operation.get("data_sample", [])
                }
            else:
                task = {
                    "type": "collaboration",
                    "operation_goal": operation_goal,
                    "family_coordination": True
                }
            
            family_tasks.append(self.execute_agent_task(agent_id, task))
        
        # Execute family tasks
        family_results = await asyncio.gather(*family_tasks, return_exceptions=True)
        
        # Synthesize results
        synthesis_result = await albrite_ai_manager.execute_model_request(
            "analysis", "family_synthesizer",
            {
                "family_results": family_results,
                "operation_goal": operation_goal,
                "synthesis_approach": "family_coordination"
            },
            "orchestrator",
            ModelPriority.HIGH
        )
        
        return {
            "operation_id": f"family_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "operation_type": "family_coordination",
            "family_agents": family_agents,
            "family_results": family_results,
            "synthesis_result": synthesis_result,
            "orchestrated_by": "family_orchestrator",
            "timestamp": datetime.now().isoformat()
        }
    
    async def coordinate_military_agents(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate military agents for defense operations"""
        military_agents = list(self.military_agents.keys())
        operation_type = operation.get("military_type", "defense")
        
        # Create military-specific tasks
        military_tasks = []
        for agent_id in military_agents:
            agent = self.military_agents[agent_id]
            
            if agent.specialization == "supreme_military_command":
                task = {
                    "type": "military_coordination",
                    "subtype": "supreme_defense",
                    "coordination_directive": operation,
                    "military_operation": True
                }
            else:
                task = {
                    "type": "military_task",
                    "operation_type": operation_type,
                    "military_coordination": True
                }
            
            military_tasks.append(self.execute_agent_task(agent_id, task))
        
        # Execute military tasks
        military_results = await asyncio.gather(*military_tasks, return_exceptions=True)
        
        # Synthesize military results
        synthesis_result = await albrite_ai_manager.execute_model_request(
            "analysis", "military_synthesizer",
            {
                "military_results": military_results,
                "operation_type": operation_type,
                "synthesis_approach": "military_coordination"
            },
            "orchestrator",
            ModelPriority.HIGH
        )
        
        return {
            "operation_id": f"military_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "operation_type": "military_coordination",
            "military_agents": military_agents,
            "military_results": military_results,
            "synthesis_result": synthesis_result,
            "orchestrated_by": "military_orchestrator",
            "timestamp": datetime.now().isoformat()
        }
    
    async def coordinate_cross_domain(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate cross-domain operations between family and military"""
        cross_domain_teams = operation.get("teams", [])
        
        # Create cross-domain coordination
        coordination_tasks = []
        for team in cross_domain_teams:
            team_agents = team.get("agents", [])
            team_task = {
                **operation,
                "team_id": team.get("id"),
                "team_role": team.get("role"),
                "cross_domain": True
            }
            
            coordination_tasks.append(
                self.coordinate_multi_agent_task({
                    **team_task,
                    "target_agents": team_agents
                })
            )
        
        # Execute cross-domain coordination
        team_results = await asyncio.gather(*coordination_tasks, return_exceptions=True)
        
        # Synthesize cross-domain results
        synthesis_result = await albrite_ai_manager.execute_model_request(
            "analysis", "cross_domain_synthesizer",
            {
                "team_results": team_results,
                "cross_domain_operation": operation,
                "synthesis_approach": "cross_domain_coordination"
            },
            "orchestrator",
            ModelPriority.CRITICAL
        )
        
        return {
            "operation_id": f"cross_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "operation_type": "cross_domain_coordination",
            "cross_domain_teams": cross_domain_teams,
            "team_results": team_results,
            "synthesis_result": synthesis_result,
            "orchestrated_by": "cross_domain_orchestrator",
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_system_wide_task(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system-wide task across all agents"""
        system_task = operation.get("system_task", "health_check")
        
        # Create system-wide tasks
        system_tasks = []
        for agent_id, agent in self.all_agents.items():
            task = {
                "type": "system_task",
                "system_task": system_task,
                "system_wide": True,
                "execution_context": operation
            }
            system_tasks.append(self.execute_agent_task(agent_id, task))
        
        # Execute system tasks
        system_results = await asyncio.gather(*system_tasks, return_exceptions=True)
        
        # Synthesize system results
        synthesis_result = await albrite_ai_manager.execute_model_request(
            "analysis", "system_synthesizer",
            {
                "system_results": system_results,
                "system_task": system_task,
                "synthesis_approach": "system_wide_coordination"
            },
            "orchestrator",
            ModelPriority.HIGH
        )
        
        return {
            "operation_id": f"system_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "operation_type": "system_wide_task",
            "system_task": system_task,
            "all_agents": list(self.all_agents.keys()),
            "system_results": system_results,
            "synthesis_result": synthesis_result,
            "orchestrated_by": "system_orchestrator",
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_general_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general operation"""
        # Use AI to determine best approach
        approach_analysis = await albrite_ai_manager.execute_model_request(
            "analysis", "operation_analyzer",
            {
                "operation": operation,
                "available_agents": list(self.all_agents.keys()),
                "analysis_approach": "strategic"
            },
            "orchestrator",
            ModelPriority.MEDIUM
        )
        
        # Execute based on analysis
        recommended_approach = approach_analysis.get("recommended_approach", "single_agent")
        
        if recommended_approach == "single_agent":
            agent_id = approach_analysis.get("recommended_agent", list(self.all_agents.keys())[0])
            return await self.execute_agent_task(agent_id, operation)
        elif recommended_approach == "multi_agent":
            return await self.coordinate_multi_agent_task(operation)
        else:
            return await self.orchestrate_family_operation(operation)
    
    def _update_system_metrics(self, agent_id: str, result: Dict[str, Any], execution_time: float):
        """Update system-wide metrics"""
        if result.get("success", False):
            self.system_metrics["total_tasks_completed"] += 1
            
            # Update agent-specific metrics
            if agent_id in self.agent_status:
                self.agent_status[agent_id]["tasks_completed"] += 1
                self.agent_status[agent_id]["success_rate"] = (
                    (self.agent_status[agent_id]["success_rate"] * 0.9) + 
                    (1.0 if result.get("success") else 0.0) * 0.1
                )
        
        # Update system-wide metrics
        total_tasks = sum(status["tasks_completed"] for status in self.agent_status.values())
        if total_tasks > 0:
            self.system_metrics["total_tasks_completed"] = total_tasks
            self.system_metrics["system_success_rate"] = (
                sum(status["success_rate"] for status in self.agent_status.values()) / len(self.agent_status)
            )
        
        # Update AI model usage from centralized manager
        ai_metrics = albrite_ai_manager.get_system_metrics()
        self.system_metrics["ai_model_usage"] = ai_metrics
        self.system_metrics["cache_hit_rate"] = ai_metrics.get("cache_metrics", {}).get("cache_hit_rate", 0.0)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "system_metrics": self.system_metrics,
            "agent_status": self.agent_status,
            "family_agents": len(self.family_agents),
            "military_agents": len(self.military_agents),
            "total_agents": len(self.all_agents),
            "active_agents": sum(1 for status in self.agent_status.values() if status["status"] == "active"),
            "orchestration_history_count": len(self.orchestration_history),
            "top_ai_models": albrite_ai_manager.get_top_models(5),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific agent"""
        if agent_id not in self.all_agents:
            return {"error": f"Agent {agent_id} not found"}
        
        agent = self.all_agents[agent_id]
        status = self.agent_status.get(agent_id, {})
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.albrite_name,
            "specialization": agent.specialization,
            "core_skills": agent.get_core_skills(),
            "unique_abilities": agent.get_unique_abilities(),
            "genetic_traits": agent.genetic_traits,
            "related_agents": list(agent.related_agents),
            "toggle_settings": agent.toggle_settings,
            "status": status,
            "memory_summary": agent.get_memory_summary(),
            "performance_metrics": agent.get_performance_metrics(),
            "bio": agent.get_bio(),
            "collaboration_style": agent.get_collaboration_style()
        }
    
    async def run_system_demonstration(self) -> Dict[str, Any]:
        """Run comprehensive system demonstration"""
        logger.info("🎭 Running Albrite Enhanced System Demonstration")
        
        demonstration_results = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "demonstration_tasks": []
        }
        
        # Demonstrate individual agent capabilities
        demo_tasks = [
            {
                "agent_id": "seraphina",
                "task": {"type": "health_assessment", "dataset_id": "demo_dataset", "data_sample": [{"id": 1}, {"id": 2}]}
            },
            {
                "agent_id": "general",
                "task": {"type": "military_coordination", "subtype": "supreme_defense", "threat_assessment": {"level": "medium"}}
            }
        ]
        
        for demo in demo_tasks:
            result = await self.execute_agent_task(demo["agent_id"], demo["task"])
            demonstration_results["demonstration_tasks"].append(result)
        
        # Demonstrate multi-agent coordination
        multi_agent_task = {
            "target_agents": ["seraphina", "general"],
            "type": "collaboration",
            "coordination_goal": "demonstrate_cross_domain_coordination"
        }
        
        multi_result = await self.coordinate_multi_agent_task(multi_agent_task)
        demonstration_results["multi_agent_demo"] = multi_result
        
        # Demonstrate family operation
        family_op = {
            "type": "family_coordination",
            "goal": "demonstrate_family_collaboration",
            "dataset_id": "family_demo_data"
        }
        
        family_result = await self.orchestrate_family_operation(family_op)
        demonstration_results["family_demo"] = family_result
        
        # Demonstrate military operation
        military_op = {
            "type": "military_coordination",
            "military_type": "defense",
            "threat_level": "low"
        }
        
        military_result = await self.orchestrate_military_agents(military_op)
        demonstration_results["military_demo"] = military_result
        
        logger.info("✅ Enhanced system demonstration completed")
        
        return demonstration_results


# Global orchestrator instance
albrite_orchestrator_v2 = AlbriteAgentOrchestratorV2()
