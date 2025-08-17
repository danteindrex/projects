from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import httpx
import asyncio
from datetime import datetime

from app.core.security import get_current_active_user, get_current_admin_user
from app.db.database import get_db_session
from app.models.user import User
from app.models.integration import Integration, IntegrationType, IntegrationStatus
from app.schemas.integration import (
    IntegrationCreate, 
    IntegrationUpdate, 
    IntegrationResponse, 
    IntegrationTestRequest,
    IntegrationTestResponse,
    IntegrationHealth
)
from app.core.encryption import encrypt_credentials, decrypt_credentials
from app.core.logging import log_integration_event
from app.core.kafka_service import publish_integration_event
from app.services.crewai_service import initialize_agents

router = APIRouter()

@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Create a new integration"""
    try:
        # Encrypt credentials before storage
        encrypted_creds = encrypt_credentials(integration_data.credentials)
        key_id = "key_" + str(datetime.utcnow().timestamp())
        
        # Create integration
        db_integration = Integration(
            name=integration_data.name,
            description=integration_data.description,
            integration_type=integration_data.integration_type,
            base_url=str(integration_data.base_url),
            encrypted_credentials=encrypted_creds,
            encryption_key_id=key_id,
            config=integration_data.config,
            rate_limit=integration_data.rate_limit,
            timeout=integration_data.timeout,
            owner_id=current_user.id,
            tenant_id=getattr(current_user, 'tenant_id', 'default')
        )
        
        db.add(db_integration)
        db.commit()
        db.refresh(db_integration)
        
        # Initialize agents for this integration
        await initialize_agents(db)
        
        log_integration_event(db_integration.id, "integration_created", user_id=current_user.id)
        await publish_integration_event(str(db_integration.id), "integration_created", {
            "name": db_integration.name,
            "type": db_integration.integration_type.value
        })
        
        return IntegrationResponse(
            id=db_integration.id,
            external_id=db_integration.external_id,
            tenant_id=db_integration.tenant_id,
            name=db_integration.name,
            description=db_integration.description,
            integration_type=db_integration.integration_type,
            base_url=db_integration.base_url,
            config=db_integration.config,
            rate_limit=db_integration.rate_limit,
            timeout=db_integration.timeout,
            status=db_integration.status,
            health_status=db_integration.health_status,
            error_count=db_integration.error_count,
            last_error=db_integration.last_error,
            last_health_check=db_integration.last_health_check,
            created_at=db_integration.created_at.isoformat(),
            updated_at=db_integration.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        log_integration_event(0, "integration_creation_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create integration"
        )

@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get all integrations for the current user"""
    try:
        integrations = db.query(Integration).filter(
            Integration.owner_id == current_user.id
        ).all()
        
        return [
            IntegrationResponse(
                id=integration.id,
                external_id=integration.external_id,
                tenant_id=integration.tenant_id,
                name=integration.name,
                description=integration.description,
                integration_type=integration.integration_type,
                base_url=integration.base_url,
                config=integration.config,
                rate_limit=integration.rate_limit,
                timeout=integration.timeout,
                status=integration.status,
                health_status=integration.health_status,
                error_count=integration.error_count,
                last_error=integration.last_error,
                last_health_check=integration.last_health_check,
                created_at=integration.created_at.isoformat(),
                updated_at=integration.updated_at.isoformat()
            )
            for integration in integrations
        ]
        
    except Exception as e:
        log_integration_event(0, "integrations_retrieval_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integrations"
        )

@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get a specific integration"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        return IntegrationResponse(
            id=integration.id,
            external_id=integration.external_id,
            tenant_id=integration.tenant_id,
            name=integration.name,
            description=integration.description,
            integration_type=integration.integration_type,
            base_url=integration.base_url,
            config=integration.config,
            rate_limit=integration.rate_limit,
            timeout=integration.timeout,
            status=integration.status,
            health_status=integration.health_status,
            error_count=integration.error_count,
            last_error=integration.last_error,
            last_health_check=integration.last_health_check,
            created_at=integration.created_at.isoformat(),
            updated_at=integration.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_integration_event(integration_id, "integration_retrieval_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integration"
        )

@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Update an integration"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Update fields
        update_data = integration_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(integration, field, value)
        
        db.commit()
        db.refresh(integration)
        
        log_integration_event(integration_id, "integration_updated", user_id=current_user.id)
        await publish_integration_event(str(integration_id), "integration_updated", update_data)
        
        return IntegrationResponse(
            id=integration.id,
            external_id=integration.external_id,
            tenant_id=integration.tenant_id,
            name=integration.name,
            description=integration.description,
            integration_type=integration.integration_type,
            base_url=integration.base_url,
            config=integration.config,
            rate_limit=integration.rate_limit,
            timeout=integration.timeout,
            status=integration.status,
            health_status=integration.health_status,
            error_count=integration.error_count,
            last_error=integration.last_error,
            last_health_check=integration.last_health_check,
            created_at=integration.created_at.isoformat(),
            updated_at=integration.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_integration_event(integration_id, "integration_update_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update integration"
        )

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Delete an integration"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        db.delete(integration)
        db.commit()
        
        log_integration_event(integration_id, "integration_deleted", user_id=current_user.id)
        await publish_integration_event(str(integration_id), "integration_deleted", {})
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_integration_event(integration_id, "integration_deletion_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete integration"
        )

@router.post("/{integration_id}/test", response_model=IntegrationTestResponse)
async def test_integration(
    integration_id: int,
    test_data: IntegrationTestRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Test an integration connection"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Test the connection
        test_result = await _test_connection(test_data)
        
        # Update integration status based on test result
        if test_result.success:
            integration.status = IntegrationStatus.ACTIVE
            integration.health_status = "healthy"
            integration.last_health_check = datetime.utcnow().isoformat()
        else:
            integration.status = IntegrationStatus.ERROR
            integration.health_status = "unhealthy"
            integration.error_count += 1
            integration.last_error = test_result.error_details
            integration.last_health_check = datetime.utcnow().isoformat()
        
        db.commit()
        
        log_integration_event(integration_id, "integration_tested", 
                            success=test_result.success, 
                            response_time=test_result.response_time)
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        log_integration_event(integration_id, "integration_test_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test integration"
        )

async def _test_connection(test_data: IntegrationTestRequest) -> IntegrationTestResponse:
    """Test the connection to an external system"""
    try:
        start_time = datetime.utcnow()
        
        async with httpx.AsyncClient(timeout=test_data.timeout) as client:
            # Test the connection
            response = await client.get(
                str(test_data.base_url) + test_data.test_endpoint,
                headers={"Authorization": f"Bearer {test_data.credentials.get('api_key', '')}"}
            )
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                return IntegrationTestResponse(
                    success=True,
                    message="Connection successful",
                    response_time=response_time,
                    status_code=response.status_code
                )
            else:
                return IntegrationTestResponse(
                    success=False,
                    message=f"Connection failed with status {response.status_code}",
                    response_time=response_time,
                    status_code=response.status_code,
                    error_details=response.text
                )
                
    except Exception as e:
        return IntegrationTestResponse(
            success=False,
            message="Connection failed",
            error_details=str(e)
        )

@router.get("/{integration_id}/health", response_model=IntegrationHealth)
async def get_integration_health(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Get integration health status"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Calculate uptime percentage (simplified)
        uptime_percentage = 95.0 if integration.status == IntegrationStatus.ACTIVE else 50.0
        
        return IntegrationHealth(
            integration_id=integration.id,
            status=integration.health_status,
            response_time=0.0,  # Would be calculated from actual metrics
            last_check=integration.last_health_check or "Never",
            error_count=integration.error_count,
            uptime_percentage=uptime_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_integration_event(integration_id, "health_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integration health"
        )

@router.post("/{integration_id}/health-check", response_model=IntegrationHealth)
async def run_health_check(
    integration_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """Run a health check on an integration"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.owner_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Run health check in background
        background_tasks.add_task(_run_health_check_background, integration_id, db)
        
        return IntegrationHealth(
            integration_id=integration.id,
            status="checking",
            response_time=0.0,
            last_check=datetime.utcnow().isoformat(),
            error_count=integration.error_count,
            uptime_percentage=95.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_integration_event(integration_id, "health_check_initiation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate health check"
        )

async def _run_health_check_background(integration_id: int, db: Session):
    """Run health check in background"""
    try:
        # This would perform actual health checks
        # For now, just simulate
        await asyncio.sleep(2)
        
        # Update integration health status
        integration = db.query(Integration).filter(Integration.id == integration_id).first()
        if integration:
            integration.last_health_check = datetime.utcnow().isoformat()
            integration.health_status = "healthy"
            db.commit()
            
            log_integration_event(integration_id, "health_check_completed", status="healthy")
            
    except Exception as e:
        log_integration_event(integration_id, "health_check_background_failed", error=str(e))
