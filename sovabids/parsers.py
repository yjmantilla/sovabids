from sovabids.utils import deep_merge_N,nested_notation_to_tree,flat_paren_counter
import re
def parse_string_from_template(string,pattern,splitter='%'):
    """
    USE POSIX
    params:
    string : string to be parsed ie 'y:/code/sovabids/_data/lemon/sub-010002.vhdr'
    pattern : string with the temmplate ie 'y:/code/sovabids/_data/%dataset_description.name%/sub-%entities.subject%.vhdr'
    splitter : open and close symbol for the fields ie '%'
    
    WARNING: This function assumes that the string fields are separated by at least 1 char
    that is, metadata does not directly touch in the string.
    
    See eeg_bids_fields_collection.yml for fields, note that dot notation is used (dataset_description.name)
    
    For example:
    good: %entities.subject%-%entities.task%
    bad: %entities.subject%%entities.task%

    Use %ignore% to avoid inputting the whole path
    Not including at least absolute path with %ignore% not currently suported
    Possible problems:
    fields with numeric values, they should be converted, the problem is which to convert?
    """
    #TODO: Change the name of the function for something more appropiate
    string = string.replace('\\','/') # USE POSIX PLEASE
    pattern = pattern.replace('\\','/')
    if pattern.count('%') == 0 or pattern.count('%') % 2 != 0:
        return {}
    else:
        borders = pattern.split(splitter)[::2]
        fields = pattern.split(splitter)[1::2]
        last_end = 0
        l = []
        for i,field in enumerate(fields):
            start = last_end+len(borders[i])+string[last_end:].find(borders[i])
            if field == fields[-1] and borders[-1] == '':
                end = -1
                value = string[start:]
            else:
                end = len(string[:start])+string[start:].find(borders[i+1])
                last_end=end
                value = string[start:end]
            d = nested_notation_to_tree(field,value)
            l.append(d)
        return deep_merge_N(l)

def custom_notation_to_regex(custom_notation,splitter='%',matcher='(.+)'):
    """
    matchers = (.*?),(.*),(.+)
    """
    pattern = custom_notation
    pattern = pattern.replace('\\','/')
    if pattern.count('%') == 0 or pattern.count('%') % 2 != 0:
        return '',[]
    else:
        borders = pattern.split(splitter)[::2]
        fields = pattern.split(splitter)[1::2]
    for field in fields:
        pattern = pattern.replace(splitter+field+splitter, matcher, 1)
    pattern = pattern.replace('/','\\/')
    return pattern,fields

def parse_from_custom_notation(string,pattern,splitter='%',matcher='(.+)'):
    pattern,fields = custom_notation_to_regex(pattern,splitter,matcher)
    return regex_parser(string,pattern,fields)

def regex_parser(string,expression,fields):
    string = string.replace('\\','/') # USE POSIX PLEASE
    num_groups = flat_paren_counter(expression)
    if isinstance(fields,str):
        fields = [fields]
    num_fields = len(fields)
    if not num_fields == num_groups:
        return {}
    match = re.search(expression,string)
    if not num_groups == len(match.groups()):
        return {}
    
    l = []
    
    for field,value in zip(fields,list(match.groups())):
        d = nested_notation_to_tree(field,value)
        l.append(d)
    return deep_merge_N(l)
