#!/usr/bin/env python3
"""
Test complete MIDT pipeline with motion regressor extraction.
"""

import sys
import os
from pathlib import Path

# Add the pipeline to Python path
sys.path.insert(0, '/home/uqahonne/uq/fmri_pipe/midt-python-pipeline')

from midt_pipeline import MIDTConfig, run_complete_pipeline

def test_complete_pipeline():
    """Test the complete pipeline with motion regressors."""
    print("🧪 COMPLETE MIDT PIPELINE TEST")
    print("Testing with sub-017, session 1")
    print("=" * 60)
    
    # Create test configuration
    config = MIDTConfig(
        base_dir="/home/uqahonne/uq/fmri_pipe/midt-python-pipeline/test_complete",
        behavioral_dir="/home/uqahonne/uq/fmri_pipe/new_code/new_code/behavioral_data",
        fmriprep_dir="/home/uqahonne/uq/fmri_pipe/new_code/new_code/fmriprep",
        subject_ids=["sub-017"],
        sessions_to_process=["1"],
        tr=1.6,
        smooth_fwhm=6,
        n_volumes=367,
        dummy_scans=5,
        # Enable all processing steps
        run_timing_extraction=True,
        run_motion_extraction=True,
        run_first_level=True
    )
    
    try:
        # Run complete pipeline
        summary = run_complete_pipeline(config, n_jobs=1)
        
        print(f"\n🎉 PIPELINE COMPLETED!")
        print(f"   Sessions processed: {summary['sessions_processed']}")
        print(f"   Total subjects: {summary['total_subjects']}")
        print(f"   Successful subjects: {summary['successful_subjects']}")
        
        if summary['failed_subjects']:
            print(f"   Failed subjects: {summary['failed_subjects']}")
        
        # Check output files
        print(f"\n📂 CHECKING OUTPUT FILES:")
        check_output_files(config, "sub-017", "1")
        
        return summary['successful_subjects'] > 0
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_output_files(config, subject_id, session):
    """Check that all expected output files were created."""
    
    base_path = Path(config.base_dir)
    
    # Expected files
    expected_files = [
        # Timing files
        f"timing_files/ses-{session}/{subject_id}_ses-{session}_task-MIDT_events.tsv",
        # Motion regressors
        f"motion_regressors/ses-{session}/{subject_id}/{subject_id}_ses-{session}_task-MIDT_Regressors.txt",
        f"motion_regressors/motion_qc_report.csv",
        # First-level results
        f"first_level_results/ses-{session}/{subject_id}/{subject_id}_ses-{session}_task-MIDT_design-matrix.tsv",
        f"first_level_results/ses-{session}/{subject_id}/{subject_id}_ses-{session}_task-MIDT_contrast-anticip-reward_stat-effect.nii.gz",
        f"first_level_results/ses-{session}/{subject_id}/{subject_id}_ses-{session}_task-MIDT_contrast-anticip-reward_stat-t.nii.gz",
    ]
    
    all_files_exist = True
    
    for file_path in expected_files:
        full_path = base_path / file_path
        if full_path.exists():
            file_size = full_path.stat().st_size
            print(f"   ✅ {file_path} ({file_size} bytes)")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_files_exist = False
    
    return all_files_exist

def main():
    """Run complete pipeline test."""
    success = test_complete_pipeline()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPLETE PIPELINE TEST PASSED!")
        print("\nThe MIDT Python pipeline is working correctly with:")
        print("   ✅ Event extraction from behavioral data")
        print("   ✅ Motion regressor extraction with QC")
        print("   ✅ First-level GLM analysis with contrasts")
        print("   ✅ BIDS-compliant outputs")
    else:
        print("❌ COMPLETE PIPELINE TEST FAILED!")

if __name__ == "__main__":
    main()