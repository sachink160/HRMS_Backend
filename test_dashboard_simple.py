#!/usr/bin/env python3
"""
Simple dashboard test.
"""

import asyncio
import requests
import json

async def test_dashboard_api():
    """Test dashboard API endpoint directly."""
    try:
        print("🧪 Testing Dashboard API...")
        
        # Test the API endpoint directly
        response = requests.get("http://localhost:8000/admin/dashboard")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Dashboard API working!")
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print("❌ Dashboard API failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_dashboard_api())
