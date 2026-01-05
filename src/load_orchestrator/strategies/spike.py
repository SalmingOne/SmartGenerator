from .base import IStrategy
from ..models import AnalyzedMetrics, Decision


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
        spike_users: int,
        spike_duration: int = 60,  # секунд
        baseline_users: int = 10,
        check_recovery: bool = True,
    ):
        """
        Args:
            spike_users: Количество пользователей для скачка
            spike_duration: Длительность скачка (секунд)
            baseline_users: Базовая нагрузка (для проверки восстановления)
            check_recovery: Проверять ли восстановление после скачка
        """
        self.spike_users = spike_users
        self.spike_duration = spike_duration
        self.baseline_users = baseline_users
        self.check_recovery = check_recovery

        self._phase = "baseline"  # baseline -> spike -> recovery
        self._spike_steps = 0

    def decide(self, metrics: AnalyzedMetrics) -> Decision:
        """
        TODO: Реализовать логику принятия решения

        Фазы:
        1. baseline: Установить базовую нагрузку -> переход в spike
        2. spike: Держать spike_users в течение spike_duration -> переход в recovery
        3. recovery: Вернуться к baseline, проверить восстановление -> STOP

        Останавливаться если:
        - Система отказала во время spike (error_rate > 50%)
        - Прошли все фазы
        """
        return Decision.INCREASE

    def get_next_users(self, current_users: int, metrics: AnalyzedMetrics) -> int:
        """
        TODO: Вычислить следующее количество пользователей

        В зависимости от фазы:
        - baseline: baseline_users
        - spike: spike_users
        - recovery: baseline_users
        """
        if self._phase == "baseline":
            return self.baseline_users
        elif self._phase == "spike":
            return self.spike_users
        else:  # recovery
            return self.baseline_users

    def reset(self) -> None:
        """TODO: Сбросить внутреннее состояние"""
        self._phase = "baseline"
        self._spike_steps = 0