"""Tests that pathlib.Path objects are accepted wherever str paths are accepted."""
import os
from pathlib import Path

import pytest

from sovabids.parsers import (
    find_bidsroot,
    parse_entities_from_bidspath,
    parse_entity_from_bidspath,
    parse_path_pattern_from_entities,
)
from sovabids.heuristics import from_io_example
from sovabids.files import _get_files, _write_yaml


# ---------------------------------------------------------------------------
# parsers
# ---------------------------------------------------------------------------

def test_parse_entity_from_bidspath_path():
    p = 'y:/bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr'
    assert parse_entity_from_bidspath(p, 'sub') == parse_entity_from_bidspath(Path(p), 'sub')


def test_parse_entities_from_bidspath_path():
    p = 'y:/bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr'
    assert parse_entities_from_bidspath(p) == parse_entities_from_bidspath(Path(p))


def test_parse_path_pattern_from_entities_path():
    source = 'data/lemon/session009/taskT001/010002.vhdr'
    entities = {'sub': '010002', 'task': 'T001', 'ses': '009'}
    assert (
        parse_path_pattern_from_entities(source, entities)
        == parse_path_pattern_from_entities(Path(source), entities)
    )


def test_find_bidsroot_path():
    p = 'y:/code/sovabids/_data/DUMMY/DUMMY_BIDS/sub-SU0/ses-SE0/eeg/sub-SU0_ses-SE0_task-TA0_acq-AC0_run-0_eeg.vhdr'
    assert find_bidsroot(p) == find_bidsroot(Path(p))


# ---------------------------------------------------------------------------
# heuristics
# ---------------------------------------------------------------------------

def test_from_io_example_path():
    source = 'data/lemon/V001/resting/010002.vhdr'
    target = 'data_bids/sub-010002/ses-001/eeg/sub-010002_ses-001_task-resting_eeg.vhdr'
    expected = from_io_example(source, target)
    assert from_io_example(Path(source), target) == expected
    assert from_io_example(source, Path(target)) == expected
    assert from_io_example(Path(source), Path(target)) == expected


# ---------------------------------------------------------------------------
# files
# ---------------------------------------------------------------------------

def test_get_files_path(tmp_path):
    (tmp_path / 'a.txt').write_text('x')
    (tmp_path / 'b.txt').write_text('y')
    str_result = sorted(_get_files(str(tmp_path)))
    path_result = sorted(_get_files(tmp_path))
    assert str_result == path_result


def test_write_yaml_path(tmp_path):
    data = {'key': 'value'}
    out = tmp_path / 'sub' / 'out.yml'
    _write_yaml(data, out)
    assert out.exists()
