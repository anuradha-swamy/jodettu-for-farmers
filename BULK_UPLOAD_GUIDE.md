# Machine Bulk Upload Guide

## CSV File Format

Your CSV file must have the following headers:

### Required Headers:
- `machine_name` - Name of the machine
- `machine_brand` - Brand/manufacturer
- `machine_price` - Price (must be a number > 0)
- `machine_desc` - Description

### Optional Headers:
- `images` - Image filenames separated by semicolon (;)

## CSV Template Example

```csv
machine_name,machine_brand,machine_price,machine_desc,images
John Deere 5055E,John Deere,25000.00,55 HP utility tractor perfect for small to medium farms,john_deere_5055e.jpg
Mahindra Arjun 555,Mahindra,18000.00,45 HP 2WD tractor with advanced features,mahindra_arjun.jpg
Tata Ace Mini Truck,Tata,4500.00,Compact mini truck for transporting agricultural goods,tata_ace.jpg
Sundar 500 Sprayer,Sundar,850.00,Agricultural sprayer for pesticide application,sundar_sprayer.jpg
New Holland 3630 TX Plus,New Holland,32000.00,55 HP 4WD tractor with advanced transmission system,new_holland_3630.jpg
```

## Image Files

- Image filenames in CSV must match the uploaded image file names exactly
- Multiple images can be separated by semicolons: `image1.jpg;image2.jpg;image3.jpg`
- Images are optional - if no images, leave the images column empty

## API Usage

### Endpoint:
```
POST /Jodettu/Machines/bulk-upload
```

### Required Files:
1. CSV file with machine data
2. Image files (optional)

### Authentication:
- Requires admin privileges (JWT token with admin role)

## Common Issues and Solutions

### 1. "Missing required CSV headers"
**Solution:** Ensure your CSV has all required headers: `machine_name`, `machine_brand`, `machine_price`, `machine_desc`

### 2. "Image file not found in upload"
**Solution:** Check that image filenames in CSV exactly match the uploaded file names (case-sensitive)

### 3. "machine_price must be a valid number"
**Solution:** Ensure price values are numbers (e.g., 25000.00) not text (e.g., "25,000" or "25k")

### 4. "File must be a CSV file"
**Solution:** Ensure your file has .csv extension and is properly formatted

### 5. "CSV file is empty"
**Solution:** Ensure your CSV has data rows and proper formatting

## Error Response Format

```json
{
  "message": "Successfully imported 3 out of 5 machines.",
  "total_rows": 5,
  "successful_imports": 3,
  "failed_imports": 2,
  "errors": [
    "Row 2: machine_price must be greater than 0",
    "Row 4: Image file 'missing.jpg' not found in upload"
  ],
  "warning": "Some machines could not be imported. Check errors list for details."
}
```

## Success Response Format

```json
{
  "message": "Successfully imported 5 out of 5 machines.",
  "total_rows": 5,
  "successful_imports": 5,
  "failed_imports": 0,
  "errors": null
}
```

## Testing

1. Use the provided template: `machines_bulk_upload_template.csv`
2. Prepare test images with matching filenames
3. Upload via Swagger UI or API client
4. Check response for any errors

## Notes

- Machine IDs are auto-generated (BRAND_XX format)
- Images are stored as base64 in the database
- The upload directory is created automatically if it doesn't exist
- All validation errors are reported with specific row numbers
