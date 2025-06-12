function run_complete_pipeline()
% RUN_COMPLETE_PIPELINE Execute the entire MIDT analysis pipeline

    addpath(genpath(pwd));
    
    % Check SPM availability
    if ~exist('spm', 'file')
        error('SPM12 not found in MATLAB path. Please install SPM12 and add to path.');
    end
    
    spm('defaults', 'FMRI');
    
    fprintf('=== MIDT ANALYSIS PIPELINE ===\n');
    config = setup_midt_config();
    
    create_output_directories(config);
    
    overall_summary = struct();
    overall_summary.sessions_processed = {};
    overall_summary.total_subjects = 0;
    overall_summary.successful_subjects = 0;
    
    for session_idx = 1:length(config.sessions_to_process)
        session = config.sessions_to_process{session_idx};
        session_key = ['ses' session];
        
        fprintf('\n? ======= PROCESSING SESSION %s ======= ?\n', session);
        
        if isfield(config.session_subject_lists, session_key)
            session_subjects = config.session_subject_lists.(session_key);
        else
            session_subjects = config.subject_ids;
        end
        
        fprintf('Session %s: Processing %d subjects\n', session, length(session_subjects));
        
        session_dirs = create_session_directories(config, session);
        session_summary = process_single_session(config, session, session_subjects, session_dirs);
        
        overall_summary.sessions_processed{end+1} = session;
        overall_summary.total_subjects = overall_summary.total_subjects + session_summary.total_subjects;
        overall_summary.successful_subjects = overall_summary.successful_subjects + session_summary.successful_subjects;
        
        fprintf('\n? Session %s completed: %d/%d subjects successful\n', ...
            session, session_summary.successful_subjects, session_summary.total_subjects);
    end
    
    fprintf('\n? ======= COMPLETE PIPELINE FINISHED ======= ?\n');
    fprintf('Sessions processed: %s\n', strjoin(overall_summary.sessions_processed, ', '));
    fprintf('Total subjects processed: %d\n', overall_summary.total_subjects);
    fprintf('Overall success rate: %.1f%%\n', ...
        (overall_summary.successful_subjects / overall_summary.total_subjects) * 100);
    fprintf('Results saved in: %s\n', config.base_dir);
end

function session_summary = process_single_session(config, session, session_subjects, session_dirs)
    session_summary = struct();
    session_summary.session = session;
    session_summary.total_subjects = length(session_subjects);
    session_summary.successful_subjects = 0;
    
    %% STEP 1: Extract Timing Information
    fprintf('\n--- STEP 1: EXTRACTING TIMING INFORMATION (Session %s) ---\n', session);
    if config.options.run_timing_extraction
        try
            extract_midt_onsets(config.behavioral_dir, session_dirs.timing, 'session', session);
            fprintf('? Timing extraction completed for session %s\n', session);
        catch ME
            fprintf('? Error in timing extraction for session %s: %s\n', session, ME.message);
            return;
        end
    end
    
    %% STEP 2: Extract Reaction Times
%     fprintf('\n--- STEP 2: EXTRACTING REACTION TIMES (Session %s) ---\n', session);
%     if config.options.run_rt_extraction
%         try
%             extract_reaction_times(config.behavioral_dir, session_dirs.rt, session_subjects, ...
%                 'auto_detect', false, 'session', session);
%             fprintf('? Reaction time extraction completed for session %s\n', session);
%         catch ME
%             fprintf('? Error in reaction time extraction for session %s: %s\n', session, ME.message);
%             return;
%         end
%     end
    
    %% STEP 3: Extract Motion Regressors
    fprintf('\n--- STEP 2: EXTRACTING MOTION REGRESSORS (Session %s) ---\n', session);
    if config.options.run_motion_extraction
        try
            motion_config = config;
            motion_config.subject_ids = session_subjects;
            motion_config.sessions = {session};
            motion_config.output_dir = session_dirs.motion;
            extract_motion_regressors(motion_config);
            fprintf('? Motion regressor extraction completed for session %s\n', session);
        catch ME
            fprintf('? Error in motion regressor extraction for session %s: %s\n', session, ME.message);
            return;
        end
    end
    
    %% STEP 4: Run First-Level Analysis
    fprintf('\n--- STEP 3: RUNNING FIRST-LEVEL ANALYSIS (Session %s) ---\n', session);
    if config.options.run_first_level
        try
            analysis_config = prepare_session_analysis_config(config, session, session_subjects, session_dirs);
            run_first_level_analysis(analysis_config);
            fprintf('? First-level analysis completed for session %s\n', session);
            session_summary.successful_subjects = length(session_subjects);
        catch ME
            fprintf('? Error in first-level analysis for session %s: %s\n', session, ME.message);
            return;
        end
    end
end

function session_dirs = create_session_directories(config, session)
    session_dirs = struct();
    session_dirs.timing = fullfile(config.timing_dir, sprintf('ses-%s', session));
    session_dirs.rt = fullfile(config.rt_dir, sprintf('ses-%s', session));
    session_dirs.motion = fullfile(config.motion_regressor_dir, sprintf('ses-%s', session));
    session_dirs.first_level = fullfile(config.first_level_dir, sprintf('ses-%s', session));
    session_dirs.qc = fullfile(config.qc_dir, sprintf('ses-%s', session));
    
    dirs_to_create = struct2cell(session_dirs);
    for i = 1:length(dirs_to_create)
        if ~exist(dirs_to_create{i}, 'dir')
            mkdir(dirs_to_create{i});
        end
    end
end

function analysis_config = prepare_session_analysis_config(config, session, session_subjects, session_dirs)
    analysis_config.subject_ids = session_subjects;
    analysis_config.data_dir = config.fmriprep_dir;
    analysis_config.timing_dir = session_dirs.timing;
    analysis_config.regressor_dir = session_dirs.motion;
    analysis_config.output_dir = session_dirs.first_level;
    analysis_config.tr = config.tr;
    analysis_config.hpf = config.hpf;
    analysis_config.smooth_fwhm = config.smooth_fwhm;
    analysis_config.n_volumes = config.n_volumes;
    analysis_config.session = session;
end

function create_output_directories(config)
    base_dirs_to_create = {
        config.timing_dir
        config.rt_dir
        config.motion_regressor_dir  
        config.first_level_dir
        config.qc_dir
    };
    
    for i = 1:length(base_dirs_to_create)
        if ~exist(base_dirs_to_create{i}, 'dir')
            mkdir(base_dirs_to_create{i});
        end
    end
    
    for session_idx = 1:length(config.sessions_to_process)
        session = config.sessions_to_process{session_idx};
        create_session_directories(config, session);
    end
end