"""Module to perform the conversions.
"""
import argparse
import os

import logging
from sovabids.dicts import deep_get
from sovabids.rules import load_rules,apply_rules_to_single_file
from sovabids.bids import update_dataset_description
from sovabids.loggers import setup_logging
from sovabids.settings import SECTION_STRING

LOGGER = logging.getLogger(__name__)

def convert_them(mappings_input):
    """Convert eeg files to bids according to the mappings given.

    Parameters
    ----------
    mappings_input : str|dict
        The path to the mapping file or the mapping dictionary:
            {
                'General': dict with the general rules,
                'Individual':  list of dicts with the individual mappings of each file.
            }
    
    Returns
    -------
    None
    """

    # Loading Mappings
    mappings = load_rules(mappings_input)
    mapping_file = mappings_input if isinstance(mappings_input,str) else None
    
    # Verifying Mappings
    assert 'Individual' in mappings,f'`Individual` does not exist in the mapping dictionary'
    assert 'General' in mappings,f'`General` does not exist in the mapping dictionary'
    
    # Getting input,output and log path
    bids_path = mappings['General']['IO']['target']
    source_path = mappings['General']['IO']['target']
    log_file = os.path.join(bids_path,'code','sovabids','sovabids.log')

    # Setup the logging
    setup_logging(log_file)
    LOGGER.info('')
    LOGGER.info(SECTION_STRING + ' START CONVERT_THEM ' + SECTION_STRING)
    LOGGER.info(f"source_path={source_path} bids_path={bids_path} mapping_file={str(mapping_file)} ")

    LOGGER.info(f"Converting Individual Mappings")
    num_files = len(mappings['Individual'])
    for i,mapping in enumerate(mappings['Individual']):
        input_file=deep_get(mapping,'IO.source',None)
        try:

            LOGGER.info(f"File {i+1} of {num_files} ({(i+1)*100/num_files}%) : {input_file}")

            apply_rules_to_single_file(input_file,mapping,bids_path,write=True)
        except TheError:
            LOGGER.exception(f'Error for {input_file}')

    LOGGER.info(f"Conversion Done!")

    LOGGER.info(f"Updating Dataset Description")

    # Grab the info from the last file to make the dataset description
    if 'dataset_description' in mappings['General']:
        dataset_description = mappings['General']['dataset_description']
        update_dataset_description(dataset_description,bids_path)

    LOGGER.info(f"Dataset Description Updated!")

    LOGGER.info(SECTION_STRING + ' END CONVERT_THEM ' + SECTION_STRING)


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
