import sys
import pytest
from unittest.mock import patch
from sovabids.misc import handle_unicode_dashes, _UNICODE_DASHES


@pytest.fixture(autouse=True)
def restore_argv():
    original = sys.argv[:]
    yield
    sys.argv[:] = original


def test_no_unicode_dashes_unchanged():
    sys.argv = ['prog', '--flag', 'value', '-x']
    handle_unicode_dashes()
    assert sys.argv == ['prog', '--flag', 'value', '-x']


def test_em_dash_replaced():
    sys.argv = ['prog', '——flag']
    handle_unicode_dashes()
    assert sys.argv == ['prog', '--flag']


def test_en_dash_replaced():
    sys.argv = ['prog', '–flag']
    handle_unicode_dashes()
    assert sys.argv == ['prog', '-flag']


@pytest.mark.parametrize("dash_char", list(_UNICODE_DASHES.keys()))
def test_all_unicode_dashes_replaced(dash_char):
    sys.argv = ['prog', dash_char + dash_char + 'mapping', 'val']
    handle_unicode_dashes()
    assert sys.argv[1] == '--mapping'
    assert sys.argv[2] == 'val'


def test_argv_0_not_touched():
    # sys.argv[0] is the program name — never modify it
    sys.argv = ['—prog', '--flag']
    handle_unicode_dashes()
    assert sys.argv[0] == '—prog'
    assert sys.argv[1] == '--flag'


def test_warning_printed_on_replacement(capsys):
    sys.argv = ['prog', '——flag']
    handle_unicode_dashes()
    out = capsys.readouterr().out
    assert 'WARNING' in out
    assert 'U+2014' in out


def test_no_warning_when_clean(capsys):
    sys.argv = ['prog', '--flag', 'value']
    handle_unicode_dashes()
    out = capsys.readouterr().out
    assert out == ''


def test_mixed_args_only_affected_reported(capsys):
    sys.argv = ['prog', '--clean', '——dirty', 'val']
    handle_unicode_dashes()
    assert sys.argv == ['prog', '--clean', '--dirty', 'val']
    out = capsys.readouterr().out
    assert '--clean' not in out
    assert 'dirty' in out


def test_value_arg_with_dash_in_content():
    # Dash inside a value (not a flag) should also be replaced
    sys.argv = ['prog', '--flag', 'file—name']
    handle_unicode_dashes()
    assert sys.argv == ['prog', '--flag', 'file-name']
