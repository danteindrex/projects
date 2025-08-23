"""
Base tool classes for business system integrations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import asyncio
import logging
import json
from datetime import datetime
from pydantic import BaseModel, Field
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from crewai.tools import tool

logger = logging.getLogger(__name__)


class ToolCredentials(BaseModel):
    """Base model for tool credentials."""
    integration_type: str
    credentials: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionEvent(BaseModel):
    """Event emitted during tool execution."""
    type: str  # 'start', 'progress', 'complete', 'error'
    tool_name: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class BaseBusinessTool(ABC):
    """
    Abstract base class for all business system integration tools.
    Provides common functionality for authentication, error handling, and logging.
    """
    
    def __init__(
        self, 
        credentials: ToolCredentials,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.credentials = credentials
        self.timeout = timeout
        self.max_retries = max_retries
        self.name = self.__class__.__name__
        self.integration_type = credentials.integration_type
        
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Unique name for this tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does."""
        pass
    
    @property
    @abstractmethod
    def required_credentials(self) -> List[str]:
        """List of required credential fields."""
        pass
    
    def validate_credentials(self) -> bool:
        """Validate that all required credentials are present."""
        creds = self.credentials.credentials
        missing = [field for field in self.required_credentials if field not in creds]
        if missing:
            logger.error(f"Missing required credentials for {self.tool_name}: {missing}")
            return False
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response
    
    async def emit_event(self, event: ToolExecutionEvent) -> None:
        """Emit tool execution event for streaming."""
        # This will be connected to WebSocket streaming later
        logger.info(f"Tool Event: {event.type} - {event.tool_name} - {event.message}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute the tool with given parameters."""
        pass
    
    async def test_connection(self) -> ToolExecutionResult:
        """Test connection to the business system."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message="Testing connection..."
            ))
            
            if not self.validate_credentials():
                raise ValueError("Invalid credentials")
            
            # Subclasses should override this for specific connection tests
            result = await self._test_connection_impl()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message="Connection test successful"
            ))
            
            return ToolExecutionResult(
                success=True,
                data=result,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "test_connection"}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Connection test failed: {error_msg}"
            ))
            
            logger.error(f"Connection test failed for {self.tool_name}: {error_msg}")
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "test_connection"}
            )
    
    @abstractmethod
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Implementation-specific connection test."""
        pass


def CrewAITool(business_tool: BaseBusinessTool):
    """
    Wrapper factory to make BaseBusinessTool compatible with CrewAI framework.
    Returns a CrewAI tool created using the @tool decorator.
    """
    
    @tool(business_tool.tool_name)
    def execute_business_tool(**kwargs) -> str:
        """Execute business tool operation. This tool provides real-time data from integrated business systems and supports various operations including search, create, update, and data retrieval. Parameters: query (str): Input parameters for the tool operation. Returns: str: JSON formatted results from the business tool operation."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def run_async_in_thread():
            """Run the async business tool in a separate thread with its own event loop."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(business_tool.execute(**kwargs))
            finally:
                new_loop.close()
        
        # Run the async function in a separate thread to avoid event loop conflicts
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_in_thread)
            result = future.result()
        
        if result.success:
            return json.dumps(result.data, default=str)
        else:
            return f"Error: {result.error}"
    
    return execute_business_tool


class ToolCategory:
    """Tool categories for organization."""
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"