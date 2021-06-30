import re

from sovabids.utils import deep_merge_N,nested_notation_to_tree,flat_paren_counter

def placeholder_to_regex(placeholder,encloser='%',matcher='(.+)'):
    """Translate a placeholder pattern to a regex pattern.

    placeholder : The placeholder pattern to translate.
    matcher     : The regex pattern to use for the placeholder, ie : (.*?),(.*),(.+).
    encloser    : The symbol which encloses the fields of the placeholder pattern.
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

    string      : The string to parse.
    pattern     : The placeholder pattern to use for parsing.
    matcher     : The regex pattern to use for the placeholder, ie : (.*?),(.*),(.+).
    encloser    : The symbol which encloses the fields of the placeholder pattern.
    """
    pattern,fields = placeholder_to_regex(pattern,encloser,matcher)
    return parse_from_regex(string,pattern,fields)

def parse_from_regex(string,pattern,fields):
    """Parse string from regex pattern.

    string      : The string to parse.
    pattern     : The regex pattern to use for parsing.
    fields      : List of fields in the same order as they appear in the regex pattern.
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
