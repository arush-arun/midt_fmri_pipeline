# MIDT fMRI Analysis Pipeline

A comprehensive analysis pipeline for Monetary Incentive Delay Task (MIDT) fMRI data, available in both **Python** (recommended) and **MATLAB** implementations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MATLAB R2018b+](https://img.shields.io/badge/MATLAB-R2018b+-orange.svg)](https://www.mathworks.com/products/matlab.html)

## 🚀 Quick Start

### Python Version (Recommended)
```bash
cd python/
pip install -r requirements.txt
# Edit run_midt.py with your paths
python run_midt.py
```

### MATLAB Version (Legacy)
```matlab
cd matlab/
% Edit setup_midt_config.m with your paths
run_complete_pipeline()
```

## 📖 Overview

This pipeline processes MIDT fMRI data through three main stages:
1. **Event Extraction** - Converts behavioral timing files to BIDS events
2. **Motion Regressor Extraction** - Processes fMRIPrep confounds with QC
3. **First-Level Analysis** - GLM analysis with standard MIDT contrasts

### MIDT Task Conditions
- **Anticipation**: Reward vs. Neutral cue processing
- **Feedback**: Success vs. Failure outcome processing
- **6 Conditions**: `anticip-reward`, `anticip-neutral`, `fb-reward`, `fb-miss-reward`, `fb-corr-neutral`, `fb-incorr-neutral`

## 📁 Repository Structure

```
midt_fmri_pipeline/
├── README.md                 # This file
├── CHANGELOG.md              # Version history
├── LICENSE                   # MIT license
├── .gitignore               # Git ignore rules
│
├── python/                  # Python Implementation (Recommended)
│   ├── midt_pipeline/       # Core pipeline package
│   ├── run_midt.py          # Main execution script
│   ├── requirements.txt     # Python dependencies
│   └── README_python.md     # Python-specific docs
│
├── matlab/                  # MATLAB Implementation (Legacy)
│   ├── *.m                  # MATLAB functions
│   └── README_matlab.md     # MATLAB-specific docs
│
├── examples/               # Example configurations
│   ├── config_template.yaml
│   └── sample_data/
│
└── docs/                   # Additional documentation
    ├── installation.md
    ├── troubleshooting.md
    └── comparison.md
```

## 🔧 Requirements

### Python Version
- **Python**: 3.8 or later
- **Key packages**: nilearn ≥0.10.0, pandas ≥1.5.0, nibabel ≥4.0.0
- **Data**: BIDS-formatted dataset with fMRIPrep preprocessing

### MATLAB Version  
- **MATLAB**: R2018b or later
- **SPM12**: Statistical Parametric Mapping toolbox
- **Data**: BIDS-formatted dataset with fMRIPrep preprocessing

### Common Requirements
- **Preprocessed fMRI data**: fMRIPrep v20.0.0+ recommended
- **Behavioral data**: Tab-delimited timing files (.txt format)
- **Storage**: ~500MB per subject for results

## 📊 Expected Outputs

Both implementations generate:

### Timing Files
- `sub-XXX_ses-X_task-MIDT_events.tsv` - BIDS events format

### Motion Regressors
- `sub-XXX_ses-X_task-MIDT_Regressors.txt` - 6DOF motion parameters
- `motion_qc_report.csv` - Quality control metrics

### First-Level Results  
- **Effect size maps**: `*_stat-effect.nii.gz`
- **Statistical maps**: `*_stat-t.nii.gz`
- **Design matrix**: `*_design-matrix.tsv`

### Standard Contrasts (8 total)
1. Individual conditions: `anticip-reward`, `anticip-neutral`, `fb-reward`, `fb-corr-neutral`
2. Difference contrasts: `anticip-reward-vs-neutral`, `feedback-reward-vs-neutral-correct`, `feedback-reward-success-vs-failure`, `feedback-neutral-success-vs-failure`

## 🚦 Getting Started

### 1. Choose Your Implementation
- **New projects**: Start with Python version
- **Existing workflows**: Continue with MATLAB or migrate gradually

### 2. Install Dependencies
```bash
# Python
cd python/
pip install -r requirements.txt

# MATLAB
% Ensure SPM12 is in MATLAB path
addpath('/path/to/spm12')
```

### 3. Prepare Your Data
- **fMRIPrep preprocessed data** in BIDS format
- **Behavioral timing files** in tab-delimited format
- **Subject list** with BIDS naming (`sub-XXX`)

### 4. Configure Analysis
```python
# Python: Edit run_midt.py
config = MIDTConfig(
    base_dir="/path/to/output",
    behavioral_dir="/path/to/behavioral/data",
    fmriprep_dir="/path/to/fmriprep",
    subject_ids=["sub-001", "sub-002"],
    sessions_to_process=["1"]
)
```

```matlab
% MATLAB: Edit setup_midt_config.m
config.base_dir = '/path/to/output';
config.behavioral_dir = '/path/to/behavioral/data';
config.fmriprep_dir = '/path/to/fmriprep';
config.subject_ids = {'sub-001', 'sub-002'};
```

### 5. Run Analysis
```bash
# Python
python run_midt.py

# MATLAB  
run_complete_pipeline()
```

## 📜 Citation

If you use this pipeline in your research, please cite:

TBC

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: Both implementations follow BIDS (Brain Imaging Data Structure) conventions and are designed for reproducible neuroimaging research.
