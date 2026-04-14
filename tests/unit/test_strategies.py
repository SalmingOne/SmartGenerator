from load_orchestrator.models import Decision, SpikeConfig, SpikePhase
from load_orchestrator.strategies.degradation_search import DegradationSearch
from load_orchestrator.strategies.break_point import BreakPoint
from load_orchestrator.strategies.sla_validation import SLAValidation
from load_orchestrator.strategies.spike import Spike
from load_orchestrator.strategies.canary import Canary
from conftest import make_metrics


# ── DegradationSearch ─────────────────────────────────────────────────────────

class TestDegradationSearch:
    def test_continue_when_not_enough_history(self):
        strategy = DegradationSearch()
        # меньше 5 точек — ещё не хватает данных
        for _ in range(4):
            decision = strategy.decide(make_metrics(p95=200.0))
        assert decision == Decision.CONTINUE

    def test_stop_when_p95_spikes_above_baseline(self):
        strategy = DegradationSearch()
        # накапливаем стабильный baseline
        for _ in range(15):
            strategy.decide(make_metrics(p95=200.0))
        # резкий скачок p95
        for _ in range(3):
            decision = strategy.decide(make_metrics(p95=1000.0))
        assert decision == Decision.STOP

    def test_stop_when_error_rate_spikes(self):
        strategy = DegradationSearch()
        # накапливаем стабильный baseline
        for _ in range(15):
            strategy.decide(make_metrics(error_rate=1.0))
        # резкий скачок p95
        for _ in range(3):
            decision = strategy.decide(make_metrics(error_rate=10.0))
        assert decision == Decision.STOP

    def test_get_next_users_returns_initial_when_zero(self):
        strategy = DegradationSearch(initial_users=20)
        assert strategy.get_next_users(0, make_metrics()) == 20

    def test_get_next_users_linear_growth(self):
        strategy = DegradationSearch(step_size=10)
        assert strategy.get_next_users(50, make_metrics()) == 60

    def test_get_next_users_exponential_growth(self):
        strategy = DegradationSearch(step_multiplier=10)
        assert strategy.get_next_users(50, make_metrics()) == 501

    def test_reset_clears_history(self):
        strategy = DegradationSearch()
        for _ in range(10):
            strategy.decide(make_metrics())
        strategy.reset()
        assert strategy.metrics_history == []


# ── BreakPoint ────────────────────────────────────────────────────────────────

class TestBreakPoint:
    def test_stop_when_error_rate_exceeds_threshold(self):
        strategy = BreakPoint(error_threshold=10.0)
        decision = strategy.decide(make_metrics(error_rate=15.0))
        assert decision == Decision.STOP

    def test_stop_when_rps_drops_to_zero(self):
        strategy = BreakPoint()
        decision = strategy.decide(make_metrics(rps=0.0, users=50))
        assert decision == Decision.STOP

    def test_stop_when_p99_exceeds_10_seconds(self):
        strategy = BreakPoint()
        decision = strategy.decide(make_metrics(p99=10000.1))
        assert decision == Decision.STOP

    def test_stop_when_rps_drops_50_percent(self):
        strategy = BreakPoint()
        strategy.decide(make_metrics(rps=100.0, users=50))
        decision = strategy.decide(make_metrics(rps=49.0, users=50))
        assert decision == Decision.STOP

    def test_get_next_users_returns_initial_when_zero(self):
        strategy = BreakPoint(initial_users=10)
        assert strategy.get_next_users(0, make_metrics()) == 10

    def test_reset_restores_empty_previous_metrics(self):
        strategy = BreakPoint()
        strategy.decide(make_metrics(rps=100.0))
        strategy.reset()
        assert strategy.previous_metrics.rps == 0


# ── SLAValidation ─────────────────────────────────────────────────────────────

class TestSLAValidation:
    def test_continue_during_stabilization_phase(self):
        strategy = SLAValidation(max_error_rate=1.0, stabilization_time=30)
        # первый вызов — начало фазы стабилизации
        decision = strategy.decide(make_metrics())
        assert decision == Decision.CONTINUE

    def test_stop_when_avg_p99_exceeds_threshold(self):
        pass

    def test_stop_when_avg_error_rate_exceeds_threshold(self):
        pass

    def test_continue_and_reset_when_sla_met(self):
        pass

    def test_get_next_users_does_not_exceed_max_users(self):
        strategy = SLAValidation(max_error_rate=1.0, max_users=100)
        result = strategy.get_next_users(90, make_metrics())
        assert result <= 100


# ── Spike ─────────────────────────────────────────────────────────────────────

class TestSpike:
    def _make_spike(self):
        config = SpikeConfig(
            baseline_users=10, baseline_duration=5,
            spike_users=100, spike_duration=10,
            recovery_users=10, recovery_duration=5,
        )
        return Spike(config=config)

    def test_returns_baseline_users_in_baseline_phase(self):
        strategy = self._make_spike()
        assert strategy.get_next_users(0, make_metrics()) == 10

    def test_transitions_to_spike_after_baseline_duration(self):
        strategy = self._make_spike()
        # первый вызов инициализирует время фазы
        strategy.decide(make_metrics(timestamp=1.0))
        # через 6 секунд — baseline_duration=5 истёк
        decision = strategy.decide(make_metrics(timestamp=7.0))
        assert decision == Decision.CONTINUE
        assert strategy._phase == SpikePhase.SPIKE

    def test_returns_spike_users_in_spike_phase(self):
        strategy = self._make_spike()
        # первый вызов инициализирует время фазы
        strategy.decide(make_metrics(timestamp=1.0))
        # через 6 секунд — baseline_duration=5 истёк
        strategy.decide(make_metrics(timestamp=7.0))

        users = strategy.get_next_users(0, make_metrics())
        assert users == 100

    def test_transitions_to_recovery_after_spike_duration(self):
        strategy = self._make_spike()
        # первый вызов инициализирует время фазы
        strategy.decide(make_metrics(timestamp=1.0))
        # через 6 секунд — baseline_duration=5 истёк
        strategy.decide(make_metrics(timestamp=7.0))
        decision = strategy.decide(make_metrics(timestamp=18.0))
        assert decision == Decision.CONTINUE
        assert strategy._phase == SpikePhase.RECOVERY


    def test_stop_after_recovery_duration(self):
        strategy = self._make_spike()
        # первый вызов инициализирует время фазы
        strategy.decide(make_metrics(timestamp=1.0))
        # через 6 секунд — baseline_duration=5 истёк
        strategy.decide(make_metrics(timestamp=7.0))
        strategy.decide(make_metrics(timestamp=18.0))
        decision = strategy.decide(make_metrics(timestamp=26.0))

        assert decision == Decision.STOP
        assert strategy._phase == SpikePhase.FINISHED

    def test_reset_restores_baseline_phase(self):
        strategy = self._make_spike()
        strategy.decide(make_metrics(timestamp=1.0))
        strategy.decide(make_metrics(timestamp=7.0))  # переходим в SPIKE
        strategy.reset()
        assert strategy._phase == SpikePhase.BASELINE


# ── Canary ────────────────────────────────────────────────────────────────────

class TestCanary:
    def test_hold_while_healthy_within_duration(self):
        strategy = Canary(canary_users=5, canary_duration=30, error_threshold=1.0)
        strategy.decide(make_metrics())  # первый вызов — инициализация
        decision = strategy.decide(make_metrics(error_rate=0.0, p99=100.0))
        assert decision == Decision.HOLD

    def test_stop_when_error_rate_exceeds_threshold(self):
        strategy = Canary(error_threshold=1.0)
        strategy.decide(make_metrics())  # инициализация
        decision = strategy.decide(make_metrics(error_rate=5.0))
        assert decision == Decision.STOP

    def test_stop_when_p99_exceeds_threshold(self):
        pass

    def test_stop_after_canary_duration(self):
        pass

    def test_always_returns_canary_users(self):
        strategy = Canary(canary_users=5)
        assert strategy.get_next_users(0, make_metrics()) == 5
        assert strategy.get_next_users(100, make_metrics()) == 5