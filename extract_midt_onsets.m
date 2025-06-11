%IMPORTANT- inspect your text file- this code will not run properly if the
%text filehas issues such as empty text file, or coding of the variables
%done incorrectly.
function extract_midt_onsets(data_dir, output_dir, varargin)
% EXTRACT_MIDT_ONSETS Extract onset and duration times from MIDT timing files

    p = inputParser;
    addParameter(p, 'session', '1', @ischar);
    addParameter(p, 'auto_detect', true, @islogical);
    addParameter(p, 'interactive', false, @islogical);
    parse(p, varargin{:});
    
    session = p.Results.session;
    auto_detect = p.Results.auto_detect;
    interactive = p.Results.interactive;

    if ~exist(data_dir, 'dir')
        error('Data directory does not exist: %s', data_dir);
    end
    
    if ~exist(output_dir, 'dir')
        mkdir(output_dir);
    end
    
    % Get timing files
    if interactive
        [filenames, pathname] = uigetfile('*.txt', 'Select timing files', data_dir, 'MultiSelect', 'on');
        if ischar(filenames)
            filenames = {filenames};
        end
        if isequal(filenames, 0)
            fprintf('No files selected. Exiting.\n');
            return;
        end
    else
        pathname = data_dir;
        txt_files = dir(fullfile(data_dir, '*task*.txt'));
        if isempty(txt_files)
            txt_files = dir(fullfile(data_dir, 'Reward_task*.txt'));
        end
        if isempty(txt_files)
            txt_files = dir(fullfile(data_dir, '*.txt'));
        end
        
        if isempty(txt_files)
            error('No .txt files found in directory: %s', data_dir);
        end
        
        % Filter out hidden files and metadata files
        valid_files = {};
        for i = 1:length(txt_files)
            filename = txt_files(i).name;
            if ~startsWith(filename, '.') && ~startsWith(filename, '._') && ~strcmp(filename, 'desktop.ini')
                valid_files{end+1} = filename;
            else
                fprintf('Skipping metadata/hidden file: %s\n', filename);
            end
        end
        
        if isempty(valid_files)
            error('No valid .txt files found in directory: %s', data_dir);
        end
        
        filenames = valid_files;
        fprintf('Auto-detected %d valid timing files\n', length(filenames));
    end
    
    % Process each file
    successful_files = 0;
    failed_files = {};
    
    for j = 1:length(filenames)
        filename = filenames{j};
        fprintf('Processing file %d/%d: %s\n', j, length(filenames), filename);
        
        try
            original_subject_id = extract_subject_from_filename(filename);
            
            if isempty(original_subject_id)
                fprintf('  WARNING: Could not extract subject ID from filename. Skipping.\n');
                failed_files{end+1} = filename;
                continue;
            end
            
            bids_subject_id = convert_to_bids_format(original_subject_id);
            fprintf('  Subject: %s -> %s\n', original_subject_id, bids_subject_id);
            
            timing_data = importdata(fullfile(pathname, filename));
            
            if ~isstruct(timing_data) || ~isfield(timing_data, 'data') || ~isfield(timing_data, 'textdata')
                fprintf('  WARNING: Invalid timing file format. Skipping.\n');
                failed_files{end+1} = filename;
                continue;
            end
            
            % Initialize SPM condition structures
            names = cell(1, 6);
            onsets = cell(1, 6);
            durations = cell(1, 6);
            
            names{1} = 'anticip-reward';
            names{2} = 'anticip-neutral';
            names{3} = 'fb-reward';
            names{4} = 'fb-miss-reward';
            names{5} = 'fb-corr-neutral';
            names{6} = 'fb-incorr-neutral';
            
            % Process trials (typically trials 21-80 in MIDT)
            trial_start = 21;
            trial_end = min(80, size(timing_data.data, 1));
            
            for i = trial_start:trial_end
                if i+1 > size(timing_data.textdata, 1) || i > size(timing_data.data, 1)
                    continue;
                end
                
                if size(timing_data.textdata, 2) >= 3
                    cue_type = timing_data.textdata{i+1, 3};
                else
                    continue;
                end
                
                if size(timing_data.data, 2) >= 9
                    accuracy = timing_data.data(i, 1);
                    cue_onset = timing_data.data(i, 7) / 1000;
                    cue_offset = timing_data.data(i, 8) / 1000;
                    feedback_onset = timing_data.data(i, 9) / 1000;
                else
                    continue;
                end
                
                cue_duration = cue_offset - cue_onset;
                feedback_duration = 2;
                
                % Process reward trials
                if strcmp(cue_type, 'cue_smile.bmp')
                    onsets{1} = [onsets{1}, cue_onset];
                    durations{1} = [durations{1}, cue_duration];
                    
                    if accuracy == 1
                        onsets{3} = [onsets{3}, feedback_onset];
                        durations{3} = [durations{3}, feedback_duration];
                    elseif accuracy == 0
                        onsets{4} = [onsets{4}, feedback_onset];
                        durations{4} = [durations{4}, feedback_duration];
                    end
                    
                % Process neutral trials
                elseif strcmp(cue_type, 'cue_neutral.bmp')
                    onsets{2} = [onsets{2}, cue_onset];
                    durations{2} = [durations{2}, cue_duration];
                    
                    if accuracy == 1
                        onsets{5} = [onsets{5}, feedback_onset];
                        durations{5} = [durations{5}, feedback_duration];
                    elseif accuracy == 0
                        onsets{6} = [onsets{6}, feedback_onset];
                        durations{6} = [durations{6}, feedback_duration];
                    end
                end
            end
            
            % Save in BIDS format
            output_filename = sprintf('%s_ses-%s_task-MIDT.mat', bids_subject_id, session);
            output_file = fullfile(output_dir, output_filename);
            save(output_file, 'names', 'onsets', 'durations');
            fprintf('  Saved as: %s\n', output_filename);
            
            fprintf('    Reward anticipation: %d trials\n', length(onsets{1}));
            fprintf('    Neutral anticipation: %d trials\n', length(onsets{2}));
            fprintf('    Total trials: %d\n', length(onsets{1}) + length(onsets{2}));
            
            successful_files = successful_files + 1;
            
        catch ME
            fprintf('  ERROR processing file %s: %s\n', filename, ME.message);
            failed_files{end+1} = filename;
        end
    end
    
    fprintf('\n=== TIMING EXTRACTION SUMMARY ===\n');
    fprintf('Successfully processed: %d files\n', successful_files);
    fprintf('Failed to process: %d files\n', length(failed_files));
    
    if ~isempty(failed_files)
        fprintf('Failed files: %s\n', strjoin(failed_files, ', '));
    end
end

function original_id = extract_subject_from_filename(filename)
    original_id = '';
    if isempty(filename) || ~ischar(filename)
        return;
    end
    
    patterns = {
        'Reward_task_([^_]+)_reward'
        'task_([^_]+)_'
        '^([^_]+)_'
        '([a-zA-Z]*\d+[a-zA-Z]*\d*)'
    };
    
    for i = 1:length(patterns)
        match = regexp(filename, patterns{i}, 'tokens');
        if ~isempty(match)
            original_id = match{1}{1};
            return;
        end
    end
end

function bids_id = convert_to_bids_format(original_id)
    bids_id = '';
    
    if isempty(original_id) || ~ischar(original_id)
        bids_id = 'sub-unknown';
        return;
    end
    
    % Pattern 1: ld###s# format
    pattern1 = '^ld(\d+)s\d*$';
    match1 = regexp(original_id, pattern1, 'tokens');
    if ~isempty(match1)
        subject_num = str2double(match1{1}{1});
        bids_id = sprintf('sub-%03d', subject_num);
        return;
    end
    
    % Pattern 2: sub### format
    pattern2 = '^sub(\d+)$';
    match2 = regexp(original_id, pattern2, 'tokens');
    if ~isempty(match2)
        subject_num = str2double(match2{1}{1});
        bids_id = sprintf('sub-%03d', subject_num);
        return;
    end
    
    % Pattern 3: Just numbers
    pattern3 = '^(\d+)$';
    match3 = regexp(original_id, pattern3, 'tokens');
    if ~isempty(match3)
        subject_num = str2double(match3{1}{1});
        bids_id = sprintf('sub-%03d', subject_num);
        return;
    end
    
    % Pattern 4: Already BIDS
    pattern4 = '^sub-\d{3}$';
    if ~isempty(regexp(original_id, pattern4, 'match'))
        bids_id = original_id;
        return;
    end
    
    % Fallback
    pattern5 = '(\d+)';
    match5 = regexp(original_id, pattern5, 'tokens');
    if ~isempty(match5)
        subject_num = str2double(match5{1}{1});
        bids_id = sprintf('sub-%03d', subject_num);
        return;
    end
    
    bids_id = ['sub-', strrep(original_id, '-', '')];
end
