"""Regression tests for issue #92 — YAML ``pattern`` examples in the docs must be loadable.

A plain YAML scalar cannot begin with ``%`` (a reserved indicator character), so any ``pattern:``
value that starts with ``%`` must be quoted. This slipped through because our other tests exercise
``%``-leading patterns as Python strings (never through a YAML loader) and every shipped rules fixture
happens to start with an ordinary character.

Both ``%``-leading doc examples are kept as real fixtures that are rendered into the docs via
``literalinclude`` and loaded here through the real loader, so the docs and the tested file cannot drift
apart: ``examples/quickstart_rules.yml`` (quickstart) and ``examples/operation_example_rules.yml`` (the
operation example in the rules-schema docs).
"""
import json
import os

import pytest

from sovabids.rules import load_rules

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
QUICKSTART_RULES = os.path.join(REPO_ROOT, "examples", "quickstart_rules.yml")
OPERATION_RULES = os.path.join(REPO_ROOT, "examples", "operation_example_rules.yml")


def _load_snippet_through_rules(tmp_path, snippet):
    """Write a YAML snippet and load it through the production rules path."""
    rules_file = tmp_path / "rules.yml"
    rules_file.write_text(snippet, encoding="utf-8")
    return load_rules(rules_file)


def test_quickstart_fixture_loads_through_real_loader():
    """The quickstart rules example shown in the docs loads via ``load_rules`` (not just safe_load)."""
    rules = load_rules(QUICKSTART_RULES)
    assert isinstance(rules, dict)
    assert rules["non-bids"]["path_analysis"]["pattern"] == "%ignore%/sub-%entities.subject%.vhdr"


def test_operation_example_fixture_loads_through_real_loader():
    """The rules-schema operation example is a real fixture too (drift-locked like the quickstart).

    It is the second ``%``-leading site the reviewer named. Because the docs render this exact file via
    ``literalinclude`` and this test loads the same file, un-quoting the pattern in the docs would fail
    here — the doc example and the tested file cannot silently diverge.
    """
    rules = load_rules(OPERATION_RULES)
    assert isinstance(rules, dict)
    assert rules["non-bids"]["path_analysis"]["pattern"] == "%a%_%b%_%entities.task%.set"


@pytest.mark.parametrize("snippet", [
    "pattern: %ignore%/sub-%entities.subject%.vhdr",   # quickstart example (unquoted)
    "pattern: %a%_%b%_%entities.task%.set",            # rules_schema operation example (unquoted)
])
def test_unquoted_percent_leading_pattern_is_invalid_yaml(snippet, tmp_path):
    """The production loader must reject an unquoted ``%``-leading pattern, and now
    surface (and chain) the real YAML cause instead of hiding it (#95)."""
    import yaml as _yaml
    with pytest.raises(OSError, match="Couldnt read .* file as a rule file") as excinfo:
        _load_snippet_through_rules(tmp_path, snippet)
    # the underlying YAML parse error is chained and included in the message (#95)
    assert isinstance(excinfo.value.__cause__, _yaml.YAMLError)
    assert str(excinfo.value.__cause__) in str(excinfo.value)


@pytest.mark.parametrize("snippet,expected", [
    ('pattern: "%ignore%/sub-%entities.subject%.vhdr"', "%ignore%/sub-%entities.subject%.vhdr"),
    ('pattern: "%a%_%b%_%entities.task%.set"', "%a%_%b%_%entities.task%.set"),
])
def test_quoted_percent_leading_pattern_parses_and_preserves_string(snippet, expected, tmp_path):
    """The production loader preserves a quoted ``%``-leading pattern."""
    assert _load_snippet_through_rules(tmp_path, snippet) == {"pattern": expected}


def test_quickstart_example_runs_end_to_end(tmp_path):
    """RUN the documented quickstart example on a simulated dataset (not just parse it).

    This is the answer to "is the example actually tested?": it loads the *real* quickstart rules
    fixture (the exact file the docs render via ``literalinclude``), simulates a tiny BrainVision
    dataset laid out to match its ``%ignore%/sub-%entities.subject%.vhdr`` pattern, then performs the
    quickstart's Steps 3-4 for real — ``apply_rules`` (source -> mappings) and ``convert_them``
    (mappings -> BIDS) — and checks a valid BIDS dataset lands on disk. So the documented example is
    exercised end to end, not merely loaded.
    """
    from bids_validator import BIDSValidator

    from sovabids.datasets import make_dummy_dataset, save_dummy_vhdr
    from sovabids.rules import apply_rules
    from sovabids.convert import convert_them

    rules = load_rules(QUICKSTART_RULES)  # the exact documented example

    source_root = str(tmp_path / "source")
    bids_root = str(tmp_path / "bids")
    os.makedirs(source_root, exist_ok=True)
    os.makedirs(bids_root, exist_ok=True)

    # Simulate a source dataset matching the fixture's pattern: <dir>/sub-<subject>.vhdr
    example = save_dummy_vhdr(str(tmp_path / "dummy.vhdr"))
    make_dummy_dataset(
        EXAMPLE=example,
        PATTERN="%dataset%/sub-%subject%",   # -> DUMMY/sub-SU0.vhdr, DUMMY/sub-SU1.vhdr
        DATASET="DUMMY",
        NSUBS=2, NSESSIONS=1, NTASKS=1, NRUNS=1, NACQS=1,
        ROOT=source_root,
    )

    # Step 3 — generate mappings by applying the real quickstart rules
    mappings = apply_rules(source_path=source_root, bids_path=bids_root, rules=rules)
    individual = mappings["Individual"]
    assert len(individual) == 2, f"expected 2 mapped files, got {len(individual)}"

    # Targets are valid BIDS; subject came from the pattern, task ('resting') from the fixture
    validator = BIDSValidator()
    rels = [m["IO"]["target"].replace(bids_root, "") for m in individual]
    for rel in rels:
        assert validator.is_bids(rel), f"{rel} is not a valid BIDS path"
        assert "task-resting" in rel
    assert any("sub-SU0" in rel for rel in rels)
    assert any("sub-SU1" in rel for rel in rels)

    # Step 4 — actually convert to BIDS and confirm the dataset landed on disk
    convert_them(mappings)

    dd = os.path.join(bids_root, "dataset_description.json")
    assert os.path.isfile(dd)
    with open(dd) as fh:
        assert json.load(fh)["Name"] == "MyDataset"  # from the fixture's dataset_description
    for sub in ("SU0", "SU1"):
        eeg = os.path.join(bids_root, f"sub-{sub}", "eeg", f"sub-{sub}_task-resting_eeg.vhdr")
        assert os.path.isfile(eeg), f"missing converted file {eeg}"
