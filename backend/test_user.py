#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == 'test@example.com').first()
        if user:
            print(f'User exists: {user.email}, ID: {user.id}')
            return user.id
        else:
            print('Creating test user...')
            # Create test user
            hashed_password = get_password_hash('testpassword123')
            new_user = User(
                email='test@example.com',
                username='testuser',
                hashed_password=hashed_password,
                full_name='Test User',
                role=UserRole.USER
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f'Created user: {new_user.email}, ID: {new_user.id}')
            return new_user.id
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()