import base64,csv,shutil,io
from fastapi import HTTPException
from collections import OrderedDict
from datetime import datetime
from models.product_model import ProductModel
from general.database import market
from services import taxes,discounts,convenience_fees
UPLOAD_FILES="upload_files"

"""
This module defines enhanced services for managing feed and medicine products.
"""

class MarketServices:
    @staticmethod
    async def add_feed(product_data,images):
        dict_data=product_data.model_dump()
        dict_data["expiry_date"]=dict_data["expiry_date"].isoformat()
        counter_doc=market.find_one({"function":"ID_counter"})
        counter_value=counter_doc["feed_count"]if counter_doc else 1
        product_id=f"FEED_{counter_value:02d}"
        ordered_data=OrderedDict([("id",product_id),*dict_data.items()])
        file_data=[]
        for image in images:
            file_content=await image.read()
            base64_string=base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename":image.filename,"data":base64_string})
        ordered_data["images"]=file_data
        market.insert_one(ordered_data)
        market.update_one({"function":"ID_counter"},{"$inc":{"feed_count":1}},upsert=True)
        return HTTPException(status_code=200,detail=f"Feed {ordered_data['name']} added successfully.")

    @staticmethod
    async def add_medicine(product_data,images):
        dict_data=product_data.model_dump()
        dict_data["expiry_date"]=dict_data["expiry_date"].isoformat()
        counter_doc=market.find_one({"function":"ID_counter"})
        counter_value=counter_doc["medicine_count"]if counter_doc else 1
        product_id=f"MED_{counter_value:02d}"
        ordered_data=OrderedDict([("id",product_id),*dict_data.items()])
        file_data=[]
        for image in images:
            file_content=await image.read()
            base64_string=base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename":image.filename,"data":base64_string})
        ordered_data["images"]=file_data
        market.insert_one(ordered_data)
        market.update_one({"function":"ID_counter"},{"$inc":{"medicine_count":1}},upsert=True)
        return HTTPException(status_code=200,detail=f"Medicine {ordered_data['name']} added successfully.")

    @staticmethod 
    async def list_all_products():
        """
        Lists all products with type classification.
        """
        exclude_filter={"function":"ID_counter"}
        cursor=market.find()
        docs=list(cursor)
        
        # Add product type to each document
        formatted_docs = []
        for doc in docs:
            if not all(doc.get(k)==v for k,v in exclude_filter.items()):
                # Determine product type based on ID prefix
                doc_id = doc.get("id", "")
                if doc_id.startswith("FEED_"):
                    product_type = "feed"
                elif doc_id.startswith("MED_"):
                    product_type = "medicine"
                else:
                    product_type = "unknown"
                
                formatted_doc = {
                    **doc,
                    "_id": str(doc["_id"]),
                    "type": product_type
                }
                formatted_docs.append(formatted_doc)
        
        return formatted_docs

    @staticmethod
    async def list_feeds_only():
        """
        Lists only feed products.
        """
        exclude_filter={"function":"ID_counter"}
        cursor=market.find({"id": {"$regex": "^FEED_"}})
        docs=list(cursor)
        return[{**doc,"_id":str(doc["_id"]),"type":"feed"}for doc in docs]

    @staticmethod
    async def list_medicines_only():
        """
        Lists only medicine products.
        """
        exclude_filter={"function":"ID_counter"}
        cursor=market.find({"id": {"$regex": "^MED_"}})
        docs=list(cursor)
        return[{**doc,"_id":str(doc["_id"]),"type":"medicine"}for doc in docs]

    @staticmethod
    async def search_product(product_id):
        existing_product=market.find_one({"id":product_id})
        if not existing_product:raise HTTPException(status_code=404,detail=f"Product {product_id} not found")
        else:existing_product["_id"]=str(existing_product["_id"])
        return existing_product

    @staticmethod
    async def update_feed(product_id,product_data):
        dict_data=product_data.model_dump()
        dict_data["expiry_date"]=dict_data["expiry_date"].isoformat()
        existing_product=market.find_one({"id":product_id})
        if not existing_product:raise HTTPException(status_code=404,detail=f"Feed {product_id} not found")
        
        # Preserve existing images if not provided
        if "images" not in dict_data or dict_data["images"] is None:
            dict_data["images"] = existing_product.get("images", [])
        
        result=market.update_one(
            {"id":product_id},
            {"$set":dict_data}
        )
        if result.modified_count:return {"message":f"Feed {product_id} updated successfully!"}
        raise HTTPException(400,"No changes detected")

    @staticmethod
    async def update_medicine(product_id,product_data):
        dict_data=product_data.model_dump()
        dict_data["expiry_date"]=dict_data["expiry_date"].isoformat()
        existing_product=market.find_one({"id":product_id})
        if not existing_product:raise HTTPException(status_code=404,detail=f"Medicine {product_id} not found")
        
        # Preserve existing images if not provided
        if "images" not in dict_data or dict_data["images"] is None:
            dict_data["images"] = existing_product.get("images", [])
        
        result=market.update_one(
            {"id":product_id},
            {"$set":dict_data}
        )
        if result.modified_count:return {"message":f"Medicine {product_id} updated successfully!"}
        raise HTTPException(400,"No changes detected")

    @staticmethod
    async def delete_product(product_id):
        existing_product=market.find_one({"id":product_id})
        if not existing_product:raise HTTPException(status_code=404,detail=f"Product {product_id} not found")
        result=market.delete_one({"id":product_id})
        if result.deleted_count==0:raise HTTPException(status_code=404,detail=f"Product {product_id} not found")
        return {"message":f"Product {product_id} deleted successfully"}

    @staticmethod
    async def buy_feed(product_id):
        price=market.find_one({"id":product_id},{"_id":0,"price":1})
        base_price=price["price"]
        tax=taxes.TaxCalculator.taxes(base_price)
        discount=discounts.DiscountCalculator.discounts(base_price)
        fee=convenience_fees.ConvFeeCalculator.conv_fees(base_price)
        return {
            "base_price":base_price,
            "tax":tax,
            "discount":discount,
            "convenience_fee":fee,
            "final_price":base_price+tax+fee-discount
        }

    @staticmethod
    async def buy_medicine(product_id):
        price=market.find_one({"id":product_id},{"_id":0,"price":1})
        base_price=price["price"]
        tax=taxes.TaxCalculator.taxes(base_price)
        discount=discounts.DiscountCalculator.discounts(base_price)
        fee=convenience_fees.ConvFeeCalculator.conv_fees(base_price)
        return {
            "base_price":base_price,
            "tax":tax,
            "discount":discount,
            "convenience_fee":fee,
            "final_price":base_price+tax+fee-discount
        }
