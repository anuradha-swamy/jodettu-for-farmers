#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from fastapi import UploadFile
from services.feed_medicine_services import MarketServices
from io import BytesIO

async def debug_bulk_upload():
    try:
        print("=== DEBUG BULK UPLOAD ===")
        
        # Create a mock CSV file
        csv_content = """type,name,brand,composition,animal,manufacturer,price,expiry_date
feed,Test Feed,Test Brand,Test Composition,Cow,Test Manu,25.50,2024-12-31
medicine,Test Med,Test Brand,Test Composition,Dog,Test Manu,15.75,2024-12-31"""
        
        # Create a mock UploadFile object
        mock_file = UploadFile(
            filename="test.csv",
            file=BytesIO(csv_content.encode('utf-8')),
            size=len(csv_content.encode('utf-8'))
        )
        
        print(f"Mock file created: {mock_file.filename}")
        print(f"Mock file size: {mock_file.size}")
        
        # Test the bulk import function
        print("\n--- Testing bulk_import_products ---")
        result = await MarketServices.bulk_import_products(mock_file, [])
        print(f"SUCCESS! Result: {result}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_bulk_upload())
