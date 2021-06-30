from sovabids.rules import load_rules,apply_rules_to_single_file
import mne_bids
import argparse
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
        if 'Name' in dataset_description:
            # Renaming for mne_bids.make_dataset_description support
            dataset_description['name'] = dataset_description.pop('Name')
        if 'Authors' in dataset_description:
            dataset_description['authors'] = dataset_description.pop('Authors')
        mne_bids.make_dataset_description(bids_root,**dataset_description,overwrite=True)
        # Problem: Authors with strange characters are written incorrectly.



def sovaconvert():
    """Console script usage"""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('convert_them')
    parser.add_argument('mappings')
    args = parser.parse_args()
    convert_them(args.mappings)

if __name__ == "__main__":
    sovaconvert()
