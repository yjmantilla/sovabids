import os, sys
import mne
import pandas as pd 
import shutil
import ntpath
from mne_bids import BIDSPath, read_raw_bids, print_dir_tree, make_report,write_raw_bids

source_path = '/home/neuro/lemon'
bids_root= '/home/neuro/lemon_bids'


# Generate all files
def get_files(root_path):
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths

filepaths = get_files(source_path)
filepaths = [x for x in filepaths if '.vhdr' in x]

# Check they open ok
# for f in filepaths:
#     mne.io.read_raw_brainvision(f)

#%% BIDS CONVERSION

print_dir_tree(source_path)

for f in filepaths:
    raw = mne.io.read_raw_brainvision(f)

    # Should we try to infer the line frequency automatically from the psd?
    raw.info['line_freq'] = 50  # specify power line frequency as required by BIDS
    
    sub_id = os.path.splitext(ntpath.basename(f))[0].replace('sub-','') #this would be a rule
    bids_path = BIDSPath(subject=sub_id,task='resting',root=bids_root)
    write_raw_bids(raw, bids_path=bids_path,overwrite=True)