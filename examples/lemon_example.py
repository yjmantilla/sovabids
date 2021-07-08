  
"""
======================
LEMON dataset example
======================

This example illustrates the use of ``sovabids`` on the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_
using both the python API and the CLI tool.

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
# Using the python API
# --------------------
# First we will illustrate how to run the software within python.
#
# Imports
# ^^^^^^^
# First we import some functions we will need:

import os # For path manipulation
import shutil # File manipulation
from mne_bids import print_dir_tree # To show the input/output directories structures inside this example
from sovabids.utils import get_project_dir # Getting a directory to get the dataset files
from sovabids.rules import apply_rules # Apply rules for conversion
from sovabids.convert import convert_them # Do the conversion
from sovabids.datasets import lemon_prepare # Download the dataset

#%%
# Getting and preparing the dataset
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# We have to download and decompress the dataset. We also need to fix a filename inconsistency
# (without this correction the file won't be able to be opened in mne). Luckily all of that is 
# encapsulated in the lemon_prepare function since these issues are not properly of sovabids. 
# 
# By default the files are saved in the '_data' directory of the sovabids project.
lemon_prepare()

#%%
# Setting up the paths
# ^^^^^^^^^^^^^^^^^^^^
# Now we will set up four paths. Because this example is intended to run relative 
# to the repository directory we use relative path but for real use-cases it is 
# easier to just input the absolute-path. We will print these paths for more clarity.

source_path = os.path.abspath(os.path.join(get_project_dir(),'_data','lemon')) # For the input data we will convert
bids_root= os.path.abspath(os.path.join(get_project_dir(),'_data','lemon_bids')) # The output directory that will have the converted data
rules_path = os.path.abspath(os.path.join(get_project_dir(),'examples','lemon_example_rules.yml')) # The rules file that setups the rule for conversion
mapping_path = os.path.abspath(os.path.join(bids_root,'code','sovabids','mappings.yml')) # The mapping file that will hold the results of applying the rules to each file

print('source_path:',source_path)
print('bids_root:', bids_root)
print('rules_path:',rules_path)
print('mapping_path:',mapping_path)

#%%
# Cleaning the output directory
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# We will clean the output path as a safety measure from previous conversions.

try:
    shutil.rmtree(bids_root)
except:
    pass

#%%
# The input directory
# ^^^^^^^^^^^^^^^^^^^
# For clarity purposes we will print here the directory we are trying to convert to BIDS.

print_dir_tree(source_path)

#%%
# Making the rules
# ^^^^^^^^^^^^^^^^
# The most important and complicated part of this is making the rules file, 
# either by hand or by the "DISCOVER_RULES" module (which is not yet implemented).
#
# This part is already done for you, but for clarification here are the rules 
# we are applying. Please read the following output as the yaml has some basic 
# documentation comments.
#
# See the Rules File Schema documentation for help regarding making this rules file.
#
with open(rules_path,encoding="utf-8") as f:
    rules = f.read()
    print(rules)

#%%
# Applying the rules
# ^^^^^^^^^^^^^^^^^^
# We apply the rules to the input dataset by giving the input,ouput,rules, and mapping paths to the apply_rules function.
#
# This will produce by default a 'mappings.yml' file at the specified directory of 'bids_root/code/sovabids'.
#
# This file holds the result of applying the rules to each of the dataset files.
apply_rules(source_path,bids_root,rules_path,mapping_path)

#%%
# Doing the conversion
# ^^^^^^^^^^^^^^^^^^^^
# We now do the conversion of the dataset by reading the mapping file ('mappings.yml') with the convert them module.
convert_them(mapping_path)

#%%
# Checking the conversion
# ^^^^^^^^^^^^^^^^^^^^^^^
# For clarity purposes we will check the output directory we got from sovabids.

print_dir_tree(bids_root)

print('LEMON CONVERSION FINISHED!')

#%%
# Using the CLI tool
# ------------------
#
# sovabids can also be used through the command line. Here we provide an example of how to do so.
#
#
# The overview of what we are doing is now:
#
# .. mermaid::
#
#     graph LR
#         S>"Source path"]
#         B>"Bids path"]
#         R>"Rules file"]
#         AR(("sovapply"))
#         M>"Mappings file"]
#         CT(("sovaconvert"))
#         O[("Converted dataset")]
#         S --> AR
#         B --> AR
#         R --> AR
#         AR --> M
#         M --> CT
#         CT --> O

#%%
# Same old blues
# ^^^^^^^^^^^^^^
# Notice that we will run this inside of python so that the example can be run without needing configuration.
#
# To run this locally you will need to run lemon_prepare() function from the command line. You can do so by running:
# .. code-block:: bash
#
#    python -c "from sovabids.datasets import lemon_prepare; lemon_prepare()"
#
# Since we already have run lemon_prepare() inside this example, we will start from this step.
#
# We set up the paths again, but now we will change the output to a new path (with "_cli" at the end). We will also clean this path as we did before.
#
source_path = os.path.abspath(os.path.join(get_project_dir(),'_data','lemon')) # For the input data we will convert
bids_root= os.path.abspath(os.path.join(get_project_dir(),'_data','lemon_bids_cli')) # The output directory that will have the converted data
rules_path = os.path.abspath(os.path.join(get_project_dir(),'examples','lemon_example_rules.yml')) # The rules file that setups the rule for conversion
mapping_path = os.path.abspath(os.path.join(bids_root,'code','sovabids','mappings.yml')) # The mapping file that will hold the results of applying the rules to each file

print('source_path:',source_path)
print('bids_root:', bids_root)
print('rules_path:',rules_path)
print('mapping_path:',mapping_path)

try:
    shutil.rmtree(bids_root)
except:
    pass

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
# sovapply
# ^^^^^^^^
# In this example we have already made the rules. So we will apply them using the sovapply tool.
#
# Use the following command to print the help of the tool:
#
command = "sovapply --help"
print(command)
#%%
# This will give the following output
#
my_output= out(command)
print(my_output)

#%%
# Now we will use the following command to get the mappings file.
#
command = 'sovapply '+source_path + ' '+ bids_root + ' ' + rules_path + ' -m ' + mapping_path
print(command)

#%%
# This will produce the following output:
my_output= out(command)
print(my_output)

#%%
# sovaconvert
# ^^^^^^^^^^^
# Now we are ready to perform the conversion given the mapping file just made.
#
# Use the following command to print the help of the tool:
#
command = "sovaconvert --help"
print(command)
#%%
# This will give the following output
#
my_output= out(command)
print(my_output)

#%%
# Now we will use the following command to perform the conversion.
#
command = 'sovaconvert ' + mapping_path
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

print('LEMON CLI CONVERSION FINISHED!')



