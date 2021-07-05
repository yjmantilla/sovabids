import os
import json
import yaml
import argparse

from copy import deepcopy
from mne_bids import write_raw_bids,BIDSPath
from mne_bids.utils import _handle_datatype,_write_json
from mne_bids.path import _parse_ext
from pandas import read_csv
from traceback import format_exc

from sovabids.utils import get_nulls,deep_merge_N,get_supported_extensions,get_files,mne_open
from sovabids.parsers import parse_from_regex,parse_from_placeholder

def get_info_from_path(path,rules_):
    """
    Two ways to parse:

    Through regex:
        pattern: REQUIRED
        fields: REQUIRED
    We know it is regex because fields are given, if not it is custom notation.

    Through custom notation:
        pattern: REQUIRED
        encloser: OPTIONAL %
        matcher: OPTIONAL, (.+)
    """
    rules = deepcopy(rules_)
    patterns_extracted = {}
    non_bids_rules = rules.get('non-bids',{})
    if 'path_analysis' in non_bids_rules:
        path_analysis = non_bids_rules['path_analysis']
        pattern = path_analysis.get('pattern','')
        # Check if regex
        if 'fields' in path_analysis:
            patterns_extracted = parse_from_regex(path,pattern,path_analysis.get('fields',[]))
        else: # custom notation
            encloser = path_analysis.get('encloser','%')
            matcher = path_analysis.get('matcher','(.+)')
            patterns_extracted = parse_from_placeholder(path,pattern,encloser,matcher)
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

def apply_rules_to_single_file(f,rules_,bids_root,write=False):
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
                    try:
                        exec(command)
                    except:
                        error_string = 'There was an error with the follwing command:\n'+command+'\ngiving the following traceback:\n'+format_exc()
                        print(error_string)
                        #maybe log errors here?
                        #or should we raise an exception?


        bids_path = BIDSPath(**entities,root=bids_root)
        if write:
            write_raw_bids(raw, bids_path=bids_path,overwrite=True)
        else:
            # These lines are taken from mne_bids.write
            raw_fname = raw.filenames[0]
            if '.ds' in os.path.dirname(raw.filenames[0]):
                raw_fname = os.path.dirname(raw.filenames[0])
            # point to file containing header info for multifile systems
            raw_fname = raw_fname.replace('.eeg', '.vhdr')
            raw_fname = raw_fname.replace('.fdt', '.set')
            raw_fname = raw_fname.replace('.dat', '.lay')
            _, ext = _parse_ext(raw_fname)

            datatype = _handle_datatype(raw)
            bids_path = bids_path.copy()
            bids_path = bids_path.update(
                datatype=datatype, suffix=datatype, extension=ext)

        rules['IO']={}
        rules['IO']['target'] = bids_path.fpath.__str__()
        rules['IO']['source'] = f

        # POST-PROCESSING. For stuff easier to overwrite in the files rather than in the raw object
        # Rules that need to be applied to the result of mne-bids
        # Or maybe we should add the functionality directly to mne-bids
        if write:
            if 'sidecar' in rules:
                sidecar_path = bids_path.copy().update(datatype='eeg',suffix='eeg', extension='.json')
                with open(sidecar_path.fpath) as f:
                    dummy_dict = json.load(f)
                    sidecar = rules['sidecar']
                    #TODO Validate the sidecar rules so as not to include dangerous stuff??
                    dummy_dict.update(sidecar)
                    # maybe include an overwrite rule
                    _write_json(sidecar_path.fpath,dummy_dict,overwrite=True)

            if 'channels' in rules:
                channels_path = bids_path.copy().update(datatype='eeg',suffix='channels', extension='.tsv')
                channels_table = read_csv (channels_path.fpath, sep = '\t',dtype=str,keep_default_na=False,na_filter=False,na_values=[],true_values=[],false_values=[])
                channels_rules = rules['channels']
                if 'type' in channels_rules: # types are post since they are not saved in vhdr (are they in edf??)
                    for ch_name,ch_type in channels_rules['type'].items():
                        channels_table.loc[(channels_table.name==str(ch_name)),'type'] = ch_type
                channels_table.to_csv(channels_path.fpath, index=False,sep='\t')
    #TODO remove general information of the dataset from the INDIVIDUAL MAPPINGS (ie dataset_description stuff)
    return rules
def apply_rules(source_path,bids_root,rules_,mapping_path=''):

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
        rules = apply_rules_to_single_file(f,rules_,bids_root,write=False) #TODO There should be a way to control how verbose this is
        all_mappings.append(rules)
    
    outputfolder,outputname = os.path.split(mapping_path)
    if outputname == '':
        outputname = 'mappings.yml'
    if outputfolder == '':
        outputfolder = os.path.join(bids_root,'code','sovabids')
    os.makedirs(outputfolder,exist_ok=True)
    full_rules_path = os.path.join(outputfolder,outputname)

    # ADD IO to General Rules (this is for the mapping file)
    rules_['IO'] = {}
    rules_['IO']['source'] = source_path
    rules_['IO']['target'] = bids_root
    mapping_data = {'General':rules_,'Individual':all_mappings}
    with open(full_rules_path, 'w') as outfile:
        yaml.dump(mapping_data, outfile, default_flow_style=False)

    print('Mapping file wrote to:',full_rules_path) #TODO This should be a log print
    return mapping_data

def sovapply():
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
    sovapply()