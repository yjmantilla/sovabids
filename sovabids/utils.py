import os
import mne
import re

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

def unescape(text):
    regex = re.compile(b'\\\\(\\\\|[0-7]{1,3}|x.[0-9a-f]?|[\'"abfnrt]|.|$)')
    def replace(m):
        b = m.group(1)
        if len(b) == 0:
            raise ValueError("Invalid character escape: '\\'.")
        i = b[0]
        if i == 120:
            v = int(b[1:], 16)
        elif 48 <= i <= 55:
            v = int(b, 8)
        elif i == 34: return b'"'
        elif i == 39: return b"'"
        elif i == 92: return b'\\'
        elif i == 97: return b'\a'
        elif i == 98: return b'\b'
        elif i == 102: return b'\f'
        elif i == 110: return b'\n'
        elif i == 114: return b'\r'
        elif i == 116: return b'\t'
        else:
            s = b.decode('ascii')
            raise UnicodeDecodeError(
                'stringescape', text, m.start(), m.end(), "Invalid escape: %r" % s
            )
        return bytes((v, ))
    result = regex.sub(replace, text)

def parse_string_from_template(string,pattern,splitter='%'):
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
    string = string.replace('\\','/') # USE POSIX PLEASE
    pattern = pattern.replace('\\','/')
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

        if '.' in field:
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
