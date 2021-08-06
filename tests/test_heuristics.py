from numpy import source
from test_bids import dummy_dataset
from sovabids.heuristics import from_io_example

if __name__ == '__main__':
    mappings = dummy_dataset()

    sourcepath=mappings[0]['IO']['source']
    targetpath=mappings[0]['IO']['target']
    answer=mappings[0]['non-bids']['path_analysis']['pattern']
    pattern = from_io_example(sourcepath,targetpath)
    assert pattern == answer

    print('ok')