import time

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static
from textual.worker import Worker, WorkerState

from ...factory import OrchestratorFactory
from ...models import State


def _format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class RunScreen(Screen):
    BINDINGS = [
        ("f1", "app.switch_screen('config')", "Config"),
        ("f2", "app.switch_screen('run')", "Run"),
        ("f3", "app.switch_screen('metrics')", "Metrics"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_history_len = 0
        self._poll_timer = None
        self._worker: Worker | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="status-bar"):
            yield Static("Status: IDLE", id="status_label")
            yield Static("Strategy: —", id="strategy_label")
            yield Static("Elapsed: 00:00:00", id="elapsed_label")

        with Horizontal(id="metrics-bar"):
            with Vertical(classes="metric-card"):
                yield Static("—", id="mc_users", classes="metric-value")
                yield Static("Users", classes="metric-label")
            with Vertical(classes="metric-card"):
                yield Static("—", id="mc_rps", classes="metric-value")
                yield Static("RPS", classes="metric-label")
            with Vertical(classes="metric-card"):
                yield Static("—", id="mc_p95", classes="metric-value")
                yield Static("P95 (ms)", classes="metric-label")
            with Vertical(classes="metric-card"):
                yield Static("—", id="mc_errors", classes="metric-value")
                yield Static("Error %", classes="metric-label")

        yield RichLog(id="log-panel", highlight=True, markup=True)

        with Horizontal(id="run-button-bar"):
            yield Button.success("Start Test", id="start_btn")
            yield Button.error("Stop Test", id="stop_btn", disabled=True)
            yield Button("View Metrics (F3)", id="metrics_btn")

        yield Footer()

    def on_screen_resume(self) -> None:
        """Called when screen becomes active again."""
        self._update_button_states()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_btn":
            self._start_test()
        elif event.button.id == "stop_btn":
            self._stop_test()
        elif event.button.id == "metrics_btn":
            self.app.switch_screen("metrics")

    def _start_test(self) -> None:
        config = getattr(self.app, "current_config", None)
        if config is None:
            self.notify("No config loaded. Go to Config screen first.", severity="error")
            return

        orch = getattr(self.app, "orchestrator", None)
        if orch is not None and orch.state == State.RUNNING:
            self.notify("Test is already running", severity="warning")
            return

        log = self.query_one("#log-panel", RichLog)
        log.clear()
        self._last_history_len = 0

        try:
            self.app.orchestrator = OrchestratorFactory.create_orchestrator(config)
        except Exception as e:
            self.notify(f"Error creating orchestrator: {e}", severity="error")
            log.write(f"[red]Error: {e}[/red]")
            return

        strategy_name = config.strategy.type
        self.query_one("#strategy_label", Static).update(f"Strategy: {strategy_name}")
        self.query_one("#status_label", Static).update("Status: STARTING")
        log.write(f"[green]Starting test with strategy: {strategy_name}[/green]")

        self.query_one("#start_btn", Button).disabled = True
        self.query_one("#stop_btn", Button).disabled = False

        self._worker = self.run_worker(self._run_test, thread=True, exclusive=True)
        self._poll_timer = self.set_interval(1.0, self._poll_metrics)

    def _run_test(self) -> None:
        result = self.app.orchestrator.run()
        self.app.test_result = result

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is not self._worker:
            return
        if event.state == WorkerState.SUCCESS:
            self._on_test_finished()
        elif event.state == WorkerState.ERROR:
            self._on_test_error(event.worker.error)

    def _on_test_finished(self) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        # Final poll to capture all remaining metrics
        self._poll_metrics()

        result = getattr(self.app, "test_result", None)
        status = "FINISHED"
        if result:
            status = f"FINISHED ({result.stop_reason.name})"

        self.query_one("#status_label", Static).update(f"Status: {status}")
        self.query_one("#start_btn", Button).disabled = False
        self.query_one("#stop_btn", Button).disabled = True

        log = self.query_one("#log-panel", RichLog)
        log.write("")
        log.write("[bold green]═══ Test Finished ═══[/bold green]")
        if result:
            log.write(f"  Stop Reason: {result.stop_reason.name}")
            log.write(f"  Max Stable Users: {result.max_stable_users}")
            log.write(f"  Max Stable RPS: {result.max_stable_rps:.1f}")
            if result.started_at and result.finished_at:
                dur = result.finished_at - result.started_at
                log.write(f"  Duration: {_format_duration(dur)}")
            log.write(f"  Data Points: {len(result.history)}")

    def _on_test_error(self, error: BaseException | None) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        self.query_one("#status_label", Static).update("Status: ERROR")
        self.query_one("#start_btn", Button).disabled = False
        self.query_one("#stop_btn", Button).disabled = True

        log = self.query_one("#log-panel", RichLog)
        log.write(f"[bold red]Test error: {error}[/bold red]")

    def _stop_test(self) -> None:
        orch = getattr(self.app, "orchestrator", None)
        if orch is not None:
            orch.stop()
            self.query_one("#log-panel", RichLog).write(
                "[yellow]Stop requested...[/yellow]"
            )

    def _poll_metrics(self) -> None:
        orch = getattr(self.app, "orchestrator", None)
        if orch is None:
            return

        history = orch.history
        new_count = len(history)

        if new_count > self._last_history_len:
            latest = history[-1]

            self.query_one("#mc_users", Static).update(str(latest.users))
            self.query_one("#mc_rps", Static).update(f"{latest.rps:.1f}")
            self.query_one("#mc_p95", Static).update(f"{latest.p95:.0f}")
            self.query_one("#mc_errors", Static).update(f"{latest.error_rate:.1f}%")

            log = self.query_one("#log-panel", RichLog)
            for i in range(self._last_history_len, new_count):
                m = history[i]
                log.write(
                    f"[dim]#{i+1}[/dim] "
                    f"users={m.users} "
                    f"rps={m.rps:.1f} "
                    f"p50={m.p50:.0f} "
                    f"p95={m.p95:.0f} "
                    f"p99={m.p99:.0f} "
                    f"err={m.error_rate:.1f}%"
                )

            self._last_history_len = new_count

        if orch.state == State.RUNNING:
            self.query_one("#status_label", Static).update("Status: RUNNING")

        if orch.started_at:
            elapsed = time.time() - orch.started_at
            self.query_one("#elapsed_label", Static).update(
                f"Elapsed: {_format_duration(elapsed)}"
            )

    def _update_button_states(self) -> None:
        orch = getattr(self.app, "orchestrator", None)
        running = orch is not None and orch.state == State.RUNNING
        self.query_one("#start_btn", Button).disabled = running
        self.query_one("#stop_btn", Button).disabled = not running