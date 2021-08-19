
"""
========================================
RPC API example with the LEMON dataset
========================================

This example illustrates the use of ``sovabids`` on the `LEMON dataset <http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html>`_
using the RPC API.

.. warning::
    To run this example, you need to install sovabids in 'advanced-usage' mode ( `see here <https://sovabids.readthedocs.io/en/latest/README.html#installation-for-advanced-usage>`_ ).

"""

#%%
# Sovabids uses an action-oriented API. Here we will illustrate each of the available functionalities.
#
# Imports
# -------
# First we import some functions we will need:


import os # For path manipulation
import shutil # File manipulation
from mne_bids import print_dir_tree # To show the input/output directories structures inside this example
from sovabids.datasets import lemon_prepare # Download the dataset
from sovabids.settings import REPO_PATH
from sovabids.sovarpc import app as sovapp # The RPC API application
import sovabids.sovarpc as sovarpc
from fastapi.testclient import TestClient # This will be for simulating ourselves as a client of the RPC API
import json # for making json-based requests
import copy # just to make deep copies of variables

#%%
# Getting and preparing the dataset
# ---------------------------------
# We have to download and decompress the dataset. We also need to fix a filename inconsistency
# (without this correction the file won't be able to be opened in mne). Luckily all of that is 
# encapsulated in the lemon_prepare function since these issues are not properly of sovabids. 
# 
# By default the files are saved in the '_data' directory of the sovabids project.
lemon_prepare()

#%%
# Setting up the paths
# --------------------
# Now we will set up four paths. Because this example is intended to run relative 
# to the repository directory we use relative path but for real use-cases it is 
# easier to just input the absolute-path. We will print these paths for more clarity.

source_path = os.path.abspath(os.path.join(REPO_PATH,'_data','lemon')) # For the input data we will convert
bids_path= os.path.abspath(os.path.join(REPO_PATH,'_data','lemon_bids_rpc')) # The output directory that will have the converted data
rules_path = os.path.abspath(os.path.join(REPO_PATH,'examples','lemon_example_rules.yml')) # The rules file that setups the rule for conversion
mapping_path = os.path.abspath(os.path.join(bids_path,'code','sovabids','mappings.yml')) # The mapping file that will hold the results of applying the rules to each file

print('source_path:',source_path.replace(REPO_PATH,''))
print('bids_path:', bids_path.replace(REPO_PATH,''))
print('rules_path:',rules_path.replace(REPO_PATH,''))
print('mapping_path:',mapping_path.replace(REPO_PATH,''))

#%%
# Cleaning the output directory
# -----------------------------
# We will clean the output path as a safety measure from previous conversions.

try:
    shutil.rmtree(bids_path)
except:
    pass

#%%
# The input directory
# -------------------
# For clarity purposes we will print here the directory we are trying to convert to BIDS.

print_dir_tree(source_path)



#%%
# RPC API
# -------
# Simulating ourselves as clients
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# We will use the TestClient class to send requests to the API (the sovapp variable)

client = TestClient(sovapp)

#%%
# The general request
# ^^^^^^^^^^^^^^^^^^^
# We will define a function to make a request to the API
# given the name of the method and its parameters as a dictionary

def make_request(method,params):
    print('Method:',method)
    print('');print('');
    print('Parameters:')
    print(json.dumps(params, indent=4))
    print('');print('');
    # We create the complete request
    request= { 
    "jsonrpc": "2.0",
    "id": 0,
    "method": method,
    "params": params}
    print('Request:')
    print(json.dumps(request, indent=4))
    print('');print('');
   # json dumps is important to avoid parsing errors in the API request
    request = json.dumps(request)

    # Send the request
    request_url = "/api/sovabids/" +method
    print('Request URL:')
    print(request_url)
    print('');print('');
    response = client.post(request_url,data=request ) # POST request as common in RPC-based APIs

    # Get the answer
    result = json.loads(response.content.decode())['result']
    print('Answer:')
    print(json.dumps(result, indent=4))
    print('');print('');
    return result

#%%
# load_rules
# ^^^^^^^^^^
# For loading a yaml rules file.
# Lets see the docstring of this method

print(sovarpc.load_rules.__doc__)

#%%
# Lets define the request

method = 'load_rules' # Just a variable for the method name 

params = {                  # Parameters of the method
"rules_path": rules_path
    }

#%%
# And proceed with it

result = make_request(method,params)

rules = copy.deepcopy(result)

#%%
# save_rules
# ^^^^^^^^^^
# We can for example use it as a way to save a backup of the already-existing rules file.
# Lets see the docstring of this method
print(sovarpc.save_rules.__doc__)

#%%
# Lets define the request
method = "save_rules" # Just a variable for the method name 

params = {                  # Parameters of the method
    "rules": rules,
    "path": mapping_path.replace('mappings','rules')+'.bkp' # We will do it as if we were saving a backup of the rules
                              # Since the rules file already exists
    }

#%%
# And proceed with it
result = make_request(method,params)

#%%
# get_files
# ^^^^^^^^^
# Useful for getting the files on a directory.
# Lets see the docstring of this method
print(sovarpc.get_files.__doc__)

#%%
# .. note::
#     
#     get_files uses the rules because of the non-bids.eeg_extension configuration.


#%%
# Lets define the request
method = "get_files" # Just a variable for the method name 

params = {                  # Parameters of the method
            "rules": rules,
            "path": source_path
    }

#%%
# And proceed with it
result = make_request(method,params)

filelist = copy.deepcopy(result)

#%%
# apply_rules_to_single_file
# ^^^^^^^^^^^^^^^^^^^^^^^^^^
# We can use this to get a mapping for a single mapping 
# and for previewing the bids files that would be written.
# Lets see the docstring of this method
print(sovarpc.apply_rules_to_single_file.__doc__)

#%%
# Lets define the request
method = "apply_rules_to_single_file" # Just a variable for the method name 

params = {                  # Parameters of the method
        "file": filelist[0],
        "bids_path": bids_path+'.preview',
        "rules": rules,
        "write":False,
        "preview":True
    }

#%%
# And proceed with it
result = make_request(method,params)


#%%
# apply_rules
# ^^^^^^^^^^^
# We can use this to get the mappings for all the files in a list of them.
# Lets see the docstring of this method
print(sovarpc.apply_rules.__doc__)

#%%
# Lets define the request
method = "apply_rules" # Just a variable for the method name 

params = {                  # Parameters of the method
        "file_list": filelist,
        "bids_path": bids_path,
        "rules": rules,
        "mapping_path":mapping_path
    }

#%%
# And proceed with it
result = make_request(method,params)

file_mappings=copy.deepcopy(result)

#%%
# save_mappings
# ^^^^^^^^^^^^^
# We can use this to save a backup of the mappings.
# Lets see the docstring of this method
print(sovarpc.save_mappings.__doc__)

#%%
# Lets define the request
method = "save_mappings" # Just a variable for the method name 

params = {                  # Parameters of the method
    "general": file_mappings['General'],
    "individual":file_mappings['Individual'],
    "path": mapping_path+'.bkp'
    }

#%%
# And proceed with it
result = make_request(method,params)

#%%
# convert_them
# ^^^^^^^^^^^^
# We can use this to perform the conversion given the mappings.
# Lets see the docstring of this method
print(sovarpc.convert_them.__doc__)

#%%
# Lets define the request
method = "convert_them" # Just a variable for the method name 

params = {                  # Parameters of the method
    "general": file_mappings['General'],
    "individual":file_mappings['Individual']
    }

#%%
# And proceed with it
result = make_request(method,params)


#%%
# Checking the conversion
# -----------------------
# For clarity purposes we will check the output directory we got from sovabids.

print_dir_tree(bids_path)

print('LEMON CONVERSION FINISHED!')