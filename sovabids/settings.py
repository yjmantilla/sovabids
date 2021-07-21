"""Module dealing with general settings and constants for the package."""
import os
from sovabids import __path__

SUPPORTED_EXTENSIONS = ['.set' ,'.cnt' ,'.vhdr' ,'.bdf','.edf' ,'.fif']
"""The current supported extensions of the package."""

NULL_VALUES = ['',None,{},[]]
"""The values to consider as NULL or NOT-AVAILABLE."""

SECTION_STRING = 11*'-'
"""A string intended to announce the start and end of a section in the logging."""

SOVABIDS_PATH = __path__[0]
"""The path of the package."""

REPO_PATH = os.path.realpath(os.path.join(SOVABIDS_PATH,'..'))
"""The path of the sovabids project, that is the root of the git repository. Needs that sovabids was installed in editable mode from the git repository.
"""
