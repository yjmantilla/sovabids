import os
import shutil
from sys import path
import yaml
from sovabids.parsers import custom_notation_to_regex
from sovabids.rules import apply_rules,load_rules
from sovabids.utils import create_dir, make_dummy_dataset,deep_merge_N
from bids_validator import BIDSValidator
from sovabids.convert import convert_them
def dummy_dataset(pattern_type='custom',write=True,cli=False):

    # Getting current file path and then going to _data directory
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir,'..','_data')
    data_dir = os.path.abspath(data_dir)

    # Defining relevant conversion paths
    test_root = os.path.join(data_dir,'DUMMY')
    input_root = os.path.join(test_root,'DUMMY_SOURCE')
    cli_str = '' if cli == False else '_cli'
    bids_root = os.path.join(test_root,'DUMMY_BIDS'+'_'+pattern_type+cli_str)

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
    dirs = [input_root,bids_root] #dont include test_root for saving multiple conversions
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
    'dataset_description':
        {
            'Name':'Dummy',
            'Authors':['A1','A2'],
        },
    'sidecar':  
        {
            'PowerLineFrequency' : 50,
            'EEGReference':'FCz',
            'SoftwareFilters':{"Anti-aliasing filter": {"half-amplitude cutoff (Hz)": 500, "Roll-off": "6dB/Octave"}}
        },
    'non-bids':
        {
        'eeg_extension':'.vhdr',
        'path_analysis':{'pattern':FIXED_PATTERN},
        'code_execution':['print(raw.info)']
        },
    'channels':
        {'name':{'0':'ECG_CHAN','1':'EOG_CHAN'},
        'type':{'ECG_CHAN':'ECG','EOG_CHAN':'EOG'}}
    }

    if pattern_type == 'regex':
        FIXED_PATTERN_RE,fields = custom_notation_to_regex(FIXED_PATTERN)
        dregex = {'non-bids':{'path_analysis':{'fields':fields,'pattern':FIXED_PATTERN_RE}}}
        data = deep_merge_N([data,dregex])
    # Writing the rules file
    outputname = 'dummy_rules'+'_'+pattern_type+'.yml'

    full_rules_path = os.path.join(test_root,outputname)
    with open(full_rules_path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

    mappings_path=None

    if not cli:
        # Loading the rules file (yes... kind of redundant but tests the io of the rules file)
        rules = load_rules(full_rules_path)

        file_mappings = apply_rules(source_path=input_root,bids_root=bids_root,rules_=rules)
    else:
        os.system('sovapply '+input_root + ' '+ bids_root + ' ' + full_rules_path)
        mappings_path = os.path.join(bids_root,'code','sovabids','mappings.yml')
        file_mappings = load_rules(mappings_path)

    individuals=file_mappings['Individual']

    # Testing the mappings (at the moment it only test the filepaths)
    validator = BIDSValidator()
    filepaths = [x['IO']['target'].replace(bids_root,'') for x in individuals]
    for filepath in filepaths:
        assert validator.is_bids(filepath)
    if write:
        if not cli:
            convert_them(file_mappings)
        else:
            os.system('sovaconvert '+mappings_path)

def test_dummy_dataset():
    dummy_dataset('custom',write=True)
    dummy_dataset('regex',write=True)
    dummy_dataset('custom',write=True,cli=True)
    dummy_dataset('regex',write=True,cli=True)

if __name__ == '__main__':
    test_dummy_dataset()
    print('ok')