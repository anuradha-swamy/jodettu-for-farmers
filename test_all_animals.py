#!/usr/bin/env python3
"""
Simple test to isolate the 500 error in all-animals endpoint
"""

import requests
import json

def test_all_animals_endpoint():
    base_url = "http://202.21.38.161:9090"
    
    print("🔍 Testing all-animals endpoint...")
    print("=" * 50)
    
    # Test 1: Try without auth first
    print("\n1. Testing without authentication:")
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/all-animals")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Try with a dummy token (might give different error)
    print("\n2. Testing with dummy authentication:")
    headers = {"Authorization": "Bearer dummy_token"}
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/all-animals", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Try debug endpoint (should work)
    print("\n3. Testing debug endpoint (should work):")
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/debug/routes-info", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   File: {data.get('file')}")
            print(f"   Has image endpoints: {data.get('has_image_endpoints')}")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Try animal-types endpoint (should work)
    print("\n4. Testing animal-types endpoint (should work):")
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/animal-types", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Animal types: {len(data)} types found")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 ANALYSIS:")
    print("1. If debug endpoint works -> New code is deployed")
    print("2. If animal-types works -> Basic endpoints work")
    print("3. If all-animals fails -> Issue with that specific endpoint")
    print("4. Check server logs for detailed error messages")
    print("5. Look for 'DEBUG' messages in server logs")

if __name__ == "__main__":
    test_all_animals_endpoint()
