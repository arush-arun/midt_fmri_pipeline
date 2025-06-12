"""
Configuration management for MIDT pipeline.

This module defines the configuration structure and handles loading/validation
of pipeline parameters. Converted from setup_midt_config.m.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import yaml
import json


@dataclass
class MIDTConfig:
    """Configuration class for MIDT fMRI analysis pipeline.
    
    This class replaces the MATLAB setup_midt_config.m function and provides
    a structured way to manage pipeline parameters.
    """
    
    # Required paths
    base_dir: str
    behavioral_dir: str
    fmriprep_dir: str
    
    # Subject information
    subject_ids: List[str]
    sessions_to_process: List[str] = field(default_factory=lambda: ['1'])
    excluded_subjects: List[List[str]] = field(default_factory=list)
    
    # Acquisition parameters
    tr: float = 1.6
    n_volumes: int = 367
    dummy_scans: int = 5
    smooth_fwhm: int = 6
    hpf: float = 128.0  # High-pass filter in seconds
    
    # Processing options
    run_timing_extraction: bool = True
    run_motion_extraction: bool = True
    run_first_level: bool = True
    
    # Motion parameters to extract
    motion_params: List[str] = field(default_factory=lambda: [
        'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
    ])
    
    # Task parameters
    task: str = 'MIDT'
    
    # Output directories (computed automatically)
    timing_dir: Optional[str] = None
    motion_regressor_dir: Optional[str] = None
    first_level_dir: Optional[str] = None
    qc_dir: Optional[str] = None
    
    def __post_init__(self):
        """Initialize computed paths after object creation."""
        if self.timing_dir is None:
            self.timing_dir = str(Path(self.base_dir) / 'timing_files')
        if self.motion_regressor_dir is None:
            self.motion_regressor_dir = str(Path(self.base_dir) / 'motion_regressors')
        if self.first_level_dir is None:
            self.first_level_dir = str(Path(self.base_dir) / 'first_level_results')
        if self.qc_dir is None:
            self.qc_dir = str(Path(self.base_dir) / 'quality_control')
            
        # Convert string paths to Path objects for validation
        self._validate_paths()
        
    def _validate_paths(self):
        """Validate that required paths exist and are accessible."""
        # Check if paths contain placeholder values
        placeholder_indicators = ['/path/to/', 'CHANGE_THIS', 'UPDATE_ME']
        
        for indicator in placeholder_indicators:
            if (indicator in self.base_dir or 
                indicator in self.behavioral_dir or 
                indicator in self.fmriprep_dir):
                raise ValueError(
                    f"Configuration contains placeholder paths. "
                    f"Please update paths in your configuration file."
                )
        
        # Check if input directories exist
        behavioral_path = Path(self.behavioral_dir)
        if not behavioral_path.exists():
            raise FileNotFoundError(f"Behavioral directory not found: {self.behavioral_dir}")
            
        fmriprep_path = Path(self.fmriprep_dir)
        if not fmriprep_path.exists():
            raise FileNotFoundError(f"fMRIPrep directory not found: {self.fmriprep_dir}")
            
    def create_output_directories(self):
        """Create output directories if they don't exist."""
        output_dirs = [
            self.timing_dir,
            self.motion_regressor_dir, 
            self.first_level_dir,
            self.qc_dir
        ]
        
        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            
        # Create session-specific subdirectories
        for session in self.sessions_to_process:
            for dir_path in output_dirs:
                session_dir = Path(dir_path) / f'ses-{session}'
                session_dir.mkdir(parents=True, exist_ok=True)
                
    def get_valid_subjects_for_session(self, session: str) -> List[str]:
        """Get list of valid subjects for a specific session after applying exclusions."""
        valid_subjects = self.subject_ids.copy()
        
        for exclusion in self.excluded_subjects:
            if len(exclusion) >= 3:
                subject_id, reason, affected_sessions = exclusion[0], exclusion[1], exclusion[2]
                
                # Check if this session is affected
                session_affected = False
                if affected_sessions == 'all':
                    session_affected = True
                elif affected_sessions == f'ses-{session}':
                    session_affected = True
                elif isinstance(affected_sessions, list) and f'ses-{session}' in affected_sessions:
                    session_affected = True
                    
                if session_affected and subject_id in valid_subjects:
                    valid_subjects.remove(subject_id)
                    print(f"Excluding {subject_id} from session {session}: {reason}")
                    
        return valid_subjects
    
    @classmethod
    def from_yaml(cls, yaml_file: str) -> 'MIDTConfig':
        """Load configuration from YAML file."""
        with open(yaml_file, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)
        
    @classmethod
    def from_json(cls, json_file: str) -> 'MIDTConfig':
        """Load configuration from JSON file."""
        with open(json_file, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
        
    def to_yaml(self, yaml_file: str):
        """Save configuration to YAML file."""
        config_dict = self.__dict__.copy()
        with open(yaml_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
    def to_json(self, json_file: str):
        """Save configuration to JSON file."""
        config_dict = self.__dict__.copy()
        with open(json_file, 'w') as f:
            json.dump(config_dict, f, indent=2)


def create_example_config() -> MIDTConfig:
    """Create an example configuration with placeholder values.
    
    Users should customize this for their specific setup.
    """
    return MIDTConfig(
        base_dir='/path/to/your/analysis/directory',
        behavioral_dir='/path/to/behavioral/timing/files',
        fmriprep_dir='/path/to/fmriprep/derivatives',
        subject_ids=[
            'sub-001',
            'sub-002',
            'sub-003'
            # Add your subjects here
        ],
        sessions_to_process=['1'],
        excluded_subjects=[
            # Format: [subject_id, reason, affected_sessions]
            # Example: ['sub-021', 'Motion artifacts', 'all']
            # Example: ['sub-032', 'Timing file issues', 'ses-1']
        ]
    )