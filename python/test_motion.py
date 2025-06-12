#!/usr/bin/env python3
"""
Test motion regressor extraction for MIDT pipeline.
"""

import sys
import os
from pathlib import Path

# Add the pipeline to Python path
sys.path.insert(0, '/home/uqahonne/uq/fmri_pipe/midt-python-pipeline')

from midt_pipeline.config import MIDTConfig
from midt_pipeline.motion import extract_motion_regressors

def test_motion_extraction():
    """Test motion regressor extraction with real data."""
    print("=== Testing Motion Regressor Extraction ===")
    
    # Create test configuration
    config = MIDTConfig(
        base_dir="/home/uqahonne/uq/fmri_pipe/midt-python-pipeline/test_output",
        behavioral_dir="/home/uqahonne/uq/fmri_pipe/new_code/new_code/behavioral_data",
        fmriprep_dir="/home/uqahonne/uq/fmri_pipe/new_code/new_code/fmriprep",
        subject_ids=["sub-017"],
        sessions_to_process=["1"],
        tr=1.6,
        smooth_fwhm=6,
        n_volumes=367,
        dummy_scans=5
    )
    
    # Create output directories
    config.create_output_directories()
    
    try:
        # Extract motion regressors
        summary = extract_motion_regressors(config)
        
        print(f"✅ Motion extraction successful!")
        print(f"   Processed: {summary['successful_subjects']}/{summary['total_subjects']} subjects")
        
        if summary['qc_data']:
            qc = summary['qc_data'][0]
            print(f"   Max motion: {qc['max_motion_mm']:.3f} mm")
            print(f"   Mean motion: {qc['mean_motion_mm']:.3f} mm")
            print(f"   Motion parameters: {qc['available_params']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Motion extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_motion_file_loading():
    """Test loading extracted motion files."""
    print("\n=== Testing Motion File Loading ===")
    
    from midt_pipeline.motion import load_motion_regressors
    
    motion_file = "/home/uqahonne/uq/fmri_pipe/midt-python-pipeline/test_output/motion_regressors/ses-1/sub-017/sub-017_ses-1_task-MIDT_Regressors.txt"
    
    try:
        if Path(motion_file).exists():
            motion_data = load_motion_regressors(motion_file)
            print(f"✅ Motion file loaded successfully!")
            print(f"   Shape: {motion_data.shape}")
            print(f"   Range: {motion_data.min():.4f} to {motion_data.max():.4f}")
            return True
        else:
            print(f"❌ Motion file not found: {motion_file}")
            return False
            
    except Exception as e:
        print(f"❌ Motion file loading failed: {e}")
        return False

def main():
    """Run motion extraction tests."""
    print("🧪 MIDT Motion Regressor Test")
    print("Testing with sub-017, session 1")
    print("=" * 50)
    
    # Test 1: Motion extraction
    extraction_success = test_motion_extraction()
    
    # Test 2: File loading
    loading_success = test_motion_file_loading()
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 MOTION TEST SUMMARY")
    print(f"   Motion extraction: {'✅ PASS' if extraction_success else '❌ FAIL'}")
    print(f"   File loading: {'✅ PASS' if loading_success else '❌ FAIL'}")
    
    if extraction_success and loading_success:
        print("\n🎉 All motion tests passed!")
    else:
        print("\n⚠️  Some tests failed.")

if __name__ == "__main__":
    main()