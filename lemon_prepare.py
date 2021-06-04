import os, sys
import mne
import pandas as pd 
import shutil

root_path = '/home/neuro/lemon'


#shutil.unpack_archive("sub-032301.tar.gz")

# Generate all files
def get_files(root_path):
    filepaths = []
    for root, dirs, files  in os.walk(root_path, topdown=False):
        for name in files:
            filepaths.append(os.path.join(root, name))
    return filepaths

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
        os.makedirs(dir)
    shutil.move(old_paths[i],new_paths[i])

# Cleanup Empty Folders
for name in indi_ids:
    try :
        shutil.rmtree(os.path.join(root_path,name))
    except :
        pass