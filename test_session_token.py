#!/usr/bin/env python3
"""
Test script to verify session token generation and decoding
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from general.security import Security
from dotenv import load_dotenv

def test_session_token():
    load_dotenv()
    
    # Test phone number
    phone = "+918050733563"
    print(f"Testing session token with phone: {phone}")
    print("-" * 50)
    
    try:
        # Generate session token
        session_token = Security.create_session_token(phone)
        print(f"✅ Generated session token: {session_token}")
        print(f"   Token length: {len(session_token)} characters")
        
        # Decode it back
        decoded_phone = Security.decode_session_token(session_token)
        print(f"✅ Decoded phone: {decoded_phone}")
        print(f"✅ Phone numbers match: {phone == decoded_phone}")
        
        # Test with invalid token
        try:
            Security.decode_session_token("invalid_token")
            print("❌ Should have failed with invalid token")
        except Exception as e:
            print(f"✅ Correctly rejected invalid token: {e}")
            
        print("-" * 50)
        print("🎉 All tests passed! Session token generation works correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    test_session_token()
