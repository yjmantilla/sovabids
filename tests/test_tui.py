import os
import types
import pytest
import anyio
from sovabids.tui import SovabidsApp
from sovabids.datasets import make_dummy_dataset, save_dummy_vhdr
from textual.widgets import Input, Label, DataTable, Button, Static, DirectoryTree

@pytest.fixture
def dummy_source(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    # save_dummy_vhdr returns a list of files [vhdr, eeg, vmrk]
    example_files = save_dummy_vhdr(str(tmp_path / "example.vhdr"))
    make_dummy_dataset(
        EXAMPLE=example_files,
        PATTERN="sub-%subject%_task-%task%_run-%run%",
        ROOT=str(source_dir),
        NSUBS=1,
        NTASKS=1,
        NRUNS=1,
        NSESSIONS=1
    )
    return str(source_dir)

@pytest.mark.anyio
async def test_tui_flow(dummy_source, tmp_path):
    bids_output = tmp_path / "bids"
    bids_output.mkdir()
    
    app = SovabidsApp()
    # Use a large size to avoid layout issues in tests
    async with app.run_test(size=(120, 40)) as pilot:
        # --- TAB 1: SETUP ---
        # Switch to setup tab first just in case
        app.query_one("TabbedContent").active = "tab-setup"
        await pilot.pause()
        
        # Set values
        app.query_one("#source-input", Input).value = dummy_source
        app.query_one("#bids-input", Input).value = str(bids_output)
        await pilot.pause()
        
        # --- TAB 2: RULES ---
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        
        # Set extension explicitly
        from textual.widgets import Select
        app.query_one("#ext-select", Select).value = ".vhdr"
        
        # Set a pattern that avoids greedy matching of the whole path
        rules_pane = app.query_one("RulesPane")
        rules_pane.query_one("#pattern-input", Input).value = "sub-%subject%_task-%task%_run-%run%.vhdr"
        # Set dataset name to ensure dataset_description.json is created
        rules_pane.query_one("#ds-name-input", Input).value = "Test Dataset"
        rules_pane._schedule_preview()
        
        # Wait longer for worker
        await anyio.sleep(15)
        await pilot.pause()
        
        preview_label = app.query_one("#preview-label", Label)
        content = str(preview_label.content)
        assert "1 file(s) matched" in content
        
        # --- TAB 3: MAPPINGS ---
        app.query_one("TabbedContent").active = "tab-mappings"
        await pilot.pause()
        
        await pilot.click("#gen-mappings")
        # Generator is a worker thread
        await anyio.sleep(15)
        await pilot.pause()
        
        table = app.query_one("#mappings-table", DataTable)
        assert table.row_count == 1
        assert app._mapping_data is not None
        
        # --- TAB 4: CONVERT ---
        app.query_one("TabbedContent").active = "tab-convert"
        await pilot.pause()
        
        # Call start_convert directly to avoid any pilot click issues
        app.query_one("ConvertPane")._start_convert()
        
        # Conversion worker thread - can be slow
        await anyio.sleep(60.0)
        await pilot.pause()
        
        # Verify BIDS output
        assert os.path.exists(os.path.join(bids_output, "dataset_description.json"))
        assert os.path.exists(os.path.join(bids_output, "sub-SU0"))
        # Check for a specific BIDS file
        # The exact filename might vary depending on how SU0 and TA0 are handled, 
        # but dataset_description.json is a sure sign of success.

@pytest.mark.anyio
async def test_tui_dir_picker(dummy_source):
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click("#browse-source")
        # Modal should be pushed
        from sovabids.tui import DirPickerScreen
        assert isinstance(app.screen, DirPickerScreen)
        
        # Cancel should dismiss it
        await pilot.click("#cancel")
        await pilot.pause()
        assert not isinstance(app.screen, DirPickerScreen)

@pytest.mark.anyio
async def test_tui_rules_picker_returns_file(tmp_path):
    """#89: the rules-file browser must return the file you pick, not a directory."""
    from sovabids.tui import FilePickerScreen
    rules_yml = tmp_path / "rules.yml"
    rules_yml.write_text("non-bids:\n  eeg_extension: .vhdr\n")
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click("#browse-rules")
        await pilot.pause()
        # browse-rules opens the FILE picker, not the directory picker
        assert isinstance(app.screen, FilePickerScreen)
        # a file selection sets the confirmable value; OK returns it
        app.screen.on_directory_tree_file_selected(
            types.SimpleNamespace(path=str(rules_yml))
        )
        await pilot.click("#ok")
        await pilot.pause()
        assert not isinstance(app.screen, FilePickerScreen)
        assert app.query_one("#rules-file-input", Input).value == str(rules_yml)


@pytest.mark.anyio
async def test_tui_rules_picker_ok_requires_file(tmp_path):
    """OK with only directory navigation (no file chosen) must not return a directory."""
    from sovabids.tui import FilePickerScreen
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click("#browse-rules")
        await pilot.pause()
        assert isinstance(app.screen, FilePickerScreen)
        # nothing (no file) selected -> OK is a no-op, modal stays open
        await pilot.click("#ok")
        await pilot.pause()
        assert isinstance(app.screen, FilePickerScreen)
        await pilot.click("#cancel")
        await pilot.pause()
        assert app.query_one("#rules-file-input", Input).value == ""


@pytest.mark.anyio
async def test_tui_rules_picker_reopen_from_file(tmp_path):
    """Reopening the picker when the input holds a file must root the tree at its directory."""
    from sovabids.tui import FilePickerScreen
    rules_yml = tmp_path / "rules.yml"
    rules_yml.write_text("a: 1\n")
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#rules-file-input", Input).value = str(rules_yml)
        await pilot.pause()
        await pilot.click("#browse-rules")
        await pilot.pause()
        assert isinstance(app.screen, FilePickerScreen)
        tree = app.screen.query_one(DirectoryTree)
        # tree root is the file's parent directory, not the file itself
        assert str(tree.path) == str(tmp_path)


@pytest.mark.anyio
async def test_tui_generate_rejects_nonfile_rules(dummy_source, tmp_path):
    """A rules-file box holding a non-file (the #89 directory) must error, not silently fall back."""
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#source-input", Input).value = dummy_source
        app.query_one("#bids-input", Input).value = str(tmp_path / "bids")
        # point the rules-file box at a DIRECTORY (what the old broken picker returned)
        app.query_one("#rules-file-input", Input).value = str(tmp_path)
        await pilot.pause()
        mp = app.query_one("MappingsPane")
        mp._generate()
        await pilot.pause()
        # must surface an error and NOT build mappings from the Rules tab
        assert getattr(app, "_mapping_data", None) is None
        status = str(app.query_one("#mappings-status", Static).render()).lower()
        assert "not found" in status


@pytest.mark.anyio
async def test_tui_files_modal(dummy_source):
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Setup source
        app.query_one("TabbedContent").active = "tab-setup"
        await pilot.pause()
        app.query_one("#source-input", Input).value = dummy_source
        await pilot.pause()
        
        # Rules tab
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        
        # Set extension explicitly
        from textual.widgets import Select
        app.query_one("#ext-select", Select).value = ".vhdr"
        
        rules_pane = app.query_one("RulesPane")
        rules_pane.query_one("#pattern-input", Input).value = "sub-%subject%_task-%task%_run-%run%.vhdr"
        rules_pane._schedule_preview()
        
        # Wait for worker
        await anyio.sleep(15)
        await pilot.pause()
        
        # Check if button is enabled
        btn = app.query_one("#show-files", Button)
        assert not btn.disabled
        
        # Click "Show all"
        await pilot.click("#show-files")
        await pilot.pause()
        
        from sovabids.tui import FilesListScreen
        assert isinstance(app.screen, FilesListScreen)
        
        # Close modal
        await pilot.click("#close-files")
        await pilot.pause()
        assert not isinstance(app.screen, FilesListScreen)
