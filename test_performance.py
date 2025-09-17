#!/usr/bin/env python3
"""
Performance testing script for HRMS database optimizations.
"""

import asyncio
import time
from sqlalchemy import select, func, and_
from app.database import get_db, monitor_query
from app.models import User, Leave, Holiday, UserTracker, LeaveStatus
from app.logger import log_info, log_error

async def test_dashboard_performance():
    """Test dashboard query performance."""
    async for db in get_db():
        try:
            log_info("Testing dashboard performance...")
            
            # Test old way (multiple queries)
            start_time = time.time()
            
            # Simulate old dashboard query pattern
            total_users_result = await db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar()
            
            today = time.strftime('%Y-%m-%d')
            active_users_result = await db.execute(
                select(func.count(UserTracker.user_id.distinct())).where(
                    and_(
                        UserTracker.date == today,
                        UserTracker.check_in.isnot(None)
                    )
                )
            )
            active_users = active_users_result.scalar()
            
            pending_leaves_result = await db.execute(
                select(func.count(Leave.id)).where(Leave.status == LeaveStatus.PENDING)
            )
            pending_leaves = pending_leaves_result.scalar()
            
            upcoming_holidays_result = await db.execute(
                select(func.count(Holiday.id)).where(Holiday.date >= today)
            )
            upcoming_holidays = upcoming_holidays_result.scalar()
            
            old_time = time.time() - start_time
            
            # Test new optimized way
            start_time = time.time()
            
            async with monitor_query("test_dashboard_optimized"):
                result = await db.execute(
                    select(
                        func.count(User.id).label('total_users'),
                        func.count(
                            select(UserTracker.user_id)
                            .where(
                                and_(
                                    func.date(UserTracker.date) == today,
                                    UserTracker.check_in.isnot(None)
                                )
                            ).distinct()
                        ).label('active_users'),
                        func.count(
                            select(Leave.id)
                            .where(Leave.status == LeaveStatus.PENDING)
                        ).label('pending_leaves'),
                        func.count(
                            select(Holiday.id)
                            .where(
                                and_(
                                    func.date(Holiday.date) >= today,
                                    Holiday.is_active == True
                                )
                            )
                        ).label('upcoming_holidays')
                    )
                )
                
                stats = result.first()
            
            new_time = time.time() - start_time
            
            improvement = ((old_time - new_time) / old_time) * 100 if old_time > 0 else 0
            
            log_info(f"Dashboard Performance Test Results:")
            log_info(f"  Old method: {old_time:.3f}s")
            log_info(f"  New method: {new_time:.3f}s")
            log_info(f"  Improvement: {improvement:.1f}%")
            log_info(f"  Speed increase: {old_time/new_time:.1f}x" if new_time > 0 else "  Speed increase: N/A")
            
            return {
                "old_time": old_time,
                "new_time": new_time,
                "improvement": improvement
            }
            
        except Exception as e:
            log_error(f"Dashboard performance test failed: {str(e)}")
            return None

async def test_user_listing_performance():
    """Test user listing query performance."""
    async for db in get_db():
        try:
            log_info("Testing user listing performance...")
            
            # Test with monitoring
            start_time = time.time()
            
            async with monitor_query("test_user_listing"):
                result = await db.execute(
                    select(User)
                    .offset(0)
                    .limit(10)
                    .order_by(User.created_at.desc())
                )
                users = result.scalars().all()
            
            query_time = time.time() - start_time
            
            log_info(f"User listing query time: {query_time:.3f}s")
            log_info(f"Retrieved {len(users)} users")
            
            return query_time
            
        except Exception as e:
            log_error(f"User listing performance test failed: {str(e)}")
            return None

async def test_leave_queries_performance():
    """Test leave-related query performance."""
    async for db in get_db():
        try:
            log_info("Testing leave queries performance...")
            
            # Test my leaves query
            start_time = time.time()
            
            async with monitor_query("test_my_leaves"):
                result = await db.execute(
                    select(Leave)
                    .where(Leave.user_id == 1)  # Assuming user ID 1 exists
                    .offset(0)
                    .limit(10)
                    .order_by(Leave.created_at.desc())
                )
                leaves = result.scalars().all()
            
            query_time = time.time() - start_time
            
            log_info(f"My leaves query time: {query_time:.3f}s")
            log_info(f"Retrieved {len(leaves)} leaves")
            
            return query_time
            
        except Exception as e:
            log_error(f"Leave queries performance test failed: {str(e)}")
            return None

async def run_performance_tests():
    """Run all performance tests."""
    try:
        log_info("HRMS Database Performance Tests")
        log_info("=" * 50)
        
        # Run tests
        dashboard_results = await test_dashboard_performance()
        user_listing_time = await test_user_listing_performance()
        leave_queries_time = await test_leave_queries_performance()
        
        # Summary
        log_info("\nPerformance Test Summary:")
        log_info("=" * 30)
        
        if dashboard_results:
            log_info(f"Dashboard optimization: {dashboard_results['improvement']:.1f}% improvement")
        
        if user_listing_time:
            log_info(f"User listing: {user_listing_time:.3f}s")
        
        if leave_queries_time:
            log_info(f"Leave queries: {leave_queries_time:.3f}s")
        
        log_info("\nPerformance tests completed!")
        
    except Exception as e:
        log_error(f"Performance tests failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
