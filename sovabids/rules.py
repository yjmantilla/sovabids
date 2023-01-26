"""Module dealing with the rules for bids conversion."""
import os
import json
from shutil import ReadError
import yaml
import argparse
import logging
import re

from copy import deepcopy
from mne_bids import write_raw_bids,BIDSPath
from mne_bids.utils import _handle_datatype,_write_json,_get_ch_type_mapping
from mne_bids.path import _parse_ext
from mne.io import read_raw
from pandas import read_csv
from traceback import format_exc

from sovabids.settings import NULL_VALUES,SUPPORTED_EXTENSIONS
from sovabids.files import _get_files
from sovabids.dicts import deep_merge_N,deep_get,nested_notation_to_tree
from sovabids.parsers import parse_from_regex,parse_from_placeholder
from sovabids.bids import update_dataset_description
from sovabids.loggers import setup_logging
from sovabids.settings import SECTION_STRING
from sovabids.heuristics import from_io_example

import logging
LOGGER = logging.getLogger(__name__)

def _regex_match(pattern,string):
    match = re.search(pattern,string)
    match = True if match else False
    return match 
def get_info_from_path(path,rules):
    """Parse information from a given path, given a set of rules.

    Parameters
    ----------

    path : str
        The path from where we want to extract information.
    rules : dict
        A dictionary following the "Rules File Schema".

    Notes
    --------

    See the Rules File Schema documentation for the expected schema of the dictionary.
    """
    rules_copy = deepcopy(rules)
    patterns_extracted = {}

    # Check first if we have an example-based conversion
    target = deep_get(rules_copy,'non-bids.path_analysis.target',None)
    source = deep_get(rules_copy,'non-bids.path_analysis.source',None)

    if target is not None and source is not None:
        # Example based path pattern
        pattern = from_io_example(source,target).get('pattern',None)
        rules_copy = deep_merge_N([rules_copy,{'non-bids':{'path_analysis':{'pattern':pattern}}}])

    pattern = deep_get(rules_copy,'non-bids.path_analysis.pattern',None)
    if pattern is None: # No path_patten rule
        LOGGER.warning(f"Warning.No path pattern found.")
        return rules_copy
    else:
        fields = deep_get(rules_copy,'non-bids.path_analysis.fields',None)
        if fields is None: # assume placeholder pattern
            encloser = deep_get(rules_copy,'non-bids.path_analysis.encloser','%')
            matcher = deep_get(rules_copy,'non-bids.path_analysis.matcher','(.+)')
            patterns_extracted = parse_from_placeholder(path,pattern,encloser,matcher)
        else: # is a regex pattern
            patterns_extracted = parse_from_regex(path,pattern,fields)
    
    # If operations between values extracted should be carried out, it should be here
    postprocess = deep_get(rules_copy,'non-bids.path_analysis.operation',None)

    if postprocess:
        l=[]
        for key,val in postprocess.items():
            scoped_expression=val.replace('[',"patterns_extracted['").replace("]","']")
            treated_value=eval(scoped_expression)
            d = nested_notation_to_tree(key,treated_value.replace('-','').replace('_',''))
            l.append(d)
        patterns_extracted = deep_merge_N([patterns_extracted]+l)
    if 'ignore' in patterns_extracted:
        del patterns_extracted['ignore']
    # merge needed because using rules_copy.update(patterns_extracted) replaced it all
    rules_copy = deep_merge_N([rules_copy,patterns_extracted])
    return rules_copy

def get_files(source_path,rules):
    """Recursively scan the directory for valid files, returning a list with the full-paths to each.
    
    The valid files are given by the 'non-bids.eeg_extension' rule. See the "Rules File Schema".

    Parameters
    ----------

    source_path : str
        The path we want to obtain the files from.
    rules : str|dict
        The path to the rules file, or the rules dictionary.

    Returns
    -------

    filepaths : list of str
        A list containing the path to each valid file in the source_path.
    """
    rules_copy = load_rules(rules)

    if isinstance(source_path,str):
        # Generate all files
        extensions = deep_get(rules_copy,'non-bids.eeg_extension',None)
        filters = deep_get(rules_copy,'non-bids.file_filter',[])
        if extensions is None:
            extensions = deepcopy(SUPPORTED_EXTENSIONS)

        if isinstance(extensions,str):
            extensions = [extensions]
        
        # append dot to extensions if missing
        extensions = [x if x[0]=='.' else '.'+x for x in extensions]

        filepaths = _get_files(source_path)
        filepaths = [x for x in filepaths if os.path.splitext(x)[1] in extensions]
        for filter_ in filters:
            for key,val in filter_.items():
                if key == 'include':
                    filepaths = [x  for x in filepaths if _regex_match(val,x)]
                if key == 'exclude':
                    filepaths = [x  for x in filepaths if not _regex_match(val,x)]
    else:
        raise ValueError('The source_path should be str.')
    return filepaths

def load_rules(rules):
    """Load rules if given a path, bypass if given a dict.

    Parameters
    ----------
    
    rules : str|dict
        The path to the rules file, or the rules dictionary.

    Returns
    -------

    dict
        The rules dictionary.
    """
    if isinstance(rules,str):
        try:
            with open(rules,encoding="utf-8") as f:
                return yaml.load(f,yaml.FullLoader)
        except:
            raise IOError(f"Couldnt read {rules} file as a rule file.")
    elif isinstance(rules,dict):
        return deepcopy(rules)
    else:
        raise ValueError(f'Expected str or dict as rules, got {type(rules)} instead.')

def apply_rules_to_single_file(file,rules,bids_path,write=False,preview=False):
    """Apply rules to a single file.

    Parameters
    ----------

    file : str
        Path to the file.
    rules : str|dict
        Path to the rules file or rules dictionary.
    bids_path : str
        Path to the bids directory
    write : bool, optional
        Whether to write the converted files to disk or not.
    preview : bool, optional
        Whether to return a dictionary with a "preview" of the conversion.
        This dict will have the same schema as the "Mapping File Schema" but may have flat versions of its fields.
        *UNDER CONSTRUCTION*

    Returns
    -------

    mapping : dict
        The mapping obtained from applying the rules to the given file
    preview : bool|dict
        If preview = False, then False. If True, then the preview dictionary.
    """
    if isinstance(file,str):
        f = file
    else:
        raise ValueError(f'Expected file to be str, got {type(file)} instead.')

    rules_copy = load_rules(rules)

    # Read file with MNE
    try:
        raw = read_raw(f,preload=False)#not write)
        # TODO:Should we try to artificially past MNE-BIDS CHECK?
        # Which checks that
        # ext in ALLOWED_INPUT_EXTENSIONS?
        # raw.filenames[0]=''.join(raw.filenames[0].split('.')[:-1])+'.set'
    except:
        raise IOError(f'MNE couldnt read {f} .')

    # Get info from path
    rules_copy = get_info_from_path(f,rules_copy)

    # Apply Rules

    # Entities
    assert 'entities' in rules_copy,'`entities` must be in the rules or mapping dictionary'
    entities = rules_copy['entities'] # this key has the same fields as BIDSPath constructor argument

    # Sidecar json
    if 'sidecar' in rules_copy:
        sidecar = rules_copy['sidecar']
        if "PowerLineFrequency" in sidecar and sidecar['PowerLineFrequency'] not in NULL_VALUES:
            raw.info['line_freq'] = sidecar["PowerLineFrequency"]  # specify power line frequency as required by BIDS
        # Should we try to infer the line frequency automatically from the psd?

    # Channels tsv
    if 'channels' in rules_copy:
        channels = rules_copy['channels']

        # Renaming
        if "name" in channels:
            raw.rename_channels(channels['name'])

        # Retyping

        if "type" in channels: # We overwrite whatever channel types we can on the files
            # See: https://github.com/mne-tools/mne-bids/blob/3711613edc0e2039c921ad9b1a32beccc52156b1/mne_bids/utils.py#L78-L83
            # care should be taken with the channel counts set up by mne-bids https://github.com/mne-tools/mne-bids/blob/main/mne_bids/write.py#L774-L782
            # but right now is inofensive
            types = channels['type']
            
            # Map the bidstypes to mnetypes
            types = {key:_get_ch_type_mapping(fro='bids',to='mne').get(val,None) for key,val in types.items() }
            valid_types = {k: v for k, v in types.items() if v is not None} # invalid types for mne will be None,remove them
            raw.set_channel_types(valid_types)
    #TODO: Document format option
    output_format = 'BrainVision'
    # Non-bids section
    if 'non-bids' in rules_copy:
        non_bids = rules_copy['non-bids']

        if 'format' in non_bids: # DEPRECATED BACKWARD COMPATIBLE
            output_format = non_bids.get('format','BrainVision')
        if 'output_format' in non_bids:
            output_format = non_bids.get('output_format','BrainVision')
        if "code_execution" in non_bids:
            code_execution = non_bids.get('code_execution',None)

            if isinstance(code_execution,str):
                non_bids["code_execution"] = [non_bids["code_execution"]]

            if isinstance(code_execution,list):
                for command in non_bids["code_execution"]:
                    try:
                        exec(command)
                    except:
                        error_string = 'There was an error with the following command:\n'+command+'\ngiving the following traceback:\n'+format_exc()
                        print(error_string)
                        #maybe log errors here?
                        #or should we raise an exception?
            else:
                raise ValueError(f'Expected code_execution to be str or list, got {type(code_execution)} instead')

        # remember the `entities` key fields must have the same parameters as the BIDSPath constructor argument
        bids_path = BIDSPath(**entities,root=bids_path)

        real_times = raw.times[-1] # Save real duration of the eeg, since it is lost if write is false

        if write:
            write_raw_bids(raw, bids_path=bids_path,format=output_format,allow_preload=True,overwrite=True)
        else:
            if preview:
                # Crop the file for less computational cost
                max_samples = min(10,raw.last_samp)
                tmax = max_samples/raw.info['sfreq']
                raw.crop(tmax=tmax)
                orig_files = _get_files(bids_path.root)
                write_raw_bids(raw, bids_path=bids_path,overwrite=True,format=output_format,allow_preload=True,verbose=False)

            else:
                # Since write_raw_bids is not called we must run 
                # the following lines, which are taken from mne_bids.write

                ################################################################
                raw_fname = raw.filenames[0]
                if '.ds' in os.path.dirname(raw.filenames[0]):
                    raw_fname = os.path.dirname(raw.filenames[0])
                # point to file containing header info for multifile systems
                raw_fname = raw_fname.replace('.eeg', '.vhdr')
                raw_fname = raw_fname.replace('.fdt', '.set')
                raw_fname = raw_fname.replace('.dat', '.lay')
                _, ext = _parse_ext(raw_fname)

                datatype = _handle_datatype(raw,None)
                bids_path = bids_path.copy()
                bids_path = bids_path.update(
                    datatype=datatype, suffix=datatype, extension=ext)
                if bids_path.datatype in ['eeg', 'ieeg']:
                    if ext not in ['.vhdr', '.edf', '.bdf', '.EDF']:
                        bids_path.update(extension='.vhdr')
                ##################################################################


        # Construct the mapping using rules_copy
        rules_copy['IO']={}
        rules_copy['IO']['target'] = bids_path.fpath.__str__()
        rules_copy['IO']['source'] = f

        # POST-PROCESSING.
        # For stuff easier to overwrite in the files rather than in the raw object
        # Rules that need to be applied to the result of mne-bids
        # Or maybe we should add the functionality directly to mne-bids

        # Update the dataset description wrote by mne-bids with the input from the rules
        update_dataset_description(rules_copy.get('dataset_description',{}),bids_path.root,do_not_create=write)

        if write or preview:
            # sidecar json
            try:
                sidecar_path = bids_path.copy().update(datatype='eeg',suffix='eeg', extension='.json')
                with open(sidecar_path.fpath) as f:
                    sidecarjson = json.load(f)
                    sidecar = rules_copy.get('sidecar',{})
                    #TODO Validate the sidecar rules so as not to include dangerous stuff??
                    sidecarjson.update(sidecar)
                    sidecarjson.update({'RecordingDuration':real_times}) # needed if preview,since we crop
                    # maybe include an overwrite rule

                    # remove count fields (may have wrong values)
                    for count in ["EEGChannelCount" ,"EOGChannelCount" ,"ECGChannelCount" ,"EMGChannelCount" ,"MiscChannelCount" ,"TriggerChannelCount"]:
                        if count in sidecarjson:
                            del sidecarjson[count]

                _write_json(sidecar_path.fpath,sidecarjson,overwrite=True)

                # Get flat version of the sidecar
                with open(sidecar_path.fpath) as f:
                    sidecarjson = f.read().replace('\n', '')
            except:
                sidecarjson = ''
 
            # channels
            channels_path = bids_path.copy().update(datatype='eeg',suffix='channels', extension='.tsv')
            try:
                channels_table = read_csv (channels_path.fpath, sep = '\t',dtype=str,keep_default_na=False,na_filter=False,na_values=[],true_values=[],false_values=[])
                channels_rules = rules_copy.get('channels',{})

                # Modify the able with the new types
                # Note that this will add the types even if they are not supported by mne
                # Nevertheless, if a type was supported by mne, it was written to it previously

                if 'type' in channels_rules: # types are post since they are not saved in vhdr (are they in edf??)
                    for ch_name,ch_type in channels_rules['type'].items():
                        channels_table.loc[(channels_table.name==str(ch_name)),'type'] = ch_type
                
                # Save
                channels_table.to_csv(channels_path.fpath, index=False,sep='\t')

                with open(channels_path.fpath) as f:
                    channels = f.read().replace('\n', '__').replace('\t',',')

                # Make a preview version of channels tsv
                chans_dict = channels_table.to_dict(orient='list')

                channels={}
                for key,value in chans_dict.items():
                     channels[str(key)] = ','.join(value)
            except:
                channels = ''


            # dataset_description
            daset_path = os.path.join(bids_path.root, 'dataset_description.json')
            if os.path.isfile(daset_path):
                with open(daset_path) as f:

                    #NOTE Dataset description is currently managed by convert_them
                    # This since there is only one dataset description for all files
                    # So the lines that would write it here are commented

                    #dasetjson = json.load(f)
                    #daset = rules_copy.get('dataset_description',{}) #TODO more work needed to overwrite, specifically fields which arent pure strings like authors
                    #TODO Validate the sidecar rules_copy so as not to include dangerous stuff??
                    #dasetjson.update(daset)
                    # maybe include an overwrite rule
                    #if write:
                    #    _write_json(daset_path.fpath,dasetjson,overwrite=True)
                    
                    # We just read it for preview purposes
                    dasetjson = f.read().replace('\n', '')
            else:
                dasetjson =''

    # Make the preview (this is the 'header' that bidscoin reads with the keys as attributes)
    if preview:
        preview = {
            'IO' : rules_copy.get('IO',{}),
            'entities':rules_copy.get('entities',{}),
            'dataset_description':dasetjson,
            'sidecar':sidecarjson,
            'channels':channels,
            }
    #TODO remove general information of the dataset from the INDIVIDUAL MAPPINGS (ie dataset_description stuff)
    
    # CLEAN FILES IF NOT WRITE
    if not write and preview:
        new_files = _get_files(bids_path.root)
        new_files = list(set(new_files)-set(orig_files))
        for filename in new_files:
            if os.path.exists(filename): os.remove(filename)


    # Delete dataset_description from the individual mapping since it is a general property of the dataset
    if 'dataset_description' in rules_copy:
        del rules_copy['dataset_description']

    mapping = rules_copy # Just to rename the variable for something less confusing in the output

    return mapping,preview

def apply_rules(source_path,bids_path,rules,mapping_path=''):
    """Apply rules to a set of files.

    Parameters
    ----------

    source_path : str | list of str
        If str, the path with the files we want to convert to bids.
        If list of str with the paths of the files we want to convert (ie the output of get_files).
    bids_path : str
        The path we want the converted files in.
    rules : str|dict
        The path to the rules file, or a dictionary with the rules.
    mapping_path : str, optional
        The fullpath where we want to write the mappings file.
        If '', then bids_path/code/sovabids/mappings.yml will be used.
    
    Returns
    -------

    dict :
        A dictionary following: {
                                    'General': rules given,
                                    'Individual':list of mapping dictionaries for each file
                                }
    """
    
    # Safe Copy/Load Rules
    rules_copy = load_rules(rules)

    # Setup Mapping Path
    if isinstance(mapping_path,str):
        outputfolder,outputname = os.path.split(mapping_path)
        if outputname == '':
            outputname = 'mappings.yml'
        if outputfolder == '':
            outputfolder = os.path.join(bids_path,'code','sovabids')
        os.makedirs(outputfolder,exist_ok=True)
        full_mapping_path = os.path.join(outputfolder,outputname)
    else:
        raise ValueError(f'Expected mapping_path as an str but got {type(mapping_path)} instead')

    # Setup the logging
    log_file = os.path.join(bids_path,'code','sovabids','sovabids.log')
    setup_logging(log_file)
    LOGGER.info('')
    LOGGER.info(SECTION_STRING + ' START APPLY_RULES ' + SECTION_STRING)
    LOGGER.info(f"source_path={source_path} bids_path={bids_path} mapping={str(full_mapping_path)} ")

    if isinstance(source_path,str):
        LOGGER.info(f"Obtaining list of files.")
        filepaths = get_files(source_path,rules_copy)
        LOGGER.info(f"Found {len(filepaths)} files")
    elif isinstance(source_path,list) and len(source_path)!= 0 and isinstance(source_path[0],str):
        filepaths = deepcopy(source_path)
    else:
        raise ValueError(f'The source_path should be either str or a non-empty list of str. Got {type(source_path)}.')


    #%% BIDS CONVERSION
    LOGGER.info(f"Generating Individual Mappings")

    all_mappings = []
    num_files = len(filepaths)
    for i,f in enumerate(filepaths):
        try:
            LOGGER.info(f"File {i+1} of {num_files} ({(i+1)*100/num_files}%) : {f}")
            map,_ = apply_rules_to_single_file(f,rules_copy,bids_path,write=False,preview=False) #TODO There should be a way to control how verbose this is
            all_mappings.append(map)
        except :
            LOGGER.exception(f'Error for {f}')
            
            


    LOGGER.info(f"Individual Mappings Done!")

    # ADD IO to General Rules (this is for the mapping file)
    LOGGER.info(f"Making General Mapping")
    rules_copy['IO'] = {}
    rules_copy['IO']['source'] = source_path
    rules_copy['IO']['target'] = bids_path
    mapping_data = {'General':rules_copy,'Individual':all_mappings}
    LOGGER.info(f"General Mapping Done!")

    LOGGER.info(f"Saving Mapping File at {full_mapping_path}")

    try:
        with open(full_mapping_path, 'w') as outfile:
            yaml.dump(mapping_data, outfile, default_flow_style=False)
        LOGGER.info(f"Mapping file written to:{full_mapping_path}")
    except:
        LOGGER.warning(f'Couldn\'t write mapping file to:{full_mapping_path}')

    LOGGER.info(SECTION_STRING + ' END APPLY_RULES ' + SECTION_STRING)

    return mapping_data

def sovapply():
    """Console script usage for applying rules."""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('apply_rules')
    parser.add_argument('source_path',help='The path to the input data directory that will be converted to bids')  # add the name argument
    parser.add_argument('bids_path',help='The path to the output bids directory')  # add the name argument
    parser.add_argument('rules',help='The fullpath of the rules file')  # add the name argument
    parser.add_argument('-m','--mapping', help='The fullpath of the mapping file to be written. If not set it will be located in bids_path/code/sovabids/mappings.yml',default='')
    args = parser.parse_args()
    apply_rules(args.source_path,args.bids_path,args.rules,args.mapping)

if __name__ == "__main__":
    sovapply()
