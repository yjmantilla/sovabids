"""Module to perform the conversions.
"""
import argparse
import json
import os
import logging
from contextlib import suppress

from mne_bids import make_dataset_description
from sovabids.rules import load_rules,apply_rules_to_single_file
from sovabids.utils import update_dataset_description,setup_logging,START_DECORATOR

def convert_them(mappings_input):
    """Converts eeg files to bids according to the mapping given.

    Parameters
    ----------
    mappings_input : str
        The path to the mapping file or the mapping dictionary.
    """

 
    # Loading Mappings
    mappings = load_rules(mappings_input)
    mapping_file = mappings_input if isinstance(mappings_input,str) else 'not a mapping file'
    
    # Verifying Mappings
    assert 'Individual' in mappings
    assert 'General' in mappings
    
    # Getting input,output and log path
    bids_path = mappings['General']['IO']['target']
    rawfolder = mappings['General']['IO']['target']
    log_file = os.path.join(bids_path,'code','sovabids','sovaconvert.log')

    # Setup the logging
    LOGGER = setup_logging(log_file)
    LOGGER.info('')
    LOGGER.info(START_DECORATOR+ ' START CONVERT_THEM '+START_DECORATOR)
    LOGGER.info(f"source_path={rawfolder} targetfolder={bids_path} bidsmap={mapping_file} ")

    for mapping in mappings['Individual']:
        apply_rules_to_single_file(mapping['IO']['source'],mapping,bids_path,write=True,logger=LOGGER)
    
    # Grab the info from the last file to make the dataset description
    if 'dataset_description' in mappings['General']:
        dataset_description = mappings['General']['dataset_description']
        update_dataset_description(dataset_description,bids_path)


def sovaconvert():
    """Console script usage for conversion."""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('convert_them')
    parser.add_argument('mappings',help='The mapping file of the conversion.')
    args = parser.parse_args()
    convert_them(args.mappings)

if __name__ == "__main__":
    sovaconvert()
