#!/usr/bin/env python3
"""
Simple test script for AI DevOps Platform
"""

import requests
import json
import sys
from datetime import datetime

def test_api():
    """Test the main API endpoints"""
    base_url = "http://127.0.0.1:8001"
    
    print("🚀 AI DevOps Platform Test Suite")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health check: FAILED (Error: {e})")
        return False
    
    # Test 2: Hello endpoint
    print("\n2. Testing Hello Endpoint...")
    try:
        response = requests.get(f"{base_url}/hello", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "Hello World!":
                print("✅ Hello endpoint: PASSED")
                print(f"   Response: {data}")
            else:
                print(f"❌ Hello endpoint: FAILED (Wrong message: {data})")
                return False
        else:
            print(f"❌ Hello endpoint: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Hello endpoint: FAILED (Error: {e})")
        return False
    
    # Test 3: Root endpoint
    print("\n3. Testing Root Endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "AI DevOps Platform" in data.get("message", ""):
                print("✅ Root endpoint: PASSED")
                print(f"   Available endpoints: {list(data.get('endpoints', {}).keys())}")
            else:
                print(f"❌ Root endpoint: FAILED (Wrong message)")
                return False
        else:
            print(f"❌ Root endpoint: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Root endpoint: FAILED (Error: {e})")
        return False
    
    # Test 4: AI Config endpoint
    print("\n4. Testing AI Config Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/ai/config", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Config endpoint: PASSED")
            print(f"   Supported platforms: {data.get('supported_platforms', [])}")
        else:
            print(f"❌ AI Config endpoint: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ AI Config endpoint: FAILED (Error: {e})")
        return False
    
    # Test 5: Test Reports endpoint
    print("\n5. Testing Reports Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/reports", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Reports endpoint: PASSED")
            print(f"   Total reports: {data.get('total_count', 0)}")
        else:
            print(f"❌ Reports endpoint: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Reports endpoint: FAILED (Error: {e})")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All basic tests PASSED!")
    print(f"✅ Test completed at: {datetime.now().isoformat()}")
    return True

if __name__ == "__main__":
    if test_api():
        sys.exit(0)
    else:
        sys.exit(1)