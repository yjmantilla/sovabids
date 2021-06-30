# Run lemon_prepare first

import os, sys
import mne
import pandas as pd 
import shutil
import requests
from sovabids.utils import get_files

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')
root_path = os.path.abspath(os.path.join(data_dir,'lemon'))
bidscoin_input_path = os.path.abspath(os.path.join(data_dir,'lemon_bidscoin_input'))

os.makedirs(bidscoin_input_path,exist_ok=True)

files = get_files(root_path)
files = [x for x in files if x.split('.')[-1] in ['eeg','vmrk','vhdr'] ]

files_out = []
for f in files:
    session = 'ses-001'
    task = 'resting'
    head,tail=os.path.split(f)
    sub = tail.split('.')[0]
    new_path = os.path.join(bidscoin_input_path,sub,session,task,tail)
    files_out.append(new_path)

for old,new in zip(files,files_out):
    print(old,' to ',new)
    os.makedirs(os.path.split(new)[0], exist_ok=True)
    if not os.path.isfile(new):
        shutil.copy2(old,new)
    else:
        print('already done, skipping...')
print('finish')