"""
Utility functions for MIDT pipeline.

This module contains helper functions for file management, validation,
and other common operations.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import numpy as np


def check_environment():
    """Check that required packages are available."""
    
    required_packages = {
        'nilearn': 'nilearn',
        'nibabel': 'nibabel', 
        'pandas': 'pandas',
        'numpy': 'numpy',
        'sklearn': 'scikit-learn'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    print("✓ All required packages available")
    return True


def validate_bids_structure(data_dir: str, required_files: List[str] = None) -> bool:
    """Validate basic BIDS directory structure.
    
    Parameters
    ----------
    data_dir : str
        Path to BIDS dataset
    required_files : list, optional
        List of required files to check for
        
    Returns
    -------
    bool
        True if structure is valid
    """
    
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Data directory does not exist: {data_dir}")
        return False
    
    # Check for basic BIDS structure
    has_subjects = any(item.name.startswith('sub-') for item in data_path.iterdir() if item.is_dir())
    
    if not has_subjects:
        print(f"No subject directories found in: {data_dir}")
        return False
    
    print(f"✓ Valid BIDS structure found in: {data_dir}")
    return True


def create_directory_structure(base_dir: str, subdirs: List[str]):
    """Create directory structure for pipeline outputs.
    
    Parameters
    ----------
    base_dir : str
        Base directory path
    subdirs : list
        List of subdirectory names to create
    """
    
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    for subdir in subdirs:
        subdir_path = base_path / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {subdir_path}")


def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """Find files matching a pattern in a directory.
    
    Parameters
    ----------
    directory : str
        Directory to search in
    pattern : str
        Glob pattern to match
        
    Returns
    -------
    list
        List of matching file paths
    """
    
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    
    return [str(f) for f in dir_path.glob(pattern)]


def log_processing_step(step_name: str, subject_id: str, status: str, 
                       log_file: Optional[str] = None):
    """Log processing step status.
    
    Parameters
    ----------
    step_name : str
        Name of processing step
    subject_id : str
        Subject identifier
    status : str
        Status ('success', 'failed', 'skipped')
    log_file : str, optional
        Path to log file
    """
    
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {step_name} | {subject_id} | {status}\n"
    
    if log_file:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    else:
        print(log_entry.strip())


def generate_processing_summary(log_file: str) -> Dict:
    """Generate summary statistics from processing log.
    
    Parameters
    ----------
    log_file : str
        Path to log file
        
    Returns
    -------
    dict
        Summary statistics
    """
    
    if not Path(log_file).exists():
        return {}
    
    log_df = pd.read_csv(log_file, sep=' | ', header=None, 
                        names=['timestamp', 'step', 'subject', 'status'])
    
    summary = {
        'total_subjects': len(log_df['subject'].unique()),
        'total_steps': len(log_df),
        'success_rate': (log_df['status'] == 'success').mean(),
        'by_step': log_df.groupby('step')['status'].value_counts().to_dict(),
        'by_subject': log_df.groupby('subject')['status'].value_counts().to_dict()
    }
    
    return summary


def check_disk_space(directory: str, required_gb: float = 10.0) -> bool:
    """Check available disk space.
    
    Parameters
    ----------
    directory : str
        Directory to check
    required_gb : float
        Required space in GB
        
    Returns
    -------
    bool
        True if sufficient space available
    """
    
    try:
        stat = os.statvfs(directory)
        available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        
        if available_gb < required_gb:
            print(f"Warning: Only {available_gb:.1f} GB available in {directory}")
            print(f"Recommended: {required_gb} GB")
            return False
        
        print(f"✓ Sufficient disk space: {available_gb:.1f} GB available")
        return True
        
    except Exception as e:
        print(f"Could not check disk space: {e}")
        return True  # Assume OK if can't check


def estimate_processing_time(n_subjects: int, n_sessions: int = 1) -> str:
    """Estimate total processing time.
    
    Parameters
    ----------
    n_subjects : int
        Number of subjects
    n_sessions : int
        Number of sessions per subject
        
    Returns
    -------
    str
        Estimated processing time
    """
    
    # Rough estimates (in minutes per subject per session)
    time_estimates = {
        'events_extraction': 0.5,
        'first_level_analysis': 8.0,
        'qc_generation': 1.0
    }
    
    total_minutes = sum(time_estimates.values()) * n_subjects * n_sessions
    
    if total_minutes < 60:
        return f"{total_minutes:.0f} minutes"
    elif total_minutes < 1440:  # 24 hours
        hours = total_minutes / 60
        return f"{hours:.1f} hours"
    else:
        days = total_minutes / 1440
        return f"{days:.1f} days"


def safe_parallel_processing(func, items: List, n_jobs: int = 1, **kwargs):
    """Safely run parallel processing with error handling.
    
    Parameters
    ----------
    func : callable
        Function to run in parallel
    items : list
        Items to process
    n_jobs : int
        Number of parallel jobs
    **kwargs
        Additional arguments to pass to function
        
    Returns
    -------
    list
        Results from successful processing
    """
    
    if n_jobs == 1:
        # Sequential processing
        results = []
        for item in items:
            try:
                result = func(item, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error processing {item}: {e}")
                results.append(None)
        return results
    
    try:
        from joblib import Parallel, delayed
        
        results = Parallel(n_jobs=n_jobs, verbose=1)(
            delayed(func)(item, **kwargs) for item in items
        )
        return results
        
    except ImportError:
        print("Warning: joblib not available, falling back to sequential processing")
        return safe_parallel_processing(func, items, n_jobs=1, **kwargs)
    except Exception as e:
        print(f"Error in parallel processing: {e}")
        print("Falling back to sequential processing")
        return safe_parallel_processing(func, items, n_jobs=1, **kwargs)