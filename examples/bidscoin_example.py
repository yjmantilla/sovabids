  
"""
===================================
LEMON dataset example with BIDSCOIN
===================================

This example illustrates the use of ``sovabids`` on the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_
using bidscoin.

The main elements of this example are:
    * A source path with the original dataset.
    * A bids path that will be the output path of the conversion.
    * A rules file that configures how the conversion is done.
    * A bidsmap template required by bidscoin. (Equivalent to our rules file)
    * A study bidsmap. (Equivalent to our mappings file)

Refer to the `bidscoin documentation <https://bidscoin.readthedocs.io/en/stable/workflow.html>`_ to understand the components and workflow of bidscoin.

In summary, bidscoin uses a bidsmap to encode how a conversion is done.

Intuitively, the bidsmapper grabs a template to produce a study bidsmap, which may or may not be customized for each file through the bidseditor. Either way the final study bidsmap is passed to bidscoiner to perform the conversion.

The connection of sovabids and bidscoin is through a plugin called sova2coin which helps the bidscoin modules by dealing with the EEG data.

.. mermaid::

    graph LR
        S>"Source path"]
        B>"Bids path"]
        R>"Rules file"]
        O[("Converted dataset")]
        BM((bidsmapper))
        BC((bidscoiner))
        BE((bidseditor))
        BF>bidsmap template]
        SOVA((sova2coin)) --> BM
        B-->BM
        BM-->|bidsmap|BE
        BE-->|user-edited bidsmap|BC
        BC-->O
        R --> SOVA
        BF -->BM
        S --> BM
        SOVA-->BC


.. warning::

    To run this example you need to install our `bidscoin branch <>`_
    
    That is, you need to run:

    .. code-block:: bash

        pip install git+https://github.com/yjmantilla/bidscoin.git@sovabids

    If that doesn't work try:

    .. code-block:: bash
        git clone https://github.com/yjmantilla/bidscoin/tree/sovabids
        cd bidscoin
        pip install .
"""

#%%
# Imports
# ^^^^^^^
# First we import some functions we will need:

import os
from re import template # For path manipulation
import shutil # File manipulation
import yaml # To do yaml operations
from mne_bids import print_dir_tree # To show the input/output directories structures inside this example
from sovabids.utils import get_project_dir # Getting a directory to get the dataset files
from sovabids.datasets import lemon_bidscoin_prepare # Dataset
from sovabids.schemas import bidsmap_sova2coin # bidsmap template schema

#%%
# Setting up the paths
# ^^^^^^^^^^^^^^^^^^^^
# First, we will set up four paths. Because this example is intended to run relative 
# to the repository directory we use relative path but for real use-cases it is 
# easier to just input the absolute-path. We will print these paths for more clarity.

dataset = 'lemon_bidscoin' # Just folder name where to save or dataset
data_dir = os.path.join(get_project_dir(),'_data')
data_dir = os.path.abspath(data_dir)

source_path = os.path.abspath(os.path.join(data_dir,dataset+'_input'))
bids_root= os.path.abspath(os.path.join(data_dir,dataset+'_output'))
code_path = os.path.join(bids_root,'code','bidscoin')
rules_path = os.path.join(code_path,'rules.yml')
template_path = os.path.join(code_path,'template.yml')
bidsmap_path  = os.path.join( code_path,'bidsmap.yaml')
print('source_path:',source_path)
print('bids_root:', bids_root)
print('rules_path:',rules_path)
print('template_path:',template_path)
print('bidsmap_path:',bidsmap_path)

#%%
# Cleaning the output directory
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# We will clean the output path as a safety measure from previous conversions.

try:
    shutil.rmtree(bids_root)
except:
    pass

#%%
#
# Make the folders if they don't exist to avoid errors
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
for p in [source_path,bids_root,code_path]:
    os.makedirs(p,exist_ok=True)

#%%
# Getting and preparing the dataset
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# We have to download and decompress the dataset. We also need to fix a filename inconsistency
# (without this correction the file won't be able to be opened in mne). Luckily all of that is 
# encapsulated in the lemon_prepare function since these issues are not properly of sovabids. 
# 
# We also need to prepare the data to the `bidscoin required source data structure <https://bidscoin.readthedocs.io/en/stable/preparation.html>`_
# We will save this input data to source_path .
lemon_bidscoin_prepare(source_path)


#%%
# The input directory
# ^^^^^^^^^^^^^^^^^^^
# For clarity purposes we will print here the directory we are trying to convert to BIDS.

print_dir_tree(source_path)

#%%
# Making the rules
# ^^^^^^^^^^^^^^^^
# See the Rules File Schema documentation for help regarding making this rules file.
# Here we will make the rules from a python dictionary.

rules ={
'entities':{'task':'resting'},
'dataset_description':{'Name':dataset},
'sidecar':{'PowerLineFrequency':50,'EEGReference':'FCz'},
'channels':{'type':{'VEOG':'VEOG'}},
'non-bids':{'path_analysis':{'pattern':'sub-%entities.subject%/ses-%entities.session%/%ignore%/%ignore%.vhdr'}}
}
with open(rules_path, 'w') as outfile:
    yaml.dump(rules, outfile, default_flow_style=False)

#%%
# Now print the rules to see how the yaml file we made from the python dictionary looks like
#
with open(rules_path,encoding="utf-8") as f:
    rules = f.read()
    print(rules)

#%%
# Making the bidsmap template
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^
# The template is equivalent to the "rules" file of sovabids. It encodes the general way of doing the conversion.
# Explaining this file is out of scope of this example (this is bidscoin territory).
# We will notice however that: 
#   * We input our rules file as an option to the sova2coin plugin.
#   * We are interested in a "EEG" dataformat with an "eeg" datatype.
#   * We match every file with a .* in the properties.filename section
#   * The attributes are basically the metadata information extracted from the files which may be used to derive bids-related information.
#   * In the attributes section we have the objects as they are named in our rules file schema (that is, here we deal with sovabids terminology using a dot notation for nesting)
#   * We populate bids-related info with the extracted attributes (see subject, session and bids sections of the file)
#   * We set the suffix to eeg.
#   * The ``<`` and ``<<`` is best explained `here <https://bidscoin.readthedocs.io/en/stable/bidsmap.html#special-bidsmap-features>`_
template = bidsmap_sova2coin.format(rules_path)

print(template)

with open(template_path,mode='w') as f:
    f.write(template)

#%%
# .. tip::
#       
#       You can also input the rules directly (ie writing the rules instead of the path to the rules file)
#       What is important is that inside the "rules" field of the sova2coin "options"
#
# .. note::
#       The EEG:eeg hierarchy just says that there is an 'EEG' dataformat which a general 'eeg' datatype. 
#       This is a bit redundant but it happens because bidscoin was originally thought for DICOM (dataformat) 
#       which holds many datatypes (anat,perf,etc). In eeg this doesnt happens.
#
# %%
# Some necessary code
# ^^^^^^^^^^^^^^^^^^^
# To be able to run commands from this notebook and capture their outputs we need to define the following, nevertheless this is not relevant to actually running this from the command line.

from subprocess import PIPE, run

def out(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result.stdout

my_output = out("echo hello world")
print(my_output)

#%%
# bidsmapper
# ^^^^^^^^^^
# First we execute the bidsmapper to get a study bidsmap from our bidsmap template.
# The bidsmap file is equivalent to our "mappings" file; it encodes how the conversion is done on a per-file basis.
# Lets see the help

command = "bidsmapper --help"
print(command)
#%%
# This will give the following output
#
my_output= out(command)
print(my_output)

#%%
# Now we will use the following command to get the bidsmap study file.
# Note we use -t to set the template and -a to run this without the bidseditor
# You can skip the -a option if you are able to open the bidseditor (ie you are able to give user-input in its interface)
# Just remember to save the bidsmap yaml at the end.
# See the `bidseditor documentation <https://bidscoin.readthedocs.io/en/stable/workflow.html#main-window>`_ for more info.
command = 'bidsmapper '+source_path + ' '+ bids_root + ' -t ' + template_path + ' -a'
print(command)

#%%
# This will produce the following study bidsmap:

my_output= out(command)
print(my_output)

with open(bidsmap_path,encoding="utf8", errors='ignore') as f:
    bidsmap= f.read()
    print(bidsmap)

#%%
# at the following path:

print(bidsmap_path)

#%%
# bidscoiner
# ^^^^^^^^^^
# Now we are ready to perform the conversion given the study bidsmap file just made.
# Use the following command to print the help of the tool:
#
command = "bidscoiner --help"
print(command)
#%%
# This will give the following output
#
my_output= out(command)
print(my_output)

#%%
# Now we will use the following command to perform the conversion.
#
command = 'bidscoiner '+source_path + ' '+ bids_root + ' -b '+ bidsmap_path

print(command)

#%%
# This will produce the following output:
my_output= out(command)
print(my_output)

#%%
# Checking the conversion
# ^^^^^^^^^^^^^^^^^^^^^^^
# For clarity purposes we will check the output directory we got from sovabids.

print_dir_tree(bids_root)

print('BIDSCOIN CONVERSION FINISHED!')



