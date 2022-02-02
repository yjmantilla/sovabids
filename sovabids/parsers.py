"""Module with parser utilities."""
import re
from copy import deepcopy

from numpy import mat
from sovabids.misc import flat_paren_counter
from sovabids.dicts import deep_merge_N,nested_notation_to_tree

def placeholder_to_regex(placeholder,encloser='%',matcher='(.+)'):
    """Translate a placeholder pattern to a regex pattern.

    Parameters
    ----------
    placeholder : str
        The placeholder pattern to translate.
    matcher : str, optional
        The regex pattern to use for the placeholder, ie : (.*?),(.*),(.+).
    encloser : str, optional
        The symbol which encloses the fields of the placeholder pattern.
    
    Returns
    -------

    pattern : str
        The regex pattern.
    fields  : list of str
        The fields as they appear in the regex pattern.
    """
    pattern = placeholder
    pattern = pattern.replace('\\','/')
    if pattern.count('%') == 0 or pattern.count('%') % 2 != 0:
        return '',[]
    else:
        borders = pattern.split(encloser)[::2]
        fields = pattern.split(encloser)[1::2]
    for field in fields:
        pattern = pattern.replace(encloser+field+encloser, matcher, 1)
    pattern = pattern.replace('/','\\/')
    return pattern,fields

def parse_from_placeholder(string,pattern,encloser='%',matcher='(.+)'):
    """Parse string from a placeholder pattern.

    Parameters
    ----------

    string : str
        The string to parse.
    pattern : str
        The placeholder pattern to use for parsing.
    matcher : str, optional
        The regex pattern to use for the placeholder, ie : (.*?),(.*),(.+).
    encloser : str, optional
        The symbol which encloses the fields of the placeholder pattern.

    Returns
    -------

    dict
        The dictionary with the fields and values requested.
    """
    pattern,fields = placeholder_to_regex(pattern,encloser,matcher)
    return parse_from_regex(string,pattern,fields)

def parse_from_regex(string,pattern,fields):
    """Parse string from regex pattern.

    Parameters
    ----------
    string : str
        The string to parse.
    pattern : str
        The regex pattern to use for parsing.
    fields : list of str
        List of fields in the same order as they appear in the regex pattern.

    Returns
    -------

    dict
        The dictionary with the fields and values requested.
    """

    string = string.replace('\\','/') # USE POSIX PLEASE
    num_groups = flat_paren_counter(pattern)
    if isinstance(fields,str):
        fields = [fields]
    num_fields = len(fields)
    if not num_fields == num_groups:
        return {}
    match = re.search(pattern,string)

    if not hasattr(match, 'groups'):
        raise AttributeError(f"Couldn't find fields in the string {string} using the pattern {pattern}. Recheck the pattern for errors.")

    if not num_groups == len(match.groups()):
        return {}
    
    l = []
    
    for field,value in zip(fields,list(match.groups())):
        if '_' in value or '-' in value:
            value2 = value.replace('_','')
            value2 = value2.replace('-','')
            d = nested_notation_to_tree(field,value2)
        else:
            d = nested_notation_to_tree(field,value)        
        l.append(d)
    return deep_merge_N(l)

def parse_entity_from_bidspath(path,entity,mode='r2l'):
    """Get the value of a bids-entity from a path.
    
    Parameters
    ----------
    path : str
        The bidspath we are going to derive the information on.
        Should be the complete path of file of a modality (ie an _eeg file).
    entity : str
        The entity we are going to extract.
        SHOULD be one of sub|ses|task|acq|run 
    mode : str
        Direction of lookup. One of r2l|l2r .
        r2l (right to left)
        l2r (left to right)

    Returns
    -------
    value : str
        The extracted value of the entity as a string.
        If None, it means the entity was not found on the string.
    """
    entity = entity if '-' in entity else entity + '-'
    # Easier to find it from the tail of the bidspath
    if mode == 'r2l':
        entity_position = path.rfind(entity)
    elif mode == 'l2r':
        entity_position = path.find(entity)
    else:
        raise ValueError('Incorrect usage of the mode argument.')

    if entity_position == -1:
        return None

    little_path = path[entity_position:]

    value = re.search('%s(.*?)%s' % ('-', '_'), little_path,).group(1)

    return value

def _modify_entities_of_placeholder_pattern(pattern,mode='append'):
    """Convert between sovabids entities pattern notation and the shorter notation.
    
    The shorter notation is:
    %dataset%, %task%, %session%, %subject%, %run%, %acquisition%
    
    Parameters
    ----------
    string : str
        The pattern string to convert.
    mode : str
        Whether to append 'entities' or cut it. One of {'append','cut'}

    Returns
    -------
    str
        The converted pattern string.
    """
    if mode == 'append':
        for keyword in ['%task%','%session%','%subject%','%run%','%acquisition%']:
            pattern = pattern.replace(keyword,'%entities.'+keyword[1:])
        pattern = pattern.replace('%dataset%','%dataset_description.Name%')
    elif mode == 'cut':
        for keyword in ['%task%','%session%','%subject%','%run%','%acquisition%']:
            pattern = pattern.replace('%entities.'+keyword[1:],keyword)
        pattern = pattern.replace('%dataset_description.Name%','%dataset%')
    return pattern

def parse_entities_from_bidspath(targetpath,entities=['sub','ses','task','acq','run'],mode='r2l'):
    """Get the bids entities from a bidspath.
    
    Parameters
    ----------
    targetpath : str
        The bidspath we are going to derive the information on.
    entities : list of str
        The entities we are going to extract.
        Defaults to sub,ses,task,acq,run
    mode : str
        Direction of lookup. One of r2l|l2r .
        r2l (right to left)
        l2r (left to right)

    Returns
    -------
    dict
        A dictionary with the extracted entities.
        {'sub':'11','task':'resting','ses':'V1','acq':'A','run':1}
    """
    path = deepcopy(targetpath)
    bids_dict = dict()
    for entity in entities:
        bids_dict[entity] = parse_entity_from_bidspath(path,entity,mode)
    # Clean Non Existent key
    bids_dict2 = {key:value for key,value in bids_dict.items() if value is not None}
    return bids_dict2

def parse_path_pattern_from_entities(sourcepath,bids_entities):
    """Get the path pattern from a path and a dictionary of bids entities and their values.

    Parameters
    ----------
    sourcepath : str
        The sourcepath that will be modified to get the path pattern
    bids_entities : dict
        Dictionary with the entities and their values on the path.
        Ie {'sub':'11','task':'resting','ses':'V1','acq':'A','run':1}
        There should be no ambiguity between the sourcepath and each of the values.
        Otherwise an error will be raised.

    Returns
    -------

    str :
        The path pattern in placeholder format
    """
    path = deepcopy(sourcepath)
    values = [val for key,val in bids_entities.items()]
    key_map={
        'sub':'%subject%',
        'ses':'%session%',
        'task':'%task%',
        'acq':'%acquisition%',
        'run':'%run%'
    }
    assert '%' not in path # otherwise it will mess up the logic
    for key,val in bids_entities.items():
        pathcopy = deepcopy(path)
        # Replace all other values which are superstrings of the current one
        superstrings = [x for x in values if val in x and val!=x]
        for string in superstrings:
            pathcopy = pathcopy.replace(string,'*'*len(string))
        # handle ambiguity
        if pathcopy.count(val) > 1:
            raise ValueError('Ambiguity: The path has multiple instances of {}'.format(val))
        if pathcopy.count(val) < 1:
            superstrings = [x for x in bids_entities.values() if val in x and val!=x]
            substrings = [x for x in bids_entities.values() if x in val and val!=x]
            possible_ambiguity_with = set(superstrings+substrings)
            raise ValueError(f'{val} seems to be ambiguous with any of the following values {possible_ambiguity_with}')
        path = path.replace(val,key_map[key])
        values[values.index(val)] = key_map[key]
    path = _modify_entities_of_placeholder_pattern(path)
    path = path.replace('\\','/')
    # Find first changing value and put the pattern from there
    first_placeholder  = path.find('%')
    # Identify where should the pattern start
    start = path[:first_placeholder].rfind('/') + 1 if '/' in path[:first_placeholder] else 0
    path = path[start:]
    return  path

def find_bidsroot(path):
    """Get the bidsroot from an absolute path describing a bids file inside a subject subfolder.

    Parameters
    ----------
    path : str
        The absolute path to any bids file inside a sub- folder.

    Returns
    -------

    str :
        The bidsroot absolute path.
    """
    sub = parse_entities_from_bidspath(path,entities=['sub'],mode='r2l')
    index = path.find(sub['sub'])
    #We know the bids root is the path up until that index minus some stuff
    bidsroot = path[:index-4] #remove sub- prefix
    return bidsroot
