from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional

class ProductModel(BaseModel):
    """
    Base model for the Product model.
    This model is used to define the attributes of a product.
    """
    name:str=Field(...)
    brand:str=Field(...)
    composition:str=Field(...)
    animal:str=Field(...)
    manufacturer:str=Field(...)
    price:float=Field(...)
    expiry_date:datetime=Field(...)
    is_wishlisted: Optional[bool] = Field(default=False, description="Whether this product is in user's wishlist")
