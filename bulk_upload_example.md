# Correct way to call bulk-upload endpoint

## Problem
The 422 error occurs because you're sending strings instead of actual files.

## Solution
You need to send actual files, not file paths or strings.

### Example with curl:
```bash
curl -X POST "http://202.21.38.161:9090/Jodettu/Market/bulk-upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "csv_file=@path/to/your/feed_medicine_bulk_upload_template.csv" \
  -F "files=@path/to/image1.jpg" \
  -F "files=@path/to/image2.jpg"
```

### Example with JavaScript (Fetch):
```javascript
const formData = new FormData();
formData.append('csv_file', csvFileInput.files[0]);
formData.append('files', imageFile1);
formData.append('files', imageFile2);

fetch('http://202.21.38.161:9090/Jodettu/Market/bulk-upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Example with Python (requests):
```python
import requests

files = {
    'csv_file': open('feed_medicine_bulk_upload_template.csv', 'rb'),
    'files': open('image1.jpg', 'rb'),
    'files': open('image2.jpg', 'rb')
}

headers = {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
}

response = requests.post(
    'http://202.21.38.161:9090/Jodettu/Market/bulk-upload',
    files=files,
    headers=headers
)

print(response.json())
```

## Key Points:
1. Use `@` prefix in curl to specify file paths
2. Don't send file paths as strings - send actual file objects
3. Include proper JWT token in Authorization header
4. The endpoint expects: `csv_file` (single file) and `files` (multiple files)

## Endpoint Details:
- **URL**: `/Jodettu/Market/bulk-upload`
- **Method**: POST
- **Authentication**: Required (Admin user)
- **Parameters**:
  - `csv_file`: UploadFile (CSV template)
  - `files`: List[UploadFile] (Image files)
- **Content-Type**: multipart/form-data
