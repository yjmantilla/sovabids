from sovabids.heuristics import from_io_example
from sovabids.rules import apply_rules_to_single_file
from sovabids.dicts import deep_merge_N
try:
    from test_bids import dummy_dataset
except ImportError:
    from .test_bids import dummy_dataset


def test_from_io_example():
    mappings = dummy_dataset()
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

if __name__ == '__main__':
    test_from_io_example()
    print('ok')