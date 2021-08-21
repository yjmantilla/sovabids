"""Heuristics Module

Functions should return a dictionary.
"""
from sovabids.parsers import parse_path_pattern_from_entities
from sovabids.parsers import parse_entities_from_bidspath
from sovabids.parsers import find_bidsroot
from bids_validator import BIDSValidator

def from_io_example(sourcepath,targetpath):
    """Get the path pattern from a source-target mapping example.
    
    The name of the function means "from input-output example", as one provides an input and output pair of (source,target) paths.
    
    Parameters
    ----------
    sourcepath : str
        The sourcepath that will be modified to get the path pattern
    targetpath : str
        The bidspath we are going to derive the information on.

    Returns
    -------
    dict :
        {
            'pattern': The path pattern in placeholder format.
        }
    """
    # TODO: Should  we also allow the user to just populate the bids stuff by himself
    # That is, instead of providing the target , directly provide the values
    # of the entities he expects on a dictionary
    # In example:  source = 'data/lemon/V001/resting/010002.vhdr'
    # target = {'subject':'010002','task':'resting','session':'001'}
    # With the currently implemented functions this is rather trivial. Is just a matter of exposing it.
    validator = BIDSValidator()
    # Find the root since we need it relative to the bidspath for the validator to work
    try:
        bidsroot = find_bidsroot(targetpath)
    except:
        raise IOError(f'targetpath :{targetpath} is not a valid bidspath.')
    targetpath2 = targetpath.replace(bidsroot,'') # avoid side-effects explicitly, although this shouldnt affect the str as it is immutable
    targetpath2 = targetpath2.replace('\\','/')
    # add / prefix
    if targetpath2[0] != '/':
        targetpath2 = '/' + targetpath2
    assert validator.is_bids(targetpath2),'ERROR: The provided target-path is not a valid bids-path'
    bids_entities=parse_entities_from_bidspath(targetpath)
    pattern = parse_path_pattern_from_entities(sourcepath,bids_entities)
    return {'pattern':pattern}
