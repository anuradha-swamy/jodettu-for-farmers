#!/usr/bin/env python3
"""
Test script to verify the animal routes fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.animal_services import OwnAnimalServices

async def test_list_all_animals():
    """Test the list_all_animals method with user_id"""
    try:
        # Test with a sample user_id
        test_user_id = "USER_0001"
        result = await OwnAnimalServices.list_all_animals(test_user_id)
        print(f"✅ SUCCESS: list_all_animals({test_user_id}) returned {len(result)} animals")
        return True
    except Exception as e:
        print(f"❌ FAILED: list_all_animals({test_user_id}) error: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    print("🧪 Testing animal services fix...")
    success = asyncio.run(test_list_all_animals())
    if success:
        print("🎉 Fix verified! The deployment should work now.")
    else:
        print("❌ Fix failed. Check the error above.")
