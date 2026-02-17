from .validator import DatasetValidator
from .scanner import DatasetScanner

def run_full_scan(dataset_root):
    """
    Convenience function to run both validation and scanning in one pipeline.
    """
    validator = DatasetValidator(dataset_root)
    validator.validate_all()
    
    scanner = DatasetScanner(dataset_root)
    return scanner.scan_dataset()

__all__ = ["DatasetValidator", "DatasetScanner", "run_full_scan"]
