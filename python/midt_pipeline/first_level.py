"""
First-level GLM analysis module for MIDT pipeline.

This module handles first-level statistical analysis using nilearn.
Converted from run_first_level_analysis.m.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

from nilearn.glm.first_level import FirstLevelModel
from nilearn.interfaces.fmriprep import load_confounds
from nilearn.image import load_img
import nibabel as nib


def run_first_level_midt(config, subject_id: str, session: str = '1') -> bool:
    """Run first-level GLM analysis for MIDT task.
    
    This function replaces the MATLAB run_first_level_analysis.m function
    using nilearn instead of SPM12.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object with analysis parameters
    subject_id : str
        Subject identifier (BIDS format)
    session : str, default '1'
        Session identifier
        
    Returns
    -------
    bool
        True if analysis completed successfully
    """
    
    print(f"\nProcessing subject: {subject_id}, session: {session}")
    
    # Setup output directory
    subject_output_dir = Path(config.first_level_dir) / f'ses-{session}' / subject_id
    subject_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define file paths
    events_file = Path(config.timing_dir) / f'ses-{session}' / f'{subject_id}_ses-{session}_task-MIDT_events.tsv'
    
    # Find functional data file
    func_file = find_functional_file(config.fmriprep_dir, subject_id, session, config.smooth_fwhm)
    if func_file is None:
        print(f"  WARNING: Functional data not found for {subject_id}")
        return False
    
    # Find confounds file
    confounds_file = find_confounds_file(config.fmriprep_dir, subject_id, session)
    if confounds_file is None:
        print(f"  WARNING: Confounds file not found for {subject_id}")
        return False
    
    # Check if required files exist
    if not events_file.exists():
        print(f"  WARNING: Events file not found: {events_file}")
        return False
    
    try:
        # Load events
        events_df = pd.read_csv(events_file, sep='\t')
        print(f"  Loaded {len(events_df)} events")
        
        # Load confounds - check if dummy scan removal is needed based on fMRI data
        fmri_img = load_img(func_file)
        n_timepoints_fmri = fmri_img.shape[3]
        
        # Read confounds file to check timepoints
        confounds_raw = pd.read_csv(confounds_file, sep='\t')
        n_timepoints_confounds = len(confounds_raw)
        
        print(f"  fMRI timepoints: {n_timepoints_fmri}, Confounds timepoints: {n_timepoints_confounds}")
        
        # For MIDT pipeline, we assume dummy scans need to be removed consistently
        # The fMRI data should have dummy scans removed, and confounds should match
        if n_timepoints_fmri == n_timepoints_confounds:
            # Both have same timepoints - need to remove dummy scans from both
            dummy_scans_to_remove = config.dummy_scans
            print(f"  Will remove {dummy_scans_to_remove} dummy scans from confounds")
        elif n_timepoints_fmri == (n_timepoints_confounds - config.dummy_scans):
            # Confounds already have dummy scans removed
            dummy_scans_to_remove = config.dummy_scans
            print(f"  Confounds already have dummy scans removed")
        else:
            print(f"  WARNING: Unexpected timepoint mismatch - using confounds as-is")
            dummy_scans_to_remove = 0
        
        # Try to load extracted motion regressors first, fallback to direct confounds
        motion_regressor_file = Path(config.motion_regressor_dir) / f'ses-{session}' / subject_id / \
                               f'{subject_id}_ses-{session}_task-{config.task}_Regressors.txt'
        
        if motion_regressor_file.exists():
            # Use extracted motion regressors (dummy scans already removed during extraction)
            from .motion import load_motion_regressors
            motion_data = load_motion_regressors(str(motion_regressor_file), 0)  # Don't remove again
            
            # Create DataFrame with proper column names
            motion_columns = config.motion_params[:motion_data.shape[1]]
            confounds_df = pd.DataFrame(motion_data, columns=motion_columns)
            print(f"  Loaded extracted motion regressors: {confounds_df.shape[1]} parameters")
        else:
            # Fallback to loading from confounds file
            confounds_df = load_midt_confounds(confounds_file, dummy_scans_to_remove)
            print(f"  Loaded confounds from fMRIPrep: {confounds_df.shape[1]} regressors")
        
        # Setup and fit GLM
        glm = FirstLevelModel(
            t_r=config.tr,
            hrf_model='spm',  # Use SPM canonical HRF for consistency
            smoothing_fwhm=None,  # Data already smoothed
            high_pass=1/config.hpf,  # Convert from period to frequency
            standardize=False,
            noise_model='ar1',
            drift_model=None,  # High-pass filter handles this
            memory=None,
            verbose=1
        )
        
        print("  Fitting GLM...")
        
        # Load fMRI data and remove dummy scans
        fmri_img = load_img(func_file)
        print(f"  Original fMRI shape: {fmri_img.shape}")
        
        # Remove first 5 volumes (dummy scans)
        if fmri_img.shape[3] > config.dummy_scans:
            from nilearn.image import index_img
            fmri_img_trimmed = index_img(fmri_img, slice(config.dummy_scans, None))
            print(f"  After removing {config.dummy_scans} dummy scans: {fmri_img_trimmed.shape}")
        else:
            fmri_img_trimmed = fmri_img
            print(f"  WARNING: Not enough volumes to remove dummy scans")
        
        print(f"  Confounds shape: {confounds_df.shape}")
        print(f"  Events: {len(events_df)} events")
        
        # Verify timepoint matching
        if fmri_img_trimmed.shape[3] != confounds_df.shape[0]:
            raise ValueError(f"Timepoint mismatch: fMRI has {fmri_img_trimmed.shape[3]} volumes, "
                           f"confounds have {confounds_df.shape[0]} timepoints")
        
        glm.fit(fmri_img_trimmed, events=events_df, confounds=confounds_df)
        
        # Compute contrasts
        contrasts = define_midt_contrasts()
        print(f"  Computing {len(contrasts)} contrasts...")
        
        for contrast_name, contrast_weights in contrasts.items():
            try:
                # Get design matrix
                design_matrix = glm.design_matrices_[0]
                
                # Get design matrix columns to check available conditions
                condition_columns = [col for col in design_matrix.columns 
                                   if not col.startswith(('drift', 'constant'))]
                
                # Use condition name-based contrasts for single run
                if contrast_name == 'anticip-reward':
                    contrast_def = 'anticip-reward'
                elif contrast_name == 'anticip-neutral':
                    contrast_def = 'anticip-neutral'
                elif contrast_name == 'feedback-reward-success':
                    contrast_def = 'fb-reward'
                elif contrast_name == 'feedback-neutral-success':
                    contrast_def = 'fb-corr-neutral'
                elif contrast_name == 'anticip-reward-vs-neutral':
                    # Create contrast using numpy array
                    if 'anticip-reward' in condition_columns and 'anticip-neutral' in condition_columns:
                        contrast_vector = np.zeros(len(condition_columns))
                        contrast_vector[condition_columns.index('anticip-reward')] = 1
                        contrast_vector[condition_columns.index('anticip-neutral')] = -1
                        contrast_def = contrast_vector
                    else:
                        print(f"    Skipping {contrast_name}: missing conditions")
                        continue
                elif contrast_name == 'feedback-reward-vs-neutral-correct':
                    if 'fb-reward' in condition_columns and 'fb-corr-neutral' in condition_columns:
                        contrast_vector = np.zeros(len(condition_columns))
                        contrast_vector[condition_columns.index('fb-reward')] = 1
                        contrast_vector[condition_columns.index('fb-corr-neutral')] = -1
                        contrast_def = contrast_vector
                    else:
                        print(f"    Skipping {contrast_name}: missing conditions")
                        continue
                elif contrast_name == 'feedback-reward-success-vs-failure':
                    if 'fb-reward' in condition_columns and 'fb-miss-reward' in condition_columns:
                        contrast_vector = np.zeros(len(condition_columns))
                        contrast_vector[condition_columns.index('fb-reward')] = 1
                        contrast_vector[condition_columns.index('fb-miss-reward')] = -1
                        contrast_def = contrast_vector
                    else:
                        print(f"    Skipping {contrast_name}: missing conditions")
                        continue
                elif contrast_name == 'feedback-neutral-success-vs-failure':
                    if 'fb-corr-neutral' in condition_columns and 'fb-incorr-neutral' in condition_columns:
                        contrast_vector = np.zeros(len(condition_columns))
                        contrast_vector[condition_columns.index('fb-corr-neutral')] = 1
                        contrast_vector[condition_columns.index('fb-incorr-neutral')] = -1
                        contrast_def = contrast_vector
                    else:
                        print(f"    Skipping {contrast_name}: missing conditions")
                        continue
                else:
                    # Skip other complex contrasts for now
                    print(f"    Skipping complex contrast: {contrast_name}")
                    continue
                
                # Compute contrast
                contrast_img = glm.compute_contrast(
                    contrast_def, 
                    output_type='effect_size'
                )
                
                # Save contrast image
                contrast_filename = (
                    f'{subject_id}_ses-{session}_task-MIDT_'
                    f'contrast-{contrast_name}_stat-effect.nii.gz'
                )
                contrast_path = subject_output_dir / contrast_filename
                contrast_img.to_filename(str(contrast_path))
                
                # Compute and save statistical map
                stat_img = glm.compute_contrast(
                    contrast_def, 
                    output_type='stat'
                )
                
                stat_filename = (
                    f'{subject_id}_ses-{session}_task-MIDT_'
                    f'contrast-{contrast_name}_stat-t.nii.gz'
                )
                stat_path = subject_output_dir / stat_filename
                stat_img.to_filename(str(stat_path))
                
            except Exception as e:
                print(f"    WARNING: Failed to compute contrast {contrast_name}: {e}")
                continue
        
        # Save design matrix
        design_matrix = glm.design_matrices_[0]
        design_filename = f'{subject_id}_ses-{session}_task-MIDT_design-matrix.tsv'
        design_path = subject_output_dir / design_filename
        design_matrix.to_csv(design_path, sep='\t', float_format='%.6f')
        
        print(f"  ✓ First-level analysis completed for {subject_id}")
        return True
        
    except Exception as e:
        print(f"  ERROR: Failed to process {subject_id}: {e}")
        return False


def find_functional_file(fmriprep_dir: str, subject_id: str, session: str, 
                        smooth_fwhm: int) -> Optional[str]:
    """Find the preprocessed functional file.
    
    Parameters
    ----------
    fmriprep_dir : str
        fMRIPrep derivatives directory
    subject_id : str
        Subject ID
    session : str
        Session ID
    smooth_fwhm : int
        Smoothing kernel size
        
    Returns
    -------
    str or None
        Path to functional file, or None if not found
    """
    
    func_dir = Path(fmriprep_dir) / subject_id / f'ses-{session}' / 'func'
    
    # Try different possible naming patterns
    patterns = [
        f'{subject_id}_ses-{session}_task-MIDT_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold_{smooth_fwhm}mm_blur.nii',
        f'{subject_id}_ses-{session}_task-MIDT_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold_{smooth_fwhm}mm_blur.nii.gz',
        f'{subject_id}_ses-{session}_task-MIDT_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz',
        f'{subject_id}_ses-{session}_task-MIDT_space-MNI152NLin2009cAsym_desc-preproc_bold.nii'
    ]
    
    for pattern in patterns:
        func_file = func_dir / pattern
        if func_file.exists():
            return str(func_file)
    
    return None


def find_confounds_file(fmriprep_dir: str, subject_id: str, session: str) -> Optional[str]:
    """Find the confounds file.
    
    Parameters
    ----------
    fmriprep_dir : str
        fMRIPrep derivatives directory
    subject_id : str
        Subject ID
    session : str
        Session ID
        
    Returns
    -------
    str or None
        Path to confounds file, or None if not found
    """
    
    func_dir = Path(fmriprep_dir) / subject_id / f'ses-{session}' / 'func'
    confounds_file = func_dir / f'{subject_id}_ses-{session}_task-MIDT_desc-confounds_timeseries.tsv'
    
    if confounds_file.exists():
        return str(confounds_file)
    
    return None


def load_midt_confounds(confounds_file: str, dummy_scans: int = 5) -> pd.DataFrame:
    """Load motion and other confounds for MIDT analysis.
    
    Parameters
    ----------
    confounds_file : str
        Path to fMRIPrep confounds file
    dummy_scans : int, default 5
        Number of initial volumes to exclude
        
    Returns
    -------
    pd.DataFrame
        Confounds DataFrame with selected regressors
    """
    
    try:
        # Use nilearn's built-in confound loading
        confounds_df, _ = load_confounds(
            confounds_file,
            strategy=['motion', 'wm_csf', 'global_signal'],
            motion='basic',  # 6 motion parameters
            wm_csf='basic',  # Mean WM and CSF signals
            global_signal='basic',  # Global signal
            demean=True
        )
        
        # Remove dummy scans
        if dummy_scans > 0:
            confounds_df = confounds_df.iloc[dummy_scans:].reset_index(drop=True)
        
        return confounds_df
        
    except Exception as e:
        print(f"    Warning: Could not load confounds with nilearn, trying manual loading: {e}")
        
        # Fallback to manual loading
        confounds_raw = pd.read_csv(confounds_file, sep='\t')
        
        # Select basic motion parameters
        motion_params = [
            'trans_x', 'trans_y', 'trans_z',
            'rot_x', 'rot_y', 'rot_z'
        ]
        
        confounds_selected = []
        for param in motion_params:
            if param in confounds_raw.columns:
                confounds_selected.append(param)
        
        # Add tissue signals if available
        tissue_params = ['csf', 'white_matter', 'global_signal']
        for param in tissue_params:
            if param in confounds_raw.columns:
                confounds_selected.append(param)
        
        if not confounds_selected:
            raise ValueError("No usable confound regressors found")
        
        confounds_df = confounds_raw[confounds_selected].fillna(0)
        
        # Remove dummy scans
        if dummy_scans > 0:
            confounds_df = confounds_df.iloc[dummy_scans:].reset_index(drop=True)
        
        return confounds_df


def define_midt_contrasts() -> Dict[str, List[float]]:
    """Define standard contrasts for MIDT analysis.
    
    Returns
    -------
    Dict[str, List[float]]
        Dictionary mapping contrast names to contrast vectors
    """
    
    # MIDT conditions (same order as in events):
    # 1. anticip-reward
    # 2. anticip-neutral  
    # 3. fb-reward
    # 4. fb-miss-reward
    # 5. fb-corr-neutral
    # 6. fb-incorr-neutral
    
    contrasts = {
        'anticip-reward-vs-neutral': [1, -1, 0, 0, 0, 0],
        'anticip-neutral-vs-reward': [-1, 1, 0, 0, 0, 0],
        'feedback-reward-vs-neutral-correct': [0, 0, 1, 0, -1, 0],
        'feedback-neutral-correct-vs-reward': [0, 0, -1, 0, 1, 0],
        'feedback-reward-success-vs-failure': [0, 0, 1, -1, 0, 0],
        'feedback-reward-failure-vs-success': [0, 0, -1, 1, 0, 0],
        'feedback-neutral-success-vs-failure': [0, 0, 0, 0, 1, -1],
        'feedback-neutral-failure-vs-success': [0, 0, 0, 0, -1, 1],
        'anticip-reward': [1, 0, 0, 0, 0, 0],
        'anticip-neutral': [0, 1, 0, 0, 0, 0],
        'feedback-reward-success': [0, 0, 1, 0, 0, 0],
        'feedback-neutral-success': [0, 0, 0, 0, 1, 0]
    }
    
    return contrasts


def generate_first_level_report(glm, events_df: pd.DataFrame, 
                              output_dir: str, subject_id: str) -> str:
    """Generate quality control report for first-level analysis.
    
    Parameters
    ----------
    glm : FirstLevelModel
        Fitted GLM object
    events_df : pd.DataFrame
        Events DataFrame
    output_dir : str
        Output directory
    subject_id : str
        Subject ID
        
    Returns
    -------
    str
        Path to generated HTML report
    """
    
    try:
        from nilearn.reporting import make_glm_report
        
        # Define contrasts for report
        contrasts = {
            'Anticip: Reward > Neutral': [1, -1, 0, 0, 0, 0],
            'Feedback: Reward > Neutral': [0, 0, 1, 0, -1, 0]
        }
        
        # Generate report
        report = make_glm_report(
            glm,
            contrasts=contrasts,
            title=f"MIDT First-Level Analysis: {subject_id}",
            cluster_threshold=15,
            height_control='fdr',
            alpha=0.05
        )
        
        # Save report
        report_path = Path(output_dir) / f'{subject_id}_first-level-report.html'
        report.save_as_html(str(report_path))
        
        print(f"  ✓ QC report saved: {report_path}")
        return str(report_path)
        
    except ImportError:
        print("  Warning: Could not generate report (nilearn reporting not available)")
        return ""
    except Exception as e:
        print(f"  Warning: Could not generate report: {e}")
        return ""