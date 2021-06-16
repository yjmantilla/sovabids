import os
import mne

macro = """try:
    exec(command)
except:
    print("WARNING, there was a problem with the following command:")
    print(command)
"""

def get_files(root_path):
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths

def run_command(raw,command):
    # Maybe we should actually stop the whole process instead of trying it
    # After all it means ther is a problem with the rules, which is fundamental
    try:
        exec(command)
        return raw
    except:
        print("WARNING, there was a problem with the following command:")
        print(command)
        return raw

def split_by_n(lst,n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def parse_string_from_template(string,pattern,splitter):
    """
    params:
    string : string to be parsed ie 'y:\\code\\sovabids\\_data\\lemon\\sub-010002.vhdr'
    pattern : string with the temmplate ie 'y:\\code\\sovabids\\_data\\%dataset_description.name%\\sub-%entities.subject%.vhdr'
    splitter : open and close symbol for the fields ie '%'
    
    WARNING: This function assumes that the string fields are separated by at least 1 char
    that is, metadata does not directly touch in the string.
    
    See eeg_bids_fields_collection.yml for fields, note that dot notation is used (dataset_description.name)
    
    For example:
    good: %entities.subject%-%entities.task%
    bad: %entities.subject%%entities.task%

    Use %ignore% to avoid inputting the whole path
    Not including at least absolute path with %ignore% not currently suported
    Possible problems:
    fields with numeric values, they should be converted, the problem is which to convert?
    """
    patterns_extracted = {}
    borders = pattern.split(splitter)[::2]
    fields = pattern.split(splitter)[1::2]
    last_end = 0
    for i,field in enumerate(fields):
        start = last_end+len(borders[i])+string[last_end:].find(borders[i])
        if field == fields[-1] and borders[-1] == '':
            end = -1
            value = string[start:]
        else:
            end = len(string[:start])+string[start:].find(borders[i+1])
            last_end=end
            value = string[start:end]

        if '.' in field:
            tree_list = field.split('.')
            tree_dict = value
            for key in reversed(tree_list):
                tree_dict = {key: tree_dict}
            patterns_extracted.update(tree_dict)
        else:
            patterns_extracted.update({field:value})
        #pattern = string[:value_end] + pattern[end+1:]
    return patterns_extracted

def mne_open(filename,verbose='CRITICAL',preload=False):
    """
    Function wrapper to read many eeg file types.
    Returns the Raw mne object or the RawEpoch object depending on the case. 
    """
    if '.set' in filename:
        try:
            return mne.io.read_raw_eeglab(filename,preload=preload,verbose=verbose)
        except:
            return mne.io.read_epochs_eeglab(filename,verbose=verbose)
    elif '.cnt' in filename:
        return mne.io.read_raw_cnt(filename,preload=preload,verbose=verbose)
    elif '.vhdr' in filename:
        return mne.io.read_raw_brainvision(filename,preload=preload,verbose=verbose)
    elif '.bdf' in filename:
        return mne.io.read_raw_bdf(filename,preload=preload,verbose=verbose)
    elif '-epo.fif' in filename:
        return mne.read_epochs(filename, preload=preload, verbose=verbose)
    elif '.fif' in filename:
        return mne.io.read_raw_fif(filename,preload=preload,verbose=verbose)
    else:
        return None
