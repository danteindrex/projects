"""
Comprehensive Pydantic models for AI agent outputs and responses.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator

# Agent status and result enums
class AgentExecutionStatus(str, Enum):
    """Status of agent task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResponseType(str, Enum):
    """Type of agent response."""
    TEXT = "text"
    DATA = "data"
    ERROR = "error"
    TOOL_RESULT = "tool_result"
    AGGREGATED = "aggregated"


class AgentType(str, Enum):
    """Type of AI agent."""
    ROUTER = "router"
    INTEGRATION = "integration"
    ANALYTICAL = "analytical"
    ORCHESTRATOR = "orchestrator"


# Base response models
class BaseAgentResponse(BaseModel):
    """Base response model for all agent outputs."""
    id: str = Field(..., description="Unique identifier for this response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this response was generated")
    agent_id: str = Field(..., description="ID of the agent that generated this response")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: AgentExecutionStatus = Field(..., description="Execution status")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentMetadata(BaseModel):
    """Metadata about agent execution."""
    agent_role: str = Field(..., description="Role description of the agent")
    agent_goal: str = Field(..., description="Goal description of the agent")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    model_used: Optional[str] = Field(None, description="LLM model used")
    temperature: Optional[float] = Field(None, description="Model temperature setting")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")


class ToolReference(BaseModel):
    """Reference to a tool used by an agent."""
    tool_name: str = Field(..., description="Name of the tool")
    tool_version: Optional[str] = Field(None, description="Version of the tool")
    integration_id: Optional[str] = Field(None, description="ID of the integration this tool belongs to")
    execution_id: Optional[str] = Field(None, description="Execution ID for tracking")


class AgentResponse(BaseAgentResponse):
    """Individual agent response model."""
    response_type: ResponseType = Field(..., description="Type of response")
    content: str = Field(..., description="Main response content")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data returned")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[AgentMetadata] = Field(None, description="Agent execution metadata")
    tools_used: List[ToolReference] = Field(default_factory=list, description="Tools used in this response")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in the response")
    reasoning: Optional[str] = Field(None, description="Agent's reasoning process")
    sources: List[str] = Field(default_factory=list, description="Data sources referenced")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v
    
    @root_validator
    def validate_response_consistency(cls, values):
        status = values.get('status')
        error = values.get('error')
        content = values.get('content')
        
        if status == AgentExecutionStatus.FAILED and not error:
            raise ValueError('Failed responses must include an error message')
        if status == AgentExecutionStatus.COMPLETED and not content:
            raise ValueError('Completed responses must include content')
        return values


class RoutingDecision(BaseModel):
    """Routing decision for multi-agent queries."""
    agents: List[str] = Field(..., description="List of agent IDs to route to")
    strategy: Literal["sequential", "parallel"] = Field(..., description="Execution strategy")
    reasoning: str = Field(..., description="Explanation of routing decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in routing decision")
    fallback_agents: List[str] = Field(default_factory=list, description="Fallback agents if primary fails")


class AggregatedResponse(BaseAgentResponse):
    """Aggregated response from multiple agents."""
    query: str = Field(..., description="Original user query")
    routing_decision: RoutingDecision = Field(..., description="How the query was routed")
    individual_responses: List[AgentResponse] = Field(..., description="Individual agent responses")
    summary: str = Field(..., description="Aggregated summary of all responses")
    synthesis_reasoning: Optional[str] = Field(None, description="How responses were synthesized")
    conflicts_detected: List[str] = Field(default_factory=list, description="Any conflicts between responses")
    consensus_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Level of consensus between agents")
    total_execution_time_ms: Optional[int] = Field(None, description="Total execution time across all agents")
    
    @validator('individual_responses')
    def validate_responses_exist(cls, v):
        if not v:
            raise ValueError('Aggregated response must contain at least one individual response')
        return v


# Analytics-specific response models
class MetricValue(BaseModel):
    """A single metric value with metadata."""
    name: str = Field(..., description="Metric name")
    value: Union[int, float, str] = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When metric was measured")
    source: Optional[str] = Field(None, description="Source system for this metric")


class AnalyticsInsight(BaseModel):
    """Analytical insight generated by AI."""
    insight_id: str = Field(..., description="Unique identifier for the insight")
    title: str = Field(..., description="Title of the insight")
    description: str = Field(..., description="Detailed description")
    insight_type: Literal["trend", "anomaly", "recommendation", "forecast", "correlation"] = Field(..., description="Type of insight")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the insight")
    impact_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Potential impact level")
    supporting_data: List[MetricValue] = Field(default_factory=list, description="Data supporting this insight")
    actionable_recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")


class AgentAnalyticsResponse(BaseAgentResponse):
    """Analytics-specific agent response."""
    query_type: Literal["dashboard", "report", "insight", "forecast", "comparison"] = Field(..., description="Type of analytics query")
    metrics: List[MetricValue] = Field(default_factory=list, description="Metrics calculated")
    insights: List[AnalyticsInsight] = Field(default_factory=list, description="AI-generated insights")
    visualizations: List[Dict[str, Any]] = Field(default_factory=list, description="Visualization configurations")
    data_sources: List[str] = Field(..., description="Data sources used")
    time_range: Optional[Dict[str, str]] = Field(None, description="Time range for analytics")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters applied to data")
    
    @validator('insights')
    def validate_insights_quality(cls, v):
        for insight in v:
            if insight.confidence < 0.3:
                raise ValueError(f'Insight "{insight.title}" has too low confidence ({insight.confidence})')
        return v


# Error and failure models
class AgentError(BaseModel):
    """Detailed error information for agent failures."""
    error_code: str = Field(..., description="Error code for categorization")
    error_type: Literal["validation", "execution", "timeout", "integration", "model", "network"] = Field(..., description="Type of error")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    resolution_steps: List[str] = Field(default_factory=list, description="Suggested resolution steps")
    retry_possible: bool = Field(default=True, description="Whether the operation can be retried")
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "TOOL_EXECUTION_FAILED",
                "error_type": "execution",
                "message": "Jira API returned authentication error",
                "details": {"status_code": 401, "api_endpoint": "/rest/api/2/search"},
                "resolution_steps": ["Check API credentials", "Verify API permissions"],
                "retry_possible": True
            }
        }


class FailedAgentResponse(BaseAgentResponse):
    """Response model for failed agent executions."""
    error: AgentError = Field(..., description="Detailed error information")
    partial_results: Optional[Dict[str, Any]] = Field(None, description="Any partial results before failure")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context at time of failure")
    
    def __init__(self, **data):
        data['status'] = AgentExecutionStatus.FAILED
        data['response_type'] = ResponseType.ERROR
        super().__init__(**data)


# Union type for all possible agent responses
AgentResponseUnion = Union[AgentResponse, AggregatedResponse, AgentAnalyticsResponse, FailedAgentResponse]


# Serialization helpers
class AgentResponseSerializer:
    """Helper class for serializing/deserializing agent responses."""
    
    @staticmethod
    def to_dict(response: BaseAgentResponse) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return response.dict(by_alias=True)
    
    @staticmethod
    def to_json(response: BaseAgentResponse) -> str:
        """Convert response to JSON string."""
        return response.json(by_alias=True)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> AgentResponseUnion:
        """Create response from dictionary."""
        response_type = data.get('response_type', 'text')
        
        if 'individual_responses' in data:
            return AggregatedResponse(**data)
        elif 'metrics' in data or 'insights' in data:
            return AgentAnalyticsResponse(**data)
        elif data.get('status') == AgentExecutionStatus.FAILED or 'error' in data:
            return FailedAgentResponse(**data)
        else:
            return AgentResponse(**data)
    
    @staticmethod
    def from_json(json_str: str) -> AgentResponseUnion:
        """Create response from JSON string."""
        import json
        data = json.loads(json_str)
        return AgentResponseSerializer.from_dict(data)


# Response validation functions
def validate_agent_response(response: Dict[str, Any]) -> bool:
    """Validate that a response dictionary is properly formatted."""
    try:
        AgentResponseSerializer.from_dict(response)
        return True
    except Exception:
        return False


def sanitize_agent_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and clean agent response data."""
    # Remove any sensitive information
    sensitive_keys = ['api_key', 'password', 'token', 'secret', 'credential']
    
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items() 
                   if not any(sens in k.lower() for sens in sensitive_keys)}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        else:
            return d
    
    return clean_dict(response)