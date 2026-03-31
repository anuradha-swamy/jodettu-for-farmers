#!/usr/bin/env python3
"""
Test script to demonstrate the updated animal model with image support.
This shows how to use the new images field in your JSON structure.
"""

import json
from datetime import datetime
from models.animal_model import OwnAnimalBase, ImageFile, Vaccination

def create_sample_animal_with_images():
    """Create a sample animal with images to demonstrate the new structure."""
    
    # Sample image data (in real usage, this would be base64 encoded file content)
    sample_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    sample_pdf_data = "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKNSAwIG9iago8PC9UeXBlL1BhZ2UKL1BhcmVudCAyIDAgUgovUmVzb3VyY2VzPDwvRm9udDw8L0YxIDcgMCBSPj4+Ci9NZWRpYUJveFsgMCAwIDYxMiA3OTJdCi9Db250ZW50cyA4IDAgUj4+CmVuZG9iago2IDAgb2JqCjw8L0xlbmd0aCA0NAo+PgplbmRvYmoKNyAwIG9iago8PC9UeXBlL0ZvbnQKL1N1YnR5cGUvVHlwZTEKL0Jhc2VGb250L0hlbHZldGljYQo+PgplbmRvYmoKOCAwIG9iago8PC9MZW5ndGggNDQKPj4KZW5kb2JqCjIgMCBvYmoKPDwvVHlwZS9QYWdlcy9LaWRzWzMgMCBSXS9Db3VudCAxPj4KZW5kb2JqCjkgMCBvYmoKPDwvVHlwZS9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKMTAgMCBvYmoKPDwvUHJvZHVjZXIocHR0aXN0aWNzKQovQ3JlYXRpb25EYXRlKEQ6MjAyNjAzMjcxMzAyMjcrMDUnMDAnKQo+PgplbmRvYmoKeHJlZgowIDExCjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDA5OCAwMDAwMCBuIAowMDAwMDAwMTU4IDAwMDAwIG4gCjAwMDAwMDAyMTUgMDAwMDAgbiAKMDAwMDAwMDI4NiAwMDAwMCBuIAowMDAwMDAwMzQzIDAwMDAwIG4gCjAwMDAwMDAzOTggMDAwMDAgbiAKMDAwMDAwMDQ1NiAwMDAwMCBuIAowMDAwMDAwNDg1IDAwMDAwIG4gCjAwMDAwMDA1MTUgMDAwMDAgbiAKMDAwMDAwMDU0NSAwMDAwMCBuIAp0cmFpbGVyCjw8L1NpemUgMTEKL1Jvb3QgOSAwIFIKL0luZm8gMTAgMCBSCj4+CnN0YXJ0eHJlZgo1NjYKJSVFT0YK"

    # Create image objects
    images = [
        ImageFile(
            filename="cow_photo.jpg",
            data=sample_image_data,
            upload_date=datetime.now()
        ),
        ImageFile(
            filename="vaccination_cert.pdf",
            data=sample_pdf_data,
            upload_date=datetime.now()
        )
    ]
    
    # Create vaccination records
    vaccinations = [
        Vaccination(
            vaccination_name="Foot and Mouth Disease Vaccine",
            next_vaccination_date=datetime(2026, 4, 27, 8, 0, 0),
            vaccination_status="pending"
        ),
        Vaccination(
            vaccination_name="Rabies Vaccine",
            next_vaccination_date=datetime(2026, 5, 27, 8, 0, 0),
            vaccination_status="pending"
        )
    ]
    
    # Create the animal with all fields
    animal = OwnAnimalBase(
        own_animal_type="cow",
        own_animal_breed="Holstein",
        own_animal_name="Bessie",
        own_animal_age=4,
        own_animal_height=150.5,
        own_animal_weight=600.0,
        own_animal_last_vacc=datetime(2026, 3, 27, 8, 2, 27),
        own_animal_desc="Healthy dairy cow, good milk producer",
        images=images,  # New images field
        vaccinations=vaccinations,
        is_wishlisted=False
    )
    
    return animal

def main():
    """Main function to demonstrate the animal model with images."""
    
    print("🐄 Animal Model with Images - Demo")
    print("=" * 50)
    
    # Create sample animal
    animal = create_sample_animal_with_images()
    
    # Convert to JSON
    animal_json = animal.model_dump_json(indent=2)
    
    print("📋 Complete Animal JSON Structure with Images:")
    print(animal_json)
    
    print("\n" + "=" * 50)
    print("🔍 Key Points:")
    print("✅ Added 'images' field to OwnAnimalBase model")
    print("✅ Each image has: filename, data (base64), upload_date")
    print("✅ Supports multiple images and documents")
    print("✅ Backward compatible with existing data")
    print("✅ Works with your existing vaccination system")
    
    print("\n" + "=" * 50)
    print("📝 How to Use in Your API:")
    print("""
1. When adding/updating animals, include images in your JSON:
   {
     "...other_fields...": "...",
     "images": [
       {
         "filename": "photo.jpg",
         "data": "base64_encoded_content"
       }
     ]
   }

2. The frontend forms I created automatically handle:
   - File upload → Base64 conversion
   - Multiple file selection
   - Image preview and removal

3. Backend services already support image handling in:
   - animal_services.py (add_new_animal, update_animal)
   - animal_routes_fixed.py (endpoints with image support)
    """)

if __name__ == "__main__":
    main()
