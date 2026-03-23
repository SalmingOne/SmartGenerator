from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from ...models import RawMetrics

try:
    from textual_plotext import PlotextPlot

    HAS_PLOTEXT = True
except ImportError:
    HAS_PLOTEXT = False


class MetricsScreen(Screen):
    BINDINGS = [
        ("f1", "app.switch_screen('config')", "Config"),
        ("f2", "app.switch_screen('run')", "Run"),
        ("f3", "app.switch_screen('metrics')", "Metrics"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._poll_timer = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        if not HAS_PLOTEXT:
            yield Static(
                "textual-plotext not installed. Run: pip install textual-plotext",
                id="no-plotext-warning",
            )
            yield Footer()
            return

        with TabbedContent(id="metrics-tabs"):
            with TabPane("RPS & Users", id="tab-rps"):
                yield PlotextPlot(id="chart_rps")
                yield PlotextPlot(id="chart_users")
            with TabPane("Response Times", id="tab-rt"):
                yield PlotextPlot(id="chart_rt")
            with TabPane("Errors", id="tab-errors"):
                yield PlotextPlot(id="chart_error_rate")
                yield PlotextPlot(id="chart_failed")

        yield Footer()

    def on_screen_resume(self) -> None:
        if HAS_PLOTEXT:
            self._refresh_charts()
            if self._poll_timer is None:
                self._poll_timer = self.set_interval(2.0, self._refresh_charts)

    def on_screen_suspend(self) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

    def on_mount(self) -> None:
        if HAS_PLOTEXT:
            self._poll_timer = self.set_interval(2.0, self._refresh_charts)

    def _get_history(self) -> list[RawMetrics]:
        orch = getattr(self.app, "orchestrator", None)
        if orch is not None and orch.history:
            return orch.history[:]

        result = getattr(self.app, "test_result", None)
        if result is not None and result.history:
            return result.history[:]

        return []

    def _refresh_charts(self) -> None:
        if not HAS_PLOTEXT:
            return

        history = self._get_history()
        if not history:
            return

        t0 = history[0].timestamp
        xs = [m.timestamp - t0 for m in history]

        self._update_rps_chart(xs, history)
        self._update_users_chart(xs, history)
        self._update_rt_chart(xs, history)
        self._update_error_rate_chart(xs, history)
        self._update_failed_chart(xs, history)

    def _update_rps_chart(self, xs: list, history: list[RawMetrics]) -> None:
        try:
            chart = self.query_one("#chart_rps", PlotextPlot)
        except Exception:
            return
        plt = chart.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("RPS")
        plt.xlabel("Time (s)")
        plt.ylabel("req/s")
        plt.plot(xs, [m.rps for m in history])
        chart.refresh()

    def _update_users_chart(self, xs: list, history: list[RawMetrics]) -> None:
        try:
            chart = self.query_one("#chart_users", PlotextPlot)
        except Exception:
            return
        plt = chart.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Users")
        plt.xlabel("Time (s)")
        plt.ylabel("users")
        plt.plot(xs, [m.users for m in history])
        chart.refresh()

    def _update_rt_chart(self, xs: list, history: list[RawMetrics]) -> None:
        try:
            chart = self.query_one("#chart_rt", PlotextPlot)
        except Exception:
            return
        plt = chart.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Response Times (ms)")
        plt.xlabel("Time (s)")
        plt.ylabel("ms")
        plt.plot(xs, [m.rt_avg for m in history], label="avg")
        plt.plot(xs, [m.p50 for m in history], label="p50")
        plt.plot(xs, [m.p95 for m in history], label="p95")
        plt.plot(xs, [m.p99 for m in history], label="p99")
        chart.refresh()

    def _update_error_rate_chart(self, xs: list, history: list[RawMetrics]) -> None:
        try:
            chart = self.query_one("#chart_error_rate", PlotextPlot)
        except Exception:
            return
        plt = chart.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Error Rate (%)")
        plt.xlabel("Time (s)")
        plt.ylabel("%")
        plt.plot(xs, [m.error_rate for m in history])
        chart.refresh()

    def _update_failed_chart(self, xs: list, history: list[RawMetrics]) -> None:
        try:
            chart = self.query_one("#chart_failed", PlotextPlot)
        except Exception:
            return
        plt = chart.plt
        plt.clear_data()
        plt.clear_figure()
        plt.title("Failed Requests")
        plt.xlabel("Time (s)")
        plt.ylabel("count")
        plt.plot(xs, [m.failed_requests for m in history])
        chart.refresh()