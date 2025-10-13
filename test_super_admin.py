#!/usr/bin/env python3
"""
Test script to verify super admin creation and authentication
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User, UserRole
from app.auth import authenticate_user, get_password_hash, verify_password
from app.database import DATABASE_URL

load_dotenv()

async def test_super_admin():
    """Test super admin creation and authentication."""
    print("Testing Super Admin Creation and Authentication")
    print("=" * 50)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        async with AsyncSessionLocal() as session:
            # Test credentials
            test_email = "sachin@gmail.com"
            test_password = "Thunder@123"
            
            print(f"SEARCH: Looking for user: {test_email}")
            
            # Check if user exists
            result = await session.execute(
                select(User).where(User.email == test_email)
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"SUCCESS: User found!")
                print(f"   ID: {user.id}")
                print(f"   Name: {user.name}")
                print(f"   Email: {user.email}")
                print(f"   Role: {user.role}")
                print(f"   Active: {user.is_active}")
                print(f"   Created: {user.created_at}")
                
                # Test authentication
                print(f"\nAUTH: Testing authentication...")
                auth_user = await authenticate_user(session, test_email, test_password)
                
                if auth_user:
                    print(f"SUCCESS: Authentication successful!")
                    print(f"   Authenticated user: {auth_user.name}")
                    print(f"   Role: {auth_user.role}")
                    
                    # Test password verification
                    print(f"\nKEY: Testing password verification...")
                    is_valid = verify_password(test_password, user.hashed_password)
                    print(f"   Password verification: {'SUCCESS: Valid' if is_valid else 'ERROR: Invalid'}")
                    
                    # Test role permissions
                    print(f"\nCROWN: Testing role permissions...")
                    if user.role == UserRole.SUPER_ADMIN:
                        print(f"   SUCCESS: Super admin role confirmed")
                        print(f"   SUCCESS: Full system access granted")
                    else:
                        print(f"   ⚠️  User role is {user.role}, not SUPER_ADMIN")
                        
                else:
                    print(f"ERROR: Authentication failed!")
                    print(f"   Check password or user status")
                    
            else:
                print(f"ERROR: User not found!")
                print(f"   Run create_super_admin.py first")
                
    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_super_admin())
