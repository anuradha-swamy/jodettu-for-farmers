import torch
import torch.nn as nn
from torchvision import models
from PIL import Image
import torchvision.transforms as transforms
from typing import Dict, Tuple
import os
from pathlib import Path

class AnimalClassifier:
    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None  # Will be loaded lazily
        self.classes = self._get_animal_classes()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                              std=[0.229, 0.224, 0.225])
        ])
        self.model_path = model_path
        self._model_loaded = False
    
    def _ensure_model_loaded(self):
        """Load model only when needed"""
        if not self._model_loaded:
            print("🚀 Loading ResNet50 model (this may take a moment)...")
            self.model = self._load_model()
            
            if self.model_path and os.path.exists(self.model_path):
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            
            self.model.eval()
            self.model.to(self.device)
            self._model_loaded = True
            print("✅ Model loaded successfully")
    
    def _load_model(self) -> nn.Module:
        """Load a pre-trained ResNet50 model with custom weights for livestock."""
        # Load pre-trained model
        model = models.resnet50(pretrained=True)
        
        # Freeze early layers
        for param in model.parameters():
            param.requires_grad = False
            
        # Replace the final fully connected layer
        num_ftrs = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(num_ftrs, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, len(self._get_animal_classes()))
        )
        
        # Load custom weights if available
        custom_weights = Path("models/livestock_resnet50.pth")
        if custom_weights.exists():
            model.load_state_dict(torch.load(custom_weights, map_location=self.device))
            print("Loaded custom livestock model weights")
        else:
            print("Warning: Using base ResNet50 weights. For better results, train on livestock data.")
            
        return model
    
    @staticmethod
    def _get_animal_classes() -> Dict[int, str]:
        """Return a mapping of class indices to livestock animal types."""
        return {
            0: "cattle_holstein",
            1: "cattle_jersey",
            2: "cattle_angus",
            3: "sheep_dorper",
            4: "sheep_merino",
            5: "sheep_suffolk",
            6: "goat_boer",
            7: "goat_nubian",
            8: "goat_saanen",
            9: "horse"  # Keeping horse as a fallback, but we'll adjust confidence thresholds
        }
    
    def preprocess_image(self, image_path: str) -> torch.Tensor:
        """Load and preprocess an image for the model."""
        image = Image.open(image_path).convert('RGB')
        image = self.transform(image)
        return image.unsqueeze(0).to(self.device)
    
    def predict(self, image_path: str) -> Tuple[str, float]:
        """Predict the animal and breed from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            tuple: (animal_breed, confidence)
        """
        try:
            # Ensure model is loaded before prediction
            self._ensure_model_loaded()
            
            # Preprocess the image
            input_tensor = self.preprocess_image(image_path)
            
            # Make prediction
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                confidence, pred_idx = torch.max(probabilities, 0)
                
            # Get the predicted class
            animal_breed = self.classes.get(pred_idx.item(), "unknown")
            
            # Convert to standard Python types
            confidence = confidence.item()
            
            return animal_breed, confidence
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            return "error", 0.0
    
    def get_animal_and_breed(self, image_path: str) -> Dict[str, str]:
        """Get the animal type and breed from an image with enhanced livestock handling."""
        prediction, confidence = self.predict(image_path)
        
        # Higher confidence threshold for livestock classification
        if prediction == "error" or confidence < 0.7:  # Increased threshold
            return {
                "animal": "unknown",
                "breed": "unknown",
                "confidence": 0.0,
                "error": "Could not identify the animal with sufficient confidence"
            }
            
        # Handle horse predictions more carefully
        if "horse" in prediction and confidence < 0.9:  # Require very high confidence for horse
            return {
                "animal": "unknown",
                "breed": "unknown",
                "confidence": confidence,
                "error": "Low confidence in prediction"
            }
        
        # Split the prediction into animal and breed
        parts = prediction.split('_', 1)
        if len(parts) == 2:
            animal, breed = parts
        else:
            animal = parts[0]
            breed = "unknown"
        
        return {
            "animal": animal,
            "breed": breed.replace('_', ' ').title(),
            "confidence": round(confidence, 4),
            "error": None
        }
