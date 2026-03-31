import base64,csv,shutil,io
from fastapi import HTTPException
from collections import OrderedDict
from general.database import machines
from models.machine_model import MachineModel
from services import taxes,discounts,convenience_fees
UPLOAD_FILES="upload_files"

"""
This module defines the MachineServices class, which handles machine-related operations.
"""
class MachineServices:
    @staticmethod
    async def add_new_machine(machine_data,files):
        """
        This function adds a new machine to the database.
        It generates a unique machine ID based on the machine brand and a counter.
        Args:
            machine_data (MachineModel): The machine data to be added.
            files (list): A list of files associated with the machine.
        Returns:
            HTTPException: An exception indicating the success or failure of the operation.
        """
        counter_doc=machines.find_one({"function":"ID_counter"})
        counter_value=counter_doc["count"]if counter_doc else 1
        data=machine_data.model_dump()
        prefix=data["machine_brand"][:3].upper()
        machine_id=f"{prefix}_{counter_value:02d}"
        ordered_data=OrderedDict([("machine_id",machine_id),*data.items()])
        file_data=[]
        for file in files:
            file_content=file.read()
            base64_string=base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename":file.filename,"data":base64_string})
        ordered_data["images"]=file_data
        machines.insert_one(ordered_data)
        machines.update_one({"function":"ID_counter"},{"$inc":{"count": 1}},upsert=True)
        return HTTPException(status_code=200,detail=f"Machine {ordered_data['machine_name']} added successfully.")
    
    @staticmethod
    async def get_all_machines(user_id: str = None):
        """
        This function retrieves all machines from the database with wishlist flags.
        Args:
            user_id: User ID to check wishlist status
        Returns:
            list: A list of machines in the database with wishlist status.
        """
        exclude_filter={"function": {"$ne": "ID_counter"}}
        docs=list(machines.find(exclude_filter))
        
        # Add wishlist flags if user_id is provided
        if user_id:
            try:
                from general.wishlist_settings import wishlist_service
                machines_with_wishlist = []
                for doc in docs:
                    machine_data = {**doc, "_id": str(doc["_id"])}
                    machine_data["is_wishlisted"] = wishlist_service.is_item_wishlisted(
                        user_id, doc.get("machine_id", ""), "machine"
                    )
                    machines_with_wishlist.append(machine_data)
                return machines_with_wishlist
            except Exception:
                # If wishlist check fails, return machines without wishlist flags
                pass
        
        return [{**doc, "_id": str(doc["_id"]), "is_wishlisted": False} for doc in docs]
    
    @staticmethod
    async def update_machine(data,machine_id):
        """
        This function updates an existing machine in the database.
        It checks if the machine exists and updates its information.
        Args:
            data (MachineModel): The updated machine data.
            machine_id (str): The ID of the machine to be updated.
        Returns:
            HTTPException: An exception indicating the success or failure of the operation.
        """
        existing_machine=machines.find_one({"machine_id":machine_id})
        if not existing_machine:raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found")
        dict_data=data.model_dump()
        result=machines.update_one({"machine_id": machine_id},{"$set":dict_data})
        if result.modified_count:raise HTTPException(status_code=200,detail=f"Machine {machine_id} updated successfully!")
        else:raise HTTPException(status_code=400,detail="No changes detected!")
    
    @staticmethod
    async def delete_machine(machine_id):
        """
        This function deletes a machine from the database.
        It checks if the machine exists and deletes it.
        Args:
            machine_id (str): The ID of the machine to be deleted.
        Returns:
            HTTPException: An exception indicating the success or failure of the operation.
        """
        existing_machine=machines.find_one({"machine_id":machine_id})
        if not existing_machine:raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found")
        result=machines.delete_one({"machine_id": machine_id})
        if result.deleted_count:raise HTTPException(status_code=200,detail=f"Machine {machine_id} deleted successfully!")
        else:raise HTTPException(status_code=400,detail="Machine deletion failed!")
    
    @staticmethod
    async def search_machine_by_id(machine_id):
        """
        This function searches for a machine by its ID.
        Args:
            machine_id (str): The ID of the machine to search for.
        Returns:
            dict: The machine data if found, None otherwise.
        """
        machine=machines.find_one({"machine_id":machine_id})
        if machine:
            return {**machine, "_id": str(machine["_id"])}
        else:
            raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found")

    @staticmethod
    async def search_machine_by_name(machine_name: str):
        """
        Search machines by name (case-insensitive, partial match).
        Returns a list of matching machines.
        """
        query = {"machine_name": {"$regex": machine_name, "$options": "i"}}
        cursor = machines.find(query)
        machines_list = list(cursor)
        if not machines_list:
            raise HTTPException(status_code=404, detail=f"No machines found for name '{machine_name}'")
        return [{**doc, "_id": str(doc["_id"])} for doc in machines_list]
    
    @staticmethod
    async def buy_machine(machine_id):
        """
        This function handles the purchase of a machine.
        Args:
            machine_id (str): The ID of the machine to buy.
        Returns:
            HTTPException: An exception indicating the success or failure of the operation.
        """
        machine=machines.find_one({"machine_id":machine_id})
        if not machine:raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found")
        # Add purchase logic here
        return HTTPException(status_code=200,detail=f"Machine {machine_id} purchased successfully!")
