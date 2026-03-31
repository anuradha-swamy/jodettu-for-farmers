import random
import redis
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from twilio.rest import Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class OTPService:
    def __init__(self):
        self.twilio_client = Client(settings.ACCOUNT_SSID, settings.AUTH_TOKEN)
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST if hasattr(settings, 'REDIS_HOST') else 'localhost',
            port=settings.REDIS_PORT if hasattr(settings, 'REDIS_PORT') else 6379,
            db=0,
            decode_responses=True
        )
        self.otp_expiry_minutes = settings.OTP_EXPIRY_MINUTES if hasattr(settings, 'OTP_EXPIRY_MINUTES') else 5
        self.max_otp_attempts = settings.MAX_OTP_ATTEMPTS if hasattr(settings, 'MAX_OTP_ATTEMPTS') else 3

    def mask_phone_number(self, phone_number: str) -> str:
        """Mask phone number for security"""
        if len(phone_number) <= 4:
            return phone_number
        return phone_number[:2] + "*" * (len(phone_number) - 4) + phone_number[-2:]

    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    def get_redis_key(self, phone_number: str, suffix: str = "") -> str:
        """Generate Redis key for OTP storage"""
        return f"otp:{phone_number}{suffix}"

    async def send_otp(self, phone_number: str) -> Dict[str, Any]:
        """Send OTP via Twilio and store in Redis"""
        try:
            # Check rate limiting
            rate_limit_key = self.get_redis_key(phone_number, ":rate_limit")
            current_attempts = self.redis_client.get(rate_limit_key)
            
            if current_attempts and int(current_attempts) >= 3:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many OTP requests. Please try again later."
                )

            # Generate OTP
            otp = self.generate_otp()
            masked_phone = self.mask_phone_number(phone_number)
            
            # Store OTP in Redis with expiry
            otp_key = self.get_redis_key(phone_number)
            self.redis_client.setex(
                otp_key,
                timedelta(minutes=self.otp_expiry_minutes),
                otp
            )

            # Increment rate limit counter
            self.redis_client.incr(rate_limit_key)
            self.redis_client.expire(rate_limit_key, timedelta(hours=1))

            # Send OTP via Twilio
            message_body = f"Your JODETTU verification code is: {otp}. Valid for {self.otp_expiry_minutes} minutes."
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=settings.FROM_WHATSAPP_NUMBER,
                to=f'whatsapp:{phone_number}'
            )

            logger.info(f"OTP sent to {masked_phone}. Message SID: {message.sid}")

            # Check if user is registered (you might want to move this to a separate service)
            from general.database import users as registered_users
            user = await registered_users.find_one({"user_phone_number": phone_number})
            registered = bool(user and user.get("user_name"))

            return {
                "success": True,
                "message": f"OTP sent successfully to {masked_phone}",
                "masked_phone": masked_phone,
                "otp_expiry_minutes": self.otp_expiry_minutes,
                "registered": registered
            }

        except Exception as e:
            logger.error(f"Failed to send OTP to {phone_number}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP. Please try again."
            )

    async def verify_otp(self, phone_number: str, user_otp: str) -> Dict[str, Any]:
        """Verify OTP and return JWT token if valid"""
        try:
            otp_key = self.get_redis_key(phone_number)
            stored_otp = self.redis_client.get(otp_key)

            if not stored_otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OTP not found or expired. Please request a new OTP."
                )

            # Check attempts
            attempts_key = self.get_redis_key(phone_number, ":attempts")
            attempts = int(self.redis_client.get(attempts_key) or 0)
            
            if attempts >= self.max_otp_attempts:
                self.redis_client.delete(otp_key)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum OTP attempts exceeded. Please request a new OTP."
                )

            if stored_otp != user_otp:
                self.redis_client.incr(attempts_key)
                self.redis_client.expire(attempts_key, timedelta(minutes=15))
                
                remaining_attempts = self.max_otp_attempts - (attempts + 1)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid OTP. {remaining_attempts} attempts remaining."
                )

            # OTP is valid - clean up Redis
            self.redis_client.delete(otp_key)
            self.redis_client.delete(attempts_key)
            self.redis_client.delete(self.get_redis_key(phone_number, ":rate_limit"))

            # Generate JWT token
            from general.security import Security
            security = Security()
            
            access_token = security.create_access_token(
                data={"sub": phone_number},
                expires_delta=timedelta(minutes=settings.TOKEN_EXPIRY_MINUTES)
            )

            # Check if user is registered
            from general.database import users as registered_users
            user = await registered_users.find_one({"user_phone_number": phone_number})
            registered = bool(user and user.get("user_name"))

            return {
                "success": True,
                "message": "OTP verified successfully",
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.TOKEN_EXPIRY_MINUTES * 60,
                "registered": registered
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify OTP for {phone_number}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify OTP. Please try again."
            )
