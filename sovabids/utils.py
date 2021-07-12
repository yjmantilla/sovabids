"Module with misc utils for sovabids."

import os
import mne
import requests
import numpy as np
import collections
import json
from mne_bids.utils import _write_json
from sovabids import __path__

from mne_bids.write import _write_raw_brainvision

def get_nulls():
    """Return values we consider as 'empty'."""
    return ['',None,{},[]]

def get_supported_extensions():
    """Return the current supported extensions.
    
    Returns
    -------
    
    list of str :
        The extensions supported by the package.
    """
    return ['.set' ,'.cnt' ,'.vhdr' ,'.bdf','.edf' ,'.fif'] 

def get_files(root_path):
    """Recursively scan the directory for files, returning a list with the full-paths to each.
    
    Parameters
    ----------

    root_path : str
        The path we want to obtain the files from.

    Returns
    -------

    filepaths : list of str
        A list containing the path to each file in root_path.
    """
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths

def split_by_n(lst,n):
    """Split the list in sublists of n elements.
    
    Parameters
    ----------

    lst : list
        The list to be split

    n : int
        The number of elements in each sublist.
    
    Returns
    -------

    list of list
        The split list
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def deep_merge_N(l):
    """Merge the list of dictionaries, such that the latest one has the greater precedence.
    
    Parameters
    ----------

    l : list of dict
        List containing the dictionaries to be merged, having precedence on the last ones.
    
    Returns
    -------

    dict :
        The merged dictionary.
    """
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

    Parameters
    ----------

    a : object
    b : object

    Returns
    -------

    dict :
        Merged dictionary.
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

    Parameters
    ----------

    d : dict
        The dictionary to flat.
    parent_key : str, optional
        The optional top-level field of the dictionary.
    sep : str, optional
        The separator to indicate nesting/branching/hierarchy.

    Returns
    -------
    dict :
        A dictionary with only one level of fields.
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
    """Create a nested dictionary from the single (key,value) pair, with the key being branched by the leaf separator.
    
    Parameters
    ----------
    key : str
        The key/field to be nested, assuming nesting is represented with the "leaf" parameters.
    value : object
        The value that it will have at the last level of nesting.
    leaf : str, optional
        The separator used to indicate nesting in "key" parameter.
    
    Returns
    -------

    dict :
        Nested dictionary.
    """
    if leaf in key:
        tree_list = key.split(leaf)
        tree_dict = value
        for key in reversed(tree_list):
            tree_dict = {key: tree_dict}
        return tree_dict
    else:
        return {key:value}

def flat_paren_counter(string):
    """Count the number of non-nested balanced parentheses in the string. If parenthesis is not balanced then return -1.

    Parameters
    ----------

    string : str
        The string we will inspect for balanced parentheses.
    
    Returns
    -------

    int :
        The number of non-nested balanced parentheses or -1 if the string has unbalanced parentheses.
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

def download(url,path):
    """Download in the path the file from the given url.

    From H S Umer farooq answer at https://stackoverflow.com/questions/22676/how-to-download-a-file-over-http

    Parameters
    ----------

    url : str
        The url of the file to download.
    path : str
        The path where to download the file.
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
    """Return the number of digits of the given number N.
    
    Paremeters
    ----------
    N : int
        The number we want to apply the function to.
    
    Returns
    -------
    int :
        The numbers of digits needed to represent the number N.
    """
    return int(np.log10(N))+1

def get_project_dir():
    """Return the path of the sovabids project, that is the root of the git repository.

    Needs that sovabids was installed in editable mode from the git repository.

    Returns
    -------

    str :
        Path of the root of the git repository.
    """
    return os.path.realpath(os.path.join(__path__[0],'..'))

def update_dataset_description(dataset_description,bids_root):
    """Update the dataset_description.json located at bids_root given a dictionary.

    If it exist, updates with the new given values. If it doesn't exist, then creates it.

    Parameters
    ----------

    dataset_description : dict
        The dataset_description dictionary to update with, following the schema of the dataset_description.json file of bids.
    bids_root : str
        The path of the bids_root of the dataset description file, basically the folder where the file is.
    """
    jsonfile = os.path.join(bids_root,'dataset_description.json')
    os.makedirs(bids_root,exist_ok=True)
    if os.path.isfile(jsonfile):
        with open(jsonfile) as f:
            info = json.load(f)
    else:
        info = {}
    if dataset_description != {}:
        info.update(dataset_description)
        _write_json(jsonfile,info,overwrite=True)
    # Problem: Authors with strange characters are written incorrectly.
