#!/usr/bin/env python3
"""
Test script for AI/ML services
Run this to verify all AI services are working correctly
"""

import asyncio
import requests
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw
import sys

def create_test_image():
    """Create a simple test image"""
    # Create a simple 224x224 test image
    img = Image.new('RGB', (224, 224), color='blue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 174, 174], fill='red')
    draw.ellipse([75, 75, 149, 149], fill='yellow')
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()

async def test_ai_services(base_url="http://localhost:8000"):
    """Test all AI services"""
    print("🧪 Testing AI/ML Services")
    print("=" * 50)
    
    # Test image
    test_image = create_test_image()
    
    # Test endpoints
    tests = [
        {
            "name": "Object Detection (YOLOv8)",
            "url": f"{base_url}/Jodettu/ai/detect-objects",
            "method": "POST",
            "files": {"image": ("test.jpg", test_image, "image/jpeg")},
            "data": {}
        },
        {
            "name": "Image Classification (ResNet50)",
            "url": f"{base_url}/Jodettu/ai/classify-image", 
            "method": "POST",
            "files": {"image": ("test.jpg", test_image, "image/jpeg")},
            "data": {}
        },
        {
            "name": "Animal Detection",
            "url": f"{base_url}/Jodettu/ai/detect-animals",
            "method": "POST", 
            "files": {"image": ("test.jpg", test_image, "image/jpeg")},
            "data": {}
        },
        {
            "name": "Translation (EN to HI)",
            "url": f"{base_url}/Jodettu/translation/translate",
            "method": "POST",
            "files": {},
            "data": {
                "text": "Hello, how are you?",
                "src_lang": "en",
                "tgt_lang": "hi"
            }
        },
        {
            "name": "Language Detection",
            "url": f"{base_url}/Jodettu/translation/detect-language",
            "method": "POST",
            "files": {},
            "data": {
                "text": "नमस्ते आप कैसे हैं?"
            }
        },
        {
            "name": "Geocoding",
            "url": f"{base_url}/Jodettu/location/geocode",
            "method": "POST",
            "files": {},
            "data": {
                "address": "Delhi, India"
            }
        },
        {
            "name": "Supported Languages",
            "url": f"{base_url}/Jodettu/translation/supported-languages",
            "method": "GET",
            "files": {},
            "data": {}
        }
    ]
    
    # Authentication token (you'll need to get this from your auth endpoint)
    headers = {}
    
    print("⚠️  Note: Make sure you have a valid authentication token")
    print("   You can get one by logging in at /Jodettu/Auth/login")
    print("   Then add the token to the Authorization header")
    print()
    
    results = []
    
    for test in tests:
        print(f"🔍 Testing: {test['name']}")
        try:
            if test['method'] == 'POST':
                if test['files']:
                    response = requests.post(
                        test['url'], 
                        files=test['files'], 
                        data=test['data'],
                        headers=headers,
                        timeout=30
                    )
                else:
                    response = requests.post(
                        test['url'],
                        data=test['data'],
                        headers=headers,
                        timeout=30
                    )
            else:  # GET
                response = requests.get(test['url'], headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success - Status: {response.status_code}")
                
                # Show sample results
                if 'detections' in result:
                    print(f"   Objects detected: {len(result['detections'])}")
                elif 'predictions' in result:
                    print(f"   Top prediction: {result['predictions'][0]['class']}")
                elif 'translated_text' in result:
                    print(f"   Translation: {result['translated_text']}")
                elif 'detected_language' in result:
                    print(f"   Detected: {result['detected_language']}")
                elif 'coordinates' in result:
                    print(f"   Coordinates: {result['coordinates']}")
                
                results.append({"test": test['name'], "status": "success", "result": result})
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                print(f"   Error: {response.text}")
                results.append({"test": test['name'], "status": "failed", "error": response.text})
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Is the server running at {base_url}?")
            results.append({"test": test['name'], "status": "connection_error"})
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({"test": test['name'], "status": "error", "error": str(e)})
        
        print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    total_count = len(results)
    
    print(f"✅ Passed: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All tests passed! AI services are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
        # Show failed tests
        failed_tests = [r for r in results if r['status'] != 'success']
        print("\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test['test']}: {test.get('error', test['status'])}")
    
    return results

def check_server_status(base_url="http://localhost:8000"):
    """Check if the server is running"""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

async def main():
    print("🚀 AI/ML Services Test Suite")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Check if server is running
    print("🔍 Checking server status...")
    if not check_server_status(base_url):
        print(f"❌ Server is not running at {base_url}")
        print("Please start the server first:")
        print("   python main.py")
        return
    
    print("✅ Server is running!")
    print()
    
    # Run tests
    await test_ai_services(base_url)

if __name__ == "__main__":
    asyncio.run(main())
