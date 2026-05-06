"""Smoke test: one file per supported MNE format converts to BIDS."""

import re

import mne
import numpy as np
import pytest

from sovabids.rules import apply_rules_to_single_file

# (extension, optional_dep_required_to_write_it)
FORMATS = [
    ("vhdr", "pybv"),
    ("edf", "edfio"),
    ("set", "eeglabio"),
    ("fif", None),
]


def _make_raw():
    sfreq = 256
    data = np.random.RandomState(0).randn(4, sfreq * 5) * 1e-6
    info = mne.create_info(["Fp1", "Fp2", "Cz", "Oz"], sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info)
    # EDF requires date in [1985, 2084]; epoch 0 = 1970
    from datetime import datetime, timezone
    raw.set_meas_date(datetime(2000, 1, 1, tzinfo=timezone.utc))
    # EEGLAB→BIDS needs fiducials; standard_1020 includes them
    raw.set_montage(mne.channels.make_standard_montage("standard_1020"))
    return raw


def _write_raw(raw, path, ext):
    if ext == "fif":
        raw.save(str(path), overwrite=True)
    else:
        mne.export.export_raw(str(path), raw, overwrite=True)


def _rules(ext, source_dir, bids_dir):
    # Use regex mode anchored to source_dir so tmp_path dir name can't pollute capture.
    # Placeholder mode leaves '.' unescaped which causes false matches on dir names.
    pattern = re.escape(str(source_dir)) + r"/([^/]+)\." + ext
    return {
        "entities": {"task": "test"},
        "dataset_description": {"Name": "FormatTest"},
        "sidecar": {"PowerLineFrequency": 50},
        "channels": {},
        "non-bids": {
            "eeg_extension": f".{ext}",
            "path_analysis": {
                "pattern": pattern,
                "fields": ["entities.subject"],
            },
        },
        "IO": {"source": str(source_dir), "target": str(bids_dir)},
    }


@pytest.mark.parametrize("ext,dep", FORMATS, ids=[f[0] for f in FORMATS])
def test_format_to_bids(ext, dep, tmp_path):
    if dep:
        pytest.importorskip(dep)

    source = tmp_path / "source"
    source.mkdir()
    bids = tmp_path / "bids"
    bids.mkdir()

    raw = _make_raw()
    fname = source / f"01.{ext}"
    _write_raw(raw, fname, ext)

    rules = _rules(ext, source, bids)
    mapping, _ = apply_rules_to_single_file(str(fname), rules, str(bids), write=True)

    assert mapping["entities"]["subject"] == "01"
    assert any(bids.rglob("sub-01*eeg.json")), "No EEG sidecar written to BIDS"


def test_meg_to_bids(tmp_path):
    from datetime import datetime, timezone

    source = tmp_path / "source"
    source.mkdir()
    bids = tmp_path / "bids"
    bids.mkdir()

    sfreq = 256
    data = np.random.RandomState(1).randn(4, sfreq * 5) * 1e-12
    info = mne.create_info(["MEG001", "MEG002", "MEG003", "MEG004"], sfreq, ch_types="grad")
    raw = mne.io.RawArray(data, info)
    raw.set_meas_date(datetime(2000, 1, 1, tzinfo=timezone.utc))

    fname = source / "01.fif"
    raw.save(str(fname), overwrite=True)

    pattern = re.escape(str(source)) + r"/([^/]+)\.fif"
    rules = {
        "entities": {"task": "test"},
        "dataset_description": {"Name": "MEGTest"},
        "sidecar": {},
        "channels": {},
        "non-bids": {
            "eeg_extension": ".fif",
            "path_analysis": {"pattern": pattern, "fields": ["entities.subject"]},
        },
        "IO": {"source": str(source), "target": str(bids)},
    }

    mapping, _ = apply_rules_to_single_file(str(fname), rules, str(bids), write=True)

    assert mapping["entities"]["subject"] == "01"
    assert any(bids.rglob("sub-01*meg.json")), "No MEG sidecar written to BIDS"
