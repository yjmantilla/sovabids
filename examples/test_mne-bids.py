import os
import shutil
from sovabids.apply_rules import apply_rules

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')
data_dir = os.path.abspath(data_dir)

source_path = os.path.abspath(os.path.join(data_dir,'lemon'))
bids_root= os.path.abspath(os.path.join(data_dir,'lemon_bids'))
rules_path = 'examples\\test_mne-bids_rules.yml'

#CLEAN BIDS PATH
try:
    shutil.rmtree(bids_root)
except:
    pass

apply_rules(source_path,bids_root,rules_path)
