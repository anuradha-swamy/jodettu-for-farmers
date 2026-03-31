#!/usr/bin/env python3
"""
Test script to verify image endpoints are working on deployed server
"""

import requests
import json

def test_image_endpoints():
    base_url = "http://202.21.38.161:9090"
    
    print("🔍 Testing Image Endpoints on Deployed Server...")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    # Test 1: Debug endpoint
    print("\n1. Testing Debug Endpoint:")
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/debug/routes-info")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - File: {data.get('file')}")
            print(f"   ✅ Has image endpoints: {data.get('has_image_endpoints')}")
        else:
            print(f"   ❌ FAILED - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 2: Get animal with images (using a sample ID)
    print("\n2. Testing Animal Endpoint (should include images field):")
    test_animal_id = "OWN_01"
    try:
        response = requests.get(f"{base_url}/Jodettu/Animals/animal/{test_animal_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Animal data retrieved")
            if 'images' in data:
                images = data.get('images', [])
                print(f"   ✅ Images field present: {len(images)} images")
                if images:
                    for i, img in enumerate(images[:2]):  # Show first 2
                        print(f"      Image {i+1}: {img.get('filename', 'unnamed')}")
            else:
                print(f"   ❌ Images field MISSING - this is the issue!")
        elif response.status_code == 401:
            print(f"   🔒 Requires authentication (this is expected)")
        elif response.status_code == 404:
            print(f"   ❌ Animal not found (try different ID)")
        else:
            print(f"   ❌ FAILED - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: Test image-specific endpoints
    print("\n3. Testing Image-Specific Endpoints:")
    image_endpoints = [
        f"/Jodettu/Animals/animal/{test_animal_id}/images",
        f"/Jodettu/Animals/animal/{test_animal_id}/edit"
    ]
    
    for endpoint in image_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - Available")
            elif response.status_code == 401:
                print(f"   🔒 {endpoint} - Available (requires auth)")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint} - Not found")
            else:
                print(f"   ⚠️ {endpoint} - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("✅ If debug endpoint works -> New code is deployed")
    print("✅ If image endpoints exist -> Image support is available")
    print("❌ If images field missing -> Service layer issue")
    print("\n🔧 NEXT STEPS:")
    print("1. If endpoints work but images field is missing, check animal_services.py")
    print("2. Test with actual authentication token")
    print("3. Try the new endpoints with proper file uploads")

if __name__ == "__main__":
    test_image_endpoints()
