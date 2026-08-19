"""Terminal User Interface for sovabids."""
from __future__ import annotations

import os
import threading
import time
from copy import deepcopy
from typing import ClassVar

import yaml
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.validation import ValidationResult, Validator
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    RichLog,
    Rule,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from sovabids.settings import SUPPORTED_EXTENSIONS


# ── Directory picker modal ────────────────────────────────────────────────────

def _tree_root(start: str) -> str:
    """Return a valid *directory* to root a ``DirectoryTree`` at.

    A ``DirectoryTree`` root must be a directory, so normalize the seed value:
    a file opens at its parent directory (fixes reopening a picker whose input
    already holds a file path), and an empty / nonexistent path falls back to
    the nearest existing ancestor, then the home directory.
    """
    if not start:
        return os.path.expanduser("~")
    path = os.path.abspath(os.path.expanduser(start))
    if os.path.isdir(path):
        return path
    if os.path.isfile(path):
        return os.path.dirname(path)
    parent = os.path.dirname(path)
    while parent and not os.path.isdir(parent):
        parent = os.path.dirname(parent)
    return parent or os.path.expanduser("~")


class FSPickerScreen(ModalScreen[str]):
    """Base filesystem browser modal: an editable location bar + an Up button + a
    ``DirectoryTree``, so the user can navigate anywhere (not just below the seed
    folder). Subclasses decide whether OK returns a directory or a file.
    """

    DEFAULT_CSS = """
    FSPickerScreen {
        align: center middle;
    }
    FSPickerScreen > Vertical {
        width: 80%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    FSPickerScreen DirectoryTree {
        height: 1fr;
    }
    FSPickerScreen Label {
        height: 1;
        margin-bottom: 1;
    }
    FSPickerScreen .loc-row {
        height: 3;
    }
    FSPickerScreen .loc-row Input {
        width: 1fr;
    }
    FSPickerScreen .newdir-row {
        height: 3;
    }
    FSPickerScreen .newdir-row Input {
        width: 1fr;
    }
    FSPickerScreen .btn-row {
        height: 3;
        align: right middle;
    }
    FSPickerScreen Button {
        margin-left: 1;
    }
    """

    _prompt: ClassVar[str] = "Select a path:"
    _DOUBLE_CLICK_SECONDS: ClassVar[float] = 0.5

    def __init__(self, start: str = ".") -> None:
        super().__init__()
        self._selected = ""
        self._root = _tree_root(start)
        self._last_dir = ""
        self._last_dir_t = 0.0

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._prompt, id="fs-status")
            with Horizontal(classes="loc-row"):
                yield Input(value=self._root, id="loc-input")
                yield Button("Up", id="go-up", variant="default")
            yield from self._extra_controls()
            yield DirectoryTree(self._root, id="fs-tree")
            with Horizontal(classes="btn-row"):
                yield Button("Cancel", id="cancel", variant="default")
                yield Button("OK", id="ok", variant="primary")

    def _extra_controls(self) -> list:
        """Widgets to place between the location bar and the tree. Base: none."""
        return []

    def _reroot(self, path: str) -> None:
        """Point the tree (and the location bar) at ``path``'s nearest directory."""
        root = _tree_root(path)
        self._root = root
        # Navigating away invalidates any earlier single-click selection, so OK
        # can't return a folder the user has since moved away from. Paths that do
        # mean to select (double-click, make-folder) re-select right after this.
        self._selected = ""
        try:
            self.query_one("#ok", Button).label = "OK"
        except Exception:
            pass
        tree = self.query_one("#fs-tree", DirectoryTree)
        tree.path = root
        tree.reload()
        self.query_one("#loc-input", Input).value = root

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "loc-input":
            self._reroot(event.value)
        elif event.input.id == "new-folder-name":
            self._make_folder()

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        # Double-click (same folder, quickly) navigates INTO the folder (re-roots).
        # A single selection is delegated to the subclass hook — the directory
        # picker marks it as the choice; the file picker deliberately ignores it,
        # so a directory can never become a file result (#89).
        path = str(event.path)
        now = time.monotonic()
        if path == self._last_dir and (now - self._last_dir_t) <= self._DOUBLE_CLICK_SECONDS:
            self._last_dir = ""
            self._reroot(path)             # enter the folder (clears selection)…
            self._on_dir_selected(path)    # …and re-select it (no-op for file mode)
            return
        self._last_dir, self._last_dir_t = path, now
        self._on_dir_selected(path)

    def _on_dir_selected(self, path: str) -> None:
        """Single-selection hook. Base does nothing (a file picker ignores directories)."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss("")
        elif event.button.id == "go-up":
            self._reroot(os.path.dirname(self._root))
        elif event.button.id == "mk-folder":
            self._make_folder()
        elif event.button.id == "ok":
            self._confirm()

    def _make_folder(self) -> None:
        """Create a folder named after the ``new-folder-name`` box inside the
        folder currently shown, then step into it and pre-select it. Only the
        directory picker renders that box, so file mode never reaches here."""
        try:
            box = self.query_one("#new-folder-name", Input)
        except Exception:
            return
        name = box.value.strip()
        if not name:
            return
        # Keep creation INSIDE the folder shown. Without this, os.path.join lets an
        # absolute name ("/etc/x") or traversal ("../x") escape the root and then
        # become the confirmed directory.
        if os.path.isabs(name) or name in (".", "..") or "/" in name or "\\" in name:
            self.query_one("#fs-status", Label).update(
                "[red]Enter a plain folder name (no “/”, “\\”, or “..”).[/red]"
            )
            return
        target = os.path.join(self._root, name)
        try:
            os.makedirs(target, exist_ok=True)
        except OSError as exc:
            self.query_one("#fs-status", Label).update(
                f"[red]Could not create folder: {exc}[/red]"
            )
            return
        box.value = ""
        self.query_one("#fs-status", Label).update(self._prompt)  # clear any prior error
        self._reroot(target)           # step into the new folder
        self._on_dir_selected(target)  # and mark it as the pending choice

    def _confirm(self) -> None:
        raise NotImplementedError

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss("")


class DirPickerScreen(FSPickerScreen):
    """Modal that lets user browse and confirm a directory."""

    _prompt = "Pick a directory: click to select, double-click to enter; OK confirms."

    def _extra_controls(self) -> list:
        # A create-folder row, so an output directory that doesn't exist yet can
        # be made without leaving the picker. Only the directory picker gets it.
        return [
            Horizontal(
                Input(placeholder="new folder name (created here)", id="new-folder-name"),
                Button("New folder", id="mk-folder", variant="default"),
                classes="newdir-row",
            )
        ]

    def _on_dir_selected(self, path: str) -> None:
        self._selected = path
        self.query_one("#ok", Button).label = f"OK  [{os.path.basename(path)}]"

    def _confirm(self) -> None:
        # Return the highlighted directory, or fall back to the folder currently
        # shown in the tree if the user only navigated.
        self.dismiss(self._selected or self._root)


class FilePickerScreen(FSPickerScreen):
    """Modal that lets user browse and confirm a *file* (e.g. a rules YAML).

    Unlike :class:`DirPickerScreen`, only a *file* selection sets the confirmable
    value; clicking a folder just navigates the tree and never becomes the
    result. That is what keeps a stray navigation click before OK from returning
    a directory — the exact failure in issue #89. (It inherits the base
    directory handler, which only *navigates* into folders and never sets the
    confirmable value here.)
    """

    _prompt = "Pick a file: double-click folders to enter, click a file, then OK."

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        self._selected = str(event.path)
        self.query_one("#ok", Button).label = f"OK  [{os.path.basename(self._selected)}]"

    def _confirm(self) -> None:
        # Confirm only when a real file is chosen; otherwise OK is a no-op.
        if os.path.isfile(self._selected):
            self.dismiss(self._selected)


# ── Setup tab ─────────────────────────────────────────────────────────────────

class SetupPane(Static):
    DEFAULT_CSS = """
    SetupPane { padding: 1 2; }
    SetupPane Label { margin-top: 1; }
    SetupPane .path-row { height: 3; }
    SetupPane Input { width: 1fr; }
    SetupPane Button { width: 14; margin-left: 1; }
    SetupPane .hint { color: $text-muted; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Label("[b]Source directory[/b] — raw EEG files")
        with Horizontal(classes="path-row"):
            yield Input(placeholder="/path/to/source", id="source-input")
            yield Button("Browse…", id="browse-source")
        yield Label("[b]BIDS output directory[/b]")
        with Horizontal(classes="path-row"):
            yield Input(placeholder="/path/to/bids_output", id="bids-input")
            yield Button("Browse…", id="browse-bids")
        yield Static(
            "Then define your conversion rules in the Rules tab "
            "(or load an existing rules file there).",
            classes="hint",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "browse-source": ("source-input", True),
            "browse-bids": ("bids-input", True),
        }
        if event.button.id in mapping:
            target_id, is_dir = mapping[event.button.id]
            self.app._pending_input_id = target_id
            start = self.query_one(f"#{target_id}", Input).value or "."
            screen = DirPickerScreen(start) if is_dir else FilePickerScreen(start)
            self.app.push_screen(screen, self.app._on_path_picked)

    def get_values(self) -> dict:
        return {
            "source": self.query_one("#source-input", Input).value.strip(),
            "bids": self.query_one("#bids-input", Input).value.strip(),
        }


# ── Files list modal ─────────────────────────────────────────────────────────

class FilesListScreen(ModalScreen):
    """Modal showing all matched files with extraction details on click."""

    DEFAULT_CSS = """
    FilesListScreen { align: center middle; }
    FilesListScreen > Vertical {
        width: 92%; height: 90%;
        border: thick $primary; background: $surface; padding: 1;
    }
    FilesListScreen DataTable { height: 1fr; }
    FilesListScreen #extraction-panel {
        height: auto;
        max-height: 40%;
        border: solid $primary;
        padding: 0 1;
        color: $success;
        overflow-y: auto;
    }
    FilesListScreen #extraction-panel.muted { color: $text-muted; }
    FilesListScreen #extraction-panel.error { color: $error; }
    FilesListScreen Horizontal { height: 3; align: right middle; }
    """

    def __init__(self, files: list[str], pattern: str = "", mode: str = "placeholder", fields: list[str] | None = None) -> None:
        super().__init__()
        self._files = files
        self._pattern = pattern
        self._mode = mode
        self._fields = fields or []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{len(self._files)} matched file(s)[/b] — click a file to see extracted fields")
            yield DataTable(id="files-table", zebra_stripes=True, cursor_type="row")
            yield Static("Select a file to see extracted fields.", id="extraction-panel", classes="muted")
            with Horizontal():
                yield Button("Close", id="close-files", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#files-table", DataTable)
        table.add_column("File path")
        for f in self._files:
            table.add_row(f)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        table = self.query_one("#files-table", DataTable)
        filepath = str(table.get_row(event.row_key)[0])
        self._show_extraction(filepath)

    def _show_extraction(self, filepath: str) -> None:
        from sovabids.parsers import parse_from_placeholder, parse_from_regex
        panel = self.query_one("#extraction-panel", Static)
        if not self._pattern:
            panel.update("No pattern set.")
            panel.remove_class("muted", "error")
            panel.add_class("muted")
            return
        try:
            if self._mode == "regex" and self._fields:
                result = parse_from_regex(filepath, self._pattern, self._fields)
            else:
                result = parse_from_placeholder(filepath, self._pattern)
            if result:
                lines = "\n".join(f"  [cyan]{k}[/cyan] = [yellow]{v}[/yellow]" for k, v in _flatten_dict(result).items())
                panel.update(f"[b]Extracted fields:[/b]\n{lines}")
                panel.remove_class("muted", "error")
            else:
                panel.update("No fields extracted — pattern may not match this file.")
                panel.remove_class("muted", "error")
                panel.add_class("error")
        except Exception as exc:
            panel.update(f"Parse error: {exc}")
            panel.remove_class("muted", "error")
            panel.add_class("error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-files":
            self.dismiss()

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss()


# ── Channel names modal ───────────────────────────────────────────────────────

class ChannelNamesScreen(ModalScreen):
    """Modal showing channel names and types from a file."""

    DEFAULT_CSS = """
    ChannelNamesScreen { align: center middle; }
    ChannelNamesScreen > Vertical {
        width: 70%; height: 85%;
        border: thick $primary; background: $surface; padding: 1;
    }
    ChannelNamesScreen DataTable { height: 1fr; }
    ChannelNamesScreen #ch-status { color: $text-muted; height: 1; }
    ChannelNamesScreen Horizontal { height: 3; align: right middle; }
    """

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self._filepath = filepath

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Loading: [cyan]{os.path.basename(self._filepath)}[/cyan]", id="ch-label")
            yield Static("", id="ch-status")
            yield DataTable(id="ch-table", zebra_stripes=True, cursor_type="row")
            with Horizontal():
                yield Button("Close", id="close-ch", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#ch-table", DataTable).add_columns("#", "Channel", "Type")
        self._load_worker()

    @work(thread=True)
    def _load_worker(self) -> None:
        try:
            from mne.io import read_raw
            raw = read_raw(self._filepath, preload=False, verbose=False)
            ch_names = raw.ch_names
            ch_types = raw.get_channel_types()
            self.app.call_from_thread(self._populate, ch_names, ch_types)
        except Exception as exc:
            self.app.call_from_thread(
                self.query_one("#ch-label", Label).update,
                f"[red]Error loading file: {exc}[/red]",
            )

    def _populate(self, ch_names: list, ch_types: list) -> None:
        self.query_one("#ch-label", Label).update(
            f"[b]{len(ch_names)} channel(s)[/b] — [cyan]{os.path.basename(self._filepath)}[/cyan]"
        )
        table = self.query_one("#ch-table", DataTable)
        for i, (name, typ) in enumerate(zip(ch_names, ch_types)):
            table.add_row(str(i), name, typ)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-ch":
            self.dismiss()

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss()


def _flatten_dict(d: dict, prefix: str = "") -> dict:
    """Flatten nested dict with dot-notation keys."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten_dict(v, key))
        else:
            out[key] = v
    return out


class _OptionalNumber(Validator):
    """Blank is allowed (the field is optional); a non-blank value must parse as a
    number. Used so an unparseable power-line frequency is flagged instead of
    silently dropped."""

    def validate(self, value: str) -> ValidationResult:
        if not value.strip():
            return self.success()
        try:
            float(value)
        except ValueError:
            return self.failure("Enter a number in Hz, e.g. 50")
        return self.success()


# ── Rules tab ─────────────────────────────────────────────────────────────────

class RulesPane(Static):
    DEFAULT_CSS = """
    RulesPane { padding: 1 2; }
    RulesPane Label { margin-top: 1; }
    RulesPane .hint { color: $text-muted; }
    RulesPane .pattern-examples {
        color: $text-muted;
        margin-bottom: 1;
        padding: 0 2;
        border-left: solid $primary;
    }
    RulesPane .rulesfile-row { height: 3; }
    RulesPane .rulesfile-row Input { width: 1fr; }
    RulesPane .rulesfile-row Button { width: 14; margin-left: 1; }
    RulesPane #rules-lock-note {
        display: none;
        height: auto;
        color: $warning;
        border: round $warning;
        padding: 0 1;
        margin-bottom: 1;
    }
    RulesPane #rules-lock-note.locked { display: block; }
    RulesPane #rules-builder { height: auto; }
    RulesPane #ext-count { color: $text-muted; height: 1; margin-bottom: 1; }
    RulesPane #sample-paths {
        display: none;
        height: auto;
        margin-bottom: 1;
        padding: 0 2;
        border-left: solid $success;
    }
    RulesPane #preview-row { height: auto; margin-top: 1; }
    RulesPane #preview-label {
        padding: 1;
        border: solid $primary;
        color: $success;
        width: 1fr;
        height: auto;
        min-height: 3;
    }
    RulesPane #preview-label.error { color: $error; }
    RulesPane #preview-label.muted { color: $text-muted; }
    RulesPane #show-files { width: 18; margin-left: 1; }
    RulesPane Select { margin-bottom: 1; }
    RulesPane Input { margin-bottom: 1; }
    RulesPane .section-head { margin-top: 1; }
    RulesPane RadioSet { margin-bottom: 1; }
    RulesPane #regex-fields-row { display: none; height: auto; }
    RulesPane #regex-fields-row.visible { display: block; }
    RulesPane #regex-examples { display: none; }
    RulesPane #regex-examples.visible { display: block; }
    RulesPane #io-example-row { display: none; height: auto; }
    RulesPane #io-examples { display: none; }
    RulesPane #io-src-row { height: 3; }
    RulesPane #io-src-row Input { width: 1fr; }
    RulesPane #io-src-row Button { width: 18; margin-left: 1; }
    RulesPane #pattern-section { height: auto; }
    RulesPane .inspect-row { height: 3; margin-bottom: 1; }
    RulesPane .inspect-row Button { margin-right: 1; }
    """

    _preview_lock: ClassVar = threading.Lock()
    _SAMPLE_SHOW: ClassVar[int] = 2       # how many example paths to display
    _SAMPLE_COLLECT_CAP: ClassVar[int] = 200  # bound work on huge trees

    def __init__(self) -> None:
        super().__init__()
        self._preview_timer = None
        self._ext_count_timer = None
        self._matched_files: list[str] = []

    def compose(self) -> ComposeResult:
        # Either load an existing rules file, OR build the rules below. Loading a
        # file wins at Generate time (#89), so it locks the builder.
        yield Label("[b]Load existing rules file[/b] (optional — locks the builder below)")
        with Horizontal(classes="rulesfile-row"):
            yield Input(placeholder="/path/to/rules.yml", id="rules-file-input")
            yield Button("Browse…", id="browse-rules")
        yield Static(
            "🔒 A rules file is loaded — the builder below is ignored. "
            "Clear the field to build rules here.",
            id="rules-lock-note",
        )
        yield Rule()
        with Vertical(id="rules-builder"):
            yield from self._compose_builder()

    def _compose_builder(self) -> ComposeResult:
        yield Label("[b]EEG file extension[/b]")
        ext_options = [(e, e) for e in SUPPORTED_EXTENSIONS]
        yield Select(ext_options, value=SUPPORTED_EXTENSIONS[0], id="ext-select")
        yield Static("", id="ext-count")

        yield Label("[b]Pattern mode[/b]")
        with RadioSet(id="pattern-mode"):
            yield RadioButton("Placeholder  (%field%)", id="mode-placeholder", value=True)
            yield RadioButton("Regex  (with named fields)", id="mode-regex")
            yield RadioButton("File example  (source → BIDS path)", id="mode-example")
        yield Vertical(
            Label("Fields (comma-separated, same order as regex groups)"),
            Input(placeholder="entities.subject, entities.task", id="regex-fields-input"),
            id="regex-fields-row",
        )
        yield Vertical(
            Label("Source example  (one raw EEG file path)"),
            Horizontal(
                Input(placeholder="/data/sub-01_task-rest.vhdr", id="io-src-input"),
                Button("Pick first match", id="io-pick-src", disabled=True),
                id="io-src-row",
            ),
            Label("Target BIDS example  (corresponding BIDS output path)"),
            Input(
                placeholder="/bids/sub-01/eeg/sub-01_task-rest_eeg.vhdr",
                id="io-tgt-input",
            ),
            id="io-example-row",
        )

        yield Static("", id="sample-paths")

        yield Vertical(
            Label("[b]Path pattern[/b]", id="pattern-label"),
            Static(
                "Use %entity% placeholders matched against the full file path.",
                id="pattern-hint",
                classes="hint",
            ),
            Static(
                "[dim]Placeholder examples:[/dim]\n"
                "  [cyan]%subject%_%task%.vhdr[/cyan]\n"
                "    matches: /data/001_rest.vhdr  →  subject=001, task=rest\n"
                "  [cyan]%subject%/%task%_%run%.bdf[/cyan]\n"
                "    matches: /data/001/rest_01.bdf  →  subject=001, task=rest, run=01\n"
                "  [cyan]raw/%subject%_%session%_%task%_%run%.eeg[/cyan]\n"
                "    matches: /raw/001_ses01_rest_01.eeg\n"
                "  [cyan]sub-%subject%/ses-%session%/eeg/sub-%subject%_ses-%session%_%task%_eeg.set[/cyan]\n"
                "    already-partially-BIDSified paths",
                id="placeholder-examples",
                classes="pattern-examples",
            ),
            Static(
                "[dim]Regex examples:[/dim]\n"
                "  Pattern: [cyan]([^/]+)_([^/]+)\\.vhdr[/cyan]   Fields: [cyan]entities.subject, entities.task[/cyan]\n"
                "    matches: /data/001_rest.vhdr  →  subject=001, task=rest\n"
                "  Pattern: [cyan]([^/]+)/([^/]+)_([^/]+)\\.bdf[/cyan]   Fields: [cyan]entities.subject, entities.task, entities.run[/cyan]\n"
                "    matches: /data/001/rest_01.bdf  →  subject=001, task=rest, run=01\n"
                "  Fields use dot-notation: [cyan]entities.subject[/cyan], [cyan]entities.task[/cyan], [cyan]entities.session[/cyan], [cyan]entities.run[/cyan]",
                id="regex-examples",
                classes="pattern-examples",
            ),
            Static(
                "[dim]File example mode:[/dim]\n"
                "  Give one raw file path and its corresponding BIDS output path.\n"
                "  The pattern is derived automatically via entity matching.\n"
                "  [cyan]Source:[/cyan] /data/sub-SU0/ses-SE0/eeg-TA0-0.vhdr\n"
                "  [cyan]Target:[/cyan] /bids/sub-SU0/ses-SE0/eeg/sub-SU0_ses-SE0_task-TA0_run-0_eeg.vhdr\n"
                "  Derived pattern applied to all matched files.",
                id="io-examples",
                classes="pattern-examples",
            ),
            Input(placeholder="%subject%_%task%.vhdr", id="pattern-input"),
            id="pattern-section",
        )
        with Horizontal(id="preview-row"):
            yield Label(
                "Waiting for source path and pattern…",
                id="preview-label",
                classes="muted",
            )
            yield Button("Refresh", id="refresh-preview", variant="default")
            yield Button("Show all (0)", id="show-files", variant="default", disabled=True)

        yield Rule()
        yield Label("[b]Sidecar fields[/b]", classes="section-head")
        yield Static("Inspect first matched file:", classes="hint")
        with Horizontal(classes="inspect-row"):
            yield Button("Power Spectrum", id="show-psd", variant="default", disabled=True)
            yield Button("Channel Names", id="show-channels", variant="default", disabled=True)
        yield Label("Power line frequency (Hz)")
        yield Input(placeholder="50", id="plf-input", validators=[_OptionalNumber()])
        yield Label("EEG reference")
        yield Input(placeholder="FCz", id="ref-input")

        yield Rule()
        yield Label("[b]Dataset description[/b]", classes="section-head")
        yield Label("Dataset name")
        yield Input(placeholder="My EEG Dataset", id="ds-name-input")
        yield Label("Authors (comma-separated)")
        yield Input(placeholder="Author One, Author Two", id="ds-authors-input")

    # ── pattern preview ───────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "rules-file-input":
            self._set_builder_locked(bool(event.value.strip()))
            return
        if event.input.id in ("pattern-input", "regex-fields-input", "io-src-input", "io-tgt-input"):
            self._schedule_preview()

    def _set_builder_locked(self, locked: bool) -> None:
        try:
            self.query_one("#rules-builder").disabled = locked
            self.query_one("#rules-lock-note", Static).set_class(locked, "locked")
        except Exception:
            pass

    def get_rules_file(self) -> str:
        return self.query_one("#rules-file-input", Input).value.strip()

    def plf_error(self) -> str:
        """Return an error message if the power-line frequency is set but not a
        number, else "". Lets an action block instead of silently dropping it (#102)."""
        val = self.query_one("#plf-input", Input).value.strip()
        if val:
            try:
                float(val)
            except ValueError:
                return f"Power line frequency must be a number in Hz, got: {val}"
        return ""

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "ext-select":
            self._schedule_ext_count()
            self._schedule_preview()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "pattern-mode":
            regex_row = self.query_one("#regex-fields-row", Vertical)
            io_row = self.query_one("#io-example-row", Vertical)
            pat_sec = self.query_one("#pattern-section", Vertical)
            ph_ex = self.query_one("#placeholder-examples", Static)
            rx_ex = self.query_one("#regex-examples", Static)
            io_ex = self.query_one("#io-examples", Static)
            pat = self.query_one("#pattern-input", Input)
            lbl = self.query_one("#pattern-label", Label)
            hint = self.query_one("#pattern-hint", Static)
            if event.index == 1:  # regex
                regex_row.display = True
                io_row.display = False
                pat_sec.display = True
                ph_ex.display = False
                rx_ex.display = True
                io_ex.display = False
                pat.placeholder = "([^/]+)_([^/]+)\\.vhdr"
                lbl.update("[b]Regex pattern[/b]  (only the regex — put field names in the Fields box above)")
                hint.update("Enter a Python regex. Each capture group [cyan]()[/cyan] maps to one field, in order.")
            elif event.index == 2:  # file example
                regex_row.display = False
                io_row.display = True
                pat_sec.display = False
                ph_ex.display = False
                rx_ex.display = False
                io_ex.display = True
            else:  # placeholder
                regex_row.display = False
                io_row.display = False
                pat_sec.display = True
                ph_ex.display = True
                rx_ex.display = False
                io_ex.display = False
                pat.placeholder = "%subject%_%task%.vhdr"
                lbl.update("[b]Path pattern[/b]")
                hint.update("Use %entity% placeholders matched against the full file path.")
            self._schedule_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse-rules":
            self.app._pending_input_id = "rules-file-input"
            start = self.query_one("#rules-file-input", Input).value or "."
            self.app.push_screen(FilePickerScreen(start), self.app._on_path_picked)
        elif event.button.id == "refresh-preview":
            self._run_preview()
        elif event.button.id == "show-files":
            mode, fields = self._get_mode_and_fields()
            if mode == "example":
                io_src, io_tgt = self._get_io_example()
                try:
                    from sovabids.heuristics import from_io_example
                    pattern = from_io_example(io_src, io_tgt).get("pattern", "")
                except Exception:
                    pattern = ""
                self.app.push_screen(FilesListScreen(self._matched_files, pattern=pattern, mode="placeholder", fields=[]))
            else:
                pattern = self.query_one("#pattern-input", Input).value.strip()
                self.app.push_screen(FilesListScreen(self._matched_files, pattern=pattern, mode=mode, fields=fields))
        elif event.button.id == "io-pick-src":
            if self._matched_files:
                self.query_one("#io-src-input", Input).value = self._matched_files[0]
        elif event.button.id == "show-psd":
            if self._matched_files:
                self._set_preview("Computing PSD — window will open separately…", "muted")
                self._psd_worker(self._matched_files[0])
        elif event.button.id == "show-channels":
            if self._matched_files:
                self.app.push_screen(ChannelNamesScreen(self._matched_files[0]))

    def _get_mode_and_fields(self) -> tuple[str, list[str]]:
        radio = self.query_one("#pattern-mode", RadioSet)
        idx = radio.pressed_index
        if idx == 1:
            mode = "regex"
        elif idx == 2:
            mode = "example"
        else:
            mode = "placeholder"
        fields_raw = self.query_one("#regex-fields-input", Input).value.strip()
        fields = [f.strip() for f in fields_raw.split(",") if f.strip()] if fields_raw else []
        return mode, fields

    def _get_io_example(self) -> tuple[str, str]:
        return (
            self.query_one("#io-src-input", Input).value.strip(),
            self.query_one("#io-tgt-input", Input).value.strip(),
        )

    def _schedule_ext_count(self) -> None:
        # Debounce: extension changes and Rules-tab activation both trigger this,
        # so coalesce bursts instead of firing a scan per event.
        if self._ext_count_timer is not None:
            self._ext_count_timer.stop()
        self._ext_count_timer = self.set_timer(0.1, self._run_ext_count)

    def _run_ext_count(self) -> None:
        source = self._get_source()
        ext = str(self.query_one("#ext-select", Select).value)
        if not source or not os.path.isdir(source):
            self.query_one("#ext-count", Static).update("")
            self._update_samples([], source)
            return
        self._ext_count_worker(source, ext)

    @work(thread=True, exclusive=True, group="ext-count")
    def _ext_count_worker(self, source: str, ext: str) -> None:
        count = 0
        samples: list[str] = []
        for root, _, files in os.walk(source):
            for f in sorted(files):
                if f.endswith(ext):
                    count += 1
                    if len(samples) < self._SAMPLE_COLLECT_CAP:
                        samples.append(os.path.join(root, f))
        samples.sort()
        self.app.call_from_thread(
            self.query_one("#ext-count", Static).update,
            f"{count} file(s) with [cyan]{ext}[/cyan] in source directory",
        )
        self.app.call_from_thread(self._update_samples, samples[: self._SAMPLE_SHOW], source)

    @work(thread=True)
    def _psd_worker(self, filepath: str) -> None:
        import subprocess
        import tempfile

        try:
            import matplotlib
            import matplotlib.pyplot as plt
            plt.switch_backend("agg")
            from mne.io import read_raw
            raw = read_raw(filepath, preload=True, verbose=False)
            fmax = min(120.0, raw.info["sfreq"] / 2.0)
            try:
                fig = raw.compute_psd(fmax=fmax).plot(show=False)
            except AttributeError:
                fig = raw.plot_psd(fmax=fmax, show=False)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = f.name
            fig.savefig(tmp, dpi=100, bbox_inches="tight")
            plt.close(fig)
            subprocess.Popen(["xdg-open", tmp])
            self.app.call_from_thread(
                self._set_preview,
                f"PSD saved — opening image viewer ({os.path.basename(filepath)})",
                "",
            )
        except Exception as exc:
            self.app.call_from_thread(self._set_preview, f"PSD error: {exc}", "error")

    def _schedule_preview(self) -> None:
        if self._preview_timer is not None:
            self._preview_timer.stop()
        self._preview_timer = self.set_timer(0.6, self._run_preview)

    def _run_preview(self) -> None:
        source = self._get_source()
        ext = self.query_one("#ext-select", Select).value
        mode, fields = self._get_mode_and_fields()
        if not source:
            self._set_preview("Set source directory in Setup tab first.", "muted")
            return
        if mode == "example":
            io_src, io_tgt = self._get_io_example()
            if not io_src or not io_tgt:
                self._set_preview("File example mode: enter source and target paths above.", "muted")
                return
            self._set_preview("Deriving pattern from example…", "muted")
            self._preview_worker(source, "", str(ext), mode, fields, io_src, io_tgt)
            return
        pattern = self.query_one("#pattern-input", Input).value.strip()
        if not pattern:
            self._set_preview("Enter a pattern above.", "muted")
            return
        if mode == "regex" and not fields:
            self._set_preview("Regex mode: enter fields above.", "muted")
            return
        self._set_preview("Scanning…", "muted")
        self._preview_worker(source, pattern, str(ext), mode, fields)

    @work(thread=True)
    def _preview_worker(self, source: str, pattern: str, ext: str, mode: str, fields: list[str], io_src: str = "", io_tgt: str = "") -> None:
        from sovabids.parsers import parse_from_placeholder, parse_from_regex
        from sovabids.rules import get_files

        if mode == "example":
            try:
                from sovabids.heuristics import from_io_example
                derived_pattern = from_io_example(io_src, io_tgt).get("pattern", "")
            except Exception as exc:
                self.app.call_from_thread(self._set_preview, f"Example error: {exc}", "error")
                self.app.call_from_thread(self._update_show_files_btn, [])
                return
            # derived pattern already uses %entities.subject% notation
            scan_rules = {"non-bids": {"eeg_extension": ext, "path_analysis": {"pattern": derived_pattern}}}
            try:
                files = get_files(source, scan_rules)
            except Exception as exc:
                self.app.call_from_thread(self._set_preview, f"Error: {exc}", "error")
                return
            matched = []
            for f in files:
                try:
                    if parse_from_placeholder(f, derived_pattern):
                        matched.append(f)
                except Exception:
                    pass
            count = len(matched)
            if count == 0:
                msg = f"0 files matched with derived pattern: {derived_pattern}"
                self.app.call_from_thread(self._set_preview, msg, "error")
            else:
                example = os.path.relpath(matched[0], source)
                msg = f"{count} file(s) matched.  Derived pattern: [cyan]{derived_pattern}[/cyan]  Example: …/{example}"
                self.app.call_from_thread(self._set_preview, msg, "")
            self.app.call_from_thread(self._update_show_files_btn, matched)
            return

        rules = {"non-bids": {"eeg_extension": ext, "path_analysis": {"pattern": pattern}}}
        try:
            files = get_files(source, rules)
        except Exception as exc:
            self.app.call_from_thread(self._set_preview, f"Error: {exc}", "error")
            return

        matched = []
        for f in files:
            try:
                if mode == "regex" and fields:
                    result = parse_from_regex(f, pattern, fields)
                else:
                    result = parse_from_placeholder(f, pattern)
                if result:
                    matched.append(f)
            except Exception:
                pass

        count = len(matched)
        if count == 0:
            msg = "0 files matched — check your pattern and extension."
            self.app.call_from_thread(self._set_preview, msg, "error")
        else:
            example = os.path.relpath(matched[0], source)
            msg = f"{count} file(s) matched.  Example: …/{example}"
            self.app.call_from_thread(self._set_preview, msg, "")
        self.app.call_from_thread(self._update_show_files_btn, matched)

    def _update_show_files_btn(self, files: list[str]) -> None:
        self._matched_files = files
        has = len(files) > 0
        btn = self.query_one("#show-files", Button)
        btn.label = f"Show all ({len(files)})"
        btn.disabled = not has
        self.query_one("#show-psd", Button).disabled = not has
        self.query_one("#show-channels", Button).disabled = not has
        self.query_one("#io-pick-src", Button).disabled = not has

    def _set_preview(self, text: str, css_class: str) -> None:
        label = self.query_one("#preview-label", Label)
        label.update(text)
        label.remove_class("muted", "error")
        if css_class:
            label.add_class(css_class)

    def _update_samples(self, samples: list, source: str) -> None:
        """Show a couple of real source-file paths so the user can read off the
        structure and build the pattern from it. Hidden when nothing is found."""
        stat = self.query_one("#sample-paths", Static)
        if not samples:
            stat.update("")
            stat.display = False
            return
        lines = ["[dim]Example source files — build your pattern from these:[/dim]"]
        for p in samples:
            try:
                rel = os.path.relpath(p, source)
            except Exception:
                rel = p
            lines.append(f"  [cyan]…/{rel}[/cyan]")
        stat.update("\n".join(lines))
        stat.display = True

    def _get_source(self) -> str:
        try:
            setup = self.app.query_one(SetupPane)
            return setup.get_values()["source"]
        except Exception:
            return ""

    def get_rules(self) -> dict:
        ext = str(self.query_one("#ext-select", Select).value)
        pattern = self.query_one("#pattern-input", Input).value.strip()
        plf = self.query_one("#plf-input", Input).value.strip()
        ref = self.query_one("#ref-input", Input).value.strip()
        ds_name = self.query_one("#ds-name-input", Input).value.strip()
        ds_authors_raw = self.query_one("#ds-authors-input", Input).value.strip()
        authors = [a.strip() for a in ds_authors_raw.split(",") if a.strip()]
        mode, fields = self._get_mode_and_fields()

        rules: dict = {"non-bids": {"eeg_extension": ext}}
        if mode == "example":
            io_src, io_tgt = self._get_io_example()
            if io_src and io_tgt:
                rules["non-bids"]["path_analysis"] = {"source": io_src, "target": io_tgt}
        elif pattern:
            if mode == "placeholder":
                from sovabids.parsers import _modify_entities_of_placeholder_pattern
                rules_pattern = _modify_entities_of_placeholder_pattern(pattern, mode="append")
            else:
                rules_pattern = pattern
            path_analysis: dict = {"pattern": rules_pattern}
            if mode == "regex" and fields:
                path_analysis["fields"] = fields
            rules["non-bids"]["path_analysis"] = path_analysis
        if plf or ref:
            rules["sidecar"] = {}
            if plf:
                try:
                    rules["sidecar"]["PowerLineFrequency"] = float(plf)
                except ValueError:
                    pass
            if ref:
                rules["sidecar"]["EEGReference"] = ref
        if ds_name or authors:
            rules["dataset_description"] = {}
            if ds_name:
                rules["dataset_description"]["Name"] = ds_name
            if authors:
                rules["dataset_description"]["Authors"] = authors
        return rules


# ── Mappings tab ──────────────────────────────────────────────────────────────

class MappingsPane(Static):
    DEFAULT_CSS = """
    MappingsPane { padding: 1 2; }
    MappingsPane #mappings-status { margin-bottom: 1; color: $text-muted; }
    MappingsPane DataTable { height: 1fr; }
    MappingsPane Horizontal { height: 3; margin-bottom: 1; }
    MappingsPane Button { margin-right: 1; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Generate Mappings", id="gen-mappings", variant="primary")
            yield Button("Save Mappings YAML…", id="save-mappings", variant="default")
        yield Static("Press Generate to scan files and build mappings.", id="mappings-status")
        yield DataTable(id="mappings-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#mappings-table", DataTable)
        table.add_columns("Source file", "Target file")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gen-mappings":
            self._generate()
        elif event.button.id == "save-mappings":
            self._save_mappings_yaml()

    def _generate(self) -> None:
        vals = self.app.query_one(SetupPane).get_values()
        source, bids = vals["source"], vals["bids"]
        rules_file = self.app.query_one(RulesPane).get_rules_file()

        if not source or not bids:
            self._set_status("Set source and BIDS directories in Setup tab.", error=True)
            return

        if rules_file:
            # A rules file was given: it must be a readable file, and it must
            # parse. Don't silently fall back to the Rules tab (that hides a bad
            # path — e.g. the directory a broken picker used to return, #89) and
            # don't let a parse error crash the app.
            if not os.path.isfile(rules_file):
                self._set_status(
                    f"Rules file not found (or it is a directory): {rules_file}", error=True
                )
                return
            try:
                from sovabids.rules import load_rules
                rules = load_rules(rules_file)
            except Exception as exc:
                self._set_status(f"Could not read rules file: {exc}", error=True)
                return
        else:
            rules_pane = self.app.query_one(RulesPane)
            plf_err = rules_pane.plf_error()
            if plf_err:
                self._set_status(plf_err, error=True)
                return
            rules = rules_pane.get_rules()

        self._set_status("Generating mappings…")
        self._gen_worker(source, bids, rules)

    @work(thread=True)
    def _gen_worker(self, source: str, bids: str, rules: dict) -> None:
        from sovabids.rules import apply_rules

        try:
            mapping_data = apply_rules(source_path=source, bids_path=bids, rules=rules)
            self.app._mapping_data = mapping_data
            self.app.call_from_thread(self._populate_table, mapping_data["Individual"])
        except Exception as exc:
            self.app.call_from_thread(
                self._set_status, f"Error generating mappings: {exc}", True
            )

    def _populate_table(self, individuals: list) -> None:
        table = self.query_one("#mappings-table", DataTable)
        table.clear()
        for m in individuals:
            src = m.get("IO", {}).get("source", "")
            tgt = m.get("IO", {}).get("target", "")
            table.add_row(src, tgt)
        self._set_status(f"{len(individuals)} file(s) mapped. Ready to convert.")

    def _save_mappings_yaml(self) -> None:
        data = getattr(self.app, "_mapping_data", None)
        if not data:
            self._set_status("Generate mappings first.", error=True)
            return
        bids = self.app.query_one(SetupPane).get_values()["bids"]
        if not bids:
            # Without this, os.path.join("", ...) is relative and silently writes
            # mappings.yml into the current working directory.
            self._set_status("Set a BIDS output directory first (Setup tab).", error=True)
            return
        out_path = os.path.join(bids, "code", "sovabids", "mappings.yml")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        self._set_status(f"Saved to {out_path}")

    def _set_status(self, msg: str, error: bool = False) -> None:
        label = self.query_one("#mappings-status", Static)
        label.update(f"[red]{msg}[/red]" if error else msg)


# ── Convert tab ───────────────────────────────────────────────────────────────

class ConvertPane(Static):
    DEFAULT_CSS = """
    ConvertPane { padding: 1 2; }
    ConvertPane Horizontal { height: 3; margin-bottom: 1; }
    ConvertPane Button { margin-right: 1; }
    ConvertPane RichLog { height: 1fr; border: solid $primary; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Convert", id="convert-btn", variant="success")
            yield Button("Clear log", id="clear-log", variant="default")
        yield RichLog(id="convert-log", highlight=True, markup=True, wrap=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "convert-btn":
            self._start_convert()
        elif event.button.id == "clear-log":
            self.query_one("#convert-log", RichLog).clear()

    def _start_convert(self) -> None:
        data = getattr(self.app, "_mapping_data", None)
        if not data:
            self._log("[red]Generate mappings first (Mappings tab).[/red]")
            return
        self._log("[bold]Starting conversion…[/bold]")
        self._convert_worker(data)

    @work(thread=True)
    def _convert_worker(self, mapping_data: dict) -> None:
        import logging

        from sovabids.convert import convert_them

        log = self.query_one("#convert-log", RichLog)

        class TuiHandler(logging.Handler):
            def __init__(self, richlog: RichLog, call_fn) -> None:
                super().__init__()
                self._rl = richlog
                self._call = call_fn

            def emit(self, record: logging.LogRecord) -> None:
                msg = self.format(record)
                if record.levelno >= logging.ERROR:
                    line = f"[red]{msg}[/red]"
                elif record.levelno >= logging.WARNING:
                    line = f"[yellow]{msg}[/yellow]"
                else:
                    line = msg
                self._call(self._rl.write, line)

        root = logging.getLogger()
        handler = TuiHandler(log, self.app.call_from_thread)
        handler.setLevel(logging.INFO)
        root.addHandler(handler)
        try:
            convert_them(mapping_data)
            self.app.call_from_thread(
                self._log, "[bold green]Conversion complete![/bold green]"
            )
        except Exception as exc:
            self.app.call_from_thread(self._log, f"[red]Conversion failed: {exc}[/red]")
        finally:
            root.removeHandler(handler)

    def _log(self, msg: str) -> None:
        self.query_one("#convert-log", RichLog).write(msg)


# ── Main App ──────────────────────────────────────────────────────────────────

class SovabidsApp(App):
    """sovabids TUI — EEG to BIDS conversion wizard."""

    TITLE = "sovabids"
    SUB_TITLE = "EEG → BIDS conversion"
    CSS = """
    TabbedContent { height: 1fr; }
    TabPane { height: 1fr; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+s", "save_rules", "Save rules"),
    ]

    _mapping_data: dict | None = None
    _pending_input_id: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("1 · Setup", id="tab-setup"):
                yield ScrollableContainer(SetupPane())
            with TabPane("2 · Rules", id="tab-rules"):
                yield ScrollableContainer(RulesPane())
            with TabPane("3 · Mappings", id="tab-mappings"):
                yield MappingsPane()
            with TabPane("4 · Convert", id="tab-convert"):
                yield ConvertPane()
        yield Footer()

    def _on_path_picked(self, path: str) -> None:
        if path and self._pending_input_id:
            try:
                self.query_one(f"#{self._pending_input_id}", Input).value = path
            except Exception:
                pass

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        # Opening the Rules tab (re)scans the source so the file count and the
        # example paths reflect whatever was set in Setup.
        if getattr(event.pane, "id", None) == "tab-rules":
            try:
                self.query_one(RulesPane)._schedule_ext_count()
            except Exception:
                pass

    def action_save_rules(self) -> None:
        bids = self.query_one(SetupPane).get_values().get("bids", "")
        if not bids:
            self.notify("Set a BIDS output directory first (Setup tab).", severity="warning")
            return
        rules_pane = self.query_one(RulesPane)
        if rules_pane.get_rules_file():
            self.notify(
                "A rules file is loaded — clear it in the Rules tab to save builder rules.",
                severity="warning",
            )
            return
        plf_err = rules_pane.plf_error()
        if plf_err:
            self.notify(plf_err, severity="warning")
            return
        rules = rules_pane.get_rules()
        out = os.path.join(bids, "code", "sovabids", "rules.yml")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            yaml.dump(rules, f, default_flow_style=False)
        self.notify(f"Saved rules to {out}")


def main() -> None:
    SovabidsApp().run()


if __name__ == "__main__":
    main()
