import os
import shutil
import yaml
from fastapi.testclient import TestClient
from sovabids.sovarpc import app
import json

from bids_validator import BIDSValidator

from sovabids.parsers import placeholder_to_regex,_modify_entities_of_placeholder_pattern
from sovabids.rules import apply_rules,load_rules
from sovabids.dicts import deep_merge_N
from sovabids.datasets import make_dummy_dataset,save_dummy_vhdr,save_dummy_cnt
from sovabids.convert import convert_them

def dummy_dataset(pattern_type='placeholder',write=True,mode='python',format='.vhdr'):

    # Getting current file path and then going to _data directory
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir,'..','_data')
    data_dir = os.path.abspath(data_dir)

    # Defining relevant conversion paths
    test_root = os.path.join(data_dir,'DUMMY')
    input_root = os.path.join(test_root,'DUMMY_SOURCE')
    mode_str = '_' + mode
    bids_path = os.path.join(test_root,'DUMMY_BIDS'+'_'+pattern_type+mode_str+'_'+format.replace('.',''))

    # Make example File
    if format == '.vhdr':
        example_fpath = save_dummy_vhdr(os.path.join(data_dir,'dummy.vhdr'))
    elif format == '.cnt':
        example_fpath = save_dummy_cnt(os.path.join(data_dir,'dummy.cnt'))

    # PARAMS for making the dummy dataset
    DATA_PARAMS ={ 'EXAMPLE':example_fpath,
        'PATTERN':'T%task%/S%session%/sub%subject%_%acquisition%_%run%',
        'DATASET' : 'DUMMY',
        'NSUBS' : 2,
        'NTASKS' : 2,
        'NRUNS' : 2,
        'NSESSIONS' : 2,
        'ROOT' : input_root
    }

    if mode == 'rpc':
        client = TestClient(app)
    else:
        client = None

    # Preparing directories
    dirs = [input_root,bids_path] #dont include test_root for saving multiple conversions
    for dir in dirs:
        try:
            shutil.rmtree(dir)
        except:
            pass

    [os.makedirs(dir,exist_ok=True) for dir in dirs]

    # Generating the dummy dataset
    make_dummy_dataset(**DATA_PARAMS)

    # Making rules for the dummy conversion

    # Gotta fix the pattern that wrote the dataset to the notation of the rules file
    FIXED_PATTERN =DATA_PARAMS.get('PATTERN',None)

    FIXED_PATTERN = _modify_entities_of_placeholder_pattern(FIXED_PATTERN,'append')
    FIXED_PATTERN = FIXED_PATTERN + format

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
        'eeg_extension':format,
        'path_analysis':{'pattern':FIXED_PATTERN},
        'code_execution':['print(\'some good code\')','print(raw.info)','print(some bad code)']
        },
    'channels':
        {'name':{'1':'ECG_CHAN','2':'EOG_CHAN'}, #Note example vhdr and CNT have these channels
        'type':{'ECG_CHAN':'ECG','EOG_CHAN':'EOG'}} # Names (keys) are after the rename of the previous line
    }

    if pattern_type == 'regex':
        FIXED_PATTERN_RE,fields = placeholder_to_regex(FIXED_PATTERN)
        dregex = {'non-bids':{'path_analysis':{'fields':fields,'pattern':FIXED_PATTERN_RE}}}
        data = deep_merge_N([data,dregex])
    # Writing the rules file
    outputname = 'dummy_rules'+'_'+pattern_type+'.yml'

    full_rules_path = os.path.join(test_root,outputname)
    with open(full_rules_path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

    mappings_path=None

    if mode=='python':
        # Loading the rules file (yes... kind of redundant but tests the io of the rules file)
        rules = load_rules(full_rules_path)

        file_mappings = apply_rules(source_path=input_root,bids_path=bids_path,rules=rules)
    elif mode=='cli':
        os.system('sovapply '+input_root + ' '+ bids_path + ' ' + full_rules_path)
        mappings_path = os.path.join(bids_path,'code','sovabids','mappings.yml')
        file_mappings = load_rules(mappings_path)
    elif mode=='rpc':

        # Load Rules
        request=json.dumps({ #jsondumps important to avoid parse errors
        "jsonrpc": "2.0",
        "id": 0,
        "method": "load_rules",
        "params": {
        "rules_path": full_rules_path
            }
        })

        response = client.post("/api/sovabids/load_rules",data=request )
        print(request,'response',response.content.decode())
        rules = json.loads(response.content.decode())['result']

        # Save Rules
        request = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "save_rules",
        "params": {
            "rules": rules,
            "path": full_rules_path+'.bkp'
        }
        })
        response = client.post("/api/sovabids/save_rules",data=request )
        print(request,'response',response.content.decode())

        # Get Files
        request = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "get_files",
        "params": {
            "rules": rules,
            "path": input_root
        }
        })
        response = client.post("/api/sovabids/get_files",data=request )
        print(request,'response',response.content.decode())
        filelist = json.loads(response.content.decode())['result']

        # Preview Single File

        request=json.dumps({ #jsondumps important to avoid parse errors
        "jsonrpc": "2.0",
        "id": 0,
        "method": "apply_rules_to_single_file",
        "params": {
        "file": filelist[0],
        "bids_path": bids_path+'.preview',
        "rules": rules,
        "write":False,
        "preview":True
            }
        })
        response = client.post("/api/sovabids/apply_rules_to_single_file",data=request )
        print(request,'response',response.content.decode())
        single_file = json.loads(response.content.decode())
        print(single_file)

        # Get Mappings
        request=json.dumps({ #jsondumps important to avoid parse errors
        "jsonrpc": "2.0",
        "id": 0,
        "method": "apply_rules",
        "params": {
        "file_list": filelist,
        "bids_path": bids_path,
        "rules": rules,
        "mapping_path":''
            }
        })
        response = client.post("/api/sovabids/apply_rules",data=request )
        print(request,'response',response.content.decode())
        file_mappings = json.loads(response.content.decode())
        file_mappings=file_mappings['result']
        mappings_path = os.path.join(bids_path,'code','sovabids','mappings.yml')

        # Save Mappings
        request = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "save_mappings",
        "params": {
            "general": file_mappings['General'],
            "individual":file_mappings['Individual'],
            "path": mappings_path+'.bkp'
        }
        })
        response = client.post("/api/sovabids/save_mappings",data=request )
        print(request,'response',response.content.decode())

    individuals=file_mappings['Individual']

    # Testing the mappings (at the moment it only test the filepaths)
    validator = BIDSValidator()
    filepaths = [x['IO']['target'].replace(bids_path,'') for x in individuals]
    for filepath in filepaths:
        assert validator.is_bids(filepath),'{} is not a valid bids path'.format(filepath)
    if write:
        if mode=='python':
            convert_them(file_mappings)
        elif mode=='cli':
            os.system('sovaconvert '+mappings_path)
        elif mode=='rpc':
            request=json.dumps({ #jsondumps important to avoid parse errors
            "jsonrpc": "2.0",
            "id": 0,
            "method": "convert_them",
            "params": {
            "general": file_mappings['General'],
            "individual":file_mappings['Individual']
                }
            })
            response = client.post("/api/sovabids/convert_them",data=request)

            print('okrpc')
    return file_mappings
def test_dummy_dataset():
    # apparently it cannot download the cnt consistenly on the github actions machine
    #dummy_dataset('placeholder',write=True,format='.cnt') # Test cnt conversion
    dummy_dataset('placeholder',write=True)
    dummy_dataset('regex',write=True)
    dummy_dataset('placeholder',write=True,mode='cli')
    dummy_dataset('regex',write=True,mode='cli')
    dummy_dataset('placeholder',write=True,mode='rpc')
    dummy_dataset('regex',write=True,mode='rpc')

#TODO: A test for incremental conversion
if __name__ == '__main__':
    test_dummy_dataset()
    print('ok')