#!/usr/bin/env python3
"""
Script to create database indexes for improved query performance
"""
import sqlite3
import sys
import os
from pathlib import Path

def create_indexes():
    """Create database indexes"""
    
    # Get database path
    db_path = Path(__file__).parent / "business_platform.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("Please ensure the database is created first by running the application.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Creating database indexes...")
        
        # Index creation queries
        indexes = [
            # User table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_role_active ON users(role, is_active)",
            
            # Integration table indexes
            "CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_owner_id ON integrations(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_tenant_id ON integrations(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_created_at ON integrations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_health_status ON integrations(health_status)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_owner_status ON integrations(owner_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_integrations_tenant_type ON integrations(tenant_id, integration_type)",
            
            # Chat session indexes
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status)",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant_id ON chat_sessions(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_status ON chat_sessions(user_id, status)",
            
            # Chat message indexes
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_tenant_id ON chat_messages(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at)",
        ]
        
        created_count = 0
        for index_query in indexes:
            try:
                cursor.execute(index_query)
                created_count += 1
                print(f"✓ Created index: {index_query.split()[-1].split('(')[0]}")
            except sqlite3.Error as e:
                print(f"✗ Failed to create index: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\nSuccessfully created {created_count} database indexes!")
        print("Database query performance should now be improved.")
        
        return True
        
    except Exception as e:
        print(f"Error creating indexes: {e}")
        return False

def analyze_database():
    """Analyze database and suggest optimizations"""
    db_path = Path(__file__).parent / "business_platform.db"
    
    if not db_path.exists():
        print("Database not found. Please create the database first.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== Database Analysis ===")
        
        # Get table sizes
        tables = ["users", "integrations", "chat_sessions", "chat_messages"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
            except sqlite3.Error:
                print(f"{table}: Table not found")
        
        # Check existing indexes
        print("\n=== Existing Indexes ===")
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        
        if indexes:
            for index_name, table_name in indexes:
                print(f"✓ {index_name} on {table_name}")
        else:
            print("No custom indexes found")
        
        conn.close()
        
    except Exception as e:
        print(f"Error analyzing database: {e}")

if __name__ == "__main__":
    print("Database Index Creation Script")
    print("==============================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        analyze_database()
    else:
        if create_indexes():
            analyze_database()
        else:
            sys.exit(1)