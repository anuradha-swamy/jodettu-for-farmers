# Animal Breed Classification

This feature allows users to upload images of animals and get predictions about the animal type and breed using a deep learning model.

## Features

- Upload animal images for classification
- Get predictions for animal type and breed
- Confidence scores for predictions
- Support for multiple animal types (dogs, cats, birds, etc.)
- Image validation and preprocessing

## API Endpoints

### Classify Animal

- **URL**: `POST /api/v1/animals/classify`
- **Description**: Upload an image to classify the animal and its breed
- **Request**: Form-data with an image file
- **Response**: 
  ```json
  {
    "success": true,
    "data": {
      "animal": "dog",
      "breed": "Beagle",
      "confidence": 0.9567,
      "original_filename": "my_dog.jpg"
    }
  }
  ```

### Health Check

- **URL**: `GET /api/v1/animals/health`
- **Description**: Check if the animal classification service is running
- **Response**:
  ```json
  {
    "status": "healthy",
    "model_loaded": true
  }
  ```

## How It Works

1. The system accepts image uploads through the `/classify` endpoint
2. The image is validated for size and format
3. The image is preprocessed (resized, normalized) for the model
4. A pre-trained ResNet50 model is used to predict the animal and breed
5. The prediction is returned with a confidence score

## Requirements

- Python 3.8+
- PyTorch
- torchvision
- Pillow
- FastAPI
- uvicorn

## Setup

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Access the API at `http://localhost:8000`

## Example Usage

Using `curl`:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/animals/classify' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@path/to/your/image.jpg;type=image/jpeg'
```

Using Python with `requests`:

```python
import requests

url = "http://localhost:8000/api/v1/animals/classify"
files = {"file": open("path/to/your/image.jpg", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

## Error Handling

The API returns appropriate HTTP status codes and error messages for various scenarios:

- `400 Bad Request`: Invalid file type or corrupted image
- `413 Payload Too Large`: Image file is too large (default max 10MB)
- `500 Internal Server Error`: Server-side error during processing

## Notes

- The model is pre-trained on common animal breeds but may not recognize all possible breeds
- For best results, use clear, well-lit images of animals
- The confidence threshold is set to 0.5 by default
