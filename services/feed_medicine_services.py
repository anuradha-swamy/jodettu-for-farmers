import base64,csv,shutil,io
from fastapi import HTTPException
from collections import OrderedDict
from datetime import datetime
from models.product_model import ProductModel
from general.database import market
from pymongo import ReturnDocument
from services import taxes,discounts,convenience_fees
from general.wishlist_settings import wishlist_service
UPLOAD_FILES="upload_files"

"""
This module defines the services for managing feed and medicine products.
"""

class MarketServices:
    @staticmethod
    def _infer_product_type(doc: dict) -> str:
        """
        Best-effort inference of product type for legacy records missing 'id'.
        """
        text = f"{doc.get('name', '')} {doc.get('composition', '')}".lower()
        if "feed" in text:
            return "feed"

        medicine_keywords = [
            "medicine", "syrup", "tonic", "injection", "spray", "dewormer",
            "antibiotic", "vaccine", "vitamin", "calcium", "ivermectin",
            "oxytetracycline", "albendazole"
        ]
        if any(keyword in text for keyword in medicine_keywords):
            return "medicine"

        # Fallback to medicine if unknown
        return "medicine"

    @staticmethod
    def _ensure_product_id(doc: dict) -> str:
        """
        Ensure legacy products have a stable 'id' (FEED_XX / MED_XX).
        """
        existing_id = doc.get("id")
        if existing_id:
            return existing_id

        product_type = MarketServices._infer_product_type(doc)
        counter_key = "feed_count" if product_type == "feed" else "med_count"
        prefix = "FEED" if product_type == "feed" else "MED"

        counter_doc = market.find_one_and_update(
            {"function": "ID_counter"},
            {"$inc": {counter_key: 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        counter_value = counter_doc.get(counter_key, 1)
        product_id = f"{prefix}_{counter_value:02d}"

        market.update_one(
            {"_id": doc["_id"]},
            {"$set": {"id": product_id, "product_type": product_type}}
        )

        return product_id
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
        return {"message": "Feed added successfully!"}
        
    @staticmethod   
    async def add_medicine(product_data,images):
        dict_data=product_data.model_dump()
        dict_data["expiry_date"]=dict_data["expiry_date"].isoformat()
        counter_doc=market.find_one({"function":"ID_counter"})
        counter_value=counter_doc["med_count"]if counter_doc else 1
        product_id=f"MED_{counter_value:02d}"
        ordered_data=OrderedDict([("id",product_id),*dict_data.items()])
        file_data=[]
        for image in images:
            file_content=await image.read()
            base64_string=base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename":image.filename,"data":base64_string})
        ordered_data["images"]=file_data
        market.insert_one(ordered_data)
        market.update_one({"function":"ID_counter"},{"$inc":{"med_count":1}},upsert=True)
        return {"message": "Medicine added successfully!"}
        
    @staticmethod 
    async def list_all_products():
        exclude_filter={"function":"ID_counter"}
        cursor=market.find()
        docs=list(cursor)
        products = []
        for doc in docs:
            if not all(doc.get(k)==v for k,v in exclude_filter.items()):
                product = {**doc, "_id": str(doc["_id"])}
                product["id"] = MarketServices._ensure_product_id(doc)
                products.append(product)
        return products

    @staticmethod
    async def list_all_products_with_wishlist(user_id):
        """
        Get all products with wishlist flags for the current user.
        """
        try:
            exclude_filter={"function":"ID_counter"}
            cursor=market.find()
            docs=list(cursor)
            
            # Get user's wishlist
            wishlist_data = wishlist_service.get_user_wishlist(user_id)
            wishlisted_products = set(wishlist_data.get("wishlisted_products", []))
            
            # Add wishlist flag to each product
            products_with_wishlist = []
            for doc in docs:
                if not all(doc.get(k)==v for k,v in exclude_filter.items()):
                    product = {**doc, "_id": str(doc["_id"])}
                    # Ensure id is always included in response (backfill if missing)
                    product["id"] = MarketServices._ensure_product_id(doc)
                    product["is_wishlisted"] = product.get("id") in wishlisted_products
                    products_with_wishlist.append(product)
            
            return products_with_wishlist
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve products: {str(e)}")

    @staticmethod
    async def search_products_by_name(product_name, user_id):
        """
        Search for feed and medicine products by name with wishlist flags.
        """
        try:
            # Case-insensitive search by name
            regex_pattern = f".*{product_name}.*"
            cursor = market.find({
                "name": {"$regex": regex_pattern, "$options": "i"},
                "function": {"$ne": "ID_counter"}
            })
            docs = list(cursor)
            
            # Get user's wishlist
            wishlist_data = wishlist_service.get_user_wishlist(user_id)
            wishlisted_products = set(wishlist_data.get("wishlisted_products", []))
            
            # Add wishlist flag to each product
            products_with_wishlist = []
            for doc in docs:
                product = {**doc, "_id": str(doc["_id"])}
                product["is_wishlisted"] = product.get("id") in wishlisted_products
                products_with_wishlist.append(product)
            
            return products_with_wishlist
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")

    @staticmethod
    async def search_feed_by_name(feed_name, user_id):
        """
        Search for feed products by name with wishlist flags.
        """
        try:
            # Case-insensitive search for feed products
            regex_pattern = f".*{feed_name}.*"
            cursor = market.find({
                "name": {"$regex": regex_pattern, "$options": "i"},
                "id": {"$regex": "^FEED_"},
                "function": {"$ne": "ID_counter"}
            })
            docs = list(cursor)
            
            # Get user's wishlist
            wishlist_data = wishlist_service.get_user_wishlist(user_id)
            wishlisted_products = set(wishlist_data.get("wishlisted_products", []))
            
            # Add wishlist flag to each product
            products_with_wishlist = []
            for doc in docs:
                product = {**doc, "_id": str(doc["_id"])}
                product["is_wishlisted"] = product.get("id") in wishlisted_products
                products_with_wishlist.append(product)
            
            return products_with_wishlist
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search feed: {str(e)}")

    @staticmethod
    async def search_medicine_by_name(medicine_name, user_id):
        """
        Search for medicine products by name with wishlist flags.
        """
        try:
            # Case-insensitive search for medicine products
            regex_pattern = f".*{medicine_name}.*"
            cursor = market.find({
                "name": {"$regex": regex_pattern, "$options": "i"},
                "id": {"$regex": "^MED_"},
                "function": {"$ne": "ID_counter"}
            })
            docs = list(cursor)
            
            # Get user's wishlist
            wishlist_data = wishlist_service.get_user_wishlist(user_id)
            wishlisted_products = set(wishlist_data.get("wishlisted_products", []))
            
            # Add wishlist flag to each product
            products_with_wishlist = []
            for doc in docs:
                product = {**doc, "_id": str(doc["_id"])}
                product["is_wishlisted"] = product.get("id") in wishlisted_products
                products_with_wishlist.append(product)
            
            return products_with_wishlist
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search medicine: {str(e)}")

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
        if not existing_product:raise HTTPException (status_code=404,detail=f"Feed {product_id} not found")
        else:
            result=market.update_one({"id":product_id},{"$set":dict_data})
            if result.modified_count:return {"message": f"Feed {product_id} updated successfully"}
            else:raise HTTPException(status_code=400,detail="No changes detected")

    @staticmethod
    async def update_medicine(product_id,product_data):
        dict_data=product_data.model_dump()
        dict_data["expiry_date"]=dict_data["expiry_date"].isoformat()
        existing_product=market.find_one({"id":product_id})
        if not existing_product:raise HTTPException (status_code=404,detail=f"Medicine {product_id} not found")
        else:
            result=market.update_one({"id":product_id},{"$set":dict_data})
            if result.modified_count:return {"message": f"Medicine {product_id} updated successfully"}
            else:raise HTTPException (status_code=400,detail="No changes detected")

    @staticmethod
    async def delete_product(product_id):
        existing_product=market.find_one({"id":product_id})
        if not existing_product:raise HTTPException(status_code=404,detail=f"Product {product_id} not found")
        else:market.delete_one({"id":product_id})
        return {"message": f"Product {product_id} deleted successfully"}

    @staticmethod
    async def buy_feed(product_id):
        price_doc=market.find_one({"id":product_id},{"_id":0,"price":1})
        if not price_doc: raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        base_price=float(price_doc["price"])
        tax=taxes.TaxCalculator.taxes(base_price)
        discount=discounts.DiscountCalculator.discounts(base_price)
        conv_fees=convenience_fees.ConvFeeCalculator.conv_fees(base_price)
        final_price=(base_price+tax+conv_fees)-discount 
        price_data={"base_price":base_price,"tax":tax,"discount":discount,"final_price":final_price,"convenience_fee":conv_fees}
        return(price_data)    

    @staticmethod
    async def buy_medicine(product_id):
        price_doc=market.find_one({"id":product_id},{"_id":0,"price":1})
        if not price_doc: raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        base_price=float(price_doc["price"])
        tax=taxes.TaxCalculator.taxes(base_price)
        discount=discounts.DiscountCalculator.discounts(base_price)
        conv_fees=convenience_fees.ConvFeeCalculator.conv_fees(base_price)
        final_price=(base_price+tax+conv_fees)-discount 
        price_data={"base_price":base_price,"tax":tax,"discount":discount,"final_price":final_price,"convenience_fee":conv_fees}
        return(price_data)

    @staticmethod
    async def bulk_import_products(csv_file, image_files):
        try:
            csv_bytes = await csv_file.read()
            csv_text = io.StringIO(csv_bytes.decode("utf-8"), newline="")
            csv_reader = csv.DictReader(csv_text)
            
            products_to_insert = []
            image_lookup = {file.filename: file for file in image_files}

            for row in csv_reader:
                product_type = row.get("type", "").lower()
                if product_type not in ["feed", "medicine"]:
                    continue # Or raise an error for invalid types

                # Validate and model the data
                product_model = ProductModel(
                    name=row["name"],
                    brand=row["brand"],
                    composition=row["composition"],
                    animal=row["animal"],
                    manufacturer=row["manufacturer"],
                    price=float(row["price"]),
                    expiry_date=datetime.fromisoformat(row["expiry_date"])
                )
                
                dict_data = product_model.model_dump()
                dict_data["expiry_date"] = dict_data["expiry_date"].isoformat()

                # Handle images
                image_filenames = [name.strip() for name in row.get("images", "").split(";") if name.strip()]
                file_data = []
                for name in image_filenames:
                    if name in image_lookup:
                        upload_file = image_lookup[name]
                        file_content = await upload_file.read()
                        base64_string = base64.b64encode(file_content).decode("utf-8")
                        file_data.append({"filename": name, "data": base64_string})
                        upload_file.seek(0) # Reset pointer
                
                dict_data["images"] = file_data
                
                # Generate product id based on type
                counter_doc = market.find_one({"function":"ID_counter"}) or {}
                if product_type == "feed":
                    counter_value = counter_doc.get("feed_count", 1)
                    product_id = f"FEED_{counter_value:02d}"
                    market.update_one({"function":"ID_counter"},{"$inc":{"feed_count":1}},upsert=True)
                else:
                    counter_value = counter_doc.get("med_count", 1)
                    product_id = f"MED_{counter_value:02d}"
                    market.update_one({"function":"ID_counter"},{"$inc":{"med_count":1}},upsert=True)

                dict_data["id"] = product_id
                dict_data["product_type"] = product_type

                # Add to list for bulk insertion
                products_to_insert.append(dict_data)

            if not products_to_insert:
                return {"message": "No valid products found to import."}

            # Bulk insert into the database
            market.insert_many(products_to_insert)
            
            return {"message": f"Successfully imported {len(products_to_insert)} products."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred during bulk import: {str(e)}")
