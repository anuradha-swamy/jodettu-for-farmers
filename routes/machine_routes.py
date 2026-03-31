from fastapi import APIRouter,UploadFile,File,Form,HTTPException,Depends
from general.security import Security
from services.machine_services import MachineServices
from services.machine_bulk_service import MachineBulkService
from general.wishlist_settings import wishlist_service
from models.machine_model import MachineModel
service=MachineServices()
router=APIRouter()

"""
This module defines the routes for machine-related operations.
- /add-machine: Adds a new machine (Admin only).
- /buy/{machine_id}: Buys a machine.
- /all-machines: Lists all machines.
- /update-machine/{machine_name}: Updates an existing machine (Admin only).
- /delete-machine/{machine_name}: Deletes a machine (Admin only).
- /bulk-upload: Imports machines from a CSV file and images (Admin only).
- /search/{machine_id}: Searches for a machine by ID.
"""

@router.post("/add-machine")
async def add_new_machine(
    machine_name:str=Form(...),
    machine_brand:str=Form(...),
    machine_price:float=Form(...),
    machine_desc:str=Form(...),
    files:list[UploadFile]=File(...),
    current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    try:
        machine_data=MachineModel(
            machine_name=machine_name,
            machine_brand=machine_brand,
            machine_price=machine_price,
            machine_desc=machine_desc,)
        return await service.add_new_machine(machine_data,files)
    except Exception as e:raise HTTPException(status_code=400,detail=str(e))

@router.post("/machines/{machine_id}/toggle-wishlist")
async def toggle_machine_wishlist(
    machine_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Toggle machine wishlist status (heart symbol click).
    Adds to wishlist if not present, removes if present.
    
    Args:
        machine_id: ID of the machine to toggle
        current_user: Authenticated user from security dependency
        
    Returns:
        Updated wishlist status
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Check current status
        is_wishlisted = wishlist_service.is_item_wishlisted(user_id, machine_id, "machine")
        
        # Toggle status
        if is_wishlisted:
            result = wishlist_service.remove_from_wishlist(user_id, machine_id, "machine")
            action = "removed from"
        else:
            result = wishlist_service.add_to_wishlist(user_id, machine_id, "machine")
            action = "added to"
            
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return {
            "success": True,
            "message": f"Machine {action} wishlist",
            "is_wishlisted": not is_wishlisted,
            "machine_id": machine_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle wishlist: {str(e)}")

@router.post("/buy/{machine_id}")
async def buy_machine(machine_id,current_user:dict=Depends(Security.get_current_user)):return await service.buy_machine(machine_id)

@router.get("/all-machines")
async def get_all_machines(current_user: dict = Depends(Security.get_current_user)):
    """
    Get all machines with wishlist flags.
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        return await service.get_all_machines(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve machines: {str(e)}")

@router.put("/update-machine/{machine_id}")
async def update_machine(data:MachineModel,machine_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.update_machine(data,machine_id)

@router.delete("/delete-machine/{machine_id}")
async def delete_machine(machine_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.delete_machine(machine_id)

@router.post("/bulk-upload")
async def bulk_upload(csv_file:UploadFile=File(...),current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await MachineBulkService.bulk_upload_machines(csv_file,[])

@router.get("/search/{machine_name}")
async def search_machine(machine_name:str,current_user:dict=Depends(Security.get_current_user)):
    return await service.search_machine_by_name(machine_name)

@router.get("/machine/{machine_id}")
async def get_machine_by_id(machine_id: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Get a specific machine by ID.
    """
    try:
        return await service.search_machine_by_id(machine_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve machine: {str(e)}")
