"""
Integration data endpoints for fetching specific data from each integration type.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.database import get_db_session
from app.models.user import User
from app.models.integration import Integration
from app.services.integration_service import integration_service
from app.schemas.integration import IntegrationDataResponse
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/{integration_id}/github/repositories")
async def get_github_repositories(
    integration_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get repositories from a GitHub integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "github":
        raise HTTPException(status_code=400, detail="Integration is not a GitHub integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/user/repos",
            params={"page": page, "per_page": per_page, "sort": "updated", "direction": "desc"}
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=len(result) if result else 0,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch GitHub repositories: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch repositories: {str(e)}"
        )

@router.get("/{integration_id}/github/issues")
async def get_github_issues(
    integration_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    state: str = Query(default="all", regex="^(open|closed|all)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get issues from a GitHub integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "github":
        raise HTTPException(status_code=400, detail="Integration is not a GitHub integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/issues",
            params={
                "page": page, 
                "per_page": per_page, 
                "state": state,
                "sort": "updated",
                "direction": "desc"
            }
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=len(result) if result else 0,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch GitHub issues: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch issues: {str(e)}"
        )

@router.get("/{integration_id}/slack/channels")
async def get_slack_channels(
    integration_id: int,
    exclude_archived: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get channels from a Slack integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "slack":
        raise HTTPException(status_code=400, detail="Integration is not a Slack integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/conversations.list",
            params={
                "exclude_archived": str(exclude_archived).lower(),
                "types": "public_channel,private_channel"
            }
        )
        
        # Extract channels from Slack API response
        channels = result.get("channels", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=channels,
            total=len(channels)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Slack channels: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch channels: {str(e)}"
        )

@router.get("/{integration_id}/slack/users")
async def get_slack_users(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get users from a Slack integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "slack":
        raise HTTPException(status_code=400, detail="Integration is not a Slack integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/users.list",
            params={}
        )
        
        # Extract users from Slack API response
        users = result.get("members", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=users,
            total=len(users)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Slack users: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch users: {str(e)}"
        )

@router.get("/{integration_id}/jira/projects")
async def get_jira_projects(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get projects from a Jira integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "jira":
        raise HTTPException(status_code=400, detail="Integration is not a Jira integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/rest/api/3/project",
            params={"expand": "description,lead,url,projectKeys"}
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=len(result) if result else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Jira projects: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch projects: {str(e)}"
        )

@router.get("/{integration_id}/jira/issues")
async def get_jira_issues(
    integration_id: int,
    project_key: Optional[str] = Query(default=None),
    max_results: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get issues from a Jira integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "jira":
        raise HTTPException(status_code=400, detail="Integration is not a Jira integration")
    
    try:
        # Build JQL query
        jql = "ORDER BY updated DESC"
        if project_key:
            jql = f"project = {project_key} " + jql
        
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/rest/api/3/search",
            params={
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,status,issuetype,assignee,reporter,created,updated,priority,project"
            }
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=result.get("total", 0) if result else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Jira issues: {e}")
        return IntegrationDataResponse(
            success=False,
            data={"issues": []},
            message=f"Failed to fetch issues: {str(e)}"
        )

@router.get("/{integration_id}/salesforce/accounts")
async def get_salesforce_accounts(
    integration_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get accounts from a Salesforce integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "salesforce":
        raise HTTPException(status_code=400, detail="Integration is not a Salesforce integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/services/data/v57.0/query/",
            params={
                "q": f"SELECT Id,Name,Type,Industry,Website,Phone,BillingCity,BillingState,BillingCountry,NumberOfEmployees,AnnualRevenue,CreatedDate,LastModifiedDate FROM Account ORDER BY LastModifiedDate DESC LIMIT {limit}"
            }
        )
        
        # Extract records from Salesforce response
        records = result.get("records", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Salesforce accounts: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch accounts: {str(e)}"
        )

@router.get("/{integration_id}/salesforce/opportunities")
async def get_salesforce_opportunities(
    integration_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get opportunities from a Salesforce integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "salesforce":
        raise HTTPException(status_code=400, detail="Integration is not a Salesforce integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/services/data/v57.0/query/",
            params={
                "q": f"SELECT Id,Name,StageName,CloseDate,Amount,Probability,Type,LeadSource,Description,AccountId,Account.Name,CreatedDate,LastModifiedDate FROM Opportunity ORDER BY LastModifiedDate DESC LIMIT {limit}"
            }
        )
        
        # Extract records from Salesforce response
        records = result.get("records", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Salesforce opportunities: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch opportunities: {str(e)}"
        )

@router.get("/{integration_id}/salesforce/leads")
async def get_salesforce_leads(
    integration_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get leads from a Salesforce integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "salesforce":
        raise HTTPException(status_code=400, detail="Integration is not a Salesforce integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/services/data/v57.0/query/",
            params={
                "q": f"SELECT Id,FirstName,LastName,Company,Title,Email,Phone,Status,LeadSource,Industry,Rating,City,State,Country,CreatedDate,LastModifiedDate,ConvertedDate FROM Lead ORDER BY LastModifiedDate DESC LIMIT {limit}"
            }
        )
        
        # Extract records from Salesforce response
        records = result.get("records", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=records,
            total=len(records)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Salesforce leads: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch leads: {str(e)}"
        )

@router.get("/{integration_id}/zendesk/tickets")
async def get_zendesk_tickets(
    integration_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get tickets from a Zendesk integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "zendesk":
        raise HTTPException(status_code=400, detail="Integration is not a Zendesk integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/api/v2/tickets.json",
            params={
                "page": page,
                "per_page": per_page,
                "sort_by": "updated_at",
                "sort_order": "desc"
            }
        )
        
        # Extract tickets from Zendesk response
        tickets = result.get("tickets", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=tickets,
            total=len(tickets),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Zendesk tickets: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch tickets: {str(e)}"
        )

@router.get("/{integration_id}/zendesk/users")
async def get_zendesk_users(
    integration_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get users from a Zendesk integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "zendesk":
        raise HTTPException(status_code=400, detail="Integration is not a Zendesk integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/api/v2/users.json",
            params={
                "page": page,
                "per_page": per_page
            }
        )
        
        # Extract users from Zendesk response
        users = result.get("users", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=users,
            total=len(users),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Zendesk users: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch users: {str(e)}"
        )

@router.get("/{integration_id}/zendesk/organizations")
async def get_zendesk_organizations(
    integration_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get organizations from a Zendesk integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "zendesk":
        raise HTTPException(status_code=400, detail="Integration is not a Zendesk integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/api/v2/organizations.json",
            params={
                "page": page,
                "per_page": per_page
            }
        )
        
        # Extract organizations from Zendesk response
        organizations = result.get("organizations", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=organizations,
            total=len(organizations),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Zendesk organizations: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch organizations: {str(e)}"
        )

@router.get("/{integration_id}/trello/boards")
async def get_trello_boards(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get boards from a Trello integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "trello":
        raise HTTPException(status_code=400, detail="Integration is not a Trello integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/1/members/me/boards",
            params={
                "filter": "open",
                "fields": "name,desc,closed,url,shortUrl,prefs,dateLastActivity,dateLastView"
            }
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=len(result) if result else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Trello boards: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch boards: {str(e)}"
        )

@router.get("/{integration_id}/trello/cards")
async def get_trello_cards(
    integration_id: int,
    board_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get cards from a Trello integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "trello":
        raise HTTPException(status_code=400, detail="Integration is not a Trello integration")
    
    try:
        if board_id:
            # Get cards from a specific board
            endpoint = f"/1/boards/{board_id}/cards"
        else:
            # Get cards from all boards (member cards)
            endpoint = "/1/members/me/cards"
        
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint=endpoint,
            params={
                "fields": "name,desc,closed,idList,idBoard,pos,url,shortUrl,due,dueComplete,dateLastActivity,labels,members"
            }
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=len(result) if result else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Trello cards: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch cards: {str(e)}"
        )

@router.get("/{integration_id}/trello/lists")
async def get_trello_lists(
    integration_id: int,
    board_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get lists from a Trello integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "trello":
        raise HTTPException(status_code=400, detail="Integration is not a Trello integration")
    
    try:
        if board_id:
            # Get lists from a specific board
            endpoint = f"/1/boards/{board_id}/lists"
        else:
            # Get lists from all boards for the member
            endpoint = "/1/members/me/boards/open/lists"
        
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint=endpoint,
            params={
                "fields": "name,closed,pos,idBoard"
            }
        )
        
        return IntegrationDataResponse(
            success=True,
            data=result,
            total=len(result) if result else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Trello lists: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch lists: {str(e)}"
        )

@router.get("/{integration_id}/asana/projects")
async def get_asana_projects(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get projects from an Asana integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "asana":
        raise HTTPException(status_code=400, detail="Integration is not an Asana integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/api/1.0/projects",
            params={
                "archived": "false",
                "opt_fields": "name,notes,archived,current_status,team,owner,created_at,modified_at"
            }
        )
        
        # Extract projects from Asana response
        projects = result.get("data", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=projects,
            total=len(projects)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Asana projects: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch projects: {str(e)}"
        )

@router.get("/{integration_id}/asana/tasks")
async def get_asana_tasks(
    integration_id: int,
    project_gid: Optional[str] = Query(default=None),
    completed_since: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get tasks from an Asana integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "asana":
        raise HTTPException(status_code=400, detail="Integration is not an Asana integration")
    
    try:
        params = {
            "opt_fields": "name,notes,completed,due_on,due_at,projects,assignee,created_at,modified_at,completed_at"
        }
        
        if project_gid:
            params["project"] = project_gid
        if completed_since:
            params["completed_since"] = completed_since
        
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/api/1.0/tasks",
            params=params
        )
        
        # Extract tasks from Asana response
        tasks = result.get("data", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=tasks,
            total=len(tasks)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Asana tasks: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch tasks: {str(e)}"
        )

@router.get("/{integration_id}/asana/teams")
async def get_asana_teams(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get teams from an Asana integration."""
    
    # Verify integration ownership
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.owner_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration.integration_type.value != "asana":
        raise HTTPException(status_code=400, detail="Integration is not an Asana integration")
    
    try:
        # Use integration service to fetch data
        result = await integration_service.fetch_integration_data(
            integration,
            endpoint="/api/1.0/teams",
            params={
                "opt_fields": "name,description,organization"
            }
        )
        
        # Extract teams from Asana response
        teams = result.get("data", []) if result else []
        
        return IntegrationDataResponse(
            success=True,
            data=teams,
            total=len(teams)
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch Asana teams: {e}")
        return IntegrationDataResponse(
            success=False,
            data=[],
            message=f"Failed to fetch teams: {str(e)}"
        )