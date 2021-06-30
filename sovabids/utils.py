import os
import mne
import requests
import numpy as np
import collections

from mne_bids.write import _write_raw_brainvision

def get_nulls():
    """Return values we consider as 'empty'."""
    return ['',None,{},[]]

def get_supported_extensions():
    """Return the current supported extensions."""
    return ['.set' ,'.cnt' ,'.vhdr' ,'.bdf','.edf' ,'.fif'] 

def get_files(root_path):
    """Recursively scan the directory for files, returning a list with the full-paths to each."""
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths

def split_by_n(lst,n):
    """Split the list in sublists of n elements."""
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def deep_merge_N(l):
    """Merge the list of dictionaries, such that the latest one has the greater precedence."""
    d = {}
    while True:
        if len(l) == 0:
            return {}
        if len(l) == 1:
            return l[0]
        d1 = l.pop(0)
        d2 = l.pop(0)
        d = deep_merge(d1,d2)
        l.insert(0, d)

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

    From David Schneider answer at https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/15836901#15836901
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


def flatten(d, parent_key='', sep='.'):
    """Flatten the nested dictionary structure using the given separator.

    If parent_key is given, then that level is added at the start of the tree.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def nested_notation_to_tree(key,value,leaf='.'):
    """Create a nested dictionary from the single (key,value) pair, with the key being branched by the leaf separator."""
    if leaf in key:
        tree_list = key.split(leaf)
        tree_dict = value
        for key in reversed(tree_list):
            tree_dict = {key: tree_dict}
        return tree_dict
    else:
        return {key:value}

def flat_paren_counter(string):
    """Count the number of non-nested balanced parentheses in the string.
    If parenthesis is not balanced then return -1.
    """
    #Modified from
    #jeremy radcliff
    #https://codereview.stackexchange.com/questions/153078/balanced-parentheses-checker-in-python
    counter = 0
    times = 0
    inside = False
    for c in string:
        if not inside and c == '(':
            counter += 1
            inside = True
        elif inside and c == ')':
            counter -= 1
            times +=1
            inside = False
        if counter < 0:
            return -1

    if counter == 0:
        return times
    return -1

def mne_open(filepath,verbose='CRITICAL',preload=False):
    """Return the Raw mne object or the RawEpoch object depending on the case given a filepath."""
    if '.set' in filepath:
        try:
            return mne.io.read_raw_eeglab(filepath,preload=preload,verbose=verbose)
        except:
            return mne.io.read_epochs_eeglab(filepath,verbose=verbose)
    elif '.cnt' in filepath:
        return mne.io.read_raw_cnt(filepath,preload=preload,verbose=verbose)
    elif '.vhdr' in filepath:
        return mne.io.read_raw_brainvision(filepath,preload=preload,verbose=verbose)
    elif '.bdf' in filepath:
        return mne.io.read_raw_bdf(filepath,preload=preload,verbose=verbose)
    elif '-epo.fif' in filepath:
        return mne.read_epochs(filepath, preload=preload, verbose=verbose)
    elif '.fif' in filepath:
        return mne.io.read_raw_fif(filepath,preload=preload,verbose=verbose)
    else:
        return None

def download(url,path):
    """Download in the path the file from the given url.
    From H S Umer farooq answer at https://stackoverflow.com/questions/22676/how-to-download-a-file-over-http
    """
    get_response = requests.get(url,stream=True)
    file_name  = url.split("/")[-1]
    p = os.path.abspath(os.path.join(path))
    os.makedirs(p,exist_ok=True)
    print('Downloading',file_name,'at',p)
    if not os.path.isfile(os.path.join(p,file_name)):
        with open(os.path.join(p,file_name), 'wb') as f:
            for chunk in get_response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
            print('100')
    else:
        print("WARNING: File already existed. Skipping...")

def get_num_digits(N):
    """Return the number of digits of the given number N."""
    return int(np.log10(N))+1

