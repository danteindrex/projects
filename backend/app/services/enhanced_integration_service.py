"""
Enhanced Integration Service with Full Kafka Monitoring
Use this as a reference to update your existing integration_service.py
"""

import aiohttp
import time
from typing import Dict, Any, Optional

from app.services.integration_monitor import integration_monitor
from app.models.integration import Integration

class EnhancedIntegrationService:
    """Integration Service with comprehensive monitoring"""
    
    async def monitored_api_call(
        self, 
        integration: Integration,
        endpoint: str, 
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an API call with full monitoring"""
        
        # Use the monitor context manager
        async with integration_monitor.monitor_api_call(
            integration, endpoint, method, params, headers
        ) as response_data:
            
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    
                    # Make the actual API call
                    async with session.request(
                        method=method,
                        url=f"{integration.base_url}{endpoint}",
                        headers=headers,
                        params=params,
                        json=data
                    ) as response:
                        
                        # Capture response metadata
                        response_text = await response.text()
                        response_data.update({
                            "status_code": response.status,
                            "response_size": len(response_text.encode('utf-8')),
                            "content_type": response.headers.get('content-type', '')
                        })
                        
                        # Handle different response types
                        if response.status == 429:  # Rate limit
                            retry_after = response.headers.get('retry-after')
                            await integration_monitor.log_rate_limit_hit(
                                integration, endpoint, 
                                int(retry_after) if retry_after else None
                            )
                            raise Exception(f"Rate limit exceeded: {response_text}")
                        
                        elif response.status == 401:  # Auth failure
                            await integration_monitor.log_authentication_failure(
                                integration, endpoint, "bearer"  # or determine auth type
                            )
                            raise Exception(f"Authentication failed: {response_text}")
                        
                        elif response.status >= 400:
                            raise Exception(f"API error {response.status}: {response_text}")
                        
                        # Parse successful response
                        if response.headers.get('content-type', '').startswith('application/json'):
                            return await response.json()
                        else:
                            return {"text": response_text}
            
            except Exception as e:
                # Exception is automatically logged by the monitor context manager
                raise

# Example usage patterns:
async def example_jira_integration_calls():
    """Example of how to use monitored integration calls"""
    
    # Assume you have a Jira integration
    jira_integration = None  # Get from database
    service = EnhancedIntegrationService()
    
    try:
        # Get user profile - monitored automatically
        user_data = await service.monitored_api_call(
            jira_integration, 
            "/rest/api/3/myself",
            method="GET"
        )
        
        # Get projects - monitored automatically  
        projects = await service.monitored_api_call(
            jira_integration,
            "/rest/api/3/project", 
            method="GET",
            params={"expand": "description,lead,url"}
        )
        
        # Create issue - monitored automatically
        new_issue = await service.monitored_api_call(
            jira_integration,
            "/rest/api/3/issue",
            method="POST", 
            data={
                "fields": {
                    "project": {"key": "TEST"},
                    "summary": "Test issue via API",
                    "issuetype": {"name": "Task"}
                }
            }
        )
        
        # Log successful data sync
        await integration_monitor.log_data_sync_event(
            jira_integration, "pull", len(projects), True
        )
        
    except Exception as e:
        # Log failed data sync
        await integration_monitor.log_data_sync_event(
            jira_integration, "pull", 0, False, str(e)
        )