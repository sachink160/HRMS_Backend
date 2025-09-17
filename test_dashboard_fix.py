#!/usr/bin/env python3
"""
Quick test to verify the dashboard fix works.
"""

import asyncio
from app.database import get_db
from app.routes.admin import get_dashboard_stats
from app.models import User
from app.auth import get_current_admin_user

async def test_dashboard():
    """Test the dashboard endpoint."""
    try:
        print("Testing dashboard fix...")
        
        # Get a test admin user (assuming one exists)
        async for db in get_db():
            # Get first admin or super admin user
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.role.in_(["admin", "super_admin"])).limit(1)
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("No admin or super admin user found. Please create an admin user first.")
                return
            
            print(f"Using admin user: {admin_user.email}")
            
            # Test the dashboard function
            stats = await get_dashboard_stats(admin_user, db)
            print("Dashboard stats:", stats)
            print("✅ Dashboard fix successful!")
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dashboard())
