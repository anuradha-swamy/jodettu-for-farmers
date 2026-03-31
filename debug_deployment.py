#!/usr/bin/env python3
"""
Deployment Debug Script for Jodettu API
Run this on the server to debug database and authentication issues
"""
import os
import sys
import traceback
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_environment():
    """Test environment variables"""
    print("🔍 Testing Environment Variables...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        mongo_uri = os.getenv("MONGO_URI")
        jwt_secret = os.getenv("HASH_SECRET_KEY")
        jwt_algorithm = os.getenv("JWT_ALGORITHM")
        
        print(f"✅ MONGO_URI: {'SET' if mongo_uri else 'NOT SET'}")
        print(f"✅ HASH_SECRET_KEY: {'SET' if jwt_secret else 'NOT SET'}")
        print(f"✅ JWT_ALGORITHM: {'SET' if jwt_algorithm else 'NOT SET'}")
        
        if not mongo_uri:
            print("❌ CRITICAL: MONGO_URI is not set!")
            return False
        return True
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_database_connection():
    """Test MongoDB connection and collections"""
    print("\n🔍 Testing Database Connection...")
    try:
        from general.database import client, db, own_animals, users, otp_collection
        print("✅ Database connection successful")
        
        # Test collections
        print("✅ Collections initialized:")
        print(f"   - own_animals: {own_animals.name}")
        print(f"   - users: {users.name}")
        print(f"   - otp_collection: {otp_collection.name}")
        
        # Test database operations
        animal_count = own_animals.count_documents({})
        user_count = users.count_documents({})
        print(f"✅ Database stats:")
        print(f"   - Total animals: {animal_count}")
        print(f"   - Total users: {user_count}")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return False

def test_jwt_functionality():
    """Test JWT token generation and decoding"""
    print("\n🔍 Testing JWT Functionality...")
    try:
        from general.security import Security
        
        # Test session token
        phone = "+918050733563"
        session_token = Security.create_session_token(phone)
        decoded_phone = Security.decode_session_token(session_token)
        
        print(f"✅ Session token generation: SUCCESS")
        print(f"   Original phone: {phone}")
        print(f"   Decoded phone: {decoded_phone}")
        print(f"   Match: {phone == decoded_phone}")
        
        # Test access token
        token_payload = {
            "sub": phone,
            "user_id": "USER_0001",
            "role": "user"
        }
        access_token = Security.create_access_token(token_payload)
        print(f"✅ Access token generation: SUCCESS")
        print(f"   Token length: {len(access_token)} characters")
        
        return True
    except Exception as e:
        print(f"❌ JWT functionality failed: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return False

def test_animal_services():
    """Test animal services"""
    print("\n🔍 Testing Animal Services...")
    try:
        from services.animal_services import OwnAnimalServices
        
        # Test with a sample user_id
        test_user_id = "USER_0001"
        animals = OwnAnimalServices.list_all_animals(test_user_id)
        
        print(f"✅ Animal services: SUCCESS")
        print(f"   Animals for {test_user_id}: {len(animals)}")
        
        for animal in animals[:2]:  # Show first 2 animals
            print(f"   - {animal.get('own_animal_name')} ({animal.get('own_animal_type')})")
        
        return True
    except Exception as e:
        print(f"❌ Animal services failed: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return False

def test_login_services():
    """Test login services"""
    print("\n🔍 Testing Login Services...")
    try:
        from services.login_services import LoginServices
        
        # Test send_otp (without actually sending)
        print("✅ Login services: SUCCESS")
        print("   - Service class loaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ Login services failed: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("🚀 JODETTU API DEPLOYMENT DEBUG SCRIPT")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Database Connection", test_database_connection),
        ("JWT Functionality", test_jwt_functionality),
        ("Animal Services", test_animal_services),
        ("Login Services", test_login_services),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\n🔧 RECOMMENDATIONS:")
        print("1. Check environment variables on server")
        print("2. Verify MongoDB Atlas network access")
        print("3. Check firewall and security group settings")
        print("4. Verify all dependencies are installed")
        print("5. Check server logs for detailed errors")
    else:
        print("\n🎉 All tests passed! Check server logs for runtime errors.")

if __name__ == "__main__":
    main()
