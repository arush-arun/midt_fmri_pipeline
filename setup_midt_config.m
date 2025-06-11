%% =========================================================================
%% 1. SETUP_MIDT_CONFIG.m - Configuration file
%% =========================================================================

function config = setup_midt_config()
% SETUP_MIDT_CONFIG Configure paths and parameters for MIDT analysis

    %% SUBJECT INFORMATION
    % IMPORTANT: Update this list with your actual subject IDs
    config.subject_ids = {
        'sub-001'
        'sub-002'
        % Add your complete subject list here...
        % Example: 'sub-003', 'sub-004', etc.
    };
    
    %% ===== SESSION CONFIGURATION =====
    % Choose which sessions to process:
    config.sessions_to_process = {'1'};  % CHANGE THIS AS NEEDED
    % Options: {'1'}, {'2'}, {'1', '2'}, {'all'}
    
    % Session-specific exclusions (optional - customize for your dataset)
    config.excluded_subjects = {
        % Format: {'subject_id', 'exclusion_reason', 'affected_sessions'}
        % Example: 'sub-021', 'Motion artifacts', 'all'
        % Example: 'sub-032', 'Timing file issues', 'ses-1'
    };
    
    %% DIRECTORY STRUCTURE - UPDATE THESE PATHS FOR YOUR SYSTEM
    config.base_dir = '/path/to/your/analysis/directory';
    config.behavioral_dir = '/path/to/behavioral/timing/files';
    config.fmriprep_dir = '/path/to/fmriprep/derivatives';
    
    % Output directories
    config.timing_dir = fullfile(config.base_dir, 'timing_files');
    config.rt_dir = fullfile(config.base_dir, 'reaction_times');
    config.motion_regressor_dir = fullfile(config.base_dir, 'motion_regressors');
    config.first_level_dir = fullfile(config.base_dir, 'first_level_results');
    config.qc_dir = fullfile(config.base_dir, 'quality_control');
    
    %% ACQUISITION PARAMETERS
    config.tr = 1.6;
    config.n_volumes = 367;
    config.dummy_scans = 5;
    config.smooth_fwhm = 6;
    config.hpf = 128;
    
    %% PROCESSING OPTIONS
    config.options.run_timing_extraction = true;
    config.options.run_rt_extraction = true;
    config.options.run_motion_extraction = true;
    config.options.run_first_level = true;
    
    %% APPLY SESSION EXCLUSIONS
    config = apply_session_exclusions(config);
    
    fprintf('Configuration loaded for %d subjects\n', length(config.subject_ids));
    fprintf('Sessions to process: %s\n', strjoin(config.sessions_to_process, ', '));
end

function config = apply_session_exclusions(config)
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
