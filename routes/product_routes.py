from fastapi import APIRouter, HTTPException, Depends
from general.security import Security
from general.wishlist_settings import wishlist_service

router = APIRouter()

"""
This module defines the wishlist routes for product-related operations.
- /products/{product_id}/toggle-wishlist: Toggle product wishlist status
"""

# --- Product Wishlist Endpoints ---

@router.post("/products/{product_id}/toggle-wishlist")
async def toggle_product_wishlist(
    product_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Toggle product wishlist status (heart symbol click).
    Adds to wishlist if not present, removes if present.
    
    Args:
        product_id: ID of the product to toggle
        current_user: Authenticated user from security dependency
        
    Returns:
        Updated wishlist status
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Check current status
        is_wishlisted = wishlist_service.is_item_wishlisted(user_id, product_id, "product")
        
        # Toggle status
        if is_wishlisted:
            result = wishlist_service.remove_from_wishlist(user_id, product_id, "product")
            action = "removed from"
        else:
            result = wishlist_service.add_to_wishlist(user_id, product_id, "product")
            action = "added to"
            
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return {
            "success": True,
            "message": f"Product {action} wishlist",
            "is_wishlisted": not is_wishlisted,
            "product_id": product_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle wishlist: {str(e)}")
