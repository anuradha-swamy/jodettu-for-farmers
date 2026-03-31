from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from general.security import Security
from services.enhanced_ai_service import enhanced_ai_service
from typing import Optional, List
from datetime import datetime
import json

router = APIRouter()

"""
Enhanced AI Service Routes
- Animal detection with breed and detailed information
- Skin disease detection
- Training data management for AI model improvement
"""

# ===== Animal Detection with Breed Identification =====

@router.post("/ai/animal-breed-detection")
async def detect_animal_and_breed(
    image: UploadFile = File(...),
    animal_type: Optional[str] = Form(None),  # Optional filter for specific animal type
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Single API for animal detection AND breed identification.
    Detects animals in image and provides detailed breed information.
    """
    try:
        image_bytes = await image.read()
        result = await enhanced_ai_service.detect_animal_with_details(image_bytes, animal_type)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Animal and breed detection failed: {str(e)}")

@router.post("/ai/animal-detection")
async def detect_animal_with_details(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Detect animal in image and provide detailed information including breed, characteristics, and care instructions
    """
    try:
        image_bytes = await image.read()
        result = await enhanced_ai_service.detect_animal_with_details(image_bytes)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Animal detection failed: {str(e)}")

@router.post("/ai/breed-identification")
async def identify_breed(
    image: UploadFile = File(...),
    animal_type: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Identify specific breed from animal image
    """
    try:
        image_bytes = await image.read()
        
        # First detect animal to confirm type matches
        detection_result = await enhanced_ai_service.detect_animal_with_details(image_bytes, animal_type)
        
        if not detection_result.get("success"):
            raise HTTPException(status_code=400, detail="No animals detected in image")
        
        # Filter results by specified animal type
        detected_animals = [
            animal for animal in detection_result["detections"]
            if animal["animal_type"].lower() == animal_type.lower()
        ]
        
        if not detected_animals:
            raise HTTPException(
                status_code=400, 
                detail=f"No {animal_type} detected in image"
            )
        
        return {
            "success": True,
            "animal_type": animal_type,
            "detected_breeds": detected_animals[0]["detected_breeds"],
            "confidence": detected_animals[0]["confidence"],
            "details": detected_animals[0]["details"],
            "care_instructions": detected_animals[0]["care_instructions"],
            "breed_analysis": detected_animals[0]["breed_analysis"],
            "message": f"Successfully identified {animal_type} with breed information"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breed identification failed: {str(e)}")

# ===== Disease Detection =====

@router.post("/ai/disease-detection")
async def detect_skin_disease(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Detect skin diseases from animal images
    """
    try:
        image_bytes = await image.read()
        result = await enhanced_ai_service.detect_skin_disease(image_bytes)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disease detection failed: {str(e)}")

@router.post("/ai/health-analysis")
async def comprehensive_health_analysis(
    image: UploadFile = File(...),
    animal_type: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Comprehensive health analysis including animal detection, breed info, and disease detection
    """
    try:
        image_bytes = await image.read()
        
        # Animal detection with details
        animal_result = await enhanced_ai_service.detect_animal_with_details(image_bytes)
        
        # Disease detection
        disease_result = await enhanced_ai_service.detect_skin_disease(image_bytes)
        
        # Combine results
        analysis = {
            "success": True,
            "analysis_type": "comprehensive_health",
            "animal_analysis": animal_result,
            "disease_analysis": disease_result,
            "summary": {
                "animals_detected": len(animal_result.get("detected_animals", [])),
                "diseases_detected": len(disease_result.get("disease_detections", [])),
                "overall_health_status": "healthy" if not disease_result.get("disease_detections") else "requires_attention",
                "recommendations": []
            }
        }
        
        # Add recommendations based on analysis
        if not animal_result.get("success"):
            analysis["summary"]["recommendations"].append("Clearer image needed for animal detection")
        
        if disease_result.get("disease_detections"):
            analysis["summary"]["recommendations"].append("Consult veterinarian immediately")
            analysis["summary"]["recommendations"].append("Follow treatment recommendations")
        else:
            analysis["summary"]["recommendations"].append("Continue regular health monitoring")
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health analysis failed: {str(e)}")

# ===== Training Data Management =====

@router.post("/ai/training-data/add")
async def add_training_data(
    image: UploadFile = File(...),
    animal_type: str = Form(...),
    breed: Optional[str] = Form(None),
    disease_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Add training data for AI model improvement
    """
    try:
        user_id = current_user.get("user_id")
        result = await enhanced_ai_service.add_training_data(
            image, animal_type, breed, disease_name, user_id, notes
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add training data: {str(e)}")

@router.get("/ai/training-data")
async def get_training_data(
    data_type: Optional[str] = None,
    animal_type: Optional[str] = None,
    verified_only: bool = False,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get training data for AI models
    """
    try:
        training_data = await enhanced_ai_service.get_training_data(
            data_type, animal_type, verified_only
        )
        
        return {
            "success": True,
            "training_data": training_data,
            "count": len(training_data),
            "filters": {
                "data_type": data_type,
                "animal_type": animal_type,
                "verified_only": verified_only
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training data: {str(e)}")

@router.put("/ai/training-data/{training_data_id}/verify")
async def verify_training_data(
    training_data_id: str,
    verified: bool = Form(...),
    expert_notes: Optional[str] = Form(None),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Verify training data (expert/veterinarian function)
    """
    try:
        user_id = current_user.get("user_id")
        result = await enhanced_ai_service.verify_training_data(
            training_data_id, verified, expert_notes, user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify training data: {str(e)}")

# ===== AI Statistics and Management =====

@router.get("/ai/statistics")
async def get_ai_statistics(
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get AI model performance and training statistics
    """
    try:
        stats = await enhanced_ai_service.get_ai_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI statistics: {str(e)}")

@router.post("/ai/batch-analysis")
async def batch_analysis(
    images: List[UploadFile] = File(...),
    analysis_type: str = Form("animal"),  # "animal", "disease", or "comprehensive"
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Analyze multiple images in batch
    """
    try:
        results = []
        
        for image in images:
            image_bytes = await image.read()
            
            if analysis_type == "animal":
                result = await enhanced_ai_service.detect_animal_with_details(image_bytes)
            elif analysis_type == "disease":
                result = await enhanced_ai_service.detect_skin_disease(image_bytes)
            elif analysis_type == "comprehensive":
                # Animal detection
                animal_result = await enhanced_ai_service.detect_animal_with_details(image_bytes)
                # Disease detection
                disease_result = await enhanced_ai_service.detect_skin_disease(image_bytes)
                
                result = {
                    "success": True,
                    "animal_analysis": animal_result,
                    "disease_analysis": disease_result,
                    "image_filename": image.filename
                }
            else:
                raise HTTPException(status_code=400, detail="Invalid analysis type")
            
            result["image_filename"] = image.filename
            results.append(result)
        
        return {
            "success": True,
            "analysis_type": analysis_type,
            "total_images": len(images),
            "results": results,
            "summary": {
                "successful_analyses": len([r for r in results if r.get("success")]),
                "failed_analyses": len([r for r in results if not r.get("success")])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

# ===== AI Model Training Support =====

@router.post("/ai/model-training/prepare-dataset")
async def prepare_training_dataset(
    data_type: str = Form(...),  # "animal_breed" or "disease"
    animal_type: Optional[str] = Form(None),
    verified_only: bool = Form(True),
    current_user: dict = Depends(Security.get_current_admin_user)  # Admin only
):
    """
    Prepare dataset for AI model training (Admin only)
    """
    try:
        training_data = await enhanced_ai_service.get_training_data(
            data_type, animal_type, verified_only
        )
        
        # Prepare dataset in format suitable for training
        dataset = {
            "dataset_type": data_type,
            "animal_type": animal_type,
            "total_samples": len(training_data),
            "verified_samples": len([d for d in training_data if d.get("verified")]),
            "samples": training_data,
            "prepared_at": datetime.utcnow().isoformat(),
            "download_ready": True
        }
        
        return dataset
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare dataset: {str(e)}")

@router.get("/ai/supported-animals")
async def get_supported_animals(
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get list of supported animal types for AI detection
    """
    try:
        supported_animals = {
            "supported_types": [
                {
                    "type": "cow",
                    "name": "Cow/Cattle",
                    "breeds_available": ["Holstein", "Jersey", "Angus", "Hereford", "Brahman", "Sahiwal"],
                    "detection_confidence": "high"
                },
                {
                    "type": "goat", 
                    "name": "Goat",
                    "breeds_available": ["Boer", "Alpine", "Nubian", "Saanen", "Toggenburg", "Jamunapari"],
                    "detection_confidence": "medium"
                },
                {
                    "type": "chicken",
                    "name": "Chicken/Poultry",
                    "breeds_available": ["Rhode Island Red", "Leghorn", "Plymouth Rock", "Sussex", "Orpington", "Aseel"],
                    "detection_confidence": "high"
                }
            ],
            "disease_detection": {
                "supported_conditions": ["Mange", "Dermatitis", "Fungal infections", "Skin irritations"],
                "accuracy_note": "Disease detection is preliminary - always consult veterinarian"
            }
        }
        
        return supported_animals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get supported animals: {str(e)}")
