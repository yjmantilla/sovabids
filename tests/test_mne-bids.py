import os, sys
import mne
import pandas as pd 
import shutil
import ntpath
import json
import yaml
from mne_bids import BIDSPath, read_raw_bids, print_dir_tree, make_report,write_raw_bids

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')

source_path = os.path.abspath(os.path.join(data_dir,'lemon'))

bids_root= os.path.abspath(os.path.join(data_dir,'lemon_bids'))

# Generate all files
def get_files(root_path):
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths

def run_command(command):
    # Maybe we should actually stop the whole process instead of trying it
    # After all it means ther is a problem with the rules, which is fundamental
    try:
        exec(command)
        return True
    except:
        print("WARNING, there was a problem with the following command:")
        print(command)
        return False

filepaths = get_files(source_path)
filepaths = [x for x in filepaths if '.vhdr' in x]

# Check they open ok
# for f in filepaths:
#     mne.io.read_raw_brainvision(f)

#%% BIDS CONVERSION

#CLEAN BIDS PATH
try:
    shutil.rmtree(bids_root)
except:
    pass

print_dir_tree(source_path)

with open('rules.json') as f:
    rules = json.load(f)

with open('rules.yml') as f:
    rules = yaml.load(f,yaml.FullLoader)

for f in filepaths:
    
    # Upon reading RAW MNE makes the assumptions
    raw = mne.io.read_raw_brainvision(f)

    # Should we try to infer the line frequency automatically from the psd?
    if "line_freq" in rules:
        raw.info['line_freq'] = rules["line_freq"]  # specify power line frequency as required by BIDS
    
    if "retype_channels" in rules:
        raw.set_channel_types(rules["retype_channels"])

    if "execute" in rules:
        if isinstance(rules["execute"],str):
            run_command(rules["execute"])
        if isinstance(rules["execute"],list):
            for command in rules["execute"]:
                run_command(command)
                # maybe log errors here?

    sub_id = os.path.splitext(ntpath.basename(f))[0].replace('sub-','') #this would be a rule
    bids_path = BIDSPath(subject=sub_id,task='resting',root=bids_root)
    write_raw_bids(raw, bids_path=bids_path,overwrite=True)