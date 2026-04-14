import time

from .base import IStrategy
from ..models import RawMetrics, Decision


class SLAValidation(IStrategy):
    def __init__(
        self,
        max_error_rate: float,
        max_p99: float = None,
        max_p95: float = None,
        initial_users: int = 10,
        step_multiplier: float = 1.5,
        max_users: int = 1000,
        stabilization_time: int = 30,  # ждём после изменения нагрузки
    ):
        self.max_p99 = max_p99
        self.max_p95 = max_p95
        self.max_error_rate = max_error_rate
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.max_users = max_users
        self.stabilization_time = stabilization_time

        # внутреннее состояние
        self._phase_started_at: float | None = None
        self._observation_metrics: list[RawMetrics] = []
        self._in_stabilization: bool = True

    def decide(self, metrics: RawMetrics) -> Decision:
        now = time.time()

        # Первый вызов после смены нагрузки — начинаем фазу
        if self._phase_started_at is None:
            self._phase_started_at = now
            self._in_stabilization = True
            return Decision.CONTINUE

        elapsed = now - self._phase_started_at

        # Фаза стабилизации — просто ждём, ничего не проверяем
        if elapsed < self.stabilization_time:
            return Decision.CONTINUE

        # Переход в фазу наблюдения
        if self._in_stabilization:
            self._in_stabilization = False
            self._observation_metrics = []

        # Накапливаем метрики в observation window
        self._observation_metrics.append(metrics)

        # Наблюдение ещё не закончилось — просто копим (5 сек после стабилизации)
        OBSERVATION_WINDOW = 5
        if elapsed < self.stabilization_time + OBSERVATION_WINDOW:
            return Decision.CONTINUE

        return self._check_sla()

    def _check_sla(self) -> Decision:
        if not self._observation_metrics:
            return Decision.CONTINUE

        avg_p99 = sum(m.p99 for m in self._observation_metrics) / len(self._observation_metrics)
        avg_p95 = sum(m.p95 for m in self._observation_metrics) / len(self._observation_metrics)
        avg_error_rate = sum(m.error_rate for m in self._observation_metrics) / len(self._observation_metrics)

        if self.max_p95 is not None and avg_p95 > self.max_p95:
            print(f"⚠️  SLA violation: avg P95={avg_p99:.0f}ms > {self.max_p95}ms")
            return Decision.STOP

        if self.max_p99 is not None and avg_p99 > self.max_p99:
            print(f"⚠️  SLA violation: avg P99={avg_p99:.0f}ms > {self.max_p99}ms")
            return Decision.STOP

        if avg_error_rate > self.max_error_rate:
            print(f"⚠️  SLA violation: avg error_rate={avg_error_rate:.2f}% > {self.max_error_rate}%")
            return Decision.STOP
        parts = []
        if self.max_p95:
            parts.append(f'P95={avg_p95:.0f}ms')
        if self.max_p99:
            parts.append(f'P95={avg_p99:.0f}ms')
        parts.append(f'errors={avg_error_rate:.2f}%')

        print(f"✅ SLA OK: {', '.join(parts)}")
        # Сбрасываем фазу — оркестратор вызовет get_next_users() и снова изменит нагрузку
        self._phase_started_at = None
        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        if current_users == 0:
            return self.initial_users

        next_users = int(current_users * self.step_multiplier)
        return min(next_users, self.max_users)

    def get_wait_time(self) -> int:
        return self.stabilization_time + 5

    def reset(self) -> None:
        self._phase_started_at = None
        self._observation_metrics = []
        self._in_stabilization = True