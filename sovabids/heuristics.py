"""Heuristics Module

Functions should return a dictionary.
"""
from sovabids.parsers import parse_path_pattern_from_entities
from sovabids.parsers import parse_entities_from_bidspath

def from_io_example(sourcepath,targetpath):
    """Get the path pattern from a source-target mapping example.
    
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
    bids_entities=parse_entities_from_bidspath(targetpath)
    pattern = parse_path_pattern_from_entities(sourcepath,bids_entities)
    return {'pattern':pattern}
