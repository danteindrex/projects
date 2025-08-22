"""
Salesforce API integration tools.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolExecutionResult, ToolExecutionEvent, ToolCategory
from app.tools.registry import register_tool


@register_tool("salesforce", {"category": ToolCategory.SEARCH, "priority": 1})
class SalesforceQueryTool(BaseBusinessTool):
    """Query Salesforce records using SOQL."""
    
    @property
    def tool_name(self) -> str:
        return "salesforce_query"
    
    @property
    def description(self) -> str:
        return "Query Salesforce records using SOQL (Salesforce Object Query Language). Can search Accounts, Contacts, Opportunities, Leads, and other objects."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["username", "password", "security_token", "client_id", "client_secret", "sandbox"]
    
    async def _get_access_token(self) -> str:
        """Get Salesforce access token using OAuth Username-Password flow."""
        creds = self.credentials.credentials
        
        # Determine login URL
        login_url = "https://test.salesforce.com" if creds.get("sandbox", False) else "https://login.salesforce.com"
        token_url = f"{login_url}/services/oauth2/token"
        
        # Prepare OAuth request
        data = {
            "grant_type": "password",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "username": creds["username"],
            "password": f"{creds['password']}{creds['security_token']}"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = await self._make_request("POST", token_url, headers=headers, data=data)
        token_data = response.json()
        
        return token_data["access_token"], token_data["instance_url"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test Salesforce connection."""
        access_token, instance_url = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get organization info
        url = f"{instance_url}/services/data/v58.0/sobjects/Organization/describe"
        response = await self._make_request("GET", url, headers=headers)
        org_info = response.json()
        
        return {
            "organization": org_info.get("label", "Unknown"),
            "instance_url": instance_url,
            "api_version": "58.0",
            "sandbox": self.credentials.credentials.get("sandbox", False)
        }
    
    async def execute(
        self, 
        query: str = "",
        object_type: str = "Account",
        limit: int = 20,
        **kwargs
    ) -> ToolExecutionResult:
        """Execute SOQL query."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Querying Salesforce {object_type} records"
            ))
            
            access_token, instance_url = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Build SOQL query if not provided
            if not query:
                if object_type.lower() == "account":
                    query = f"SELECT Id, Name, Type, Industry, Phone, Website FROM Account LIMIT {limit}"
                elif object_type.lower() == "contact":
                    query = f"SELECT Id, FirstName, LastName, Email, Phone, Account.Name FROM Contact LIMIT {limit}"
                elif object_type.lower() == "opportunity":
                    query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity LIMIT {limit}"
                elif object_type.lower() == "lead":
                    query = f"SELECT Id, FirstName, LastName, Email, Company, Status FROM Lead LIMIT {limit}"
                else:
                    query = f"SELECT Id, Name FROM {object_type} LIMIT {limit}"
            
            # Execute query
            query_url = f"{instance_url}/services/data/v58.0/query"
            params = {"q": query}
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Executing SOQL query..."
            ))
            
            response = await self._make_request("GET", query_url, headers=headers, params=params)
            result_data = response.json()
            
            records = result_data.get("records", [])
            
            # Process records to remove metadata
            processed_records = []
            for record in records:
                clean_record = {k: v for k, v in record.items() if not k.startswith("attributes")}
                processed_records.append(clean_record)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Found {len(processed_records)} records"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "records": processed_records,
                    "total_size": result_data.get("totalSize", 0),
                    "query": query,
                    "object_type": object_type
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "query", "object_type": object_type}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Query failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "query", "object_type": object_type}
            )


@register_tool("salesforce", {"category": ToolCategory.CREATE, "priority": 2})
class SalesforceCreateRecordTool(BaseBusinessTool):
    """Create new Salesforce records."""
    
    @property
    def tool_name(self) -> str:
        return "salesforce_create_record"
    
    @property
    def description(self) -> str:
        return "Create new Salesforce records (Accounts, Contacts, Leads, Opportunities, etc.). Requires object type and field values."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["username", "password", "security_token", "client_id", "client_secret", "sandbox"]
    
    async def _get_access_token(self) -> str:
        """Get Salesforce access token."""
        creds = self.credentials.credentials
        
        login_url = "https://test.salesforce.com" if creds.get("sandbox", False) else "https://login.salesforce.com"
        token_url = f"{login_url}/services/oauth2/token"
        
        data = {
            "grant_type": "password",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "username": creds["username"],
            "password": f"{creds['password']}{creds['security_token']}"
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = await self._make_request("POST", token_url, headers=headers, data=data)
        token_data = response.json()
        
        return token_data["access_token"], token_data["instance_url"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test by getting available objects."""
        access_token, instance_url = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{instance_url}/services/data/v58.0/sobjects"
        response = await self._make_request("GET", url, headers=headers)
        sobjects = response.json()
        
        createable_objects = [
            obj["name"] for obj in sobjects["sobjects"] 
            if obj.get("createable", False)
        ][:10]
        
        return {
            "createable_objects": createable_objects,
            "total_objects": len(sobjects["sobjects"])
        }
    
    async def execute(
        self, 
        object_type: str,
        fields: Dict[str, Any],
        **kwargs
    ) -> ToolExecutionResult:
        """Create a new Salesforce record."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Creating {object_type} record"
            ))
            
            access_token, instance_url = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create record
            create_url = f"{instance_url}/services/data/v58.0/sobjects/{object_type}"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting record creation..."
            ))
            
            response = await self._make_request("POST", create_url, headers=headers, data=fields)
            result_data = response.json()
            
            record_id = result_data.get("id")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Created {object_type} with ID: {record_id}"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "id": record_id,
                    "object_type": object_type,
                    "fields": fields,
                    "success": result_data.get("success", True)
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "object_type": object_type}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Record creation failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "create", "object_type": object_type}
            )


@register_tool("salesforce", {"category": ToolCategory.UPDATE, "priority": 3})
class SalesforceUpdateRecordTool(BaseBusinessTool):
    """Update existing Salesforce records."""
    
    @property
    def tool_name(self) -> str:
        return "salesforce_update_record"
    
    @property
    def description(self) -> str:
        return "Update existing Salesforce records. Requires record ID, object type, and fields to update."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["username", "password", "security_token", "client_id", "client_secret", "sandbox"]
    
    async def _get_access_token(self) -> str:
        """Get Salesforce access token."""
        creds = self.credentials.credentials
        
        login_url = "https://test.salesforce.com" if creds.get("sandbox", False) else "https://login.salesforce.com"
        token_url = f"{login_url}/services/oauth2/token"
        
        data = {
            "grant_type": "password",
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "username": creds["username"],
            "password": f"{creds['password']}{creds['security_token']}"
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = await self._make_request("POST", token_url, headers=headers, data=data)
        token_data = response.json()
        
        return token_data["access_token"], token_data["instance_url"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test connection."""
        access_token, instance_url = await self._get_access_token()
        return {"status": "connected", "instance_url": instance_url}
    
    async def execute(
        self, 
        record_id: str,
        object_type: str,
        fields: Dict[str, Any],
        **kwargs
    ) -> ToolExecutionResult:
        """Update a Salesforce record."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Updating {object_type} record {record_id}"
            ))
            
            access_token, instance_url = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Update record
            update_url = f"{instance_url}/services/data/v58.0/sobjects/{object_type}/{record_id}"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Submitting record update..."
            ))
            
            response = await self._make_request("PATCH", update_url, headers=headers, data=fields)
            
            # 204 No Content indicates successful update
            success = response.status_code == 204
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Successfully updated {object_type} record"
            ))
            
            return ToolExecutionResult(
                success=success,
                data={
                    "id": record_id,
                    "object_type": object_type,
                    "updated_fields": list(fields.keys()),
                    "fields": fields
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "update", "object_type": object_type}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Record update failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "update", "object_type": object_type}
            )