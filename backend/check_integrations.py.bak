#!/usr/bin/env python3
"""
Simple script to check integrations and create test data
"""
import sqlite3
import json
from datetime import datetime

def check_integrations():
    """Check existing integrations in the database"""
    conn = sqlite3.connect('business_platform.db')
    cursor = conn.cursor()
    
    try:
        # Check if integrations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integrations'")
        if not cursor.fetchone():
            print("❌ Integrations table does not exist")
            return
        
        # Get all integrations
        cursor.execute("SELECT id, name, integration_type, status, created_at FROM integrations")
        integrations = cursor.fetchall()
        
        print(f"📊 Total integrations: {len(integrations)}")
        
        if integrations:
            print("\n🔗 Existing Integrations:")
            for integration in integrations:
                print(f"  - ID: {integration[0]} | {integration[1]} ({integration[2]}) - Status: {integration[3]} | Created: {integration[4]}")
        else:
            print("\n🆕 No integrations found. Creating sample integration...")
            create_sample_integration(cursor)
        
        # Check users table
        cursor.execute("SELECT id, email FROM users LIMIT 5")
        users = cursor.fetchall()
        print(f"\n👥 Users in database: {len(users)}")
        for user in users:
            print(f"  - ID: {user[0]} | {user[1]}")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def create_sample_integration(cursor):
    """Create a sample GitHub integration for testing"""
    try:
        # Sample GitHub integration with dummy credentials
        integration_data = (
            'GitHub Demo',
            'My GitHub Integration for Testing',
            'github',
            'https://api.github.com',
            'configured',  # status
            json.dumps({
                'api_token': 'your_github_token_here',
                'username': 'your_username'
            }),  # credentials (encrypted in real use)
            json.dumps({
                'rate_limit': 5000,
                'timeout': 30
            }),  # config
            'API_KEY',  # auth_type
            1,  # user_id
            'default',  # tenant_id
            datetime.utcnow().isoformat()  # created_at
        )
        
        cursor.execute("""
            INSERT INTO integrations 
            (name, description, integration_type, base_url, status, encrypted_credentials, config, auth_type, user_id, tenant_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, integration_data)
        
        print("✅ Sample GitHub integration created")
        
    except Exception as e:
        print(f"❌ Failed to create sample integration: {e}")

if __name__ == "__main__":
    check_integrations()