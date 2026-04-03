"""
Animal routes for FastAPI application.
This module handles all animal-related endpoints using MongoDB for transactional data
and PostgreSQL for master data (animal types and breeds).
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from general.security import Security
from services.animal_services import OwnAnimalServices
from services.master_data_service import MasterDataService
from models.animal_model import OwnAnimalBase
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from db.async_db import get_postgres_db

# Initialize services - Use class directly for static methods
# animal_service = OwnAnimalServices()  # Not needed for static methods
master_data_service = MasterDataService()
router = APIRouter()

print("FIXED animal_routes_fixed.py loaded - user_id parameter issue resolved")
print("INFO: IMAGE UPDATE ENDPOINTS ADDED - /animal/{id}/with-images, /animal/{id}/images, /animal/{id}/edit")
print("INFO: REGULAR UPDATE ENDPOINT UPDATED - Now returns animal data with images")
print("INFO: ASYNC/SYNC ISSUE FIXED - All MongoDB operations now synchronous")
print("INFO: IMAGE DISPLAY ENHANCED - Regular update now shows existing images with displayable URLs")


@router.get("/debug/routes-info")
async def debug_routes_info(current_user: dict = Depends(Security.get_current_user)):
    """
    Debug endpoint to identify which routes file is being used
    """
    return {
        "message": "This is from animal_routes_fixed.py (production file)",
        "file": "animal_routes_fixed.py",
        "has_image_endpoints": True,
        "new_endpoints": [
            "GET /animal/{id}/images",
            "GET /animal/{id}/edit", 
            "PUT /animal/{id}/with-images",
            "PUT /animal/{id}/images"
        ],
        "timestamp": datetime.now().isoformat()
    }


# Response Models for Swagger UI
class UpdateAnimalResponse(BaseModel):
    message: str
    animal_data: dict  # Include animal data with images
    existing_images: list = []  # Displayable image URLs
    image_count: int = 0
    has_images: bool = False


class AnimalResponse(BaseModel):
    message: str


@router.get("/animal-types", response_model=List[str])
async def get_animal_types(
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Get all active animal types from PostgreSQL master data.
    
    Args:
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session
        
    Returns:
        List of animal type names
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        animal_types = await master_data_service.get_animal_types(db)
        return animal_types
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve animal types: {str(e)}"
        )


@router.get("/breeds/{animal_type}", response_model=List[str])
async def get_breeds(
    animal_type: str,
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Get all active breeds for a specific animal type from PostgreSQL master data.
    
    Args:
        animal_type: The animal type to get breeds for
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session
        
    Returns:
        List of breed names for the specified animal type
        
    Raises:
        HTTPException: If animal type not found or database operation fails
    """
    try:
        breeds = await master_data_service.get_breeds_by_animal_type(db, animal_type)
        return breeds
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve breeds for '{animal_type}': {str(e)}"
        )


@router.get("/master-data", response_model=List[dict])
async def get_master_data(
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Get all animal types with their breeds from PostgreSQL master data.
    
    Args:
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session
        
    Returns:
        List of animal types with their breeds
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        master_data = await master_data_service.get_all_animal_types_with_breeds(db)
        return master_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve master data: {str(e)}"
        )


@router.post(
    "/add-animal",
    response_model=AnimalResponse,
    summary="Add New Animal",
    description="Add a new animal to the user's collection. Validates animal type and breed against master data.",
    responses={
        200: {
            "description": "Animal added successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Animal Bessie added successfully."}
                }
            }
        },
        400: {
            "description": "Invalid data or breed not valid for animal type"
        },
        401: {
            "description": "Unauthorized"
        }
    }
)
async def add_new_animal(
    own_animal_type: str = Form(...),
    own_animal_breed: str = Form(...),
    own_animal_name: str = Form(...),
    own_animal_age: int = Form(...),
    own_animal_height: float = Form(...),
    own_animal_weight: float = Form(...),
    own_animal_last_vacc: datetime = Form(...),
    own_animal_desc: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(default=None),
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Add a new animal to the system.
    Validates that the animal type and breed exist in PostgreSQL master data
    before saving to MongoDB transactional data.
    
    Args:
        own_animal_type: Type of the animal
        own_animal_breed: Breed of the animal
        own_animal_name: Name of the animal
        own_animal_age: Age of the animal
        own_animal_height: Height of the animal
        own_animal_weight: Weight of the animal
        own_animal_last_vacc: Last vaccination date
        own_animal_desc: Optional description
        files: Optional image files
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session for validation
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If validation fails or database operation fails
    """
    try:
        # Validate animal type and breed exist in master data
        breeds = await master_data_service.get_breeds_by_animal_type(db, own_animal_type)
        if own_animal_breed not in breeds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Breed '{own_animal_breed}' is not valid for animal type '{own_animal_type}'. "
                       f"Valid breeds are: {', '.join(breeds)}"
            )
        
        # Create animal data object
        animal_data = OwnAnimalBase(
            own_animal_type=own_animal_type,
            own_animal_breed=own_animal_breed,
            own_animal_name=own_animal_name,
            own_animal_age=own_animal_age,
            own_animal_height=own_animal_height,
            own_animal_weight=own_animal_weight,
            own_animal_last_vacc=own_animal_last_vacc,
            own_animal_desc=own_animal_desc
        )
        
        # Save to MongoDB (transactional data)
        user_id = current_user.get("user_id")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token")
        return await OwnAnimalServices.add_new_animal(animal_data, files, user_id)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add animal: {str(e)}"
        )


@router.get(
    "/all-animals",
    response_model=List[dict],
    summary="Get All Animals",
    description="Retrieve all animals belonging to the currently authenticated user.",
    responses={
        200: {
            "description": "List of animals retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "user_id": "USER_001",
                            "own_animal_id": "OWN_01",
                            "own_animal_type": "cow",
                            "own_animal_breed": "holstein",
                            "own_animal_name": "Bessie",
                            "own_animal_age": 4,
                            "own_animal_height": 150.5,
                            "own_animal_weight": 600.0,
                            "own_animal_last_vacc": "2024-01-15T10:30:00",
                            "own_animal_desc": "Healthy dairy cow",
                            "images": []
                        }
                    ]
                }
            }
        },
        401: {
            "description": "Unauthorized"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def list_all_animals(current_user: dict = Depends(Security.get_current_user)):
    """
    Get all animals from MongoDB transactional data.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        List of all animals
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        # Extract user_id from current_user token
        user_id = current_user.get("user_id")
        print(f"DEBUG: list_all_animals called with user_id: {user_id}")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token. Please re-authenticate."
            )
        print(f"DEBUG: Calling OwnAnimalServices.list_all_animals({user_id})")
        result = OwnAnimalServices.list_all_animals(user_id)
        print(f"DEBUG: Successfully retrieved {len(result)} animals")
        return result
    except Exception as e:
        print(f"DEBUG: Unexpected error in list_all_animals: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve animals: {str(e)}"
        )


@router.put(
    "/update/{own_animal_id}",
    response_model=UpdateAnimalResponse,
    summary="Update Animal",
    description="Update an existing animal's information (JSON body only). Returns updated animal data including existing images. The animal type and breed must exist in the master data.",
    responses={
        200: {
            "description": "Animal updated successfully",
            "content": {
                "application/json": {
                    "example": {
                    "message": "Animal OWN_01 updated successfully",
                    "animal_data": {
                        "own_animal_id": "OWN_01",
                        "own_animal_type": "cow",
                        "own_animal_breed": "holstein",
                        "own_animal_name": "Bessie",
                        "own_animal_age": 4,
                        "own_animal_height": 150.5,
                        "own_animal_weight": 600.0,
                        "own_animal_last_vacc": "2024-01-15T10:30:00",
                        "own_animal_desc": "Healthy dairy cow",
                        "images": [
                            {
                                "filename": "cow1.jpg",
                                "data": "base64_encoded_image_data"
                            }
                        ]
                    },
                    "existing_images": [
                        {
                            "filename": "cow1.jpg",
                            "data_url": "data:image/jpeg;base64,base64_encoded_image_data",
                            "preview_url": "data:image/jpeg;base64,base64_encoded_image_data",
                            "size": 256
                        }
                    ],
                    "image_count": 1,
                    "has_images": True
                }
                }
            }
        },
        400: {
            "description": "Invalid data or breed not valid for animal type"
        },
        404: {
            "description": "Animal not found"
        },
        401: {
            "description": "Unauthorized"
        }
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "own_animal_type": {"type": "string", "example": "cow"},
                            "own_animal_breed": {"type": "string", "example": "holstein"},
                            "own_animal_name": {"type": "string", "example": "Bessie"},
                            "own_animal_age": {"type": "integer", "example": 4},
                            "own_animal_height": {"type": "number", "example": 150.5},
                            "own_animal_weight": {"type": "number", "example": 600.0},
                            "own_animal_last_vacc": {"type": "string", "format": "date-time", "example": "2024-01-15T10:30:00"},
                            "own_animal_desc": {"type": "string", "example": "Healthy dairy cow"}
                        },
                        "required": ["own_animal_type", "own_animal_breed", "own_animal_name", "own_animal_age", "own_animal_height", "own_animal_weight", "own_animal_last_vacc"]
                    },
                    "example": {
                        "own_animal_type": "cow",
                        "own_animal_breed": "holstein", 
                        "own_animal_name": "Bessie",
                        "own_animal_age": 4,
                        "own_animal_height": 150.5,
                        "own_animal_weight": 600.0,
                        "own_animal_last_vacc": "2024-01-15T10:30:00",
                        "own_animal_desc": "Healthy dairy cow"
                    }
                }
            },
            "required": True
        }
    }
)
async def update_animal(
    data: OwnAnimalBase,
    own_animal_id: str,
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Update an existing animal.
    Validates that the animal type and breed exist in PostgreSQL master data
    before updating in MongoDB transactional data.
    
    Args:
        data: Updated animal data
        own_animal_id: ID of the animal to update
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session for validation
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If validation fails or database operation fails
    """
    try:
        # Validate animal type and breed exist in master data
        breeds = await master_data_service.get_breeds_by_animal_type(db, data.own_animal_type)
        if data.own_animal_breed not in breeds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Breed '{data.own_animal_breed}' is not valid for animal type '{data.own_animal_type}'. "
                       f"Valid breeds are: {', '.join(breeds)}"
            )
        
        # Update animal and return updated data with images
        result = OwnAnimalServices.update_animal(data, own_animal_id)
        
        # Get updated animal data to return with images
        updated_animal = OwnAnimalServices.get_animal_by_id(own_animal_id)
        
        # Format images for display
        existing_images = []
        for img in updated_animal.get("images", []):
            if img.get("data"):
                # Create data URL for display
                data_url = f"data:image/jpeg;base64,{img['data']}"
                existing_images.append({
                    "filename": img.get("filename", "image.jpg"),
                    "data_url": data_url,
                    "preview_url": data_url,
                    "size": len(img.get("data", "")) // 1024  # Size in KB
                })
        
        return {
            "message": result.get("message", "Animal updated successfully"),
            "animal_data": updated_animal,
            "existing_images": existing_images,
            "image_count": len(existing_images),
            "has_images": len(existing_images) > 0
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update animal: {str(e)}"
        )


@router.put("/animal/{own_animal_id}/with-images")
async def update_animal_with_images(
    own_animal_id: str,
    own_animal_type: str = Form(...),
    own_animal_breed: str = Form(...),
    own_animal_name: str = Form(...),
    own_animal_age: int = Form(...),
    own_animal_height: float = Form(...),
    own_animal_weight: float = Form(...),
    own_animal_last_vacc: datetime = Form(...),
    own_animal_desc: Optional[str] = Form(None),
    files: Optional[list[UploadFile]] = File(default=None),
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Update an existing animal's information with image support.
    Allows updating all animal fields including images.
    Validates that the animal type and breed exist in PostgreSQL master data.
    """
    try:
        # Validate animal type and breed exist in master data
        breeds = await master_data_service.get_breeds_by_animal_type(db, own_animal_type)
        if own_animal_breed not in breeds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Breed '{own_animal_breed}' is not valid for animal type '{own_animal_type}'. "
                       f"Valid breeds are: {', '.join(breeds)}"
            )

        animal_data = OwnAnimalBase(
            own_animal_type=own_animal_type,
            own_animal_breed=own_animal_breed,
            own_animal_name=own_animal_name,
            own_animal_age=own_animal_age,
            own_animal_height=own_animal_height,
            own_animal_weight=own_animal_weight,
            own_animal_last_vacc=own_animal_last_vacc,
            own_animal_desc=own_animal_desc
        )
        
        return await OwnAnimalServices.update_animal(animal_data, own_animal_id, files)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update animal: {str(e)}"
        )


@router.put("/animal/{own_animal_id}/images")
async def update_animal_images(
    own_animal_id: str,
    files: Optional[list[UploadFile]] = File(default=None),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Update only the images for an existing animal.
    Use this endpoint when you want to add/replace images without changing other animal data.
    """
    try:
        # Get existing animal data
        existing_animal = OwnAnimalServices.get_animal_by_id(own_animal_id)
        
        # Create animal data with existing values
        animal_data = OwnAnimalBase(
            own_animal_type=existing_animal.get("own_animal_type", ""),
            own_animal_breed=existing_animal.get("own_animal_breed", ""),
            own_animal_name=existing_animal.get("own_animal_name", ""),
            own_animal_age=existing_animal.get("own_animal_age", 0),
            own_animal_height=existing_animal.get("own_animal_height", 0.0),
            own_animal_weight=existing_animal.get("own_animal_weight", 0.0),
            own_animal_last_vacc=datetime.fromisoformat(existing_animal.get("own_animal_last_vacc", datetime.now().isoformat())),
            own_animal_desc=existing_animal.get("own_animal_desc")
        )
        
        return await OwnAnimalServices.update_animal(animal_data, own_animal_id, files)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update animal images: {str(e)}"
        )


@router.get("/animal/{own_animal_id}/images")
async def get_animal_images(
    own_animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get only the images for an animal, formatted for display in edit forms.
    Returns existing images as data URLs that can be directly displayed in HTML.
    """
    try:
        animal = OwnAnimalServices.get_animal_by_id(own_animal_id)
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
            "animal_id": own_animal_id,
            "image_count": len(image_data),
            "has_images": len(image_data) > 0,
            "images": image_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve animal images: {str(e)}"
        )


@router.get("/animal/{own_animal_id}/edit")
async def get_animal_for_edit(
    own_animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Retrieve animal data formatted for editing, including existing images.
    This endpoint returns the animal data in a format suitable for populating an edit form.
    """
    try:
        animal = OwnAnimalServices.get_animal_by_id(own_animal_id)
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve animal for edit: {str(e)}"
        )


@router.delete("/delete/{animal_id}")
async def delete_animal(
    animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Delete an animal from MongoDB transactional data.
    
    Args:
        animal_id: ID of the animal to delete
        current_user: Authenticated user from security dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        return await OwnAnimalServices.delete_animal(animal_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete animal: {str(e)}"
        )


@router.get("/search/{animal_id}")
async def search_animal(
    animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Search for an animal by ID in MongoDB transactional data.
    
    Args:
        animal_id: ID of the animal to search
        current_user: Authenticated user from security dependency
        
    Returns:
        Animal data
        
    Raises:
        HTTPException: If animal not found or database operation fails
    """
    try:
        return await OwnAnimalServices.get_animal_by_id(animal_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search animal: {str(e)}"
        )


@router.post("/import-csv-images/")
async def import_animals_from_csv(
    csv_file: UploadFile = File(...),
    image_files: List[UploadFile] = File(...),
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Import animals from CSV file with associated images.
    Validates animal types and breeds against PostgreSQL master data.
    
    Args:
        csv_file: CSV file containing animal data
        image_files: Associated image files
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session for validation
        
    Returns:
        Import result message
        
    Raises:
        HTTPException: If validation fails or database operation fails
    """
    try:
        # Get all valid animal types and breeds for validation
        master_data = await master_data_service.get_all_animal_types_with_breeds(db)
        valid_combinations = {}
        for animal_type_data in master_data:
            valid_combinations[animal_type_data["name"]] = set(animal_type_data["breeds"])
        
        # Perform import with validation
        return await OwnAnimalServices.bulk_import_animals(csv_file, image_files, valid_combinations)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import animals: {str(e)}"
        )


@router.post("/sell-animal/{animal_id}")
async def sell_animal(
    animal_id: str,
    market_price: float = Form(...),
    latitude: str = Form(...),
    longitude: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Put an animal up for sale in the market.
    
    Args:
        animal_id: ID of the animal to sell
        market_price: Asking price for the animal
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        current_user: Authenticated user from security dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        location = {"latitude": latitude, "longitude": longitude}
        return await OwnAnimalServices.sell_own_animal(animal_id, market_price, location)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sell animal: {str(e)}"
        )


@router.get("/market-animals")
async def all_market_animals(current_user: dict = Depends(Security.get_current_user)):
    """
    Get all animals available in the market from MongoDB transactional data.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        List of market animals
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        return await OwnAnimalServices.list_all_market_animals()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market animals: {str(e)}"
        )


@router.get("/market-animal/search")
async def search_market_animal(
    animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Search for a market animal by ID in MongoDB transactional data.
    
    Args:
        animal_id: ID of the market animal to search
        current_user: Authenticated user from security dependency
        
    Returns:
        Market animal data
        
    Raises:
        HTTPException: If animal not found or database operation fails
    """
    try:
        return await OwnAnimalServices.search_market_animal_by_id(animal_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search market animal: {str(e)}"
        )


@router.post("/buy-animal/{animal_id}")
async def buy_animal(
    animal_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Buy an animal from the market.
    
    Args:
        animal_id: ID of the market animal to buy
        current_user: Authenticated user from security dependency
        
    Returns:
        Purchase details with pricing breakdown
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        return await OwnAnimalServices.buy_animal(animal_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to buy animal: {str(e)}"
        )


@router.get("/count-animals")
async def count_animals(current_user: dict = Depends(Security.get_current_user)):
    """
    Get count statistics for animals from MongoDB transactional data.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        Animal count statistics
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        # Extract user_id for count_animals
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token. Please re-authenticate."
            )
        return await OwnAnimalServices.count_animals(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count animals: {str(e)}"
        )


@router.get("/vaccination-due-dates")
async def vacc_dues(current_user: dict = Depends(Security.get_current_user)):
    """
    Get animals with upcoming vaccination due dates from MongoDB transactional data.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        List of animals with vaccination due dates
        
    Raises:
        HTTPException: If database operation fails
    """
    try:
        # Extract user_id for vacc_dues
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token. Please re-authenticate."
            )
        return await OwnAnimalServices.vacc_dues(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vaccination due dates: {str(e)}"
        )


# Admin endpoints for master data management
@router.post("/admin/animal-types")
async def create_animal_type(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Create a new animal type in PostgreSQL master data (admin only).
    
    Args:
        name: Name of the animal type
        description: Optional description
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session
        
    Returns:
        Created animal type data
        
    Raises:
        HTTPException: If validation fails or database operation fails
    """
    try:
        # Check if user has admin privileges (you may need to implement this check)
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        animal_type = await master_data_service.create_animal_type(db, name, description)
        return {
            "id": animal_type.id,
            "name": animal_type.name,
            "description": animal_type.description,
            "is_active": animal_type.is_active,
            "created_at": animal_type.created_at
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create animal type: {str(e)}"
        )


@router.post("/admin/breeds")
async def create_breed(
    animal_type: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    origin: Optional[str] = Form(None),
    characteristics: Optional[str] = Form(None),
    current_user: dict = Depends(Security.get_current_user),
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Create a new breed in PostgreSQL master data (admin only).
    
    Args:
        animal_type: Animal type for the breed
        name: Name of the breed
        description: Optional description
        origin: Optional origin information
        characteristics: Optional breed characteristics
        current_user: Authenticated user from security dependency
        db: PostgreSQL database session
        
    Returns:
        Created breed data
        
    Raises:
        HTTPException: If validation fails or database operation fails
    """
    try:
        # Check if user has admin privileges (you may need to implement this check)
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        breed = await master_data_service.create_breed(
            db, animal_type, name, description, origin, characteristics
        )
        return {
            "id": breed.id,
            "name": breed.name,
            "animal_type": animal_type,
            "description": breed.description,
            "origin": breed.origin,
            "characteristics": breed.characteristics,
            "is_active": breed.is_active,
            "created_at": breed.created_at
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create breed: {str(e)}"
        )
