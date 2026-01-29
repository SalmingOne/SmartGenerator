from collections import deque

from .base import IStrategy
from ..analytics.metrics_calculator import MetricsCalculator
from ..models import RawMetrics, Decision

import statistics


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
        step_multiplier: float | None = 1.5,  # Экспоненциальный рост (множитель)
        step_size: int | None = None,  # Линейный рост (фиксированный шаг)
        window_size: int = 5,  # Размер скользящего окна
        threshold_count: int = 3,  # Сколько проверок из window_size должны превысить порог
    ):
        """
        Args:
            initial_users: Начальное количество пользователей
            step_multiplier: Множитель для экспоненциального роста (например, 1.5 = +50%)
            step_size: Фиксированный шаг для линейного роста (например, +50 users)
            degradation_threshold: Порог Locust-SDI для остановки
            window_size: Размер скользящего окна для проверки
            threshold_count: Сколько проверок должны превысить порог
            ref_metrics: Эталонные метрики для расчета Locust-SDI

        Note:
            Если задан step_size, используется линейный рост (StepLoad режим).
            Если step_size=None, используется step_multiplier (экспоненциальный рост).
        """
        self.initial_users = initial_users
        self.step_multiplier = step_multiplier
        self.step_size = step_size
        self.degradation_threshold = 0.6
        self.window_size = window_size
        self.threshold_count = threshold_count

        self.previous_growth = 0


        # История для расчета Locust-SDI
        self.metrics_history: list[RawMetrics] = []
        self.previous_metrics: RawMetrics | None = None
        self.last_sdi: float | None = None

        # Скользящее окно для проверки деградации
        self.violation_window: deque[bool] = deque(maxlen=window_size)


    # previous_growth = 0
    #
    #     for i in range(1, len(p95_history)):
    #         current_val = p95_history[i]
    #         prev_val = p95_history[i-1]
    #
    #         # Текущий прирост времени отклика
    #         current_growth = current_val - prev_val
    #
    #         # Логика детекции перегиба (Inflection Point):
    #         # Вариант А: Резкое превышение базового уровня в N раз [5]
    #         if current_val > baseline * 2: # "Разумный порог" по Алексею Рагозину
    #              return f"Точка деградации найдена: p95 ({current_val}мс) превысил baseline в 2 раза"
    #
    #         # Вариант Б: Математический - резкое ускорение роста (производная)
    #         # Если текущий скачок в 3 раза (sensitivity) больше предыдущего [6]
    #         if i > 2 and current_growth > previous_growth * sensitivity:
    #             return f"Точка деградации найдена: резкое ускорение роста на шаге {i}"
    #
    #         previous_growth = current_growth
    #
    #     return "Точка деградации не обнаружена: система остается в зеленой зоне"
    import statistics

    def decide(self, metrics: RawMetrics) -> Decision:
        self.metrics_history.append(metrics)

        # Минимум данных
        if len(self.metrics_history) < 15:
            return Decision.CONTINUE

        # Берём только p95
        p95 = [m.p95 for m in self.metrics_history]
        errors = [m.error_rate for m in self.metrics_history]

        BASELINE_WINDOW = 10
        CHECK_WINDOW = 3
        MULTIPLIER = 1.5

        # baseline — медиана стабильного участка
        baseline_slice_p95 = p95[-(BASELINE_WINDOW + CHECK_WINDOW):-CHECK_WINDOW]
        baseline_slice_error_rate = errors[-(BASELINE_WINDOW + CHECK_WINDOW):-CHECK_WINDOW]
        baseline_p95 = statistics.median(baseline_slice_p95)
        baseline_error_rate = statistics.median(baseline_slice_error_rate)

        # последние значения
        recent_p95 = p95[-CHECK_WINDOW:]
        recent_error_rate = errors[-CHECK_WINDOW:]

        # условие деградации:
        # все последние значения сильно выше baseline
        print(recent_p95, baseline_p95)
        print(recent_error_rate, baseline_error_rate)
        if all(v > baseline_p95 * MULTIPLIER for v in recent_p95) or all(v > baseline_error_rate * MULTIPLIER for v in recent_error_rate) :
            return Decision.STOP

        return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        Вычислить следующее количество пользователей

        Поддерживает два режима:
        1. Линейный рост (step_size): users + step_size
        2. Экспоненциальный рост (step_multiplier): users * step_multiplier
        """
        return current_users + 10

    def get_wait_time(self) -> int:
        return 5

    def reset(self) -> None:
        """Сбросить внутреннее состояние стратегии"""
        self.metrics_history.clear()
        self.previous_metrics = None
        self.last_sdi = None
        self.violation_window.clear()
