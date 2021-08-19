"""
Action Oriented RPC API for Sovabids.
"""

import traceback
import fastapi_jsonrpc as jsonrpc
from typing import List, Optional
import sovabids.rules as ru
import sovabids.convert as co
import sovabids.files as fi
from sovabids.errors import ApplyError,ConvertError,SaveError,RulesError,FileListError
app = jsonrpc.API()

api = jsonrpc.Entrypoint('/api/sovabids')


# Sadly we will need to manage the docstring of these methods by hand since the fastapi documentation
# Does not support sphinx references
@api.method(errors=[ApplyError])
def apply_rules(
    file_list: List[str],
    bids_path: str,
    rules: dict,
    mapping_path: str
) -> dict:
    """Apply rules to a set of files.

    Parameters
    ----------

    file_list : list of str
        List of str with the paths of the files we want to convert (ie the output of get_files).
    bids_path : str
        The path we want the converted files in.
    rules : dict
        A dictionary with the rules.
    mapping_path : str, optional
        The fullpath where we want to write the mappings file.
        If '', then bids_path/code/sovabids/mappings.yml will be used.
    
    Returns
    -------

    dict :
        A dictionary following: {
                                    'General': rules given,
                                    'Individual':list of mapping dictionaries for each file
                                }
    

    Notes
    -----
    A wrapper of around rules.apply_rules function.
    See docstring of :py:func:`apply_rules() <rules.apply_rules>` in :py:mod:`rules`
    """
    try:
        mappings = ru.apply_rules(source_path=file_list,bids_path=bids_path,rules=rules,mapping_path=mapping_path)
    except:
        raise ApplyError(data={'details': traceback.format_exc()})
    return mappings

@api.method(errors=[ConvertError])
def convert_them(
    general  : dict,
    individual: List[dict]
) -> None:
    """Convert eeg files to bids according to the mappings given.

    Parameters
    ----------
    general : dict
        The general rules
    individual:  list[dict]
        List with the individual mappings of each file.

    Notes
    -----
    A wrapper of around convert.convert_them function.

    See docstring of :py:func:`convert_them() <convert.convert_them>` in :py:mod:`convert`

    Returns
    -------
    None
    """
    try:
        data = {'General':general,'Individual':individual}
        co.convert_them(mappings_input=data)
    except:
        raise ConvertError(data={'details': traceback.format_exc()})

@api.method(errors=[RulesError])
def load_rules(
    rules_path: str,
) -> dict:
    """Load rules from a path.

    Parameters
    ----------
    
    rules_path : str
        The path to the rules file.

    Returns
    -------

    dict
        The rules dictionary.
    
    Notes
    -----
    A wrapper of around rules.load_rules function.

    See docstring of :py:func:`load_rules() <rules.load_rules>` in :py:mod:`rules`
    """

    try:
        rules = ru.load_rules(rules_path)
    except:
        raise RulesError(data={'details': traceback.format_exc()})
    return rules

@api.method(errors=[ApplyError])
def apply_rules_to_single_file(
    file:str,
    rules:dict,
    bids_path:str,
    write:bool=False,
    preview:bool=False
) -> dict:
    """Apply rules to a single file.

    Parameters
    ----------

    file : str
        Path to the file.
    rules : dict
        The rules dictionary.
    bids_path : str
        Path to the bids directory
    write : bool, optional
        Whether to write the converted files to disk or not.
    preview : bool, optional
        Whether to return a dictionary with a "preview" of the conversion.
        This dict will have the same schema as the "Mapping File Schema" but may have flat versions of its fields.
        *UNDER CONSTRUCTION*

    Returns
    -------
    
    dict:
        {
        mapping : dict
            The mapping obtained from applying the rules to the given file
        preview : bool|dict
            If preview = False, then False. If True, then the preview dictionary.
        }

    Notes
    -----
    A wrapper of around rules.apply_rules_to_single_file function.

    See docstring of :py:func:`apply_rules_to_single_file() <rules.apply_rules_to_single_file>` in :py:mod:`rules`
    """

    try:
        mapping,preview=ru.apply_rules_to_single_file(file,rules,bids_path,write,preview)
    except:
        raise ApplyError(data={'details': traceback.format_exc()})
    return {'mapping':mapping,'preview':preview}

@api.method(errors=[SaveError])
def save_rules(
    rules:dict,
    path:str
    ) -> None:
    """Save rules as a yaml file to a path.

    Parameters
    ----------
    rules: dict
        The rules dictionary to save
    path : str
        The full-path (including filename) where to save the rules as yaml.

    Returns
    -------

    None

    Notes
    -----

    A wrapper of around files._write_yaml function.

    See docstring of :py:func:`_write_yaml() <files._write_yaml>` in :py:mod:`files`
    """

    try:
        fi._write_yaml(path,rules)
    except:
        raise SaveError(data={'details': traceback.format_exc()})
    return

@api.method(errors=[SaveError])
def save_mappings(
    path:str,
    general:dict,
    individual:List[dict]
    ) -> None:
    """Save mappings as a yaml file to a path.

    Parameters
    ----------

    path : str
        The full-path (including filename) where to save the mappings as yaml.
    general: dict
        The general rules dictionary.
    individual: list of dict
        A list containing the mapping dictionary of each file.

    Returns
    -------

    None

    Notes
    -----

    A wrapper of around files._write_yaml function.

    See docstring of :py:func:`_write_yaml() <files._write_yaml>` in :py:mod:`files`
    """

    try:
        data = {'General':general,'Individual':individual}
        fi._write_yaml(path,data)
    except:
        raise SaveError(data={'details': traceback.format_exc()})
    return

@api.method(errors=[FileListError])
def get_files(
    path:str,
    rules:dict
    ) -> list:
    """Recursively scan the directory for valid files, returning a list with the full-paths to each.
    
    The valid files are given by the 'non-bids.eeg_extension' rule. See the "Rules File Schema".

    Parameters
    ----------

    path : str
        The path we want to obtain the files from.
    rules : dict
        The rules dictionary.

    Returns
    -------

    list[str]:
        A list containing the path to each valid file in the source_path.


    Notes
    -----

    A wrapper of around rules.get_files function.

    See docstring of :py:func:`get_files() <rules.get_files>` in :py:mod:`rules`
    """

    try:
        filelist = ru.get_files(path,rules)
    except:
        raise FileListError(data={'details': traceback.format_exc()})
    return filelist


app.bind_entrypoint(api)

def main(entry='sovarpc:app',port=5000,debug=False):
    import uvicorn
    uvicorn.run(entry, port=port, debug=debug, access_log=False)

if __name__ == '__main__':
    main(port=5100)