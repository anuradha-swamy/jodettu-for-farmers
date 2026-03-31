import sys

print(f"Python version: {sys.version}")

print("\n--- Testing Imports ---")

try:
    import torch
    print(f"✅ torch imported (Version: {torch.__version__})")
except ImportError as e:
    print(f"❌ Failed to import torch: {e}")

try:
    import torchvision
    print(f"✅ torchvision imported (Version: {torchvision.__version__})")
except ImportError as e:
    print(f"❌ Failed to import torchvision: {e}")

try:
    from ultralytics import YOLO
    print("✅ ultralytics (YOLO) imported")
except ImportError as e:
    print(f"❌ Failed to import ultralytics: {e}")

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    print("✅ transformers imported")
except ImportError as e:
    print(f"❌ Failed to import transformers: {e}")

try:
    import cv2
    print(f"✅ cv2 (opencv-python) imported (Version: {cv2.__version__})")
except ImportError as e:
    print(f"❌ Failed to import cv2: {e}")

print("\n--- Check Complete ---")
