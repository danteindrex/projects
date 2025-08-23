"""
Tool Registry System for dynamic tool loading and management.
"""
from typing import Dict, List, Optional, Type, Any
import logging
from collections import defaultdict
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolCredentials, CrewAITool
from app.models.integration import Integration
from app.core.encryption import encryption_service

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for managing business system tools.
    Handles tool discovery, loading, and lifecycle management.
    """
    
    def __init__(self):
        self._tool_classes: Dict[str, Type[BaseBusinessTool]] = {}
        self._active_tools: Dict[str, Dict[str, BaseBusinessTool]] = defaultdict(dict)
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        
    def register_tool_class(
        self, 
        integration_type: str, 
        tool_class: Type[BaseBusinessTool],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool class for an integration type."""
        key = f"{integration_type}_{tool_class.__name__}"
        self._tool_classes[key] = tool_class
        self._tool_metadata[key] = metadata or {}
        
        logger.info(f"Registered tool class: {key}")
    
    def get_available_tools(self, integration_type: str) -> List[Dict[str, Any]]:
        """Get available tools for an integration type."""
        tools = []
        for key, tool_class in self._tool_classes.items():
            if key.startswith(f"{integration_type}_"):
                tools.append({
                    "name": tool_class.__name__,
                    "tool_name": tool_class.tool_name if hasattr(tool_class, 'tool_name') else key,
                    "description": tool_class.__doc__ or "No description available",
                    "integration_type": integration_type,
                    "metadata": self._tool_metadata.get(key, {})
                })
        return tools
    
    async def load_tools_for_integration(
        self, 
        integration: Integration
    ) -> List[BaseBusinessTool]:
        """Load and initialize tools for a specific integration."""
        tools = []
        
        try:
            # Decrypt credentials
            decrypted_creds = encryption_service.decrypt_credentials(
                integration.encrypted_credentials
            )
            
            # Create tool credentials
            credentials = ToolCredentials(
                integration_type=integration.integration_type,
                credentials=decrypted_creds,
                is_active=integration.is_active
            )
            
            # Find and instantiate tools for this integration type
            for key, tool_class in self._tool_classes.items():
                if key.startswith(f"{integration.integration_type.lower()}_"):
                    try:
                        tool = tool_class(credentials)
                        
                        # Test connection before adding to active tools
                        test_result = await tool.test_connection()
                        if test_result.success:
                            tools.append(tool)
                            
                            # Store in active tools
                            self._active_tools[str(integration.id)][tool.tool_name] = tool
                            
                            logger.info(f"Successfully loaded tool: {tool.tool_name} for integration {integration.id}")
                        else:
                            logger.warning(f"Tool connection test failed: {tool.tool_name} - {test_result.error}")
                            
                    except Exception as e:
                        logger.error(f"Failed to load tool {tool_class.__name__}: {str(e)}")
                        continue
            
            logger.info(f"Loaded {len(tools)} tools for integration {integration.id}")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to load tools for integration {integration.id}: {str(e)}")
            return []
    
    def get_tools_for_integration(self, integration_id: str) -> List[BaseBusinessTool]:
        """Get active tools for an integration."""
        return list(self._active_tools.get(integration_id, {}).values())
    
    def get_crewai_tools_for_integration(self, integration_id: str) -> List[CrewAITool]:
        """Get CrewAI-compatible tools for an integration."""
        business_tools = self.get_tools_for_integration(integration_id)
        return [CrewAITool(tool) for tool in business_tools]
    
    def get_all_crewai_tools_for_user(self, user_integrations: List[Integration]) -> List[CrewAITool]:
        """Get all CrewAI tools for a user's active integrations."""
        all_tools = []
        for integration in user_integrations:
            if integration.is_active:
                tools = self.get_crewai_tools_for_integration(str(integration.id))
                all_tools.extend(tools)
        return all_tools
    
    def unload_tools_for_integration(self, integration_id: str) -> None:
        """Unload tools for an integration."""
        if integration_id in self._active_tools:
            del self._active_tools[integration_id]
            logger.info(f"Unloaded tools for integration {integration_id}")
    
    def get_tool_by_name(self, integration_id: str, tool_name: str) -> Optional[BaseBusinessTool]:
        """Get a specific tool by name."""
        return self._active_tools.get(integration_id, {}).get(tool_name)
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded tools."""
        stats = {
            "total_tool_classes": len(self._tool_classes),
            "active_integrations": len(self._active_tools),
            "total_active_tools": sum(len(tools) for tools in self._active_tools.values()),
            "tools_by_integration": {
                integration_id: list(tools.keys()) 
                for integration_id, tools in self._active_tools.items()
            }
        }
        return stats


# Global tool registry instance
tool_registry = ToolRegistry()


# Tool registration decorators
def register_tool(integration_type: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator to register a tool class."""
    def decorator(tool_class: Type[BaseBusinessTool]):
        tool_registry.register_tool_class(integration_type, tool_class, metadata)
        return tool_class
    return decorator


# Auto-discovery functions
def discover_and_register_tools():
    """Discover and register all available tools."""
    # Import all tool modules to trigger registration
    try:
        from app.tools import jira, salesforce, github, zendesk, slack, hubspot
        logger.info("Successfully discovered and registered all tools")
    except ImportError as e:
        logger.warning(f"Some tools modules not found: {e}")


# Initialize tool discovery
def initialize_tool_registry():
    """Initialize the tool registry with all available tools."""
    discover_and_register_tools()
    logger.info("Tool registry initialized")