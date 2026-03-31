from pydantic import BaseModel,Field
from typing import Optional

class MachineModel(BaseModel):
    """
    Base model for the Machine model.
    This model is used to define the attributes of a machine.
    """
    machine_name:str=Field(...)
    machine_brand:str=Field(...)
    machine_price:float=Field(...)
    machine_desc:str=Field(...)