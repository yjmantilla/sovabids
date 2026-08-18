"""Regression guard for the ``sovatui`` entry point on a base install (issue #90).

``textual`` ships only with the ``sovabids[tui]`` extra, but ``sovatui`` is always
installed as a console script. A plain ``pip install sovabids`` must therefore give
an actionable "install the extra" message instead of a raw ``ModuleNotFoundError``
traceback. CI installs all extras, so this path is never exercised unless we simulate
``textual`` being absent on purpose.
"""
import subprocess
import sys
import textwrap

import pytest


def test_sovatui_missing_textual_exits_with_hint():
    """No ``textual`` -> non-zero exit with the ``sovabids[tui]`` hint, and no traceback."""
    bootstrap = textwrap.dedent(
        """
        import sys

        class _BlockTextual:
            def find_spec(self, name, path=None, target=None):
                if name == "textual" or name.startswith("textual."):
                    raise ModuleNotFoundError("No module named 'textual'", name="textual")
                return None

        sys.meta_path.insert(0, _BlockTextual())
        for _m in [k for k in list(sys.modules)
                   if k == "textual" or k.startswith("textual.") or k == "sovabids.tui"]:
            del sys.modules[_m]

        from sovabids.sovatui import main
        main()
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", bootstrap],
        capture_output=True,
        text=True,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, f"expected non-zero exit, got 0\n{combined}"
    assert "sovabids[tui]" in combined, combined
    # SystemExit(str) prints only the message; a raw ModuleNotFoundError would show a traceback.
    assert "Traceback" not in proc.stderr, proc.stderr
    assert "ModuleNotFoundError" not in combined, combined


def test_sovatui_delegates_when_textual_present(monkeypatch):
    """When ``textual`` is importable, the wrapper hands off to the real TUI entry point."""
    pytest.importorskip("textual")
    import sovabids.tui as tui

    calls = []
    monkeypatch.setattr(tui, "main", lambda: calls.append(True))

    import sovabids.sovatui as sovatui
    sovatui.main()  # must not raise SystemExit

    assert calls == [True]
