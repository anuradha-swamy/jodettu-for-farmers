# AI/ML Services Integration

This document describes the AI/ML services integrated into the Jodettu application.

## Integrated Services

### 1. YOLOv8 Object Detection
- **Purpose**: Real-time object detection in images
- **Service File**: `services/yolo_service.py`
- **Features**:
  - General object detection
  - Animal-specific detection
  - Bounding box coordinates
  - Confidence scores

### 2. ResNet50 Image Classification
- **Purpose**: Image classification using pre-trained ResNet50
- **Service File**: `services/resnet_service.py`
- **Features**:
  - General image classification
  - Animal-specific classification
  - Top-5 predictions with confidence scores
  - ImageNet categories

### 3. OpenStreetMap Location Services
- **Purpose**: Geocoding, reverse geocoding, and location-based services
- **Service File**: `services/location_service.py`
- **Features**:
  - Address to coordinates conversion
  - Coordinates to address conversion
  - Nearby places search
  - Distance calculation
  - Interactive map creation
  - Route planning

### 4. IndicTrans2 Translation
- **Purpose**: Multi-language translation for Indian languages
- **Service File**: `services/translation_service.py`
- **Features**:
  - English ↔ Indian languages translation
  - Batch translation
  - Language detection
  - Support for 13 Indian languages
  - Multi-language translation

## API Endpoints

### AI/ML Services (`/Jodettu/ai/`)

#### Object Detection
- `POST /Jodettu/ai/detect-objects` - Detect objects in image
- `POST /Jodettu/ai/detect-animals` - Detect animals in image

#### Image Classification
- `POST /Jodettu/ai/classify-image` - Classify image
- `POST /Jodettu/ai/classify-animals` - Classify animals in image

#### Combined Analysis
- `POST /Jodettu/ai/analyze-image` - Comprehensive image analysis

### Location Services (`/Jodettu/location/`)

#### Geocoding
- `POST /Jodettu/location/geocode` - Address to coordinates
- `POST /Jodettu/location/reverse-geocode` - Coordinates to address

#### Places & Routes
- `POST /Jodettu/location/nearby-places` - Find nearby places
- `POST /Jodettu/location/calculate-distance` - Calculate distance
- `POST /Jodettu/location/create-map` - Create interactive map
- `POST /Jodettu/location/get-route` - Get route between points

### Translation Services (`/Jodettu/translation/`)

#### Translation
- `POST /Jodettu/translation/translate` - Translate text
- `POST /Jodettu/translation/translate-batch` - Batch translation
- `POST /Jodettu/translation/translate-multiple` - Translate to multiple languages

#### Language Support
- `POST /Jodettu/translation/detect-language` - Detect language
- `GET /Jodettu/translation/supported-languages` - Get supported languages

### Combined Services
- `POST /Jodettu/ai/location-translate` - Analyze image and translate location

## Supported Languages for Translation

- English (en)
- Hindi (hi)
- Bengali (bn)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)
- Marathi (mr)
- Odia (or)
- Punjabi (pa)
- Tamil (ta)
- Telugu (te)
- Assamese (as)
- Urdu (ur)

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage Examples

### Object Detection
```python
import requests

# Detect objects in image
with open('image.jpg', 'rb') as f:
    files = {'image': f}
    headers = {'Authorization': 'Bearer YOUR_TOKEN'}
    response = requests.post(
        'http://localhost:8000/Jodettu/ai/detect-objects',
        files=files,
        headers=headers
    )
```

### Translation
```python
import requests

# Translate English to Hindi
data = {
    'text': 'Hello, how are you?',
    'src_lang': 'en',
    'tgt_lang': 'hi'
}
headers = {'Authorization': 'Bearer YOUR_TOKEN'}
response = requests.post(
    'http://localhost:8000/Jodettu/translation/translate',
    data=data,
    headers=headers
)
```

### Location Services
```python
import requests

# Geocode address
data = {'address': 'Delhi, India'}
headers = {'Authorization': 'Bearer YOUR_TOKEN'}
response = requests.post(
    'http://localhost:8000/Jodettu/location/geocode',
    data=data,
    headers=headers
)
```

## Configuration

### Environment Variables
No additional environment variables are required for the AI services. The models will be downloaded automatically on first use.

### Model Storage
- YOLOv8 models are stored locally after first download
- ResNet50 uses PyTorch's pre-trained weights
- IndicTrans2 models are downloaded from Hugging Face

### GPU Support
All services automatically detect and use GPU if available:
- YOLOv8: CUDA acceleration
- ResNet50: PyTorch GPU support
- IndicTrans2: Transformers GPU support

## Performance Considerations

### Model Loading
- Models are loaded on startup
- First request may be slower due to model initialization
- Subsequent requests are faster

### Memory Usage
- YOLOv8: ~50MB RAM
- ResNet50: ~100MB RAM
- IndicTrans2: ~2GB RAM
- Total GPU memory: ~2-3GB if GPU available

### Optimization Tips
1. Use GPU for better performance
2. Batch multiple requests when possible
3. Implement caching for frequently translated texts
4. Use appropriate image sizes for optimal processing

## Error Handling

All services return consistent error responses:
```json
{
    "error": "Error description"
}
```

Common error codes:
- 400: Bad request (invalid parameters)
- 401: Unauthorized (invalid token)
- 500: Internal server error (model/service failure)

## Security

- All endpoints require authentication
- File uploads are validated
- Input sanitization is implemented
- Rate limiting recommended for production

## Troubleshooting

### Model Loading Issues
- Check internet connection for model downloads
- Verify sufficient disk space
- Check GPU availability and drivers

### Translation Issues
- Verify source/target language codes
- Check input text encoding
- Ensure sufficient memory for large texts

### Location Service Issues
- Check internet connection for API calls
- Verify address format
- Check rate limits for external APIs

## Future Enhancements

1. **Additional Models**: Integrate more specialized models
2. **Custom Training**: Support for custom-trained models
3. **Real-time Processing**: WebSocket support for real-time AI processing
4. **Model Optimization**: Quantization and pruning for better performance
5. **Offline Support**: Local models for offline functionality
