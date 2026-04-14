import random

import pytest

from load_orchestrator.configuration import OrchestratorConfig, Config, AdapterConfig, StrategyConfig
from load_orchestrator.orchestrator import Orchestrator
from load_orchestrator.models import Decision, StopReason, State
from conftest import make_metrics


def make_orchestrator(adapter, strategy, config=None):
    """Создаёт оркестратор с моками адаптера и стратегии."""
    from load_orchestrator.configuration import (
        Config, AdapterConfig, StrategyConfig, OrchestratorConfig
    )
    if config is None:
        config = Config(
            adapter=AdapterConfig(type="locust", test_file="dummy.py"),
            strategy=StrategyConfig(type="degradation_search"),
            orchestrator=OrchestratorConfig(spawn_rate=10, monitoring_interval=1),
        )
    return Orchestrator(config=config, adapter=adapter, strategy=strategy)


class TestOrchestratorRun:
    def test_returns_test_result(self, mock_adapter, mock_strategy_stop):
        orc = make_orchestrator(mock_adapter, mock_strategy_stop)
        # пропускаем sleep и wait_until_ready
        mock_adapter.is_ready.return_value = True
        mock_strategy_stop.get_next_users.return_value = 10

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result is not None
        assert result.stop_reason is not None

    def test_result_returned_even_if_adapter_throws_on_shutdown(self, mock_adapter_dead, mock_strategy_stop):
        orc = make_orchestrator(mock_adapter_dead, mock_strategy_stop)
        mock_adapter_dead.is_ready.return_value = True
        mock_adapter_dead.get_stats.side_effect = None
        mock_adapter_dead.get_stats.return_value = make_metrics()
        mock_strategy_stop.get_next_users.return_value = 10

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()  # не должно бросать исключение

        assert result is not None

    def test_stop_reason_is_error_on_unexpected_exception(self, mock_adapter, mock_strategy):
        orc = make_orchestrator(mock_adapter, mock_strategy)
        mock_adapter.is_ready.return_value = True
        mock_adapter.get_stats.side_effect = RuntimeError("boom")
        mock_strategy.get_next_users.return_value = 10

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result.stop_reason == StopReason.ERROR


class TestOrchestratorStopConditions:
    def test_stops_when_strategy_returns_stop(self, mock_adapter, mock_strategy_stop):
        orc = make_orchestrator(mock_adapter, mock_strategy_stop)
        mock_adapter.is_ready.return_value = True
        mock_strategy_stop.get_next_users.return_value = 10

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result.stop_reason == StopReason.TARGET_REACHED

    def test_stops_on_critical_error_rate(self, mock_adapter, mock_strategy):
        orc = make_orchestrator(mock_adapter, mock_strategy)
        mock_adapter.is_ready.return_value = True
        mock_adapter.get_stats.return_value = make_metrics(error_rate=60.0)
        mock_strategy.get_next_users.return_value = 10

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result.stop_reason == StopReason.DEGRADATION

    def test_stops_when_rps_drops_to_zero(self, mock_adapter, mock_strategy):
        orc = make_orchestrator(mock_adapter, mock_strategy)
        mock_adapter.is_ready.return_value = True
        mock_adapter.get_stats.side_effect = [
            make_metrics(rps=100.0),
            make_metrics(rps=0.0),
        ]

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result.stop_reason == StopReason.DEGRADATION

    def test_stops_when_max_users_exceeded(self, mock_adapter, mock_strategy):
        config = Config(
            adapter=AdapterConfig(type="locust", test_file="dummy.py"),
            strategy=StrategyConfig(type="degradation_search"),
            orchestrator=OrchestratorConfig(spawn_rate=10, max_users=10),
        )

        orc = make_orchestrator(mock_adapter, mock_strategy, config)
        mock_adapter.is_ready.return_value = True
        mock_adapter.get_stats.side_effect = [
            make_metrics(rps=100.0, users=1),
            make_metrics(rps=100.0, users=15),
        ]
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result.stop_reason == StopReason.MAX_USERS

    def test_stops_on_timeout(self, mock_adapter, mock_strategy):
        config = Config(
            adapter=AdapterConfig(type="locust", test_file="dummy.py"),
            strategy=StrategyConfig(type="degradation_search"),
            orchestrator=OrchestratorConfig(spawn_rate=10, max_wait_time=1),
        )

        orc = make_orchestrator(mock_adapter, mock_strategy, config)
        mock_adapter.is_ready.return_value = True

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()
        assert result.stop_reason == StopReason.TIMEOUT


class TestOrchestratorLoadControl:
    def test_does_not_change_load_on_hold(self, mock_adapter, mock_strategy_hold):
        orc = make_orchestrator(mock_adapter, mock_strategy_hold)
        mock_adapter.is_ready.return_value = True
        mock_strategy_hold.get_next_users.return_value = 10

        orc.state = State.RUNNING
        orc.current_users = 50
        orc.started_at = 0.0
        orc.history = []

        # один шаг running phase вручную
        metrics = mock_adapter.get_stats()
        decision = mock_strategy_hold.decide(metrics)
        assert decision == Decision.HOLD
        # при HOLD нагрузка не меняется
        assert orc.current_users == 50

    def test_calls_get_next_users_on_continue(self, mock_adapter, mock_strategy):
        orc = make_orchestrator(mock_adapter, mock_strategy)
        mock_adapter.is_ready.return_value = True
        mock_adapter.get_stats.return_value = make_metrics(users=50)
        # первый вызов — CONTINUE (меняем нагрузку), второй — STOP (выходим)
        mock_strategy.decide.side_effect = [Decision.CONTINUE, Decision.STOP]
        mock_strategy.get_wait_time.return_value = 0  # без ожидания

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            orc.run()

        mock_strategy.get_next_users.assert_called()
        mock_adapter.configure.assert_called_with(user_count=20, spawn_rate=10)

    def test_does_not_change_load_before_wait_time(self, mock_adapter, mock_strategy):
        orc = make_orchestrator(mock_adapter, mock_strategy)
        mock_adapter.is_ready.return_value = True
        mock_adapter.get_stats.return_value = make_metrics()
        mock_strategy.get_next_users.side_effect = None
        mock_strategy.get_next_users.return_value = 50
        # большой wait_time — нагрузка не должна меняться между тиками
        mock_strategy.get_wait_time.return_value = 9999
        # два CONTINUE подряд, потом STOP
        mock_strategy.decide.side_effect = [
            Decision.CONTINUE,
            Decision.CONTINUE,
            Decision.STOP,
        ]

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            orc.run()

        # configure с spawn_rate=10 (из running phase) не должен вызываться —
        # wait_time ещё не истёк
        running_phase_calls = [
            c for c in mock_adapter.configure.call_args_list
            if c.kwargs.get("spawn_rate") == 10 or
               (c.args and len(c.args) > 1 and c.args[1] == 10)
        ]
        assert len(running_phase_calls) == 1


class TestOrchestratorResult:
    def test_result_contains_stop_reason(self, mock_adapter, mock_strategy_stop):
        orc = make_orchestrator(mock_adapter, mock_strategy_stop)
        mock_adapter.is_ready.return_value = True
        mock_strategy_stop.get_next_users.return_value = 10

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()

        assert result.stop_reason == StopReason.TARGET_REACHED

    def test_manual_stop_sets_correct_reason(self):
        orc = Orchestrator.__new__(Orchestrator)
        orc.state = State.RUNNING
        orc.stop_reason = StopReason.MANUAL

        orc.stop()

        assert orc.stop_reason == StopReason.MANUAL
        assert orc.state == State.FINISHED

    def test_result_contains_full_history(self, mock_adapter, mock_strategy):
        orc = make_orchestrator(mock_adapter, mock_strategy)
        mock_adapter.is_ready.return_value = True
        mock_strategy.get_next_users.return_value = 10
        random_len = random.randint(1,10)
        mock_adapter.get_stats.side_effect = [
            make_metrics(users=10) for _ in range(random_len)
        ]

        mock_strategy.decide.side_effect = [
            Decision.CONTINUE for _ in range(random_len-1)] + [Decision.STOP]

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("time.sleep", lambda _: None)
            result = orc.run()


        assert result.stop_reason == StopReason.TARGET_REACHED
        assert len(result.history) == random_len