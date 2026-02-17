import pandas as pd
import os
import json

class DataProcessor:
    """
    Processes the scanned dataset metadata to identify eligible subjects
    and filter videos based on labels and availability.
    """
    def __init__(self, scan_results: dict):
        """
        Initialize with the dictionary returned by run_full_scan.
        """
        self.worker_data = scan_results.get('worker_data', [])
        self.labels_data = scan_results.get('labels_data', [])
        self.available_files = scan_results.get('video_files', set())
        
        self.merged_df = None
        self.filtered_df = None
        
        # Initialize the dataframe immediately
        self._create_initial_df()

    def _create_initial_df(self):
        """Creates the initial merged dataframe from worker and label data."""
        if not self.worker_data or not self.labels_data:
            print("WARNING: DataProcessor: Metadata is empty.")
            self.merged_df = pd.DataFrame()
            return

        worker_df = pd.DataFrame(self.worker_data)
        labels_df = pd.DataFrame(self.labels_data)
        
        # Merge on video_path
        # Assuming inner join is desired to ensure we have both worker ID and labels
        self.merged_df = pd.merge(worker_df, labels_df, on='video_path', how='inner')

    def filter_by_label_prefix(self, prefix: str = "squats"):
        """
        Filters the dataframe for videos where at least one label starts with the prefix.
        Updates self.filtered_df.
        """
        if self.merged_df is None or self.merged_df.empty:
            print("WARNING: DataProcessor: merged_df is empty.")
            self.filtered_df = pd.DataFrame()
            return

        def has_prefix(label_list):
            if not isinstance(label_list, list): return False
            return any(l.startswith(prefix) for l in label_list)
            
        # Create a copy to avoid SettingWithCopy warnings on subsequent operations
        self.filtered_df = self.merged_df[self.merged_df['labels'].apply(has_prefix)].copy()
        print(f"DEBUG: DataProcessor: Filtered for '{prefix}': {len(self.filtered_df)} videos.")

    def filter_available_files(self):
        """
        Filters self.filtered_df to include only files that actually exist 
        (based on the scan results).
        """
        if self.filtered_df is None or self.filtered_df.empty:
            return

        # Extract filename for matching
        self.filtered_df['filename'] = self.filtered_df['video_path'].apply(lambda x: os.path.basename(x))
        
        # Check existence
        self.filtered_df['exists'] = self.filtered_df['filename'].isin(self.available_files)
        
        # Filter
        original_count = len(self.filtered_df)
        self.filtered_df = self.filtered_df[self.filtered_df['exists']].copy()
        
        print(f"DEBUG: DataProcessor: Verified availability. {len(self.filtered_df)}/{original_count} videos found.")

    def find_eligible_subjects(self, good_keywords: list, bad_keywords: list, min_good=1, min_bad=1, strict_good=True) -> list:
        """
        Groups by worker_id and identifies subjects with sufficient good and bad videos.
        
        Args:
            good_keywords: list of strings indicating "good" technique.
            bad_keywords: list of strings indicating "bad" technique.
            min_good: minimum number of good videos required.
            min_bad: minimum number of bad videos required.
            strict_good: if True, a "good" video must NOT have any "bad" labels.
            
        Returns:
            List of dictionaries containing subject stats.
        """
        if self.filtered_df is None or self.filtered_df.empty:
            print("WARNING: DataProcessor: No data to process for subjects.")
            return []

        eligible_subjects = []
        grouped = self.filtered_df.groupby('worker_id')
        
        print(f"DEBUG: DataProcessor: Analyzing {len(grouped)} workers...")

        for worker_id, group in grouped:
            def has_label_match(labels, keywords):
                if not keywords: return False
                # Check if any label contains any keyword substring
                return any(any(k in l for k in keywords) for l in labels)

            # Identify Good and Bad candidates based on keywords
            # merged_df has 'labels' column which is a list of strings
            
            is_good = group['labels'].apply(lambda l: has_label_match(l, good_keywords))
            is_bad = group['labels'].apply(lambda l: has_label_match(l, bad_keywords))
            
            if strict_good:
                # "Good" means matches good keywords AND does NOT match bad keywords
                # (e.g. "deep" but not "deep but fast")
                good_videos = group[is_good & (~is_bad)]
            else:
                good_videos = group[is_good]
                
            bad_videos = group[is_bad]
            
            if len(good_videos) >= min_good and len(bad_videos) >= min_bad:
                eligible_subjects.append({
                    'worker_id': int(worker_id),
                    'good_count': len(good_videos),
                    'bad_count': len(bad_videos),
                    'total_videos': len(group),
                    'good_samples': good_videos['video_path'].tolist(),
                    'bad_samples': bad_videos['video_path'].tolist()
                })
        
        # Sort by total videos descending
        eligible_subjects.sort(key=lambda x: x['total_videos'], reverse=True)
        print(f"DEBUG: DataProcessor: Found {len(eligible_subjects)} eligible subjects.")
        return eligible_subjects

    def save_eligible_subjects(self, subjects: list, output_path: str):
        """Saves values to JSON."""
        try:
            with open(output_path, "w") as f:
                json.dump(subjects, f, indent=2)
            print(f"DEBUG: Saved eligible subjects to {output_path}")
        except Exception as e:
            print(f"ERROR: Could not save to {output_path}: {e}")
