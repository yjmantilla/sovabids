import os
import mne
import re
import requests


macro = """try:
    exec(command)
except:
    print("WARNING, there was a problem with the following command:")
    print(command)
"""

def get_supported_extensions():
    return ['.set' ,'.cnt' ,'.vhdr' ,'.bdf','.edf' ,'.fif'] 

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

def deep_merge_N(l):
    d = {}
    while True:
        if len(l) == 0:
            return {}
        if len(l) == 1:
            return l[0]
        d1 = l.pop()
        d2 = l.pop()
        d = deep_merge(d1,d2)
        l.append(d)

def deep_merge(a, b):
    """
    Merge two values, with `b` taking precedence over `a`.

    Semantics:
    - If either `a` or `b` is not a dictionary, `a` will be returned only if
      `b` is `None`. Otherwise `b` will be returned.
    - If both values are dictionaries, they are merged as follows:
        * Each key that is found only in `a` or only in `b` will be included in
          the output collection with its value intact.
        * For any key in common between `a` and `b`, the corresponding values
          will be merged with the same semantics.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a if b is None else b
    else:
        # If we're here, both a and b must be dictionaries or subtypes thereof.

        # Compute set of all keys in both dictionaries.
        keys = set(a.keys()) | set(b.keys())

        # Build output dictionary, merging recursively values with common keys,
        # where `None` is used to mean the absence of a value.
        return {
            key: deep_merge(a.get(key), b.get(key))
            for key in keys
        }

import collections

def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def parse_string_from_template(string,pattern,splitter='%'):
    """
    USE POSIX
    params:
    string : string to be parsed ie 'y:/code/sovabids/_data/lemon/sub-010002.vhdr'
    pattern : string with the temmplate ie 'y:/code/sovabids/_data/%dataset_description.name%/sub-%entities.subject%.vhdr'
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
    #TODO: Change the name of the function for something more appropiate
    string = string.replace('\\','/') # USE POSIX PLEASE
    pattern = pattern.replace('\\','/')
    if pattern.count('%') == 0 or pattern.count('%') % 2 != 0:
        return {}
    else:
        borders = pattern.split(splitter)[::2]
        fields = pattern.split(splitter)[1::2]
        last_end = 0
        l = []
        for i,field in enumerate(fields):
            start = last_end+len(borders[i])+string[last_end:].find(borders[i])
            if field == fields[-1] and borders[-1] == '':
                end = -1
                value = string[start:]
            else:
                end = len(string[:start])+string[start:].find(borders[i+1])
                last_end=end
                value = string[start:end]

            if '.' in field: #TODO: Make this an argument
                tree_list = field.split('.')
                tree_dict = value
                for key in reversed(tree_list):
                    tree_dict = {key: tree_dict}
                l.append(tree_dict)
            else:
                l.append({field:value})
        return deep_merge_N(l)


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


def create_dir(data_dir):
    if not os.path.isdir(data_dir):
        #os.makedirs(data_dir, exist_ok=True)
        os.mkdir(data_dir)

def download(url,path):
    get_response = requests.get(url,stream=True)
    file_name  = url.split("/")[-1]
    p = os.path.abspath(os.path.join(path))
    create_dir(p)
    print('Downloading',file_name,'at',p)
    if not os.path.isfile(os.path.join(p,file_name)):
        with open(os.path.join(p,file_name), 'wb') as f:
            for chunk in get_response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
            print('100')
    else:
        print("WARNING: File already existed. Skipping...")


def get_files(root_path):
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths
