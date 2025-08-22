"""
Streaming service for real-time agent and tool execution.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.models.chat import ChatSession, ChatMessage
from app.models.integration import Integration
from app.services.crewai_service import crewai_service
from app.tools.registry import tool_registry
from app.tools.base import ToolExecutionEvent
from app.core.kafka_service import publish_agent_event
from app.db.database import get_db_session
from app.services.tool_tracking_service import tool_tracking_service

logger = logging.getLogger(__name__)


class StreamingEvent:
    """Streaming event types."""
    TOKEN = "token"
    AGENT_EVENT = "agent_event" 
    TOOL_CALL = "tool_call"
    THINKING = "thinking"
    FINAL = "final"
    ERROR = "error"


class WebSocketManager:
    """Manage WebSocket connections and streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
        
    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        """Connect a WebSocket client."""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        self.active_connections[connection_id] = websocket
        self.session_connections[session_id] = connection_id
        
        logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
        return connection_id
    
    def disconnect(self, connection_id: str, session_id: str = None):
        """Disconnect a WebSocket client."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id and session_id in self.session_connections:
            del self.session_connections[session_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send message to a specific session."""
        connection_id = self.session_connections.get(session_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to session {session_id}: {e}")
                self.disconnect(connection_id, session_id)
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to connection {connection_id}: {e}")
                self.disconnect(connection_id)


class StreamingCrewAIService:
    """Enhanced CrewAI service with real-time streaming capabilities."""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.crewai_service = crewai_service
        
    async def process_query_streaming(
        self, 
        query: str, 
        user_id: str, 
        session_id: str,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process query with real-time streaming."""
        
        try:
            # Start processing
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.THINKING,
                "content": "Analyzing your request...",
                "metadata": {"phase": "initialization"},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get user integrations
            user_integrations = db.query(Integration).filter(
                Integration.owner_id == user_id,
                Integration.is_active == True
            ).all()
            
            if not user_integrations:
                yield {
                    "type": StreamingEvent.ERROR,
                    "content": "No active integrations found. Please configure your integrations first.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Load tools for user integrations
            all_tools = []
            for integration in user_integrations:
                tools = await tool_registry.load_tools_for_integration(integration)
                all_tools.extend(tools)
            
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.AGENT_EVENT,
                "content": f"Loaded {len(all_tools)} tools from {len(user_integrations)} integrations",
                "metadata": {
                    "tools_count": len(all_tools),
                    "integrations_count": len(user_integrations)
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Route query to appropriate agents
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.THINKING,
                "content": "Determining which systems can help with your request...",
                "metadata": {"phase": "routing"},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            routing_result = await self._route_query_streaming(query, user_integrations, session_id)
            
            # Execute agent tasks with tool calls
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.AGENT_EVENT,
                "content": f"Executing tasks using {len(routing_result.get('agents', []))} specialized agents",
                "metadata": routing_result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            execution_results = {}
            for agent_id in routing_result.get("agents", []):
                async for result in self._execute_agent_task_streaming(
                    agent_id, query, session_id, db
                ):
                    yield result
                    if result.get("type") == StreamingEvent.FINAL:
                        execution_results[agent_id] = result.get("data", {})
            
            # Aggregate results
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.THINKING,
                "content": "Combining results from all systems...",
                "metadata": {"phase": "aggregation"},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            final_result = await self._aggregate_results_streaming(
                execution_results, query, session_id
            )
            
            # Send final result
            yield {
                "type": StreamingEvent.FINAL,
                "content": final_result.get("summary", "Task completed"),
                "data": final_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Streaming query processing failed: {e}")
            yield {
                "type": StreamingEvent.ERROR,
                "content": f"Processing failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _emit_stream_event(self, session_id: str, event: Dict[str, Any]):
        """Emit streaming event to WebSocket."""
        await self.websocket_manager.send_to_session(session_id, event)
        
        # Also publish to Kafka for logging
        await publish_agent_event("streaming_service", "stream_event", {
            "session_id": session_id,
            "event": event
        })
    
    async def _route_query_streaming(
        self, 
        query: str, 
        user_integrations: List[Integration],
        session_id: str
    ) -> Dict[str, Any]:
        """Route query with streaming updates."""
        
        # Simple routing based on keywords and available integrations
        routing_result = {
            "agents": [],
            "strategy": "sequential",
            "reasoning": "Keyword-based routing with available integrations"
        }
        
        query_lower = query.lower()
        integration_types = {integration.integration_type.lower() for integration in user_integrations}
        
        # Route based on available integrations and query content
        if "jira" in query_lower or any(word in query_lower for word in ["issue", "bug", "sprint", "project"]) and "jira" in integration_types:
            jira_integrations = [i for i in user_integrations if i.integration_type.lower() == "jira"]
            for integration in jira_integrations[:1]:  # Limit to first Jira integration
                routing_result["agents"].append(f"integration_{integration.id}")
        
        if "salesforce" in query_lower or any(word in query_lower for word in ["lead", "opportunity", "account", "crm"]) and "salesforce" in integration_types:
            sf_integrations = [i for i in user_integrations if i.integration_type.lower() == "salesforce"]
            for integration in sf_integrations[:1]:
                routing_result["agents"].append(f"integration_{integration.id}")
        
        if "zendesk" in query_lower or any(word in query_lower for word in ["ticket", "support", "customer"]) and "zendesk" in integration_types:
            zd_integrations = [i for i in user_integrations if i.integration_type.lower() == "zendesk"]
            for integration in zd_integrations[:1]:
                routing_result["agents"].append(f"integration_{integration.id}")
        
        if "github" in query_lower or any(word in query_lower for word in ["repository", "repo", "commit", "pull request"]) and "github" in integration_types:
            gh_integrations = [i for i in user_integrations if i.integration_type.lower() == "github"]
            for integration in gh_integrations[:1]:
                routing_result["agents"].append(f"integration_{integration.id}")
        
        if "slack" in query_lower or any(word in query_lower for word in ["message", "channel", "team"]) and "slack" in integration_types:
            slack_integrations = [i for i in user_integrations if i.integration_type.lower() == "slack"]
            for integration in slack_integrations[:1]:
                routing_result["agents"].append(f"integration_{integration.id}")
        
        if "hubspot" in query_lower or any(word in query_lower for word in ["contact", "deal", "marketing"]) and "hubspot" in integration_types:
            hs_integrations = [i for i in user_integrations if i.integration_type.lower() == "hubspot"]
            for integration in hs_integrations[:1]:
                routing_result["agents"].append(f"integration_{integration.id}")
        
        # If no specific routing, use first available integration
        if not routing_result["agents"] and user_integrations:
            routing_result["agents"].append(f"integration_{user_integrations[0].id}")
            routing_result["reasoning"] = f"Default routing to {user_integrations[0].name}"
        
        await self._emit_stream_event(session_id, {
            "type": StreamingEvent.AGENT_EVENT,
            "content": f"Routing to {len(routing_result['agents'])} agents: {routing_result['reasoning']}",
            "metadata": routing_result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return routing_result
    
    async def _execute_agent_task_streaming(
        self,
        agent_id: str,
        query: str,
        session_id: str,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute agent task with streaming tool execution."""
        
        try:
            # Get integration for this agent
            integration_id = agent_id.replace("integration_", "")
            integration = db.query(Integration).filter(Integration.id == int(integration_id)).first()
            
            if not integration:
                yield {
                    "type": StreamingEvent.ERROR,
                    "content": f"Integration not found for agent {agent_id}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.AGENT_EVENT,
                "content": f"Starting {integration.name} agent...",
                "metadata": {"agent_id": agent_id, "integration_type": integration.integration_type},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get tools for this integration
            tools = tool_registry.get_tools_for_integration(str(integration.id))
            
            if not tools:
                yield {
                    "type": StreamingEvent.ERROR,
                    "content": f"No tools available for {integration.name}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Determine which tool to use based on query
            selected_tool = await self._select_tool_for_query(query, tools, integration.integration_type)
            
            if not selected_tool:
                yield {
                    "type": StreamingEvent.AGENT_EVENT,
                    "content": f"No suitable tool found for query in {integration.name}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Extract tool parameters BEFORE using them
            tool_params = await self._extract_tool_parameters(query, selected_tool, integration.integration_type)
            
            # Execute tool with streaming
            await self._emit_stream_event(session_id, {
                "type": StreamingEvent.TOOL_CALL,
                "content": f"Executing {selected_tool.tool_name}...",
                "metadata": {
                    "tool_name": selected_tool.tool_name,
                    "integration": integration.name,
                    "status": "starting"
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Set up tool event streaming
            original_emit = selected_tool.emit_event
            
            async def streaming_emit_event(event: ToolExecutionEvent):
                await original_emit(event)
                await self._emit_stream_event(session_id, {
                    "type": StreamingEvent.TOOL_CALL,
                    "content": event.message,
                    "metadata": {
                        "tool_name": event.tool_name,
                        "event_type": event.type,
                        "data": event.data
                    },
                    "timestamp": event.timestamp.isoformat()
                })
            
            selected_tool.emit_event = streaming_emit_event
            
            # Start tracking tool execution
            execution_id = await tool_tracking_service.start_tool_execution(
                tool_name=selected_tool.tool_name,
                integration_id=integration.id,
                session_id=session_id,
                user_id=int(session_id.split("_")[1]),  # Extract user_id from session_id
                parameters=tool_params,
                db=db
            )
            
            # Execute tool
            result = await selected_tool.execute(**tool_params)
            
            # Complete tracking
            await tool_tracking_service.complete_tool_execution(execution_id, result, db)
            
            if result.success:
                yield {
                    "type": StreamingEvent.FINAL,
                    "content": f"{integration.name} task completed successfully",
                    "data": {
                        "agent_id": agent_id,
                        "integration": integration.name,
                        "tool_used": selected_tool.tool_name,
                        "result": result.data,
                        "execution_time": result.execution_time
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                yield {
                    "type": StreamingEvent.ERROR,
                    "content": f"{integration.name} task failed: {result.error}",
                    "metadata": {
                        "agent_id": agent_id,
                        "tool_used": selected_tool.tool_name,
                        "error": result.error
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Agent task execution failed for {agent_id}: {e}")
            yield {
                "type": StreamingEvent.ERROR,
                "content": f"Agent execution failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _select_tool_for_query(self, query: str, tools: List, integration_type: str):
        """Select appropriate tool based on query content."""
        query_lower = query.lower()
        
        # Priority order based on query keywords
        for tool in tools:
            tool_name = tool.tool_name.lower()
            
            # Search tools (high priority for general queries)
            if "search" in tool_name and any(word in query_lower for word in ["find", "search", "get", "show", "list"]):
                return tool
            
            # Create tools
            if "create" in tool_name and any(word in query_lower for word in ["create", "new", "add", "make"]):
                return tool
            
            # Update tools
            if "update" in tool_name and any(word in query_lower for word in ["update", "change", "modify", "edit"]):
                return tool
        
        # Fallback to first search tool or first available tool
        search_tools = [t for t in tools if "search" in t.tool_name.lower()]
        if search_tools:
            return search_tools[0]
        
        return tools[0] if tools else None
    
    async def _extract_tool_parameters(self, query: str, tool, integration_type: str) -> Dict[str, Any]:
        """Extract parameters for tool execution from query."""
        params = {}
        query_lower = query.lower()
        
        # Common parameter extraction
        if "search" in tool.tool_name.lower():
            # Extract search query
            if integration_type.lower() == "jira":
                if "issue" in query_lower or "bug" in query_lower:
                    params["query"] = query
                    params["max_results"] = 10
            elif integration_type.lower() == "github":
                if "repo" in query_lower or "repository" in query_lower:
                    params["query"] = query
                    params["search_type"] = "repositories"
                elif "issue" in query_lower:
                    params["query"] = query
                    params["search_type"] = "issues"
                else:
                    params["query"] = query
                    params["search_type"] = "repositories"
            else:
                params["query"] = query
        
        return params
    
    async def _aggregate_results_streaming(
        self,
        execution_results: Dict[str, Any],
        query: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        
        if not execution_results:
            return {
                "summary": "No results were obtained from the available integrations.",
                "agent_results": {},
                "total_agents": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if len(execution_results) == 1:
            # Single result
            result = list(execution_results.values())[0]
            return {
                "summary": f"Task completed using {result.get('integration', 'unknown integration')}. {result.get('tool_used', '')} executed successfully.",
                "agent_results": execution_results,
                "total_agents": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Multiple results - create summary
        integrations_used = []
        tools_used = []
        total_results = 0
        
        for agent_id, result in execution_results.items():
            if isinstance(result, dict):
                integrations_used.append(result.get("integration", "Unknown"))
                tools_used.append(result.get("tool_used", "Unknown"))
                if result.get("result") and isinstance(result["result"], dict):
                    # Count results from different tools
                    if "issues" in result["result"]:
                        total_results += len(result["result"]["issues"])
                    elif "contacts" in result["result"]:
                        total_results += len(result["result"]["contacts"])
                    elif "tickets" in result["result"]:
                        total_results += len(result["result"]["tickets"])
                    elif "repositories" in result["result"] or "items" in result["result"]:
                        items = result["result"].get("repositories") or result["result"].get("items", [])
                        total_results += len(items)
        
        summary = f"Successfully executed query across {len(execution_results)} systems: {', '.join(set(integrations_used))}. "
        if total_results > 0:
            summary += f"Retrieved {total_results} total results. "
        summary += f"Tools used: {', '.join(set(tools_used))}"
        
        return {
            "summary": summary,
            "agent_results": execution_results,
            "total_agents": len(execution_results),
            "integrations_used": list(set(integrations_used)),
            "tools_used": list(set(tools_used)),
            "total_results": total_results,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instances
websocket_manager = WebSocketManager()
streaming_service = StreamingCrewAIService(websocket_manager)