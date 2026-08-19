from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from ...configuration import AdapterConfig, Config, OrchestratorConfig, StrategyConfig
from ...tui.strategy_params import ADAPTER_TYPES, STRATEGY_TYPES
from ...tui.widgets.strategy_form import StrategyForm
from ...tui.screens.file_picker import FilePicker


class ConfigScreen(Screen):
    BINDINGS = [
        ("f1", "app.switch_screen('config')", "Config"),
        ("f2", "goto_run", "Run"),
        ("f3", "app.switch_screen('metrics')", "Metrics"),
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="header-bar"):
            yield Button("Load YAML", id="load_btn", variant="default")
            yield Button("Save YAML", id="save_btn", variant="default")
            yield Button.success("Start Test", id="start_btn")

        with VerticalScroll():
            # Load/Save path
            with Vertical(classes="config-section"):
                yield Static("File Path", classes="section-title")
                with Horizontal(classes="form-group"):
                    yield Label("YAML Path:")
                    yield Input(
                        value="./configs/degradation.yaml",
                        id="yaml_path",
                        placeholder="Path to YAML config",
                    )
                    yield Button("Browse", id="browse_yaml", classes="browse-btn")
            # Adapter section
            with Vertical(classes="config-section"):
                yield Static("Adapter", classes="section-title")
                with Horizontal(classes="form-group"):
                    yield Label("Type:")
                    yield Select(
                        [(t, t) for t in ADAPTER_TYPES],
                        value="locust",
                        id="adapter_type",
                    )
                with Horizontal(classes="form-group"):
                    yield Label("Test File:")
                    yield Input(
                        id="test_file",
                        placeholder="Path to test file",
                    )
                    yield Button("Browse", id="browse_test_file", classes="browse-btn")
                with Horizontal(classes="form-group"):
                    yield Label("Host:")
                    yield Input(value="0.0.0.0", id="host")
                with Horizontal(classes="form-group"):
                    yield Label("Port:")
                    yield Input(value="8089", id="port", placeholder="int")

            # Strategy section
            with Vertical(classes="config-section"):
                yield Static("Strategy", classes="section-title")
                with Horizontal(classes="form-group"):
                    yield Label("Type:")
                    yield Select(
                        [(t, t) for t in STRATEGY_TYPES],
                        value="degradation_search",
                        id="strategy_type",
                    )
                yield StrategyForm(id="strategy_form")

            # Orchestrator section
            with Vertical(classes="config-section"):
                yield Static("Orchestrator", classes="section-title")
                with Horizontal(classes="form-group"):
                    yield Label("Spawn Rate:")
                    yield Input(value="10", id="spawn_rate", placeholder="int")
                with Horizontal(classes="form-group"):
                    yield Label("Max Users (optional):")
                    yield Input(value="", id="max_users", placeholder="int or empty")
                with Horizontal(classes="form-group"):
                    yield Label("Monitoring Interval (sec):")
                    yield Input(value="5", id="monitoring_interval", placeholder="int")

        yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "strategy_type":
            form = self.query_one("#strategy_form", StrategyForm)
            form.strategy_type = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load_btn":
            self._load_yaml()
        elif event.button.id == "save_btn":
            self._save_yaml()
        elif event.button.id == "start_btn":
            self._start_test()
        elif event.button.id == "browse_yaml":
            self.app.push_screen(
                FilePicker(
                    root=".",
                    filter_glob="*.yaml",
                    title="Select Config YAML",
                ),
                callback=self._on_yaml_selected,
            )
        elif event.button.id == "browse_test_file":
            self.app.push_screen(
                FilePicker(
                    root=".",
                    filter_glob="*.py",
                    title="Select Test File",
                ),
                callback=self._on_test_file_selected,
            )

    def _load_yaml(self) -> None:
        yaml_path = self.query_one("#yaml_path", Input).value.strip()
        if not yaml_path:
            self.notify("Enter a YAML path first", severity="error")
            return
        try:
            config = Config.from_yaml(yaml_path)
            self._populate_from_config(config)
            self.notify(f"Loaded: {yaml_path}", severity="information")
        except Exception as e:
            self.notify(f"Error loading: {e}", severity="error")

    def _populate_from_config(self, config: Config) -> None:
        self.query_one("#adapter_type", Select).value = config.adapter.type
        self.query_one("#test_file", Input).value = config.adapter.test_file
        self.query_one("#host", Input).value = config.adapter.host
        self.query_one("#port", Input).value = str(config.adapter.port)

        self.query_one("#strategy_type", Select).value = config.strategy.type
        form = self.query_one("#strategy_form", StrategyForm)
        form.strategy_type = config.strategy.type
        # Give the form time to rebuild, then set values
        if config.strategy.params:
            self.set_timer(0.1, lambda: form.set_values(config.strategy.params))

        self.query_one("#spawn_rate", Input).value = str(config.orchestrator.spawn_rate)
        self.query_one("#max_users", Input).value = (
            str(config.orchestrator.max_users) if config.orchestrator.max_users else ""
        )
        self.query_one("#monitoring_interval", Input).value = str(
            config.orchestrator.monitoring_interval
        )

    def _build_config(self) -> Config:
        adapter = AdapterConfig(
            type=str(self.query_one("#adapter_type", Select).value),
            test_file=self.query_one("#test_file", Input).value.strip(),
            host=self.query_one("#host", Input).value.strip(),
            port=int(self.query_one("#port", Input).value.strip()),
        )

        strategy_type = str(self.query_one("#strategy_type", Select).value)
        form = self.query_one("#strategy_form", StrategyForm)
        params = form.get_values()

        strategy = StrategyConfig(
            type=strategy_type,
            params=params if params else None,
        )

        max_users_str = self.query_one("#max_users", Input).value.strip()
        orchestrator = OrchestratorConfig(
            spawn_rate=int(self.query_one("#spawn_rate", Input).value.strip()),
            max_users=int(max_users_str) if max_users_str else None,
            monitoring_interval=int(
                self.query_one("#monitoring_interval", Input).value.strip()
            ),
        )

        return Config(adapter=adapter, strategy=strategy, orchestrator=orchestrator)

    def _save_yaml(self) -> None:
        yaml_path = self.query_one("#yaml_path", Input).value.strip()
        if not yaml_path:
            self.notify("Enter a YAML path first", severity="error")
            return
        try:
            config = self._build_config()
            config.to_yaml(yaml_path)
            self.notify(f"Saved: {yaml_path}", severity="information")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    def _start_test(self) -> None:
        try:
            config = self._build_config()
            self.app.current_config = config
            self.app.switch_screen("run")
        except Exception as e:
            self.notify(f"Invalid config: {e}", severity="error")

    def _on_yaml_selected(self, path: str | None) -> None:
        if path:
            self.query_one("#yaml_path", Input).value = path
            self._load_yaml()

    def _on_test_file_selected(self, path: str | None) -> None:
        if path:
            self.query_one("#test_file", Input).value = path

    def action_goto_run(self) -> None:
        self.app.switch_screen("run")