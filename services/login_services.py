from fastapi import HTTPException, status
from general.database import users as registered_users, otp_collection, own_animals
from models.user_model import User
from general.security import Security
from datetime import timedelta, datetime
from app.utils.schemas import OTPSentResponse, TokenResponse

sec = Security()

class LoginServices:
    @staticmethod
    async def send_otp(phone_number: str) -> OTPSentResponse:
        """
        Step 1: Send OTP
        - Calls the synchronous send_otp method.
        - Stores phone number temporarily for verification.
        - Automatically prepends +91 if country code is missing.
        """
        try:
            # --- FIX: Normalize phone number to include +91 ---
            if not phone_number.startswith('+'):
                phone_number = '+91' + phone_number
            elif not phone_number.startswith('+91'):
                # If it starts with '+' but not '+91', assume it's another country code
                pass 
            
            expiry_seconds = Security.send_otp(phone_number)
            masked_phone = Security.mask_phone_number(phone_number)
            
            return OTPSentResponse(
                success=True,
                message=f"OTP has been sent successfully to {masked_phone}",
                expires_in=expiry_seconds,
                phone_number=phone_number
            )
        except Exception as e:
            print(f"🔴 UNHANDLED EXCEPTION IN SEND_OTP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An internal error occurred: {str(e)}"
            )

    @staticmethod
    async def verify_otp(phone_number: str, user_otp: str) -> TokenResponse:
        """
        Step 2: Verify OTP & Generate Access Token
        - Verifies the OTP directly with the phone number.
        - If valid, generates and returns the JWT access token.
        """
        try:
            # --- FIX: Normalize phone number to include +91 ---
            if not phone_number.startswith('+'):
                phone_number = '+91' + phone_number
            elif not phone_number.startswith('+91'):
                # If it starts with '+' but not '+91', assume it's another country code
                pass
            
            # --- FIX: Removed 'await' from synchronous Security call ---
            Security.verify_otp(phone_number, user_otp)

            # DB calls can remain async if using Motor, but we assume PyMongo for now
            # For consistency, let's treat them as sync calls run by FastAPI in a thread pool
            user = registered_users.find_one({"user_phone_number": phone_number})
            is_registered = bool(user and user.get("user_name"))

            if not user:
                counter_doc = registered_users.find_one_and_update(
                    {"function": "ID_counter"},
                    {"$inc": {"count": 1}},
                    upsert=True,
                    return_document=True
                )
                counter_value = counter_doc.get("count", 1)
                user_id = f"USER_{counter_value:04d}"
                
                registered_users.insert_one({
                    "user_phone_number": phone_number, 
                    "user_id": user_id,
                    "role": "user" # Default role
                })
                # Fetch the newly created user to get the ID for the token
                user = registered_users.find_one({"user_phone_number": phone_number})

            # 3. Generate ACCESS TOKEN with User ID and Role
            token_payload = {
                "sub": phone_number,
                "user_id": user.get("user_id"),
                "role": user.get("role", "user")
            }
            
            access_token = Security.create_access_token(
                data=token_payload, 
                expires_delta=timedelta(minutes=60)
            )

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                registered=is_registered,
                requires_registration=not is_registered
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"🔴 UNHANDLED EXCEPTION IN VERIFY_OTP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An internal error occurred: {str(e)}"
            )

    @staticmethod
    async def register_user(registration_data: dict, phone_number: str):
        user = registered_users.find_one({"user_phone_number": phone_number})
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        if user.get("user_name"):
            raise HTTPException(status_code=400, detail="User is already registered.")
        
        # Update user profile with new fields
        update_data = {
            "user_name": f"{registration_data.get('first_name', '')} {registration_data.get('last_name', '')}".strip(),
            "first_name": registration_data.get('first_name'),
            "last_name": registration_data.get('last_name'),
            "dob": registration_data.get('dob'),
            "gender": registration_data.get('gender'),
            "address": registration_data.get('address'),
            "role": registration_data.get('role', 'user')
        }
        
        # Update user profile
        registered_users.update_one(
            {"user_phone_number": phone_number},
            {"$set": update_data}
        )
        
        # --- AUTOMATIC DUMMY ANIMAL SEEDING ---
        user_id = user.get("user_id")
        if user_id:
            # Check if user already has animals to avoid duplicates
            existing_animals = own_animals.find_one({"user_id": user_id})
            if not existing_animals:
                dummy_animals = [
                    {
                        "user_id": user_id,
                        "own_animal_id": f"OWN_{user_id}_01",
                        "own_animal_type": "cow",
                        "own_animal_breed": "Gir",
                        "own_animal_name": "Gauri",
                        "own_animal_age": 4,
                        "own_animal_height": 140.5,
                        "own_animal_weight": 350.0,
                        "own_animal_last_vacc": datetime.now().isoformat(),
                        "own_animal_desc": "Healthy and active.",
                        "images": "No Images Attached"
                    },
                    {
                        "user_id": user_id,
                        "own_animal_id": f"OWN_{user_id}_02",
                        "own_animal_type": "buffalo",
                        "own_animal_breed": "Murrah",
                        "own_animal_name": "Kaali",
                        "own_animal_age": 5,
                        "own_animal_height": 145.0,
                        "own_animal_weight": 400.0,
                        "own_animal_last_vacc": datetime.now().isoformat(),
                        "own_animal_desc": "High milk yield.",
                        "images": "No Images Attached"
                    }
                ]
                own_animals.insert_many(dummy_animals)
                print(f"✅ Dummy animals seeded for user {user_id}")

        return {"message": "User registered successfully."}

    @staticmethod
    async def get_all_registered_users():
        users_cursor = registered_users.find({"user_name": {"$exists": True}})
        users_list = list(users_cursor)  # Convert cursor to list

        normalized_users = []
        for user in users_list:
            normalized_users.append({
                "user_name": user.get("user_name", ""),
                "user_dob": user.get("user_dob") or user.get("dob") or "",
                "user_gender": user.get("user_gender") or user.get("gender") or "",
                "user_address": user.get("user_address") or user.get("address") or "",
                "user_phone_number": user.get("user_phone_number", ""),
                "role": user.get("role", "user")
            })

        return normalized_users

    @staticmethod
    async def delete_user_by_phone(phone_number: str):
        """
        Deletes a user and their associated data by phone number.
        Prevents deletion of other admins.
        """
        user = registered_users.find_one({"user_phone_number": phone_number})
        if not user:
            raise HTTPException(status_code=404, detail=f"User with phone number {phone_number} not found.")
        
        # Check if the user to be deleted is an admin
        if user.get("role") == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot delete another admin user."
            )
        
        user_id = user.get("user_id")
        
        # Delete user record
        result = registered_users.delete_one({"user_phone_number": phone_number})
        
        # Delete associated animals
        if user_id:
            own_animals.delete_many({"user_id": user_id})
            
        if result.deleted_count > 0:
            return {"message": f"User {phone_number} and associated data deleted successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user.")

    @staticmethod
    async def edit_user_profile(phone_number: str, profile_data: dict):
        """
        Edit user profile details.
        """
        try:
            user = registered_users.find_one({"user_phone_number": phone_number})
            if not user:
                raise HTTPException(status_code=404, detail="User not found.")
            
            # Prepare update data
            update_data = {}
            
            # Only update fields that are provided
            if 'user_name' in profile_data:
                update_data['user_name'] = profile_data['user_name']
            if 'first_name' in profile_data:
                update_data['first_name'] = profile_data['first_name']
            if 'last_name' in profile_data:
                update_data['last_name'] = profile_data['last_name']
            if 'user_dob' in profile_data:
                update_data['user_dob'] = profile_data['user_dob']
            if 'user_gender' in profile_data:
                update_data['user_gender'] = profile_data['user_gender']
            if 'user_address' in profile_data:
                update_data['user_address'] = profile_data['user_address']
            if 'user_phone_number' in profile_data:
                update_data['user_phone_number'] = profile_data['user_phone_number']
            
            if not update_data:
                raise HTTPException(status_code=400, detail="No valid fields to update.")
            
            # Update user in database
            result = registered_users.update_one(
                {"user_phone_number": phone_number},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return {"message": "Profile updated successfully!", "updated_fields": list(update_data.keys())}
            else:
                raise HTTPException(status_code=400, detail="No changes made to profile.")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")

    @staticmethod
    async def get_user_profile(phone_number: str):
        """
        Get user profile details.
        """
        try:
            user = registered_users.find_one({"user_phone_number": phone_number})
            if not user:
                raise HTTPException(status_code=404, detail="User not found.")
            
            # Convert ObjectId to string for JSON response
            user["_id"] = str(user["_id"])
            
            # Remove sensitive data if needed
            user.pop("password", None)
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")
