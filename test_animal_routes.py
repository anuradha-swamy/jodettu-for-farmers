#!/usr/bin/env python3
"""
Test script to verify the animal routes implementation
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.animal_services import OwnAnimalServices

def test_list_all_animals():
    print("Testing OwnAnimalServices.list_all_animals method...")
    
    # Test 1: Call without user_id (should fail)
    try:
        result = OwnAnimalServices.list_all_animals()
        print("❌ ERROR: list_all_animals() should require user_id parameter")
        return False
    except TypeError as e:
        if "missing 1 required positional argument: 'user_id'" in str(e):
            print("✅ CORRECT: list_all_animals() requires user_id parameter")
        else:
            print(f"❌ UNEXPECTED ERROR: {e}")
            return False
    
    # Test 2: Call with user_id (should work)
    try:
        result = OwnAnimalServices.list_all_animals("TEST_USER_001")
        print("✅ CORRECT: list_all_animals(user_id) works properly")
        print(f"   Returned: {len(result)} animals")
        return True
    except Exception as e:
        print(f"❌ ERROR with user_id: {e}")
        return False

if __name__ == "__main__":
    success = test_list_all_animals()
    if success:
        print("\n🎉 All tests passed! The service method is correctly implemented.")
    else:
        print("\n❌ Tests failed. Check the implementation.")
