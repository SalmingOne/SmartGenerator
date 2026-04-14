from unittest.mock import MagicMock
from load_orchestrator.adapters.LocustAdapter import LocustAdapter


def make_adapter(session):
    """Создаёт адаптер без реального запуска locust."""
    adapter = LocustAdapter.__new__(LocustAdapter)
    adapter._session = session
    adapter._host = "http://0.0.0.0:8089"
    adapter._process = None
    adapter.log_file = MagicMock()
    adapter.log_file.closed = False
    return adapter


class TestLocustAdapterIsReady:
    def test_returns_true_when_locust_responds_200(self):
        session = MagicMock()
        session.get.return_value = MagicMock(status_code=200)
        adapter = make_adapter(session)

        assert adapter.is_ready() is True

    def test_returns_false_on_connection_error(self):
        session = MagicMock()
        session.get.side_effect = ConnectionError()
        adapter = make_adapter(session)

        assert adapter.is_ready() is False


class TestLocustAdapterGetStats:
    def test_maps_response_to_raw_metrics(self):
        session = MagicMock()
        session.get.return_value = MagicMock(json=lambda: {
            "user_count": 50,
            "total_rps": 30.0,
            "fail_ratio": 0.0,
            "stats": [{"name": "Aggregated", "avg_response_time": 100,
                        "median_response_time": 90, "response_time_percentile_0.95": 200,
                        "response_time_percentile_0.99": 300,
                        "num_requests": 1000, "num_failures": 0}]
        })
        adapter = make_adapter(session)
        metrics = adapter.get_stats()

        assert metrics.users == 50
        assert metrics.rps == 30.0
        assert metrics.p95 == 200

    def test_converts_fail_ratio_to_percent(self):
        session = MagicMock()
        session.get.return_value = MagicMock(json=lambda: {
            "user_count": 100, "total_rps": 50.0, "fail_ratio": 0.05,
            "stats": [{"name": "Aggregated", "avg_response_time": 0,
                        "median_response_time": 0, "response_time_percentile_0.95": 0,
                        "response_time_percentile_0.99": 0,
                        "num_requests": 0, "num_failures": 0}]
        })
        adapter = make_adapter(session)
        metrics = adapter.get_stats()

        assert metrics.error_rate == 5.0


class TestLocustAdapterShutdown:
    def test_terminates_process_and_closes_log_file(self):
        session = MagicMock()
        adapter = make_adapter(session)
        adapter._process = MagicMock()

        adapter.shutdown()

        adapter.log_file.close.assert_called_once_with()