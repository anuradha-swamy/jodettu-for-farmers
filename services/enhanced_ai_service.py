import os
import json
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import HTTPException, UploadFile
from general.database import own_animals, breeds_collection, training_data_collection
from bson import ObjectId
import shutil

class EnhancedAIService:
    """
    Enhanced AI service for animal detection, breed identification, and disease detection
    """
    
    @staticmethod
    async def detect_animal_with_details(image_bytes: bytes, animal_type: str = None) -> Dict[str, Any]:
        """
        Detect animal and provide detailed information about breed and characteristics
        """
        try:
            # Use existing YOLO service for animal detection
            from services.yolo_service import yolo_service
            yolo_result = await yolo_service.detect_animals(image_bytes)
            
            if not yolo_result.get("animal_detections"):
                return {
                    "success": False,
                    "message": "No animals detected in the image",
                    "detected_animals": []
                }
            
            # Enhance with breed and detailed information
            enhanced_results = []
            for detection in yolo_result["animal_detections"]:
                animal_type = detection.get("class", "unknown").lower()
                
                # Get detailed animal information
                animal_details = await EnhancedAIService._get_animal_details(animal_type)
                
                enhanced_result = {
                    "animal_type": animal_type,
                    "confidence": detection.get("confidence", 0),
                    "bbox": detection.get("bbox", {}),
                    "details": animal_details,
                    "common_breeds": await EnhancedAIService._get_common_breeds(animal_type),
                    "care_instructions": await EnhancedAIService._get_care_instructions(animal_type)
                }
                enhanced_results.append(enhanced_result)
            
            return {
                "success": True,
                "message": f"Detected {len(enhanced_results)} animal(s)",
                "detected_animals": enhanced_results,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Animal detection failed: {str(e)}",
                "detected_animals": []
            }
    
    @staticmethod
    async def detect_skin_disease(image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect skin diseases from animal images
        """
        try:
            # Use ResNet for disease classification
            from services.resnet_service import resnet_service
            classification_result = await resnet_service.classify_image(image_bytes)
            
            # Check for disease-related classifications
            predictions = classification_result.get("predictions", [])
            disease_predictions = []
            
            # Common skin disease keywords (this would be enhanced with proper disease model)
            disease_keywords = [
                "mange", "rash", "lesion", "dermatitis", "eczema", "infection",
                "fungus", "parasite", "allergy", "irritation", "inflammation"
            ]
            
            for pred in predictions:
                class_name = pred.get("class", "").lower()
                confidence = pred.get("confidence", 0)
                
                # Check if classification matches disease keywords
                for keyword in disease_keywords:
                    if keyword in class_name and confidence > 0.3:
                        disease_info = await EnhancedAIService._get_disease_info(keyword)
                        disease_predictions.append({
                            "disease_name": disease_info.get("name", keyword.title()),
                            "confidence": confidence,
                            "symptoms": disease_info.get("symptoms", []),
                            "treatment": disease_info.get("treatment", []),
                            "severity": disease_info.get("severity", "moderate"),
                            "contagious": disease_info.get("contagious", False),
                            "veterinary_care_required": disease_info.get("veterinary_care_required", True)
                        })
                        break
            
            if not disease_predictions:
                return {
                    "success": True,
                    "message": "No specific skin diseases detected. Image appears normal.",
                    "disease_detections": [],
                    "recommendation": "Regular health monitoring recommended"
                }
            
            return {
                "success": True,
                "message": f"Detected {len(disease_predictions)} potential condition(s)",
                "disease_detections": disease_predictions,
                "recommendation": "Consult veterinarian for proper diagnosis and treatment",
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Disease detection failed: {str(e)}",
                "disease_detections": []
            }
    
    @staticmethod
    async def add_training_data(
        image: UploadFile,
        animal_type: str,
        breed: Optional[str] = None,
        disease_name: Optional[str] = None,
        user_id: str = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add training data for AI model improvement
        """
        try:
            # Read and save image
            image_bytes = await image.read()
            image_filename = f"training_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{image.filename}"
            
            # Save to training data directory
            training_dir = "data/training_images"
            os.makedirs(training_dir, exist_ok=True)
            
            image_path = os.path.join(training_dir, image_filename)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            # Prepare training data record
            training_record = {
                "image_filename": image_filename,
                "image_path": image_path,
                "animal_type": animal_type.lower(),
                "breed": breed.lower() if breed else None,
                "disease_name": disease_name.lower() if disease_name else None,
                "data_type": "disease" if disease_name else "animal_breed",
                "user_id": user_id,
                "notes": notes,
                "created_at": datetime.utcnow(),
                "verified": False,  # Needs expert verification
                "used_for_training": False
            }
            
            # Save to database
            result = training_data_collection.insert_one(training_record)
            training_record["_id"] = str(result.inserted_id)
            
            return {
                "success": True,
                "message": "Training data added successfully",
                "training_data_id": str(result.inserted_id),
                "data_type": training_record["data_type"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add training data: {str(e)}")
    
    @staticmethod
    async def get_training_data(
        data_type: Optional[str] = None,
        animal_type: Optional[str] = None,
        verified_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get training data for AI model training
        """
        try:
            query = {}
            if data_type:
                query["data_type"] = data_type
            if animal_type:
                query["animal_type"] = animal_type.lower()
            if verified_only:
                query["verified"] = True
            
            training_data = list(training_data_collection.find(query))
            
            # Convert ObjectId to string and add image data
            for data in training_data:
                data["_id"] = str(data["_id"])
                
                # Read image and convert to base64 if needed
                if os.path.exists(data["image_path"]):
                    with open(data["image_path"], "rb") as f:
                        image_bytes = f.read()
                        data["image_base64"] = base64.b64encode(image_bytes).decode('utf-8')
                else:
                    data["image_base64"] = None
            
            return training_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get training data: {str(e)}")
    
    @staticmethod
    async def verify_training_data(
        training_data_id: str,
        verified: bool,
        expert_notes: Optional[str] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Verify training data (expert/veterinarian function)
        """
        try:
            result = training_data_collection.update_one(
                {"_id": ObjectId(training_data_id)},
                {
                    "$set": {
                        "verified": verified,
                        "expert_notes": expert_notes,
                        "verified_by": user_id,
                        "verified_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Training data not found")
            
            return {
                "success": True,
                "message": f"Training data {'verified' if verified else 'unverified'} successfully"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to verify training data: {str(e)}")
    
    @staticmethod
    async def get_ai_statistics() -> Dict[str, Any]:
        """
        Get AI model performance statistics
        """
        try:
            stats = {
                "training_data_count": training_data_collection.count_documents({}),
                "verified_training_data": training_data_collection.count_documents({"verified": True}),
                "animal_breed_data": training_data_collection.count_documents({"data_type": "animal_breed"}),
                "disease_data": training_data_collection.count_documents({"data_type": "disease"}),
                "animal_types": list(training_data_collection.distinct("animal_type")),
                "diseases_tracked": list(training_data_collection.distinct("disease_name")),
                "recent_additions": list(
                    training_data_collection.find({})
                    .sort("created_at", -1)
                    .limit(5)
                )
            }
            
            # Convert ObjectId to string for recent additions
            for item in stats["recent_additions"]:
                item["_id"] = str(item["_id"])
            
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get AI statistics: {str(e)}")
    
    # ===== Helper Methods =====
    
    @staticmethod
    async def _get_animal_details(animal_type: str) -> Dict[str, Any]:
        """
        Get detailed information about an animal type
        """
        # This would typically come from a database or knowledge base
        animal_info = {
            "cow": {
                "name": "Cow (Cattle)",
                "scientific_name": "Bos taurus",
                "description": "Domesticated bovine farm animals",
                "average_lifespan": "15-20 years",
                "average_weight": "400-1100 kg",
                "common_uses": ["milk production", "meat", "draft animals"],
                "diet": "herbivore - grass, hay, silage",
                "habitat": "pastures, barns"
            },
            "goat": {
                "name": "Goat",
                "scientific_name": "Capra aegagrus hircus",
                "description": "Small domesticated ruminants",
                "average_lifespan": "12-15 years",
                "average_weight": "20-140 kg",
                "common_uses": ["milk", "meat", "fiber", "brush control"],
                "diet": "herbivore - browse, grass, grains",
                "habitat": "mountains, farms"
            },
            "chicken": {
                "name": "Chicken",
                "scientific_name": "Gallus gallus domesticus",
                "description": "Domesticated fowl",
                "average_lifespan": "5-10 years",
                "average_weight": "1.5-4.5 kg",
                "common_uses": ["eggs", "meat", "feathers"],
                "diet": "omnivore - seeds, insects, grains",
                "habitat": "coops, free-range"
            }
        }
        
        return animal_info.get(animal_type, {
            "name": animal_type.title(),
            "description": "Farm animal",
            "average_lifespan": "Varies",
            "average_weight": "Varies",
            "common_uses": ["Various"],
            "diet": "Varies",
            "habitat": "Farm environment"
        })
    
    @staticmethod
    async def _get_common_breeds(animal_type: str) -> List[str]:
        """
        Get common breeds for an animal type
        """
        breeds = {
            "cow": ["Holstein", "Jersey", "Angus", "Hereford", "Brahman", "Sahiwal"],
            "goat": ["Boer", "Alpine", "Nubian", "Saanen", "Toggenburg", "Jamunapari"],
            "chicken": ["Rhode Island Red", "Leghorn", "Plymouth Rock", "Sussex", "Orpington", "Aseel"]
        }
        
        return breeds.get(animal_type, ["Various breeds available"])
    
    @staticmethod
    async def _get_care_instructions(animal_type: str) -> List[str]:
        """
        Get basic care instructions for an animal type
        """
        care_instructions = {
            "cow": [
                "Provide clean water daily",
                "Feed quality hay and pasture",
                "Regular veterinary checkups",
                "Clean and dry living area",
                "Proper vaccination schedule"
            ],
            "goat": [
                "Provide fresh water and minerals",
                "Secure fencing to prevent escape",
                "Regular hoof trimming",
                "Parasite control program",
                "Shelter from extreme weather"
            ],
            "chicken": [
                "Clean water and balanced feed",
                "Secure coop from predators",
                "Regular cleaning of living area",
                "Nest boxes for egg laying",
                "Dust baths for parasite control"
            ]
        }
        
        return care_instructions.get(animal_type, [
            "Provide proper nutrition",
            "Ensure clean water",
            "Regular health monitoring",
            "Appropriate shelter",
            "Veterinary care when needed"
        ])
    
    @staticmethod
    async def _get_disease_info(disease_keyword: str) -> Dict[str, Any]:
        """
        Get disease information based on keyword
        """
        disease_info = {
            "mange": {
                "name": "Mange",
                "symptoms": ["Intense itching", "Hair loss", "Skin irritation", "Crusty patches"],
                "treatment": ["Medicated shampoos", "Ivermectin medication", "Environmental cleaning"],
                "severity": "moderate",
                "contagious": True,
                "veterinary_care_required": True
            },
            "dermatitis": {
                "name": "Dermatitis",
                "symptoms": ["Red skin", "Swelling", "Itching", "Possible discharge"],
                "treatment": ["Anti-inflammatory medications", "Topical creams", "Identify allergen"],
                "severity": "mild to moderate",
                "contagious": False,
                "veterinary_care_required": True
            },
            "fungus": {
                "name": "Fungal Infection",
                "symptoms": ["Circular lesions", "Hair loss", "Scaly skin", "Itching"],
                "treatment": ["Antifungal medications", "Topical treatments", "Environmental disinfection"],
                "severity": "mild to moderate",
                "contagious": True,
                "veterinary_care_required": True
            }
        }
        
        return disease_info.get(disease_keyword, {
            "name": "Skin Condition",
            "symptoms": ["Visible skin changes", "Itching", "Discomfort"],
            "treatment": ["Veterinary consultation", "Proper diagnosis", "Targeted treatment"],
            "severity": "unknown",
            "contagious": False,
            "veterinary_care_required": True
        })

# Global service instance
enhanced_ai_service = EnhancedAIService()
