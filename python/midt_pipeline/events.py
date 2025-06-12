"""
Event extraction module for MIDT pipeline.

This module handles conversion of behavioral timing files to BIDS events format.
Converted from extract_midt_onsets.m.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import re
import warnings


def extract_midt_events(timing_file: str, output_dir: str, session: str = '1', 
                       subject_id: Optional[str] = None) -> pd.DataFrame:
    """Extract MIDT onset and duration times from timing files.
    
    Converts behavioral timing files to BIDS-compliant events.tsv format.
    This function replaces the MATLAB extract_midt_onsets.m function.
    
    Parameters
    ----------
    timing_file : str
        Path to the behavioral timing file (.txt format)
    output_dir : str  
        Directory to save the output events file
    session : str, default '1'
        Session identifier
    subject_id : str, optional
        Subject ID. If None, will be extracted from filename
        
    Returns
    -------
    pd.DataFrame
        BIDS events DataFrame with columns: onset, duration, trial_type, response_time, accuracy
    """
    
    # Extract subject ID if not provided
    if subject_id is None:
        subject_id = extract_subject_from_filename(timing_file)
        if subject_id is None:
            raise ValueError(f"Could not extract subject ID from filename: {timing_file}")
    
    # Ensure BIDS format
    bids_subject_id = convert_to_bids_format(subject_id)
    
    # Read timing data with manual parsing to handle inconsistent columns
    try:
        with open(timing_file, 'r') as f:
            lines = f.readlines()
        
        # Process each line manually to handle varying column counts
        header = lines[0].strip().split('\t')
        data_rows = []
        
        for line in lines[1:]:
            if line.strip():  # Skip empty lines
                row_data = line.strip().split('\t')
                # Pad with empty strings if too short, truncate if too long
                if len(row_data) < len(header):
                    row_data.extend([''] * (len(header) - len(row_data)))
                elif len(row_data) > len(header):
                    row_data = row_data[:len(header)]
                data_rows.append(row_data)
        
        timing_data = pd.DataFrame(data_rows, columns=header)
        
        # Convert numeric columns
        numeric_columns = ['trial_number', 'acc', 'rt', 'min', 'cti_duration', 
                          'target_duration', 'iti_duration', 'onsettime_cue', 
                          'onsettime_target', 'onsettime_feedback', 'totalreward']
        
        for col in numeric_columns:
            if col in timing_data.columns:
                timing_data[col] = pd.to_numeric(timing_data[col], errors='coerce')
            
    except Exception as e:
        raise ValueError(f"Error reading timing file {timing_file}: {e}")
    
    # Validate timing data structure
    if timing_data.empty:
        raise ValueError(f"Timing file is empty: {timing_file}")
    
    # Process trials (typically trials 21-80 in MIDT, corresponding to rows 20-79 in 0-indexed)
    trial_start = 20  # 0-indexed (was 21 in MATLAB 1-indexed)
    trial_end = min(79, len(timing_data) - 1)  # 0-indexed
    
    events_list = []
    
    for trial_idx in range(trial_start, trial_end + 1):
        try:
            event_data = process_single_trial(timing_data, trial_idx)
            if event_data:
                events_list.extend(event_data)
        except Exception as e:
            warnings.warn(f"Error processing trial {trial_idx}: {e}")
            continue
    
    if not events_list:
        raise ValueError(f"No valid trials found in timing file: {timing_file}")
    
    # Create events DataFrame
    events_df = pd.DataFrame(events_list)
    
    # Sort by onset time
    events_df = events_df.sort_values('onset').reset_index(drop=True)
    
    # Adjust onset times for dummy scan removal (assuming config is available)
    # For now, use a default of 5 dummy scans and 1.6s TR
    dummy_scans = 5
    tr = 1.6
    dummy_scan_time = dummy_scans * tr  # 8.0 seconds
    
    # Subtract dummy scan time from all onsets
    events_df['onset'] = events_df['onset'] - dummy_scan_time
    
    # Remove any events with negative onsets (before dummy scan period)
    events_df = events_df[events_df['onset'] >= 0].reset_index(drop=True)
    
    print(f"  Adjusted onsets for {dummy_scans} dummy scans ({dummy_scan_time}s)")
    print(f"  Events after dummy scan adjustment: {len(events_df)}")
    
    # Save as BIDS events.tsv
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"{bids_subject_id}_ses-{session}_task-MIDT_events.tsv"
    output_file = output_dir / output_filename
    
    events_df.to_csv(output_file, sep='\t', index=False, float_format='%.3f')
    
    print(f"  Saved events file: {output_filename}")
    print(f"    Reward anticipation trials: {len(events_df[events_df.trial_type == 'anticip-reward'])}")
    print(f"    Neutral anticipation trials: {len(events_df[events_df.trial_type == 'anticip-neutral'])}")
    print(f"    Total events: {len(events_df)}")
    
    return events_df


def process_single_trial(timing_data: pd.DataFrame, trial_idx: int) -> List[dict]:
    """Process a single trial and extract events.
    
    Parameters
    ----------
    timing_data : pd.DataFrame
        Full timing data
    trial_idx : int
        Trial index (0-based)
        
    Returns
    -------
    List[dict]
        List of event dictionaries for this trial
    """
    
    events = []
    
    # Get trial data based on actual MIDT file structure
    try:
        # Get cue type (column 3: cue_type)
        cue_type = timing_data.iloc[trial_idx, 2]  # 0-indexed column 2 = cue_type
        
        # Get accuracy (column 4: acc)
        accuracy = timing_data.iloc[trial_idx, 3]  # 0-indexed column 3 = acc
        
        # Get timing data (columns 10, 11, 12: onsettime_cue, onsettime_target, onsettime_feedback)
        cue_onset = timing_data.iloc[trial_idx, 9] / 1000  # Convert from ms to seconds
        cue_offset = timing_data.iloc[trial_idx, 10] / 1000  # onsettime_target = cue offset
        feedback_onset = timing_data.iloc[trial_idx, 11] / 1000
            
    except (IndexError, KeyError) as e:
        warnings.warn(f"Missing data for trial {trial_idx}: {e}")
        return events
    
    # Calculate durations
    cue_duration = cue_offset - cue_onset
    feedback_duration = 2.0  # Fixed feedback duration
    
    # Determine trial type and create events
    if 'smile' in str(cue_type).lower():  # Reward trial
        # Anticipation event
        events.append({
            'onset': cue_onset,
            'duration': cue_duration,
            'trial_type': 'anticip-reward',
            'accuracy': accuracy,
            'response_time': np.nan  # Could add RT if available
        })
        
        # Feedback event
        if accuracy == 1:
            trial_type = 'fb-reward'
        else:
            trial_type = 'fb-miss-reward'
            
        events.append({
            'onset': feedback_onset,
            'duration': feedback_duration,
            'trial_type': trial_type,
            'accuracy': accuracy,
            'response_time': np.nan
        })
        
    elif 'neutral' in str(cue_type).lower():  # Neutral trial
        # Anticipation event
        events.append({
            'onset': cue_onset,
            'duration': cue_duration,
            'trial_type': 'anticip-neutral',
            'accuracy': accuracy,
            'response_time': np.nan
        })
        
        # Feedback event
        if accuracy == 1:
            trial_type = 'fb-corr-neutral'
        else:
            trial_type = 'fb-incorr-neutral'
            
        events.append({
            'onset': feedback_onset,
            'duration': feedback_duration,
            'trial_type': trial_type,
            'accuracy': accuracy,
            'response_time': np.nan
        })
    
    return events


def extract_subject_from_filename(filename: str) -> Optional[str]:
    """Extract subject ID from filename using various patterns.
    
    Parameters
    ----------
    filename : str
        Input filename
        
    Returns
    -------
    str or None
        Extracted subject ID, or None if not found
    """
    
    filename = Path(filename).name  # Get just the filename, not full path
    
    # Define patterns (same as MATLAB version)
    patterns = [
        r'Reward_task_([^_]+)_reward',
        r'task_([^_]+)_',
        r'^([^_]+)_',
        r'([a-zA-Z]*\d+[a-zA-Z]*\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    return None


def convert_to_bids_format(original_id: str) -> str:
    """Convert subject ID to BIDS format.
    
    Parameters
    ----------
    original_id : str
        Original subject identifier
        
    Returns
    -------
    str
        BIDS-formatted subject ID (sub-XXX)
    """
    
    if not original_id:
        return 'sub-unknown'
    
    # Pattern 1: ld###s# format
    match = re.match(r'^ld(\d+)s\d*$', original_id)
    if match:
        subject_num = int(match.group(1))
        return f'sub-{subject_num:03d}'
    
    # Pattern 2: sub### format
    match = re.match(r'^sub(\d+)$', original_id)
    if match:
        subject_num = int(match.group(1))
        return f'sub-{subject_num:03d}'
    
    # Pattern 3: Just numbers
    match = re.match(r'^(\d+)$', original_id)
    if match:
        subject_num = int(match.group(1))
        return f'sub-{subject_num:03d}'
    
    # Pattern 4: Already BIDS format
    if re.match(r'^sub-\d{3}$', original_id):
        return original_id
    
    # Fallback: extract any numbers
    match = re.search(r'(\d+)', original_id)
    if match:
        subject_num = int(match.group(1))
        return f'sub-{subject_num:03d}'
    
    # Last resort: clean and prefix
    clean_id = re.sub(r'[^a-zA-Z0-9]', '', original_id)
    return f'sub-{clean_id}'


def validate_events_file(events_df: pd.DataFrame) -> bool:
    """Validate that events DataFrame follows BIDS specification.
    
    Parameters
    ----------
    events_df : pd.DataFrame
        Events DataFrame to validate
        
    Returns
    -------
    bool
        True if valid, raises ValueError if not
    """
    
    required_columns = ['onset', 'duration', 'trial_type']
    missing_columns = [col for col in required_columns if col not in events_df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required BIDS columns: {missing_columns}")
    
    # Check for negative onsets or durations
    if (events_df['onset'] < 0).any():
        raise ValueError("Found negative onset times")
    
    if (events_df['duration'] < 0).any():
        raise ValueError("Found negative durations")
    
    # Check for expected MIDT trial types
    expected_types = {
        'anticip-reward', 'anticip-neutral', 
        'fb-reward', 'fb-miss-reward', 
        'fb-corr-neutral', 'fb-incorr-neutral'
    }
    
    found_types = set(events_df['trial_type'].unique())
    unexpected_types = found_types - expected_types
    
    if unexpected_types:
        warnings.warn(f"Found unexpected trial types: {unexpected_types}")
    
    return True