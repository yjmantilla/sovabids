"""Tests for error handling during conversion."""

import re
from copy import deepcopy

import pytest

from sovabids.convert import convert_them
from sovabids.rules import apply_rules_to_single_file

from .test_formats import _make_raw, _rules, _write_raw


def _mappings(good_mapping, bad_source, bids_dir):
    bad = deepcopy(good_mapping)
    bad["IO"]["source"] = bad_source
    bad["IO"]["target"] = str(bids_dir / "sub-99" / "eeg" / "sub-99_task-test_eeg.vhdr")
    return {
        "General": {
            "IO": {"source": good_mapping["IO"]["source"], "target": str(bids_dir)},
            "dataset_description": {"Name": "ErrorTest"},
        },
        "Individual": [good_mapping, bad],
    }


def test_convert_them_partial_failure(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    bids = tmp_path / "bids"
    bids.mkdir()

    raw = _make_raw()
    fname = source / "01.vhdr"
    _write_raw(raw, fname, "vhdr")

    rules = _rules("vhdr", source, bids)
    good_mapping, _ = apply_rules_to_single_file(str(fname), rules, str(bids), write=False)

    bad_source = str(source / "nonexistent.vhdr")
    mappings = _mappings(good_mapping, bad_source, bids)

    result = convert_them(mappings)

    assert result["succeeded"] == [str(fname)]
    assert result["failed"] == [bad_source]
    assert any(bids.rglob("sub-01*eeg.json")), "Good file was not converted"
