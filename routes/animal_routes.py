# --- THIS IS THE LATEST VERSION - CHECK THE LOGS FOR THIS PRINT STATEMENT ---
print("EXECUTING LATEST animal_routes.py - DEPLOYMENT IS WORKING")
# --- IF YOU DON'T SEE THIS, THE SERVER IS RUNNING AN OLD FILE ---

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from general.security import Security
from services.animal_services import OwnAnimalServices
from services.master_data_service import master_data_service
from general.wishlist_settings import wishlist_service
from models.animal_model import OwnAnimalBase, Vaccination, ImageFile
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()

# Request model for JSON update endpoint
class UpdateAnimalBody(BaseModel):
    own_animal_type: str
    own_animal_breed: str
    own_animal_name: str
    own_animal_age: int
    own_animal_height: float
    own_animal_weight: float
    own_animal_last_vacc: datetime
    own_animal_desc: Optional[str] = None
    images: Optional[List[ImageFile]] = None
    next_vaccination_date: Optional[datetime] = None
    is_wishlisted: Optional[bool] = False

# --- Admin Endpoints (PostgreSQL) ---
# ... (code for admin endpoints remains the same)

# --- Public Endpoints (PostgreSQL) ---
# ... (code for public endpoints remains the same)

# --- User Animal Endpoints (MongoDB) ---
@router.post("/add-animal")
async def add_new_animal(
    own_animal_type:str=Form(...),
    own_animal_breed:str=Form(...),
    own_animal_name:str=Form(...),
    own_animal_age:int=Form(...),
    own_animal_height:float=Form(...),
    own_animal_weight:float=Form(...),
    own_animal_last_vacc:datetime=Form(...),
    own_animal_desc:Optional[str]=Form(None),
    next_vaccination_date: datetime = Form(
        ...,
        description="Next vaccination date (ISO date-time)"
    ),
    files:Optional[list[UploadFile]]=File(default=None),
    current_user:dict=Depends(Security.get_current_user)
):
    try:
        vaccinations_list = [
            Vaccination(
                vaccination_name="General Vaccination",
                next_vaccination_date=next_vaccination_date
            )
        ]

        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        animal_data = OwnAnimalBase(
            own_animal_type=own_animal_type,
            own_animal_breed=own_animal_breed,
            own_animal_name=own_animal_name,
            own_animal_age=own_animal_age,
            own_animal_height=own_animal_height,
            own_animal_weight=own_animal_weight,
            own_animal_last_vacc=own_animal_last_vacc,
            own_animal_desc=own_animal_desc,
            vaccinations=vaccinations_list if vaccinations_list else None
        )
        return OwnAnimalServices.add_new_animal(animal_data, files, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add animal: {str(e)}")

@router.get("/all-animals")
async def list_all_animals(current_user: dict = Depends(Security.get_current_user)):
    """
    Retrieves all animals belonging to the currently authenticated user.
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token. Please re-authenticate.")
        return OwnAnimalServices.list_all_animals(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animals: {str(e)}")

@router.post("/market-animals/{animal_id}/toggle-wishlist")
async def toggle_animal_wishlist(
    animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Toggle animal wishlist status (heart symbol click).
    Adds to wishlist if not present, removes if present.
    
    Args:
        animal_id: ID of the animal to toggle
        current_user: Authenticated user from security dependency
        
    Returns:
        Updated wishlist status
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Check current status
        is_wishlisted = wishlist_service.is_item_wishlisted(user_id, animal_id, "animal")
        
        # Toggle status
        if is_wishlisted:
            result = wishlist_service.remove_from_wishlist(user_id, animal_id, "animal")
            action = "removed from"
        else:
            result = wishlist_service.add_to_wishlist(user_id, animal_id, "animal")
            action = "added to"
            
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return {
            "success": True,
            "message": f"Animal {action} wishlist",
            "is_wishlisted": not is_wishlisted,
            "animal_id": animal_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle wishlist: {str(e)}")

@router.get("/market-animals")
async def list_market_animals(current_user: dict = Depends(Security.get_current_user)):
    """
    Retrieves all market animals available for sale with wishlist flags.
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        return await OwnAnimalServices.list_all_market_animals(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market animals: {str(e)}")

@router.post("/sell-animal/{animal_id}")
async def sell_animal(
    animal_id: str,
    market_price: float = Form(...),
    verification: bool = Form(False),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Put an animal up for sale in the market.
    
    Args:
        animal_id: ID of the animal to sell
        market_price: Asking price for the animal
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        verification: Whether user has verified the sale details
        current_user: Authenticated user from security dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If database operation fails or verification not confirmed
    """
    try:
        if not verification:
            raise HTTPException(
                status_code=400, 
                detail="Please verify the sale details before proceeding. Set verification flag to true."
            )
        
        return await OwnAnimalServices.sell_own_animal(animal_id, market_price, location=None)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sell animal: {str(e)}")

@router.post("/bulk-upload-market-animals")
async def bulk_upload_market_animals(
    csv_file: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Bulk upload animals directly to market from CSV file with associated images.
    
    Args:
        csv_file: CSV file containing animal data with market-specific fields
        image_files: Associated image files (optional)
        current_user: Authenticated user from security dependency
        
    Returns:
        Import result message
        
    Raises:
        HTTPException: If validation fails or database operation fails
        
    CSV Required Fields:
        - own_animal_type: Type of the animal
        - own_animal_breed: Breed of the animal  
        - own_animal_name: Name of the animal
        - own_animal_age: Age of the animal
        - own_animal_height: Height of the animal
        - own_animal_weight: Weight of the animal
        - own_animal_last_vacc: Last vaccination date (ISO format)
        - market_price: Price for the market
        - latitude: Location latitude
        - longitude: Location longitude
        - is_verified: Verification status (true/false)
        
    CSV Optional Fields:
        - own_animal_desc: Description of the animal
        - images: Semicolon-separated list of image filenames
    """
    try:
        return await OwnAnimalServices.bulk_import_market_animals(csv_file, [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk upload market animals: {str(e)}")

@router.post("/buy-animal/{market_animal_id}")
async def buy_animal(
    market_animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Buy a market animal and transfer ownership.
    
    Args:
        market_animal_id: ID of the market animal to buy
        current_user: Authenticated user from security dependency
        
    Returns:
        Purchase confirmation with pricing breakdown and new animal ID
        
    Raises:
        HTTPException: If animal not found or database operation fails
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token. Please re-authenticate.")
            
        return OwnAnimalServices.buy_animal(market_animal_id, buyer_user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to buy animal: {str(e)}"
        )

# --- Other Endpoints ---

@router.get("/animal/{animal_id}")
async def get_animal_by_id(animal_id: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Retrieve a specific animal by ID.
    """
    try:
        return OwnAnimalServices.get_animal_by_id(animal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animal: {str(e)}")

@router.get("/animal/{animal_id}/images")
async def get_animal_images(animal_id: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Get only the images for an animal, formatted for display in edit forms.
    Returns existing images as data URLs that can be directly displayed in HTML.
    """
    try:
        animal = await OwnAnimalServices.get_animal_by_id(animal_id)
        images = animal.get("images", [])
        
        image_data = []
        for img in images:
            if img.get("data"):
                # Create data URL for display
                data_url = f"data:image/jpeg;base64,{img['data']}"
                image_data.append({
                    "filename": img.get("filename", "image.jpg"),
                    "data_url": data_url,
                    "preview_url": data_url,
                    "size": len(img.get("data", "")) // 1024  # Size in KB
                })
        
        return {
            "animal_id": animal_id,
            "image_count": len(image_data),
            "has_images": len(image_data) > 0,
            "images": image_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animal images: {str(e)}")

@router.get("/animal/{animal_id}/edit")
async def get_animal_for_edit(animal_id: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Retrieve animal data formatted for editing, including existing images.
    This endpoint returns the animal data in a format suitable for populating an edit form.
    """
    try:
        animal = await OwnAnimalServices.get_animal_by_id(animal_id)
        
        # Format the response for edit form
        edit_data = {
            "own_animal_id": animal.get("own_animal_id", ""),
            "own_animal_type": animal.get("own_animal_type", ""),
            "own_animal_breed": animal.get("own_animal_breed", ""),
            "own_animal_name": animal.get("own_animal_name", ""),
            "own_animal_age": animal.get("own_animal_age", 0),
            "own_animal_height": animal.get("own_animal_height", 0.0),
            "own_animal_weight": animal.get("own_animal_weight", 0.0),
            "own_animal_last_vacc": animal.get("own_animal_last_vacc", ""),
            "own_animal_desc": animal.get("own_animal_desc", ""),
            "vaccinations": animal.get("vaccinations", []),
            "images": animal.get("images", []),
            "image_count": len(animal.get("images", [])),
            "has_images": len(animal.get("images", [])) > 0,
            "existing_image_urls": []
        }
        
        # Convert base64 image data to displayable URLs/data URLs
        for img in animal.get("images", []):
            if img.get("data"):
                # Create data URL for display
                data_url = f"data:image/jpeg;base64,{img['data']}"
                edit_data["existing_image_urls"].append({
                    "filename": img.get("filename", "image.jpg"),
                    "data_url": data_url,
                    "preview_url": data_url  # For frontend preview
                })
        
        return edit_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animal for edit: {str(e)}")

@router.put("/animal/{animal_id}")
async def update_animal(
    animal_id: str,
    animal_data: UpdateAnimalBody,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Update an existing animal's information (JSON body only).
    """
    try:
        vaccinations_list = []
        if animal_data.next_vaccination_date:
            vaccinations_list = [
                Vaccination(
                    vaccination_name="General Vaccination",
                    next_vaccination_date=animal_data.next_vaccination_date
                )
            ]

        own_animal = OwnAnimalBase(
            own_animal_type=animal_data.own_animal_type,
            own_animal_breed=animal_data.own_animal_breed,
            own_animal_name=animal_data.own_animal_name,
            own_animal_age=animal_data.own_animal_age,
            own_animal_height=animal_data.own_animal_height,
            own_animal_weight=animal_data.own_animal_weight,
            own_animal_last_vacc=animal_data.own_animal_last_vacc,
            own_animal_desc=animal_data.own_animal_desc,
            images=animal_data.images,
            vaccinations=vaccinations_list if vaccinations_list else None,
            is_wishlisted=animal_data.is_wishlisted
        )

        return await OwnAnimalServices.update_animal(own_animal, animal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update animal: {str(e)}")

@router.put("/animal/{animal_id}/with-images")
async def update_animal_with_images(
    animal_id: str,
    own_animal_type: str = Form(...),
    own_animal_breed: str = Form(...),
    own_animal_name: str = Form(...),
    own_animal_age: int = Form(...),
    own_animal_height: float = Form(...),
    own_animal_weight: float = Form(...),
    own_animal_last_vacc: datetime = Form(...),
    own_animal_desc: Optional[str] = Form(None),
    next_vaccination_date: datetime = Form(
        ...,
        description="Next vaccination date (ISO date-time)"
    ),
    files: Optional[list[UploadFile]] = File(default=None),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Update an existing animal's information with image support.
    Allows updating all animal fields including images.
    """
    try:
        vaccinations_list = [
            Vaccination(
                vaccination_name="General Vaccination",
                next_vaccination_date=next_vaccination_date
            )
        ]

        animal_data = OwnAnimalBase(
            own_animal_type=own_animal_type,
            own_animal_breed=own_animal_breed,
            own_animal_name=own_animal_name,
            own_animal_age=own_animal_age,
            own_animal_height=own_animal_height,
            own_animal_weight=own_animal_weight,
            own_animal_last_vacc=own_animal_last_vacc,
            own_animal_desc=own_animal_desc,
            vaccinations=vaccinations_list if vaccinations_list else None
        )
        
        return await OwnAnimalServices.update_animal(animal_data, animal_id, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update animal: {str(e)}")

@router.put("/animal/{animal_id}/images")
async def update_animal_images(
    animal_id: str,
    files: Optional[list[UploadFile]] = File(default=None),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Update only the images for an existing animal.
    Use this endpoint when you want to add/replace images without changing other animal data.
    """
    try:
        # Get existing animal data
        existing_animal = await OwnAnimalServices.get_animal_by_id(animal_id)
        
        # Create animal data with existing values
        animal_data = OwnAnimalBase(
            own_animal_type=existing_animal.get("own_animal_type", ""),
            own_animal_breed=existing_animal.get("own_animal_breed", ""),
            own_animal_name=existing_animal.get("own_animal_name", ""),
            own_animal_age=existing_animal.get("own_animal_age", 0),
            own_animal_height=existing_animal.get("own_animal_height", 0.0),
            own_animal_weight=existing_animal.get("own_animal_weight", 0.0),
            own_animal_last_vacc=datetime.fromisoformat(existing_animal.get("own_animal_last_vacc", datetime.now().isoformat())),
            own_animal_desc=existing_animal.get("own_animal_desc"),
            vaccinations=existing_animal.get("vaccinations", [])
        )
        
        return await OwnAnimalServices.update_animal(animal_data, animal_id, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update animal images: {str(e)}")

@router.delete("/animal/{animal_id}")
async def delete_animal(animal_id: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Delete an animal by ID.
    """
    try:
        return OwnAnimalServices.delete_animal(animal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete animal: {str(e)}")

@router.get("/master-data")
async def get_master_data():
    """
    Get master data for animal types and breeds.
    """
    try:
        return master_data_service.get_master_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve master data: {str(e)}")

@router.get("/animal-types")
async def get_animal_types():
    """
    Get all available animal types.
    """
    try:
        return await OwnAnimalServices.get_animal_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animal types: {str(e)}")

@router.get("/breeds/{animal_type}")
async def get_breeds_by_animal_type(animal_type: str):
    """
    Get all breeds for a specific animal type.
    """
    try:
        return await OwnAnimalServices.get_breeds_by_animal_type(animal_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve breeds: {str(e)}")

@router.get("/count")
async def count_animals():
    """
    Get count of animals by type.
    """
    try:
        return await OwnAnimalServices.count_animals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count animals: {str(e)}")

@router.get("/market-animal/search")
async def search_market_animal(animal_id: str):
    """
    Search for a market animal by ID.
    """
    try:
        return await OwnAnimalServices.search_market_animal_by_id(animal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search market animal: {str(e)}")

@router.get("/vaccination-due-dates")
async def vaccination_due_dates():
    """
    Get animals with upcoming vaccination due dates.
    """
    try:
        return await OwnAnimalServices.vacc_dues()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vaccination dues: {str(e)}")

@router.get("/animal/{animal_id}/share")
async def get_shareable_animal_details(animal_id: str):
    """
    Get shareable animal details for social media sharing.
    Returns essential information that can be shared via WhatsApp, Instagram, etc.
    
    Args:
        animal_id: ID of the animal to get shareable details for
        
    Returns:
        Shareable animal information with formatted text for social media
    """
    try:
        animal = await OwnAnimalServices.get_animal_by_id(animal_id)
        
        # Create shareable content
        share_text = f"""
🐄 *Animal for Sale - {animal.get('own_animal_name', 'Unknown')}*

📝 *Details:*
• Type: {animal.get('own_animal_type', 'N/A').title()}
• Breed: {animal.get('own_animal_breed', 'N/A').title()}
• Age: {animal.get('own_animal_age', 'N/A')} years
• Height: {animal.get('own_animal_height', 'N/A')} feet
• Weight: {animal.get('own_animal_weight', 'N/A')} kgs

💰 *Price:* ₹{animal.get('market_price', 'Contact for price')}
📍 *Location:* Available for purchase

📞 *Interested?* Check out our app for more details!
🔗 *Download Link:* [Your App Store Link]

#Jodettu #AnimalsForSale #{animal.get('own_animal_type', '').title()}ForSale
        """.strip()
        
        # Generate shareable URL (this would be your app's deep link)
        share_url = f"https://yourapp.com/animal/{animal_id}"
        
        return {
            "animal_id": animal_id,
            "animal_name": animal.get('own_animal_name', 'Unknown'),
            "animal_type": animal.get('own_animal_type', 'N/A'),
            "animal_breed": animal.get('own_animal_breed', 'N/A'),
            "price": animal.get('market_price', 'Contact for price'),
            "share_text": share_text,
            "share_url": share_url,
            "whatsapp_message": f"Check out this {animal.get('own_animal_type', 'animal')} for sale: {share_url}",
            "has_images": len(animal.get('images', [])) > 0,
            "image_count": len(animal.get('images', []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate shareable details: {str(e)}")

# --- Admin Endpoints ---
@router.post("/admin/animal-types")
async def create_animal_type(
    animal_type: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Create a new animal type (admin only).
    """
    try:
        # This would need to be implemented in the service
        return {"message": f"Animal type {animal_type} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create animal type: {str(e)}")

@router.post("/admin/breeds")
async def create_breed(
    animal_type: str = Form(...),
    breed: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Create a new breed for an animal type (admin only).
    """
    try:
        # This would need to be implemented in the service
        return {"message": f"Breed {breed} for {animal_type} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create breed: {str(e)}")
