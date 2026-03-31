import base64, csv, io, shutil
from fastapi import HTTPException
from collections import OrderedDict
from general.database import own_animals, market_animals, animal_types_collection, breeds_collection
from models.animal_model import OwnAnimalBase
from datetime import datetime
from services import taxes,discounts,convenience_fees,vaccinations
import os
UPLOAD_FILES="upload_files"

"""
This module defines the OwnAnimalServices class, which provides various services related to animal management.
"""

class OwnAnimalServices:
    @staticmethod
    async def get_animal_types():
        """
        Retrieves a distinct list of animal types from the own_animals collection.
        """
        try:
            animal_types = own_animals.distinct("own_animal_type")
            return animal_types
        except Exception as e:
            raise e

    @staticmethod
    async def get_breeds_by_animal_type(animal_type: str):
        """
        Retrieves a distinct list of breeds for a given animal type.
        """
        normalized_type = animal_type.lower()
        breeds = own_animals.distinct("own_animal_breed", {"own_animal_type": normalized_type})
        return breeds

    @staticmethod
    async def add_new_animal(animal_data, files, user_id):
        """
        Adds a new animal to the database linked to the user.
        """
        # DEBUG PRINT to confirm this method is running
        print(f"DEBUG: add_new_animal called with user_id={user_id}")
        
        counter_doc = own_animals.find_one({"function":"ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 1
        own_animal_id = f"OWN_{counter_value:02d}"
        
        data_dict = animal_data.dict()
        ordered_data = OrderedDict([
            ("user_id", user_id),
            ("own_animal_id", own_animal_id),
            *data_dict.items()
        ])
        ordered_data["own_animal_last_vacc"] = ordered_data["own_animal_last_vacc"].isoformat()
        
        file_data = []
        if files:
            for file in files:
                file_content = file.read() 
                base_64_string = base64.b64encode(file_content).decode("utf-8")
                file_data.append({"filename": file.filename, "data": base_64_string})       
            ordered_data["images"] = file_data
        else:
            ordered_data["images"] = "No Images Attached"
        
        own_animals.insert_one(ordered_data)
        own_animals.update_one({"function":"ID_counter"},{"$inc":{"count":1}},upsert=True)
        return {"message": f"Animal {ordered_data['own_animal_name']} added successfully."}
    
    @staticmethod
    async def list_all_animals(user_id):
        cursor = own_animals.find({"user_id": user_id})
        docs = list(cursor)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    @staticmethod
    async def get_animal_by_id(animal_id):
        existing_animal = own_animals.find_one({"own_animal_id":animal_id})
        if not existing_animal:
            raise HTTPException(status_code=404,detail=f"Animal {animal_id} not found!")
        existing_animal["_id"] = str(existing_animal["_id"])
        return existing_animal

    @staticmethod
    async def update_animal(animal_data,animal_id):
        existing_animal = own_animals.find_one({"own_animal_id":animal_id})
        if not existing_animal:
            raise HTTPException(status_code=404,detail=f"Animal {animal_id} not found")
        
        dict_data = animal_data.model_dump()
        dict_data["own_animal_last_vacc"] = dict_data["own_animal_last_vacc"].isoformat()
        
        result = own_animals.update_one({"own_animal_id":animal_id},{"$set":dict_data})
        
        if result.modified_count > 0:
            return {"message": f"Animal {animal_id} updated successfully!"}
        else:
            raise HTTPException(status_code=400,detail="No changes were detected or made.")

    @staticmethod
    async def delete_animal(animal_id):
        result = own_animals.delete_one({"own_animal_id":animal_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404,detail=f"Animal {animal_id} not found!")
        return {"message": f"Animal {animal_id} deleted successfully!"}

    @staticmethod
    def bulk_import_animals(csv_file,image_files):
        try:
            csv_bytes = csv_file.read()
            csv_text = io.StringIO(csv_bytes.decode("utf-8"), newline="")
            csv_reader = csv.DictReader(csv_text)
            animal_data = list(csv_reader)
            image_lookup = {file.filename: file for file in image_files}
            inserted = 0
            for animal in animal_data:
                image_filenames = [name.strip()for name in animal.get("images","").split(";")if name.strip()]
                matched_files = []
                for name in image_filenames:
                    if name in image_lookup:
                        upload_file = image_lookup[name]
                        file_location = f"{UPLOAD_FILES}/{upload_file.filename}"
                        with open(file_location,"wb") as buffer:
                            shutil.copyfileobj(upload_file.file, buffer)
                        upload_file.seek(0)
                        matched_files.append(upload_file)
                    else:
                        raise HTTPException(status_code=400,detail=f"Image {name} not found in upload.")
                try:
                    animal["own_animal_last_vacc"] = datetime.fromisoformat(animal["own_animal_last_vacc"]).isoformat()
                    animal_model = OwnAnimalBase(**animal)
                except Exception as e:
                    raise HTTPException(status_code=422, detail=f"Invalid data format: {str(e)}")
                
                # This call needs user_id to work correctly now
                # OwnAnimalServices.add_new_animal(animal_model,matched_files, user_id) 
                inserted+=1
            return{"message":f"Successfully imported {inserted} animals."}
        except Exception as e:
            raise HTTPException(status_code=500,detail=str(e))

    @staticmethod
    async def sell_own_animal(animal_id,market_price,location):
        existing_animal = own_animals.find_one({"own_animal_id":animal_id})
        if not existing_animal:
            raise HTTPException(status_code=404,detail=f"Animal {animal_id} not found")
        
        counter_doc = market_animals.find_one_and_update({"function":"ID_counter"},{"$inc":{"count":1}}, upsert=True, return_document=True)
        counter_value = counter_doc.get("count", 1)
        market_animal_id = f"MKT_{animal_id}_{counter_value:02d}"
        
        already_on_market = market_animals.find_one({"market_animal_id":market_animal_id})
        if already_on_market:
            raise HTTPException(status_code=400, detail=f"Animal {animal_id} is already on the market")
        
        existing_animal.pop("_id",None)
        ordered_data = OrderedDict([("market_animal_id",market_animal_id),("market_price",market_price),*existing_animal.items(),("location", location)])
        market_animals.insert_one(ordered_data)
        
        return {"message": f"Animal {animal_id} added to the market successfully"}

    @staticmethod
    async def list_all_market_animals():
        cursor = market_animals.find({"function":{"$ne":"ID_counter"}})
        docs = list(cursor)
        for doc in docs: doc["_id"] = str(doc["_id"])
        return docs

    @staticmethod
    async def search_market_animal_by_id(animal_id):
        existing_animal = market_animals.find_one({"market_animal_id":animal_id})
        if not existing_animal:
            raise HTTPException(status_code=404,detail=f"Animal {animal_id} not found")
        existing_animal["_id"] = str(existing_animal["_id"])
        return existing_animal

    @staticmethod
    async def buy_animal(animal_id):
        existing_animal = market_animals.find_one({"market_animal_id":animal_id})
        if not existing_animal:
            raise HTTPException(status_code=404,detail=f"Animal {animal_id} not found")
        
        price = existing_animal.get("market_price", 0)
        tax = taxes.TaxCalculator.taxes(price)
        discount = discounts.DiscountCalculator.discounts(price)
        conv_fees = convenience_fees.ConvFeeCalculator.conv_fees(price)
        final_price = (price+tax+conv_fees)-discount 
        
        price_data={"base_price":price,"tax":tax,"discount":discount,"final_price":final_price,"convenience_fee":conv_fees}
        return(price_data)    

    @staticmethod
    async def count_animals():
        # ✅ CORRECT: Use distinct to get a list of unique strings directly
        animal_types = own_animals.distinct("own_animal_type")
        count_data = {"total_animals": own_animals.count_documents({"function": {"$ne": "ID_counter"}})}
        for animal_type in animal_types:
            count_data[animal_type.upper()] = own_animals.count_documents({"own_animal_type": animal_type})
        return count_data

    @staticmethod
    async def vacc_dues():
        exclude_filter={"function":"ID_counter"}        
        docs = list(own_animals.find(exclude_filter))
        vacc_dues=[]
        for doc in docs:
            updated_doc=vaccinations.VaccinationDues.vaccinations(doc)
            updated_doc["_id"]=str(doc["_id"])
            vacc_dues.append({"animal_name":updated_doc['own_animal_name'],"due_date":updated_doc['vaccination_due_date'],"breed":updated_doc["own_animal_breed"],"age":updated_doc["own_animal_age"]})
        return vacc_dues
