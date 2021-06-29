import os
import mne_bids
import json
import yaml
import argparse
import pandas as pd

from sovabids.utils import create_dir, get_nulls,deep_merge_N,get_supported_extensions,get_files,macro, run_command,split_by_n,mne_open
from sovabids.parsers import parse_string_from_template
from mne_bids import BIDSPath, read_raw_bids, print_dir_tree, make_report,write_raw_bids
from copy import deepcopy


def get_info_from_path(path,rules_):
    rules = deepcopy(rules_)
    patterns_extracted = {}
    if 'splitter' in rules.get('non-bids',{}):
        splitter = rules['non-bids']['splitter']
    else:
        splitter = '%'

    if "path_pattern" in rules.get('non-bids',{}) and rules['non-bids']['path_pattern'] not in get_nulls():
        patterns_extracted = parse_string_from_template(path,rules['non-bids']['path_pattern'],splitter)
    if 'ignore' in patterns_extracted:
        del patterns_extracted['ignore']
    # this what needed because using rules.update(patterns_extracted) replaced it all
    rules = deep_merge_N([rules,patterns_extracted])
    return rules

def load_rules(rules_):
    if not isinstance(rules_,dict):
        with open(rules_,encoding="utf-8") as f:
            return yaml.load(f,yaml.FullLoader)
    return rules_

def apply_rules_to_single_file(f,rules_,bids_root):
    rules = deepcopy(rules_) #otherwise the deepmerge wont update the values for a new file

    # Upon reading RAW MNE makes the assumptions
    raw = mne_open(f)

    # First get info from path

    rules = get_info_from_path(f,rules)

    # Apply Rules
    assert 'entities' in rules
    entities = rules['entities'] # this key has the same fields as BIDSPath constructor argument

    if 'sidecar' in rules:
        sidecar = rules['sidecar']
        if "PowerLineFrequency" in sidecar and sidecar['PowerLineFrequency'] not in get_nulls():
            raw.info['line_freq'] = sidecar["PowerLineFrequency"]  # specify power line frequency as required by BIDS
        # Should we try to infer the line frequency automatically from the psd?

    if 'channels' in rules:
        channels = rules['channels']
        if "name" in channels:
            raw.rename_channels(channels['name'])

    if 'non-bids' in rules:
        non_bids = rules['non-bids']
        if "code_execution" in non_bids:
            if isinstance(non_bids["code_execution"],str):
                non_bids["code_execution"] = [non_bids["code_execution"]]
            if isinstance(non_bids["code_execution"],list):
                for command in non_bids["code_execution"]:
                    exec(macro)
                    #raw = run_command(raw,command) #another way...
                    # maybe log errors here?


        bids_path = BIDSPath(**entities,root=bids_root)
        write_raw_bids(raw, bids_path=bids_path,overwrite=True)
        rules['IO']={}
        rules['IO']['target'] = bids_path.fpath.__str__()
        rules['IO']['source'] = f

        # POST-PROCESSING. For stuff easier to overwrite in the files rather than in the raw object
        # Rules that need to be applied to the result of mne-bids
        # Or maybe we should add the functionality directly to mne-bids

        if 'sidecar' in rules:
            sidecar_path = bids_path.copy().update(datatype='eeg',suffix='eeg', extension='.json')
            with open(sidecar_path.fpath) as f:
                dummy_dict = json.load(f)
                sidecar = rules['sidecar']
                #TODO Validate the sidecar rules so as not to include dangerous stuff??
                dummy_dict.update(sidecar)
                # maybe include an overwrite rule
                mne_bids.utils._write_json(sidecar_path.fpath,dummy_dict,overwrite=True)

        if 'channels' in rules:
            channels_path = bids_path.copy().update(datatype='eeg',suffix='channels', extension='.tsv')
            channels_table = pd.read_csv (channels_path.fpath, sep = '\t',dtype=str,keep_default_na=False,na_filter=False,na_values=[],true_values=[],false_values=[])
            channels_rules = rules['channels']
            if 'type' in channels_rules: # types are post since they are not saved in vhdr (are they in edf??)
                for ch_name,ch_type in channels_rules['type'].items():
                    channels_table.loc[(channels_table.name==str(ch_name)),'type'] = ch_type
            channels_table.to_csv(channels_path.fpath, index=False,sep='\t')
    #TODO remove general information of the dataset from the INDIVIDUAL FILES (ie dataset_description stuff)
    return rules
def apply_rules(source_path,bids_root,rules_):

    rules_ = load_rules(rules_)
    # Generate all files
    try:
        extensions = rules_['non-bids']['eeg_extension']
    except:
        extensions = get_supported_extensions()

    if isinstance(extensions,str):
        extensions = [extensions]

    # append dot to extensions if missing
    extensions = [x if x[0]=='.' else '.'+x for x in extensions]

    filepaths = get_files(source_path)
    filepaths = [x for x in filepaths if os.path.splitext(x)[1] in extensions]

    #%% BIDS CONVERSION
    all_mappings = []
    for f in filepaths:
        rules = apply_rules_to_single_file(f,rules_,bids_root)
        all_mappings.append(rules)
    # Grab the info from the last file to make the dataset description
    if 'dataset_description' in rules:
        dataset_description = rules['dataset_description']
        if 'Name' in dataset_description:
            # Renaming for mne_bids.make_dataset_description support
            dataset_description['name'] = dataset_description.pop('Name')
        if 'Authors' in dataset_description:
            dataset_description['authors'] = dataset_description.pop('Authors')

        mne_bids.make_dataset_description(bids_root,**dataset_description,overwrite=True)
        # Problem: Authors with strange characters are written incorrectly.
    outputname = 'file_mappings.yml'
    outputfolder = os.path.join(bids_root,'code','sovabids')
    create_dir(outputfolder)
    full_rules_path = os.path.join(outputfolder,outputname)
    mapping_data = {'General_Rules':rules_,'Individual_Mappings':all_mappings}
    with open(full_rules_path, 'w') as outfile:
        yaml.dump(mapping_data, outfile, default_flow_style=False)
    return mapping_data

def main():
    """Console script usage"""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('apply_rules')
    parser.add_argument('source_path')  # add the name argument
    parser.add_argument('bids_root')  # add the name argument
    parser.add_argument('rules')  # add the name argument
    args = parser.parse_args()
    apply_rules(args.source_path,args.bids_root,args.rules)

if __name__ == "__main__":
    main()