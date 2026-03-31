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
    async def get_all_machines():
        """
        This function retrieves all machines from the database.
        Args:
            exclude_filter (dict): A dictionary of filters to exclude certain machines.
        Returns:
            list: A list of machines in the database.
        """
        exclude_filter={"function": {"$ne": "ID_counter"}}
        doc_cursor=machines.find(exclude_filter)
        docs=doc_cursor.to_list(length=None)
        return[{**doc,"_id":str(doc["_id"])}for doc in docs]
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
        existing_machine=await machines.find_one({"machine_id":machine_id})
        if not existing_machine:raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found")
        dict_data=data.model_dump()
        result=await machines.update_one({"machine_id": machine_id},{"$set":dict_data})
        if result.modified_count:raise HTTPException(status_code=200,detail=f"Machine {machine_id} updated successfully!")
        else:raise HTTPException(status_code=400,detail="No changes detected!")
    @staticmethod
    async def delete_machine(machine_id):
        """
        This function deletes a machine from the database.
        It checks if the machine exists and deletes it if it does.
        Args:
            machine_id (str): The ID of the machine to be deleted.
        Returns:
            HTTPException: An exception indicating the success or failure of the operation.
        """
        existing_machine=await machines.find_one({"machine_id":machine_id})
        if not existing_machine:raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found!")
        else:
            machines.delete_one({"machine_id":machine_id})
            raise HTTPException(status_code=200,detail=f"Machine {machine_id} deleted successfully!")        
    @staticmethod
    async def bulk_upload_machines(csv_file,image_files):
        """
        This function handles the bulk upload of machines from a CSV file.
        It reads the CSV file, processes the machine data, and adds them to the database.
        Args:
            csv_file (UploadFile): The CSV file containing machine data.
            image_files (list): A list of image files associated with the machines.
        Returns:
            HTTPException: An exception indicating the success or failure of the operation.
        """
        try:
            csv_bytes=await csv_file.read()
            csv_text=io.StringIO(csv_bytes.decode("utf-8"),newline="")
            csv_reader=csv.DictReader(csv_text)
            machine_data=list(csv_reader)
            image_lookup={file.filename: file for file in image_files}
            inserted=0
            for machine in machine_data:
                image_filename=[name.strip()for name in machine.get("images","").split(";")if name.strip()]
                matched_files=[]
                for name in image_filename:
                    if name in image_lookup:
                        upload_file=image_lookup[name]
                        await upload_file.seek(0)
                        file_location=f"{UPLOAD_FILES}/{upload_file.filename}"
                        with open(file_location,"wb")as buffer:shutil.copyfileobj(upload_file.file,buffer)
                        await upload_file.seek(0)
                        matched_files.append(upload_file)
                    else:raise HTTPException(status_code=400,detail=f"Image {name} not found in upload.")
                try:
                    machine_data=MachineModel(
                        machine_name=machine["machine_name"],
                        machine_brand=machine["machine_brand"],
                        machine_price=float(machine["machine_price"]),
                        machine_desc=machine["machine_desc"],)
                except Exception as e:raise HTTPException(status_code=422,detail=f"Invalid data format: {str(e)}")
                await MachineServices.add_new_machine(machine_data,matched_files)
                inserted+=1
            return{"message":f"Successfully imported {inserted} machines."}
        except Exception as e:raise HTTPException(status_code=500,detail=str(e))
    @staticmethod
    async def search_machine_by_id(machine_id):
        """
        This function searches for a machine by its ID in the database.
        It checks if the machine exists and returns its information.
        Args:
            machine_id (str): The ID of the machine to be searched.
        Returns:
            dict: A dictionary containing the machine information.
        """
        existing_machine=await machines.find_one({"machine_id":machine_id})
        if not existing_machine:raise HTTPException(status_code=404,detail=f"Machine {machine_id} not found")
        else:existing_machine["_id"]=str(existing_machine["_id"]);return existing_machine
    @staticmethod
    async def buy_machine(machine_id):
        """
        This function calculates the final price of a machine based on its base price, tax, discount, and convenience fees.
        It retrieves the machine price from the database and applies the necessary calculations.
        Args:
            machine_id (str): The ID of the machine to be purchased.
        Returns:
            dict: A dictionary containing the base price, tax, discount, final price, and convenience fees.
        """
        price=machines.find_one({"machine_id":machine_id},{"_id": 0,"machine_price":1})
        base_price=price["machine_price"]
        tax=taxes.TaxCalculator.taxes(base_price)
        discount=discounts.DiscountCalculator.discounts(base_price)
        conv_fees=convenience_fees.ConvFeeCalculator.conv_fees(base_price)
        final_price=(base_price+tax+conv_fees)-discount 
        price_data={"base_price":base_price,"tax":tax,"discount":discount,"final_price":final_price,"convenience_fees":conv_fees}
        return (price_data)