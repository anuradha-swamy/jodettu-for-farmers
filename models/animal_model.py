from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class ImageFile(BaseModel):
    """
    Model for an uploaded image or document file.
    """
    filename: str = Field(..., description="Original filename of the uploaded file")
    data: str = Field(..., description="Base64 encoded file content")
    upload_date: Optional[datetime] = Field(default_factory=datetime.now, description="When the file was uploaded")

class Vaccination(BaseModel):
    """
    Model for a single vaccination record.
    """
    vaccination_name: str = Field(..., description="Name of the vaccination")
    next_vaccination_date: datetime = Field(..., description="Date for the next dose")
    vaccination_status: str = Field(default="pending", description="Status: pending/completed")

class OwnAnimalBase(BaseModel):
    """
    Base model for the OwnAnimal model.
    This model is used to define the attributes of an animal owned by a user.
    """
    own_animal_type: str = Field(..., description="Type of animal (e.g., cow, goat, chicken)")
    own_animal_breed: str = Field(..., description="Breed of the animal")
    own_animal_name: str = Field(..., description="Name of the animal")
    own_animal_age: int = Field(..., description="Age of the animal in years")
    own_animal_height: float = Field(..., description="Height of the animal in cm")
    own_animal_weight: float = Field(..., description="Weight of the animal in kg")
    own_animal_last_vacc: datetime = Field(..., description="Last vaccination date")
    own_animal_desc: Optional[str] = Field(None, description="Optional description of the animal")
    
    # Images and documents field
    images: Optional[List[ImageFile]] = Field(default=None, description="List of uploaded images and documents")
    
    # New field for multiple vaccinations
    vaccinations: Optional[List[Vaccination]] = Field(default=None, description="List of upcoming vaccinations")
    
    # Wishlist flag for market animals
    is_wishlisted: Optional[bool] = Field(default=False, description="Whether this animal is in user's wishlist")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
