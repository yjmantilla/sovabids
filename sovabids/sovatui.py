"""Console-script entry point for the sovabids TUI (``sovatui``).

The TUI depends on the optional ``textual`` library, which is only installed with
the ``sovabids[tui]`` extra. :mod:`sovabids.tui` imports ``textual`` at module
level and uses its classes as base classes, so importing it under a plain
``pip install sovabids`` fails immediately with a raw ``ModuleNotFoundError``.

This thin wrapper is what ``sovatui`` points at, so a base install still gets a
short, actionable message telling the user how to install the extra instead of a
traceback.
"""
from __future__ import annotations


def main() -> None:
    """Launch the sovabids TUI, or explain how to install it if ``textual`` is missing."""
    try:
        from sovabids.tui import main as _run
    except ModuleNotFoundError as e:
        # Only intercept a missing ``textual`` — let any other import error
        # (including a broken/too-old ``textual`` that fails deeper) surface normally.
        if e.name == "textual":
            raise SystemExit(
                "The sovabids TUI needs the 'textual' package, which is not installed.\n"
                "Install it with:  pip install \"sovabids[tui]\""
            )
        raise
    _run()


if __name__ == "__main__":
    main()
