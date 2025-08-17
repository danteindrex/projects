import uuid
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.logging import log_event

class MultiTenantManager:
    def __init__(self):
        self.tenant_context = {}
    
    def get_current_tenant_id(self, request: Request) -> str:
        """Get current tenant ID from request headers or JWT token"""
        # Check for tenant header first
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # Check for tenant in JWT token (would be implemented in auth middleware)
        # For now, return default tenant
        return "default"
    
    def set_tenant_context(self, tenant_id: str, context: Dict[str, Any]):
        """Set tenant context for current request"""
        self.tenant_context[tenant_id] = context
    
    def get_tenant_context(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant context"""
        return self.tenant_context.get(tenant_id)
    
    def validate_tenant_access(self, user_tenant_id: str, resource_tenant_id: str) -> bool:
        """Validate if user has access to tenant resource"""
        # Admin users can access all tenants
        # Regular users can only access their own tenant
        return user_tenant_id == resource_tenant_id or user_tenant_id == "admin"
    
    def apply_tenant_filter(self, query, tenant_id: str):
        """Apply tenant filter to SQLAlchemy query"""
        if hasattr(query.column_descriptions[0]['type'], '__table__'):
            table = query.column_descriptions[0]['type'].__table__
            if hasattr(table.c, 'tenant_id'):
                return query.filter(table.c.tenant_id == tenant_id)
        return query

class RLSManager:
    def __init__(self):
        self.policies = {}
    
    def create_tenant_policy(self, table_name: str, tenant_id: str):
        """Create RLS policy for a specific tenant"""
        policy_name = f"{table_name}_tenant_{tenant_id}_policy"
        
        policy_sql = f"""
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL
        USING (tenant_id = '{tenant_id}')
        WITH CHECK (tenant_id = '{tenant_id}');
        """
        
        return policy_sql
    
    def enable_rls_on_table(self, table_name: str):
        """Enable RLS on a table"""
        return f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
    
    def create_tenant_isolation_policies(self, db: Session):
        """Create RLS policies for all tables"""
        tables = [
            'users',
            'integrations', 
            'agents',
            'chat_sessions',
            'chat_messages'
        ]
        
        policies = []
        for table in tables:
            # Enable RLS
            policies.append(self.enable_rls_on_table(table))
            
            # Create tenant isolation policy
            policies.append(self.create_tenant_policy(table, 'default'))
        
        return policies
    
    def apply_rls_policies(self, db: Session):
        """Apply RLS policies to database"""
        try:
            policies = self.create_tenant_isolation_policies(db)
            
            for policy in policies:
                db.execute(text(policy))
            
            db.commit()
            log_event("rls_policies_applied", success=True)
            
        except Exception as e:
            db.rollback()
            log_event("rls_policies_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to apply RLS policies"
            )

# Global instances
tenant_manager = MultiTenantManager()
rls_manager = RLSManager()

# Dependency functions
def get_current_tenant(request: Request) -> str:
    """Get current tenant ID"""
    return tenant_manager.get_current_tenant_id(request)

def validate_tenant_resource(user_tenant_id: str, resource_tenant_id: str) -> bool:
    """Validate tenant access"""
    return tenant_manager.validate_tenant_access(user_tenant_id, resource_tenant_id)

def apply_tenant_filter_to_query(query, tenant_id: str):
    """Apply tenant filter to query"""
    return tenant_manager.apply_tenant_filter(query, tenant_id)
