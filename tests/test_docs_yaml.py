"""Regression tests for issue #92 — YAML ``pattern`` examples in the docs must be loadable.

A plain YAML scalar cannot begin with ``%`` (a reserved indicator character), so any ``pattern:``
value that starts with ``%`` must be quoted. This slipped through because our other tests exercise
``%``-leading patterns as Python strings (never through a YAML loader) and every shipped rules fixture
happens to start with an ordinary character.

The quickstart example is kept as a real fixture (``examples/quickstart_rules.yml``) that is both
rendered into the docs via ``literalinclude`` and loaded here through the real loader, so the docs and
the tested file cannot drift apart.
"""
import os

import pytest
import yaml

from sovabids.rules import load_rules

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
QUICKSTART_RULES = os.path.join(REPO_ROOT, "examples", "quickstart_rules.yml")


def test_quickstart_fixture_loads_through_real_loader():
    """The quickstart rules example shown in the docs loads via ``load_rules`` (not just safe_load)."""
    rules = load_rules(QUICKSTART_RULES)
    assert isinstance(rules, dict)
    assert rules["non-bids"]["path_analysis"]["pattern"] == "%ignore%/sub-%entities.subject%.vhdr"


@pytest.mark.parametrize("snippet", [
    "pattern: %ignore%/sub-%entities.subject%.vhdr",   # quickstart example (unquoted)
    "pattern: %a%_%b%_%entities.task%.set",            # rules_schema operation example (unquoted)
])
def test_unquoted_percent_leading_pattern_is_invalid_yaml(snippet):
    """An unquoted ``pattern`` beginning with ``%`` must fail to parse — this is the #92 bug."""
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(snippet)


@pytest.mark.parametrize("snippet,expected", [
    ('pattern: "%ignore%/sub-%entities.subject%.vhdr"', "%ignore%/sub-%entities.subject%.vhdr"),
    ('pattern: "%a%_%b%_%entities.task%.set"', "%a%_%b%_%entities.task%.set"),
])
def test_quoted_percent_leading_pattern_parses_and_preserves_string(snippet, expected):
    """Quoting makes the pattern valid and preserves the exact string."""
    assert yaml.safe_load(snippet) == {"pattern": expected}
