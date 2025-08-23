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
        """Process query with CrewAI agents."""
        
        try:
            # Debug: First yield to test streaming
            yield {
                "type": "debug",
                "content": "Streaming service called successfully!",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Initialize CrewAI crew
            yield {
                "type": StreamingEvent.THINKING,
                "content": "Initializing AI agents...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processing query for user {user_id}: {query[:50]}...")
            
            # LOAD ACTUAL TOOLS FROM USER'S INTEGRATIONS
            from app.models.integration import Integration, IntegrationStatus
            from app.tools.registry import tool_registry
            
            user_integrations = db.query(Integration).filter(
                Integration.owner_id == user_id,
                Integration.status == IntegrationStatus.ACTIVE
            ).all()
            
            # Load tools for each integration WITH CREDENTIALS
            available_tools = []
            for integration in user_integrations:
                tools = await tool_registry.load_tools_for_integration(integration)
                available_tools.extend(tools)
            
            logger.info(f"Loaded {len(available_tools)} tools for user {user_id}")
            
            # Debug: Check what tools and credentials were loaded
            for tool in available_tools:
                logger.info(f"Tool: {tool.tool_name}")
                logger.info(f"Has credentials: {hasattr(tool, 'credentials')}")
                if hasattr(tool, 'credentials'):
                    logger.info(f"Credential keys: {list(tool.credentials.credentials.keys())}")
                    logger.info(f"Has access_token: {'access_token' in tool.credentials.credentials}")
            
            # Create and run CrewAI crew with ACTUAL TOOLS
            result = await self.crewai_service.process_user_query(
                query=query,
                user_id=user_id,
                tools=available_tools,  # ← NOW HAS TOOLS WITH CREDENTIALS
                callback=self._stream_callback(session_id)
            )
            
            # Send final result
            yield {
                "type": StreamingEvent.FINAL,
                "content": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Streaming query processing failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            yield {
                "type": StreamingEvent.ERROR,
                "content": f"Processing failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _stream_callback(self, session_id: str):
        """Create callback for streaming updates"""
        loop = asyncio.get_running_loop()
        def callback(agent_output):
            # This would stream intermediate results
            event = {"type": "agent_step", "data": str(agent_output)}
            asyncio.run_coroutine_threadsafe(self._emit_stream_event(session_id, event), loop)
        return callback
    
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
        
# Routing completed - event will be emitted by main generator
        
        return routing_result
    
    async def _analyze_query_intent(self, query: str, session_id: str) -> Dict[str, Any]:
        """Analyze query intent and complexity for better routing and processing."""
        try:
            query_lower = query.lower()
            
            # Determine query complexity
            complexity = "simple"
            if len(query.split()) > 20:
                complexity = "complex"
            elif len(query.split()) > 10:
                complexity = "medium"
            
            # Analyze intent based on keywords and patterns
            intent_categories = []
            
            # CRUD operations detection
            if any(word in query_lower for word in ["create", "add", "new", "make"]):
                intent_categories.append("create")
            if any(word in query_lower for word in ["update", "change", "modify", "edit"]):
                intent_categories.append("update")
            if any(word in query_lower for word in ["delete", "remove", "cancel"]):
                intent_categories.append("delete")
            if any(word in query_lower for word in ["search", "find", "get", "show", "list", "fetch"]):
                intent_categories.append("read")
            
            # System/Integration specific detection
            systems_mentioned = []
            if "jira" in query_lower or any(word in query_lower for word in ["issue", "sprint", "project", "bug"]):
                systems_mentioned.append("jira")
            if "salesforce" in query_lower or any(word in query_lower for word in ["lead", "opportunity", "account", "crm"]):
                systems_mentioned.append("salesforce")
            if "zendesk" in query_lower or any(word in query_lower for word in ["ticket", "support", "customer"]):
                systems_mentioned.append("zendesk")
            if "slack" in query_lower or any(word in query_lower for word in ["message", "channel", "team"]):
                systems_mentioned.append("slack")
            if "github" in query_lower or any(word in query_lower for word in ["repository", "repo", "commit", "pull request"]):
                systems_mentioned.append("github")
            if "hubspot" in query_lower or any(word in query_lower for word in ["contact", "deal", "marketing"]):
                systems_mentioned.append("hubspot")
            
            # Determine primary intent
            primary_intent = "general_inquiry"
            if intent_categories:
                primary_intent = intent_categories[0]
            
            # Estimate processing time based on complexity and systems
            estimated_time_seconds = 5  # Base time
            if complexity == "medium":
                estimated_time_seconds = 10
            elif complexity == "complex":
                estimated_time_seconds = 20
            
            estimated_time_seconds += len(systems_mentioned) * 3  # Additional time per system
            
            analysis_result = {
                "intent": primary_intent,
                "intent_categories": intent_categories,
                "complexity": complexity,
                "systems_mentioned": systems_mentioned,
                "estimated_time_seconds": estimated_time_seconds,
                "requires_multiple_systems": len(systems_mentioned) > 1,
                "word_count": len(query.split()),
                "has_specific_entities": bool(systems_mentioned or intent_categories)
            }
            
# Analysis completed - event will be emitted by main generator
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            # Return basic analysis
            return {
                "intent": "general_inquiry",
                "complexity": "simple",
                "systems_mentioned": [],
                "estimated_time_seconds": 5,
                "error": str(e)
            }
    
    async def _execute_agent_task_streaming(
        self,
        agent_id: str,
        query: str,
        session_id: str,
        user_id: str,
        db: Session
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute agent task with streaming tool execution."""
        
        try:
            # Get integration for this agent (run in thread pool to avoid blocking)
            integration_id = agent_id.replace("integration_", "")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                integration = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda: db.query(Integration).filter(Integration.id == int(integration_id)).first()
                )
            
            if not integration:
                yield {
                    "type": StreamingEvent.ERROR,
                    "content": f"Integration not found for agent {agent_id}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            yield {
                "type": StreamingEvent.AGENT_EVENT,
                "content": f"Starting {integration.name} agent...",
                "metadata": {"agent_id": agent_id, "integration_type": integration.integration_type},
                "timestamp": datetime.utcnow().isoformat()
            }
            
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
            yield {
                "type": StreamingEvent.TOOL_CALL,
                "content": f"Executing {selected_tool.tool_name}...",
                "metadata": {
                    "tool_name": selected_tool.tool_name,
                    "integration": integration.name,
                    "status": "starting"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Tool events will be handled by the main generator flow
            
            # Start tracking tool execution
            execution_id = await tool_tracking_service.start_tool_execution(
                tool_name=selected_tool.tool_name,
                integration_id=integration.id,
                session_id=session_id,
                user_id=int(user_id),
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