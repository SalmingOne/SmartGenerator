from collections import deque

from .base import IStrategy
from ..analytics.metrics_calculator import MetricsCalculator, ReferenceMetrics
from ..models import RawMetrics, Decision


class DegradationSearch(IStrategy):
    """
    Стратегия поиска точки деградации системы на основе Locust-SDI

    Использует академический индекс деградации системы (Locust-SDI),
    который учитывает:
    - Амплитудную деградацию (отклонение от нормы)
    - Трендовую деградацию (наклон кривых)
    - Нестабильность (спайки на графиках)

    Интерпретация Locust-SDI:
    - 0.0-0.3: стабильная работа
    - 0.3-0.5: начало деградации
    - 0.5-0.7: серьёзная деградация
    - >0.7: критическое состояние
    """

    def __init__(
        self,
        initial_users: int = 10,
        step_multiplier: float = 1.5,
        degradation_threshold: float = 0.7,  # Порог Locust-SDI для остановки
        window_size: int = 5,  # Размер скользящего окна
        threshold_count: int = 3,  # Сколько проверок из window_size должны превысить порог
        ref_metrics: ReferenceMetrics | None = None
    ):
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.degradation_threshold = degradation_threshold
        self.window_size = window_size
        self.threshold_count = threshold_count

        # Эталонные метрики (можно задать из конфига или определить автоматически)
        self.ref_metrics = ref_metrics or ReferenceMetrics()

        # История для расчета Locust-SDI
        self.metrics_history: list[RawMetrics] = []
        self.previous_metrics: RawMetrics | None = None
        self.last_sdi: float | None = None

        # Скользящее окно для проверки деградации
        self.violation_window: deque[bool] = deque(maxlen=window_size)

    def decide(self, metrics: RawMetrics) -> Decision:
        """
        Принять решение на основе Locust-SDI

        Вызывается при каждом мониторинге для обновления состояния
        и проверки условий остановки.
        """
        # Добавить текущие метрики в историю
        self.metrics_history.append(metrics)

        # Рассчитать Locust-SDI
        sdi = MetricsCalculator.calculate_locust_sdi(
            curr=metrics,
            prev=self.previous_metrics,
            history=self.metrics_history,
            ref=self.ref_metrics
        )
        self.last_sdi = sdi
        self.previous_metrics = metrics

        # Добавить результат проверки в скользящее окно
        is_violation = sdi >= self.degradation_threshold
        self.violation_window.append(is_violation)

        # Подсчитать сколько нарушений в окне
        violations_count = sum(self.violation_window)

        # Логирование с эмодзи в зависимости от уровня
        if sdi >= 0.7:
            print(f"🔴 Locust-SDI: {sdi:.3f} (порог: {self.degradation_threshold}) [{violations_count}/{len(self.violation_window)}]")
        elif sdi >= 0.5:
            print(f"🟠 Locust-SDI: {sdi:.3f} (порог: {self.degradation_threshold}) [{violations_count}/{len(self.violation_window)}]")
        elif sdi >= 0.3:
            print(f"🟡 Locust-SDI: {sdi:.3f} (порог: {self.degradation_threshold}) [{violations_count}/{len(self.violation_window)}]")
        else:
            print(f"📊 Locust-SDI: {sdi:.3f} (порог: {self.degradation_threshold}) [{violations_count}/{len(self.violation_window)}]")

        # Остановка если достаточно подтверждений деградации
        if violations_count >= self.threshold_count:
            print(f"🛑 Деградация подтверждена: {violations_count} из {len(self.violation_window)} проверок превысили порог")
            return Decision.STOP

        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        Логика:
        - Если current_users == 0, вернуть initial_users
        - Иначе увеличить на step_multiplier (например, * 1.5)
        """
        if current_users == 0:
            return self.initial_users
        return int(current_users * self.step_multiplier)

    def reset(self) -> None:
        """Сбросить внутреннее состояние стратегии"""
        self.metrics_history.clear()
        self.previous_metrics = None
        self.last_sdi = None
        self.violation_window.clear()
