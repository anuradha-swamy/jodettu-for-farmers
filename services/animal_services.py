import base64, csv, io, shutil
from fastapi import HTTPException
from collections import OrderedDict
from general.database import own_animals, market_animals, animal_types_collection, breeds_collection
from models.animal_model import OwnAnimalBase
from datetime import datetime
from services import taxes, discounts, convenience_fees, vaccinations
import os

UPLOAD_FILES = "upload_files"


class OwnAnimalServices:
    # ---------- MASTER DATA ----------

    @staticmethod
    async def get_animal_types():
        try:
            return own_animals.distinct("own_animal_type")
        except Exception as e:
            raise e

    @staticmethod
    async def get_breeds_by_animal_type(animal_type: str):
        normalized_type = animal_type.lower()
        return own_animals.distinct(
            "own_animal_breed",
            {"own_animal_type": normalized_type}
        )

    # ---------- USER ANIMALS ----------

    @staticmethod
    async def add_new_animal(animal_data, files, user_id=None):
        """
        Adds a new animal to the database linked to the logged-in user.
        Includes a safety check for user_id.
        """
        # DIAGNOSTIC ERROR MESSAGE
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail=f"user_id is required to add an animal. Received: {user_id} (Type: {type(user_id)})"
            )

        counter_doc = own_animals.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 1
        own_animal_id = f"OWN_{counter_value:02d}"

        data_dict = animal_data.dict()
        ordered_data = OrderedDict([
            ("user_id", user_id),
            ("own_animal_id", own_animal_id),
            *data_dict.items()
        ])

        ordered_data["own_animal_last_vacc"] = (
            ordered_data["own_animal_last_vacc"].isoformat()
        )

        # Handle images
        file_data = []
        if files:
            for file in files:
                content = await file.read()
                base64_img = base64.b64encode(content).decode("utf-8")
                file_data.append({
                    "filename": file.filename,
                    "data": base64_img
                })
            ordered_data["images"] = file_data
        else:
            ordered_data["images"] = []

        own_animals.insert_one(ordered_data)
        own_animals.update_one(
            {"function": "ID_counter"},
            {"$inc": {"count": 1}},
            upsert=True
        )

        return {
            "message": f"Animal {ordered_data['own_animal_name']} added successfully."
        }

    @staticmethod
    def list_all_animals(user_id):
        """
        Retrieves all animals for a user with formatted display data and vaccination notification flags.
        """
        # Use synchronous MongoDB operations since we're using pymongo not motor
        docs = list(own_animals.find({"user_id": user_id}))
        
        # Format the response for better display
        formatted_animals = []
        for doc in docs:
            formatted_animal = {
                "_id": str(doc["_id"]),
                "user_id": doc.get("user_id", ""),
                "own_animal_id": doc.get("own_animal_id", ""),
                "own_animal_type": doc.get("own_animal_type", ""),
                "own_animal_breed": doc.get("own_animal_breed", ""),
                "own_animal_name": doc.get("own_animal_name", ""),
                "own_animal_age": doc.get("own_animal_age", 0),
                "own_animal_height": doc.get("own_animal_height", 0.0),
                "own_animal_weight": doc.get("own_animal_weight", 0.0),
                "own_animal_last_vacc": doc.get("own_animal_last_vacc", ""),
                "own_animal_desc": doc.get("own_animal_desc", ""),
                "images": doc.get("images", []),
                "created_at": doc.get("created_at", ""),
                "updated_at": doc.get("updated_at", ""),
                "vaccination_notifications": []  # Will contain notification flags
            }
            
            # Check vaccination notifications
            try:
                from datetime import datetime, timedelta
                today = datetime.utcnow()
                reminder_date = today + timedelta(days=10)
                
                vaccinations = doc.get("vaccinations", [])
                for vacc in vaccinations:
                    if isinstance(vacc, dict):
                        next_date = vacc.get("next_vaccination_date")
                        vacc_name = vacc.get("vaccination_name", "Unknown Vaccine")
                        vacc_status = vacc.get("vaccination_status", "pending")
                        
                        if next_date and vacc_status == "pending":
                            try:
                                # Parse the date if it's a string
                                if isinstance(next_date, str):
                                    next_date = datetime.fromisoformat(next_date.replace('Z', '+00:00'))
                                
                                days_until = (next_date - today).days
                                
                                # Check if vaccination is within reminder period (10 days)
                                if today <= next_date <= reminder_date:
                                    notification = {
                                        "type": "reminder",
                                        "vaccination_name": vacc_name,
                                        "next_vaccination_date": next_date.strftime('%Y-%m-%d'),
                                        "days_until": days_until,
                                        "message": f"{vacc_name} vaccination due in {days_until} days",
                                        "severity": "info" if days_until > 3 else "warning"
                                    }
                                    formatted_animal["vaccination_notifications"].append(notification)
                                
                                # Check if vaccination is overdue
                                elif next_date < today:
                                    days_overdue = (today - next_date).days
                                    notification = {
                                        "type": "overdue",
                                        "vaccination_name": vacc_name,
                                        "next_vaccination_date": next_date.strftime('%Y-%m-%d'),
                                        "days_overdue": days_overdue,
                                        "message": f"{vacc_name} vaccination overdue by {days_overdue} days",
                                        "severity": "urgent"
                                    }
                                    formatted_animal["vaccination_notifications"].append(notification)
                                    
                            except Exception:
                                # If date parsing fails, skip this vaccination
                                continue
                                
            except Exception:
                # If notification check fails, continue without notifications
                pass
            
            formatted_animals.append(formatted_animal)
        
        return formatted_animals

    @staticmethod
    def get_animals_summary(user_id):
        """
        Retrieves a summary view of animals with essential fields only.
        """
        docs = list(own_animals.find({"user_id": user_id}))
        
        # Return only essential fields for list view
        summary_animals = []
        for doc in docs:
            summary_animal = {
                "own_animal_id": doc.get("own_animal_id", ""),
                "own_animal_name": doc.get("own_animal_name", ""),
                "own_animal_type": doc.get("own_animal_type", ""),
                "own_animal_breed": doc.get("own_animal_breed", ""),
                "own_animal_age": doc.get("own_animal_age", 0),
                "own_animal_weight": doc.get("own_animal_weight", 0.0),
                "image_count": len(doc.get("images", [])),
                "has_images": len(doc.get("images", [])) > 0,
                "own_animal_last_vacc": doc.get("own_animal_last_vacc", "")
            }
            summary_animals.append(summary_animal)
        
        return summary_animals

    @staticmethod
    def get_animal_by_id(animal_id):
        animal = own_animals.find_one({"own_animal_id": animal_id})
        if not animal:
            raise HTTPException(404, f"Animal {animal_id} not found")
        
        animal["_id"] = str(animal["_id"])
        
        # Add vaccination notification flags
        animal["vaccination_notifications"] = []
        try:
            from datetime import datetime, timedelta
            today = datetime.utcnow()
            reminder_date = today + timedelta(days=10)
            
            vaccinations = animal.get("vaccinations", [])
            for vacc in vaccinations:
                if isinstance(vacc, dict):
                    next_date = vacc.get("next_vaccination_date")
                    vacc_name = vacc.get("vaccination_name", "Unknown Vaccine")
                    vacc_status = vacc.get("vaccination_status", "pending")
                    
                    if next_date and vacc_status == "pending":
                        try:
                            # Parse the date if it's a string
                            if isinstance(next_date, str):
                                next_date = datetime.fromisoformat(next_date.replace('Z', '+00:00'))
                            
                            days_until = (next_date - today).days
                            
                            # Check if vaccination is within reminder period (10 days)
                            if today <= next_date <= reminder_date:
                                notification = {
                                    "type": "reminder",
                                    "vaccination_name": vacc_name,
                                    "next_vaccination_date": next_date.strftime('%Y-%m-%d'),
                                    "days_until": days_until,
                                    "message": f"{vacc_name} vaccination due in {days_until} days",
                                    "severity": "info" if days_until > 3 else "warning"
                                }
                                animal["vaccination_notifications"].append(notification)
                            
                            # Check if vaccination is overdue
                            elif next_date < today:
                                days_overdue = (today - next_date).days
                                notification = {
                                    "type": "overdue",
                                    "vaccination_name": vacc_name,
                                    "next_vaccination_date": next_date.strftime('%Y-%m-%d'),
                                    "days_overdue": days_overdue,
                                    "message": f"{vacc_name} vaccination overdue by {days_overdue} days",
                                    "severity": "urgent"
                                }
                                animal["vaccination_notifications"].append(notification)
                                
                        except Exception:
                            # If date parsing fails, skip this vaccination
                            continue
                            
        except Exception:
            # If notification check fails, continue without notifications
            pass
        
        return animal

    @staticmethod
    async def update_animal(animal_data, animal_id, files=None):
        existing = own_animals.find_one({"own_animal_id": animal_id})
        if not existing:
            raise HTTPException(404, f"Animal {animal_id} not found")

        update_data = animal_data.model_dump()
        update_data["own_animal_last_vacc"] = (
            update_data["own_animal_last_vacc"].isoformat()
        )

        # Handle images - if new files provided, update them; otherwise keep existing
        if files is not None:
            # New images provided - process them
            file_data = []
            if files:
                for file in files:
                    content = await file.read()
                    base64_img = base64.b64encode(content).decode("utf-8")
                    file_data.append({
                        "filename": file.filename,
                        "data": base64_img
                    })
            update_data["images"] = file_data
        else:
            # No new files provided. If images were provided in JSON, use them;
            # otherwise keep existing images.
            if update_data.get("images") is None:
                existing_images = existing.get("images", [])
                update_data["images"] = existing_images

        result = own_animals.update_one(
            {"own_animal_id": animal_id},
            {"$set": update_data}
        )

        if result.modified_count:
            return {"message": f"Animal {animal_id} updated successfully"}
        else:
            raise HTTPException(400, "No changes detected")

    @staticmethod
    async def delete_animal(animal_id):
        result = own_animals.delete_one({"own_animal_id": animal_id})
        if result.deleted_count == 0:
            raise HTTPException(404, f"Animal {animal_id} not found")
        return {"message": f"Animal {animal_id} deleted successfully"}

    @staticmethod
    async def bulk_import_animals(csv_file, image_files):
        try:
            csv_bytes = await csv_file.read()
            csv_text = io.StringIO(csv_bytes.decode("utf-8"), newline="")
            csv_reader = csv.DictReader(csv_text)
            animal_data = list(csv_reader)
            image_lookup = {file.filename: file for file in image_files}
            inserted = 0
            
            # Use a system user ID for bulk imports or handle differently
            system_user_id = "SYSTEM_IMPORT" 

            for animal in animal_data:
                image_filenames = [name.strip() for name in animal.get("images", "").split(";") if name.strip()]
                matched_files = []
                for name in image_filenames:
                    if name in image_lookup:
                        upload_file = image_lookup[name]
                        file_location = f"{UPLOAD_FILES}/{upload_file.filename}"
                        with open(file_location, "wb") as buffer:
                            shutil.copyfileobj(upload_file.file, buffer)
                        await upload_file.seek(0)
                        matched_files.append(upload_file)
                    else:
                        raise HTTPException(status_code=400, detail=f"Image {name} not found in upload.")
                try:
                    animal["own_animal_last_vacc"] = datetime.fromisoformat(animal["own_animal_last_vacc"]).isoformat()
                    animal_model = OwnAnimalBase(**animal)
                except Exception as e:
                    raise HTTPException(status_code=422, detail=f"Invalid data format: {str(e)}")
                
                # Pass the system user ID to satisfy the requirement
                # Fixed typo: OwnAnimalServices instead of Own_animal_services
                await OwnAnimalServices.add_new_animal(animal_model, matched_files, user_id=system_user_id)
                inserted += 1
            return {"message": f"Successfully imported {inserted} animals."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def bulk_import_market_animals(csv_file, image_files):
        """
        Bulk import animals directly to market (skipping own animals collection).
        """
        try:
            csv_bytes = await csv_file.read()
            csv_text = io.StringIO(csv_bytes.decode("utf-8"), newline="")
            csv_reader = csv.DictReader(csv_text)
            animal_data = list(csv_reader)
            image_lookup = {file.filename: file for file in image_files}
            inserted = 0
            
            # Use a system user ID for bulk imports
            system_user_id = "SYSTEM_IMPORT"

            for animal in animal_data:
                # Validate required market fields
                if "market_price" not in animal or not animal["market_price"]:
                    raise HTTPException(status_code=400, detail="market_price is required for all animals")
                if "latitude" not in animal or not animal["latitude"]:
                    raise HTTPException(status_code=400, detail="latitude is required for all animals")
                if "longitude" not in animal or not animal["longitude"]:
                    raise HTTPException(status_code=400, detail="longitude is required for all animals")
                
                # Handle verification flag (default to false for bulk uploads)
                is_verified = animal.get("is_verified", "false").lower() == "true"

                # Handle images
                image_filenames = [name.strip() for name in animal.get("images", "").split(";") if name.strip()]
                matched_files = []
                for name in image_filenames:
                    if name in image_lookup:
                        upload_file = image_lookup[name]
                        file_location = f"{UPLOAD_FILES}/{upload_file.filename}"
                        with open(file_location, "wb") as buffer:
                            shutil.copyfileobj(upload_file.file, buffer)
                        upload_file.seek(0)
                        matched_files.append(upload_file)
                    else:
                        raise HTTPException(status_code=400, detail=f"Image {name} not found in upload.")
                
                try:
                    # Validate animal data
                    animal["own_animal_last_vacc"] = datetime.fromisoformat(animal["own_animal_last_vacc"]).isoformat()
                    animal_model = OwnAnimalBase(**animal)
                except Exception as e:
                    raise HTTPException(status_code=422, detail=f"Invalid data format: {str(e)}")
                
                # Generate market animal ID
                counter = market_animals.find_one_and_update(
                    {"function": "ID_counter"},
                    {"$inc": {"count": 1}},
                    upsert=True,
                    return_document=True
                )
                if not counter:
                    counter = {"count": 1}
                market_animal_id = f"MKT_BULK_{counter.get('count', 1):02d}"

                # Prepare data for market animals collection
                data_dict = animal_model.dict()
                ordered_data = OrderedDict([
                    ("user_id", system_user_id),
                    ("market_animal_id", market_animal_id),
                    ("market_price", float(animal["market_price"])),
                    ("location", {"latitude": animal["latitude"], "longitude": animal["longitude"]}),
                    ("is_verified", is_verified),
                    *data_dict.items()
                ])

                ordered_data["own_animal_last_vacc"] = ordered_data["own_animal_last_vacc"]
                
                # Handle images
                file_data = []
                if matched_files:
                    for file in matched_files:
                        content = file.read()
                        base64_img = base64.b64encode(content).decode("utf-8")
                        file_data.append({
                            "filename": file.filename,
                            "data": base64_img
                        })
                ordered_data["images"] = file_data

                # Insert directly into market_animals collection
                market_animals.insert_one(ordered_data)
                inserted += 1
                
            return {"message": f"Successfully imported {inserted} market animals."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ---------- MARKETPLACE ----------

    @staticmethod
    async def sell_own_animal(animal_id, market_price, location=None):
        animal = own_animals.find_one({"own_animal_id": animal_id})
        if not animal:
            raise HTTPException(404, f"Animal {animal_id} not found")

        counter = market_animals.find_one_and_update(
            {"function": "ID_counter"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True
        )

        market_animal_id = f"MKT_{animal_id}_{counter.get('count', 1):02d}"
        animal.pop("_id", None)

        market_animals.insert_one(
            OrderedDict([
                ("market_animal_id", market_animal_id),
                ("market_price", market_price),
                ("is_verified", False),  # Default to false for individual sales
                *animal.items(),
                ("location", location or {})
            ])
        )

        return {"message": "Animal listed on market"}

    @staticmethod
    async def list_all_market_animals(user_id: str = None):
        """
        Retrieves all market animals with formatted display data and wishlist flags.
        """
        docs = list(market_animals.find({"function": {"$ne": "ID_counter"}}))
        
        # Format the response for better display
        formatted_animals = []
        for doc in docs:
            formatted_animal = {
                "_id": str(doc["_id"]),
                "market_animal_id": doc.get("market_animal_id", ""),
                "user_id": doc.get("user_id", ""),
                "own_animal_id": doc.get("own_animal_id", ""),
                "own_animal_type": doc.get("own_animal_type", ""),
                "own_animal_breed": doc.get("own_animal_breed", ""),
                "own_animal_name": doc.get("own_animal_name", ""),
                "own_animal_age": doc.get("own_animal_age", 0),
                "own_animal_height": doc.get("own_animal_height", 0.0),
                "own_animal_weight": doc.get("own_animal_weight", 0.0),
                "own_animal_last_vacc": doc.get("own_animal_last_vacc", ""),
                "own_animal_desc": doc.get("own_animal_desc", ""),
                "images": doc.get("images", []),
                "market_price": doc.get("market_price", 0.0),
                "location": doc.get("location", {}),
                "is_verified": doc.get("is_verified", False),
                "created_at": doc.get("created_at", ""),
                "updated_at": doc.get("updated_at", ""),
                "is_wishlisted": False  # Default wishlist status
            }
            
            # Check if animal is in user's wishlist (if user_id is provided)
            if user_id:
                try:
                    from general.wishlist_settings import wishlist_service
                    formatted_animal["is_wishlisted"] = wishlist_service.is_item_wishlisted(
                        user_id, doc.get("market_animal_id", ""), "animal"
                    )
                except Exception:
                    # If wishlist check fails, keep default False
                    pass
            
            formatted_animals.append(formatted_animal)
        
        return formatted_animals

    @staticmethod
    async def get_market_animals_summary():
        """
        Retrieves a summary view of market animals with essential fields only.
        """
        docs = list(market_animals.find({"function": {"$ne": "ID_counter"}}))
        
        # Return only essential fields for list view
        summary_animals = []
        for doc in docs:
            summary_animal = {
                "market_animal_id": doc.get("market_animal_id", ""),
                "own_animal_id": doc.get("own_animal_id", ""),
                "own_animal_name": doc.get("own_animal_name", ""),
                "own_animal_type": doc.get("own_animal_type", ""),
                "own_animal_breed": doc.get("own_animal_breed", ""),
                "own_animal_age": doc.get("own_animal_age", 0),
                "own_animal_weight": doc.get("own_animal_weight", 0.0),
                "market_price": doc.get("market_price", 0.0),
                "location": doc.get("location", {}),
                "is_verified": doc.get("is_verified", False),
                "image_count": len(doc.get("images", [])),
                "has_images": len(doc.get("images", [])) > 0,
                "seller_id": doc.get("user_id", "")
            }
            summary_animals.append(summary_animal)
        
        return summary_animals

    @staticmethod
    async def search_market_animal_by_id(animal_id):
        animal = market_animals.find_one({"market_animal_id": animal_id})
        if not animal:
            raise HTTPException(404, "Market animal not found")
        animal["_id"] = str(animal["_id"])
        return animal

    @staticmethod
    def buy_animal(animal_id, buyer_user_id=None):
        animal = market_animals.find_one({"market_animal_id": animal_id})
        if not animal:
            raise HTTPException(404, "Market animal not found")

        price = animal.get("market_price", 0)
        tax = taxes.TaxCalculator.taxes(price)
        discount = discounts.DiscountCalculator.discounts(price)
        fee = convenience_fees.ConvFeeCalculator.conv_fees(price)

        # Get buyer user_id if not provided
        if not buyer_user_id:
            raise HTTPException(400, "Buyer user ID is required")

        # Remove animal from market
        market_animals.delete_one({"market_animal_id": animal_id})
        
        # Transfer animal to buyer's own animals collection
        animal_data = {
            "user_id": buyer_user_id,
            "own_animal_id": f"OWN_{animal_id.split('_')[-1]}",
            "own_animal_type": animal.get("own_animal_type", ""),
            "own_animal_breed": animal.get("own_animal_breed", ""),
            "own_animal_name": animal.get("own_animal_name", ""),
            "own_animal_age": animal.get("own_animal_age", 0),
            "own_animal_height": animal.get("own_animal_height", 0.0),
            "own_animal_weight": animal.get("own_animal_weight", 0.0),
            "own_animal_last_vacc": animal.get("own_animal_last_vacc", ""),
            "own_animal_desc": animal.get("own_animal_desc", ""),
            "images": animal.get("images", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Generate counter for own animals
        counter_doc = own_animals.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 1
        
        # Insert into own animals collection
        own_animals.insert_one(animal_data)
        
        # Update counter
        own_animals.update_one(
            {"function": "ID_counter"},
            {"$inc": {"count": 1}},
            upsert=True
        )

        return {
            "message": f"Successfully purchased animal {animal.get('own_animal_name', 'Unknown')}",
            "base_price": price,
            "tax": tax,
            "discount": discount,
            "convenience_fee": fee,
            "final_price": price + tax + fee - discount,
            "own_animal_id": animal_data["own_animal_id"]
        }

    @staticmethod
    async def count_animals(user_id):
        # Filter animals by user_id
        user_animals = own_animals.find({"user_id": user_id})
        count = {"total_animals": len(list(user_animals.clone()))}
        
        # Count by animal type for this user
        for t in own_animals.distinct("own_animal_type", {"user_id": user_id}):
            count[t.upper()] = own_animals.count_documents({"own_animal_type": t, "user_id": user_id})
        return count

    @staticmethod
    async def vacc_dues(user_id):
        # Filter animals by user_id
        docs = list(own_animals.find({"user_id": user_id}))
        result = []
        for doc in docs:
            updated = vaccinations.VaccinationDues.vaccinations(doc)
            result.append({
                "animal_name": updated["own_animal_name"],
                "breed": updated["own_animal_breed"],
                "age": updated["own_animal_age"],
                "due_date": updated["vaccination_due_date"]
            })
        return result
