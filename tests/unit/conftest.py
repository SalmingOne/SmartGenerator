import pytest
from datetime import datetime
from unittest.mock import MagicMock
from load_orchestrator.models import (
    RawMetrics, Decision, SpikeConfig,
)
from load_orchestrator.configuration import Config, AdapterConfig, StrategyConfig, OrchestratorConfig


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_metrics(
    users: int = 100,
    rps: float = 50.0,
    rt_avg: float = 100.0,
    p50: float = 80.0,
    p95: float = 200.0,
    p99: float = 400.0,
    error_rate: float = 0.0,
    failed_requests: int = 0,
    total_requests: int = 1000,
    timestamp: float | None = None,
) -> RawMetrics:
    return RawMetrics(
        timestamp=timestamp or datetime.now().timestamp(),
        users=users,
        rps=rps,
        rt_avg=rt_avg,
        p50=p50,
        p95=p95,
        p99=p99,
        error_rate=error_rate,
        failed_requests=failed_requests,
        total_requests=total_requests,
    )


# ── Mock adapter ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_adapter():
    """Мок адаптера. По умолчанию is_ready=True, get_stats возвращает здоровые метрики."""
    adapter = MagicMock()
    adapter.is_ready.return_value = True
    adapter.get_stats.return_value = make_metrics()
    adapter.launch.return_value = None
    adapter.stop.return_value = None
    adapter.shutdown.return_value = None
    adapter.configure.return_value = None
    return adapter


@pytest.fixture
def mock_adapter_degraded():
    """Адаптер, возвращающий деградировавшие метрики (высокий error_rate)."""
    adapter = MagicMock()
    adapter.is_ready.return_value = True
    adapter.get_stats.return_value = make_metrics(error_rate=60.0, rps=5.0)
    adapter.launch.return_value = None
    adapter.stop.return_value = None
    adapter.shutdown.return_value = None
    adapter.configure.return_value = None
    return adapter


@pytest.fixture
def mock_adapter_dead():
    """Адаптер, у которого stop/shutdown бросают исключение (locust упал)."""
    adapter = MagicMock()
    adapter.is_ready.return_value = False
    adapter.get_stats.side_effect = ConnectionError("Locust not responding")
    adapter.stop.side_effect = ConnectionError("Locust not responding")
    adapter.shutdown.side_effect = ConnectionError("Locust not responding")
    return adapter


# ── Mock strategy ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_strategy():
    """Стратегия, которая всегда говорит CONTINUE и прибавляет 10 пользователей."""
    strategy = MagicMock()
    strategy.decide.return_value = Decision.CONTINUE
    strategy.get_next_users.side_effect = lambda current, metrics: current + 10
    strategy.get_wait_time.return_value = 1
    strategy.reset.return_value = None
    return strategy


@pytest.fixture
def mock_strategy_stop():
    """Стратегия, которая сразу возвращает STOP."""
    strategy = MagicMock()
    strategy.decide.return_value = Decision.STOP
    strategy.get_next_users.return_value = 10
    strategy.get_wait_time.return_value = 1
    strategy.reset.return_value = None
    return strategy


@pytest.fixture
def mock_strategy_hold():
    """Стратегия, которая всегда возвращает HOLD (нагрузка не меняется)."""
    strategy = MagicMock()
    strategy.decide.return_value = Decision.HOLD
    strategy.get_next_users.return_value = 10
    strategy.get_wait_time.return_value = 1
    strategy.reset.return_value = None
    return strategy


# ── Config fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def base_config():
    """Минимальная корректная конфигурация для тестов оркестратора."""
    return Config(
        adapter=AdapterConfig(
            type="locust",
            test_file="tests/load_tests/locustfile.py",
            port=8089,
            host="0.0.0.0",
        ),
        strategy=StrategyConfig(
            type="degradation_search",
            params={"initial_users": 10, "step_multiplier": 1.5},
        ),
        orchestrator=OrchestratorConfig(
            spawn_rate=10,
            max_users=500,
            monitoring_interval=1,
            max_wait_time=300,
        ),
    )


@pytest.fixture
def spike_config():
    return SpikeConfig(
        baseline_users=10,
        baseline_duration=5,
        spike_users=100,
        spike_duration=10,
        recovery_users=10,
        recovery_duration=5,
    )


# ── Locust HTTP mock ──────────────────────────────────────────────────────────

LOCUST_STATS_RESPONSE = {
    "user_count": 100,
    "total_rps": 50.0,
    "fail_ratio": 0.02,
    "stats": [
        {
            "name": "Aggregated",
            "avg_response_time": 120.0,
            "median_response_time": 100.0,
            "response_time_percentile_0.95": 250.0,
            "response_time_percentile_0.99": 450.0,
            "num_requests": 5000,
            "num_failures": 100,
        }
    ],
}


@pytest.fixture
def mock_requests_session():
    """Мок requests.Session для LocustAdapter без реального HTTP."""
    session = MagicMock()
    session.get.return_value = MagicMock(
        status_code=200,
        json=MagicMock(return_value=LOCUST_STATS_RESPONSE),
    )
    session.post.return_value = MagicMock(status_code=200)
    return session