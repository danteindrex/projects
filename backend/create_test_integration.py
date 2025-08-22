#!/usr/bin/env python3
"""
Create a test integration with proper credentials for testing
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db_session
from app.models.integration import Integration, IntegrationType, IntegrationStatus, AuthType
from app.models.user import User
from app.core.encryption import encryption_service

async def create_test_integration():
    """Create a test GitHub integration with dummy credentials for testing"""
    print("🔧 Creating Test Integration...")
    
    db = next(get_db_session())
    
    try:
        # Get first user
        user = db.query(User).first()
        if not user:
            print("❌ No users found")
            return False
        
        print(f"👤 Using user: {user.email} (ID: {user.id})")
        
        # Create test credentials (dummy GitHub token for testing)
        test_credentials = {
            "api_token": "ghp_test_token_for_demo_purposes_only_not_real",
            "username": "testuser"
        }
        
        # Encrypt credentials
        encrypted_creds = encryption_service.encrypt_credentials(test_credentials)
        
        # Create integration
        integration = Integration(
            name="Test GitHub Integration",
            description="GitHub integration for testing real tool execution",
            integration_type=IntegrationType.GITHUB,
            base_url="https://api.github.com",
            status=IntegrationStatus.ACTIVE,
            encrypted_credentials=encrypted_creds,
            encryption_key_id="default",
            config=json.dumps({
                "rate_limit": 5000,
                "timeout": 30
            }),
            auth_type=AuthType.API_KEY,
            owner_id=user.id,
            tenant_id="default"
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        print(f"✅ Created integration: {integration.name} (ID: {integration.id})")
        print(f"   Status: {integration.status}")
        print(f"   Type: {integration.integration_type}")
        
        # Test decryption
        decrypted = encryption_service.decrypt_credentials(encrypted_creds)
        print(f"✅ Credentials encryption/decryption working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_test_integration())