from fastapi import APIRouter, HTTPException, Depends
from general.security import Security
from general.wishlist_settings import wishlist_service
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter()

"""
This module defines the routes for wishlist operations across all item types.
- /add: Add an item to wishlist
- /remove: Remove an item from wishlist  
- /check: Check if an item is wishlisted
- /all: Get user's complete wishlist
"""

class WishlistRequest(BaseModel):
    """
    Model for wishlist operations.
    """
    item_id: str
    item_type: str  # "animal", "machine", or "product"

@router.post("/add")
async def add_to_wishlist(
    request: WishlistRequest,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Add an item to user's wishlist (heart symbol functionality).
    
    Args:
        request: Wishlist request containing item_id and item_type
        current_user: Authenticated user from security dependency
        
    Returns:
        Success message with updated wishlist
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Validate item type
        if request.item_type not in ["animal", "machine", "product"]:
            raise HTTPException(status_code=400, detail="Invalid item type. Must be 'animal', 'machine', or 'product'")
            
        result = wishlist_service.add_to_wishlist(user_id, request.item_id, request.item_type)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add item to wishlist: {str(e)}")

@router.post("/remove")
async def remove_from_wishlist(
    request: WishlistRequest,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Remove an item from user's wishlist.
    
    Args:
        request: Wishlist request containing item_id and item_type
        current_user: Authenticated user from security dependency
        
    Returns:
        Success message with updated wishlist
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Validate item type
        if request.item_type not in ["animal", "machine", "product"]:
            raise HTTPException(status_code=400, detail="Invalid item type. Must be 'animal', 'machine', or 'product'")
            
        result = wishlist_service.remove_from_wishlist(user_id, request.item_id, request.item_type)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove item from wishlist: {str(e)}")

@router.get("/check/{item_type}/{item_id}")
async def check_wishlist_status(
    item_type: str,
    item_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Check if an item is in user's wishlist.
    
    Args:
        item_type: Type of item ("animal", "machine", or "product")
        item_id: ID of the item to check
        current_user: Authenticated user from security dependency
        
    Returns:
        Wishlist status of the item
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Validate item type
        if item_type not in ["animal", "machine", "product"]:
            raise HTTPException(status_code=400, detail="Invalid item type. Must be 'animal', 'machine', or 'product'")
            
        is_wishlisted = wishlist_service.is_item_wishlisted(user_id, item_id, item_type)
        
        return {
            "item_id": item_id,
            "item_type": item_type,
            "is_wishlisted": is_wishlisted,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check wishlist status: {str(e)}")

@router.get("/all")
async def get_complete_wishlist(
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get user's complete wishlist across all item types.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        User's complete wishlist data
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        wishlist_data = wishlist_service.get_user_wishlist(user_id)
        
        # Add user_id to response if not present
        if "user_id" not in wishlist_data:
            wishlist_data["user_id"] = user_id
            
        return wishlist_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve wishlist: {str(e)}")

@router.get("/summary")
async def get_wishlist_summary(
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get a summary of user's wishlist with counts by type.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        Summary of user's wishlist
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        wishlist_data = wishlist_service.get_user_wishlist(user_id)
        
        summary = {
            "user_id": user_id,
            "total_items": 0,
            "animals_count": len(wishlist_data.get("wishlisted_animals", [])),
            "machines_count": len(wishlist_data.get("wishlisted_machines", [])),
            "products_count": len(wishlist_data.get("wishlisted_products", [])),
            "animals": wishlist_data.get("wishlisted_animals", []),
            "machines": wishlist_data.get("wishlisted_machines", []),
            "products": wishlist_data.get("wishlisted_products", [])
        }
        
        summary["total_items"] = summary["animals_count"] + summary["machines_count"] + summary["products_count"]
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve wishlist summary: {str(e)}")

@router.delete("/clear")
async def clear_wishlist(
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Clear all items from user's wishlist.
    
    Args:
        current_user: Authenticated user from security dependency
        
    Returns:
        Success message
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Clear all wishlist items by setting empty lists
        wishlist_file = f"data/wishlists/{user_id}_wishlist.json"
        empty_wishlist = {
            "wishlisted_animals": [],
            "wishlisted_machines": [],
            "wishlisted_products": []
        }
        
        wishlist_service._write_wishlist_file(wishlist_file, empty_wishlist)
        
        return {
            "success": True,
            "message": "Wishlist cleared successfully",
            "wishlist": empty_wishlist
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear wishlist: {str(e)}")
