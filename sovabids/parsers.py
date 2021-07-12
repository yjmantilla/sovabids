"""Module with parser utilities."""
import re

from sovabids.utils import deep_merge_N,nested_notation_to_tree,flat_paren_counter

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
    if not num_groups == len(match.groups()):
        return {}
    
    l = []
    
    for field,value in zip(fields,list(match.groups())):
        d = nested_notation_to_tree(field,value)
        l.append(d)
    return deep_merge_N(l)
