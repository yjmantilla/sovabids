"""
Secure built-in transformations for Sovabids.

This module provides safe alternatives to code execution functionality,
including string operations and predefined raw object processing functions.
"""

import re
import logging
from typing import Any, Dict, List, Union, Callable
from mne.io import BaseRaw

LOGGER = logging.getLogger(__name__)

# Registry of available raw processing functions
RAW_FUNCTIONS = {}

def register_raw_function(name: str):
    """Decorator to register a raw processing function."""
    def decorator(func: Callable[[BaseRaw], BaseRaw]):
        RAW_FUNCTIONS[name] = func
        return func
    return decorator

def safe_string_concatenation(expression: str, variables: Dict[str, Any]) -> str:
    """
    Safely concatenate strings using [variable] syntax with + operator support.
    
    The function handles:
    - [variable] substitution from the variables dictionary
    - + operator for concatenation (splits on + and joins parts)
    - Literal text (anything not in brackets)
    - Ignores spaces around + operator
    
    Parameters
    ----------
    expression : str
        Expression like "[a] + [b]", "[subject]_[session]", or "prefix + [var] + suffix"
    variables : dict
        Dictionary containing variable values
        
    Returns
    -------
    str
        Concatenated result
        
    Examples
    --------
    >>> variables = {'subject': '001', 'session': 'ses1'}
    >>> safe_string_concatenation("[subject] + [session]", variables)
    '001ses1'
    >>> safe_string_concatenation("sub + [subject]", variables)
    'sub001'
    >>> safe_string_concatenation("[subject]_[session]", variables)
    '001_ses1'
    """
    if not isinstance(expression, str):
        return str(expression)
    
    # Handle + operator by splitting and processing each part
    if '+' in expression:
        # Split on + operator, ignoring spaces
        parts = [part.strip() for part in expression.split('+')]
        processed_parts = []
        
        for part in parts:
            # Process [variable] substitutions in each part
            processed_part = _substitute_variables(part, variables)
            processed_parts.append(processed_part)
        
        # Concatenate all parts
        return ''.join(processed_parts)
    else:
        # No + operator, just do variable substitution
        return _substitute_variables(expression, variables)

def _substitute_variables(text: str, variables: Dict[str, Any]) -> str:
    """
    Substitute [variable] patterns in text with values from variables dict.
    
    Parameters
    ----------
    text : str
        Text containing [variable] patterns
    variables : dict
        Dictionary containing variable values
        
    Returns
    -------
    str
        Text with variables substituted
    """
    # Find all [variable] patterns
    pattern = r'\[([^\]]+)\]'
    matches = re.findall(pattern, text)
    
    result = text
    for match in matches:
        # Get nested value using dot notation (e.g., entities.subject)
        value = _get_nested_value(variables, match)
        exists = _variable_exists(variables, match)
        
        if exists:
            # Variable exists (even if None), substitute it
            result = result.replace(f'[{match}]', str(value) if value is not None else 'None')
        else:
            # Variable doesn't exist, keep placeholder and warn
            LOGGER.warning(f"Variable '{match}' not found in context, keeping placeholder")
    
    return result

def _variable_exists(data: Dict[str, Any], key: str) -> bool:
    """Check if a variable exists in the data dictionary using dot notation."""
    if '.' not in key:
        return key in data
    
    keys = key.split('.')
    current = data
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return False
    
    return True

def _get_nested_value(data: Dict[str, Any], key: str) -> Any:
    """Get nested dictionary value using dot notation."""
    if '.' not in key:
        return data.get(key)
    
    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    
    return value

def apply_safe_transformations(operations: Dict[str, str], variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply safe transformations to variables.
    
    Parameters
    ----------
    operations : dict
        Dictionary of key: expression pairs
    variables : dict
        Available variables for transformation
        
    Returns
    -------
    dict
        Transformed variables
    """
    if operations is None:
        return {}
    
    if not isinstance(operations, dict):
        LOGGER.warning(f"Operations must be a dictionary, got {type(operations)}")
        return {}
    
    results = {}
    
    for key, expression in operations.items():
        try:
            result = safe_string_concatenation(expression, variables)
            results[key] = result
            LOGGER.debug(f"Transformation '{key}': '{expression}' -> '{result}'")
        except Exception as e:
            LOGGER.warning(f"Failed to apply transformation '{key}': {e}")
            results[key] = expression  # Fallback to original
    
    return results

def execute_safe_raw_functions(function_names: List[str], raw: BaseRaw) -> BaseRaw:
    """
    Execute predefined safe functions on raw object.
    
    Parameters
    ----------
    function_names : list
        List of registered function names to execute
    raw : BaseRaw
        MNE Raw object
        
    Returns
    -------
    BaseRaw
        Processed raw object
    """
    if function_names is None:
        return raw
    
    if not isinstance(function_names, (list, tuple)):
        LOGGER.warning(f"Function names must be a list, got {type(function_names)}")
        return raw
    
    for func_name in function_names:
        if func_name in RAW_FUNCTIONS:
            try:
                LOGGER.info(f"Executing registered function: {func_name}")
                raw = RAW_FUNCTIONS[func_name](raw)
            except Exception as e:
                LOGGER.error(f"Error executing function '{func_name}': {e}")
        else:
            LOGGER.warning(f"Unknown function '{func_name}'. Available functions: {list(RAW_FUNCTIONS.keys())}")
    
    return raw

# Built-in raw processing functions

@register_raw_function("print_info")
def print_raw_info(raw: BaseRaw) -> BaseRaw:
    """Print information about the raw object."""
    print("=== Raw Object Information ===")
    print(f"Sampling frequency: {raw.info['sfreq']} Hz")
    print(f"Number of channels: {raw.info['nchan']}")
    print(f"Duration: {raw.times[-1]:.2f} seconds")
    print(f"Channel names: {raw.ch_names[:10]}{'...' if len(raw.ch_names) > 10 else ''}")
    return raw

@register_raw_function("drop_bad_channels")
def drop_bad_channels(raw: BaseRaw) -> BaseRaw:
    """Drop channels marked as bad."""
    if raw.info['bads']:
        LOGGER.info(f"Dropping bad channels: {raw.info['bads']}")
        raw.drop_channels(raw.info['bads'])
    return raw

@register_raw_function("set_montage_standard_1020")
def set_standard_1020_montage(raw: BaseRaw) -> BaseRaw:
    """Set standard 10-20 montage for EEG channels."""
    try:
        import mne
        montage = mne.channels.make_standard_montage('standard_1020')
        raw.set_montage(montage, match_case=False, on_missing='warn')
        LOGGER.info("Applied standard 10-20 montage")
    except Exception as e:
        LOGGER.warning(f"Could not set montage: {e}")
    return raw

@register_raw_function("filter_line_noise_50hz")
def filter_line_noise_50hz(raw: BaseRaw) -> BaseRaw:
    """Apply notch filter for 50Hz line noise."""
    raw.notch_filter(freqs=50, picks='eeg', method='fir', verbose=False)
    LOGGER.info("Applied 50Hz notch filter")
    return raw

@register_raw_function("filter_line_noise_60hz")
def filter_line_noise_60hz(raw: BaseRaw) -> BaseRaw:
    """Apply notch filter for 60Hz line noise."""
    raw.notch_filter(freqs=60, picks='eeg', method='fir', verbose=False)
    LOGGER.info("Applied 60Hz notch filter")
    return raw

@register_raw_function("resample_500hz")
def resample_500hz(raw: BaseRaw) -> BaseRaw:
    """Resample data to 500Hz."""
    if raw.info['sfreq'] != 500:
        raw.resample(500)
        LOGGER.info("Resampled to 500Hz")
    return raw

@register_raw_function("crop_to_10min")
def crop_to_10min(raw: BaseRaw) -> BaseRaw:
    """Crop recording to first 10 minutes."""
    max_time = min(600, raw.times[-1])  # 600 seconds = 10 minutes
    raw.crop(tmax=max_time)
    LOGGER.info(f"Cropped to {max_time/60:.1f} minutes")
    return raw

def get_available_functions() -> List[str]:
    """Get list of available raw processing functions."""
    return list(RAW_FUNCTIONS.keys())

def get_function_documentation() -> Dict[str, str]:
    """Get documentation for all available functions."""
    docs = {}
    for name, func in RAW_FUNCTIONS.items():
        docs[name] = func.__doc__ or "No documentation available"
    return docs