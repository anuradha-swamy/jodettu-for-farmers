from typing import List, Dict, Optional
from pydantic import BaseModel
import json

class WishlistItem(BaseModel):
    """
    Base model for a wishlist item.
    """
    item_id: str
    item_type: str  # "animal", "machine", or "product"
    added_date: str
    
class WishlistSettings(BaseModel):
    """
    Settings model for user wishlist functionality.
    """
    user_id: str
    wishlisted_animals: List[str] = []
    wishlisted_machines: List[str] = []
    wishlisted_products: List[str] = []
    
class WishlistService:
    """
    Service to manage user wishlist operations.
    """
    
    @staticmethod
    def add_to_wishlist(user_id: str, item_id: str, item_type: str) -> Dict:
        """
        Add an item to user's wishlist.
        
        Args:
            user_id: User identifier
            item_id: ID of the item to add
            item_type: Type of item ("animal", "machine", "product")
            
        Returns:
            Success message
        """
        # For now, we'll use a simple file-based storage
        # In production, this should be stored in database
        wishlist_file = f"data/wishlists/{user_id}_wishlist.json"
        
        try:
            # Read existing wishlist
            wishlist_data = WishlistService._read_wishlist_file(wishlist_file)
            
            # Add item to appropriate list
            if item_type == "animal":
                if item_id not in wishlist_data.get("wishlisted_animals", []):
                    wishlist_data.setdefault("wishlisted_animals", []).append(item_id)
            elif item_type == "machine":
                if item_id not in wishlist_data.get("wishlisted_machines", []):
                    wishlist_data.setdefault("wishlisted_machines", []).append(item_id)
            elif item_type == "product":
                if item_id not in wishlist_data.get("wishlisted_products", []):
                    wishlist_data.setdefault("wishlisted_products", []).append(item_id)
            else:
                raise ValueError(f"Invalid item type: {item_type}")
            
            # Save updated wishlist
            WishlistService._write_wishlist_file(wishlist_file, wishlist_data)
            
            return {
                "success": True,
                "message": f"{item_type.capitalize()} {item_id} added to wishlist",
                "wishlist": wishlist_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add to wishlist: {str(e)}"
            }
    
    @staticmethod
    def remove_from_wishlist(user_id: str, item_id: str, item_type: str) -> Dict:
        """
        Remove an item from user's wishlist.
        
        Args:
            user_id: User identifier
            item_id: ID of the item to remove
            item_type: Type of item ("animal", "machine", "product")
            
        Returns:
            Success message
        """
        wishlist_file = f"data/wishlists/{user_id}_wishlist.json"
        
        try:
            # Read existing wishlist
            wishlist_data = WishlistService._read_wishlist_file(wishlist_file)
            
            # Remove item from appropriate list
            if item_type == "animal":
                if item_id in wishlist_data.get("wishlisted_animals", []):
                    wishlist_data["wishlisted_animals"].remove(item_id)
            elif item_type == "machine":
                if item_id in wishlist_data.get("wishlisted_machines", []):
                    wishlist_data["wishlisted_machines"].remove(item_id)
            elif item_type == "product":
                if item_id in wishlist_data.get("wishlisted_products", []):
                    wishlist_data["wishlisted_products"].remove(item_id)
            else:
                raise ValueError(f"Invalid item type: {item_type}")
            
            # Save updated wishlist
            WishlistService._write_wishlist_file(wishlist_file, wishlist_data)
            
            return {
                "success": True,
                "message": f"{item_type.capitalize()} {item_id} removed from wishlist",
                "wishlist": wishlist_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to remove from wishlist: {str(e)}"
            }
    
    @staticmethod
    def get_user_wishlist(user_id: str) -> Dict:
        """
        Get user's complete wishlist.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's wishlist data
        """
        wishlist_file = f"data/wishlists/{user_id}_wishlist.json"
        
        try:
            return WishlistService._read_wishlist_file(wishlist_file)
        except Exception as e:
            return {
                "user_id": user_id,
                "wishlisted_animals": [],
                "wishlisted_machines": [],
                "wishlisted_products": [],
                "error": str(e)
            }
    
    @staticmethod
    def is_item_wishlisted(user_id: str, item_id: str, item_type: str) -> bool:
        """
        Check if an item is in user's wishlist.
        
        Args:
            user_id: User identifier
            item_id: ID of the item to check
            item_type: Type of item ("animal", "machine", "product")
            
        Returns:
            True if item is wishlisted, False otherwise
        """
        wishlist_data = WishlistService.get_user_wishlist(user_id)
        
        if item_type == "animal":
            return item_id in wishlist_data.get("wishlisted_animals", [])
        elif item_type == "machine":
            return item_id in wishlist_data.get("wishlisted_machines", [])
        elif item_type == "product":
            return item_id in wishlist_data.get("wishlisted_products", [])
        
        return False
    
    @staticmethod
    def _read_wishlist_file(wishlist_file: str) -> Dict:
        """
        Read wishlist data from file.
        """
        import os
        from pathlib import Path
        
        # Create directory if it doesn't exist
        Path(wishlist_file).parent.mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(wishlist_file):
            with open(wishlist_file, 'r') as f:
                return json.load(f)
        else:
            # Return empty wishlist structure
            return {
                "wishlisted_animals": [],
                "wishlisted_machines": [],
                "wishlisted_products": []
            }
    
    @staticmethod
    def _write_wishlist_file(wishlist_file: str, data: Dict) -> None:
        """
        Write wishlist data to file.
        """
        import os
        from pathlib import Path
        
        # Create directory if it doesn't exist
        Path(wishlist_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(wishlist_file, 'w') as f:
            json.dump(data, f, indent=2)

# Global wishlist service instance
wishlist_service = WishlistService()
