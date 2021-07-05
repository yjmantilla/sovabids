  
"""
======================
LEMON dataset example
======================

This example illustrates the use of ``sovabids`` on the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_
using the python API.

The main elements of this example are:
    * A source path with the original dataset.
    * A bids path that will be the output path of the conversion.
    * A rules file that configures how the conversion is done.
    * A mapping file that encodes how the conversion is performed to each individual file of the dataset.

.. mermaid::

    graph LR
        S>"Source path"]
        B>"Bids path"]
        R>"Rules file"]
        AR(("Apply Rules"))
        M>"Mappings file"]
        CT(("Convert Them"))
        O[("Converted dataset")]
        S --> AR
        B --> AR
        R --> AR
        AR --> M
        M --> CT
        CT --> O
"""

#%%
# Imports
# -------
# First we import some functions we will need:

import os # For path manipulation
import shutil # File manipulation
from mne_bids import print_dir_tree # To show the input/output directories structures inside this example
from sovabids.utils import get_project_dir # Getting a directory to get the dataset files
from sovabids.rules import apply_rules # Apply rules for conversion
import yaml # Just to print the rules in the example
from sovabids.convert import convert_them # Do the conversion
from sovabids.datasets import lemon_prepare # Download the dataset

#%%
# Getting and preparing the dataset
# ---------------------------------
# We have to download and decompress the dataset. We also need to fix a filename inconsistency
# (without this correction the file won't be able to be opened in mne). Luckily all of that is 
# encapsulated in the lemon_prepare.py function since these issues are not properly of sovabids. 
# 
# By default the files are saved in the '_data' directory of the sovabids project.
lemon_prepare()

#%%
# Setting up the paths
# --------------------
# Now we will set up four paths. Because this example is intended to run relative 
# to the repository directory we use relative path but for real use-cases it is 
# easier to just input the absolute-path. We will print these paths for more clarity.

source_path = os.path.abspath(os.path.join(get_project_dir(),'_data','lemon')) # For the input data we will convert
bids_root= os.path.abspath(os.path.join(get_project_dir(),'_data','lemon_bids')) # The output directory that will have the converted data
rules_path = os.abspath(os.path.join(get_project_dir(),'examples','lemon_example_rules.yml')) # The rules file that setups the rule for conversion
mapping_path = os.abspath(os.path.join(bids_root,'code','sovabids','mappings.yml')) # The mapping file that will hold the results of applying the rules to each file

print('source_path:',source_path)
print('bids_root:', bids_root)
print('rules_path:',rules_path)
print('mapping_path:',mapping_path)

#%%
# Cleaning the output directory
# -----------------------------
# We will clean the output path as a safety measure from previous conversions.

try:
    shutil.rmtree(bids_root)
except:
    pass

#%%
# The input directory
# -------------------
# For clarity purposes we will print here the directory we are trying to convert to BIDS.

print_dir_tree(source_path)

#%%
# Making the rules
# ----------------
# The most important and complicated part of this is making the rules file, 
# either by hand or by the "DISCOVER_RULES" module (which is not yet implemented).
#
# To do it by hand we need to understand the schema of the file. For starts, 
# the file is written in yaml. As of now the purpose of this example is not to teach yaml 
# (we may have a dedicated file for that in the future). You can check this `link <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started>`_ though.
#
# sovabids works with setting up (the currently supported) parts of bids.
#
# The bids eeg specification setups mainly 6 files:
#    - dataset_description
#    - sidecar
#    - channels
#    - electrodes
#    - coordinate system
#    - events
#
# The currently supported files are: 
#    - dataset_description : https://bids-specification.readthedocs.io/en/stable/03-modality-agnostic-files.html#dataset_descriptionjson
#    - sidecar : https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html#sidecar-json-_eegjson
#    - channels : https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html#channels-description-_channelstsv
# 
# For each of these files, the yaml will have an object with its corresponding "child" properties.
#
# Besides these "file" objects, the yaml will have an "entities" object.
# Although it seems a bit obscure, "entities" is just the name bids gives to the properties that affect file name structure.
# More info at: https://bids-specification.readthedocs.io/en/stable/02-common-principles.html#file-name-structure
# In essence the "entities" object holds information that triangulates the file 
# in the study (subject,session,task,acquisition,run).
#
# At last, we have the "non-bids" object which setups additional configuration that do not clearly belong to one of the previous objects.
#
# This part is already done for you, but for clarification here are the rules 
# we are applying. Please read the following as the yaml documents itself.

with open(rules_path,encoding="utf-8") as f:
    rules = f.read()
    print(rules)

#%%
# Applying the rules
# ------------------
# We apply the rules to the input dataset by giving the input,ouput,rules, and mapping paths to the apply_rules function.
# This will produce by default a 'mappings.yml' file at the specified directory of 'bids_root/code/sovabids'.
# This file holds the result of applying the rules to each of the dataset files.
apply_rules(source_path,bids_root,rules_path,mapping_path)

#%%
# Doing the conversion
# --------------------
# We now do the conversion of the dataset by reading the mapping file ('mappings.yml') with the convert them module.
convert_them(mapping_path)

#%%
# Checking the conversion
# -----------------------
# For clarity purposes we will check the output directory we got from sovabids.

print_dir_tree(bids_root)

print('LEMON CONVERSION FINISHED!')

