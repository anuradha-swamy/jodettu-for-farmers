import cv2
import numpy as np
from PIL import Image
import io
from typing import List, Dict, Any
from ultralytics import YOLO
import torch

class YOLOv8Service:
    def __init__(self):
        """Initialize YOLOv8 model"""
        try:
            # Load pre-trained YOLOv8 model
            self.model = YOLO('yolov8n.pt')  # nano version for faster inference
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            print(f"YOLOv8 model loaded on {self.device}")
        except Exception as e:
            print(f"Error loading YOLOv8 model: {e}")
            self.model = None

    async def detect_objects(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect objects in image using YOLOv8
        Args:
            image_bytes: Raw image bytes
        Returns:
            Dictionary containing detection results
        """
        if not self.model:
            return {"error": "YOLOv8 model not loaded"}

        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {"error": "Invalid image format"}

            # Run inference
            results = self.model(image)
            
            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    detections.append({
                        "class": class_name,
                        "confidence": float(confidence),
                        "bbox": {
                            "x1": float(x1),
                            "y1": float(y1),
                            "x2": float(x2),
                            "y2": float(y2)
                        }
                    })
            
            return {
                "success": True,
                "detections": detections,
                "total_objects": len(detections)
            }
            
        except Exception as e:
            return {"error": f"Detection failed: {str(e)}"}

    async def detect_animals(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Specifically detect animals in the image
        Args:
            image_bytes: Raw image bytes
        Returns:
            Dictionary containing animal detection results
        """
        result = await self.detect_objects(image_bytes)
        
        if "error" in result:
            return result
        
        # Filter for animal classes
        animal_classes = ['dog', 'cat', 'horse', 'cow', 'sheep', 'goat', 'pig', 'chicken', 'duck', 'bird']
        animal_detections = [
            det for det in result["detections"] 
            if det["class"].lower() in animal_classes
        ]
        
        return {
            "success": True,
            "animal_detections": animal_detections,
            "total_animals": len(animal_detections),
            "all_detections": result["detections"]
        }

# Global instance
yolo_service = YOLOv8Service()
