#!/usr/bin/env python3
"""
Debug script to check dashboard issues.
"""

import asyncio
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models import User, Leave, Holiday, UserTracker, LeaveStatus, UserRole

async def debug_dashboard():
    """Debug dashboard components."""
    try:
        print("🔍 Debugging Dashboard Components...")
        print("=" * 50)
        
        async for db in get_db():
            # Check if tables exist and have data
            print("\n1. Checking Users table...")
            users_result = await db.execute(select(func.count(User.id)))
            users_count = users_result.scalar()
            print(f"   Total users: {users_count}")
            
            # Check admin users
            admin_result = await db.execute(
                select(User).where(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
            )
            admin_users = admin_result.scalars().all()
            print(f"   Admin/Super Admin users: {len(admin_users)}")
            for user in admin_users:
                print(f"     - {user.email} ({user.role})")
            
            print("\n2. Checking Leaves table...")
            leaves_result = await db.execute(select(func.count(Leave.id)))
            leaves_count = leaves_result.scalar()
            print(f"   Total leaves: {leaves_count}")
            
            pending_leaves_result = await db.execute(
                select(func.count(Leave.id)).where(Leave.status == LeaveStatus.PENDING)
            )
            pending_count = pending_leaves_result.scalar()
            print(f"   Pending leaves: {pending_count}")
            
            print("\n3. Checking Holidays table...")
            holidays_result = await db.execute(select(func.count(Holiday.id)))
            holidays_count = holidays_result.scalar()
            print(f"   Total holidays: {holidays_count}")
            
            print("\n4. Checking UserTracker table...")
            try:
                trackers_result = await db.execute(select(func.count(UserTracker.id)))
                trackers_count = trackers_result.scalar()
                print(f"   Total tracker records: {trackers_count}")
                
                # Check if there are any records with check_in
                checkin_result = await db.execute(
                    select(func.count(UserTracker.id)).where(UserTracker.check_in.isnot(None))
                )
                checkin_count = checkin_result.scalar()
                print(f"   Records with check_in: {checkin_count}")
                
            except Exception as e:
                print(f"   ❌ Error checking UserTracker: {str(e)}")
                print("   This might be the issue - UserTracker table might not exist or have issues")
            
            print("\n5. Testing date functions...")
            from datetime import datetime
            today = datetime.now().date()
            print(f"   Today's date: {today}")
            
            # Test the date function
            try:
                test_result = await db.execute(
                    select(func.date(UserTracker.date)).limit(1)
                )
                test_date = test_result.scalar()
                print(f"   Sample UserTracker date: {test_date}")
            except Exception as e:
                print(f"   ❌ Error testing date function: {str(e)}")
            
            print("\n✅ Debug complete!")
            
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_dashboard())
