"""
Jira API integration tools.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolExecutionResult, ToolExecutionEvent, ToolCategory
from app.tools.registry import register_tool


@register_tool("jira", {"category": ToolCategory.SEARCH, "priority": 1})
class JiraSearchTool(BaseBusinessTool):
    """Search for Jira issues using JQL queries."""
    
    @property
    def tool_name(self) -> str:
        return "jira_search"
    
    @property
    def description(self) -> str:
        return "Search for Jira issues using JQL (Jira Query Language) queries. Returns issue details including key, summary, status, assignee, and more."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["domain", "email", "api_token"]  # Basic Auth approach
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test Jira connection."""
        creds = self.credentials.credentials
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Use basic auth with email/token
        import base64
        auth_string = f"{creds['email']}:{creds['api_token']}"
        auth_bytes = auth_string.encode('utf-8')
        headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
        
        url = f"https://{creds['domain']}.atlassian.net/rest/api/3/myself"
        
        response = await self._make_request("GET", url, headers=headers)
        user_info = response.json()
        
        return {
            "user": user_info.get("displayName", "Unknown"),
            "email": user_info.get("emailAddress", "Unknown"),
            "account_id": user_info.get("accountId", "Unknown"),
            "domain": creds['domain']
        }
    
    async def execute(self, query: str = "", max_results: int = 20, **kwargs) -> ToolExecutionResult:
        """Execute Jira search."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Searching Jira issues with query: {query}"
            ))
            
            creds = self.credentials.credentials
            
            # Prepare headers with auth
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            
            import base64
            auth_string = f"{creds['email']}:{creds['api_token']}"
            auth_bytes = auth_string.encode('utf-8')
            headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
            
            # Build search URL
            url = f"https://{creds['domain']}.atlassian.net/rest/api/3/search"
            
            # Default query if none provided
            if not query:
                query = "order by updated DESC"
            
            # Search payload
            payload = {
                "jql": query,
                "maxResults": max_results,
                "fields": [
                    "key", "summary", "status", "assignee", "reporter", 
                    "priority", "created", "updated", "description", "issuetype"
                ],
                "expand": ["names"]
            }
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Executing JQL query..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=payload)
            result_data = response.json()
            
            # Process results
            issues = []
            for issue in result_data.get("issues", []):
                fields = issue.get("fields", {})
                issue_data = {
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                    "reporter": fields.get("reporter", {}).get("displayName"),
                    "priority": fields.get("priority", {}).get("name"),
                    "issue_type": fields.get("issuetype", {}).get("name"),
                    "created": fields.get("created"),
                    "updated": fields.get("updated"),
                    "url": f"https://{creds['domain']}.atlassian.net/browse/{issue.get('key')}"
                }
                issues.append(issue_data)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Found {len(issues)} issues"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "issues": issues,
                    "total": result_data.get("total", 0),
                    "query": query,
                    "max_results": max_results
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": query}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Search failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": query}
            )


@register_tool("jira", {"category": ToolCategory.CREATE, "priority": 2})
class JiraCreateIssueTool(BaseBusinessTool):
    """Create new Jira issues."""
    
    @property
    def tool_name(self) -> str:
        return "jira_create_issue"
    
    @property
    def description(self) -> str:
        return "Create a new Jira issue. Requires project key, issue type, summary, and optionally description, assignee, priority."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["domain", "email", "api_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test by getting projects list."""
        creds = self.credentials.credentials
        
        headers = {
            "Accept": "application/json",
        }
        
        import base64
        auth_string = f"{creds['email']}:{creds['api_token']}"
        auth_bytes = auth_string.encode('utf-8')
        headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
        
        url = f"https://{creds['domain']}.atlassian.net/rest/api/3/project"
        
        response = await self._make_request("GET", url, headers=headers)
        projects = response.json()
        
        return {
            "available_projects": len(projects),
            "sample_projects": [p.get("key") for p in projects[:3]]
        }
    
    async def execute(
        self, 
        project_key: str, 
        issue_type: str, 
        summary: str,
        description: str = "",
        assignee: Optional[str] = None,
        priority: str = "Medium",
        **kwargs
    ) -> ToolExecutionResult:
        """Create a new Jira issue."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Creating Jira issue in project {project_key}"
            ))
            
            creds = self.credentials.credentials
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            
            import base64
            auth_string = f"{creds['email']}:{creds['api_token']}"
            auth_bytes = auth_string.encode('utf-8')
            headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
            
            url = f"https://{creds['domain']}.atlassian.net/rest/api/3/issue"
            
            # Build issue payload
            issue_fields = {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority}
            }
            
            if description:
                issue_fields["description"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                }
            
            if assignee:
                # Try to find user by email or account ID
                issue_fields["assignee"] = {"emailAddress": assignee}
            
            payload = {"fields": issue_fields}
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting issue creation request..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=payload)
            result_data = response.json()
            
            issue_key = result_data.get("key")
            issue_id = result_data.get("id")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Created issue {issue_key}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "issue_key": issue_key,
                    "issue_id": issue_id,
                    "url": f"https://{creds['domain']}.atlassian.net/browse/{issue_key}",
                    "project": project_key,
                    "summary": summary,
                    "issue_type": issue_type
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "project": project_key}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Issue creation failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "project": project_key}
            )


@register_tool("jira", {"category": ToolCategory.UPDATE, "priority": 3})
class JiraUpdateIssueTool(BaseBusinessTool):
    """Update existing Jira issues."""
    
    @property
    def tool_name(self) -> str:
        return "jira_update_issue"
    
    @property
    def description(self) -> str:
        return "Update an existing Jira issue. Can modify status, assignee, priority, summary, description, and other fields."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["domain", "email", "api_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test by getting issue types."""
        creds = self.credentials.credentials
        
        headers = {
            "Accept": "application/json",
        }
        
        import base64
        auth_string = f"{creds['email']}:{creds['api_token']}"
        auth_bytes = auth_string.encode('utf-8')
        headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
        
        url = f"https://{creds['domain']}.atlassian.net/rest/api/3/issuetype"
        
        response = await self._make_request("GET", url, headers=headers)
        issue_types = response.json()
        
        return {
            "available_issue_types": [it.get("name") for it in issue_types[:5]]
        }
    
    async def execute(
        self, 
        issue_key: str,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Update a Jira issue."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Updating Jira issue {issue_key}"
            ))
            
            creds = self.credentials.credentials
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            
            import base64
            auth_string = f"{creds['email']}:{creds['api_token']}"
            auth_bytes = auth_string.encode('utf-8')
            headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"
            
            # Build update fields
            update_fields = {}
            
            if summary:
                update_fields["summary"] = summary
            
            if priority:
                update_fields["priority"] = {"name": priority}
                
            if assignee:
                update_fields["assignee"] = {"emailAddress": assignee}
            
            if description:
                update_fields["description"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                }
            
            # Handle status transition separately
            if status:
                # First get available transitions
                transitions_url = f"https://{creds['domain']}.atlassian.net/rest/api/3/issue/{issue_key}/transitions"
                transitions_response = await self._make_request("GET", transitions_url, headers=headers)
                transitions = transitions_response.json().get("transitions", [])
                
                # Find transition that matches status
                target_transition = None
                for transition in transitions:
                    if transition.get("to", {}).get("name", "").lower() == status.lower():
                        target_transition = transition
                        break
                
                if target_transition:
                    # Perform status transition
                    transition_payload = {
                        "transition": {"id": target_transition["id"]}
                    }
                    
                    await self._make_request(
                        "POST", 
                        transitions_url, 
                        headers=headers, 
                        data=transition_payload
                    )
                    
                    await self.emit_event(ToolExecutionEvent(
                        type="progress",
                        tool_name=self.tool_name,
                        message=f"Transitioned to status: {status}"
                    ))
            
            # Update other fields if any
            if update_fields:
                update_url = f"https://{creds['domain']}.atlassian.net/rest/api/3/issue/{issue_key}"
                update_payload = {"fields": update_fields}
                
                await self._make_request("PUT", update_url, headers=headers, data=update_payload)
                
                await self.emit_event(ToolExecutionEvent(
                    type="progress",
                    tool_name=self.tool_name,
                    message="Updated issue fields"
                ))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Successfully updated issue {issue_key}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "issue_key": issue_key,
                    "updated_fields": list(update_fields.keys()),
                    "status_updated": status is not None,
                    "url": f"https://{creds['domain']}.atlassian.net/browse/{issue_key}"
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "update", "issue_key": issue_key}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Update failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "update", "issue_key": issue_key}
            )