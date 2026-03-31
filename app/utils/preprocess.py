from typing import Tuple
import numpy as np
from PIL import Image, ImageOps
import io
from fastapi import UploadFile

async def validate_image(file: UploadFile) -> bool:
    """Validate the uploaded file is an image"""
    if not file.content_type.startswith('image/'):
        return False
    
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        return False
    
    return True

async def preprocess_image(
    file: UploadFile, 
    target_size: Tuple[int, int] = (224, 224)
) -> np.ndarray:
    """
    Preprocess image for model prediction
    
    Args:
        file: Uploaded file
        target_size: Target size for the image (width, height)
        
    Returns:
        Preprocessed image as numpy array
    """
    # Read image
    contents = await file.read()
    img = Image.open(io.BytesIO(contents))
    
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize maintaining aspect ratio
    img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
    
    # Convert to numpy array and normalize
    img_array = np.array(img, dtype=np.float32) / 255.0
    
    # Add batch dimension (B, H, W, C)
    return np.expand_dims(img_array, axis=0)
