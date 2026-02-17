import os
import json
import zipfile
from pathlib import Path
from collections import defaultdict

class DatasetScanner:
    """
    Scans the QEVD dataset to inventory available files and labels.
    """
    
    def __init__(self, dataset_root: str):
        self.root = Path(dataset_root).resolve()
        
    def scan_dataset(self) -> dict:
        """
        Scans the dataset for video files (mp4) and label files (json).
        Scanning includes checking inside zip archives if present.
        
        Returns a summary dictionary.
        """
        print(f"Scanning dataset at: {self.root} ...")
        
        video_files = set()
        zip_contents = defaultdict(list)
        
        # 1. Scan filesystem (unpacked)
        for f in self.root.rglob("*.mp4"):
            video_files.add(f.name)
            
        print(f"[SCAN] Found {len(video_files)} unpacked video files.")
        
        # 2. Scan zip archives
        zip_files = list(self.root.rglob("*.zip"))
        print(f"[SCAN] Found {len(zip_files)} zip archives. Scanning contents...")
        
        for zf_path in zip_files:
            try:
                # Try standard zipfile
                with zipfile.ZipFile(zf_path, 'r') as zf:
                    names = zf.namelist()
                    mp4s = [os.path.basename(n) for n in names if n.endswith('.mp4')]
                    zip_contents[zf_path.name] = len(mp4s)
                    video_files.update(mp4s)
            except (zipfile.BadZipFile, NotImplementedError):
                 print(f"[WARNING] Standard zipfile failed for {zf_path.name}. Attempting 7z fallback...")
                 import subprocess
                 try:
                     # 7z l archive.zip
                     result = subprocess.run(["7z", "l", str(zf_path)], capture_output=True, text=True)
                     if result.returncode == 0:
                         # Parse output
                         count_7z = 0
                         for line in result.stdout.splitlines():
                             if ".mp4" in line:
                                 # 7z output format varies, usually ends with filename
                                 filename = line.strip().split()[-1]
                                 if filename.endswith(".mp4"):
                                     video_files.add(os.path.basename(filename))
                                     count_7z += 1
                         print(f"[SCAN] Found {count_7z} mp4s in {zf_path.name} (via 7z)")
                         zip_contents[zf_path.name] = count_7z
                     else:
                         print(f"[ERROR] 7z failed with code {result.returncode}")
                 except Exception as e2:
                      print(f"[ERROR] 7z fallback failed: {e2}")
            except Exception as e:
                print(f"[WARNING] Error reading {zf_path.name}: {e}")
                
        total_videos = len(video_files)
        print(f"[SCAN] Total Unique Video Files (Unpacked + Zipped): {total_videos}")
        
        # 3. Check Labels
        label_files = [
            "fine_grained_labels.json",
            "feedbacks_short_clips.json", 
            "feedbacks_long_range.json",
            "questions.json"
        ]
        
        labels_found = {}
        for lf in label_files:
            # Check root or potential subdirs
            candidates = list(self.root.rglob(lf))
            if candidates:
                labels_found[lf] = str(candidates[0])
            else:
                labels_found[lf] = "MISSING"
                
        return {
            "total_videos": total_videos,
            "unpacked_videos": len([f for f in self.root.rglob("*.mp4")]),
            "zip_archives": len(zip_files),
            "labels": labels_found,
            "video_files": video_files  # Expose file list for analysis
        }
