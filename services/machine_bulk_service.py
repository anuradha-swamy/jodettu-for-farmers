import base64, csv, shutil, io, os
from fastapi import HTTPException
from collections import OrderedDict
from general.database import machines
from models.machine_model import MachineModel
from services import taxes, discounts, convenience_fees

UPLOAD_FILES = "upload_files"

class MachineBulkService:
    @staticmethod
    async def bulk_upload_machines(csv_file, image_files):
        """
        Enhanced bulk upload with proper error handling and validation.
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
            required_headers = ['machine_name', 'machine_brand', 'machine_price', 'machine_desc']
            csv_headers = csv_reader.fieldnames or []
            
            missing_headers = [header for header in required_headers if header not in csv_headers]
            if missing_headers:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required CSV headers: {', '.join(missing_headers)}. "
                            f"Required headers: {', '.join(required_headers)}"
                )
            
            # Process machine data
            machine_rows = list(csv_reader)
            if not machine_rows:
                raise HTTPException(status_code=400, detail="CSV file is empty or contains no valid data")
            
            # Create image lookup
            image_lookup = {file.filename: file for file in image_files}
            inserted = 0
            errors = []
            
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FILES, exist_ok=True)
            
            for index, machine_row in enumerate(machine_rows, 1):
                try:
                    # Validate required fields
                    if not machine_row.get('machine_name', '').strip():
                        errors.append(f"Row {index}: machine_name is required")
                        continue
                    
                    if not machine_row.get('machine_brand', '').strip():
                        errors.append(f"Row {index}: machine_brand is required")
                        continue
                    
                    if not machine_row.get('machine_price', '').strip():
                        errors.append(f"Row {index}: machine_price is required")
                        continue
                    
                    # Validate price is a number
                    try:
                        price = float(machine_row['machine_price'])
                        if price <= 0:
                            errors.append(f"Row {index}: machine_price must be greater than 0")
                            continue
                    except ValueError:
                        errors.append(f"Row {index}: machine_price must be a valid number")
                        continue
                    
                    # Handle images
                    image_filenames = [name.strip() for name in machine_row.get("images", "").split(";") if name.strip()]
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
                    
                    # Create machine data object
                    machine_data_obj = MachineModel(
                        machine_name=machine_row['machine_name'].strip(),
                        machine_brand=machine_row['machine_brand'].strip(),
                        machine_price=float(machine_row['machine_price']),
                        machine_desc=machine_row.get('machine_desc', '').strip()
                    )
                    
                    # Add machine to database
                    await MachineBulkService._add_single_machine(machine_data_obj, matched_files)
                    inserted += 1
                    
                except HTTPException as e:
                    errors.append(f"Row {index}: {e.detail}")
                except Exception as e:
                    errors.append(f"Row {index}: Unexpected error - {str(e)}")
            
            # Return results
            result = {
                "message": f"Successfully imported {inserted} out of {len(machine_rows)} machines.",
                "total_rows": len(machine_rows),
                "successful_imports": inserted,
                "failed_imports": len(errors),
                "errors": errors if errors else None
            }
            
            if errors:
                result["warning"] = "Some machines could not be imported. Check errors list for details."
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")
    
    @staticmethod
    async def _add_single_machine(machine_data, files):
        """
        Helper method to add a single machine (copied from original service).
        """
        counter_doc = machines.find_one({"function": "ID_counter"})
        counter_value = counter_doc["count"] if counter_doc else 1
        data = machine_data.model_dump()
        prefix = data["machine_brand"][:3].upper()
        machine_id = f"{prefix}_{counter_value:02d}"
        ordered_data = OrderedDict([("machine_id", machine_id), *data.items()])
        
        file_data = []
        for file in files:
            file_content = await file.read()
            base64_string = base64.b64encode(file_content).decode("utf-8")
            file_data.append({"filename": file.filename, "data": base64_string})
        ordered_data["images"] = file_data
        
        machines.insert_one(ordered_data)
        machines.update_one({"function": "ID_counter"}, {"$inc": {"count": 1}}, upsert=True)
        
        return HTTPException(status_code=200, detail=f"Machine {ordered_data['machine_name']} added successfully.")
