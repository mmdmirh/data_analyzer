from .validator import DatasetValidator
from .scanner import DatasetScanner

import json
from pathlib import Path

def run_full_scan(dataset_root):
    """
    Runs full pipeline:
    1. Validation
    2. Scanning
    3. Metadata Loading
    
    Returns a dictionary with:
    - all keys from scanner (total_videos, video_files, etc.)
    - 'worker_data': loaded content of fine_grained_labels_with_worker_ids.json
    - 'labels_data': loaded content of QEVD-FIT-COACH/fine_grained_labels.json
    """
    root = Path(dataset_root).resolve()
    
    # 1. Validation
    print("DEBUG: Library: Starting validation...")
    validator = DatasetValidator(root)
    validator.validate_all()
    
    # 2. Scanning
    print("DEBUG: Library: Starting scan...")
    scanner = DatasetScanner(root)
    scan_results = scanner.scan_dataset()
    
    # Check results
    video_files = scan_results.get('video_files', set())
    print(f"DEBUG: Library found {len(video_files)} unique video files.")
    
    if len(video_files) == 0:
        print("WARNING: Library: No videos found! Check your directory structure.")
    
    # 3. Load Metadata
    print("DEBUG: Library: Loading metadata...")
    worker_path = root / "fine_grained_labels_with_worker_ids.json"
    labels_path = root / "QEVD-FIT-COACH" / "fine_grained_labels.json"
    
    worker_data = []
    labels_data = []
    
    if worker_path.exists():
        with open(worker_path, 'r') as f:
            worker_data = json.load(f)
        print(f"DEBUG: Library: Loaded {len(worker_data)} worker records")
    else:
        print(f"WARNING: Library: {worker_path.name} not found")

    if labels_path.exists():
        with open(labels_path, 'r') as f:
            labels_data = json.load(f)
        print(f"DEBUG: Library: Loaded {len(labels_data)} label records")
    else:
        print(f"WARNING: Library: {labels_path.name} not found")
        
    # Merge results
    scan_results['worker_data'] = worker_data
    scan_results['labels_data'] = labels_data
    
    return scan_results

__all__ = ["DatasetValidator", "DatasetScanner", "run_full_scan"]
