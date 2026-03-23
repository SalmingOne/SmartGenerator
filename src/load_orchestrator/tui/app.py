import io
import sys

from textual.app import App

from ..config import Config
from ..models import TestResult
from ..orchestrator import Orchestrator
from .screens.config_screen import ConfigScreen
from .screens.metrics_screen import MetricsScreen
from .screens.run_screen import RunScreen


class SmartGeneratorApp(App):
    TITLE = "SmartGenerator"
    SUB_TITLE = "Load Testing Orchestrator"
    CSS_PATH = "styles/app.tcss"

    def __init__(self):
        super().__init__()
        self.current_config: Config | None = None
        self.orchestrator: Orchestrator | None = None
        self.test_result: TestResult | None = None

    def on_mount(self) -> None:
        self.install_screen(ConfigScreen(), name="config")
        self.install_screen(RunScreen(), name="run")
        self.install_screen(MetricsScreen(), name="metrics")
        self.push_screen("config")


def run() -> None:
    # sys.stdout = io.StringIO()
    # sys.stderr = io.StringIO()
    app = SmartGeneratorApp()
    app.run()



if __name__ == "__main__":
    run()