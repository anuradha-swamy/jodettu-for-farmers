from fastapi import HTTPException,APIRouter,Form,UploadFile,File,Depends
from general.security import Security
from services.feed_medicine_services import MarketServices
from models.product_model import ProductModel
from general.wishlist_settings import wishlist_service
from datetime import datetime
service=MarketServices()
router=APIRouter()

"""
This module defines the routes for feed and medicine-related operations.
"""

@router.post("/add-feed", operation_id="add_feed")
async def add_new_feed(
    feed_name:str=Form(...),
    feed_brand:str=Form(...),
    feed_composition:str=Form(...),
    feed_animal:str=Form(...),
    feed_manufacturer:str=Form(...),
    feed_price:float=Form(...),
    feed_expiry_date:datetime=Form(...),
    files:list[UploadFile]=File(...),
    current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    try:
        product_data=ProductModel(
            name=feed_name,
            brand=feed_brand,
            composition=feed_composition,
            animal=feed_animal,
            manufacturer=feed_manufacturer,
            price=feed_price,
            expiry_date=feed_expiry_date)
        return await service.add_feed(product_data, files)
    except Exception as e:raise HTTPException(status_code=400,detail=f"This is the flag raised{e}")        

@router.post("/add-medicine", operation_id="add_medicine")
async def add_new_medicine(
        medicine_name:str=Form(...),
        medicine_brand:str=Form(...),
        medicine_composition:str=Form(...),
        medicine_animal:str=Form(...),
        medicine_manufacturer:str=Form(...),
        medicine_price:float=Form(...),
        medicine_expiry_date:datetime=Form(...),
        files:list[UploadFile]=File(...),
        current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
        try:
            product_data=ProductModel(
                name=medicine_name,
                brand=medicine_brand,                
                composition=medicine_composition,
                animal=medicine_animal,
                manufacturer=medicine_manufacturer,
                price=medicine_price,
                expiry_date=medicine_expiry_date)
            return await service.add_medicine(product_data,files)
        except Exception as e:raise HTTPException(status_code=400,detail=str(e))        

@router.get("/all-products", operation_id="list_all_products")
async def list_all_products(current_user:dict=Depends(Security.get_current_user)):
    """
    Get all feed and medicine products with wishlist flags for the current user.
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        return await service.list_all_products_with_wishlist(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve products: {str(e)}")

@router.put("/update-feed/{feed_id}", operation_id="update_feed")
async def update_feed(feed_data:ProductModel,feed_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.update_feed(feed_id,feed_data)

@router.put("/update-medicine/{medicine_id}", operation_id="update_medicine")
async def update_medicine(medicine_data:ProductModel,medicine_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.update_medicine(medicine_id,medicine_data)

@router.delete("/delete-feed/{feed_id}", operation_id="delete_feed")
async def delete_feed(product_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.delete_product(product_id)

@router.post("/buy-feed/{feed_id}", operation_id="buy_feed")
async def buy_feed(feed_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.buy_feed(feed_id)

@router.post("/buy-medicine/{medicine_id}", operation_id="buy_medicine")
async def buy_medicine(medicine_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.buy_medicine(medicine_id)

@router.get("/search/{product_id}", operation_id="search_product")
async def search_product(product_id:str,current_user:dict=Depends(Security.get_current_user)):return await service.search_product(product_id)

@router.get("/search-by-name/{product_name}")
async def search_products_by_name(product_name: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Search for feed and medicine products by name.
    Returns all products matching the search term.
    
    Args:
        product_name: Name or partial name to search for
        current_user: Authenticated user from security dependency
        
    Returns:
        List of matching products with wishlist flags
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        return await service.search_products_by_name(product_name, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")

@router.get("/feed/search-by-name/{feed_name}")
async def search_feed_by_name(feed_name: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Search for feed products by name.
    
    Args:
        feed_name: Name or partial name to search for
        current_user: Authenticated user from security dependency
        
    Returns:
        List of matching feed products with wishlist flags
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        return await service.search_feed_by_name(feed_name, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search feed: {str(e)}")

@router.get("/medicine/search-by-name/{medicine_name}")
async def search_medicine_by_name(medicine_name: str, current_user: dict = Depends(Security.get_current_user)):
    """
    Search for medicine products by name.
    
    Args:
        medicine_name: Name or partial name to search for
        current_user: Authenticated user from security dependency
        
    Returns:
        List of matching medicine products with wishlist flags
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        return await service.search_medicine_by_name(medicine_name, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search medicine: {str(e)}")

@router.post("/bulk-upload", operation_id="bulk_upload_products")
async def bulk_upload(
    csv_file:UploadFile=File(...),
    current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.bulk_import_products(csv_file,[])

# --- Wishlist Endpoints for Feed and Medicine ---

@router.post("/feed/{feed_id}/toggle-wishlist")
async def toggle_feed_wishlist(
    feed_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Toggle feed product wishlist status (heart symbol click).
    Adds to wishlist if not present, removes if present.
    
    Args:
        feed_id: ID of the feed product to toggle
        current_user: Authenticated user from security dependency
        
    Returns:
        Updated wishlist status
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Check current status
        is_wishlisted = wishlist_service.is_item_wishlisted(user_id, feed_id, "product")
        
        # Toggle status
        if is_wishlisted:
            result = wishlist_service.remove_from_wishlist(user_id, feed_id, "product")
            action = "removed from"
        else:
            result = wishlist_service.add_to_wishlist(user_id, feed_id, "product")
            action = "added to"
            
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return {
            "success": True,
            "message": f"Feed product {action} wishlist",
            "is_wishlisted": not is_wishlisted,
            "feed_id": feed_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle wishlist: {str(e)}")

@router.post("/medicine/{medicine_id}/toggle-wishlist")
async def toggle_medicine_wishlist(
    medicine_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Toggle medicine product wishlist status (heart symbol click).
    Adds to wishlist if not present, removes if present.
    
    Args:
        medicine_id: ID of the medicine product to toggle
        current_user: Authenticated user from security dependency
        
    Returns:
        Updated wishlist status
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Check current status
        is_wishlisted = wishlist_service.is_item_wishlisted(user_id, medicine_id, "product")
        
        # Toggle status
        if is_wishlisted:
            result = wishlist_service.remove_from_wishlist(user_id, medicine_id, "product")
            action = "removed from"
        else:
            result = wishlist_service.add_to_wishlist(user_id, medicine_id, "product")
            action = "added to"
            
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return {
            "success": True,
            "message": f"Medicine product {action} wishlist",
            "is_wishlisted": not is_wishlisted,
            "medicine_id": medicine_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle wishlist: {str(e)}")
