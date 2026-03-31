import base64,csv,shutil,io,os
from fastapi import HTTPException
from collections import OrderedDict
from datetime import datetime
from models.product_model import ProductModel
from general.database import market
from services import taxes,discounts,convenience_fees
UPLOAD_FILES="upload_files"

class FeedMedicineBulkService:
    @staticmethod
    async def bulk_import_products(csv_file, image_files):
        """
        Enhanced bulk upload for feed and medicine products with type detection.
        """
        try:
            # Validate CSV file
            if not csv_file.filename.endswith('.csv'):
                raise HTTPException(status_code=400, detail="File must be a CSV file")
            
            # Read CSV content
            csv_bytes = await csv_file.read()
            csv_text = io.StringIO(csv_bytes.decode("utf-8"), newline="")
            csv_reader = csv.DictReader(csv_text)
            
            # Validate CSV headers
            required_headers = ['name', 'brand', 'composition', 'animal', 'manufacturer', 'price', 'expiry_date']
            csv_headers = csv_reader.fieldnames or []
            
            missing_headers = [header for header in required_headers if header not in csv_headers]
            if missing_headers:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required CSV headers: {', '.join(missing_headers)}. "
                            f"Required headers: {', '.join(required_headers)}"
                )
            
            # Process product data
            product_rows = list(csv_reader)
            if not product_rows:
                raise HTTPException(status_code=400, detail="CSV file is empty or contains no valid data")
            
            # Create image lookup
            image_lookup = {file.filename: file for file in image_files}
            inserted = 0
            errors = []
            
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FILES, exist_ok=True)
            
            for index, product_row in enumerate(product_rows, 1):
                try:
                    # Validate required fields
                    if not product_row.get('name', '').strip():
                        errors.append(f"Row {index}: name is required")
                        continue
                    
                    if not product_row.get('brand', '').strip():
                        errors.append(f"Row {index}: brand is required")
                        continue
                    
                    if not product_row.get('composition', '').strip():
                        errors.append(f"Row {index}: composition is required")
                        continue
                    
                    if not product_row.get('animal', '').strip():
                        errors.append(f"Row {index}: animal is required")
                        continue
                    
                    if not product_row.get('manufacturer', '').strip():
                        errors.append(f"Row {index}: manufacturer is required")
                        continue
                    
                    if not product_row.get('price', '').strip():
                        errors.append(f"Row {index}: price is required")
                        continue
                    
                    if not product_row.get('expiry_date', '').strip():
                        errors.append(f"Row {index}: expiry_date is required")
                        continue
                    
                    # Validate price is a number
                    try:
                        price = float(product_row['price'])
                        if price <= 0:
                            errors.append(f"Row {index}: price must be greater than 0")
                            continue
                    except ValueError:
                        errors.append(f"Row {index}: price must be a valid number")
                        continue
                    
                    # Validate expiry date
                    try:
                        expiry_date = datetime.fromisoformat(product_row['expiry_date'].strip())
                    except ValueError:
                        errors.append(f"Row {index}: expiry_date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
                        continue
                    
                    # Handle images
                    image_filenames = [name.strip() for name in product_row.get("images", "").split(";") if name.strip()]
                    matched_files = []
                    
                    for name in image_filenames:
                        if name in image_lookup:
                            upload_file = image_lookup[name]
                            await upload_file.seek(0)
                            file_location = f"{UPLOAD_FILES}/{upload_file.filename}"
                            with open(file_location, "wb") as buffer:
                                shutil.copyfileobj(upload_file.file, buffer)
                            await upload_file.seek(0)
                            matched_files.append(upload_file)
                        else:
                            errors.append(f"Row {index}: Image file '{name}' not found in upload")
                    
                    # Create product data object
                    product_data_obj = ProductModel(
                        name=product_row['name'].strip(),
                        brand=product_row['brand'].strip(),
                        composition=product_row['composition'].strip(),
                        animal=product_row['animal'].strip(),
                        manufacturer=product_row['manufacturer'].strip(),
                        price=float(product_row['price']),
                        expiry_date=expiry_date
                    )
                    
                    # Determine product type based on name or brand
                    product_name_lower = product_row['name'].lower()
                    product_brand_lower = product_row['brand'].lower()
                    
                    if any(keyword in product_name_lower or keyword in product_brand_lower 
                           for keyword in ['feed', 'fodder', 'nutrition', 'supplement']):
                        # Add as feed
                        FeedMedicineBulkService._add_feed_product(product_data_obj, matched_files)
                    else:
                        # Add as medicine
                        FeedMedicineBulkService._add_medicine_product(product_data_obj, matched_files)
                    
                    inserted += 1
                    
                except HTTPException as e:
                    errors.append(f"Row {index}: {e.detail}")
                except Exception as e:
                    errors.append(f"Row {index}: Unexpected error - {str(e)}")
            
            # Return results
            result = {
                "message": f"Successfully imported {inserted} out of {len(product_rows)} products.",
                "total_rows": len(product_rows),
                "successful_imports": inserted,
                "failed_imports": len(errors),
                "errors": errors if errors else None
            }
            
            if errors:
                result["warning"] = "Some products could not be imported. Check errors list for details."
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")

    @staticmethod
    def _add_feed_product(product_data, images):
        """Helper method to add feed product"""
        dict_data = product_data.model_dump()
        dict_data["expiry_date"] = dict_data["expiry_date"].isoformat()
        counter_doc = market.find_one({"function": "ID_counter"})
        counter_value = counter_doc["feed_count"] if counter_doc else 1
        product_id = f"FEED_{counter_value:02d}"
        ordered_data = OrderedDict([("id", product_id), *dict_data.items()])
        
        file_data = []
        for image in images:
            file_content = image.read()
            base64_string = base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename": image.filename, "data": base64_string})
        ordered_data["images"] = file_data
        
        market.insert_one(ordered_data)
        market.update_one({"function": "ID_counter"}, {"$inc": {"feed_count": 1}}, upsert=True)

    @staticmethod
    def _add_medicine_product(product_data, images):
        """Helper method to add medicine product"""
        dict_data = product_data.model_dump()
        dict_data["expiry_date"] = dict_data["expiry_date"].isoformat()
        counter_doc = market.find_one({"function": "ID_counter"})
        counter_value = counter_doc["medicine_count"] if counter_doc else 1
        product_id = f"MED_{counter_value:02d}"
        ordered_data = OrderedDict([("id", product_id), *dict_data.items()])
        
        file_data = []
        for image in images:
            file_content = image.read()
            base64_string = base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename": image.filename, "data": base64_string})
        ordered_data["images"] = file_data
        
        market.insert_one(ordered_data)
        market.update_one({"function": "ID_counter"}, {"$inc": {"medicine_count": 1}}, upsert=True)
