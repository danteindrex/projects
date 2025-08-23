from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, Dict, Any, List
from app.models.integration import IntegrationType, IntegrationStatus

class IntegrationBase(BaseModel):
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    base_url: str  # Changed from HttpUrl to str to match database model
    config: Optional[Dict[str, Any]] = {}
    rate_limit: Optional[int] = 100
    timeout: Optional[int] = 30

class IntegrationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    integration_type: IntegrationType
    credentials: Dict[str, str]  # Will be encrypted before storage
    config: Optional[Dict[str, Any]] = {}
    rate_limit: Optional[int] = 100
    timeout: Optional[int] = 30
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError('Integration name must be at least 2 characters long')
        return v

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    timeout: Optional[int] = None
    status: Optional[IntegrationStatus] = None

class IntegrationResponse(IntegrationBase):
    id: int
    external_id: str
    tenant_id: str
    status: IntegrationStatus
    health_status: str
    error_count: Optional[int] = 0  # Make nullable with default
    last_error: Optional[str] = None
    last_health_check: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True
        # Allow string for base_url since the database stores it as String, not HttpUrl
        json_encoders = {
            str: lambda v: str(v) if v else None
        }

class IntegrationDataResponse(BaseModel):
    """Response for integration-specific data endpoints"""
    success: bool = True
    data: List[Any] = []
    total: Optional[int] = None
    page: Optional[int] = None
    per_page: Optional[int] = None
    message: Optional[str] = None
    
    class Config:
        from_attributes = True

class IntegrationTestRequest(BaseModel):
    base_url: HttpUrl
    credentials: Dict[str, str]
    test_endpoint: Optional[str] = "/health"
    timeout: Optional[int] = 30

class IntegrationTestResponse(BaseModel):
    success: bool
    message: str
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_details: Optional[str] = None

class IntegrationHealth(BaseModel):
    integration_id: int
    status: str
    response_time: float
    last_check: str
    error_count: int
    uptime_percentage: float

# Integration-specific data response schemas
class IntegrationDataResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    total: Optional[int] = None
    page: Optional[int] = None
    per_page: Optional[int] = None
    message: Optional[str] = None

# GitHub schemas
class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    private: bool
    html_url: str
    clone_url: str
    language: Optional[str] = None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    visibility: str
    created_at: str
    updated_at: str
    pushed_at: str

class GitHubIssue(BaseModel):
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    user: Dict[str, Any]
    assignee: Optional[Dict[str, Any]] = None
    labels: List[Dict[str, Any]]
    pull_request: Optional[Dict[str, str]] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None

# Slack schemas
class SlackChannel(BaseModel):
    id: str
    name: str
    is_channel: bool
    is_group: bool
    is_im: bool
    is_private: bool
    is_archived: bool
    num_members: int
    purpose: Optional[Dict[str, Any]] = None
    topic: Optional[Dict[str, Any]] = None
    created: int

class SlackUser(BaseModel):
    id: str
    name: str
    real_name: Optional[str] = None
    profile: Dict[str, Any]
    is_bot: bool
    is_admin: bool
    is_owner: bool
    is_primary_owner: bool
    is_restricted: bool
    is_ultra_restricted: bool
    deleted: bool

# Jira schemas
class JiraProject(BaseModel):
    id: str
    key: str
    name: str
    description: Optional[str] = None
    projectTypeKey: str
    avatarUrls: Optional[Dict[str, str]] = None
    lead: Optional[Dict[str, str]] = None

class JiraIssue(BaseModel):
    id: str
    key: str
    fields: Dict[str, Any]

# Salesforce schemas
class SalesforceAccount(BaseModel):
    Id: str
    Name: str
    Type: Optional[str] = None
    Industry: Optional[str] = None
    Website: Optional[str] = None
    Phone: Optional[str] = None
    BillingCity: Optional[str] = None
    BillingState: Optional[str] = None
    BillingCountry: Optional[str] = None
    NumberOfEmployees: Optional[int] = None
    AnnualRevenue: Optional[float] = None
    CreatedDate: str
    LastModifiedDate: str

class SalesforceOpportunity(BaseModel):
    Id: str
    Name: str
    StageName: str
    CloseDate: str
    Amount: Optional[float] = None
    Probability: Optional[int] = None
    Type: Optional[str] = None
    LeadSource: Optional[str] = None
    Description: Optional[str] = None
    AccountId: Optional[str] = None
    Account: Optional[Dict[str, str]] = None
    CreatedDate: str
    LastModifiedDate: str

class SalesforceLead(BaseModel):
    Id: str
    FirstName: Optional[str] = None
    LastName: str
    Company: str
    Title: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    Status: str
    LeadSource: Optional[str] = None
    Industry: Optional[str] = None
    Rating: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Country: Optional[str] = None
    CreatedDate: str
    LastModifiedDate: str
    ConvertedDate: Optional[str] = None

# Zendesk schemas
class ZendeskTicket(BaseModel):
    id: int
    subject: str
    description: Optional[str] = None
    status: str
    priority: Optional[str] = None
    type: Optional[str] = None
    requester: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = None
    tags: List[str]
    created_at: str
    updated_at: str

class ZendeskUser(BaseModel):
    id: int
    name: str
    email: str
    role: str
    active: bool
    verified: bool
    suspended: bool
    organization_id: Optional[int] = None
    phone: Optional[str] = None
    time_zone: Optional[str] = None
    created_at: str
    updated_at: str

class ZendeskOrganization(BaseModel):
    id: int
    name: str
    domain_names: List[str]
    details: Optional[str] = None
    notes: Optional[str] = None
    shared_tickets: bool
    shared_comments: bool
    external_id: Optional[str] = None
    created_at: str
    updated_at: str

# Trello schemas
class TrelloBoard(BaseModel):
    id: str
    name: str
    desc: Optional[str] = None
    closed: bool
    url: str
    shortUrl: str
    prefs: Dict[str, Any]
    dateLastActivity: str
    dateLastView: Optional[str] = None

class TrelloList(BaseModel):
    id: str
    name: str
    closed: bool
    pos: float
    idBoard: str

class TrelloCard(BaseModel):
    id: str
    name: str
    desc: Optional[str] = None
    closed: bool
    idList: str
    idBoard: str
    pos: float
    url: str
    shortUrl: str
    due: Optional[str] = None
    dueComplete: bool
    dateLastActivity: str
    labels: List[Dict[str, Any]]
    members: List[Dict[str, Any]]

# Asana schemas
class AsanaProject(BaseModel):
    gid: str
    name: str
    notes: Optional[str] = None
    archived: bool
    current_status: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, str]] = None
    owner: Optional[Dict[str, str]] = None
    created_at: str
    modified_at: str

class AsanaTask(BaseModel):
    gid: str
    name: str
    notes: Optional[str] = None
    completed: bool
    due_on: Optional[str] = None
    due_at: Optional[str] = None
    projects: Optional[List[Dict[str, str]]] = None
    assignee: Optional[Dict[str, str]] = None
    created_at: str
    modified_at: str
    completed_at: Optional[str] = None

class AsanaTeam(BaseModel):
    gid: str
    name: str
    description: Optional[str] = None
    organization: Optional[Dict[str, str]] = None
