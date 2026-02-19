"""Module with dictionary utilities."""

import collections
from functools import reduce
def deep_get(dictionary, keys, default=None,sep='.'):
    """Safe nested dictionary getter.

    Parameters
    ----------
    dictionary: dict
        The dictionary from which to get the value.
    keys: str
        The nested keys using sep as separator.
        Ie: 'person.name.lastname' if `sep`='.'
    default: object
        The default value to return if the key is not found
    sep : str, optional
        The separator to indicate nesting/branching/hierarchy.

    Returns
    -------

    object:
        The value of the required key. `default` if the key is not found.

    Notes
    -----
    Taken from https://stackoverflow.com/a/46890853/14068216
    """
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split(sep), dictionary)

def deep_merge_N(l):
    """Merge the list of dictionaries, such that the latest one has the greater precedence.
    
    Parameters
    ----------

    l : list of dict
        List containing the dictionaries to be merged, having precedence on the last ones.
    
    Returns
    -------

    dict :
        The merged dictionary.
    """
    d = {}
    while True:
        if len(l) == 0:
            return {}
        if len(l) == 1:
            return l[0]
        d1 = l.pop(0)
        d2 = l.pop(0)
        d = deep_merge(d1,d2)
        l.insert(0, d)

def deep_merge(a, b):
    """
    Merge two values, with `b` taking precedence over `a`.

    Semantics:
    - If either `a` or `b` is not a dictionary, `a` will be returned only if
      `b` is `None`. Otherwise `b` will be returned.
    - If both values are dictionaries, they are merged as follows:
        * Each key that is found only in `a` or only in `b` will be included in
          the output collection with its value intact.
        * For any key in common between `a` and `b`, the corresponding values
          will be merged with the same semantics.

    From David Schneider answer at https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/15836901#15836901

    Parameters
    ----------

    a : object
    b : object

    Returns
    -------

    dict :
        Merged dictionary.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a if b is None else b
    else:
        # If we're here, both a and b must be dictionaries or subtypes thereof.

        # Compute set of all keys in both dictionaries.
        keys = set(a.keys()) | set(b.keys())

        # Build output dictionary, merging recursively values with common keys,
        # where `None` is used to mean the absence of a value.
        return {
            key: deep_merge(a.get(key), b.get(key))
            for key in keys
        }


def flatten(d, parent_key='', sep='.'):
    """Flatten the nested dictionary structure using the given separator.

    If parent_key is given, then that level is added at the start of the tree.

    Parameters
    ----------

    d : dict
        The dictionary to flat.
    parent_key : str, optional
        The optional top-level field of the dictionary.
    sep : str, optional
        The separator to indicate nesting/branching/hierarchy.

    Returns
    -------
    dict :
        A dictionary with only one level of fields.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def nested_notation_to_tree(key,value,leaf='.'):
    """Create a nested dictionary from the single (key,value) pair, with the key being branched by the leaf separator.
    
    Parameters
    ----------
    key : str
        The key/field to be nested, assuming nesting is represented with the "leaf" parameters.
    value : object
        The value that it will have at the last level of nesting.
    leaf : str, optional
        The separator used to indicate nesting in "key" parameter.
    
    Returns
    -------

    dict :
        Nested dictionary.
    """
    if leaf in key:
        tree_list = key.split(leaf)
        tree_dict = value
        for key in reversed(tree_list):
            tree_dict = {key: tree_dict}
        return tree_dict
    else:
        return {key:value}
