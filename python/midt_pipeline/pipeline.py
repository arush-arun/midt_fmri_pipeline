"""
Main pipeline orchestration module.

This module handles the complete MIDT analysis pipeline execution.
Converted from run_complete_pipeline.m.
"""

from pathlib import Path
from typing import Dict, List, Optional
import warnings

from .config import MIDTConfig
from .events import extract_midt_events
from .motion import extract_motion_regressors
from .first_level import run_first_level_midt
from .utils import (
    check_environment, 
    log_processing_step,
    generate_processing_summary,
    check_disk_space,
    estimate_processing_time,
    safe_parallel_processing
)


def run_complete_pipeline(config: MIDTConfig, n_jobs: int = 1, 
                         log_file: Optional[str] = None) -> Dict:
    """Execute the complete MIDT analysis pipeline.
    
    This function replaces the MATLAB run_complete_pipeline.m function.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object with analysis parameters
    n_jobs : int, default 1
        Number of parallel jobs for subject processing
    log_file : str, optional
        Path to log file for tracking progress
        
    Returns
    -------
    dict
        Summary of pipeline execution
    """
    
    print("=== MIDT ANALYSIS PIPELINE (Python Edition) ===")
    
    # Check environment
    if not check_environment():
        raise RuntimeError("Environment check failed")
    
    # Check disk space
    check_disk_space(config.base_dir, required_gb=5.0)
    
    # Create output directories
    config.create_output_directories()
    
    # Initialize summary
    overall_summary = {
        'sessions_processed': [],
        'total_subjects': 0,
        'successful_subjects': 0,
        'failed_subjects': [],
        'processing_time': None
    }
    
    # Estimate processing time
    total_subjects = sum(len(config.get_valid_subjects_for_session(session)) 
                        for session in config.sessions_to_process)
    estimated_time = estimate_processing_time(total_subjects, len(config.sessions_to_process))
    print(f"Estimated processing time: {estimated_time}")
    
    # Process each session
    for session in config.sessions_to_process:
        print(f"\n🔄 ======= PROCESSING SESSION {session} ======= 🔄")
        
        session_subjects = config.get_valid_subjects_for_session(session)
        print(f"Session {session}: Processing {len(session_subjects)} subjects")
        
        if not session_subjects:
            print(f"No valid subjects for session {session}, skipping...")
            continue
        
        session_summary = process_single_session(
            config, session, session_subjects, n_jobs, log_file
        )
        
        # Update overall summary
        overall_summary['sessions_processed'].append(session)
        overall_summary['total_subjects'] += session_summary['total_subjects']
        overall_summary['successful_subjects'] += session_summary['successful_subjects']
        overall_summary['failed_subjects'].extend(session_summary['failed_subjects'])
        
        print(f"\n✅ Session {session} completed: "
              f"{session_summary['successful_subjects']}/{session_summary['total_subjects']} "
              f"subjects successful")
    
    # Generate final summary
    print(f"\n🎉 ======= COMPLETE PIPELINE FINISHED ======= 🎉")
    print(f"Sessions processed: {', '.join(overall_summary['sessions_processed'])}")
    print(f"Total subjects processed: {overall_summary['total_subjects']}")
    
    if overall_summary['total_subjects'] > 0:
        success_rate = (overall_summary['successful_subjects'] / 
                       overall_summary['total_subjects']) * 100
        print(f"Overall success rate: {success_rate:.1f}%")
    
    if overall_summary['failed_subjects']:
        print(f"Failed subjects: {', '.join(overall_summary['failed_subjects'])}")
    
    print(f"Results saved in: {config.base_dir}")
    
    # Generate processing summary if log file was used
    if log_file and Path(log_file).exists():
        summary_stats = generate_processing_summary(log_file)
        overall_summary['detailed_stats'] = summary_stats
    
    return overall_summary


def process_single_session(config: MIDTConfig, session: str, 
                          session_subjects: List[str], n_jobs: int = 1,
                          log_file: Optional[str] = None) -> Dict:
    """Process a single session for all subjects.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object
    session : str
        Session identifier
    session_subjects : list
        List of subject IDs for this session
    n_jobs : int
        Number of parallel jobs
    log_file : str, optional
        Log file path
        
    Returns
    -------
    dict
        Session processing summary
    """
    
    session_summary = {
        'session': session,
        'total_subjects': len(session_subjects),
        'successful_subjects': 0,
        'failed_subjects': []
    }
    
    # Step 1: Extract timing information
    if config.run_timing_extraction:
        print(f"\n--- STEP 1: EXTRACTING TIMING INFORMATION (Session {session}) ---")
        timing_success = extract_timing_for_session(config, session, log_file)
        if not timing_success:
            print(f"❌ Timing extraction failed for session {session}")
            return session_summary
    
    # Step 2: Extract Motion Regressors  
    if config.run_motion_extraction:
        print(f"\n--- STEP 2: EXTRACTING MOTION REGRESSORS (Session {session}) ---")
        motion_summary = extract_motion_regressors_for_session(config, session, session_subjects, log_file)
        if not motion_summary['success']:
            print(f"❌ Motion regressor extraction failed for session {session}")
            return session_summary
    
    # Step 3: First-level analysis
    if config.run_first_level:
        print(f"\n--- STEP 3: RUNNING FIRST-LEVEL ANALYSIS (Session {session}) ---")
        
        # Process subjects (with optional parallel processing)
        if n_jobs > 1:
            print(f"Processing {len(session_subjects)} subjects with {n_jobs} parallel jobs")
            
            def process_subject_wrapper(subject_id):
                return process_single_subject(config, subject_id, session, log_file)
            
            results = safe_parallel_processing(
                process_subject_wrapper, 
                session_subjects, 
                n_jobs=n_jobs
            )
            
            # Count successful subjects
            for i, result in enumerate(results):
                if result:
                    session_summary['successful_subjects'] += 1
                else:
                    session_summary['failed_subjects'].append(session_subjects[i])
        else:
            # Sequential processing
            for subject_id in session_subjects:
                success = process_single_subject(config, subject_id, session, log_file)
                if success:
                    session_summary['successful_subjects'] += 1
                else:
                    session_summary['failed_subjects'].append(subject_id)
    
    return session_summary


def extract_timing_for_session(config: MIDTConfig, session: str, 
                              log_file: Optional[str] = None) -> bool:
    """Extract timing information for all subjects in a session.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object
    session : str
        Session identifier
    log_file : str, optional
        Log file path
        
    Returns
    -------
    bool
        True if successful
    """
    
    try:
        # Find timing files in behavioral directory
        behavioral_path = Path(config.behavioral_dir)
        timing_files = list(behavioral_path.glob('*task*.txt'))
        
        if not timing_files:
            timing_files = list(behavioral_path.glob('Reward_task*.txt'))
        if not timing_files:
            timing_files = list(behavioral_path.glob('*.txt'))
        
        if not timing_files:
            print(f"❌ No timing files found in {config.behavioral_dir}")
            return False
        
        print(f"Found {len(timing_files)} timing files")
        
        # Process each timing file
        successful_extractions = 0
        failed_files = []
        
        output_dir = Path(config.timing_dir) / f'ses-{session}'
        
        for timing_file in timing_files:
            try:
                events_df = extract_midt_events(
                    str(timing_file), 
                    str(output_dir), 
                    session=session
                )
                successful_extractions += 1
                
                if log_file:
                    log_processing_step(
                        'timing_extraction', 
                        timing_file.stem, 
                        'success', 
                        log_file
                    )
                    
            except Exception as e:
                print(f"  ❌ Failed to process {timing_file.name}: {e}")
                failed_files.append(timing_file.name)
                
                if log_file:
                    log_processing_step(
                        'timing_extraction', 
                        timing_file.stem, 
                        'failed', 
                        log_file
                    )
        
        print(f"✅ Timing extraction completed: {successful_extractions} successful, "
              f"{len(failed_files)} failed")
        
        return successful_extractions > 0
        
    except Exception as e:
        print(f"❌ Error in timing extraction: {e}")
        return False


def process_single_subject(config: MIDTConfig, subject_id: str, session: str,
                          log_file: Optional[str] = None) -> bool:
    """Process a single subject through the pipeline.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object
    subject_id : str
        Subject identifier
    session : str
        Session identifier
    log_file : str, optional
        Log file path
        
    Returns
    -------
    bool
        True if successful
    """
    
    try:
        # Run first-level analysis
        success = run_first_level_midt(config, subject_id, session)
        
        status = 'success' if success else 'failed'
        if log_file:
            log_processing_step('first_level_analysis', subject_id, status, log_file)
        
        return success
        
    except Exception as e:
        print(f"❌ Error processing subject {subject_id}: {e}")
        
        if log_file:
            log_processing_step('first_level_analysis', subject_id, 'failed', log_file)
        
        return False


def extract_motion_regressors_for_session(config: MIDTConfig, session: str, 
                                         session_subjects: List[str],
                                         log_file: Optional[str] = None) -> Dict:
    """Extract motion regressors for all subjects in a session.
    
    Parameters
    ----------
    config : MIDTConfig
        Configuration object
    session : str
        Session identifier
    session_subjects : list
        List of subject IDs for this session
    log_file : str, optional
        Log file path
        
    Returns
    -------
    dict
        Motion extraction summary
    """
    
    try:
        # Create session-specific config
        session_config = config
        session_config.subject_ids = session_subjects
        session_config.sessions_to_process = [session]
        
        # Run motion regressor extraction
        motion_summary = extract_motion_regressors(session_config)
        
        print(f"✅ Motion regressor extraction completed: "
              f"{motion_summary['successful_subjects']}/{motion_summary['total_subjects']} subjects successful")
        
        # Log results
        if log_file:
            for subject_id in session_subjects:
                if subject_id in [s.split('_')[0] for s in motion_summary['failed_subjects']]:
                    log_processing_step('motion_extraction', subject_id, 'failed', log_file)
                else:
                    log_processing_step('motion_extraction', subject_id, 'success', log_file)
        
        return {'success': motion_summary['successful_subjects'] > 0, 'summary': motion_summary}
        
    except Exception as e:
        print(f"❌ Error in motion regressor extraction: {e}")
        return {'success': False, 'error': str(e)}


def run_pipeline_from_config_file(config_file: str, n_jobs: int = 1) -> Dict:
    """Run pipeline from configuration file.
    
    Parameters
    ----------
    config_file : str
        Path to configuration file (YAML or JSON)
    n_jobs : int
        Number of parallel jobs
        
    Returns
    -------
    dict
        Pipeline execution summary
    """
    
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    # Load configuration based on file extension
    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
        config = MIDTConfig.from_yaml(config_file)
    elif config_path.suffix.lower() == '.json':
        config = MIDTConfig.from_json(config_file)
    else:
        raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
    
    # Setup log file
    log_file = str(Path(config.base_dir) / 'processing.log')
    
    # Run pipeline
    return run_complete_pipeline(config, n_jobs=n_jobs, log_file=log_file)