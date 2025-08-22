"""
Zendesk API integration tools.
"""
from typing import Dict, Any, List, Optional
import json
import base64
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolExecutionResult, ToolExecutionEvent, ToolCategory
from app.tools.registry import register_tool


@register_tool("zendesk", {"category": ToolCategory.SEARCH, "priority": 1})
class ZendeskSearchTicketsTool(BaseBusinessTool):
    """Search and retrieve Zendesk tickets."""
    
    @property
    def tool_name(self) -> str:
        return "zendesk_search_tickets"
    
    @property
    def description(self) -> str:
        return "Search Zendesk tickets by status, priority, requester, or custom queries. Returns ticket details including ID, subject, status, priority, and more."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["subdomain", "email", "api_token"]
    
    async def _get_auth_header(self) -> str:
        """Get basic auth header for Zendesk API."""
        creds = self.credentials.credentials
        auth_string = f"{creds['email']}/token:{creds['api_token']}"
        auth_bytes = auth_string.encode('utf-8')
        return f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test Zendesk connection."""
        creds = self.credentials.credentials
        
        headers = {
            "Authorization": await self._get_auth_header(),
            "Content-Type": "application/json"
        }
        
        url = f"https://{creds['subdomain']}.zendesk.com/api/v2/account/settings.json"
        
        response = await self._make_request("GET", url, headers=headers)
        settings = response.json()
        
        return {
            "account": settings.get("settings", {}).get("branding", {}).get("title", "Unknown"),
            "subdomain": creds['subdomain'],
            "url": f"https://{creds['subdomain']}.zendesk.com"
        }
    
    async def execute(
        self, 
        query: str = "",
        status: Optional[str] = None,
        priority: Optional[str] = None,
        per_page: int = 25,
        **kwargs
    ) -> ToolExecutionResult:
        """Search Zendesk tickets."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message="Searching Zendesk tickets"
            ))
            
            creds = self.credentials.credentials
            
            headers = {
                "Authorization": await self._get_auth_header(),
                "Content-Type": "application/json"
            }
            
            # Build search query
            search_query_parts = []
            
            if query:
                search_query_parts.append(query)
            
            if status:
                search_query_parts.append(f"status:{status}")
            
            if priority:
                search_query_parts.append(f"priority:{priority}")
            
            search_query = " ".join(search_query_parts) if search_query_parts else "type:ticket"
            
            # Use search API
            url = f"https://{creds['subdomain']}.zendesk.com/api/v2/search.json"
            params = {
                "query": search_query,
                "per_page": per_page
            }
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Executing ticket search..."
            ))
            
            response = await self._make_request("GET", url, headers=headers, params=params)
            result_data = response.json()
            
            # Process tickets
            tickets = []
            for result in result_data.get("results", []):
                if result.get("result_type") == "ticket":
                    ticket = {
                        "id": result.get("id"),
                        "subject": result.get("subject"),
                        "description": result.get("description"),
                        "status": result.get("status"),
                        "priority": result.get("priority"),
                        "type": result.get("type"),
                        "requester_id": result.get("requester_id"),
                        "assignee_id": result.get("assignee_id"),
                        "created_at": result.get("created_at"),
                        "updated_at": result.get("updated_at"),
                        "url": result.get("url"),
                        "tags": result.get("tags", [])
                    }
                    tickets.append(ticket)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Found {len(tickets)} tickets"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "tickets": tickets,
                    "total_count": result_data.get("count", 0),
                    "query": search_query
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": search_query}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Ticket search failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": query}
            )


@register_tool("zendesk", {"category": ToolCategory.CREATE, "priority": 2})
class ZendeskCreateTicketTool(BaseBusinessTool):
    """Create new Zendesk tickets."""
    
    @property
    def tool_name(self) -> str:
        return "zendesk_create_ticket"
    
    @property
    def description(self) -> str:
        return "Create a new Zendesk ticket. Requires subject and description, optionally priority, type, and requester information."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["subdomain", "email", "api_token"]
    
    async def _get_auth_header(self) -> str:
        """Get basic auth header."""
        creds = self.credentials.credentials
        auth_string = f"{creds['email']}/token:{creds['api_token']}"
        auth_bytes = auth_string.encode('utf-8')
        return f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test by getting ticket fields."""
        creds = self.credentials.credentials
        
        headers = {
            "Authorization": await self._get_auth_header(),
            "Content-Type": "application/json"
        }
        
        url = f"https://{creds['subdomain']}.zendesk.com/api/v2/ticket_fields.json"
        
        response = await self._make_request("GET", url, headers=headers)
        fields = response.json()
        
        return {
            "available_fields": len(fields.get("ticket_fields", [])),
            "can_create_tickets": True
        }
    
    async def execute(
        self, 
        subject: str,
        description: str,
        priority: str = "normal",
        ticket_type: str = "question",
        requester_email: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Create a new Zendesk ticket."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message="Creating Zendesk ticket"
            ))
            
            creds = self.credentials.credentials
            
            headers = {
                "Authorization": await self._get_auth_header(),
                "Content-Type": "application/json"
            }
            
            # Build ticket data
            ticket_data = {
                "subject": subject,
                "comment": {
                    "body": description
                },
                "priority": priority,
                "type": ticket_type
            }
            
            if requester_email:
                ticket_data["requester"] = {"email": requester_email}
            
            if tags:
                ticket_data["tags"] = tags
            
            payload = {"ticket": ticket_data}
            
            url = f"https://{creds['subdomain']}.zendesk.com/api/v2/tickets.json"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting ticket creation..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=payload)
            result_data = response.json()
            
            ticket = result_data.get("ticket", {})
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Created ticket #{ticket.get('id')}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "ticket_id": ticket.get("id"),
                    "subject": ticket.get("subject"),
                    "status": ticket.get("status"),
                    "priority": ticket.get("priority"),
                    "type": ticket.get("type"),
                    "url": ticket.get("url"),
                    "created_at": ticket.get("created_at")
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "subject": subject}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Ticket creation failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "subject": subject}
            )


@register_tool("zendesk", {"category": ToolCategory.UPDATE, "priority": 3})
class ZendeskUpdateTicketTool(BaseBusinessTool):
    """Update existing Zendesk tickets."""
    
    @property
    def tool_name(self) -> str:
        return "zendesk_update_ticket"
    
    @property
    def description(self) -> str:
        return "Update an existing Zendesk ticket. Can modify status, priority, assignee, add comments, and update other fields."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["subdomain", "email", "api_token"]
    
    async def _get_auth_header(self) -> str:
        """Get basic auth header."""
        creds = self.credentials.credentials
        auth_string = f"{creds['email']}/token:{creds['api_token']}"
        auth_bytes = auth_string.encode('utf-8')
        return f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test connection."""
        return {"status": "connected"}
    
    async def execute(
        self, 
        ticket_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_email: Optional[str] = None,
        comment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Update a Zendesk ticket."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Updating Zendesk ticket #{ticket_id}"
            ))
            
            creds = self.credentials.credentials
            
            headers = {
                "Authorization": await self._get_auth_header(),
                "Content-Type": "application/json"
            }
            
            # Build update data
            ticket_updates = {}
            
            if status:
                ticket_updates["status"] = status
            
            if priority:
                ticket_updates["priority"] = priority
            
            if assignee_email:
                ticket_updates["assignee"] = {"email": assignee_email}
            
            if tags:
                ticket_updates["tags"] = tags
            
            if comment:
                ticket_updates["comment"] = {
                    "body": comment,
                    "public": True
                }
            
            payload = {"ticket": ticket_updates}
            
            url = f"https://{creds['subdomain']}.zendesk.com/api/v2/tickets/{ticket_id}.json"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting ticket update..."
            ))
            
            response = await self._make_request("PUT", url, headers=headers, data=payload)
            result_data = response.json()
            
            ticket = result_data.get("ticket", {})
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Successfully updated ticket #{ticket_id}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "ticket_id": ticket.get("id"),
                    "status": ticket.get("status"),
                    "priority": ticket.get("priority"),
                    "updated_at": ticket.get("updated_at"),
                    "updated_fields": list(ticket_updates.keys())
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "update", "ticket_id": ticket_id}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Ticket update failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "update", "ticket_id": ticket_id}
            )