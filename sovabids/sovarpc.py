# apply_rules
# load_rules
# save_rules
# apply_rules_to_single_file
# convert
# save_mappings
# get_files


import fastapi_jsonrpc as jsonrpc
from numpy import source
from pydantic import BaseModel
from fastapi import Body
import sovabids.rules as ru
import sovabids.convert as co

app = jsonrpc.API()

api_v1 = jsonrpc.Entrypoint('/api/v1/sovabids')


class MyError(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = 'My error'

    class DataModel(BaseModel):
        details: str

class RulesError(jsonrpc.BaseError):
    CODE = 5100
    MESSAGE = 'Error with the rules'

    class DataModel(BaseModel):
        details: str


@api_v1.method(errors=[MyError])
def apply_rules(
    source_path: str = Body(..., example='123'),
    bids_path: str = Body(..., example='123'),
    rules_path: str = Body(..., example='123'),
    mapping_path: str = Body(..., example='123')
) -> dict:
    try:
        data = ru.apply_rules(source_path=source_path,bids_path=bids_path,rules_=rules_path,mapping_path=mapping_path)
    except:
        raise MyError(data={'details': 'error'})
    return data

@api_v1.method(errors=[MyError])
def convert_them(
    mapping_path: str = Body(..., example='123')
) -> None:
    try:
        co.convert_them(mappings_input=mapping_path)
    except:
        raise MyError(data={'details': 'error'})

@api_v1.method(errors=[RulesError])
def load_rules(
    rules_path: str = Body(..., example='123'),
) -> dict:
    try:
        rules = ru.load_rules(rules_path)
    except:
        raise RulesError(data={'details': 'error'})
    return rules

@api_v1.method(errors=[MyError])
def apply_rules_to_single_file(
    data: str = Body(..., example='123'),
) -> str:
    if data == 'error':
        raise MyError(data={'details': 'error'})
    else:
        return data

app.bind_entrypoint(api_v1)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('sovarpc:app', port=5000, debug=True, access_log=False)