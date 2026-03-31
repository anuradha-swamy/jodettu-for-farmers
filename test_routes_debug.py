#!/usr/bin/env python3
"""
Debug script to identify which routes file is being used in deployment
"""

import requests
import json

def test_routes_deployment():
    base_url = "http://202.21.38.161:9090"  # Your deployed URL from screenshot
    
    print("🔍 Testing deployment to identify which routes file is being used...")
    print("=" * 60)
    
    # Test 1: Check debug endpoint
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/debug/routes-info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug endpoint responded:")
            print(f"   File: {data.get('file')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Has image endpoints: {data.get('has_image_endpoints')}")
            print(f"   New endpoints: {data.get('new_endpoints')}")
        else:
            print(f"❌ Debug endpoint failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Could not reach debug endpoint: {e}")
    
    print("\n" + "-" * 40)
    
    # Test 2: Check if image endpoints exist
    test_animal_id = "OWN_01"  # Change this to a valid animal ID
    
    endpoints_to_test = [
        f"/Jodettu/Animals/animal/{test_animal_id}/images",
        f"/Jodettu/Animals/animal/{test_animal_id}/edit",
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {endpoint} - Available")
            elif response.status_code == 401:
                print(f"🔒 {endpoint} - Available (requires auth)")
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not found")
            else:
                print(f"⚠️ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    print("\n" + "-" * 40)
    
    # Test 3: Check regular animal endpoint
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/animal/{test_animal_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Regular animal endpoint responded")
            if 'images' in data:
                print(f"   Images field present: {len(data.get('images', []))} images")
            else:
                print(f"   ❌ Images field MISSING - this is the issue!")
        else:
            print(f"❌ Regular animal endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Regular animal endpoint error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    print("1. If debug endpoint works and shows 'animal_routes_fixed.py' -> Production deployment")
    print("2. If debug endpoint works and shows 'animal_routes.py' -> Regular deployment") 
    print("3. If debug endpoint doesn't work -> Different deployment method")
    print("4. If images field is missing -> Old routes file being used")

if __name__ == "__main__":
    test_routes_deployment()
