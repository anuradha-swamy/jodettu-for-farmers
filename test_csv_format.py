#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.feed_medicine_services import MarketServices
from fastapi import UploadFile
from io import BytesIO

def test_csv_processing():
    try:
        print("=== TEST CSV PROCESSING ===")
        
        # Test with your actual CSV content (modify this to match your file)
        csv_content = """type,name,brand,composition,animal,manufacturer,price,expiry_date
animal_products_feed_medicine_combined"""
        
        print(f"CSV Headers: {csv_content.split()[0]}")
        print(f"CSV Content preview: {csv_content[:100]}...")
        
        # Test CSV reading
        import csv
        import io
        csv_bytes = csv_content.encode('utf-8')
        csv_text = io.StringIO(csv_bytes.decode("utf-8"), newline="")
        csv_reader = csv.DictReader(csv_text)
        
        print(f"\nCSV Headers found: {csv_reader.fieldnames}")
        
        for i, row in enumerate(csv_reader):
            print(f"Row {i+1}: {row}")
            if i >= 2:  # Only show first 3 rows
                break
        
        # Check required headers
        required_headers = ['type', 'name', 'brand', 'composition', 'animal', 'manufacturer', 'price', 'expiry_date']
        missing_headers = [h for h in required_headers if h not in (csv_reader.fieldnames or [])]
        
        if missing_headers:
            print(f"\n❌ MISSING HEADERS: {missing_headers}")
            print(f"✅ REQUIRED HEADERS: {required_headers}")
        else:
            print(f"\n✅ All required headers present!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_csv_processing()
