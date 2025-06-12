# Requirements

## Software Dependencies

### MATLAB
- **Minimum Version**: R2018b
- **Recommended Version**: R2020a or later
- **Required Toolboxes**:
  - Statistics and Machine Learning Toolbox
  - Image Processing Toolbox (recommended)

### SPM12
- **Version**: SPM12 (r7771 or later)
- **Installation**: Download from [SPM website](https://www.fil.ion.ucl.ac.uk/spm/software/spm12/)
- **Setup**: Add SPM12 directory to MATLAB path

### System Requirements
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: ~500MB per subject for results
- **OS**: Windows, macOS, or Linux

## Data Prerequisites

### Preprocessed fMRI Data
- **Format**: BIDS-compliant dataset
- **Preprocessing**: fMRIPrep v20.0.0+ recommended
- **Space**: MNI152NLin2009cAsym template space
- **Resolution**: 2mm isotropic
- **Required files**:
  - Preprocessed BOLD: `*_desc-preproc_bold.nii.gz`
  - Confounds: `*_desc-confounds_timeseries.tsv`

### Behavioral Data
- **Format**: Tab-delimited text files (.txt)
- **Content**: Trial-by-trial timing and accuracy data
- **Required columns**:
  - Accuracy (0/1)
  - Cue onset time (milliseconds)
  - Cue offset time (milliseconds)  
  - Feedback onset time (milliseconds)
  - Cue type (image filename)

## Installation Verification

Test your installation with these commands:

```matlab
% Check MATLAB version
version

% Verify SPM12 installation
which spm
spm('defaults', 'FMRI')

% Test required functions
which importdata
which tdfread
which dlmwrite
```

Expected output should show no errors and confirm SPM12 is accessible.

