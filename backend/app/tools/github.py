"""
GitHub API integration tools.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolExecutionResult, ToolExecutionEvent, ToolCategory
from app.tools.registry import register_tool


@register_tool("github", {"category": ToolCategory.SEARCH, "priority": 1})
class GitHubSearchTool(BaseBusinessTool):
    """Search GitHub repositories, issues, and users."""
    
    @property
    def tool_name(self) -> str:
        return "github_search"
    
    @property
    def description(self) -> str:
        return "Search GitHub repositories, issues, pull requests, or users. Supports GitHub's powerful search syntax."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test GitHub connection."""
        headers = {
            "Authorization": f"token {self.credentials.credentials['access_token']}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BusinessPlatform/1.0"
        }
        
        url = "https://api.github.com/user"
        response = await self._make_request("GET", url, headers=headers)
        user_info = response.json()
        
        return {
            "user": user_info.get("login", "Unknown"),
            "name": user_info.get("name", "Unknown"),
            "public_repos": user_info.get("public_repos", 0),
            "followers": user_info.get("followers", 0)
        }
    
    async def execute(
        self, 
        query: str,
        search_type: str = "repositories",
        per_page: int = 20,
        **kwargs
    ) -> ToolExecutionResult:
        """Execute GitHub search."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Searching GitHub {search_type}: {query}"
            ))
            
            headers = {
                "Authorization": f"token {self.credentials.credentials['access_token']}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "BusinessPlatform/1.0"
            }
            
            # Build search URL
            url = f"https://api.github.com/search/{search_type}"
            params = {
                "q": query,
                "per_page": per_page
            }
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Executing GitHub search..."
            ))
            
            response = await self._make_request("GET", url, headers=headers, params=params)
            result_data = response.json()
            
            # Process results based on search type
            items = result_data.get("items", [])
            processed_items = []
            
            for item in items:
                if search_type == "repositories":
                    processed_item = {
                        "name": item.get("name"),
                        "full_name": item.get("full_name"),
                        "description": item.get("description"),
                        "url": item.get("html_url"),
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                        "owner": item.get("owner", {}).get("login")
                    }
                elif search_type == "issues":
                    processed_item = {
                        "title": item.get("title"),
                        "number": item.get("number"),
                        "state": item.get("state"),
                        "url": item.get("html_url"),
                        "repository": item.get("repository_url", "").split("/")[-1] if item.get("repository_url") else None,
                        "user": item.get("user", {}).get("login"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                        "labels": [label.get("name") for label in item.get("labels", [])]
                    }
                elif search_type == "users":
                    processed_item = {
                        "login": item.get("login"),
                        "name": item.get("name"),
                        "url": item.get("html_url"),
                        "avatar_url": item.get("avatar_url"),
                        "type": item.get("type"),
                        "public_repos": item.get("public_repos"),
                        "followers": item.get("followers")
                    }
                else:
                    processed_item = item
                
                processed_items.append(processed_item)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Found {len(processed_items)} {search_type}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "items": processed_items,
                    "total_count": result_data.get("total_count", 0),
                    "query": query,
                    "search_type": search_type
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "search_type": search_type}
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
                metadata={"action": "search", "search_type": search_type}
            )


@register_tool("github", {"category": ToolCategory.CREATE, "priority": 2})
class GitHubCreateIssueTool(BaseBusinessTool):
    """Create issues in GitHub repositories."""
    
    @property
    def tool_name(self) -> str:
        return "github_create_issue"
    
    @property
    def description(self) -> str:
        return "Create a new issue in a GitHub repository. Requires repository owner/name, title, and optionally body, labels, and assignees."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test by getting user repositories."""
        headers = {
            "Authorization": f"token {self.credentials.credentials['access_token']}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BusinessPlatform/1.0"
        }
        
        url = "https://api.github.com/user/repos"
        params = {"per_page": 5}
        
        response = await self._make_request("GET", url, headers=headers, params=params)
        repos = response.json()
        
        return {
            "accessible_repos": [repo.get("full_name") for repo in repos],
            "total_repos": len(repos)
        }
    
    async def execute(
        self, 
        repository: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Create a GitHub issue."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Creating issue in {repository}"
            ))
            
            headers = {
                "Authorization": f"token {self.credentials.credentials['access_token']}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "BusinessPlatform/1.0"
            }
            
            # Build issue data
            issue_data = {
                "title": title,
                "body": body
            }
            
            if labels:
                issue_data["labels"] = labels
            
            if assignees:
                issue_data["assignees"] = assignees
            
            # Create issue
            url = f"https://api.github.com/repos/{repository}/issues"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting issue creation..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=issue_data)
            result_data = response.json()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Created issue #{result_data.get('number')}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "issue_number": result_data.get("number"),
                    "issue_id": result_data.get("id"),
                    "url": result_data.get("html_url"),
                    "title": title,
                    "repository": repository,
                    "state": result_data.get("state")
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "repository": repository}
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
                metadata={"action": "create", "repository": repository}
            )


@register_tool("github", {"category": ToolCategory.READ, "priority": 3})
class GitHubGetRepositoryTool(BaseBusinessTool):
    """Get detailed information about a GitHub repository."""
    
    @property
    def tool_name(self) -> str:
        return "github_get_repository"
    
    @property
    def description(self) -> str:
        return "Get detailed information about a GitHub repository including statistics, languages, branches, and recent commits."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test connection."""
        return {"status": "connected"}
    
    async def execute(
        self, 
        repository: str,
        include_commits: bool = True,
        **kwargs
    ) -> ToolExecutionResult:
        """Get repository information."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Getting repository info for {repository}"
            ))
            
            headers = {
                "Authorization": f"token {self.credentials.credentials['access_token']}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "BusinessPlatform/1.0"
            }
            
            # Get repository info
            repo_url = f"https://api.github.com/repos/{repository}"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Fetching repository details..."
            ))
            
            repo_response = await self._make_request("GET", repo_url, headers=headers)
            repo_data = repo_response.json()
            
            # Get languages
            languages_url = f"https://api.github.com/repos/{repository}/languages"
            languages_response = await self._make_request("GET", languages_url, headers=headers)
            languages_data = languages_response.json()
            
            result = {
                "name": repo_data.get("name"),
                "full_name": repo_data.get("full_name"),
                "description": repo_data.get("description"),
                "url": repo_data.get("html_url"),
                "clone_url": repo_data.get("clone_url"),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "watchers": repo_data.get("watchers_count", 0),
                "size": repo_data.get("size", 0),
                "primary_language": repo_data.get("language"),
                "languages": languages_data,
                "default_branch": repo_data.get("default_branch"),
                "created_at": repo_data.get("created_at"),
                "updated_at": repo_data.get("updated_at"),
                "owner": repo_data.get("owner", {}).get("login"),
                "is_private": repo_data.get("private", False),
                "is_fork": repo_data.get("fork", False)
            }
            
            # Get recent commits if requested
            if include_commits:
                await self.emit_event(ToolExecutionEvent(
                    type="progress",
                    tool_name=self.tool_name,
                    message="Fetching recent commits..."
                ))
                
                commits_url = f"https://api.github.com/repos/{repository}/commits"
                commits_params = {"per_page": 10}
                
                commits_response = await self._make_request("GET", commits_url, headers=headers, params=commits_params)
                commits_data = commits_response.json()
                
                recent_commits = []
                for commit in commits_data:
                    commit_info = {
                        "sha": commit.get("sha"),
                        "message": commit.get("commit", {}).get("message"),
                        "author": commit.get("commit", {}).get("author", {}).get("name"),
                        "date": commit.get("commit", {}).get("author", {}).get("date"),
                        "url": commit.get("html_url")
                    }
                    recent_commits.append(commit_info)
                
                result["recent_commits"] = recent_commits
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message="Retrieved repository information"
            ))
            
            return ToolExecutionResult(
                success=True,
                data=result,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "get_repository", "repository": repository}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Failed to get repository info: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "get_repository", "repository": repository}
            )