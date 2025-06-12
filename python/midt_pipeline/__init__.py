"""
MIDT fMRI Analysis Pipeline - Python Edition

A comprehensive Python pipeline for analyzing Monetary Incentive Delay Task (MIDT) 
fMRI data using nilearn. This pipeline processes behavioral timing data, extracts 
motion regressors, and performs first-level statistical analysis following BIDS conventions.

Converted from the original MATLAB/SPM12 pipeline to provide:
- Better integration with modern neuroimaging tools
- Enhanced quality control and reporting
- Parallel processing capabilities
- Free, open-source alternative to MATLAB/SPM
"""

__version__ = "2.0.0"
__author__ = "MIDT Pipeline Team"
__email__ = "uqahonne@uq.edu.au"

from .config import MIDTConfig
from .events import extract_midt_events
from .motion import extract_motion_regressors
from .first_level import run_first_level_midt
from .pipeline import run_complete_pipeline

__all__ = [
    "MIDTConfig",
    "extract_midt_events",
    "extract_motion_regressors", 
    "run_first_level_midt",
    "run_complete_pipeline"
]