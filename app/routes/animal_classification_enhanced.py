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
    Singleton accessor for AnimalClassifier.
    Loads model only if it hasn't been loaded yet.
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
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Classify an animal image using multiple AI models and return comprehensive results.
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes for AI services
        image_bytes = await file.read()
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join("upload_files", "animals")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file for legacy classifier
        file_path = await save_upload_file(file, upload_dir)
        
        # Validate image
        is_valid, error_msg = validate_image(file_path, max_size_mb=10)
        if not is_valid:
            os.remove(file_path)  # Clean up
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Process image for legacy model
        processed_path = process_image(file_path)
        
        # Initialize results dictionary
        classification_results = {
            "success": True,
            "original_filename": file.filename,
            "models": {}
        }
        
        # 1. Legacy Animal Classifier (if available)
        try:
            classifier = get_classifier()
            legacy_result = classifier.get_animal_and_breed(processed_path)
            classification_results["models"]["legacy_classifier"] = {
                "animal": legacy_result["animal"],
                "breed": legacy_result["breed"],
                "confidence": legacy_result["confidence"],
                "model_type": "legacy_animal_classifier"
            }
        except Exception as e:
            classification_results["models"]["legacy_classifier"] = {
                "error": str(e),
                "model_type": "legacy_animal_classifier"
            }
        
        # 2. YOLOv8 Object Detection
        try:
            yolo_result = await yolo_service.detect_animals(image_bytes)
            if yolo_result.get("success"):
                classification_results["models"]["yolov8"] = {
                    "animal_detections": yolo_result["animal_detections"],
                    "total_animals": yolo_result["total_animals"],
                    "model_type": "yolov8_object_detection"
                }
            else:
                classification_results["models"]["yolov8"] = {
                    "error": yolo_result.get("error", "Unknown error"),
                    "model_type": "yolov8_object_detection"
                }
        except Exception as e:
            classification_results["models"]["yolov8"] = {
                "error": str(e),
                "model_type": "yolov8_object_detection"
            }
        
        # 3. ResNet50 Image Classification
        try:
            resnet_result = await resnet_service.classify_animals(image_bytes)
            if resnet_result.get("success"):
                classification_results["models"]["resnet50"] = {
                    "animal_predictions": resnet_result["animal_predictions"],
                    "is_animal": resnet_result["is_animal"],
                    "top_animal": resnet_result["top_animal"],
                    "model_type": "resnet50_classification"
                }
            else:
                classification_results["models"]["resnet50"] = {
                    "error": resnet_result.get("error", "Unknown error"),
                    "model_type": "resnet50_classification"
                }
        except Exception as e:
            classification_results["models"]["resnet50"] = {
                "error": str(e),
                "model_type": "resnet50_classification"
            }
        
        # 4. Combined Analysis Summary
        try:
            # Extract best predictions from all models
            all_animal_predictions = []
            
            # From legacy classifier
            if "legacy_classifier" in classification_results["models"] and "animal" in classification_results["models"]["legacy_classifier"]:
                all_animal_predictions.append({
                    "animal": classification_results["models"]["legacy_classifier"]["animal"],
                    "breed": classification_results["models"]["legacy_classifier"]["breed"],
                    "confidence": classification_results["models"]["legacy_classifier"]["confidence"],
                    "source": "legacy_classifier"
                })
            
            # From ResNet50
            if "resnet50" in classification_results["models"] and "top_animal" in classification_results["models"]["resnet50"]:
                top_animal = classification_results["models"]["resnet50"]["top_animal"]
                if top_animal:
                    all_animal_predictions.append({
                        "animal": top_animal["class"],
                        "confidence": top_animal["confidence"],
                        "source": "resnet50"
                    })
            
            # From YOLOv8
            if "yolov8" in classification_results["models"] and "animal_detections" in classification_results["models"]["yolov8"]:
                for detection in classification_results["models"]["yolov8"]["animal_detections"]:
                    all_animal_predictions.append({
                        "animal": detection["class"],
                        "confidence": detection["confidence"],
                        "source": "yolov8"
                    })
            
            # Find highest confidence prediction
            if all_animal_predictions:
                best_prediction = max(all_animal_predictions, key=lambda x: x["confidence"])
                classification_results["summary"] = {
                    "best_prediction": best_prediction,
                    "total_detections": len(all_animal_predictions),
                    "models_used": list(classification_results["models"].keys()),
                    "analysis_complete": True
                }
            else:
                classification_results["summary"] = {
                    "best_prediction": None,
                    "total_detections": 0,
                    "models_used": list(classification_results["models"].keys()),
                    "analysis_complete": False,
                    "message": "No animals detected in the image"
                }
                
        except Exception as e:
            classification_results["summary"] = {
                "error": f"Summary generation failed: {str(e)}",
                "analysis_complete": False
            }
        
        # Clean up processed file
        if os.path.exists(processed_path) and processed_path != file_path:
            os.remove(processed_path)
        
        return JSONResponse(content=classification_results)
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    finally:
        # Clean up original uploaded file
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

# Additional AI endpoints under animal classification

@router.post("/yolo-detect", response_model=Dict[str, Any])
async def yolo_detect_animals(
    file: UploadFile = File(..., description="Image file for YOLOv8 detection"),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Detect animals in image using YOLOv8 object detection.
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_bytes = await file.read()
        result = await yolo_service.detect_animals(image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YOLOv8 detection failed: {str(e)}")

@router.post("/resnet-classify", response_model=Dict[str, Any])
async def resnet_classify_animals(
    file: UploadFile = File(..., description="Image file for ResNet50 classification"),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Classify animals in image using ResNet50.
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_bytes = await file.read()
        result = await resnet_service.classify_animals(image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ResNet50 classification failed: {str(e)}")

@router.post("/comprehensive-analysis", response_model=Dict[str, Any])
async def comprehensive_animal_analysis(
    file: UploadFile = File(..., description="Image file for comprehensive AI analysis"),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Comprehensive animal analysis using all available AI models.
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_bytes = await file.read()
        
        # Run all analyses in parallel
        yolo_task = yolo_service.detect_animals(image_bytes)
        resnet_task = resnet_service.classify_animals(image_bytes)
        
        # Wait for all results
        yolo_result, resnet_result = await asyncio.gather(yolo_task, resnet_task, return_exceptions=True)
        
        # Process results
        analysis_results = {
            "success": True,
            "original_filename": file.filename,
            "timestamp": datetime.now().isoformat(),
            "analysis": {}
        }
        
        # YOLOv8 results
        if isinstance(yolo_result, dict) and yolo_result.get("success"):
            analysis_results["analysis"]["object_detection"] = {
                "model": "YOLOv8",
                "results": yolo_result
            }
        else:
            analysis_results["analysis"]["object_detection"] = {
                "model": "YOLOv8",
                "error": str(yolo_result) if not isinstance(yolo_result, dict) else yolo_result.get("error", "Unknown error")
            }
        
        # ResNet50 results
        if isinstance(resnet_result, dict) and resnet_result.get("success"):
            analysis_results["analysis"]["classification"] = {
                "model": "ResNet50",
                "results": resnet_result
            }
        else:
            analysis_results["analysis"]["classification"] = {
                "model": "ResNet50",
                "error": str(resnet_result) if not isinstance(resnet_result, dict) else resnet_result.get("error", "Unknown error")
            }
        
        # Legacy classifier (if available)
        try:
            # Save file temporarily for legacy classifier
            upload_dir = os.path.join("upload_files", "animals")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = await save_upload_file(file, upload_dir)
            
            is_valid, error_msg = validate_image(file_path, max_size_mb=10)
            if is_valid:
                processed_path = process_image(file_path)
                classifier = get_classifier()
                legacy_result = classifier.get_animal_and_breed(processed_path)
                
                analysis_results["analysis"]["legacy_classifier"] = {
                    "model": "Legacy Animal Classifier",
                    "results": {
                        "animal": legacy_result["animal"],
                        "breed": legacy_result["breed"],
                        "confidence": legacy_result["confidence"]
                    }
                }
                
                # Clean up
                if os.path.exists(processed_path) and processed_path != file_path:
                    os.remove(processed_path)
            else:
                analysis_results["analysis"]["legacy_classifier"] = {
                    "model": "Legacy Animal Classifier",
                    "error": error_msg
                }
            
            # Clean up original file
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            analysis_results["analysis"]["legacy_classifier"] = {
                "model": "Legacy Animal Classifier",
                "error": str(e)
            }
        
        return JSONResponse(content=analysis_results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive analysis failed: {str(e)}")

# Add health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for all AI models"""
    # Check if models are loaded without triggering load
    legacy_status = "healthy" if _classifier_instance else "healthy (model cold)"
    
    # Check AI services status
    yolo_status = "healthy" if yolo_service.model else "unhealthy"
    resnet_status = "healthy" if resnet_service.model else "unhealthy"
    
    return {
        "status": "healthy",
        "models": {
            "legacy_classifier": {
                "status": legacy_status,
                "model_loaded": _classifier_instance is not None
            },
            "yolov8": {
                "status": yolo_status,
                "model_loaded": yolo_service.model is not None
            },
            "resnet50": {
                "status": resnet_status,
                "model_loaded": resnet_service.model is not None
            }
        }
    }
