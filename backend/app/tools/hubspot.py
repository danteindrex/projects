"""
HubSpot API integration tools.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolExecutionResult, ToolExecutionEvent, ToolCategory
from app.tools.registry import register_tool


@register_tool("hubspot", {"category": ToolCategory.SEARCH, "priority": 1})
class HubSpotSearchContactsTool(BaseBusinessTool):
    """Search and retrieve HubSpot contacts."""
    
    @property
    def tool_name(self) -> str:
        return "hubspot_search_contacts"
    
    @property
    def description(self) -> str:
        return "Search HubSpot contacts by name, email, company, or other properties. Returns contact details including email, phone, company, and custom properties."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test HubSpot connection."""
        headers = {
            "Authorization": f"Bearer {self.credentials.credentials['access_token']}",
            "Content-Type": "application/json"
        }
        
        # Test with account info endpoint
        url = "https://api.hubapi.com/account-info/v3/details"
        
        response = await self._make_request("GET", url, headers=headers)
        account_info = response.json()
        
        return {
            "portal_id": account_info.get("portalId"),
            "account_type": account_info.get("accountType"),
            "currency": account_info.get("currency"),
            "time_zone": account_info.get("timeZone")
        }
    
    async def execute(
        self, 
        query: str = "",
        email: Optional[str] = None,
        limit: int = 20,
        properties: Optional[List[str]] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Search HubSpot contacts."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message="Searching HubSpot contacts"
            ))
            
            headers = {
                "Authorization": f"Bearer {self.credentials.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            
            # Default properties to retrieve
            if not properties:
                properties = [
                    "firstname", "lastname", "email", "phone", "company", 
                    "jobtitle", "country", "city", "createdate", "lastmodifieddate"
                ]
            
            # If searching by email, use specific endpoint
            if email:
                url = f"https://api.hubapi.com/crm/v3/objects/contacts/{email}"
                params = {
                    "idProperty": "email",
                    "properties": ",".join(properties)
                }
                
                await self.emit_event(ToolExecutionEvent(
                    type="progress",
                    tool_name=self.tool_name,
                    message=f"Searching for contact by email: {email}"
                ))
                
                response = await self._make_request("GET", url, headers=headers, params=params)
                contact_data = response.json()
                
                contacts = [{
                    "id": contact_data.get("id"),
                    "properties": contact_data.get("properties", {}),
                    "created_at": contact_data.get("createdAt"),
                    "updated_at": contact_data.get("updatedAt")
                }]
                
            else:
                # Use search endpoint
                url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
                
                # Build search filters
                filter_groups = []
                if query:
                    # Search in multiple fields
                    filters = []
                    search_properties = ["firstname", "lastname", "email", "company"]
                    for prop in search_properties:
                        filters.append({
                            "propertyName": prop,
                            "operator": "CONTAINS_TOKEN",
                            "value": query
                        })
                    
                    filter_groups.append({"filters": filters})
                
                search_request = {
                    "filterGroups": filter_groups,
                    "properties": properties,
                    "limit": limit,
                    "after": 0
                }
                
                await self.emit_event(ToolExecutionEvent(
                    type="progress",
                    tool_name=self.tool_name,
                    message="Executing contact search..."
                ))
                
                response = await self._make_request("POST", url, headers=headers, data=search_request)
                result_data = response.json()
                
                contacts = []
                for contact in result_data.get("results", []):
                    contacts.append({
                        "id": contact.get("id"),
                        "properties": contact.get("properties", {}),
                        "created_at": contact.get("createdAt"),
                        "updated_at": contact.get("updatedAt")
                    })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Found {len(contacts)} contacts"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "contacts": contacts,
                    "total": len(contacts),
                    "query": query or email,
                    "properties_retrieved": properties
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": query or email}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Contact search failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": query or email}
            )


@register_tool("hubspot", {"category": ToolCategory.CREATE, "priority": 2})
class HubSpotCreateContactTool(BaseBusinessTool):
    """Create new HubSpot contacts."""
    
    @property
    def tool_name(self) -> str:
        return "hubspot_create_contact"
    
    @property
    def description(self) -> str:
        return "Create a new HubSpot contact. Requires email and optionally firstname, lastname, company, phone, and other properties."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test by getting contact properties."""
        headers = {
            "Authorization": f"Bearer {self.credentials.credentials['access_token']}",
            "Content-Type": "application/json"
        }
        
        url = "https://api.hubapi.com/crm/v3/properties/contacts"
        
        response = await self._make_request("GET", url, headers=headers)
        properties = response.json()
        
        return {
            "available_properties": len(properties.get("results", [])),
            "can_create_contacts": True
        }
    
    async def execute(
        self, 
        email: str,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        jobtitle: Optional[str] = None,
        website: Optional[str] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Create a new HubSpot contact."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Creating HubSpot contact: {email}"
            ))
            
            headers = {
                "Authorization": f"Bearer {self.credentials.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            
            # Build contact properties
            properties = {"email": email}
            
            if firstname:
                properties["firstname"] = firstname
            if lastname:
                properties["lastname"] = lastname
            if company:
                properties["company"] = company
            if phone:
                properties["phone"] = phone
            if jobtitle:
                properties["jobtitle"] = jobtitle
            if website:
                properties["website"] = website
            
            # Add any additional properties from kwargs
            for key, value in kwargs.items():
                if key not in properties and value is not None:
                    properties[key] = str(value)
            
            contact_data = {"properties": properties}
            
            url = "https://api.hubapi.com/crm/v3/objects/contacts"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting contact creation..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=contact_data)
            result_data = response.json()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Created contact with ID: {result_data.get('id')}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "contact_id": result_data.get("id"),
                    "properties": result_data.get("properties", {}),
                    "created_at": result_data.get("createdAt"),
                    "updated_at": result_data.get("updatedAt")
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "email": email}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Contact creation failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "email": email}
            )


@register_tool("hubspot", {"category": ToolCategory.SEARCH, "priority": 3})
class HubSpotSearchDealsTool(BaseBusinessTool):
    """Search and retrieve HubSpot deals."""
    
    @property
    def tool_name(self) -> str:
        return "hubspot_search_deals"
    
    @property
    def description(self) -> str:
        return "Search HubSpot deals by name, stage, amount, or other properties. Returns deal details including amount, stage, close date, and associated contacts."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test connection."""
        return {"status": "connected"}
    
    async def execute(
        self, 
        query: str = "",
        deal_stage: Optional[str] = None,
        limit: int = 20,
        properties: Optional[List[str]] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Search HubSpot deals."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message="Searching HubSpot deals"
            ))
            
            headers = {
                "Authorization": f"Bearer {self.credentials.credentials['access_token']}",
                "Content-Type": "application/json"
            }
            
            # Default properties to retrieve
            if not properties:
                properties = [
                    "dealname", "amount", "dealstage", "closedate", 
                    "pipeline", "dealtype", "createdate", "hs_lastmodifieddate"
                ]
            
            url = "https://api.hubapi.com/crm/v3/objects/deals/search"
            
            # Build search filters
            filter_groups = []
            filters = []
            
            if query:
                filters.append({
                    "propertyName": "dealname",
                    "operator": "CONTAINS_TOKEN",
                    "value": query
                })
            
            if deal_stage:
                filters.append({
                    "propertyName": "dealstage",
                    "operator": "EQ",
                    "value": deal_stage
                })
            
            if filters:
                filter_groups.append({"filters": filters})
            
            search_request = {
                "filterGroups": filter_groups,
                "properties": properties,
                "limit": limit,
                "after": 0
            }
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Executing deal search..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=search_request)
            result_data = response.json()
            
            deals = []
            for deal in result_data.get("results", []):
                deal_info = {
                    "id": deal.get("id"),
                    "properties": deal.get("properties", {}),
                    "created_at": deal.get("createdAt"),
                    "updated_at": deal.get("updatedAt")
                }
                deals.append(deal_info)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Found {len(deals)} deals"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "deals": deals,
                    "total": len(deals),
                    "query": query,
                    "deal_stage": deal_stage,
                    "properties_retrieved": properties
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
                message=f"Deal search failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "search", "query": query}
            )