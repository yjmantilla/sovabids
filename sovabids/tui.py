"""Terminal User Interface for sovabids."""
from __future__ import annotations

import os
import threading
from copy import deepcopy
from typing import ClassVar

import yaml
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Rule,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from sovabids.settings import SUPPORTED_EXTENSIONS


# ── Directory picker modal ────────────────────────────────────────────────────

class DirPickerScreen(ModalScreen[str]):
    """Modal that lets user browse and confirm a directory."""

    DEFAULT_CSS = """
    DirPickerScreen {
        align: center middle;
    }
    DirPickerScreen > Vertical {
        width: 80%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    DirPickerScreen DirectoryTree {
        height: 1fr;
    }
    DirPickerScreen Label {
        height: 1;
        margin-bottom: 1;
    }
    DirPickerScreen Horizontal {
        height: 3;
        align: right middle;
    }
    DirPickerScreen Button {
        margin-left: 1;
    }
    """

    def __init__(self, start: str = ".") -> None:
        super().__init__()
        self._start = os.path.abspath(start) if start else os.path.expanduser("~")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Select directory (press Enter or OK to confirm):")
            yield DirectoryTree(self._start, id="dir-tree")
            with Horizontal():
                yield Button("Cancel", id="cancel", variant="default")
                yield Button("OK", id="ok", variant="primary")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        self._selected = str(event.path)
        self.query_one("#ok", Button).label = f"OK  [{os.path.basename(str(event.path))}]"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss("")
        elif event.button.id == "ok":
            path = getattr(self, "_selected", "")
            self.dismiss(path)


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
        yield Rule()
        yield Label("[b]Load existing rules file[/b] (optional — skips Rules tab)")
        with Horizontal(classes="path-row"):
            yield Input(placeholder="/path/to/rules.yml", id="rules-file-input")
            yield Button("Browse…", id="browse-rules")
        yield Static("Leave blank to build rules from scratch in the Rules tab.", classes="hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "browse-source": ("source-input", True),
            "browse-bids": ("bids-input", True),
            "browse-rules": ("rules-file-input", False),
        }
        if event.button.id in mapping:
            target_id, is_dir = mapping[event.button.id]
            self.app._pending_input_id = target_id
            start = self.query_one(f"#{target_id}", Input).value or "."
            if is_dir:
                self.app.push_screen(DirPickerScreen(start), self.app._on_dir_picked)
            else:
                self.app.push_screen(DirPickerScreen(start), self.app._on_dir_picked)

    def get_values(self) -> dict:
        return {
            "source": self.query_one("#source-input", Input).value.strip(),
            "bids": self.query_one("#bids-input", Input).value.strip(),
            "rules_file": self.query_one("#rules-file-input", Input).value.strip(),
        }


# ── Files list modal ─────────────────────────────────────────────────────────

class FilesListScreen(ModalScreen):
    """Modal showing all matched files with full paths."""

    DEFAULT_CSS = """
    FilesListScreen { align: center middle; }
    FilesListScreen > Vertical {
        width: 92%; height: 90%;
        border: thick $primary; background: $surface; padding: 1;
    }
    FilesListScreen DataTable { height: 1fr; }
    FilesListScreen Horizontal { height: 3; align: right middle; }
    """

    def __init__(self, files: list[str]) -> None:
        super().__init__()
        self._files = files

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{len(self._files)} matched file(s)[/b] — full paths")
            yield DataTable(id="files-table", zebra_stripes=True)
            with Horizontal():
                yield Button("Close", id="close-files", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#files-table", DataTable)
        table.add_column("File path")
        for f in self._files:
            table.add_row(f)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-files":
            self.dismiss()

    def on_key(self, event) -> None:  # noqa: ANN001
        if event.key == "escape":
            self.dismiss()


# ── Rules tab ─────────────────────────────────────────────────────────────────

class RulesPane(Static):
    DEFAULT_CSS = """
    RulesPane { padding: 1 2; }
    RulesPane Label { margin-top: 1; }
    RulesPane .hint { color: $text-muted; }
    RulesPane #pattern-examples {
        color: $text-muted;
        margin-bottom: 1;
        padding: 0 2;
        border-left: solid $primary;
    }
    RulesPane #preview-label {
        margin-top: 1;
        padding: 1;
        border: solid $primary;
        color: $success;
        width: 1fr;
    }
    RulesPane #preview-label.error { color: $error; }
    RulesPane #preview-label.muted { color: $text-muted; }
    RulesPane #show-files { width: 18; margin-left: 1; }
    RulesPane Select { margin-bottom: 1; }
    RulesPane Input { margin-bottom: 1; }
    RulesPane .section-head { margin-top: 1; }
    """

    _preview_lock: ClassVar = threading.Lock()

    def __init__(self) -> None:
        super().__init__()
        self._preview_timer = None
        self._matched_files: list[str] = []

    def compose(self) -> ComposeResult:
        yield Label("[b]EEG file extension[/b]")
        ext_options = [(e, e) for e in SUPPORTED_EXTENSIONS]
        yield Select(ext_options, value=SUPPORTED_EXTENSIONS[0], id="ext-select")

        yield Label("[b]Path pattern[/b]")
        yield Static(
            "Use %entity% placeholders matched against the full file path.",
            classes="hint",
        )
        yield Static(
            "[dim]Examples:[/dim]\n"
            "  [cyan]%subject%_%task%.vhdr[/cyan]\n"
            "    matches: /data/001_rest.vhdr  →  subject=001, task=rest\n"
            "  [cyan]%subject%/%task%_%run%.bdf[/cyan]\n"
            "    matches: /data/001/rest_01.bdf  →  subject=001, task=rest, run=01\n"
            "  [cyan]raw/%subject%_%session%_%task%_%run%.eeg[/cyan]\n"
            "    matches: /raw/001_ses01_rest_01.eeg\n"
            "  [cyan]sub-%subject%/ses-%session%/eeg/sub-%subject%_ses-%session%_%task%_eeg.set[/cyan]\n"
            "    already-partially-BIDSified paths",
            id="pattern-examples",
        )
        yield Input(placeholder="%subject%_%task%.vhdr", id="pattern-input")
        with Horizontal():
            yield Label(
                "Waiting for source path and pattern…",
                id="preview-label",
                classes="muted",
            )
            yield Button("Refresh", id="refresh-preview", variant="default")
            yield Button("Show all (0)", id="show-files", variant="default", disabled=True)

        yield Rule()
        yield Label("[b]Sidecar fields[/b]", classes="section-head")
        yield Label("Power line frequency (Hz)")
        yield Input(placeholder="50", id="plf-input")
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
        if event.input.id == "pattern-input":
            self._schedule_preview()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "ext-select":
            self._schedule_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-preview":
            self._run_preview()
        elif event.button.id == "show-files":
            self.app.push_screen(FilesListScreen(self._matched_files))

    def _schedule_preview(self) -> None:
        if self._preview_timer is not None:
            self._preview_timer.stop()
        self._preview_timer = self.set_timer(0.6, self._run_preview)

    def _run_preview(self) -> None:
        source = self._get_source()
        pattern = self.query_one("#pattern-input", Input).value.strip()
        ext = self.query_one("#ext-select", Select).value
        if not source:
            self._set_preview("Set source directory in Setup tab first.", "muted")
            return
        if not pattern:
            self._set_preview("Enter a pattern above.", "muted")
            return
        self._set_preview("Scanning…", "muted")
        self._preview_worker(source, pattern, str(ext))

    @work(thread=True)
    def _preview_worker(self, source: str, pattern: str, ext: str) -> None:
        from sovabids.rules import get_files

        rules = {"non-bids": {"eeg_extension": ext, "path_analysis": {"pattern": pattern}}}
        try:
            files = get_files(source, rules)
        except Exception as exc:
            self.app.call_from_thread(self._set_preview, f"Error: {exc}", "error")
            return
        count = len(files)
        if count == 0:
            msg = "0 files matched — check your pattern and extension."
            self.app.call_from_thread(self._set_preview, msg, "error")
        else:
            example = os.path.relpath(files[0], source)
            msg = f"{count} file(s) matched.  Example: …/{example}"
            self.app.call_from_thread(self._set_preview, msg, "")
        self.app.call_from_thread(self._update_show_files_btn, files)

    def _update_show_files_btn(self, files: list[str]) -> None:
        self._matched_files = files
        btn = self.query_one("#show-files", Button)
        btn.label = f"Show all ({len(files)})"
        btn.disabled = len(files) == 0

    def _set_preview(self, text: str, css_class: str) -> None:
        label = self.query_one("#preview-label", Label)
        label.update(text)
        label.remove_class("muted", "error")
        if css_class:
            label.add_class(css_class)

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

        rules: dict = {"non-bids": {"eeg_extension": ext}}
        if pattern:
            rules["non-bids"]["path_analysis"] = {"pattern": pattern}
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

    _mappings: reactive[list] = reactive([])

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
        rules_file = vals["rules_file"]

        if not source or not bids:
            self._set_status("Set source and BIDS directories in Setup tab.", error=True)
            return

        if rules_file and os.path.isfile(rules_file):
            with open(rules_file) as f:
                rules = yaml.safe_load(f)
        else:
            rules = self.app.query_one(RulesPane).get_rules()

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
        out_path = os.path.join(bids, "code", "sovabids", "mappings.yml")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        self._set_status(f"Saved to {out_path}")

    def _set_status(self, msg: str, error: bool = False) -> None:
        label = self.query_one("#mappings-status", Static)
        label.update(msg)


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

    def _on_dir_picked(self, path: str) -> None:
        if path and self._pending_input_id:
            try:
                self.query_one(f"#{self._pending_input_id}", Input).value = path
            except Exception:
                pass

    def action_save_rules(self) -> None:
        vals = self.query_one(SetupPane).get_values()
        rules = self.query_one(RulesPane).get_rules()
        bids = vals.get("bids", "")
        if not bids:
            return
        out = os.path.join(bids, "code", "sovabids", "rules.yml")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            yaml.dump(rules, f, default_flow_style=False)


def main() -> None:
    SovabidsApp().run()


if __name__ == "__main__":
    main()
