import argparse
import json
import os
from mne_bids import make_dataset_description
from sovabids.rules import load_rules,apply_rules_to_single_file
from sovabids.utils import update_dataset_description

def convert_them(mappings_input):
    rules = load_rules(mappings_input)
    assert 'Individual' in rules
    assert 'General' in rules
    bids_root = rules['General']['IO']['target']
    for mapping in rules['Individual']:
        apply_rules_to_single_file(mapping['IO']['source'],mapping,bids_root,write=True)
    
    # Grab the info from the last file to make the dataset description
    if 'dataset_description' in rules['General']:
        dataset_description = rules['General']['dataset_description']
        update_dataset_description(dataset_description,bids_root)


def sovaconvert():
    """Console script usage"""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('convert_them')
    parser.add_argument('mappings',help='The mapping file of the conversion.')
    args = parser.parse_args()
    convert_them(args.mappings)

if __name__ == "__main__":
    sovaconvert()
