from pydantic import BaseModel,Field
from datetime import datetime

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
    