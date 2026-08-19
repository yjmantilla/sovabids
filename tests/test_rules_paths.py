"""#94 — source/BIDS/mappings paths must expand ``~`` and ``$VARS`` instead of
being used literally (which silently creates a directory named e.g. ``$HOME``)."""
import os

import pytest

from sovabids.rules import _expand_path, get_files


def test_expand_path_user_and_vars(monkeypatch):
    monkeypatch.setenv("SOVA_TEST_VAR", "/opt/data")
    assert _expand_path("$SOVA_TEST_VAR/sub") == "/opt/data/sub"
    assert _expand_path("${SOVA_TEST_VAR}/sub") == "/opt/data/sub"
    assert _expand_path("~/x") == os.path.expanduser("~/x")
    # non-strings pass through untouched
    assert _expand_path(None) is None
    assert _expand_path(123) == 123


def test_get_files_expands_env_var_source(tmp_path, monkeypatch):
    """A source path given via ``$VAR`` (as it might come from a rules/mappings YAML)
    is expanded, so the files are actually found and returned with real paths."""
    (tmp_path / "sub-01_task-rest.vhdr").write_text("")
    monkeypatch.setenv("SOVA_TEST_SRC", str(tmp_path))
    files = get_files("$SOVA_TEST_SRC", {"non-bids": {"eeg_extension": ".vhdr"}})
    assert any(f.endswith("sub-01_task-rest.vhdr") for f in files)
    assert all("$" not in f for f in files)          # no literal "$SOVA_TEST_SRC" left


def test_convert_them_expands_paths(tmp_path, monkeypatch):
    """A ``$VAR`` target in the mappings must be expanded, not turned into a literal
    ``$VAR`` directory under the working dir (the reported failure)."""
    from sovabids.convert import convert_them

    out = tmp_path / "bids"
    out.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)                            # so any literal write lands here
    monkeypatch.setenv("SOVA_TEST_OUT", str(out))
    mappings = {
        "General": {"IO": {"target": "$SOVA_TEST_OUT", "source": "$SOVA_TEST_OUT"}},
        "Individual": [],
    }
    convert_them(mappings)
    assert (out / "code" / "sovabids").is_dir()       # log tree at the EXPANDED path
    assert not (cwd / "$SOVA_TEST_OUT").exists()      # not a literal "$VAR" directory


def test_convert_them_expands_per_file_io(tmp_path, monkeypatch):
    """Each mapping's IO.source/target are expanded before use — not just the General
    paths — so removing that expansion would fail here (empty-Individual can't) (#94)."""
    import sovabids.convert as sc

    out = tmp_path / "bids"
    out.mkdir()
    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setenv("SOVA_OUT", str(out))
    monkeypatch.setenv("SOVA_SRC", str(src))
    captured = {}

    def fake_single(input_file, mapping, bids_path, write=False):
        captured["input"] = input_file
        captured["bids"] = bids_path

    monkeypatch.setattr(sc, "apply_rules_to_single_file", fake_single)
    mappings = {
        "General": {"IO": {"target": "$SOVA_OUT", "source": "$SOVA_SRC"}},
        "Individual": [{"IO": {"source": "$SOVA_SRC/a.vhdr", "target": "$SOVA_OUT/x/a.vhdr"}}],
    }
    sc.convert_them(mappings)
    assert "$" not in captured["input"]                       # per-file IO.source expanded
    assert captured["input"] == str(src / "a.vhdr")
    assert captured["bids"] == str(out)                       # General target expanded
