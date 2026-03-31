from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from general.security import Security
# --- FIX: Importing from v2 to force cache break ---
from services.animal_services_v2 import OwnAnimalServices
from services.master_data_service import master_data_service
from models.animal_model import OwnAnimalBase
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

service = OwnAnimalServices()
router = APIRouter()

# --- Request Models for Admin APIs ---
class AnimalTypeCreate(BaseModel):
    animal_type: str

class BreedCreate(BaseModel):
    animal_type: str
    breed_name: str

# --- Admin Endpoints (PostgreSQL) ---

@router.post("/admin/animal-types", status_code=status.HTTP_201_CREATED)
async def create_animal_type(
    data: AnimalTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(Security.get_current_admin_user)
):
    """
    Creates a new animal type in PostgreSQL.
    """
    try:
        await master_data_service.create_animal_type(db, data.animal_type)
        return {"message": f"Animal type '{data.animal_type}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/breeds", status_code=status.HTTP_201_CREATED)
async def create_breed(
    data: BreedCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(Security.get_current_admin_user)
):
    """
    Creates a new breed for a specific animal type in PostgreSQL.
    """
    try:
        await master_data_service.create_breed(db, data.animal_type, data.breed_name)
        return {"message": f"Breed '{data.breed_name}' added to '{data.animal_type}' successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Public Endpoints (PostgreSQL) ---

@router.get("/animal-types", response_model=List[str])
async def get_animal_types(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Returns a list of supported animal types from PostgreSQL.
    """
    try:
        return await master_data_service.get_animal_types(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animal types: {str(e)}")

@router.get("/breeds/{animal_type}", response_model=List[str])
async def get_breeds(
    animal_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Returns a list of breeds for a given animal type from PostgreSQL.
    """
    try:
        breeds = await master_data_service.get_breeds_by_animal_type(db, animal_type)
        if not breeds:
             return []
        return breeds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve breeds for '{animal_type}': {str(e)}")

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
    files:Optional[list[UploadFile]]=File(default=None),current_user:dict=Depends(Security.get_current_user)):
    try:
        animal_data = OwnAnimalBase(
            own_animal_type=own_animal_type,
            own_animal_breed=own_animal_breed,
            own_animal_name=own_animal_name,
            own_animal_age=own_animal_age,
            own_animal_height=own_animal_height,
            own_animal_weight=own_animal_weight,
            own_animal_last_vacc=own_animal_last_vacc,
            own_animal_desc=own_animal_desc)
        
        # ✅ FIX: Extract user_id from the token payload
        user_id = current_user.get("user_id")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token")

        # ✅ FIX: Pass user_id to the service method
        return await service.add_new_animal(animal_data, files, user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add animal: {str(e)}")    

@router.get("/all-animals")
async def list_all_animals(current_user:dict=Depends(Security.get_current_user)):
    # ✅ FIX: Extract user_id from the token payload
    user_id = current_user.get("user_id")
    if not user_id:
         raise HTTPException(status_code=400, detail="User ID not found in token")
    return await service.list_all_animals(user_id)

@router.put("/update/{own_animal_id}")
async def update_animal(data:OwnAnimalBase,own_animal_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.update_animal(data,own_animal_id)

@router.delete("/delete/{animal_id}")
async def delete_animal(animal_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.delete_animal(animal_id)

@router.get("/search/{animal_id}")
async def search_animal(animal_id,current_user:dict=Depends(Security.get_current_user)):return await service.get_animal_by_id(animal_id)

@router.post("/import-csv-images/")
async def import_animals_from_csv(csv_file:UploadFile=File(...),image_files:list[UploadFile]=File(...)):return await service.bulk_import_animals(csv_file,image_files)

@router.post("/sell-animal/{animal_id}")
async def sell_animal(animal_id:str,market_price:float=Form(...),latitude:str=Form(...),longitude:str=Form(...),current_user:dict=Depends(Security.get_current_user)):
    location={"latitude":latitude,"longitude":longitude};return await service.sell_own_animal(animal_id,market_price,location)

@router.get("/market-animals")
async def all_market_animals(current_user:dict=Depends(Security.get_current_user)):return await service.list_all_market_animals()

@router.get("/market-animal/search")
async def search_market_animal(animal_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.search_market_animal_by_id(animal_id)

@router.post("/buy-animal/{animal_id}")
async def buy_animal(animal_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.buy_animal(animal_id)

@router.get("count-animals")
async def count_animals(current_user:dict=Depends(Security.get_current_user)):return await service.count_animals()

@router.get("/vaccination-due-dates")
async def vacc_dues(current_user:dict=Depends(Security.get_current_user)):return await service.vacc_dues()
