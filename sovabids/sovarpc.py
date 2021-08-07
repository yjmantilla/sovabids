"""
- [x] apply_rules
- [x] load_rules
- [x] save_rules
- [x] apply_rules_to_single_file
- [x] convert
- [x] save_mappings
- [x] get_files
"""

import traceback
import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel, errors
from typing import List, Optional
import sovabids.rules as ru
import sovabids.convert as co
import sovabids.files as fi

app = jsonrpc.API()

api = jsonrpc.Entrypoint('/api/sovabids')

class RulesError(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'Error loading the rules.'

    class DataModel(BaseModel):
        details: str

class ApplyError(jsonrpc.BaseError):
    CODE = 5100
    MESSAGE = 'Error applying rules.'

    class DataModel(BaseModel):
        details: str

class ConvertError(jsonrpc.BaseError):
    CODE = 5200
    MESSAGE = 'Error converting  files.'

    class DataModel(BaseModel):
        details: str

class SaveError(jsonrpc.BaseError):
    CODE = 5300
    MESSAGE = 'Error saving file.'

    class DataModel(BaseModel):
        details: str

class FileListError(jsonrpc.BaseError):
    CODE = 5400
    MESSAGE = 'Error getting the filelist.'

    class DataModel(BaseModel):
        details: str


@api.method(errors=[ApplyError])
def apply_rules(
    file_list: List[str],
    bids_path: str,
    rules: dict,
    mapping_path: str
) -> dict:
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
    try:
        data = {'General':general,'Individual':individual}
        co.convert_them(mappings_input=data)
    except:
        raise ConvertError(data={'details': traceback.format_exc()})

@api.method(errors=[RulesError])
def load_rules(
    rules_path: str,
) -> dict:
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
    try:
        fi._write_yaml(path,rules)
    except:
        raise SaveError(data={'details': traceback.format_exc()})
    return

@api.method(errors=[SaveError])
def save_mappings(
    path:str,
    general:dict,
    individual:list
    ) -> None:
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