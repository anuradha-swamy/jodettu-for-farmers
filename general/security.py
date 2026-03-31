import random, hashlib, os
from dotenv import load_dotenv
from twilio.rest import Client
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from general.database import otp_collection, users

load_dotenv()

# Configuration
acc_ssid = os.getenv("ACCOUNT_SSID")
auth_token = os.getenv("AUTH_TOKEN")
from_whatsapp_number = os.getenv("FROM_WHATSAPP_NUMBER")
hash_key = os.getenv("HASH_SECRET_KEY")
jwt_algorithm = os.getenv("JWT_ALGORITHM")
token_expiry_minutes = int(os.getenv("TOKEN_EXPIRY_MINUTES", "60"))

# Security Contexts
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()

# Twilio Client
client = Client(acc_ssid, auth_token)

class Security:
    @staticmethod
    def mask_phone_number(phone: str) -> str:
        if len(phone) < 8:
            return phone
        return f"{phone[:3]}******{phone[-4:]}"

    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
        token = credentials.credentials
        try:
            payload = jwt.decode(token, hash_key, algorithms=[jwt_algorithm])
            username = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid token payload.")
            
            user_id = payload.get("user_id")
            role = payload.get("role")

            # Fallback: If user_id is missing (old token), fetch from DB
            if not user_id:
                user = users.find_one({"user_phone_number": username})
                if user:
                    user_id = user.get("user_id")
                    role = user.get("role", "user")
            
            if not user_id:
                 raise HTTPException(status_code=401, detail="User ID could not be determined from token.")

            return {"username": username, "user_id": user_id, "role": role}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_current_admin_user(current_user: dict = Depends(get_current_user)):
        """
        Dependency to check if the current user has admin privileges.
        """
        phone_number = current_user["username"]
        user = users.find_one({"user_phone_number": phone_number})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
            
        # Case-insensitive check for admin role
        role = user.get("role", "").lower()
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=token_expiry_minutes))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, hash_key, algorithm=jwt_algorithm)

    @staticmethod
    def create_session_token(phone_number: str):
        """
        Creates a short-lived session token for OTP verification flow.
        Valid for 5 minutes.
        """
        expire = datetime.utcnow() + timedelta(minutes=5)
        to_encode = {"sub": phone_number, "type": "session", "exp": expire}
        return jwt.encode(to_encode, hash_key, algorithm=jwt_algorithm)

    @staticmethod
    def decode_session_token(token: str) -> str:
        """
        Decodes the session token and returns the phone number.
        """
        try:
            payload = jwt.decode(token, hash_key, algorithms=[jwt_algorithm])
            if payload.get("type") != "session":
                raise HTTPException(status_code=400, detail="Invalid token type.")
            phone_number = payload.get("sub")
            if not phone_number:
                raise HTTPException(status_code=400, detail="Invalid session token.")
            return phone_number
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid or expired session token.")

    @staticmethod
    def send_otp(phone_number: str) -> int: # No longer async
        """
        Generates an OTP, stores it in MongoDB, and sends it via Twilio.
        """
        otp = str(random.randint(100000, 999999))
        expiry_seconds = 120 # 2 minutes
        expires_at = datetime.utcnow() + timedelta(seconds=expiry_seconds)
        
        try:
            if otp_collection is None:
                 raise RuntimeError("Database not initialized: otp_collection is None")

            # --- FIX: Removed 'await' from synchronous PyMongo call ---
            otp_collection.update_one(
                {"phone_number": phone_number},
                {"$set": {"otp": otp, "expires_at": expires_at}},
                upsert=True
            )
        except Exception as e:
            print(f"🔥 CRITICAL DB ERROR in send_otp: {repr(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Database error while storing OTP: {str(e)}"
            )

        body = f"Your Jodettu verification code is: {otp}"
        
        try:
            message = client.messages.create(
                body=body,
                from_=from_whatsapp_number,
                to=f'whatsapp:{phone_number}'
            )
            print(f"OTP sent to {phone_number}. Message SID: {message.sid}")
            return expiry_seconds
        except Exception as e:
            print(f"Twilio Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Twilio error: {str(e)}")

    @staticmethod
    def verify_otp(phone_number: str, user_otp: str) -> bool: # No longer async
        """
        Verifies the OTP with CRASH-PROOF error handling.
        """
        try:
            if otp_collection is None:
                 raise RuntimeError("Database not initialized: otp_collection is None")

            # --- FIX: Removed 'await' from synchronous PyMongo call ---
            record = otp_collection.find_one({"phone_number": phone_number})
        except Exception as e:
            print(f"🔥 CRITICAL DB ERROR in verify_otp: {repr(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Database error while retrieving OTP: {str(e)}"
            )

        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP not found or already used.")
            
        if datetime.utcnow() > record["expires_at"]:
            try:
                # --- FIX: Removed 'await' from synchronous PyMongo call ---
                otp_collection.delete_one({"phone_number": phone_number})
            except Exception as e:
                print(f"⚠️ Warning: Failed to delete expired OTP: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP expired.")
            
        if record["otp"] == user_otp:
            try:
                # --- FIX: Removed 'await' from synchronous PyMongo call ---
                otp_collection.delete_one({"phone_number": phone_number})
            except Exception as e:
                print(f"⚠️ Warning: Failed to delete used OTP: {e}")
            return True
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP.")
