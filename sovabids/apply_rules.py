import os
import mne_bids
import json
import yaml

from sovabids.utils import get_files,split_by_n,parse_string_from_template,run_command,mne_open
from mne_bids import BIDSPath, read_raw_bids, print_dir_tree, make_report,write_raw_bids

def apply_rules(source_path,bids_root,rules):
    if not isinstance(rules,dict):
        with open(rules,encoding="utf-8") as f:
            rules = yaml.load(f,yaml.FullLoader)

    # Generate all files
    try:
        extensions = rules['non-bids']['eeg_extension']
    except:
        extensions = ['.set' ,'.cnt' ,'.vhdr' ,'.bdf' ,'.fif'] 

    if isinstance(extensions,str):
        extensions = [extensions]

    # append dot to extensions if missing
    extensions = [x if x[0]=='.' else '.'+x for x in extensions]

    filepaths = get_files(source_path)
    filepaths = [x for x in filepaths if os.path.splitext(x)[1] in extensions]

    #%% BIDS CONVERSION

    for f in filepaths:
        
        # Upon reading RAW MNE makes the assumptions
        raw = mne_open(f)

        # First get info from path

        patterns_extracted = {}
        if 'splitter' in rules['non-bids']:
            splitter = rules['non-bids']['splitter']
        else:
            splitter = '%'

        if "path_pattern" in rules['non-bids']:
            patterns_extracted = parse_string_from_template(f,rules['non-bids']['path_pattern'],splitter)
        if 'ignore' in patterns_extracted:
            del patterns_extracted['ignore']
        # this what needed because using rules.update(patterns_extracted) replaced it all

        for key in ['entities','channels','dataset_description','sidecar','channels','electrodes','coordsystem','events','non-bids']:
            if key in patterns_extracted:
                if key in rules:
                    rules[key].update(patterns_extracted[key])
                else:
                    rules[key] = patterns_extracted[key]
            #it wont work for nested dicts :/


        # Apply Rules
        assert 'entities' in rules
        entities = rules['entities'] # this key has the same fields as BIDSPath constructor argument

        if 'sidecar' in rules:
            sidecar = rules['sidecar']
            if "PowerLineFrequency" in sidecar:
                raw.info['line_freq'] = sidecar["PowerLineFrequency"]  # specify power line frequency as required by BIDS
            # Should we try to infer the line frequency automatically from the psd?

        if 'channels' in rules:
            channels = rules['channels']
            if "type" in channels:
                raw.set_channel_types(channels["type"])

        if 'non-bids' in rules:
            non_bids = rules['non-bids']
            if "code_execution" in non_bids:
                if isinstance(non_bids["code_execution"],str):
                    run_command(non_bids["code_execution"])
                if isinstance(non_bids["code_execution"],list):
                    for command in non_bids["code_execution"]:
                        run_command(command)
                        # maybe log errors here?


        bids_path = BIDSPath(**entities,root=bids_root)
        write_raw_bids(raw, bids_path=bids_path,overwrite=True)

        # Rules that need to be applied to the result of mne-bids
        # Or maybe we should add the functionality directly to mne-bids

        if 'sidecar' in rules:
            sidecar_path = bids_path.copy().update(suffix='eeg', extension='.json')
            with open(sidecar_path.fpath) as f:
                dummy_dict = json.load(f)
                sidecar = rules['sidecar']
                dummy_dict.update(sidecar)
                mne_bids.utils._write_json(sidecar_path.fpath,dummy_dict,overwrite=True)

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