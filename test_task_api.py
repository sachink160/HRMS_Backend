#!/usr/bin/env python3
"""
Test script for Task API endpoints
This script demonstrates how to use the Task API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

def get_auth_token():
    """Get authentication token for testing"""
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def test_task_creation(token):
    """Test task creation"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data
    task_data = {
        "name": "Complete project documentation",
        "description": "Write comprehensive documentation for the HRMS project including API documentation and user guides",
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "priority": "high",
        "category": "work"
    }
    
    response = requests.post(f"{BASE_URL}/tasks/", json=task_data, headers=headers)
    
    if response.status_code == 200:
        task = response.json()
        print("✅ Task created successfully:")
        print(f"   ID: {task['id']}")
        print(f"   Name: {task['name']}")
        print(f"   Status: {task['status']}")
        print(f"   Priority: {task['priority']}")
        return task['id']
    else:
        print(f"❌ Task creation failed: {response.text}")
        return None

def test_get_my_tasks(token):
    """Test getting user's tasks"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/tasks/my-tasks", headers=headers)
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"✅ Retrieved {len(tasks)} tasks:")
        for task in tasks:
            print(f"   - {task['name']} ({task['status']})")
        return tasks
    else:
        print(f"❌ Failed to retrieve tasks: {response.text}")
        return []

def test_get_task_summary(token):
    """Test getting task summary"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/tasks/my-tasks/summary", headers=headers)
    
    if response.status_code == 200:
        summary = response.json()
        print("✅ Task summary:")
        print(f"   Total tasks: {summary['total_tasks']}")
        print(f"   Pending: {summary['pending_tasks']}")
        print(f"   In Progress: {summary['in_progress_tasks']}")
        print(f"   Completed: {summary['completed_tasks']}")
        print(f"   Overdue: {summary['overdue_tasks']}")
        return summary
    else:
        print(f"❌ Failed to retrieve task summary: {response.text}")
        return None

def test_update_task(token, task_id):
    """Test updating a task"""
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {
        "status": "in_progress",
        "description": "Updated description - Started working on the documentation"
    }
    
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data, headers=headers)
    
    if response.status_code == 200:
        task = response.json()
        print("✅ Task updated successfully:")
        print(f"   Status: {task['status']}")
        print(f"   Description: {task['description']}")
        return task
    else:
        print(f"❌ Task update failed: {response.text}")
        return None

def test_complete_task(token, task_id):
    """Test completing a task"""
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {
        "status": "completed",
        "description": "Task completed successfully!"
    }
    
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data, headers=headers)
    
    if response.status_code == 200:
        task = response.json()
        print("✅ Task completed successfully:")
        print(f"   Status: {task['status']}")
        print(f"   Completed at: {task['completed_at']}")
        return task
    else:
        print(f"❌ Task completion failed: {response.text}")
        return None

def test_admin_endpoints(token):
    """Test admin endpoints (requires admin user)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test getting all tasks
    response = requests.get(f"{BASE_URL}/tasks/admin/all-tasks", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Admin retrieved {len(result['items'])} tasks from {result['total']} total")
        return result
    elif response.status_code == 403:
        print("⚠️  Admin endpoints require admin privileges (expected for regular user)")
        return None
    else:
        print(f"❌ Admin endpoint failed: {response.text}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting Task API Tests")
    print("=" * 50)
    
    # Get authentication token
    print("1. Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Please check your credentials.")
        return
    
    print("✅ Authentication successful")
    print()
    
    # Test task creation
    print("2. Testing task creation...")
    task_id = test_task_creation(token)
    print()
    
    if task_id:
        # Test getting tasks
        print("3. Testing get my tasks...")
        test_get_my_tasks(token)
        print()
        
        # Test task summary
        print("4. Testing task summary...")
        test_get_task_summary(token)
        print()
        
        # Test updating task
        print("5. Testing task update...")
        test_update_task(token, task_id)
        print()
        
        # Test completing task
        print("6. Testing task completion...")
        test_complete_task(token, task_id)
        print()
        
        # Test admin endpoints
        print("7. Testing admin endpoints...")
        test_admin_endpoints(token)
        print()
    
    print("🎉 Task API tests completed!")

if __name__ == "__main__":
    main()
