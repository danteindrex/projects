import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.core.config import settings
from app.core.logging import log_agent_event
from app.core.kafka_service import publish_agent_event
from app.models.agent import Agent, AgentType, AgentStatus
from app.models.integration import Integration
from app.db.database import get_db_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class CrewAIService:
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.router_agent: Optional[Any] = None
        self.integration_agents: Dict[str, Any] = {}
        
    async def initialize_agents(self, db: Session):
        """Initialize all agents in the system"""
        try:
            # Initialize router agent
            await self._create_router_agent()
            
            # Initialize integration agents
            await self._create_integration_agents(db)
            
            logger.info("CrewAI agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI agents: {e}")
            raise
    
    async def _create_router_agent(self):
        """Create the main router agent"""
        try:
            # In real implementation, this would use CrewAI
            # For now, create a mock router agent
            self.router_agent = {
                "id": "router_001",
                "name": "System Router",
                "type": "router",
                "status": "active",
                "capabilities": ["query_routing", "agent_orchestration", "response_aggregation"]
            }
            
            log_agent_event("router_001", "agent_created", agent_type="router")
            await publish_agent_event("router_001", "agent_created", {"agent_type": "router"})
            
        except Exception as e:
            logger.error(f"Failed to create router agent: {e}")
            raise
    
    async def _create_integration_agents(self, db: Session):
        """Create agents for each integration"""
        try:
            integrations = db.query(Integration).filter(Integration.status == "active").all()
            
            for integration in integrations:
                await self._create_integration_agent(integration)
                
        except Exception as e:
            logger.error(f"Failed to create integration agents: {e}")
            raise
    
    async def _create_integration_agent(self, integration: Integration):
        """Create an agent for a specific integration"""
        try:
            agent_id = f"integration_{integration.id}"
            
            # In real implementation, this would use CrewAI
            # For now, create a mock integration agent
            agent = {
                "id": agent_id,
                "name": f"{integration.name} Agent",
                "type": "integration",
                "status": "active",
                "integration_id": integration.id,
                "capabilities": [
                    "api_calls",
                    "data_retrieval",
                    "format_conversion",
                    "error_handling"
                ],
                "config": integration.config
            }
            
            self.integration_agents[agent_id] = agent
            
            log_agent_event(agent_id, "agent_created", integration_id=integration.id)
            await publish_agent_event(agent_id, "agent_created", {"integration_id": integration.id})
            
        except Exception as e:
            logger.error(f"Failed to create integration agent for {integration.name}: {e}")
            raise
    
    async def process_query(self, query: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Process a user query through the agent system"""
        try:
            # Start processing
            await publish_agent_event("router_001", "query_received", {
                "query": query,
                "user_id": user_id,
                "session_id": session_id
            })
            
            # Route query to appropriate agents
            routing_result = await self._route_query(query)
            
            # Execute agent tasks
            execution_result = await self._execute_agent_tasks(routing_result, query)
            
            # Aggregate results
            final_result = await self._aggregate_results(execution_result)
            
            # Log completion
            await publish_agent_event("router_001", "query_completed", {
                "query": query,
                "result": final_result
            })
            
            return final_result
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            await publish_agent_event("router_001", "query_failed", {"error": str(e)})
            raise
    
    async def _route_query(self, query: str) -> Dict[str, Any]:
        """Route the query to appropriate agents"""
        try:
            # Simple routing logic - in real implementation, this would use AI
            routing_result = {
                "query": query,
                "agents": [],
                "strategy": "sequential"
            }
            
            # Determine which integrations are relevant
            if "jira" in query.lower() or "issue" in query.lower():
                routing_result["agents"].append("integration_jira")
            
            if "zendesk" in query.lower() or "ticket" in query.lower():
                routing_result["agents"].append("integration_zendesk")
            
            if "salesforce" in query.lower() or "lead" in query.lower():
                routing_result["agents"].append("integration_salesforce")
            
            # If no specific integrations mentioned, use router agent
            if not routing_result["agents"]:
                routing_result["agents"].append("router_001")
            
            log_agent_event("router_001", "query_routed", routing_result=routing_result)
            return routing_result
            
        except Exception as e:
            logger.error(f"Failed to route query: {e}")
            raise
    
    async def _execute_agent_tasks(self, routing_result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Execute tasks using the routed agents"""
        try:
            execution_results = {}
            
            for agent_id in routing_result["agents"]:
                if agent_id in self.integration_agents:
                    # Execute integration agent task
                    result = await self._execute_integration_task(agent_id, query)
                    execution_results[agent_id] = result
                elif agent_id == "router_001":
                    # Execute router agent task
                    result = await self._execute_router_task(query)
                    execution_results[agent_id] = result
            
            return execution_results
            
        except Exception as e:
            logger.error(f"Failed to execute agent tasks: {e}")
            raise
    
    async def _execute_integration_task(self, agent_id: str, query: str) -> Dict[str, Any]:
        """Execute a task using an integration agent"""
        try:
            agent = self.integration_agents[agent_id]
            
            # Simulate API call to integration
            await asyncio.sleep(1)  # Simulate processing time
            
            result = {
                "agent_id": agent_id,
                "query": query,
                "result": f"Data retrieved from {agent['name']}",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            log_agent_event(agent_id, "task_executed", result=result)
            await publish_agent_event(agent_id, "task_executed", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute integration task for {agent_id}: {e}")
            raise
    
    async def _execute_router_task(self, query: str) -> Dict[str, Any]:
        """Execute a task using the router agent"""
        try:
            # Simulate router agent processing
            await asyncio.sleep(0.5)
            
            result = {
                "agent_id": "router_001",
                "query": query,
                "result": "Query processed and routed successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            log_agent_event("router_001", "task_executed", result=result)
            await publish_agent_event("router_001", "task_executed", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute router task: {e}")
            raise
    
    async def _aggregate_results(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all agents"""
        try:
            aggregated_result = {
                "summary": "Query processed successfully",
                "agent_results": execution_results,
                "timestamp": datetime.utcnow().isoformat(),
                "total_agents": len(execution_results)
            }
            
            return aggregated_result
            
        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            raise
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific agent"""
        if agent_id == "router_001":
            return self.router_agent
        elif agent_id in self.integration_agents:
            return self.integration_agents[agent_id]
        return None
    
    async def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "router_agent": self.router_agent,
            "integration_agents": self.integration_agents,
            "total_agents": len(self.integration_agents) + (1 if self.router_agent else 0)
        }

# Global CrewAI service instance
crewai_service = CrewAIService()

# Convenience functions
async def initialize_agents(db: Session):
    """Initialize all agents"""
    await crewai_service.initialize_agents(db)

async def process_query(query: str, user_id: str, session_id: str) -> Dict[str, Any]:
    """Process a user query"""
    return await crewai_service.process_query(query, user_id, session_id)

async def get_agent_status(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent status"""
    return await crewai_service.get_agent_status(agent_id)

async def get_all_agents_status() -> Dict[str, Any]:
    """Get all agents status"""
    return await crewai_service.get_all_agents_status()
