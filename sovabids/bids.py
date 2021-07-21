"""Module with bids utilities."""
import os
import json

from mne_bids.utils import _write_json

def update_dataset_description(dataset_description,bids_path):
    """Update the dataset_description.json located at bids_path given a dictionary.

    If it exist, updates with the new given values. If it doesn't exist, then creates it.

    Parameters
    ----------

    dataset_description : dict
        The dataset_description dictionary to update with, following the schema of the dataset_description.json file of bids.
    bids_path : str
        The path of the bids_path of the dataset description file, basically the folder where the file is.
    """
    jsonfile = os.path.join(bids_path,'dataset_description.json')
    os.makedirs(bids_path,exist_ok=True)
    if os.path.isfile(jsonfile):
        with open(jsonfile) as f:
            info = json.load(f)
    else:
        info = {}
    if dataset_description != {}:
        info.update(dataset_description)
        _write_json(jsonfile,info,overwrite=True)
    # Problem: Authors with strange characters are written incorrectly.