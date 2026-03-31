from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
from typing import Dict, Any
from datetime import datetime
import asyncio

from app.models.animal_classifier import AnimalClassifier
from app.utils.image_processing import save_upload_file, validate_image, process_image
from app.config import settings
from general.security import Security

# Import AI services
from services.yolo_service import yolo_service
from services.resnet_service import resnet_service

router = APIRouter(
    prefix="/api/v1/animals",
    tags=["animal_classification"],
    responses={404: {"description": "Not found"}},
)

# --- FIX START: Lazy Loading Singleton ---
# Global variable to hold the model instance
_classifier_instance = None

def get_classifier():
    """
    Singleton accessor for the AnimalClassifier.
    Loads the model only if it hasn't been loaded yet.
    """
    global _classifier_instance
    if _classifier_instance is None:
        print("LOADING: Loading Animal Classifier Model...")
        _classifier_instance = AnimalClassifier()
        print("SUCCESS: Animal Classifier Model Loaded Successfully.")
    return _classifier_instance
# --- FIX END ---

@router.post("/classify", response_model=Dict[str, Any])
async def classify_animal(
    file: UploadFile = File(..., description="Image file to classify"),
):
    """
    Classify an animal image and return the predicted animal and breed.
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join("upload_files", "animals")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded file
        file_path = await save_upload_file(file, upload_dir)
        
        # Validate the image
        is_valid, error_msg = validate_image(file_path, max_size_mb=10)
        if not is_valid:
            os.remove(file_path)  # Clean up
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Process the image for the model
        processed_path = process_image(file_path)
        
        try:
            # --- FIX: Use the getter function instead of global variable ---
            classifier = get_classifier()
            result = classifier.get_animal_and_breed(processed_path)
            
            # Clean up processed file
            if os.path.exists(processed_path) and processed_path != file_path:
                os.remove(processed_path)
            
            # Return the result
            return JSONResponse(content={
                "success": True,
                "data": {
                    "animal": result["animal"],
                    "breed": result["breed"],
                    "confidence": result["confidence"],
                    "original_filename": file.filename,
                }
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(processed_path) and processed_path != file_path:
                os.remove(processed_path)
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Clean up the original uploaded file
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

# Add health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if model is loaded without triggering load
    status_msg = "healthy" if _classifier_instance else "healthy (model cold)"
    return {"status": status_msg, "model_loaded": _classifier_instance is not None}
