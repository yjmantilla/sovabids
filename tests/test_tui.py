import os
from pathlib import Path
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
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        await pilot.click("#browse-rules")
        await pilot.pause()
        # browse-rules opens the FILE picker, not the directory picker
        assert isinstance(app.screen, FilePickerScreen)
        # post a REAL DirectoryTree.FileSelected message so this also exercises
        # Textual's event dispatch (would catch a handler-name / convention change)
        tree = app.screen.query_one(DirectoryTree)
        app.screen.post_message(DirectoryTree.FileSelected(tree.root, Path(str(rules_yml))))
        await pilot.pause()
        await pilot.click("#ok")
        await pilot.pause()
        assert not isinstance(app.screen, FilePickerScreen)
        assert app.query_one("#rules-file-input", Input).value == str(rules_yml)


@pytest.mark.anyio
async def test_tui_rules_picker_directory_click_cannot_override_file(tmp_path):
    """#89 core hazard: in file mode a directory selection never becomes the confirmable value."""
    from sovabids.tui import FilePickerScreen
    rules_yml = tmp_path / "rules.yml"
    rules_yml.write_text("a: 1\n")
    sub1 = tmp_path / "s1"
    sub1.mkdir()
    sub2 = tmp_path / "s2"
    sub2.mkdir()
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        await pilot.click("#browse-rules")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, FilePickerScreen)
        tree = screen.query_one(DirectoryTree)
        # a directory selection alone leaves the confirmable value empty (file mode)
        screen.post_message(DirectoryTree.DirectorySelected(tree.root, Path(str(sub1))))
        await pilot.pause()
        assert screen._selected == ""
        # choose a file, then select another directory -> the file still wins
        screen.post_message(DirectoryTree.FileSelected(tree.root, Path(str(rules_yml))))
        await pilot.pause()
        screen.post_message(DirectoryTree.DirectorySelected(tree.root, Path(str(sub2))))
        await pilot.pause()
        await pilot.click("#ok")
        await pilot.pause()
        assert app.query_one("#rules-file-input", Input).value == str(rules_yml)


@pytest.mark.anyio
async def test_tui_picker_double_click_enters_folder(tmp_path):
    """Double-clicking a folder navigates into it (re-roots the tree)."""
    from sovabids.tui import FilePickerScreen
    child = tmp_path / "child"
    child.mkdir()
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        app.query_one("#rules-file-input", Input).value = str(tmp_path)
        await pilot.pause()
        await pilot.click("#browse-rules")
        await pilot.pause()
        screen = app.screen
        tree = screen.query_one(DirectoryTree)
        assert str(tree.path) == str(tmp_path)
        # two quick selections of the same folder == a double-click -> enter it
        msg = DirectoryTree.DirectorySelected(tree.root, Path(str(child)))
        screen.on_directory_tree_directory_selected(msg)
        screen.on_directory_tree_directory_selected(msg)
        await pilot.pause()
        assert str(tree.path) == str(child)


@pytest.mark.anyio
async def test_tui_dir_picker_returns_directory(dummy_source):
    """Positive directory-mode: the source/BIDS picker returns the confirmed directory."""
    from sovabids.tui import DirPickerScreen
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click("#browse-source")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DirPickerScreen)
        tree = screen.query_one(DirectoryTree)
        screen.post_message(DirectoryTree.DirectorySelected(tree.root, Path(dummy_source)))
        await pilot.pause()
        await pilot.click("#ok")
        await pilot.pause()
        assert not isinstance(app.screen, DirPickerScreen)
        assert app.query_one("#source-input", Input).value == dummy_source


@pytest.mark.anyio
async def test_tui_dir_picker_create_folder(tmp_path):
    """The directory picker can make a new folder, step into it, and return it on OK."""
    from sovabids.tui import DirPickerScreen, FilePickerScreen
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # dir picker exposes the create-folder controls; file picker does not
        await pilot.click("#browse-bids")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, DirPickerScreen)
        assert screen.query("#new-folder-name") and screen.query("#mk-folder")

        # start it in a known place, name a new folder, create it
        screen._reroot(str(tmp_path))
        await pilot.pause()
        screen.query_one("#new-folder-name", Input).value = "bids_out"
        await pilot.click("#mk-folder")
        await pilot.pause()
        made = tmp_path / "bids_out"
        assert made.is_dir()                       # created on disk
        assert screen._root == str(made)           # stepped into it
        assert screen._selected == str(made)       # pre-selected

        await pilot.click("#ok")
        await pilot.pause()
        assert not isinstance(app.screen, DirPickerScreen)
        assert app.query_one("#bids-input", Input).value == str(made)

    # the FILE picker has no folder-creation controls (dir-only feature)
    app2 = SovabidsApp()
    async with app2.run_test(size=(120, 40)) as pilot:
        app2.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        await pilot.click("#browse-rules")
        await pilot.pause()
        assert isinstance(app2.screen, FilePickerScreen)
        assert not app2.screen.query("#new-folder-name")
        assert not app2.screen.query("#mk-folder")


@pytest.mark.anyio
async def test_tui_rules_picker_ok_requires_file(tmp_path):
    """OK with only directory navigation (no file chosen) must not return a directory."""
    from sovabids.tui import FilePickerScreen
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
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
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
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
async def test_tui_rules_file_locks_builder(tmp_path):
    """Loading a rules file (in the Rules tab) greys out the manual builder below it;
    it wins at Generate time (#89). Clearing the field unlocks the builder again."""
    rules_yml = tmp_path / "rules.yml"
    rules_yml.write_text("a: 1\n")
    app = SovabidsApp()
    async with app.run_test(size=(120, 50)) as pilot:
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        builder = app.query_one("#rules-builder")
        note = app.query_one("#rules-lock-note", Static)

        # starts unlocked
        assert builder.disabled is False
        assert "locked" not in note.classes

        # loading a rules file locks the builder (picker path too — .value posts Input.Changed)
        app.query_one("#rules-file-input", Input).value = str(rules_yml)
        await pilot.pause()
        assert builder.disabled is True
        assert "locked" in note.classes

        # clearing the field unlocks it
        app.query_one("#rules-file-input", Input).value = ""
        await pilot.pause()
        assert builder.disabled is False
        assert "locked" not in note.classes


@pytest.mark.anyio
async def test_tui_save_rules_feedback(tmp_path):
    """Ctrl+S notifies on save; it refuses to write (with a warning) when the BIDS
    dir is unset or a rules file is loaded."""
    bids = tmp_path / "bids"
    out = bids / "code" / "sovabids" / "rules.yml"
    app = SovabidsApp()
    async with app.run_test(size=(120, 50)) as pilot:
        # no BIDS dir -> no write, but a toast explains why
        app.action_save_rules()
        await pilot.pause()
        assert not out.exists()
        assert len(list(app._notifications)) >= 1

        # BIDS set, no rules file -> writes and notifies
        app.query_one("#bids-input", Input).value = str(bids)
        await pilot.pause()
        app.action_save_rules()
        await pilot.pause()
        assert out.exists()

        # a loaded rules file wins -> builder save is refused (no overwrite)
        out.unlink()
        app.query_one("#rules-file-input", Input).value = str(tmp_path / "external.yml")
        await pilot.pause()
        app.action_save_rules()
        await pilot.pause()
        assert not out.exists()


@pytest.mark.anyio
async def test_tui_save_mappings_requires_bids(tmp_path, monkeypatch):
    """Saving mappings reports status; without a BIDS dir it warns instead of
    silently writing mappings.yml into the current working directory."""
    monkeypatch.chdir(tmp_path)          # so any accidental relative write lands here
    app = SovabidsApp()
    async with app.run_test(size=(120, 50)) as pilot:
        mp = app.query_one("MappingsPane")

        # nothing generated -> "generate first"
        mp._save_mappings_yaml()
        await pilot.pause()
        assert "generate" in str(app.query_one("#mappings-status", Static).render()).lower()

        # a mapping exists but the BIDS dir is empty -> guarded, no CWD write
        app._mapping_data = {"Individual": [{"IO": {"source": "a", "target": "b"}}]}
        mp._save_mappings_yaml()
        await pilot.pause()
        assert "bids output" in str(app.query_one("#mappings-status", Static).render()).lower()
        assert not (tmp_path / "code" / "sovabids" / "mappings.yml").exists()

        # set the BIDS dir -> writes and reports the real path
        bids = tmp_path / "bids"
        app.query_one("#bids-input", Input).value = str(bids)
        await pilot.pause()
        mp._save_mappings_yaml()
        await pilot.pause()
        assert (bids / "code" / "sovabids" / "mappings.yml").exists()


@pytest.mark.anyio
async def test_tui_picker_navigation(tmp_path):
    """The picker can leave the seed folder: Up climbs to the parent, the location bar jumps anywhere."""
    from sovabids.tui import FilePickerScreen
    child = tmp_path / "child"
    child.mkdir()
    app = SovabidsApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        app.query_one("#rules-file-input", Input).value = str(child)
        await pilot.pause()
        await pilot.click("#browse-rules")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, FilePickerScreen)
        tree = screen.query_one(DirectoryTree)
        assert str(tree.path) == str(child)  # rooted at the seeded folder

        # Up -> parent directory
        await pilot.click("#go-up")
        await pilot.pause()
        assert str(tree.path) == str(tmp_path)

        # location bar -> jump straight to an arbitrary directory
        loc = screen.query_one("#loc-input", Input)
        loc.focus()
        await pilot.pause()
        loc.value = str(child)
        await pilot.press("enter")
        await pilot.pause()
        assert str(tree.path) == str(child)


@pytest.mark.anyio
async def test_tui_rules_shows_sample_paths(dummy_source):
    """Opening the Rules tab lists a couple of real source paths so the user can
    build the pattern from them; clearing the source hides them again."""
    from textual.widgets import Select
    app = SovabidsApp()
    async with app.run_test(size=(120, 50)) as pilot:
        app.query_one("#source-input", Input).value = dummy_source
        await pilot.pause()
        app.query_one("TabbedContent").active = "tab-rules"
        await pilot.pause()
        app.query_one("#ext-select", Select).value = ".vhdr"

        stat = app.query_one("#sample-paths", Static)
        for _ in range(30):                       # wait for the threaded scan
            await anyio.sleep(0.1)
            await pilot.pause()
            if stat.display:
                break
        assert stat.display is True
        text = str(stat.render())
        assert "build your pattern" in text.lower()
        assert ".vhdr" in text                    # a real matched file is listed

        # clearing the source hides the sample block
        app.query_one("#source-input", Input).value = ""
        app.query_one("RulesPane")._run_ext_count()
        await pilot.pause()
        assert app.query_one("#sample-paths", Static).display is False


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

        # Click "Show all" (scroll it into view first — the sample-paths block
        # can push it below the fold in a small test viewport)
        btn.scroll_visible()
        await pilot.pause()
        await pilot.click("#show-files")
        await pilot.pause()
        
        from sovabids.tui import FilesListScreen
        assert isinstance(app.screen, FilesListScreen)
        
        # Close modal
        await pilot.click("#close-files")
        await pilot.pause()
        assert not isinstance(app.screen, FilesListScreen)
