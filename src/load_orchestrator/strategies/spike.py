from .base import IStrategy
from ..models import RawMetrics, Decision, SpikePhase, SpikeConfig


class Spike(IStrategy):
    """
    Стратегия резкого скачка нагрузки (Spike Test)

    TODO: Реализовать логику:
    - Резко увеличить нагрузку до spike_users
    - Держать нагрузку spike_duration секунд
    - Проверить:
      * Выдержала ли система скачок
      * Как быстро восстановилась
    - Опционально: вернуться к baseline и проверить восстановление
    """

    def __init__(
        self,
        config: SpikeConfig,
    ):
        self.config = config
        self._phase: SpikePhase = SpikePhase.BASELINE # baseline -> spike -> recovery
        self.phase_start_time = None

        self.baseline_metrics: RawMetrics | None = None
        self.spike_metrics: list[RawMetrics] = []
        self.recovery_metrics: list[RawMetrics] = []

    def decide(self, metrics: RawMetrics, ) -> Decision:

        now = metrics.timestamp

        # Инициализация времени фазы
        if self.phase_start_time is None:
            self.phase_start_time = now

        elapsed = now - self.phase_start_time

        match self._phase:
            case SpikePhase.SPIKE:
                return self._handle_spike(metrics, elapsed)
            case SpikePhase.BASELINE:
                return self._handle_baseline(metrics, elapsed)
            case SpikePhase.RECOVERY:
                return self._handle_recovery(metrics, elapsed)


        return Decision.CONTINUE

    def _handle_spike(self, metrics: RawMetrics, elapsed: float) -> Decision:
        """Фаза spike — держим пиковую нагрузку"""

        self.spike_metrics.append(metrics)

        # Проверяем не сломалась ли система полностью
        if metrics.error_rate > 50:  # 50% ошибок — система мертва
            self._phase = SpikePhase.RECOVERY
            self.phase_start_time = metrics.timestamp  # Сброс времени для новой фазы
            return Decision.CONTINUE  # На самом деле уменьшим (см. get_next_users)

        if metrics.rps == 0:
            return Decision.STOP

        if elapsed >= self.config.spike_duration:
            self._phase = SpikePhase.RECOVERY
            self.phase_start_time = metrics.timestamp  # Сброс времени для новой фазы
            print("Сброс активности")
            return Decision.CONTINUE  # Сигнал на изменение (уменьшение)

        return Decision.HOLD

    def _handle_recovery(self, metrics: RawMetrics, elapsed: float) -> Decision:
        """Фаза recovery — проверяем восстановление"""

        self.recovery_metrics.append(metrics)

        if elapsed >= self.config.recovery_duration:
            self._phase = SpikePhase.FINISHED
            print("Тест закончен")
            return Decision.STOP

        return Decision.HOLD

    def _handle_baseline(self, metrics: RawMetrics, elapsed: float) -> Decision:
        """Фаза baseline — держим начальную нагрузку"""

        if elapsed >= self.config.baseline_duration:
            # Запоминаем baseline для сравнения
            self.baseline_metrics = metrics

            # Переходим к спайку
            self._phase = SpikePhase.SPIKE
            self.phase_start_time = metrics.timestamp  # Сброс времени для новой фазы
            print("Резкий скачок")
            return Decision.CONTINUE  # Сигнал на резкое увеличение

        return Decision.HOLD


    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        if self._phase == SpikePhase.BASELINE:
            return self.config.baseline_users
        elif self._phase == SpikePhase.SPIKE:
            return self.config.spike_users
        else:  # recovery
            return self.config.recovery_users

    def get_wait_time(self) -> int:
        """
        Spike проверяет метрики часто для отслеживания фаз

        Returns:
            1 секунда (фазы контролируются через timestamp в decide)
        """
        return 1

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        self._phase = SpikePhase.SPIKE
        self._spike_steps = 0