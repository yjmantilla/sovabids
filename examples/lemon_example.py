import os
import shutil
from sovabids.rules import apply_rules
from sovabids.convert import convert_them
from sovabids.datasets import lemon_prepare

lemon_prepare()

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')
data_dir = os.path.abspath(data_dir)
example_dir = os.path.abspath(os.path.join(this_dir,'..','examples'))

source_path = os.path.abspath(os.path.join(data_dir,'lemon'))
bids_root= os.path.abspath(os.path.join(data_dir,'lemon_bids'))
rules_path = os.path.join(example_dir,'lemon_example_rules.yml')
mapping_path = os.path.join(bids_root,'code','sovabids','mappings.yml')
#CLEAN BIDS PATH
try:
    shutil.rmtree(bids_root)
except:
    pass

apply_rules(source_path,bids_root,rules_path)
convert_them(mapping_path)
print('LEMON CONVERSION FINISHED!')
