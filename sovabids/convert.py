"""Module to perform the conversions.
"""
import argparse
import os
import sys

import logging
from sovabids.dicts import deep_get
from sovabids.rules import load_rules,apply_rules_to_single_file,_expand_path
from sovabids.bids import update_dataset_description
from sovabids.loggers import setup_logging
from sovabids.settings import SECTION_STRING

LOGGER = logging.getLogger(__name__)

def convert_them(mappings_input):
    """Convert eeg files to bids according to the mappings given.

    Parameters
    ----------
    mappings_input : str | pathlib.Path | dict
        The path to the mapping file or the mapping dictionary:
            {
                'General': dict with the general rules,
                'Individual':  list of dicts with the individual mappings of each file.
            }
    
    Returns
    -------
    dict
        ``{'succeeded': [str, ...], 'skipped': [str, ...], 'failed': [str, ...]}`` —
        source paths of files that were newly converted, skipped because their BIDS
        output already existed, and those that raised an error.
    """

    if isinstance(mappings_input, os.PathLike):
        mappings_input = os.fspath(mappings_input)
    # Loading Mappings
    mappings = load_rules(mappings_input)
    mapping_file = mappings_input if isinstance(mappings_input,str) else None
    
    # Verifying Mappings
    assert 'Individual' in mappings,f'`Individual` does not exist in the mapping dictionary'
    assert 'General' in mappings,f'`General` does not exist in the mapping dictionary'
    
    # Getting input,output and log path (expand ~ / $VARS so a path from the
    # mappings YAML isn't used literally, e.g. creating a "$HOME" directory) (#94)
    bids_path = _expand_path(mappings['General']['IO']['target'])
    source_path = _expand_path(mappings['General']['IO']['source'])
    log_file = os.path.join(bids_path,'code','sovabids','sovabids.log')

    # Setup the logging
    setup_logging(log_file)
    LOGGER.info('')
    LOGGER.info(SECTION_STRING + ' START CONVERT_THEM ' + SECTION_STRING)
    LOGGER.info(f"source_path={source_path} bids_path={bids_path} mapping_file={str(mapping_file)} ")

    LOGGER.info(f"Converting Individual Mappings")
    num_files = len(mappings['Individual'])
    succeeded = []
    skipped = []
    failed = []
    for i,mapping in enumerate(mappings['Individual']):
        input_file=_expand_path(deep_get(mapping,'IO.source',None))
        output_file=_expand_path(deep_get(mapping,'IO.target',None))
        try:
            LOGGER.info(f"File {i+1} of {num_files} ({(i+1)*100/num_files}%) : {input_file}")
            if not os.path.isfile(output_file):
                apply_rules_to_single_file(input_file,mapping,bids_path,write=True)
                succeeded.append(input_file)
            else:
                LOGGER.warning(f'SKIPPED (already converted): {input_file}')
                skipped.append(input_file)
        except Exception:
            LOGGER.exception(f'Error converting {input_file}')
            failed.append(input_file)

    LOGGER.info(
        f"Conversion Done! {len(succeeded)} converted, "
        f"{len(skipped)} skipped, {len(failed)} failed "
        f"(total {num_files})."
    )
    if skipped:
        LOGGER.warning(f"{len(skipped)} file(s) skipped (output already exists — delete to re-convert).")
    if failed:
        LOGGER.warning(f"{len(failed)} file(s) failed conversion:")
        for f in failed:
            LOGGER.warning(f"  FAILED: {f}")

    LOGGER.info(f"Updating Dataset Description")

    # Grab the info from the last file to make the dataset description
    if 'dataset_description' in mappings['General']:
        dataset_description = mappings['General']['dataset_description']
        update_dataset_description(dataset_description,bids_path)

    LOGGER.info(f"Dataset Description Updated!")

    LOGGER.info(SECTION_STRING + ' END CONVERT_THEM ' + SECTION_STRING)

    return {'succeeded': succeeded, 'skipped': skipped, 'failed': failed}


def sovaconvert():
    """Console script usage for conversion."""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    logging.basicConfig(format="%(message)s")
    LOGGER.setLevel(logging.WARN)

    from sovabids.misc import handle_unicode_dashes
    handle_unicode_dashes()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('convert_them')
    parser.add_argument('mappings',help='The mapping file of the conversion.')
    parser.add_argument('-v','--verbose', action="store_true", help='Make the output more verbose.')
    args = parser.parse_args()

    if args.verbose:
        LOGGER.setLevel(logging.INFO)

    result = convert_them(args.mappings)
    if result['failed']:
        sys.exit(1)

if __name__ == "__main__":
    sovaconvert()
