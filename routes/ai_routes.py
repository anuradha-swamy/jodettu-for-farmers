from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from general.security import Security
from services.yolo_service import yolo_service
from services.resnet_service import resnet_service
from services.location_service import location_service
from services.translation_service import translation_service
from typing import Dict, Any, List

router = APIRouter()

"""
AI/ML Service Routes
- Object detection using YOLOv8
- Image classification using ResNet50
- Location services using OpenStreetMap
- Translation services using IndicTrans2
"""

# ===== YOLOv8 Object Detection Routes =====

@router.post("/ai/detect-objects")
async def detect_objects(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Detect objects in an image using YOLOv8
    """
    try:
        image_bytes = await image.read()
        result = await yolo_service.detect_objects(image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/detect-animals")
async def detect_animals(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Specifically detect animals in an image using YOLOv8
    """
    try:
        image_bytes = await image.read()
        result = await yolo_service.detect_animals(image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ResNet50 Image Classification Routes =====

@router.post("/ai/classify-image")
async def classify_image(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Classify image using ResNet50
    """
    try:
        image_bytes = await image.read()
        result = await resnet_service.classify_image(image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/classify-animals")
async def classify_animals(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Specifically classify animals in an image using ResNet50
    """
    try:
        image_bytes = await image.read()
        result = await resnet_service.classify_animals(image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Combined AI Analysis Route =====

@router.post("/ai/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Comprehensive image analysis using both YOLOv8 and ResNet50
    """
    try:
        image_bytes = await image.read()
        
        # Run both analyses
        yolo_result = await yolo_service.detect_objects(image_bytes)
        resnet_result = await resnet_service.classify_image(image_bytes)
        
        # Combine results
        combined_result = {
            "success": True,
            "object_detection": yolo_result,
            "image_classification": resnet_result,
            "analysis_summary": {
                "total_objects_detected": len(yolo_result.get("detections", [])),
                "top_classification": resnet_result.get("predictions", [{}])[0].get("class", "Unknown"),
                "has_animals": len(yolo_service.detect_animals(image_bytes).get("animal_detections", [])) > 0
            }
        }
        
        return combined_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Location Service Routes =====

@router.post("/location/geocode")
async def geocode_address(
    address: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Convert address to coordinates
    """
    try:
        result = await location_service.geocode_address(address)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/location/reverse-geocode")
async def reverse_geocode(
    latitude: float = Form(...),
    longitude: float = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Convert coordinates to address
    """
    try:
        result = await location_service.reverse_geocode(latitude, longitude)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/location/nearby-places")
async def find_nearby_places(
    latitude: float = Form(...),
    longitude: float = Form(...),
    place_type: str = Form(...),
    radius: int = Form(5000),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Find nearby places (hospitals, schools, markets, etc.)
    """
    try:
        result = await location_service.find_nearby_places(latitude, longitude, place_type, radius)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/location/calculate-distance")
async def calculate_distance(
    lat1: float = Form(...),
    lon1: float = Form(...),
    lat2: float = Form(...),
    lon2: float = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Calculate distance between two points
    """
    try:
        result = await location_service.calculate_distance(lat1, lon1, lat2, lon2)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/location/create-map")
async def create_map(
    locations: str = Form(...),  # JSON string of locations
    center_lat: float = Form(...),
    center_lon: float = Form(...),
    zoom: int = Form(12),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Create an interactive map with markers
    """
    try:
        import json
        locations_data = json.loads(locations)
        result = await location_service.create_map(locations_data, center_lat, center_lon, zoom)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/location/get-route")
async def get_route(
    start_lat: float = Form(...),
    start_lon: float = Form(...),
    end_lat: float = Form(...),
    end_lon: float = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get route between two points
    """
    try:
        result = await location_service.get_route(start_lat, start_lon, end_lat, end_lon)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Translation Service Routes =====

@router.post("/translation/translate")
async def translate_text(
    text: str = Form(...),
    src_lang: str = Form(...),
    tgt_lang: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Translate text from source language to target language
    """
    try:
        result = await translation_service.translate(text, src_lang, tgt_lang)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translation/translate-batch")
async def translate_batch(
    texts: str = Form(...),  # JSON string of texts
    src_lang: str = Form(...),
    tgt_lang: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Translate multiple texts
    """
    try:
        import json
        texts_list = json.loads(texts)
        result = await translation_service.translate_batch(texts_list, src_lang, tgt_lang)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translation/detect-language")
async def detect_language(
    text: str = Form(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Detect the language of the given text
    """
    try:
        result = await translation_service.detect_language(text)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/translation/supported-languages")
async def get_supported_languages(
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get list of supported languages
    """
    try:
        return translation_service.get_supported_languages()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translation/translate-multiple")
async def translate_to_multiple_languages(
    text: str = Form(...),
    src_lang: str = Form(...),
    target_languages: str = Form(...),  # JSON string of language codes
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Translate text to multiple target languages
    """
    try:
        import json
        target_langs = json.loads(target_languages)
        result = await translation_service.translate_to_multiple_languages(text, src_lang, target_langs)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Combined Service Routes =====

@router.post("/ai/location-translate")
async def analyze_and_translate_location(
    image: UploadFile = File(...),
    address: str = Form(...),
    src_lang: str = Form("en"),
    tgt_lang: str = Form("hi"),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Combined service: Analyze image for animals and translate location description
    """
    try:
        # Analyze image
        image_bytes = await image.read()
        animal_result = await yolo_service.detect_animals(image_bytes)
        
        # Geocode address
        location_result = await location_service.geocode_address(address)
        
        # Translate address description
        translation_result = await translation_service.translate(
            location_result.get("location", {}).get("address", ""), 
            src_lang, 
            tgt_lang
        )
        
        return {
            "success": True,
            "animal_analysis": animal_result,
            "location_info": location_result,
            "translated_address": translation_result,
            "summary": {
                "animals_found": len(animal_result.get("animal_detections", [])),
                "location_coordinates": location_result.get("coordinates"),
                "translated_location": translation_result.get("translated_text", "")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
