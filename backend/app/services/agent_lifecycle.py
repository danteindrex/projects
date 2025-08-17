import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid

from app.core.logging import log_agent_event
from app.core.kafka_service import publish_agent_event
from app.models.agent import Agent, AgentStatus, AgentType
from app.db.database import get_db_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class AgentLifecycleState(str, Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"
    RESTARTING = "restarting"

class AgentLifecycleManager:
    def __init__(self):
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_health: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, List[Dict[str, Any]]] = {}
    
    async def create_agent(self, agent_config: Dict[str, Any], db: Session) -> str:
        """Create a new agent instance"""
        try:
            agent_id = str(uuid.uuid4())
            
            # Create agent record in database
            db_agent = Agent(
                name=agent_config.get('name', f'Agent_{agent_id[:8]}'),
                description=agent_config.get('description', ''),
                agent_type=agent_config.get('type', AgentType.SPECIALIST),
                status=AgentStatus.INACTIVE,
                config=agent_config,
                capabilities=agent_config.get('capabilities', []),
                tools=agent_config.get('tools', []),
                tenant_id=agent_config.get('tenant_id', 'default')
            )
            
            db.add(db_agent)
            db.commit()
            db.refresh(db_agent)
            
            # Initialize agent lifecycle
            self.active_agents[agent_id] = {
                'id': agent_id,
                'db_id': db_agent.id,
                'state': AgentLifecycleState.CREATED,
                'config': agent_config,
                'created_at': datetime.utcnow(),
                'last_heartbeat': datetime.utcnow(),
                'task_count': 0,
                'error_count': 0
            }
            
            # Initialize health monitoring
            self.agent_health[agent_id] = {
                'status': 'healthy',
                'last_check': datetime.utcnow(),
                'response_time': 0.0,
                'memory_usage': 0.0,
                'cpu_usage': 0.0
            }
            
            # Initialize performance metrics
            self.performance_metrics[agent_id] = []
            
            log_agent_event(agent_id, "agent_created", config=agent_config)
            await publish_agent_event(agent_id, "agent_created", agent_config)
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    async def initialize_agent(self, agent_id: str) -> bool:
        """Initialize an agent for use"""
        try:
            if agent_id not in self.active_agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.active_agents[agent_id]
            agent['state'] = AgentLifecycleState.INITIALIZING
            
            # Simulate initialization process
            await asyncio.sleep(2)
            
            # Update agent state
            agent['state'] = AgentLifecycleState.ACTIVE
            agent['initialized_at'] = datetime.utcnow()
            
            # Update database
            await self._update_agent_status(agent_id, AgentStatus.ACTIVE)
            
            log_agent_event(agent_id, "agent_initialized")
            await publish_agent_event(agent_id, "agent_initialized", {})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {agent_id}: {e}")
            await self._handle_agent_error(agent_id, str(e))
            return False
    
    async def start_agent(self, agent_id: str) -> bool:
        """Start an agent"""
        try:
            if agent_id not in self.active_agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.active_agents[agent_id]
            
            if agent['state'] in [AgentLifecycleState.ACTIVE, AgentLifecycleState.IDLE]:
                return True
            
            # Initialize if not already done
            if agent['state'] == AgentLifecycleState.CREATED:
                return await self.initialize_agent(agent_id)
            
            # Restart if in error state
            if agent['state'] == AgentLifecycleState.ERROR:
                return await self.restart_agent(agent_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {e}")
            return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent"""
        try:
            if agent_id not in self.active_agents:
                return True
            
            agent = self.active_agents[agent_id]
            agent['state'] = AgentLifecycleState.STOPPING
            
            # Wait for current tasks to complete
            if agent['task_count'] > 0:
                await asyncio.sleep(1)
            
            agent['state'] = AgentLifecycleState.STOPPED
            agent['stopped_at'] = datetime.utcnow()
            
            # Update database
            await self._update_agent_status(agent_id, AgentStatus.INACTIVE)
            
            log_agent_event(agent_id, "agent_stopped")
            await publish_agent_event(agent_id, "agent_stopped", {})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent"""
        try:
            if agent_id not in self.active_agents:
                return False
            
            agent = self.active_agents[agent_id]
            agent['state'] = AgentLifecycleState.RESTARTING
            
            # Stop first
            await self.stop_agent(agent_id)
            
            # Start again
            success = await self.start_agent(agent_id)
            
            if success:
                log_agent_event(agent_id, "agent_restarted")
                await publish_agent_event(agent_id, "agent_restarted", {})
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to restart agent {agent_id}: {e}")
            return False
    
    async def assign_task(self, agent_id: str, task: Dict[str, Any]) -> bool:
        """Assign a task to an agent"""
        try:
            if agent_id not in self.active_agents:
                return False
            
            agent = self.active_agents[agent_id]
            
            if agent['state'] not in [AgentLifecycleState.ACTIVE, AgentLifecycleState.IDLE]:
                return False
            
            agent['state'] = AgentLifecycleState.BUSY
            agent['task_count'] += 1
            agent['current_task'] = task
            agent['task_started_at'] = datetime.utcnow()
            
            log_agent_event(agent_id, "task_assigned", task=task)
            await publish_agent_event(agent_id, "task_assigned", task)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign task to agent {agent_id}: {e}")
            return False
    
    async def complete_task(self, agent_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed"""
        try:
            if agent_id not in self.active_agents:
                return False
            
            agent = self.active_agents[agent_id]
            
            if agent['state'] != AgentLifecycleState.BUSY:
                return False
            
            # Record performance metrics
            task_duration = (datetime.utcnow() - agent['task_started_at']).total_seconds()
            self.performance_metrics[agent_id].append({
                'task_type': agent['current_task'].get('type'),
                'duration': task_duration,
                'timestamp': datetime.utcnow().isoformat(),
                'success': result.get('success', True)
            })
            
            # Update agent state
            agent['state'] = AgentLifecycleState.IDLE
            agent['task_count'] = max(0, agent['task_count'] - 1)
            agent['current_task'] = None
            agent['task_started_at'] = None
            
            # Update health metrics
            self.agent_health[agent_id]['response_time'] = task_duration
            
            log_agent_event(agent_id, "task_completed", result=result, duration=task_duration)
            await publish_agent_event(agent_id, "task_completed", {
                'result': result,
                'duration': task_duration
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete task for agent {agent_id}: {e}")
            return False
    
    async def _handle_agent_error(self, agent_id: str, error: str):
        """Handle agent errors"""
        try:
            if agent_id not in self.active_agents:
                return
            
            agent = self.active_agents[agent_id]
            agent['state'] = AgentLifecycleState.ERROR
            agent['error_count'] += 1
            agent['last_error'] = error
            agent['last_error_at'] = datetime.utcnow()
            
            # Update health status
            self.agent_health[agent_id]['status'] = 'unhealthy'
            self.agent_health[agent_id]['last_error'] = error
            
            log_agent_event(agent_id, "agent_error", error=error)
            await publish_agent_event(agent_id, "agent_error", {'error': error})
            
        except Exception as e:
            logger.error(f"Failed to handle error for agent {agent_id}: {e}")
    
    async def _update_agent_status(self, agent_id: str, status: AgentStatus):
        """Update agent status in database"""
        try:
            # This would update the database
            # For now, just log the update
            log_agent_event(agent_id, "status_updated", new_status=status.value)
            
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current agent status"""
        if agent_id not in self.active_agents:
            return None
        
        agent = self.active_agents[agent_id]
        health = self.agent_health.get(agent_id, {})
        
        return {
            'id': agent_id,
            'state': agent['state'],
            'status': health.get('status', 'unknown'),
            'task_count': agent['task_count'],
            'error_count': agent['error_count'],
            'last_heartbeat': agent['last_heartbeat'].isoformat(),
            'response_time': health.get('response_time', 0.0),
            'memory_usage': health.get('memory_usage', 0.0),
            'cpu_usage': health.get('cpu_usage', 0.0)
        }
    
    async def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        statuses = []
        for agent_id in self.active_agents:
            status = await self.get_agent_status(agent_id)
            if status:
                statuses.append(status)
        return statuses
    
    async def cleanup_inactive_agents(self):
        """Clean up inactive agents"""
        try:
            current_time = datetime.utcnow()
            agents_to_remove = []
            
            for agent_id, agent in self.active_agents.items():
                # Remove agents that have been stopped for more than 1 hour
                if (agent['state'] == AgentLifecycleState.STOPPED and 
                    'stopped_at' in agent and
                    current_time - agent['stopped_at'] > timedelta(hours=1)):
                    agents_to_remove.append(agent_id)
            
            for agent_id in agents_to_remove:
                del self.active_agents[agent_id]
                if agent_id in self.agent_health:
                    del self.agent_health[agent_id]
                if agent_id in self.performance_metrics:
                    del self.performance_metrics[agent_id]
                
                log_agent_event(agent_id, "agent_cleaned_up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup inactive agents: {e}")

# Global instance
agent_lifecycle_manager = AgentLifecycleManager()

# Convenience functions
async def create_agent(config: Dict[str, Any], db: Session) -> str:
    """Create a new agent"""
    return await agent_lifecycle_manager.create_agent(config, db)

async def start_agent(agent_id: str) -> bool:
    """Start an agent"""
    return await agent_lifecycle_manager.start_agent(agent_id)

async def stop_agent(agent_id: str) -> bool:
    """Stop an agent"""
    return await agent_lifecycle_manager.stop_agent(agent_id)

async def assign_task(agent_id: str, task: Dict[str, Any]) -> bool:
    """Assign a task to an agent"""
    return await agent_lifecycle_manager.assign_task(agent_id, task)

async def get_agent_status(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent status"""
    return await agent_lifecycle_manager.get_agent_status(agent_id)
