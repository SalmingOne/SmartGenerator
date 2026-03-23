from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Label, Static


class FilteredTree(DirectoryTree):
    """DirectoryTree with file extension filter."""

    def __init__(self, path: str, filter_glob: str = "*", **kwargs):
        super().__init__(path, **kwargs)
        self.filter_glob = filter_glob

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        return [
            p for p in paths
            if p.is_dir() or p.match(self.filter_glob)
        ]


class FilePicker(ModalScreen[str | None]):
    """Modal file picker. Returns selected path string or None on cancel."""

    DEFAULT_CSS = """
    FilePicker {
        align: center middle;
    }
    #file-picker-dialog {
        width: 70;
        height: 30;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #file-picker-dialog .picker-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #file-picker-dialog DirectoryTree {
        height: 1fr;
        margin: 1 0;
        border: solid $secondary;
    }
    #file-picker-dialog #selected-label {
        height: 1;
        margin: 1 0 0 0;
        color: $text;
    }
    #file-picker-dialog .button-row {
        height: 3;
        align: right middle;
    }
    #file-picker-dialog .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        root: str = ".",
        filter_glob: str = "*",
        title: str = "Select File",
    ):
        super().__init__()
        self.root = str(Path(root).resolve())
        self.filter_glob = filter_glob
        self.picker_title = title
        self.selected_path: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="file-picker-dialog"):
            yield Static(self.picker_title, classes="picker-title")
            yield FilteredTree(self.root, filter_glob=self.filter_glob)
            yield Label("Selected: —", id="selected-label")
            with Horizontal(classes="button-row"):
                yield Button("Cancel", id="cancel_btn")
                yield Button.success("Select", id="select_btn", disabled=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        try:
            rel = event.path.relative_to(Path.cwd())
            self.selected_path = f"./{rel}"
        except ValueError:
            self.selected_path = str(event.path)
        self.query_one("#selected-label", Label).update(
            f"Selected: {self.selected_path}"
        )
        self.query_one("#select_btn", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "select_btn":
            self.dismiss(self.selected_path)
        elif event.button.id == "cancel_btn":
            self.dismiss(None)

    def key_escape(self):
        self.dismiss(None)