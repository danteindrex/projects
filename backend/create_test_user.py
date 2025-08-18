#!/usr/bin/env python3
"""
Simple script to create a test user directly in the database
"""
import sqlite3
import sys
from passlib.context import CryptContext
from datetime import datetime

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    # Connect to the database
    conn = sqlite3.connect('business_platform.db')
    cursor = conn.cursor()
    
    # Hash the password
    hashed_password = pwd_context.hash("demo123")
    
    try:
        # Insert the test user
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, role, is_verified, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'demo',
            'demo@example.com', 
            hashed_password,
            'Demo User',
            'USER',
            True,
            True,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        print("✅ Test user created successfully!")
        print("👤 Username: demo")
        print("📧 Email: demo@example.com") 
        print("🔑 Password: demo123")
        
    except sqlite3.IntegrityError as e:
        print("❌ User already exists or database error:", e)
        
        # Try to update existing user instead
        try:
            cursor.execute("""
                UPDATE users 
                SET hashed_password = ?, full_name = ?
                WHERE username = 'demo' OR email = 'demo@example.com'
            """, (hashed_password, 'Demo User'))
            
            if cursor.rowcount > 0:
                conn.commit()
                print("✅ Updated existing demo user!")
                print("👤 Username: demo")
                print("📧 Email: demo@example.com")
                print("🔑 Password: demo123")
            else:
                print("❌ Could not create or update user")
        except Exception as update_error:
            print("❌ Update failed:", update_error)
            
    except Exception as e:
        print("❌ Error creating user:", e)
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_user()