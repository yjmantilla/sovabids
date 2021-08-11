"""Errors for the RPC sovabids API
"""
import fastapi_jsonrpc as jsonrpc
from pydantic import BaseModel, errors

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
