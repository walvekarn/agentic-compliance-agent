#!/usr/bin/env python3
"""
Test script for chat endpoint
Run this to diagnose chat assistant issues
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/v1/query"

def test_endpoint():
    """Test the query endpoint"""
    print("="*70)
    print("🧪 Testing Chat Endpoint")
    print("="*70)
    
    # Test 1: Check if backend is running
    print("\n1️⃣ Checking if backend is running...")
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            print("   ✅ Backend is running")
            print(f"   Response: {health_response.json()}")
        else:
            print(f"   ❌ Backend returned status {health_response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to backend")
        print("   💡 Start backend with: make start")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Test query endpoint with simple query
    print("\n2️⃣ Testing /api/v1/query endpoint...")
    test_query = {
        "query": "What is GDPR?"
    }
    
    print(f"   Request: {json.dumps(test_query, indent=2)}")
    print("   Sending request...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            json=test_query,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        print(f"   ⏱️  Response time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            print("   ✅ Request successful!")
            result = response.json()
            print(f"   Status: {result.get('status')}")
            print(f"   Model: {result.get('model')}")
            print(f"   Response preview: {result.get('response', '')[:200]}...")
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ⏱️  Request timed out after 30 seconds")
        print("   💡 Possible causes:")
        print("      - OpenAI API is slow")
        print("      - Network issues")
        print("      - Backend is processing but taking too long")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error")
        print("   💡 Backend might have crashed or restarted")
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
    
    # Test 3: Test with context
    print("\n3️⃣ Testing with chat history...")
    test_with_history = {
        "query": "Can you elaborate on the penalties?",
        "chat_history": [
            {"role": "user", "content": "What is GDPR?"},
            {"role": "assistant", "content": "GDPR is the General Data Protection Regulation..."}
        ]
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            json=test_with_history,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        print(f"   ⏱️  Response time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            print("   ✅ Request with history successful!")
            result = response.json()
            print(f"   Response preview: {result.get('response', '')[:200]}...")
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ⏱️  Request timed out after 30 seconds")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
    
    print("\n" + "="*70)
    print("✅ Testing complete!")
    print("="*70)


if __name__ == "__main__":
    test_endpoint()

