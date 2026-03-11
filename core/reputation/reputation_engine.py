"""
Reputation + Trust Scoring
Advanced reputation system for federated learning and collaborative networks
"""

import asyncio
import time
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

logger = logging.getLogger(__name__)


class ReputationEvent(Enum):
    """Types of reputation events"""
    CONTRIBUTION = "contribution"
    VALIDATION = "validation"
    MODERATION = "moderation"
    PEER_REVIEW = "peer_review"
    SUCCESSFUL_INTERACTION = "successful_interaction"
    FAILED_INTERACTION = "failed_interaction"
    QUALITY_REPORT = "quality_report"
    TIME_DECAY = "time_decay"


class ReputationMetric(Enum):
    """Types of reputation metrics"""
    TRUST_SCORE = "trust_score"
    RELIABILITY = "reliability"
    QUALITY = "quality"
    AVAILABILITY = "availability"
    RESPONSIVENESS = "responsiveness"
    CONSENSUS_PARTICIPATION = "consensus_participation"
    PEER_VOUCHING = "peer_vouching"


class TrustLevel(Enum):
    """Trust levels for agents"""
    UNTRUSTED = "untrusted"
    LOW_TRUST = "low_trust"
    MEDIUM_TRUST = "medium_trust"
    HIGH_TRUST = "high_trust"
    TRUSTED = "trusted"
    VERIFIED = "verified"


@dataclass
class ReputationEvent:
    """Individual reputation event"""
    def __init__(self, event_id: str, agent_id: str, event_type: ReputationEvent,
                 timestamp: float, value: float, weight: float = 1.0,
                 metadata: Dict[str, Any] = None, source_agent: str = None,
                 decay_rate: float = 0.95):
        self.event_id = event_id
        self.agent_id = agent_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.value = value
        self.weight = weight
        self.metadata = metadata or {}
        self.source_agent = source_agent
        self.decay_rate = decay_rate
        self.current_value = value
    
    def apply_decay(self, current_time: float):
        """Apply time decay to reputation value"""
        time_elapsed = current_time - self.timestamp
        decayed_value = self.value * (self.decay_rate ** (time_elapsed / 86400))  # Decay per day
        self.current_value = decayed_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class AgentReputation:
    """Reputation profile for an agent"""
    def __init__(self, agent_id: str, initial_score: float = 50.0):
        self.agent_id = agent_id
        self.trust_score = initial_score
        self.reliability = 50.0
        self.quality = 50.0
        self.availability = 50.0
        self.responsiveness = 50.0
        self.consensus_participation = 0.0
        self.peer_vouches = 0.0
        
        # Historical data
        self.events: List[ReputationEvent] = []
        self.interaction_partners: Set[str] = set()
        self.successful_interactions = 0
        self.failed_interactions = 0
        self.contribution_count = 0
        self.validation_count = 0
        self.moderation_count = 0
        
        # Computed metrics
        self.overall_score = initial_score
        self.trust_level = TrustLevel.MEDIUM_TRUST
        self.last_updated = time.time()
        
        # Decay parameters
        self.decay_half_life = 30 * 86400  # 30 days in seconds
        self.min_score = 0.0
        self.max_score = 100.0
        
        # Vouching system
        self.vouches_received: List[Tuple[str, float, float]] = []  # (vouching_agent, vouch_score, timestamp)
        self.vouches_given: List[Tuple[str, float, float]] = []  # (vouched_agent, vouch_score, timestamp)
    
    def add_event(self, event: ReputationEvent):
        """Add a reputation event"""
        self.events.append(event)
        self.last_updated = time.time()
        
        # Update specific metrics based on event type
        if event.event_type == ReputationEvent.CONTRIBUTION:
            self.contribution_count += 1
            self.quality = min(100, self.quality + event.value * event.weight)
            
        elif event.event_type == ReputationEvent.VALIDATION:
            self.validation_count += 1
            self.reliability = min(100, self.reliability + event.value * event.weight)
            
        elif event.event_type == ReputationEvent.MODERATION:
            self.moderation_count += 1
            if event.value < 0:
                self.trust_score = max(self.min_score, self.trust_score + event.value * event.weight)
            else:
                self.trust_score = min(100, self.trust_score + event.value * event.weight)
            
        elif event.event_type == ReputationEvent.SUCCESSFUL_INTERACTION:
            self.successful_interactions += 1
            self.availability = min(100, self.availability + event.value * event.weight)
            self.responsiveness = min(100, self.responsiveness + event.value * event.weight)
            
        elif event.event_type == ReputationEvent.FAILED_INTERACTION:
            self.failed_interactions += 1
            self.availability = max(self.min_score, self.availability - event.value * event.weight)
            self.responsiveness = max(self.min_score, self.responsiveness - event.value * event.weight)
            
        elif event.event_type == ReputationEvent.PEER_VOUCHING:
            self.peer_vouches += event.value * event.weight
        
        # Update interaction partners
        if event.source_agent:
            self.interaction_partners.add(event.source_agent)
        
        # Update vouches
        if event.event_type == ReputationEvent.PEER_VOUCHING:
            self.vouches_received.append((event.source_agent, event.value, event.timestamp))
        
        # Recompute overall score
        self._recompute_overall_score()
    
    def add_vouch(self, vouched_agent: str, vouch_score: float, weight: float = 1.0):
        """Add a vouch for another agent"""
        vouch_event = ReputationEvent(
            event_id=hashlib.sha256(f"{self.agent_id}_vouch_{vouched_agent}_{time.time()}".encode()).hexdigest()[:16],
            agent_id=self.agent_id,
            event_type=ReputationEvent.PEER_VOUCHING,
            timestamp=time.time(),
            value=vouch_score,
            weight=weight,
            metadata={"vouched_agent": vouched_agent}
        )
        
        self.vouches_given.append((vouched_agent, vouch_score, time.time()))
        self.add_event(vouch_event)
    
    def get_vouches_for_agent(self, agent_id: str, max_age_days: int = 30) -> List[Tuple[str, float]]:
        """Get vouches for a specific agent"""
        current_time = time.time()
        max_age_seconds = max_age_days * 86400
        
        valid_vouches = []
        for vouching_agent, vouch_score, timestamp in self.vouches_given:
            if vouching_agent == agent_id and (current_time - timestamp) < max_age_seconds:
                valid_vouches.append((vouching_agent, vouch_score))
        
        return valid_vouches
    
    def _recompute_overall_score(self):
        """Recompute overall reputation score"""
        current_time = time.time()
        
        # Apply time decay to all events
        for event in self.events:
            event.apply_decay(current_time)
        
        # Calculate weighted scores
        trust_score = 50.0
        reliability_score = 50.0
        quality_score = 50.0
        availability_score = 50.0
        responsiveness_score = 50.0
        
        # Recent events (last 30 days)
        recent_events = [
            event for event in self.events
            if (current_time - event.timestamp) < self.decay_half_life
        ]
        
        # Weight recent events more heavily
        for event in recent_events:
            weight = event.weight * 2.0  # Double weight for recent events
            
            if event.event_type == ReputationEvent.CONTRIBUTION:
                quality_score += event.current_value * weight
            elif event.event_type == ReputationEvent.VALIDATION:
                reliability_score += event.current_value * weight
            elif event.event_type == ReputationEvent.MODERATION:
                trust_score += event.current_value * weight
            elif event.event_type == ReputationEvent.SUCCESSFUL_INTERACTION:
                availability_score += event.current_value * weight
                responsiveness_score += event.current_value * weight
            elif event.event_type == ReputationEvent.FAILED_INTERACTION:
                availability_score += event.current_value * weight
                responsiveness_score += event.current_value * weight
        
        # Apply vouching bonus
        vouch_bonus = 0.0
        for vouching_agent, vouch_score, timestamp in self.vouches_given:
            if (current_time - timestamp) < self.decay_half_life:
                vouch_bonus += vouch_score * 0.1  # Small bonus for vouches
        
        trust_score += vouch_bonus
        
        # Update individual scores
        self.trust_score = max(self.min_score, min(self.max_score, trust_score))
        self.reliability = max(self.min_score, min(self.max_score, reliability_score))
        self.quality = max(self.min_score, min(self.max_score, quality_score))
        self.availability = max(self.min_score, min(self.max_score, availability_score))
        self.responsiveness = max(self.min_score, min(self.max_score, responsiveness_score))
        
        # Calculate consensus participation
        self.consensus_participation = len(recent_events) * 0.1
        
        # Calculate overall score (weighted average)
        weights = {
            "trust": 0.3,
            "reliability": 0.2,
            "quality": 0.2,
            "availability": 0.1,
            "responsiveness": 0.1,
            "consensus": 0.1
        }
        
        overall_score = (
            self.trust_score * weights["trust"] +
            self.reliability * weights["reliability"] +
            self.quality * weights["quality"] +
            self.availability * weights["availability"] +
            self.responsiveness * weights["responsiveness"] +
            self.consensus_participation * weights["consensus"]
        )
        
        self.overall_score = overall_score
        
        # Update trust level
        self._update_trust_level()
    
    def _update_trust_level(self):
        """Update trust level based on score"""
        if self.overall_score >= 90:
            self.trust_level = TrustLevel.VERIFIED
        elif self.overall_score >= 75:
            self.trust_level = TrustLevel.TRUSTED
        elif self.overall_score >= 60:
            self.trust_level = TrustLevel.HIGH_TRUST
        elif self.overall_score >= 40:
            self.trust_level = TrustLevel.MEDIUM_TRUST
        elif self.overall_score >= 20:
            self.trust_level = TrustLevel.LOW_TRUST
        else:
            self.trust_level = TrustLevel.UNTRUSTED
    
    def get_interaction_success_rate(self) -> float:
        """Get interaction success rate"""
        total_interactions = self.successful_interactions + self.failed_interactions
        if total_interactions == 0:
            return 0.0
        return self.successful_interactions / total_interactions
    
    def get_vouch_score(self) -> float:
        """Get average vouch score given"""
        if not self.vouches_given:
            return 0.0
        
        total_score = sum(vouch_score for _, vouch_score, _ in self.vouches_given)
        return total_score / len(self.vouches_given)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ReputationEngine:
    """Advanced reputation engine for federated networks"""
    
    def __init__(self, decay_enabled: bool = True, global_decay_rate: float = 0.95):
        self.decay_enabled = decay_enabled
        self.global_decay_rate = global_decay_rate
        
        # Agent reputations
        self.agents: Dict[str, AgentReputation] = {}
        
        # Global reputation events
        self.global_events: List[ReputationEvent] = []
        
        # Configuration
        self.config = {
            "min_trust_threshold": 20.0,
            "max_trust_threshold": 90.0,
            "vouch_weight": 2.0,
            "vouch_decay_days": 30,
            "event_decay_half_life": 30 * 86400,  # 30 days
            "min_interactions_for_trust": 5,
            "consensus_weight": 0.1,
            "moderation_impact": 5.0,
            "contribution_weight": 1.0,
            "validation_weight": 1.0
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self.event_callbacks: Dict[str, Callable] = {}
        
        # Performance metrics
        self.metrics = {
            "total_agents": 0,
            "total_events": 0,
            "average_trust_score": 0.0,
            "trust_distribution": {},
            "vouches_given": 0,
            "vouches_received": 0
        }
    
    def register_agent(self, agent_id: str, initial_score: float = 50.0) -> bool:
        """Register a new agent"""
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} already registered")
            return False
        
        self.agents[agent_id] = AgentReputation(agent_id, initial_score)
        self.metrics["total_agents"] += 1
        
        logger.info(f"Registered agent {agent_id} with initial score {initial_score}")
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not registered")
            return False
        
        del self.agents[agent_id]
        self.metrics["total_agents"] -= 1
        
        logger.info(f"Unregistered agent {agent_id}")
        return True
    
    def add_reputation_event(self, agent_id: str, event_type: ReputationEvent,
                        value: float, weight: float = 1.0,
                        metadata: Dict[str, Any] = None, source_agent: str = None) -> bool:
        """Add a reputation event for an agent"""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not registered")
            return False
        
        agent = self.agents[agent_id]
        
        # Create event
        event = ReputationEvent(
            event_id=hashlib.sha256(f"{agent_id}_{event_type.value}_{time.time()}".encode()).hexdigest()[:16],
            agent_id=agent_id,
            event_type=event_type,
            timestamp=time.time(),
            value=value,
            weight=weight,
            metadata=metadata or {},
            source_agent=source_agent,
            decay_rate=self.global_decay_rate if self.decay_enabled else 1.0
        )
        
        agent.add_event(event)
        self.global_events.append(event)
        self.metrics["total_events"] += 1
        
        logger.debug(f"Added reputation event {event.event_id.value} for agent {agent_id}")
        return True
    
    def add_vouch(self, vouching_agent: str, vouched_agent: str, vouch_score: float,
                 weight: float = 1.0) -> bool:
        """Add a vouch from one agent to another"""
        if vouching_agent not in self.agents:
            logger.warning(f"Vouching agent {vouching_agent} not registered")
            return False
        
        if vouched_agent not in self.agents:
            logger.warning(f"Vouched agent {vouched_agent} not registered")
            return False
        
        vouching_agent_rep = self.agents[vouching_agent]
        vouching_agent_rep.add_vouch(vouched_agent, vouch_score, weight)
        
        self.metrics["vouches_given"] += 1
        
        logger.info(f"Added vouch from {vouching_agent} to {vouched_agent}: {vouch_score}")
        return True
    
    def get_agent_reputation(self, agent_id: str) -> Optional[AgentReputation]:
        """Get reputation for an agent"""
        return self.agents.get(agent_id)
    
    def get_trust_level(self, agent_id: str) -> Optional[TrustLevel]:
        """Get trust level for an agent"""
        agent = self.agents.get(agent_id)
        return agent.trust_level if agent else None
    
    def get_top_agents(self, metric: ReputationMetric = ReputationMetric.TRUST_SCORE,
                    limit: int = 10) -> List[Tuple[str, float]]:
        """Get top agents by reputation metric"""
        if not self.agents:
            return []
        
        agent_scores = []
        
        for agent_id, agent in self.agents.items():
            if metric == ReputationMetric.TRUST_SCORE:
                score = agent.overall_score
            elif metric == ReputationMetric.RELIABILITY:
                score = agent.reliability
            elif metric == ReputationMetric.QUALITY:
                score = agent.quality
            elif metric == ReputationMetric.AVAILABILITY:
                score = agent.availability
            elif metric == ReputationMetric.RESPONSIVENESS:
                score = agent.responsiveness
            elif metric == ReputationMetric.CONSENSUS_PARTICIPATION:
                score = agent.consensus_participation
            else:
                continue
            
            agent_scores.append((agent_id, score))
        
        # Sort by score (descending)
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        return agent_scores[:limit]
    
    def get_reputation_stats(self) -> Dict[str, Any]:
        """Get reputation system statistics"""
        if not self.agents:
            return {"total_agents": 0}
        
        # Calculate statistics
        trust_scores = [agent.overall_score for agent in self.agents.values()]
        trust_levels = {}
        
        for level in TrustLevel:
            trust_levels[level.value] = len([
                agent for agent in self.agents.values()
                if agent.trust_level == level
            ])
        
        # Calculate averages
        avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
        avg_reliability = sum(agent.reliability for agent in self.agents.values()) / len(self.agents)
        avg_quality = sum(agent.quality for agent in self.agents.values()) / len(self.agents)
        avg_availability = sum(agent.availability for agent in self.agents.values()) / len(self.agents)
        avg_responsiveness = sum(agent.responsiveness for agent in self.agents.values()) / len(self.agents)
        
        # Update metrics
        self.metrics["average_trust_score"] = avg_trust
        self.metrics["trust_distribution"] = {level.value: count for level, count in trust_levels.items()}
        
        return {
            "total_agents": len(self.agents),
            "total_events": len(self.global_events),
            "average_trust_score": avg_trust,
            "average_reliability": avg_reliability,
            "average_quality": avg_quality,
            "average_availability": avg_availability,
            "average_responsiveness": avg_responsiveness,
            "trust_distribution": trust_levels,
            "config": self.config,
            "metrics": self.metrics
        }
    
    async def start(self) -> bool:
        """Start reputation engine"""
        try:
            self.is_running = True
            
            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._decay_loop()),
                asyncio.create_task(self._cleanup_loop()),
                asyncio.create_task(self._statistics_loop())
            ]
            
            logger.info("Reputation engine started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start reputation engine: {e}")
            return False
    
    async def stop(self):
        """Stop reputation engine"""
        self.is_running = False
        
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        self.background_tasks.clear()
        logger.info("Reputation engine stopped")
    
    async def _decay_loop(self):
        """Background loop for time decay"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Apply decay every hour
                
                if self.decay_enabled:
                    current_time = time.time()
                    
                    # Apply decay to all agents
                    for agent in self.agents.values():
                        agent._recompute_overall_score()
                    
                    # Clean up old events
                    for agent in self.agents.values():
                        agent.events = [
                            event for event in agent.events
                            if (current_time - event.timestamp) < self.config["event_decay_half_life"] * 2
                        ]
                
                logger.debug("Applied time decay to all agent reputations")
                
            except Exception as e:
                logger.error(f"Decay loop error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Background loop for cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # Clean up every 24 hours
                
                current_time = time.time()
                max_age = self.config["event_decay_half_life"] * 4  # 120 days
                
                # Clean up old events
                for agent in self.agents.values():
                    agent.events = [
                        event for event in agent.events
                        if (current_time - event.timestamp) < max_age
                    ]
                
                logger.debug("Cleaned up old reputation events")
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    async def _statistics_loop(self):
        """Background loop for statistics"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                # Update global metrics
                self.get_reputation_stats()
                
            except Exception as e:
                logger.error(f"Statistics loop error: {e}")
                await asyncio.sleep(60)
    
    def export_reputation_data(self) -> Dict[str, Any]:
        """Export reputation data for backup"""
        return {
            "agents": {
                agent_id: agent.to_dict()
                for agent_id, agent in self.agents.items()
            },
            "global_events": [
                event.to_dict()
                for event in self.global_events
            ],
            "config": self.config,
            "metrics": self.metrics,
            "export_timestamp": time.time()
        }
    
    def import_reputation_data(self, data: Dict[str, Any]) -> bool:
        """Import reputation data from backup"""
        try:
            # Import agents
            for agent_id, agent_data in data.get("agents", {}).items():
                agent = AgentReputation(agent_id, agent_data.get("overall_score", 50.0))
                
                # Import events
                for event_data in agent_data.get("events", []):
                    event = ReputationEvent(
                        event_id=event_data["event_id"],
                        agent_id=agent_id,
                        event_type=ReputationEvent(event_data["event_type"]),
                        timestamp=event_data["timestamp"],
                        value=event_data["value"],
                        weight=event_data.get("weight", 1.0),
                        metadata=event_data.get("metadata", {}),
                        source_agent=event_data.get("source_agent")
                    )
                    agent.events.append(event)
                
                self.agents[agent_id] = agent
            
            # Import global events
            for event_data in data.get("global_events", []):
                event = ReputationEvent(
                    event_id=event_data["event_id"],
                    agent_id=event_data["agent_id"],
                    event_type=ReputationEvent(event_data["event_type"]),
                    timestamp=event_data["timestamp"],
                    value=event_data["value"],
                    weight=event_data.get("weight", 1.0),
                    metadata=event_data.get("metadata", {}),
                    source_agent=event_data.get("source_agent")
                )
                self.global_events.append(event)
            
            # Import config and metrics
            self.config.update(data.get("config", {}))
            self.metrics.update(data.get("metrics", {}))
            
            logger.info(f"Imported reputation data for {len(self.agents)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import reputation data: {e}")
            return False
    
    def register_event_callback(self, event_type: ReputationEvent, callback: Callable):
        """Register callback for reputation events"""
        event_key = f"{event_type.value}_callback"
        self.event_callbacks[event_key] = callback
        logger.info(f"Registered callback for {event_type.value}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get reputation engine status"""
        return {
            "is_running": self.is_running,
            "total_agents": len(self.agents),
            "total_events": len(self.global_events),
            "config": self.config,
            "metrics": self.metrics
        }
