#!/usr/bin/env python3
"""
Script to install ML/AI dependencies for Jodettu
Run this script to install all required packages for AI services
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🚀 Installing ML/AI dependencies for Jodettu...")
    print("=" * 50)
    
    # List of required packages
    packages = [
        "ultralytics>=8.0.0",      # YOLOv8
        "transformers>=4.20.0",    # IndicTrans2 and other transformers
        "opencv-python>=4.5.0",    # Computer vision
        "folium>=0.12.0",          # Maps
        "torch>=1.12.0",           # PyTorch (if not already installed)
        "torchvision>=0.13.0",     # Torch vision
    ]
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment. It's recommended to use a virtual environment.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return
    
    # Install packages
    failed_packages = []
    
    for package in packages:
        print(f"\n📦 Installing {package}...")
        if not install_package(package):
            failed_packages.append(package)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Installation Summary:")
    
    if failed_packages:
        print(f"❌ {len(failed_packages)} packages failed to install:")
        for package in failed_packages:
            print(f"   - {package}")
        print("\n💡 Try installing them manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
    else:
        print("✅ All packages installed successfully!")
    
    # Test imports
    print("\n🧪 Testing imports...")
    test_packages = {
        "ultralytics": "YOLOv8",
        "transformers": "Transformers",
        "cv2": "OpenCV",
        "folium": "Folium",
        "torch": "PyTorch",
        "torchvision": "TorchVision"
    }
    
    failed_imports = []
    
    for module, name in test_packages.items():
        try:
            __import__(module)
            print(f"✅ {name} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {name}: {e}")
            failed_imports.append(name)
    
    # Final instructions
    print("\n" + "=" * 50)
    if failed_imports:
        print("⚠️  Some imports failed. Please check the errors above.")
        print("The ML services may not work correctly.")
    else:
        print("🎉 All ML/AI dependencies are ready!")
        print("You can now start the Jodettu server:")
        print("   python main.py")
        print("\nThe AI services will be available at:")
        print("   /Jodettu/ai/ - Object detection and classification")
        print("   /Jodettu/location/ - Location services")
        print("   /Jodettu/translation/ - Translation services")

if __name__ == "__main__":
    main()
