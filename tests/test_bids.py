import os
import shutil
from sys import path
import yaml
from sovabids.apply_rules import apply_rules,load_rules
from sovabids.utils import create_dir, make_dummy_dataset
from bids_validator import BIDSValidator

def test_dummy_dataset():

    # Getting current file path and then going to _data directory
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir,'..','_data')
    data_dir = os.path.abspath(data_dir)

    # Defining relevant conversion paths
    test_root = os.path.join(data_dir,'DUMMY')
    input_root = os.path.join(test_root,'DUMMY_SOURCE')
    bids_root = os.path.join(test_root,'DUMMY_BIDS')

    # PARAMS for making the dummy dataset
    DATA_PARAMS ={ 'PATTERN':'T%task%/S%session%/sub%subject%_%acquisition%_%run%',
        'DATASET' : 'DUMMY',
        'NSUBS' : 2,
        'NTASKS' : 2,
        'NRUNS' : 2,
        'NSESSIONS' : 2,
        'NCHANNELS' : 32,
        'NACQS' :2,
        'SFREQ' : 200,
        'STOP' : 10,
        'NUMEVENTS' : 10,
        'ROOT' : input_root
    }


    # Preparing directories
    dirs = [test_root,input_root,bids_root]
    for dir in dirs:
        try:
            shutil.rmtree(dir)
        except:
            pass

    [create_dir(dir) for dir in dirs]

    # Generating the dummy dataset
    make_dummy_dataset(**DATA_PARAMS)

    # Making rules for the dummy conversion

    # Gotta fix the pattern that wrote the dataset to the notation of the rules file
    FIXED_PATTERN =DATA_PARAMS.get('PATTERN',None)

    for keyword in ['%task%','%session%','%subject%','%run%','%acquisition%']:
        FIXED_PATTERN = FIXED_PATTERN.replace(keyword,'%entities.'+keyword[1:])
    FIXED_PATTERN = FIXED_PATTERN.replace('%dataset%','%dataset_description.Name%')
    FIXED_PATTERN = FIXED_PATTERN + '.' + 'vhdr'

    # Making the rules dictionary
    data={
    'dataset_description':{'Name':'Dummy','Authors':['A1','A2'],},
    'sidecar':  {'PowerLineFrequency' : 50,'EEGReference':'FCz'},
    'non-bids':{'eeg_extension':'.vhdr','path_pattern':FIXED_PATTERN,'code_execution':['print(raw.info)']}
    }

    # Writing the rules file
    outputname = 'dummy_rules.yml'

    full_rules_path = os.path.join(test_root,outputname)
    with open(full_rules_path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

    # Loading the rules file (yes... kind of redundant but tests the io of the rules file)
    rules = load_rules(full_rules_path)

    file_mappings = apply_rules(source_path=input_root,bids_root=bids_root,rules_=rules)

    # Testing the mappings (at the moment it only test the filepaths)
    validator = BIDSValidator()
    filepaths = [x['io']['target'].replace(bids_root,'') for x in file_mappings]
    for filepath in filepaths:
        assert validator.is_bids(filepath)
