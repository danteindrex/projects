import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

from crewai import Agent as CrewAIAgent, Task, Crew
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import log_agent_event
from app.core.kafka_service import publish_agent_event
from app.models.agent import Agent as DBAgent, AgentType, AgentStatus
from app.models.integration import Integration
from app.db.database import get_db_session
from app.tools.registry import tool_registry
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class CrewAIService:
    def __init__(self):
        self.main_agent = None
        self.github_agent = None
        self.jira_agent = None
        self.salesforce_agent = None
        self.slack_agent = None
        self.zendesk_agent = None
        self.hubspot_agent = None
        self.crew = None
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize CrewAI agents"""
        # Main coordination agent with delegation enabled
        self.main_agent = CrewAIAgent(
            role="Business Assistant Manager",
            goal="Coordinate business operations by delegating tasks to specialized agents",
            backstory="You are a business operations manager who coordinates work across different business systems and delegates tasks to specialized agents.",
            verbose=True,
            allow_delegation=True
        )
        
        # GitHub specialist agent
        self.github_agent = CrewAIAgent(
            role="GitHub Specialist",
            goal="Handle GitHub repository operations, issues, and pull requests",
            backstory="You are a GitHub specialist who manages repositories, creates issues, and handles version control operations.",
            verbose=True,
            allow_delegation=True  # ← ENABLE DELEGATION!
        )
        
        # Jira specialist agent
        self.jira_agent = CrewAIAgent(
            role="Jira Specialist", 
            goal="Manage Jira issues, projects, and workflows",
            backstory="You are a Jira specialist who handles issue tracking, project management, and workflow automation.",
            verbose=True,
            allow_delegation=False
        )
        
        # Salesforce specialist agent
        self.salesforce_agent = CrewAIAgent(
            role="Salesforce Specialist",
            goal="Handle CRM operations including leads, opportunities, and customer data",
            backstory="You are a Salesforce specialist who manages customer relationships, sales processes, and CRM data.",
            verbose=True,
            allow_delegation=False
        )
        
        # Slack specialist agent
        self.slack_agent = CrewAIAgent(
            role="Slack Specialist",
            goal="Handle team communication, channels, and messaging",
            backstory="You are a Slack specialist who manages team communication, sends messages, and coordinates channels.",
            verbose=True,
            allow_delegation=False
        )
        
        # Zendesk specialist agent
        self.zendesk_agent = CrewAIAgent(
            role="Zendesk Specialist",
            goal="Handle customer support tickets and help desk operations", 
            backstory="You are a Zendesk specialist who manages customer support, creates tickets, and handles help desk operations.",
            verbose=True,
            allow_delegation=False
        )
        
        # HubSpot specialist agent
        self.hubspot_agent = CrewAIAgent(
            role="HubSpot Specialist",
            goal="Handle marketing automation, contacts, and deals",
            backstory="You are a HubSpot specialist who manages marketing campaigns, contacts, and sales deals.",
            verbose=True,
            allow_delegation=False
        )
        
    async def process_user_query(self, query: str, user_id: str, tools: list = None, callback=None):
        """Process user query with CrewAI crew using user's configured integrations"""
        try:
            # Assign user's integration tools to specialist agents
            self._assign_tools_to_agents(tools or [])
            
            # Create task for the user query
            task = Task(
                description=f"""Analyze the user's request: "{query}"

If this is a simple conversational input (greeting, small talk, basic question), respond directly in a friendly, helpful manner without using any tools.

If this is a business/integration request that requires real data (asking about leads, tickets, issues, sales data, etc.), then use available tools to provide actual data from their configured integrations.

Always be conversational and helpful, matching the user's tone and intent.""",
                agent=self.main_agent,
                expected_output="A helpful response that matches the user's intent - either a direct conversational response or actual data from integrations when appropriate"
            )
            
            # Create crew with all agents
            all_agents = [
                self.main_agent,
                self.github_agent,
                self.jira_agent, 
                self.salesforce_agent,
                self.slack_agent,
                self.zendesk_agent,
                self.hubspot_agent
            ]
            
            crew = Crew(
                agents=all_agents,
                tasks=[task],
                verbose=True,
                step_callback=callback
            )
            
            # Execute the crew
            result = crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error(f"CrewAI processing failed: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def _assign_tools_to_agents(self, tools: list):
        """Assign integration tools to their respective specialist agents"""
        try:
            from app.tools.base import CrewAITool
            
            # Clear existing tools
            self.github_agent.tools = []
            self.jira_agent.tools = []
            self.salesforce_agent.tools = []
            self.slack_agent.tools = []
            self.zendesk_agent.tools = []
            self.hubspot_agent.tools = []
            
            # Assign tools based on their type
            for tool in tools:
                tool_name = tool.tool_name.lower()
                crewai_tool = CrewAITool(tool)
                
                # Fix: Check for tool type, not just name
                if hasattr(tool, 'integration_type') and tool.integration_type == 'github':
                    self.github_agent.tools.append(crewai_tool)
                elif 'github' in tool_name:  # Fallback to name check
                    self.github_agent.tools.append(crewai_tool)
                elif 'jira' in tool_name:
                    self.jira_agent.tools.append(crewai_tool)
                elif 'salesforce' in tool_name:
                    self.salesforce_agent.tools.append(crewai_tool)
                elif 'slack' in tool_name:
                    self.slack_agent.tools.append(crewai_tool)
                elif 'zendesk' in tool_name:
                    self.zendesk_agent.tools.append(crewai_tool)
                elif 'hubspot' in tool_name:
                    self.hubspot_agent.tools.append(crewai_tool)
            
            # Log which tools were assigned
            logger.info(f"Assigned {len(self.github_agent.tools)} GitHub tools")
            logger.info(f"Assigned {len(self.jira_agent.tools)} Jira tools")
            logger.info(f"Assigned {len(self.salesforce_agent.tools)} Salesforce tools")
            logger.info(f"Assigned {len(self.slack_agent.tools)} Slack tools")
            logger.info(f"Assigned {len(self.zendesk_agent.tools)} Zendesk tools")
            logger.info(f"Assigned {len(self.hubspot_agent.tools)} HubSpot tools")
            
        except Exception as e:
            logger.error(f"Error assigning tools to agents: {e}")
    
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
            self.router_agent = CrewAIAgent(
                role="System Router and Orchestrator",
                goal="Route user queries to appropriate integration agents and orchestrate responses",
                backstory="""You are an intelligent routing system that understands user queries 
                and determines which business systems (Jira, Salesforce, Zendesk, etc.) should handle them. 
                You excel at analyzing query intent and coordinating between multiple agents to provide 
                comprehensive responses.""",
                verbose=True,
                allow_delegation=True,
                llm=self.llm
            )
            
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
            
            # Load tools for this integration
            tools = await tool_registry.load_tools_for_integration(integration)
            crewai_tools = tool_registry.get_crewai_tools_for_integration(str(integration.id))
            
            # Create specialized agent based on integration type
            if integration.integration_type.lower() == 'jira':
                agent = self._create_jira_agent(integration, crewai_tools)
            elif integration.integration_type.lower() == 'salesforce':
                agent = self._create_salesforce_agent(integration, crewai_tools)
            elif integration.integration_type.lower() == 'zendesk':
                agent = self._create_zendesk_agent(integration, crewai_tools)
            elif integration.integration_type.lower() == 'slack':
                agent = self._create_slack_agent(integration, crewai_tools)
            elif integration.integration_type.lower() == 'github':
                agent = self._create_github_agent(integration, crewai_tools)
            elif integration.integration_type.lower() == 'hubspot':
                agent = self._create_hubspot_agent(integration, crewai_tools)
            else:
                agent = self._create_generic_integration_agent(integration, crewai_tools)
            
            self.integration_agents[agent_id] = agent
            
            log_agent_event(agent_id, "agent_created", integration_id=integration.id, tools_count=len(tools))
            await publish_agent_event(agent_id, "agent_created", {
                "integration_id": integration.id, 
                "tools_loaded": len(tools),
                "tool_names": [tool.tool_name for tool in tools]
            })
            
        except Exception as e:
            logger.error(f"Failed to create integration agent for {integration.name}: {e}")
            raise
    
    def _create_jira_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a specialized Jira agent"""
        return CrewAIAgent(
            role="Jira Integration Specialist",
            goal="Handle all Jira-related queries including issue management, project tracking, and reporting",
            backstory="""You are an expert in Jira project management and issue tracking. 
            You can create, update, and query issues, manage sprints, generate reports, 
            and help users navigate complex project workflows. You understand Jira's 
            data structures and can provide detailed insights about project status.
            
            You have access to real Jira API tools that allow you to:
            - Search for issues using JQL queries
            - Create new issues with proper fields
            - Update existing issues including status transitions
            - Get project information and statistics
            
            Always use your tools to provide accurate, real-time data from Jira.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
    def _create_salesforce_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a specialized Salesforce agent"""
        return CrewAIAgent(
            role="Salesforce CRM Expert",
            goal="Manage Salesforce data including leads, opportunities, accounts, and customer relationships",
            backstory="""You are a Salesforce CRM specialist who excels at managing 
            customer relationships, tracking sales pipelines, and generating insights 
            from CRM data. You understand the sales process and can help users 
            optimize their customer engagement strategies.
            
            You have access to real Salesforce API tools that allow you to:
            - Query records using SOQL (Accounts, Contacts, Opportunities, Leads)
            - Create new records in any Salesforce object
            - Update existing records with new information
            - Analyze sales pipelines and customer data
            
            Always use your tools to provide accurate, real-time data from Salesforce.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
    def _create_zendesk_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a specialized Zendesk agent"""
        return CrewAIAgent(
            role="Customer Support Specialist",
            goal="Handle customer support tickets, track resolution times, and improve support processes",
            backstory="""You are a customer support expert who specializes in ticket 
            management, customer communication, and support analytics. You excel at 
            prioritizing tickets, tracking resolution metrics, and identifying 
            opportunities to improve customer satisfaction.
            
            You have access to real Zendesk API tools that allow you to:
            - Search for tickets by status, priority, or custom queries
            - Create new support tickets with proper categorization
            - Update existing tickets including status changes and comments
            - Analyze support metrics and customer satisfaction data
            
            Always use your tools to provide accurate, real-time data from Zendesk.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
    def _create_slack_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a specialized Slack agent"""
        return CrewAIAgent(
            role="Team Communication Facilitator",
            goal="Manage team communications, notifications, and collaborative workflows through Slack",
            backstory="""You are a team collaboration expert who helps manage 
            communication channels, automate notifications, and facilitate 
            productive team interactions. You understand how to use Slack 
            effectively for different types of organizational communication.
            
            You have access to real Slack API tools that allow you to:
            - Send messages to channels or direct messages
            - Get channel lists and member information
            - Retrieve message history from channels
            - Manage team communications and notifications
            
            Always use your tools to provide accurate, real-time interaction with Slack.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
    def _create_generic_integration_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a generic integration agent"""
        return CrewAIAgent(
            role=f"{integration.name} Integration Agent",
            goal=f"Handle all operations and queries related to {integration.name}",
            backstory=f"""You are an expert in {integration.name} integration and API management. 
            You understand how to interact with {integration.name} systems, process data, 
            and provide meaningful insights to users. You excel at translating business 
            requirements into actionable system operations.
            
            You have access to real API tools that allow you to interact with {integration.name} 
            in real-time. Always use your available tools to provide accurate, up-to-date information.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
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
        """Route the query to appropriate agents using AI"""
        try:
            # Create a routing task for the router agent
            routing_task = Task(
                description=f"""Analyze this user query and determine which integration agents should handle it:
                
                Query: "{query}"
                
                Available integrations: {list(self.integration_agents.keys())}
                
                Provide a JSON response with:
                - agents: list of agent IDs that should handle this query
                - strategy: "sequential" or "parallel"
                - reasoning: explanation of routing decision
                
                Consider the query content and determine if it relates to:
                - Jira (issues, projects, sprints, development)
                - Salesforce (leads, opportunities, accounts, CRM)
                - Zendesk (tickets, customer support)
                - Slack (team communication, notifications)
                - Multiple systems (if query spans across integrations)
                """,
                agent=self.router_agent
            )
            
            # Execute the routing task
            crew = Crew(
                agents=[self.router_agent],
                tasks=[routing_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the AI response
            try:
                import re
                json_match = re.search(r'\{.*\}', str(result), re.DOTALL)
                if json_match:
                    routing_result = json.loads(json_match.group())
                else:
                    # Fallback to keyword-based routing
                    routing_result = self._fallback_routing(query)
            except:
                routing_result = self._fallback_routing(query)
            
            routing_result["query"] = query
            log_agent_event("router_001", "query_routed", routing_result=routing_result)
            return routing_result
            
        except Exception as e:
            logger.error(f"Failed to route query: {e}")
            # Fallback to simple routing
            return self._fallback_routing(query)
    
    def _fallback_routing(self, query: str) -> Dict[str, Any]:
        """Fallback routing logic when AI routing fails"""
        routing_result = {
            "agents": [],
            "strategy": "sequential",
            "reasoning": "Fallback keyword-based routing"
        }
        
        query_lower = query.lower()
        
        # Check for Jira-related keywords
        if any(keyword in query_lower for keyword in ["jira", "issue", "sprint", "project", "bug", "ticket", "development"]):
            available_jira = [k for k in self.integration_agents.keys() if "jira" in k.lower()]
            routing_result["agents"].extend(available_jira)
        
        # Check for Salesforce keywords
        if any(keyword in query_lower for keyword in ["salesforce", "lead", "opportunity", "account", "crm", "sales"]):
            available_sf = [k for k in self.integration_agents.keys() if "salesforce" in k.lower()]
            routing_result["agents"].extend(available_sf)
        
        # Check for Zendesk keywords
        if any(keyword in query_lower for keyword in ["zendesk", "support", "customer", "help"]):
            available_zd = [k for k in self.integration_agents.keys() if "zendesk" in k.lower()]
            routing_result["agents"].extend(available_zd)
        
        # Check for Slack keywords
        if any(keyword in query_lower for keyword in ["slack", "message", "channel", "notification", "team"]):
            available_slack = [k for k in self.integration_agents.keys() if "slack" in k.lower()]
            routing_result["agents"].extend(available_slack)
        
        # If no specific integrations found, use all available
        if not routing_result["agents"]:
            routing_result["agents"] = list(self.integration_agents.keys())[:2]  # Limit to first 2
            routing_result["strategy"] = "parallel"
        
        return routing_result
    
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
            
            # Create a task for the integration agent
            task = Task(
                description=f"""Process this user query: "{query}"
                
                As a specialized integration agent, provide:
                1. Analysis of what the user is asking for
                2. Specific actions you would take in your system
                3. Expected results or data you would retrieve
                4. Any limitations or additional information needed
                
                Be specific about your capabilities and provide actionable insights.
                """,
                agent=agent
            )
            
            # Execute the task
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )
            
            ai_result = crew.kickoff()
            
            result = {
                "agent_id": agent_id,
                "query": query,
                "result": str(ai_result),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "agent_role": agent.role
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
            # Create a general analysis task for the router
            task = Task(
                description=f"""Analyze this user query and provide a comprehensive response: "{query}"
                
                As the system router, provide:
                1. Understanding of what the user is asking
                2. General guidance or recommendations
                3. Suggestions for which systems or integrations might be helpful
                4. Next steps the user could take
                
                Be helpful and provide actionable insights even without specific integration access.
                """,
                agent=self.router_agent
            )
            
            # Execute the task
            crew = Crew(
                agents=[self.router_agent],
                tasks=[task],
                verbose=True
            )
            
            ai_result = crew.kickoff()
            
            result = {
                "agent_id": "router_001",
                "query": query,
                "result": str(ai_result),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "agent_role": self.router_agent.role
            }
            
            log_agent_event("router_001", "task_executed", result=result)
            await publish_agent_event("router_001", "task_executed", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute router task: {e}")
            raise
    
    async def _aggregate_results(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all agents using AI"""
        try:
            if len(execution_results) <= 1:
                # Single result, no aggregation needed
                agent_result = list(execution_results.values())[0] if execution_results else {}
                return {
                    "summary": agent_result.get("result", "No results available"),
                    "agent_results": execution_results,
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_agents": len(execution_results)
                }
            
            # Multiple results, use router agent to aggregate
            results_text = ""
            for agent_id, result in execution_results.items():
                results_text += f"\n\nAgent: {result.get('agent_role', agent_id)}\n"
                results_text += f"Response: {result.get('result', 'No response')}\n"
            
            aggregation_task = Task(
                description=f"""Aggregate and synthesize these responses from multiple agents:
                {results_text}
                
                Provide a comprehensive summary that:
                1. Combines the key insights from all agents
                2. Identifies any conflicts or inconsistencies
                3. Provides a unified recommendation or next steps
                4. Highlights the most important information for the user
                
                Make the response coherent and actionable.
                """,
                agent=self.router_agent
            )
            
            crew = Crew(
                agents=[self.router_agent],
                tasks=[aggregation_task],
                verbose=True
            )
            
            aggregated_summary = crew.kickoff()
            
            return {
                "summary": str(aggregated_summary),
                "agent_results": execution_results,
                "timestamp": datetime.utcnow().isoformat(),
                "total_agents": len(execution_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            # Fallback to simple aggregation
            return {
                "summary": f"Query processed by {len(execution_results)} agents. Check individual agent results for details.",
                "agent_results": execution_results,
                "timestamp": datetime.utcnow().isoformat(),
                "total_agents": len(execution_results),
                "error": str(e)
            }
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific agent"""
        if agent_id == "router_001" and self.router_agent:
            return {
                "id": "router_001",
                "role": self.router_agent.role,
                "goal": self.router_agent.goal,
                "status": "active",
                "type": "router"
            }
        elif agent_id in self.integration_agents:
            agent = self.integration_agents[agent_id]
            return {
                "id": agent_id,
                "role": agent.role,
                "goal": agent.goal,
                "status": "active",
                "type": "integration"
            }
        return None
    
    async def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        router_status = None
        if self.router_agent:
            router_status = {
                "id": "router_001",
                "role": self.router_agent.role,
                "goal": self.router_agent.goal,
                "status": "active",
                "type": "router"
            }
        
        integration_status = {}
        for agent_id, agent in self.integration_agents.items():
            integration_status[agent_id] = {
                "id": agent_id,
                "role": agent.role,
                "goal": agent.goal,
                "status": "active",
                "type": "integration"
            }
        
        return {
            "router_agent": router_status,
            "integration_agents": integration_status,
            "total_agents": len(self.integration_agents) + (1 if self.router_agent else 0),
            "llm_model": "gpt-4-turbo-preview"
        }
    
    async def create_agent_for_integration(self, integration: Integration) -> str:
        """Create and register a new AI agent for a specific integration"""
        try:
            agent_id = f"integration_{integration.id}_{integration.name.lower().replace(' ', '_')}"
            
            # Check if agent already exists
            if agent_id in self.integration_agents:
                logger.info(f"Agent {agent_id} already exists, updating...")
                await self._update_integration_agent(integration, agent_id)
                return agent_id
            
            # Create new specialized agent
            agent = self._create_specialized_agent_by_type(integration)
            
            # Register the agent
            self.integration_agents[agent_id] = agent
            
            # Log and publish events
            log_agent_event(agent_id, "agent_created_for_integration", 
                          integration_id=integration.id, 
                          integration_name=integration.name,
                          integration_type=integration.type)
            
            await publish_agent_event(agent_id, "agent_created_for_integration", {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "integration_type": integration.type,
                "agent_role": agent.role
            })
            
            logger.info(f"Successfully created agent {agent_id} for integration {integration.name}")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent for integration {integration.name}: {e}")
            raise
    
    def _create_specialized_agent_by_type(self, integration: Integration) -> CrewAIAgent:
        """Create a specialized agent based on integration type"""
        integration_type = integration.type.lower() if hasattr(integration.type, 'lower') else str(integration.type).lower()
        
        # Create agents based on specific integration types
        if integration_type in ['jira', 'atlassian']:
            return self._create_jira_agent(integration)
        elif integration_type in ['salesforce', 'sfdc', 'crm']:
            return self._create_salesforce_agent(integration)
        elif integration_type in ['zendesk', 'support', 'helpdesk']:
            return self._create_zendesk_agent(integration)
        elif integration_type in ['slack', 'chat', 'communication']:
            return self._create_slack_agent(integration)
        elif integration_type in ['github', 'git', 'repository']:
            return self._create_github_agent(integration)
        elif integration_type in ['hubspot', 'marketing']:
            return self._create_hubspot_agent(integration)
        elif integration_type in ['asana', 'project']:
            return self._create_asana_agent(integration)
        elif integration_type in ['trello', 'board']:
            return self._create_trello_agent(integration)
        else:
            return self._create_generic_integration_agent(integration)
    
    def _create_github_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a specialized GitHub agent"""
        return CrewAIAgent(
            role="GitHub Repository Manager",
            goal="Use GitHub API tools to fetch real repository data and manage GitHub operations",
            backstory=f"""You are a GitHub API specialist for the {integration.name} integration. 

CRITICAL: You MUST always use your available GitHub tools to fetch real data. Never provide manual instructions or generic advice.

When asked for repositories, issues, or any GitHub data:
1. FIRST use your GitHub tools to fetch the actual data
2. Present the real results from the API calls
3. If tools fail, explain the specific error

Available GitHub API operations:
- Search repositories, issues, pull requests, and users  
- Create new issues in repositories
- Get detailed repository information including commits and statistics
- Manage development workflows and collaboration

ALWAYS use tools first. Never give manual instructions unless tools completely fail.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
    def _create_hubspot_agent(self, integration: Integration, tools: List = None) -> CrewAIAgent:
        """Create a specialized HubSpot agent"""
        return CrewAIAgent(
            role="HubSpot Marketing & CRM Specialist",
            goal="Manage HubSpot marketing campaigns, lead generation, and customer relationship data",
            backstory=f"""You are a HubSpot expert managing the {integration.name} integration. 
            You specialize in inbound marketing, lead nurturing, sales pipeline management, 
            and marketing automation. You understand customer journey mapping and conversion optimization.
            
            You have access to real HubSpot API tools that allow you to:
            - Search and retrieve contacts by various criteria
            - Create new contacts with detailed information
            - Search and manage deals in the sales pipeline
            - Analyze marketing and sales performance data
            
            Always use your tools to provide accurate, real-time data from HubSpot.""",
            verbose=True,
            llm=self.llm,
            tools=tools or []
        )
    
    def _create_asana_agent(self, integration: Integration) -> CrewAIAgent:
        """Create a specialized Asana agent"""
        return CrewAIAgent(
            role="Asana Project Coordinator",
            goal="Coordinate Asana projects, tasks, and team collaboration workflows",
            backstory=f"""You are an Asana project management expert handling the {integration.name} integration. 
            You excel at task organization, project planning, team collaboration, and workflow optimization. 
            You understand agile methodologies and resource management.""",
            verbose=True,
            llm=self.llm
        )
    
    def _create_trello_agent(self, integration: Integration) -> CrewAIAgent:
        """Create a specialized Trello agent"""
        return CrewAIAgent(
            role="Trello Board Organizer",
            goal="Organize Trello boards, cards, and kanban workflow management",
            backstory=f"""You are a Trello organization specialist managing the {integration.name} integration. 
            You excel at visual project management, kanban workflows, and team collaboration through 
            boards and cards. You understand workflow optimization and productivity enhancement.""",
            verbose=True,
            llm=self.llm
        )
    
    async def _update_integration_agent(self, integration: Integration, agent_id: str):
        """Update an existing integration agent with new information"""
        try:
            # Create a new agent with updated information
            updated_agent = self._create_specialized_agent_by_type(integration)
            
            # Replace the existing agent
            self.integration_agents[agent_id] = updated_agent
            
            log_agent_event(agent_id, "agent_updated_for_integration", 
                          integration_id=integration.id,
                          integration_name=integration.name)
            
            await publish_agent_event(agent_id, "agent_updated_for_integration", {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "integration_type": integration.type
            })
            
            logger.info(f"Successfully updated agent {agent_id} for integration {integration.name}")
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise
    
    async def remove_agent_for_integration(self, integration_id: int) -> bool:
        """Remove an agent when an integration is deleted"""
        try:
            # Find agents associated with this integration
            agents_to_remove = [
                agent_id for agent_id in self.integration_agents.keys() 
                if f"integration_{integration_id}_" in agent_id
            ]
            
            for agent_id in agents_to_remove:
                # Remove the agent
                del self.integration_agents[agent_id]
                
                log_agent_event(agent_id, "agent_removed_for_integration", 
                              integration_id=integration_id)
                
                await publish_agent_event(agent_id, "agent_removed_for_integration", {
                    "integration_id": integration_id
                })
                
                logger.info(f"Successfully removed agent {agent_id} for integration {integration_id}")
            
            return len(agents_to_remove) > 0
            
        except Exception as e:
            logger.error(f"Failed to remove agent for integration {integration_id}: {e}")
            return False

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

async def create_agent_for_integration(integration: Integration) -> str:
    """Create a new AI agent for an integration"""
    return await crewai_service.create_agent_for_integration(integration)

async def remove_agent_for_integration(integration_id: int) -> bool:
    """Remove an agent when integration is deleted"""
    return await crewai_service.remove_agent_for_integration(integration_id)
