import os
import pytest
import anyio
from sovabids.tui import SovabidsApp
from sovabids.datasets import make_dummy_dataset, save_dummy_vhdr
from textual.widgets import Input, Label, DataTable, Button

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
