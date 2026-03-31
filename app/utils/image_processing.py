import os
from fastapi import UploadFile, HTTPException
from typing import Tuple
from PIL import Image, ImageOps
import io

async def save_upload_file(upload_file: UploadFile, upload_dir: str) -> str:
    """Save an uploaded file to the specified directory and return the file path.
    
    Args:
        upload_file: The uploaded file
        upload_dir: Directory to save the file in
        
    Returns:
        str: Path to the saved file
    """
    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    file_path = os.path.join(upload_dir, f"{os.urandom(8).hex()}{file_extension}")
    
    # Save the file
    try:
        contents = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def validate_image(file_path: str, max_size_mb: int = 10) -> Tuple[bool, str]:
    """Validate an image file.
    
    Args:
        file_path: Path to the image file
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"File size exceeds {max_size_mb}MB"
        
        # Try to open the image
        with Image.open(file_path) as img:
            img.verify()
            
        return True, ""
        
    except (IOError, SyntaxError) as e:
        return False, "Invalid image file"
    except Exception as e:
        return False, str(e)

def process_image(image_path: str, target_size: Tuple[int, int] = (224, 224)) -> str:
    """Process an image for the model.
    
    Args:
        image_path: Path to the input image
        target_size: Target size as (width, height)
        
    Returns:
        str: Path to the processed image
    """
    try:
        # Create a processed version of the image
        processed_path = f"{os.path.splitext(image_path)[0]}_processed.jpg"
        
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Resize and save
            img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
            img.save(processed_path, 'JPEG', quality=90)
            
        return processed_path
        
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")
