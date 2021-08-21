"""
===================================
Usage example of source,target pair
===================================

This example illustrates how does the inference of the path_pattern from a (source,target) pair example works.

The main elements of this example are:
    * A source example path of one of your files
    * A target path that will be the expected mapping of your file.
    * The from_io_example heuristic that internally does the inference work.
    * A path pattern inferred from the above.


Be sure to read `the Rules File Schema documentation section relating to the Paired Example <https://sovabids.readthedocs.io/en/latest/rules_schema.html#paired-example>`_ before doing this example for more context.


.. mermaid::

    graph LR
        S>"source path example"]
        B>"target path example"]
        AR(("from_io_example"))
        M>"path pattern"]
        S --> AR
        B --> AR
        AR --> M

The Rules File
--------------
The Rules File we are dealing here has the following path_analysis rule

"""

import json # utility
from sovabids.files import _write_yaml # To print the yaml file

# The rule we are dealing with
rule = {
    'non-bids':{
        'path_analysis':
            {
            'source' : 'data/lemon/V001/resting/010002.vhdr',
            'target' : 'data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr'
            }
        }
    }

yaml_file = _write_yaml(rule)

print('Rules File:\n\n',yaml_file)

#%%
# The from_io_example function
# -----------------------------
#
# Although this is hidden from the user, internally sovabids uses this function to infer the pattern.
#
# The name of the function means "from input-output example", as one provides an input and output pair of (source,target) paths.
# 
# Here we will illustrate how this function behaves. Lets see the documentation of the function:
#

from sovabids.heuristics import from_io_example # The function itself

print('from_io_example:\n\n',from_io_example.__doc__)

#%%
# The result of the function
# -----------------------------
#
# The function will return the placeholder pattern as explained in `the Rules File Schema documentation section relating to the Placeholder Pattern <https://sovabids.readthedocs.io/en/latest/rules_schema.html#placeholder-pattern>`_ .
# 
#
sourcepath = rule['non-bids']['path_analysis']['source']
targetpath = rule['non-bids']['path_analysis']['target']
result = from_io_example(sourcepath,targetpath)

print('Result:\n\n',result)


#%%
# Ambiguity
# ----------
#
# This is explained in more detail in `the warning section of the the Paired Example documentation <https://sovabids.readthedocs.io/en/latest/rules_schema.html#paired-example>`_ .
# Be sure to read it before for fully understading what ambiguity means here.
#
# An ambiguous rule would be:
#

rule = {
    'non-bids':{
        'path_analysis':
            {
            'source':'data/lemon/session001/taskT001/010002.vhdr',
            'target':'data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-T001_eeg.vhdr'
            }
        }
    }

yaml_file = _write_yaml(rule)

print('Ambiguous Example:\n\n',yaml_file)

#%%
# If your example is ambiguous, the function will raise an error.
#
# Notice the last bit of the message, it will hint you about what part of the example is suspected to have ambiguity.
#
from traceback import format_exc

try:
    sourcepath = rule['non-bids']['path_analysis']['source']
    targetpath = rule['non-bids']['path_analysis']['target']
    result = from_io_example(sourcepath,targetpath)
except:
    print('Error:\n\n',format_exc())
