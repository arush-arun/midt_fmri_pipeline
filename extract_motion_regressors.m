function extract_motion_regressors(config)
% EXTRACT_MOTION_REGRESSORS Extract motion parameters from fMRIPrep confounds

    if ~isfield(config, 'dummy_scans'), config.dummy_scans = 5; end
    if ~isfield(config, 'sessions'), config.sessions = {'1'}; end
    if ~isfield(config, 'motion_params')
        config.motion_params = {'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'};
    end
    if ~isfield(config, 'task'), config.task = 'MIDT'; end
    
    validate_regressor_config(config);
    
    qc_data = [];
    processing_log = {};
    
    fprintf('Starting motion regressor extraction for %d subjects\n', length(config.subject_ids));
    
    for i = 1:length(config.subject_ids)
        subject_id = config.subject_ids{i};
        fprintf('\nProcessing subject %d/%d: %s\n', i, length(config.subject_ids), subject_id);
        
        for j = 1:length(config.sessions)
            session = config.sessions{j};
            fprintf('  Session %s... ', session);
            
            try
                % Create subject-specific output directory
                % config.output_dir is already session-specific (e.g., /motion_regressors/ses-1/)
                % so we just need to add the subject directory
                subject_output_dir = fullfile(config.output_dir, subject_id);
                if ~exist(subject_output_dir, 'dir')
                    mkdir(subject_output_dir);
                end
                
                confound_file = fullfile(config.fmriprep_dir, subject_id, sprintf('ses-%s', session), 'func', ...
                    sprintf('%s_ses-%s_task-%s_desc-confounds_timeseries.tsv', subject_id, session, config.task));
                
                output_file = fullfile(subject_output_dir, ...
                    sprintf('%s_ses-%s_task-%s_Regressors.txt', subject_id, session, config.task));
                
                if ~exist(confound_file, 'file')
                    fprintf('SKIP (confound file not found)\n');
                    continue;
                end
                
                [motion_data, qc_metrics] = extract_subject_motion(confound_file, config);
                save_motion_regressors(motion_data, output_file);
                
                qc_metrics.subject_id = subject_id;
                qc_metrics.session = session;
                qc_data = [qc_data; qc_metrics];
                
                fprintf('SUCCESS (%.1f mm max motion)\n', qc_metrics.max_motion_mm);
                
            catch ME
                fprintf('ERROR: %s\n', ME.message);
            end
        end
    end
    
    generate_motion_qc_report(qc_data, config.output_dir);
end

function [motion_data, qc_metrics] = extract_subject_motion(confound_file, config)
    confounds = tdfread(confound_file);
    field_names = fieldnames(confounds);
    
    n_volumes_total = length(confounds.(field_names{1}));
    n_volumes_analysis = n_volumes_total - config.dummy_scans;
    
    motion_data = [];
    
    for param_idx = 1:length(config.motion_params)
        param_name = config.motion_params{param_idx};
        
        if isfield(confounds, param_name)
            param_data = confounds.(param_name);
            param_data = param_data((config.dummy_scans + 1):end);
            motion_data = [motion_data, param_data];
        end
    end
    
    qc_metrics = calculate_motion_qc(motion_data, config.motion_params);
    qc_metrics.n_volumes = n_volumes_analysis;
end

function qc_metrics = calculate_motion_qc(motion_data, motion_params)
    trans_idx = contains(motion_params, 'trans');
    
    if sum(trans_idx) > 0
        trans_data = motion_data(:, trans_idx);
        translation_euclidean = sqrt(sum(trans_data.^2, 2));
        qc_metrics.max_motion_mm = max(translation_euclidean);
        qc_metrics.mean_motion_mm = mean(translation_euclidean);
    else
        qc_metrics.max_motion_mm = NaN;
        qc_metrics.mean_motion_mm = NaN;
    end
end

function save_motion_regressors(motion_data, output_file)
    output_dir = fileparts(output_file);
    if ~exist(output_dir, 'dir')
        mkdir(output_dir);
    end
    dlmwrite(output_file, motion_data, 'delimiter', ' ', 'precision', '%.6f');
end

function generate_motion_qc_report(qc_data, output_dir)
    if isempty(qc_data)
        return;
    end
    
    qc_table = struct2table(qc_data);
    
    fprintf('\n=== MOTION QUALITY CONTROL REPORT ===\n');
    fprintf('Total subjects processed: %d\n', height(qc_table));
    fprintf('Mean maximum motion: %.2f ± %.2f mm\n', ...
        nanmean(qc_table.max_motion_mm), nanstd(qc_table.max_motion_mm));
    
    qc_file = fullfile(output_dir, 'motion_qc_report.csv');
    writetable(qc_table, qc_file);
    fprintf('QC report saved to: %s\n', qc_file);
end

function validate_regressor_config(config)
    required_fields = {'subject_ids', 'fmriprep_dir', 'output_dir'};
    
    for i = 1:length(required_fields)
        field = required_fields{i};
        if ~isfield(config, field)
            error('Missing required configuration field: %s', field);
        end
    end
end