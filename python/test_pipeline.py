#!/usr/bin/env python3
"""
Test script for MIDT Python Pipeline with real data.
Testing with sub-017, session 1.
"""

import sys
import os
from pathlib import Path

# Add the pipeline to Python path
sys.path.insert(0, '/home/uqahonne/uq/fmri_pipe/midt-python-pipeline')

from midt_pipeline.config import MIDTConfig
from midt_pipeline.events import extract_midt_events
from midt_pipeline.first_level import run_first_level_midt

def test_events_extraction():
    """Test event extraction with real behavioral data."""
    print("=== Testing Event Extraction ===")
    
    # Setup paths
    timing_file = "/home/uqahonne/uq/fmri_pipe/new_code/new_code/behavioral_data/Reward_task_ld017s2_reward_1_dollar.txt"
    output_dir = "/home/uqahonne/uq/fmri_pipe/midt-python-pipeline/test_output/timing_files/ses-1"
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Extract events
        events_df = extract_midt_events(
            timing_file=timing_file,
            output_dir=output_dir,
            session='1',
            subject_id='sub-017'
        )
        
        print(f"✅ Event extraction successful!")
        print(f"   Extracted {len(events_df)} events")
        print(f"   Conditions: {events_df['trial_type'].unique()}")
        print(f"   Onset range: {events_df['onset'].min():.2f} - {events_df['onset'].max():.2f} seconds")
        
        return True, events_df
        
    except Exception as e:
        print(f"❌ Event extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_first_level_analysis():
    """Test first-level analysis with real fMRI data."""
    print("\n=== Testing First-Level Analysis ===")
    
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
        # Run first-level analysis
        success = run_first_level_midt(config, "sub-017", "1")
        
        if success:
            print("✅ First-level analysis successful!")
        else:
            print("❌ First-level analysis failed")
            
        return success
        
    except Exception as e:
        print(f"❌ First-level analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete test."""
    print("🧪 MIDT Python Pipeline Test")
    print("Testing with sub-017, session 1")
    print("=" * 50)
    
    # Test 1: Event extraction
    events_success, events_df = test_events_extraction()
    
    if not events_success:
        print("\n❌ Cannot proceed to first-level analysis without events")
        return
    
    # Test 2: First-level analysis
    first_level_success = test_first_level_analysis()
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print(f"   Events extraction: {'✅ PASS' if events_success else '❌ FAIL'}")
    print(f"   First-level analysis: {'✅ PASS' if first_level_success else '❌ FAIL'}")
    
    if events_success and first_level_success:
        print("\n🎉 All tests passed! Pipeline is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()