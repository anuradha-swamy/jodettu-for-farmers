from fastapi import HTTPException,APIRouter,Form,UploadFile,File,Depends
from general.security import Security
from services.feed_medicine_services_enhanced import MarketServices
from services.feed_medicine_bulk_service import FeedMedicineBulkService
from models.product_model import ProductModel
from datetime import datetime
from typing import Optional, List
service=MarketServices()
router=APIRouter()

"""
This module defines enhanced routes for feed and medicine-related operations.
"""

@router.post("/add-feed", operation_id="add_feed")
async def add_new_feed(
    feed_name:str=Form(...),
    feed_brand:str=Form(...),
    feed_composition:str=Form(...),
    feed_animal:str=Form(...),
    feed_manufacturer:str=Form(...),
    feed_price:float=Form(...),
    feed_expiry_date:datetime=Form(...),
    files:list[UploadFile]=File(...),
    current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    try:
        product_data=ProductModel(
            name=feed_name,
            brand=feed_brand,
            composition=feed_composition,
            animal=feed_animal,
            manufacturer=feed_manufacturer,
            price=feed_price,
            expiry_date=feed_expiry_date)
        return await service.add_feed(product_data, files)
    except Exception as e:raise HTTPException(status_code=400,detail=f"This is a flag raised{e}")        

@router.post("/add-medicine", operation_id="add_medicine")
async def add_new_medicine(
    medicine_name:str=Form(...),
    medicine_brand:str=Form(...),
    medicine_composition:str=Form(...),
    medicine_animal:str=Form(...),
    medicine_manufacturer:str=Form(...),
    medicine_price:float=Form(...),
    medicine_expiry_date:datetime=Form(...),
    files:list[UploadFile]=File(...),
    current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    try:
        product_data=ProductModel(
                name=medicine_name,
                brand=medicine_brand,                
                composition=medicine_composition,
                animal=medicine_animal,
                manufacturer=medicine_manufacturer,
                price=medicine_price,
                expiry_date=medicine_expiry_date)
            return await service.add_medicine(product_data,files)
        except Exception as e:raise HTTPException(status_code=400,detail=str(e))        

@router.get("/all-products", operation_id="list_all_products")
async def list_all_products(current_user:dict=Depends(Security.get_current_user)):
    return await service.list_all_products()

@router.get("/feeds-only", operation_id="list_feeds_only")
async def list_feeds_only(current_user:dict=Depends(Security.get_current_user)):
    """
    Lists only feed products with type classification.
    """
    return await service.list_feeds_only()

@router.get("/medicines-only", operation_id="list_medicines_only")
async def list_medicines_only(current_user:dict=Depends(Security.get_current_user)):
    """
    Lists only medicine products with type classification.
    """
    return await service.list_medicines_only()

@router.put("/update-feed/{feed_id}", operation_id="update_feed")
async def update_feed(feed_data:ProductModel,feed_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.update_feed(feed_id,feed_data)

@router.put("/update-medicine/{medicine_id}", operation_id="update_medicine")
async def update_medicine(medicine_data:ProductModel,medicine_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.update_medicine(medicine_id,medicine_data)

@router.delete("/delete-feed/{feed_id}", operation_id="delete_feed")
async def delete_feed(product_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.delete_product(product_id)

@router.delete("/delete-medicine/{medicine_id}", operation_id="delete_medicine")
async def delete_medicine(product_id:str,current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await service.delete_product(product_id)

@router.post("/buy-feed/{feed_id}", operation_id="buy_feed")
async def buy_feed(feed_id:str,current_user:dict=Depends(Security.get_current_user)):
    return await service.buy_feed(feed_id)

@router.post("/buy-medicine/{medicine_id}", operation_id="buy_medicine")
async def buy_medicine(medicine_id:str,current_user:dict=Depends(Security.get_current_user)):
    return await service.buy_medicine(medicine_id)

@router.get("/search/{product_id}", operation_id="search_product")
async def search_product(product_id:str,current_user:dict=Depends(Security.get_current_user)):
    return await service.search_product(product_id)

@router.post("/bulk-upload", operation_id="bulk_upload_products")
async def bulk_upload(
    csv_file:UploadFile=File(...),
    files:Optional[List[UploadFile]]=File(None),
    current_user:dict=Depends(Security.get_current_admin_user)): # Protected: Admin only
    return await FeedMedicineBulkService.bulk_import_products(csv_file,files)
