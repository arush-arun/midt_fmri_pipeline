"""
Motion regressor extraction module for MIDT pipeline.

This module handles extraction of motion parameters from fMRIPrep confounds files.
Converted from extract_motion_regressors.m.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings


def extract_motion_regressors(config) -> Dict:
    """Extract motion parameters from fMRIPrep confounds files.
    
    This function replaces the MATLAB extract_motion_regressors.m function.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object with analysis parameters
        
    Returns
    -------
    dict
        Summary of motion regressor extraction
    """
    
    print(f'Starting motion regressor extraction for {len(config.subject_ids)} subjects')
    
    qc_data = []
    processing_summary = {
        'total_subjects': len(config.subject_ids),
        'successful_subjects': 0,
        'failed_subjects': [],
        'qc_data': []
    }
    
    for i, subject_id in enumerate(config.subject_ids):
        print(f'\nProcessing subject {i+1}/{len(config.subject_ids)}: {subject_id}')
        
        for session in config.sessions_to_process:
            print(f'  Session {session}... ', end='')
            
            try:
                # Create subject-specific output directory
                subject_output_dir = Path(config.motion_regressor_dir) / f'ses-{session}' / subject_id
                subject_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Find confounds file
                confounds_file = Path(config.fmriprep_dir) / subject_id / f'ses-{session}' / 'func' / \
                                f'{subject_id}_ses-{session}_task-{config.task}_desc-confounds_timeseries.tsv'
                
                output_file = subject_output_dir / f'{subject_id}_ses-{session}_task-{config.task}_Regressors.txt'
                
                if not confounds_file.exists():
                    print('SKIP (confound file not found)')
                    continue
                
                # Extract motion data and compute QC metrics
                motion_data, qc_metrics = extract_subject_motion(str(confounds_file), config)
                
                # Save motion regressors
                save_motion_regressors(motion_data, str(output_file))
                
                # Store QC data
                qc_metrics['subject_id'] = subject_id
                qc_metrics['session'] = session
                qc_data.append(qc_metrics)
                
                print(f'SUCCESS (max motion: {qc_metrics["max_motion_mm"]:.2f} mm)')
                processing_summary['successful_subjects'] += 1
                
            except Exception as e:
                print(f'ERROR: {e}')
                processing_summary['failed_subjects'].append(f'{subject_id}_ses-{session}')
    
    # Generate QC report
    processing_summary['qc_data'] = qc_data
    if qc_data:
        generate_motion_qc_report(qc_data, config.motion_regressor_dir)
    
    return processing_summary


def extract_subject_motion(confounds_file: str, config) -> Tuple[np.ndarray, Dict]:
    """Extract motion parameters for a single subject.
    
    Parameters
    ----------
    confounds_file : str
        Path to fMRIPrep confounds file
    config : MIDTConfig
        Configuration object
        
    Returns
    -------
    motion_data : np.ndarray
        Motion parameter matrix (timepoints x parameters)
    qc_metrics : dict
        Quality control metrics
    """
    
    # Read confounds file
    confounds_df = pd.read_csv(confounds_file, sep='\t')
    
    n_volumes_total = len(confounds_df)
    n_volumes_analysis = n_volumes_total - config.dummy_scans
    
    # Extract motion parameters
    motion_data = []
    available_params = []
    
    for param_name in config.motion_params:
        if param_name in confounds_df.columns:
            param_data = confounds_df[param_name].values
            # Remove dummy scans
            param_data = param_data[config.dummy_scans:]
            motion_data.append(param_data)
            available_params.append(param_name)
        else:
            warnings.warn(f"Motion parameter '{param_name}' not found in confounds file")
    
    if not motion_data:
        raise ValueError("No motion parameters found in confounds file")
    
    motion_data = np.column_stack(motion_data)
    
    # Calculate QC metrics
    qc_metrics = calculate_motion_qc(motion_data, available_params)
    qc_metrics['n_volumes'] = n_volumes_analysis
    qc_metrics['available_params'] = available_params
    
    return motion_data, qc_metrics


def calculate_motion_qc(motion_data: np.ndarray, motion_params: List[str]) -> Dict:
    """Calculate motion quality control metrics.
    
    Parameters
    ----------
    motion_data : np.ndarray
        Motion parameter matrix
    motion_params : list
        List of motion parameter names
        
    Returns
    -------
    dict
        QC metrics including max and mean motion
    """
    
    qc_metrics = {}
    
    # Find translation parameters (in mm)
    trans_idx = [i for i, param in enumerate(motion_params) if 'trans' in param]
    
    if trans_idx:
        trans_data = motion_data[:, trans_idx]
        # Calculate Euclidean distance for translation
        translation_euclidean = np.sqrt(np.sum(trans_data**2, axis=1))
        
        qc_metrics['max_motion_mm'] = np.max(translation_euclidean)
        qc_metrics['mean_motion_mm'] = np.mean(translation_euclidean)
        qc_metrics['std_motion_mm'] = np.std(translation_euclidean)
        
        # Additional QC metrics
        qc_metrics['max_abs_displacement'] = np.max(np.abs(trans_data))
        qc_metrics['mean_abs_displacement'] = np.mean(np.abs(trans_data))
    else:
        qc_metrics['max_motion_mm'] = np.nan
        qc_metrics['mean_motion_mm'] = np.nan
        qc_metrics['std_motion_mm'] = np.nan
        qc_metrics['max_abs_displacement'] = np.nan
        qc_metrics['mean_abs_displacement'] = np.nan
    
    # Find rotation parameters (in radians, convert to degrees)
    rot_idx = [i for i, param in enumerate(motion_params) if 'rot' in param]
    
    if rot_idx:
        rot_data = motion_data[:, rot_idx]
        rot_data_deg = np.degrees(rot_data)  # Convert to degrees
        
        qc_metrics['max_rotation_deg'] = np.max(np.abs(rot_data_deg))
        qc_metrics['mean_rotation_deg'] = np.mean(np.abs(rot_data_deg))
    else:
        qc_metrics['max_rotation_deg'] = np.nan
        qc_metrics['mean_rotation_deg'] = np.nan
    
    return qc_metrics


def save_motion_regressors(motion_data: np.ndarray, output_file: str):
    """Save motion regressors to text file.
    
    Parameters
    ----------
    motion_data : np.ndarray
        Motion parameter matrix
    output_file : str
        Output file path
    """
    
    # Ensure output directory exists
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save with high precision
    np.savetxt(output_file, motion_data, fmt='%.6f', delimiter=' ')
    
    print(f'    Saved motion regressors: {Path(output_file).name}')


def generate_motion_qc_report(qc_data: List[Dict], output_dir: str):
    """Generate quality control report for motion parameters.
    
    Parameters
    ----------
    qc_data : list
        List of QC dictionaries for each subject/session
    output_dir : str
        Output directory for QC report
    """
    
    if not qc_data:
        return
    
    # Convert to DataFrame
    qc_df = pd.DataFrame(qc_data)
    
    # Generate summary statistics
    print('\n=== MOTION QUALITY CONTROL REPORT ===')
    print(f'Total subjects processed: {len(qc_df)}')
    
    if 'max_motion_mm' in qc_df.columns and not qc_df['max_motion_mm'].isna().all():
        print(f'Maximum motion range: {qc_df["max_motion_mm"].min():.2f} - {qc_df["max_motion_mm"].max():.2f} mm')
        print(f'Mean maximum motion: {qc_df["max_motion_mm"].mean():.2f} ± {qc_df["max_motion_mm"].std():.2f} mm')
        
        # Count subjects with high motion
        high_motion_threshold = 2.0  # mm
        high_motion_subjects = qc_df[qc_df['max_motion_mm'] > high_motion_threshold]
        print(f'Subjects with motion > {high_motion_threshold} mm: {len(high_motion_subjects)} ({len(high_motion_subjects)/len(qc_df)*100:.1f}%)')
    
    # Save detailed QC report
    qc_file = Path(output_dir) / 'motion_qc_report.csv'
    qc_df.to_csv(qc_file, index=False, float_format='%.4f')
    print(f'QC report saved to: {qc_file}')


def load_motion_regressors(motion_file: str, dummy_scans: int = 0) -> np.ndarray:
    """Load motion regressors from file.
    
    Parameters
    ----------
    motion_file : str
        Path to motion regressors file
    dummy_scans : int
        Number of dummy scans to remove (if not already removed)
        
    Returns
    -------
    np.ndarray
        Motion regressor matrix
    """
    
    if not Path(motion_file).exists():
        raise FileNotFoundError(f"Motion regressors file not found: {motion_file}")
    
    motion_data = np.loadtxt(motion_file)
    
    # Remove dummy scans if needed
    if dummy_scans > 0:
        motion_data = motion_data[dummy_scans:]
    
    return motion_data


def validate_motion_regressors(motion_data: np.ndarray, n_expected_volumes: int) -> bool:
    """Validate motion regressor data.
    
    Parameters
    ----------
    motion_data : np.ndarray
        Motion regressor matrix
    n_expected_volumes : int
        Expected number of volumes
        
    Returns
    -------
    bool
        True if validation passes
    """
    
    if motion_data.shape[0] != n_expected_volumes:
        raise ValueError(f"Motion regressors have {motion_data.shape[0]} timepoints, "
                        f"expected {n_expected_volumes}")
    
    # Check for missing values
    if np.any(np.isnan(motion_data)):
        warnings.warn("Motion regressors contain NaN values")
    
    # Check for extreme values (likely errors)
    max_trans = np.max(np.abs(motion_data[:, :3])) if motion_data.shape[1] >= 3 else 0
    if max_trans > 20:  # 20mm seems extreme
        warnings.warn(f"Extreme translation values detected: {max_trans:.2f} mm")
    
    return True