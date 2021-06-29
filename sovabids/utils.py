import os
import mne
import re
import requests
import numpy as np
from mne_bids.write import _write_raw_brainvision
import collections


macro = """try:
    exec(command)
except:
    print("WARNING, there was a problem with the following command:")
    print(command)
"""

def get_nulls():
    return ['',None,{},[]]
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
    ## Last items should have greater precedence
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
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def nested_notation_to_tree(field,value,leaf='.'):
    if leaf in field:
        tree_list = field.split(leaf)
        tree_dict = value
        for key in reversed(tree_list):
            tree_dict = {key: tree_dict}
        return tree_dict
    else:
        return {field:value}

def flat_paren_counter(string):
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
        os.makedirs(data_dir, exist_ok=True)
        #os.mkdir(data_dir)

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


def make_dummy_dataset(PATTERN = '%dataset_description.Name%/T%entities.task%/S%entities.session%/sub%entities.subject%_%entities.run%',
    DATASET = 'DUMMY',
    NSUBS = 11,
    NTASKS = 2,
    NACQS = 2,
    NRUNS = 2,
    NSESSIONS = 4,
    NCHANNELS = 32,
    SFREQ = 200,
    STOP = 10,
    NUMEVENTS = 10,
    ROOT=None):

    if ROOT is None:
        this_dir = os.path.dirname(__file__)
        data_dir = os.path.abspath(os.path.join(this_dir,'..','_data'))
    else:
        data_dir = ROOT
    create_dir(data_dir)


    def get_num_leading_zeros(N):
        return int(np.floor(np.log10(N-1)))

    sub_zeros = get_num_leading_zeros(NSUBS)
    subs = [ str(x).zfill(sub_zeros+1) for x in range(NSUBS)]

    task_zeros = get_num_leading_zeros(NTASKS)
    tasks = [ str(x).zfill(task_zeros+1) for x in range(NTASKS)]

    run_zeros = get_num_leading_zeros(NRUNS)
    runs = [ str(x).zfill(run_zeros+1) for x in range(NRUNS)]

    ses_zeros = get_num_leading_zeros(NSESSIONS)
    sessions = [ str(x).zfill(ses_zeros+1) for x in range(NSESSIONS)]

    acq_zeros = get_num_leading_zeros(NACQS)
    acquisitions = [ str(x).zfill(acq_zeros+1) for x in range(NACQS)]

    # Create some dummy metadata
    n_channels = NCHANNELS
    sampling_freq = SFREQ  # in Hertz
    info = mne.create_info(n_channels, sfreq=sampling_freq)

    times = np.linspace(0, STOP, STOP*sampling_freq, endpoint=False)
    data = np.zeros((NCHANNELS,times.shape[0]))

    raw = mne.io.RawArray(data, info)
    raw.set_channel_types({x:'eeg' for x in raw.ch_names})
    new_events = mne.make_fixed_length_events(raw, duration=STOP//NUMEVENTS)

    for task in tasks:
        for session in sessions:
            for run in runs:
                for sub in subs:
                    for acq in acquisitions:
                        dummy = PATTERN.replace('%dataset%',DATASET)
                        dummy = dummy.replace('%task%',task)
                        dummy = dummy.replace('%session%',session)
                        dummy = dummy.replace('%subject%',sub)
                        dummy = dummy.replace('%run%',run)
                        dummy = dummy.replace('%acquisition%',acq)
                        path = [data_dir] +dummy.split('/')
                        fpath = os.path.join(*path)
                        _write_raw_brainvision(raw,fpath,new_events)