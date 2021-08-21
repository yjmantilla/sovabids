from sovabids.heuristics import from_io_example
from sovabids.rules import apply_rules_to_single_file
from sovabids.dicts import deep_merge_N
from sovabids.rules import load_rules
import os
import pytest
try:
    from test_bids import dummy_dataset
except ImportError:
    from .test_bids import dummy_dataset


def test_from_io_example():
    
    # check if there is already an example dataset to save time

    pattern_type='placeholder'#defaults of dummy_dataset function
    mode='python'#defaults of dummy_dataset function
    # Getting current file path and then going to _data directory
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir,'..','_data')
    data_dir = os.path.abspath(data_dir)

    # Defining relevant conversion paths
    test_root = os.path.join(data_dir,'DUMMY')
    input_root = os.path.join(test_root,'DUMMY_SOURCE')
    mode_str = '_' + mode
    bids_path = os.path.join(test_root,'DUMMY_BIDS'+'_'+pattern_type+mode_str)
    mapping_file = os.path.join(bids_path,'code','sovabids','mappings.yml')
    if not os.path.isfile(mapping_file):
        mappings = dummy_dataset()
    else:
        mappings = load_rules(mapping_file)
    sourcepath=mappings['Individual'][0]['IO']['source']
    targetpath=mappings['Individual'][0]['IO']['target']
    answer=mappings['Individual'][0]['non-bids']['path_analysis']['pattern']
    pattern = from_io_example(sourcepath,targetpath)['pattern']
    assert pattern == answer
    rules = mappings['General']
    example_rule = {'non-bids':{'path_analysis':{'pattern':'None','source':sourcepath,'target':targetpath}}}
    rules = deep_merge_N([rules,example_rule])
    ind_mapping = apply_rules_to_single_file(sourcepath,rules,rules['IO']['target'])
    assert ind_mapping[0]['IO']['target'] == targetpath

    source = 'data/lemon/V001/resting/010002.vhdr'
    target =  'data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr'
    pattern = from_io_example(source,target)['pattern']
    assert pattern == 'V%entities.session%/%entities.task%/%entities.subject%.vhdr'
    

    source = 'data/lemon/V001/resting/010002.vhdr'
    target =  'data_bids/sub-010002/ses-001/eeg/010002.vhdr'
    with pytest.raises(IOError):
        from_io_example(source,target)

    target =  'data_bids/sub-010002/ses-001/eeg/sub-010002_.vhdr'
    with pytest.raises(AssertionError):
        from_io_example(source,target)

    print('hallelujah')

if __name__ == '__main__':
    test_from_io_example()
    print('ok')