# Changelog - MIDT fMRI Analysis Pipeline (MATLAB Implementation)

All notable changes to the MATLAB implementation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-01-06 - Repository Preparation Release

### Added
- **Documentation suite** for GitHub publication
  - `README.md`: Comprehensive setup and usage instructions
  - `REQUIREMENTS.md`: Detailed dependency and data requirements
  - `LICENSE`: MIT license for open source distribution
  - `example_config.m`: Template configuration file
- **Git integration**
  - `.gitignore`: MATLAB-specific ignore patterns
  - Repository structure preparation
- **Path management improvements**
  - Removed hardcoded paths from `setup_midt_config.m`
  - Added dynamic path detection and validation
  - Environment-specific configuration support

### Changed
- **Enhanced configuration management**
  - `setup_midt_config.m`: Now uses relative paths and user input
  - Improved error messages for missing directories
  - Better BIDS structure validation
- **Code organization**
  - Standardized function headers and documentation
  - Consistent variable naming conventions
  - Improved code comments and explanations

### Fixed
- **Path compatibility** issues across different operating systems
- **Directory creation** handling for output folders
- **Error handling** for missing dependencies and data files

### Documentation
- **Installation guide** with step-by-step SPM12 setup
- **Usage examples** for single subject and batch processing
- **Troubleshooting section** for common issues
- **File format specifications** for behavioral and fMRI data

## [1.1.0] - 2024-12-01 - Stability and Robustness Release

### Added
- **Enhanced file detection** in `extract_midt_onsets.m`
  - Support for multiple fMRIPrep naming conventions
  - Automatic detection of smoothed vs unsmoothed data
  - Fallback mechanisms for missing files
- **Improved motion extraction** in `extract_motion_regressors.m`
  - Better handling of confounds file variations
  - Validation of motion parameter availability
  - Quality control metrics calculation
- **Session management** capabilities
  - Multi-session processing support
  - Session-specific output organization
  - Flexible session naming conventions

### Changed
- **Enhanced error handling** across all modules
  - More informative error messages
  - Graceful handling of missing data
  - Progress reporting during processing
- **Batch processing improvements** in `run_complete_pipeline.m`
  - Better subject iteration and error recovery
  - Summary reporting of processing results
  - Skip mechanism for already processed subjects

### Fixed
- **SPM batch processing** reliability issues
  - Improved job specification handling
  - Better memory management for large datasets
  - Fixed contrast computation edge cases
- **Timing synchronization** problems
  - Consistent dummy scan removal across modules
  - Proper timepoint alignment between fMRI and confounds
  - Accurate onset time calculation

### Performance
- **Memory optimization** for large datasets
- **Processing speed** improvements through better SPM job management
- **Reduced disk I/O** through optimized file operations

## [1.0.0] - 2024-11-01 - Initial Release

### Added - Core Pipeline Implementation
- **Primary analysis modules**:
  - `extract_midt_onsets.m`: Extract timing information from behavioral files
  - `extract_motion_regressors.m`: Process motion parameters from fMRIPrep
  - `run_first_level_analysis.m`: First-level GLM analysis using SPM12
  - `run_complete_pipeline.m`: Complete pipeline orchestration
  - `setup_midt_config.m`: Configuration and path management

### Features - MIDT Task Analysis
- **Behavioral timing extraction**:
  - Support for tab-delimited timing files
  - Conversion to SPM-compatible onset format
  - Handling of practice vs main task trials
  - BIDS-compatible output naming

- **Motion parameter processing**:
  - Extraction of 6DOF motion parameters from fMRIPrep confounds
  - Dummy scan removal (first 5 volumes)
  - Quality control metrics calculation
  - SPM-compatible regressor file format

- **First-level statistical analysis**:
  - SPM12 GLM implementation
  - Standard MIDT contrasts (8 contrasts total):
    1. Anticipation: Reward vs Neutral
    2. Anticipation: Neutral vs Reward  
    3. Feedback: Reward vs Neutral (Correct)
    4. Feedback: Neutral vs Reward (Correct)
    5. Feedback: Reward Success vs Failure
    6. Feedback: Reward Failure vs Success
    7. Feedback: Neutral Success vs Failure
    8. Feedback: Neutral Failure vs Success
  - High-pass filtering (128s cutoff)
  - Motion regressor inclusion
  - Statistical and effect size maps output

- **Complete pipeline orchestration**:
  - Batch processing for multiple subjects
  - Configurable processing stages
  - Error handling and logging
  - BIDS-compliant output structure

### Technical Specifications
- **Software requirements**:
  - MATLAB R2018b or later
  - SPM12 statistical parametric mapping toolbox
  - Image Processing Toolbox (recommended)

- **Data requirements**:
  - fMRIPrep preprocessed BOLD data
  - Behavioral timing files (tab-delimited)
  - BIDS-formatted directory structure

- **Processing parameters**:
  - TR: Configurable (default 1.6s)
  - Dummy scans: 5 volumes removed
  - High-pass filter: 128s period
  - Motion parameters: 6DOF from fMRIPrep
  - Smoothing: Uses fMRIPrep smoothed data (typically 6mm FWHM)

### MIDT Task Conditions
- **Anticipation phase**:
  - `anticip-reward`: Reward cue anticipation
  - `anticip-neutral`: Neutral cue anticipation

- **Feedback phase**:
  - `fb-reward`: Successful reward trial feedback
  - `fb-miss-reward`: Failed reward trial feedback
  - `fb-corr-neutral`: Correct neutral trial feedback
  - `fb-incorr-neutral`: Incorrect neutral trial feedback

### Output Structure
```
output_dir/
├── timing_files/
│   └── ses-1/
│       └── sub-XXX_ses-1_task-MIDT_events.tsv
├── motion_regressors/
│   └── ses-1/
│       └── sub-XXX/
│           └── sub-XXX_ses-1_task-MIDT_Regressors.txt
└── first_level_results/
    └── ses-1/
        └── sub-XXX/
            ├── SPM.mat
            ├── beta_*.nii
            ├── con_*.nii
            └── spmT_*.nii
```

### Known Limitations
- **Single session processing** per pipeline run
- **Manual path configuration** required
- **Limited error recovery** for corrupted data
- **Basic quality control** metrics only
- **SPM12 dependency** for statistical analysis
- **Windows/Linux path** handling differences

---

## Development Notes

### Design Principles
1. **BIDS compliance**: Follow Brain Imaging Data Structure standards
2. **SPM12 integration**: Leverage established statistical methods
3. **Modular design**: Separate concerns for timing, motion, and analysis
4. **Batch processing**: Support multi-subject analysis workflows
5. **Error resilience**: Continue processing despite individual subject failures

### Code Organization
- **Function-based architecture**: Each module as standalone function
- **Configuration centralization**: Single config file for all parameters
- **Consistent naming**: BIDS-compatible file and variable naming
- **Error handling**: Try-catch blocks with informative messages
- **Documentation**: Inline comments and function headers

### Future Considerations
- **Multi-session support**: Process multiple sessions simultaneously
- **Advanced QC**: Motion outlier detection and reporting
- **Group analysis**: Second-level statistical modeling
- **GUI interface**: User-friendly configuration and monitoring
- **Performance optimization**: Parallel processing for batch jobs

---

**Note**: This MATLAB implementation serves as the foundation for the neuroimaging analysis pipeline and maintains compatibility with established SPM12 workflows. For new projects, consider the Python implementation which offers improved performance and modern neuroimaging practices.