from sovabids.heuristics import from_io_example
try:
    from test_bids import dummy_dataset
except ImportError:
    from .test_bids import dummy_dataset


def test_from_io_example():
    mappings = dummy_dataset()
    sourcepath=mappings[0]['IO']['source']
    targetpath=mappings[0]['IO']['target']
    answer=mappings[0]['non-bids']['path_analysis']['pattern']
    pattern = from_io_example(sourcepath,targetpath)['pattern']
    assert pattern == answer

if __name__ == '__main__':
    test_from_io_example()
    print('ok')