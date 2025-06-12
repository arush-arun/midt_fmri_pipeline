#!/usr/bin/env python3
"""
Simple script to run MIDT pipeline.
Update the paths below for your data and run: python run_midt.py
"""

import sys
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from midt_pipeline import MIDTConfig, run_complete_pipeline

def main():
    """Run MIDT pipeline with your data."""
    
    # ============================================
    # UPDATE THESE PATHS FOR YOUR DATA
    # ============================================
    
    config = MIDTConfig(
        # Output directory (where results will be saved)
        base_dir="/home/uqahonne/uq/fmri_pipe/midt-python-pipeline/new_test_12062025",
        
        # Input data directories  
        behavioral_dir="/home/uqahonne/uq/fmri_pipe/new_code/new_code/behavioral_data",
        fmriprep_dir="/home/uqahonne/uq/fmri_pipe/new_code/new_code/fmriprep",
        
        # Subject list - ADD YOUR SUBJECTS HERE
        subject_ids=[
            "sub-009",
            "sub-017", 
            "sub-135"
            # Add more subjects...
        ],
        
        # Sessions to process
        sessions_to_process=["1"],  # or ["1", "2"] for multiple sessions
        
        # Acquisition parameters (update if different)
        tr=1.6,
        n_volumes=367,  # after removing dummy scans
        dummy_scans=5,
        smooth_fwhm=6,
        
        # Processing options
        run_timing_extraction=True,
        run_motion_extraction=True, 
        run_first_level=True,
        
        # Optional: Exclude problematic subjects
        excluded_subjects=[
            # ["sub-XXX", "reason", "ses-X"]
        ]
    )
    
    # ============================================
    # RUN PIPELINE
    # ============================================
    
    print("🚀 Starting MIDT Analysis Pipeline")
    print(f"📁 Output directory: {config.base_dir}")
    print(f"👥 Subjects: {len(config.subject_ids)}")
    print(f"📊 Sessions: {config.sessions_to_process}")
    
    try:
        # Run complete pipeline
        summary = run_complete_pipeline(
            config, 
            n_jobs=4  # Change to 4 or 8 for parallel processing
        )
        
        # Print results
        print(f"\n🎉 PIPELINE COMPLETED!")
        print(f"✅ Successful subjects: {summary['successful_subjects']}")
        print(f"❌ Failed subjects: {len(summary['failed_subjects'])}")
        
        if summary['failed_subjects']:
            print(f"Failed: {summary['failed_subjects']}")
            
        print(f"📂 Results saved in: {config.base_dir}")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()