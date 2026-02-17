import os
import shutil
from pathlib import Path

class DatasetValidator:
    """
    Validates the QEVD dataset structure according to the official download instructions.
    
    Structure Requirements:
    - QEVD-FIT-300K: 4 Parts, combined zip, extracted folder.
      - Naming: QEVD-FIT-300k-Part-X.zip (combined) -> extracted content.
    - QEVD-FIT-COACH: QEVD-FIT-COACH.zip -> extracted -> fine_grained_labels.json, etc.
    - Benchmarks: Specific zip names and extracted content.
    """
    
    def __init__(self, dataset_root: str):
        self.root = Path(dataset_root).resolve()
        
    def validate_downloaded_files(self) -> dict:
        """
        Checks for the presence of required zip files and partition parts.
        Returns a status dict: { 'part_name': {'status': 'ok'|'missing'|'partial', 'files': []} }
        """
        status = {}
        
        # 1. QEVD-FIT-300K Parts 1-4
        for part_num in range(1, 5):
            part_name = f"QEVD-FIT-300k-Part-{part_num}"
            # Pattern: QEVD-FIT-300k-Part-X.z* (e.g. .z01, .z02, .zip)
            # Or the combined file: combined-part-X.zip
            
            # Check for combined file first (as per instruction step 2)
            combined_zip = self.root / f"combined-part-{part_num}.zip"
            # Or original naming if they skipped rename? Instruction says: zip -FF ... --out combined-part-X.zip
            
            # Check for original split files
            split_files = sorted(list(self.root.glob(f"{part_name}.z*")))
            
            if combined_zip.exists():
                status[part_name] = {"status": "ready_to_extract", "files": [combined_zip.name]}
            elif split_files:
                status[part_name] = {"status": "downloaded_raw", "files": [f.name for f in split_files]}
            else:
                status[part_name] = {"status": "missing", "files": []}

        # 2. QEVD-FIT-COACH
        coach_zip = self.root / "QEVD-FIT-COACH.zip"
        status["QEVD-FIT-COACH"] = {
            "status": "present" if coach_zip.exists() else "missing",
            "files": [coach_zip.name] if coach_zip.exists() else []
        }
        
        # 3. Benchmark & Competition
        for name in ["QEVD-FIT-COACH-Benchmark", "QEVD-FIT-COACH-Competition-CVPR2025"]:
            zip_file = self.root / f"{name}.zip"
            status[name] = {
                "status": "present" if zip_file.exists() else "missing",
                "files": [zip_file.name] if zip_file.exists() else []
            }
            
        return status

    def interactive_validation(self):
        """
        Validates structure and asks user about missing parts.
        """
        print(f"Validating dataset at: {self.root}")
        status = self.validate_downloaded_files()
        
        missing = []
        for name, info in status.items():
            s = info['status']
            if s == 'missing':
                missing.append(name)
            elif s == 'downloaded_raw':
                print(f"[INFO] {name}: Raw split files found. Need to combine (zip -FF).")
            elif s == 'ready_to_extract':
                print(f"[OK] {name}: Combined zip ready.")
            elif s == 'present':
                print(f"[OK] {name}: Zip present.")
        
        if missing:
            print(f"\n[WARNING] Missing parts: {', '.join(missing)}")
            resp = input("Do you want to download unexisted files? (yes/no): ").strip().lower()
            if resp in ['yes', 'y']:
                print("Please download the missing files from the official repository and place them in the root folder.")
                # We cannot automate the actual download without URLs/AUTH, so we instruct.
            else:
                print("Proceeding with partial dataset...")
        else:
            print("\n[SUCCESS] All download parts are present.")

    def validate_dataset_structure(self) -> bool:
        """
        Validates the extracted folder structure.
        """
        print("\nChecking extracted structure...")
        all_good = True
        
        # Check FitCoach Extraction
        # Expected: fine_grained_labels.json in root (from Step 4 of 300K instr? No, Step 4 says "Combine all... File structure: fine_grained_labels.json")
        # Actually, QEVD-FIT-COACH instructions say: "Once extracted... find: fine_grained_labels.json, feedbacks_short_clips.json..."
        
        required_files = [
            "fine_grained_labels.json",
            "fine_grained_labels_with_worker_ids.json",
            "feedbacks_short_clips.json",
            "feedbacks_long_range.json",
            "questions.json"
        ]
        
        for fname in required_files:
            if not (self.root / fname).exists():
                # Check inside QEVD-FIT-COACH folder? Instruction says "extract to current folder".
                # But sometimes users extract to folder.
                if (self.root / "QEVD-FIT-COACH" / fname).exists():
                     pass # OK, inside folder
                else:
                    print(f"[MISSING] {fname} not found in root or QEVD-FIT-COACH subdirectory.")
                    all_good = False
        
        # Check if 300K videos are in 'short_clips/' as per Coach instr Step 3
        # "Download all files from 300K and unzip them to 'short_clips/' folder"
        short_clips = self.root / "short_clips"
        if not short_clips.exists():
            print("[MISSING] 'short_clips/' folder not found. (Required for 300K video storage)")
            all_good = False
        else:
            # Check if empty
            if not any(short_clips.iterdir()):
                 print("[WARNING] 'short_clips/' folder exists but appears empty.")
        
        return all_good
