import os, sys
import mne
import pandas as pd 
import shutil
from sovabids.utils import download,get_files
this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')

os.makedirs(data_dir,exist_ok=True)
#shutil.unpack_archive("sub-032301.tar.gz")

#%% Donwnload lemon Database

urls = ['https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032301.tar.gz',
'https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032302.tar.gz',
'https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/Compressed_tar/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/sub-032303.tar.gz',
'https://fcp-indi.s3.amazonaws.com/data/Projects/INDI/MPI-LEMON/name_match.csv']

for url in urls:
    download(url,os.path.join(data_dir,'lemon'))

root_path = os.path.abspath(os.path.join(data_dir,'lemon'))

# Generate all files

filepaths = get_files(root_path)

# Unpack files

for file in filepaths:
    if 'tar.gz' in file:
        shutil.unpack_archive(file,root_path)
        #os.rm(file) # for deletion of packs


# Label Correction
name_match = pd.read_csv(os.path.join(root_path,'name_match.csv'))

indi_ids = name_match['INDI_ID'].tolist()
initial_ids = name_match['Initial_ID'].tolist()
del name_match

filepaths = get_files(root_path) 

new_paths = []
old_paths = []
for i in range(len(indi_ids)):
    old_name = indi_ids[i]
    new_name = initial_ids[i]
    for file in filepaths:
        if old_name in file and '.tar.gz' not in file:
            new_path = file.replace(old_name,new_name)
            dir,file2 = os.path.split(new_path)
            new_paths.append(os.path.join(root_path,file2))
            old_paths.append(file) # guarantee order


# Renaming

for i in range(len(new_paths)):
    dir,file = os.path.split(new_paths[i])
    if not os.path.exists(dir):
        os.makedirs(dir,exist_ok=True)
    shutil.move(old_paths[i],new_paths[i])

# Cleanup Empty Folders
for name in indi_ids:
    try :
        shutil.rmtree(os.path.join(root_path,name))
    except :
        pass