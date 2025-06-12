%% =================================================================

function run_first_level_analysis(config)
% RUN_FIRST_LEVEL_ANALYSIS Perform SPM first-level analysis for MIDT task
%
% Input:
%   config - Structure with analysis parameters:
%     .subject_ids     - Cell array of subject IDs
%     .data_dir        - Directory containing preprocessed fMRI data
%     .timing_dir      - Directory containing .mat timing files
%     .regressor_dir   - Directory containing confound regressors
%     .output_dir      - Directory for first-level results
%     .tr              - Repetition time (default: 1.6s)
%     .hpf             - High-pass filter cutoff (default: 128s)
%     .smooth_fwhm     - Smoothing kernel size (default: 6mm)
%
% Example usage:
%   config.subject_ids = {'sub-001', 'sub-002'};
%   config.data_dir = '/path/to/fmriprep/output';
%   config.timing_dir = '/path/to/timing/files';
%   config.regressor_dir = '/path/to/confound/regressors';
%   config.output_dir = '/path/to/first/level/results';
%   run_first_level_analysis(config);

    % Set defaults
    if ~isfield(config, 'tr'), config.tr = 1.6; end
    if ~isfield(config, 'hpf'), config.hpf = 128; end
    if ~isfield(config, 'smooth_fwhm'), config.smooth_fwhm = 6; end
    if ~isfield(config, 'n_volumes'), config.n_volumes = 367; end % Total volumes - 5 dummy
    
    % Validate required fields
    required_fields = {'subject_ids', 'data_dir', 'timing_dir', 'regressor_dir', 'output_dir'};
    for field = required_fields
        if ~isfield(config, field{1})
            error('Missing required config field: %s', field{1});
        end
    end
    
    % Initialize SPM
    spm('defaults', 'FMRI');
    
    % Process each subject
    for k = 1:length(config.subject_ids)
        
        subject_id = config.subject_ids{k};
        fprintf('\nProcessing subject %d/%d: %s\n', k, length(config.subject_ids), subject_id);
        
        % Set up directories
        subject_output_dir = fullfile(config.output_dir, subject_id);
        if ~exist(subject_output_dir, 'dir')
            mkdir(subject_output_dir);
        end
        
        % Define file paths
        timing_file = fullfile(config.timing_dir, sprintf('%s_ses-1_task-MIDT.mat', subject_id));
        regressor_file = fullfile(config.regressor_dir, subject_id, sprintf('%s_ses-1_task-MIDT_Regressors.txt', subject_id));
        
        % Check if required files exist
        if ~exist(timing_file, 'file')
            fprintf('Warning: Timing file not found for %s: %s\n', subject_id, timing_file);
            continue;
        end
        
        if ~exist(regressor_file, 'file')
            fprintf('Warning: Regressor file not found for %s: %s\n', subject_id, regressor_file);
            continue;
        end
        
        % Build functional image list
        func_images = cell(config.n_volumes, 1);
        for j = 6:(5 + config.n_volumes) % Skip first 5 dummy scans
            func_file = sprintf('%s_ses-1_task-MIDT_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold_%dmm_blur.nii,%d', ...
                subject_id, config.smooth_fwhm, j);
            func_images{j-5} = fullfile(config.data_dir, subject_id, 'ses-1', 'func', func_file);
        end
        
        % Check if functional images exist
        if ~exist(func_images{1}(1:end-2), 'file') % Remove volume number for check
            fprintf('Warning: Functional images not found for %s\n', subject_id);
            continue;
        end
        
        try
            % Create SPM batch
            matlabbatch = create_spm_batch(subject_output_dir, func_images, timing_file, regressor_file, config);
            
            % Run analysis
            spm_jobman('run', matlabbatch);
            fprintf('Completed first-level analysis for %s\n', subject_id);
            
        catch ME
            fprintf('Error processing %s: %s\n', subject_id, ME.message);
        end
    end
end

function matlabbatch = create_spm_batch(output_dir, func_images, timing_file, regressor_file, config)
% CREATE_SPM_BATCH Create SPM batch structure for first-level analysis

    % Model specification
    matlabbatch{1}.spm.stats.fmri_spec.dir = {output_dir};
    matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'secs';
    matlabbatch{1}.spm.stats.fmri_spec.timing.RT = config.tr;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = 16;
    matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = 8;
    
    % Functional images
    matlabbatch{1}.spm.stats.fmri_spec.sess.scans = func_images;
    
    % Conditions and regressors
    matlabbatch{1}.spm.stats.fmri_spec.sess.cond = struct('name', {}, 'onset', {}, 'duration', {}, 'tmod', {}, 'pmod', {}, 'orth', {});
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {timing_file};
    matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
    matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {regressor_file};
    matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = config.hpf;
    
    % Model options
    matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
    matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];
    matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
    matlabbatch{1}.spm.stats.fmri_spec.global = 'None';
    matlabbatch{1}.spm.stats.fmri_spec.mthresh = 0.8;
    matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
    matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';
    
    % Model estimation
    matlabbatch{2}.spm.stats.fmri_est.spmmat(1) = cfg_dep('fMRI model specification: SPM.mat File', ...
        substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
    matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
    matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;
    
    % Contrasts
    matlabbatch{3}.spm.stats.con.spmmat(1) = cfg_dep('Model estimation: SPM.mat File', ...
        substruct('.','val', '{}',{2}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
    
    % Define contrasts (based on 6 conditions: anticip-reward, anticip-neutral, fb-reward, fb-miss-reward, fb-corr-neutral, fb-incorr-neutral)
    contrasts = define_midt_contrasts();
    
    for i = 1:length(contrasts)
        matlabbatch{3}.spm.stats.con.consess{i}.tcon.name = contrasts(i).name;
        matlabbatch{3}.spm.stats.con.consess{i}.tcon.weights = contrasts(i).weights;
        matlabbatch{3}.spm.stats.con.consess{i}.tcon.sessrep = 'none';
    end
    
    matlabbatch{3}.spm.stats.con.delete = 0;
end

function contrasts = define_midt_contrasts()
% DEFINE_MIDT_CONTRASTS Define standard contrasts for MIDT analysis

    contrasts = [
        struct('name', 'Anticipation: Reward > Neutral', 'weights', [1 -1 0 0 0 0]),
        struct('name', 'Anticipation: Neutral > Reward', 'weights', [-1 1 0 0 0 0]),
        struct('name', 'Feedback: Reward > Correct Neutral', 'weights', [0 0 1 0 -1 0]),
        struct('name', 'Feedback: Correct Neutral > Reward', 'weights', [0 0 -1 0 1 0]),
        struct('name', 'Feedback: Reward Success > Failure', 'weights', [0 0 1 -1 0 0]),
        struct('name', 'Feedback: Reward Failure > Success', 'weights', [0 0 -1 1 0 0]),
        struct('name', 'Feedback: Neutral Success > Failure', 'weights', [0 0 0 0 1 -1]),
        struct('name', 'Feedback: Neutral Failure > Success', 'weights', [0 0 0 0 -1 1]),
        struct('name', 'Feedback: Reward Success Only', 'weights', [0 0 1 0 0 0]),
        struct('name', 'Feedback: Neutral Success Only', 'weights', [0 0 0 0 1 0]),
        struct('name', 'Anticipation: Reward Only', 'weights', [1 0 0 0 0 0]),
        struct('name', 'Anticipation: Neutral Only', 'weights', [0 1 0 0 0 0])
    ];
end
