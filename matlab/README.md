# MIDT fMRI Analysis Pipeline

A comprehensive MATLAB pipeline for analyzing Monetary Incentive Delay Task (MIDT) fMRI data using SPM12. This pipeline processes behavioral timing data, extracts motion regressors from fMRIprep outputs, and performs first-level statistical analysis following BIDS conventions.

## Overview

The pipeline consists of five main components:
1. **Configuration Setup** - Centralized parameter management
2. **Onset Extraction** - Behavioral timing file processing  
3. **Motion Regressor Extraction** - fMRIPrep confound processing
4. **First-Level Analysis** - SPM12 GLM analysis with 12 standard contrasts
5. **Complete Pipeline Orchestration** - Automated execution with quality control

## Prerequisites

### Software Requirements
- **MATLAB** R2018b or later
- **SPM12** (Statistical Parametric Mapping)
- **fMRIPrep** preprocessed data (recommended)

### Data Requirements
- BIDS-formatted dataset
- Behavioral timing files (`.txt` format)
- fMRIPrep preprocessed functional images
- fMRIPrep confound files (.tsv)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd midt-fmri-pipeline
```

2. Add SPM12 to your MATLAB path:
```matlab
addpath('/path/to/spm12')
```

3. Verify SPM installation:
```matlab
spm('defaults', 'FMRI')
```

## Configuration

1. Copy and customize the configuration file:
```matlab
config = setup_midt_config();
```

2. Update the following paths in `setup_midt_config.m`:
```matlab
config.base_dir = '/path/to/your/analysis/directory';
config.behavioral_dir = '/path/to/behavioral/data';
config.fmriprep_dir = '/path/to/fmriprep/output';
```

3. Set your subject list:
```matlab
config.subject_ids = {
    'sub-001'
    'sub-002'
    % Add your subjects here
};
```

## Usage

### Quick Start - Complete Pipeline
Run the entire pipeline for all configured subjects:
```matlab
run_complete_pipeline()
```

### Individual Components

#### 1. Extract Timing Information
```matlab
config = setup_midt_config();
extract_midt_onsets(config.behavioral_dir, config.timing_dir, 'session', '1');
```

#### 2. Extract Motion Regressors
```matlab
config = setup_midt_config();
extract_motion_regressors(config);
```

#### 3. Run First-Level Analysis
```matlab
config = setup_midt_config();
run_first_level_analysis(config);
```

## Directory Structure

The pipeline expects and creates the following directory structure:

```
analysis_directory/
├── behavioral_data/           # Input behavioral timing files
├── timing_files/             # Extracted onset/duration files
│   └── ses-1/
├── motion_regressors/        # Motion parameter files
│   └── ses-1/
├── first_level_results/      # SPM analysis results
│   └── ses-1/
└── quality_control/          # QC reports and metrics
    └── ses-1/
```

## Data Format Requirements

### Behavioral Timing Files
- Format: Tab-delimited text files (`.txt`)
- Must contain columns for accuracy, cue onset/offset, feedback onset
- Expected filename patterns: `*task*.txt`, `Reward_task*.txt`, or `*.txt`

### fMRIPrep Data
- BIDS-compliant preprocessed functional images
- Confound files: `*_desc-confounds_timeseries.tsv`
- Expected naming: `sub-XXX_ses-X_task-MIDT_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold_6mm_blur.nii`

## MIDT Task Conditions

The pipeline extracts 6 experimental conditions:
1. **anticip-reward** - Reward anticipation trials
2. **anticip-neutral** - Neutral anticipation trials
3. **fb-reward** - Successful reward feedback
4. **fb-miss-reward** - Failed reward feedback
5. **fb-corr-neutral** - Correct neutral feedback
6. **fb-incorr-neutral** - Incorrect neutral feedback

## Statistical Contrasts

The first-level analysis includes 12 standard contrasts:
- Anticipation: Reward > Neutral / Neutral > Reward
- Feedback: Reward > Neutral / Neutral > Reward
- Success vs. Failure comparisons
- Individual condition effects

## Configuration Options

### Processing Control
```matlab
config.options.run_timing_extraction = true;
config.options.run_motion_extraction = true; 
config.options.run_first_level = true;
```

### Acquisition Parameters
```matlab
config.tr = 1.6;              # Repetition time (seconds)
config.n_volumes = 367;       # Total volumes per run
config.dummy_scans = 5;       # Volumes to exclude
config.smooth_fwhm = 6;       # Smoothing kernel (mm)
config.hpf = 128;            # High-pass filter (seconds)
```

### Subject Exclusions
```matlab
config.excluded_subjects = {
    'sub-XXX', 'reason', 'ses-X'  # Subject, reason, affected sessions
};
```

## Quality Control

The pipeline generates several QC outputs:
- Motion parameter reports (`motion_qc_report.csv`)
- Processing logs with success rates
- Individual subject statistics
- File validation summaries


## Output Files

### Timing Files
- `sub-XXX_ses-X_task-MIDT.mat` - SPM-compatible onset/duration files

### Motion Regressors  
- `sub-XXX_ses-X_task-MIDT_Regressors.txt` - 6DOF motion parameters

### First-Level Results
- `SPM.mat` - SPM design matrix
- `con_*.nii` - Contrast images  
- `spmT_*.nii` - Statistical maps
- `beta_*.nii` - Parameter estimates

## Citation

If you use this pipeline in your research, please cite:
```
TBC
```
- Contact: uqahonne@uq.edu.au

## License

[Specify license - see LICENSE file]

---

**Note**: This pipeline is designed for MIDT fMRI data analysis and may require modifications for other experimental paradigms.
