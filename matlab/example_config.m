function config = example_config()
% EXAMPLE_CONFIG Template configuration file for MIDT analysis
% 
% Copy this file and customize paths and parameters for your dataset
% Save as 'setup_midt_config.m' in your analysis directory

    %% SUBJECT INFORMATION
    % List all subjects to be analyzed
    config.subject_ids = {
        'sub-001'
        'sub-002'
        'sub-003'
        % Add your complete subject list here...
        % Format: 'sub-XXX' (BIDS compliant)
    };
    
    %% SESSION CONFIGURATION
    % Specify which sessions to process
    config.sessions_to_process = {'1'};  
    % Options: {'1'}, {'2'}, {'1', '2'}, or specific session numbers
    
    % Session-specific exclusions (optional)
    % Format: {subject_id, reason, affected_sessions}
    config.excluded_subjects = {
        % Example exclusions:
        % 'sub-021', 'AUDIT score exclusion', 'all'
        % 'sub-032', 'Motion artifacts', 'ses-1'
        % 'sub-052', 'Timing file issues', 'ses-2'
    };
    
    %% DIRECTORY PATHS - CUSTOMIZE THESE FOR YOUR SYSTEM
    % Base directory for analysis outputs
    config.base_dir = '/path/to/your/analysis/directory';
    
    % Input data directories
    config.behavioral_dir = '/path/to/behavioral/timing/files';
    config.fmriprep_dir = '/path/to/fmriprep/derivatives';
    
    % Output directories (will be created automatically)
    config.timing_dir = fullfile(config.base_dir, 'timing_files');
    config.rt_dir = fullfile(config.base_dir, 'reaction_times');
    config.motion_regressor_dir = fullfile(config.base_dir, 'motion_regressors');
    config.first_level_dir = fullfile(config.base_dir, 'first_level_results');
    config.qc_dir = fullfile(config.base_dir, 'quality_control');
    
    %% ACQUISITION PARAMETERS
    % MRI acquisition settings - update based on your protocol
    config.tr = 1.6;            % Repetition time (seconds)
    config.n_volumes = 367;     % Number of volumes per run (after dummy removal)
    config.dummy_scans = 5;     % Number of dummy scans to remove
    config.smooth_fwhm = 6;     % Smoothing kernel FWHM (mm)
    config.hpf = 128;          % High-pass filter cutoff (seconds)
    
    %% PROCESSING OPTIONS
    % Enable/disable pipeline components
    config.options.run_timing_extraction = true;
    config.options.run_rt_extraction = true;      % Currently disabled in pipeline
    config.options.run_motion_extraction = true;
    config.options.run_first_level = true;
    
    %% MOTION PARAMETERS
    % Motion regressors to extract from fMRIPrep confounds
    config.motion_params = {
        'trans_x', 'trans_y', 'trans_z',    % Translation parameters
        'rot_x', 'rot_y', 'rot_z'           % Rotation parameters
    };
    
    %% TASK PARAMETERS
    config.task = 'MIDT';       % Task name (used in BIDS filenames)
    
    %% APPLY SESSION EXCLUSIONS (do not modify)
    config = apply_session_exclusions(config);
    
    % Display configuration summary
    fprintf('Configuration loaded:\n');
    fprintf('  Subjects: %d\n', length(config.subject_ids));
    fprintf('  Sessions: %s\n', strjoin(config.sessions_to_process, ', '));
    fprintf('  Base directory: %s\n', config.base_dir);
end

function config = apply_session_exclusions(config)
    % Apply subject exclusions per session (do not modify this function)
    if isempty(config.excluded_subjects)
        return;
    end
    
    config.session_subject_lists = struct();
    
    for session_idx = 1:length(config.sessions_to_process)
        session = config.sessions_to_process{session_idx};
        session_key = ['ses' session];
        valid_subjects = config.subject_ids;
        
        for excl_idx = 1:size(config.excluded_subjects, 1)
            excl_subject = config.excluded_subjects{excl_idx, 1};
            excl_reason = config.excluded_subjects{excl_idx, 2};
            excl_sessions = config.excluded_subjects{excl_idx, 3};
            
            session_affected = false;
            if strcmp(excl_sessions, 'all')
                session_affected = true;
            elseif strcmp(excl_sessions, ['ses-' session])
                session_affected = true;
            elseif iscell(excl_sessions) && any(strcmp(excl_sessions, ['ses-' session]))
                session_affected = true;
            end
            
            if session_affected
                valid_subjects = valid_subjects(~strcmp(valid_subjects, excl_subject));
                fprintf('Excluding %s from session %s: %s\n', excl_subject, session, excl_reason);
            end
        end
        
        config.session_subject_lists.(session_key) = valid_subjects;
        fprintf('Session %s: %d valid subjects\n', session, length(valid_subjects));
    end
end