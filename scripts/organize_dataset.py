import os
import shutil
import yaml
from pathlib import Path
from tqdm import tqdm

# Configuration
DATA_DIR = Path("data")
RAW_DATA_DIR = DATA_DIR / "raw" / "animals"
PROCESSED_DIR = DATA_DIR / "processed"

# Set random seed for reproducibility
import random
random.seed(42)

def parse_data_yaml(yaml_path: Path) -> dict:
    """Parse the data.yaml file to get class names and paths."""
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data

def get_class_mapping(yaml_path: Path) -> dict:
    """Get class index to name mapping from data.yaml."""
    data = parse_data_yaml(yaml_path)
    return {i: name for i, name in enumerate(data['names'])}

def organize_dataset():
    # Check if the dataset exists
    if not RAW_DATA_DIR.exists():
        print(f"Error: Dataset not found at {RAW_DATA_DIR}")
        return
    
    # Check for data.yaml
    yaml_path = RAW_DATA_DIR / 'data.yaml'
    if not yaml_path.exists():
        print(f"Error: data.yaml not found in {RAW_DATA_DIR}")
        return
    
    # Get class mapping
    try:
        class_mapping = get_class_mapping(yaml_path)
        print(f"Found {len(class_mapping)} classes: {list(class_mapping.values())}")
    except Exception as e:
        print(f"Error parsing data.yaml: {e}")
        return
    
    # Create processed directory structure
    for split in ['train', 'val', 'test']:
        for class_name in class_mapping.values():
            (PROCESSED_DIR / split / class_name).mkdir(parents=True, exist_ok=True)
    
    # Process each split
    for split in ['train', 'val', 'test']:
        print(f"\nProcessing {split} split...")
        
        # Define split directory paths
        split_dir = RAW_DATA_DIR / split
        if not split_dir.exists():
            print(f"  Warning: {split} directory not found in {RAW_DATA_DIR}, skipping...")
            continue
            
        images_dir = split_dir / 'images'
        labels_dir = split_dir / 'labels'
        
        if not images_dir.exists():
            print(f"  Warning: {images_dir} not found, skipping {split}...")
            continue
            
        if not labels_dir.exists():
            print(f"  Warning: {labels_dir} not found, skipping {split}...")
            continue
            
        # Process each image
        image_files = list(images_dir.glob('*.*'))
        print(f"  Found {len(image_files)} images in {split}")
        
        for img_path in tqdm(image_files, desc=f"  Processing {split} images"):
            # Get corresponding label file
                label_path = labels_dir / f"{img_path.stem}.txt"
            
            if not label_path.exists():
                print(f"  Warning: Label file not found for {img_path}")
                continue
                
            # Read the first line to get the class
            try:
                with open(label_path, 'r') as f:
                    first_line = f.readline().strip()
                    if not first_line:
                        print(f"  Warning: Empty label file: {label_path}")
                        continue
                        
                    class_id = int(first_line.split()[0])
                    class_name = class_mapping.get(class_id)
                    
                    if not class_name:
                        print(f"  Warning: Unknown class ID {class_id} in {label_path}")
                        continue
                    
                    # Create destination directory
                    dest_dir = PROCESSED_DIR / split / class_name
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy image and label
                    shutil.copy2(img_path, dest_dir / img_path.name)
                    
            except Exception as e:
                print(f"  Error processing {img_path}: {e}")
    
    print("\nDataset organization complete!")
    print(f"Processed dataset saved to: {PROCESSED_DIR}")
    
    # Create a new data.yaml for the processed dataset
    processed_yaml = {
        'path': str(PROCESSED_DIR.absolute()),
        'train': 'train',
        'val': 'val',
        'test': 'test',
        'names': class_mapping,
        'nc': len(class_mapping)
    }
    
    with open(PROCESSED_DIR / 'data.yaml', 'w') as f:
        yaml.dump(processed_yaml, f, default_flow_style=False)
    
    print("\nCreated processed data.yaml with the following structure:")
    print(f"- Training images: {len(list((PROCESSED_DIR / 'train').rglob('*.jpg')))} images")
    print(f"- Validation images: {len(list((PROCESSED_DIR / 'val').rglob('*.jpg')))} images")
    print(f"- Test images: {len(list((PROCESSED_DIR / 'test').rglob('*.jpg')))} images")

if __name__ == "__main__":
    organize_dataset()
