import time
from .base import IStrategy
from ..models import RawMetrics, Decision


class TargetRPS(IStrategy):
    """
    Стратегия константной нагрузки с целевым RPS

    Устанавливает нужное количество пользователей для достижения target_rps
    и держит эту нагрузку в течение заданного времени.

    Останавливается когда истекло test_duration секунд.
    """

    def __init__(
        self,
        target_rps: float,
        test_duration: int = 300,  # Сколько секунд держать нагрузку
        tolerance: float = 0.05,  # 5% погрешность для достижения target_rps
    ):
        """
        Args:
            target_rps: Целевой RPS который нужно достичь и держать
            test_duration: Длительность теста в секундах
            initial_users: Начальное количество пользователей
            tolerance: Допустимое отклонение от target_rps (в долях)
        """
        self.target_rps = target_rps
        self.test_duration = test_duration
        self.tolerance = tolerance

        self._start_time: float | None = None
        self._target_reached = False

    def decide(self, metrics: RawMetrics) -> Decision:
        """
        Принять решение: продолжать тест или остановиться

        Логика:
        1. Проверяем достигли ли целевого RPS
        2. Если достигли - запускаем таймер (если еще не запущен)
        3. Если прошло test_duration секунд - STOP
        4. Если еще не достигли RPS - CONTINUE (продолжаем подстройку)
        5. Если достигли RPS но время не вышло - HOLD (держим нагрузку)
        """
        current_rps = metrics.rps
        target_min = self.target_rps * (1 - self.tolerance)
        target_max = self.target_rps * (1 + self.tolerance)

        # Проверяем достигли ли целевого RPS
        in_target_range = target_min <= current_rps <= target_max

        if in_target_range:
            # Целевой RPS достигнут
            if not self._target_reached:
                # Первый раз достигли цели - запускаем таймер
                self._start_time = time.time()
                self._target_reached = True
                print(f"✅ Целевой RPS достигнут: {current_rps:.1f} (цель: {self.target_rps:.1f})")
                print(f"⏱️  Держим нагрузку {self.test_duration} секунд...")

            # Проверяем не истекло ли время
            elapsed = time.time() - self._start_time
            if elapsed >= self.test_duration:
                print(f"🏁 Тест завершен: {elapsed:.0f} секунд")
                return Decision.STOP

            # Держим текущую нагрузку
            return Decision.HOLD

        else:
            # Еще не достигли целевого RPS
            if current_rps < target_min:
                print(f"📈 Текущий RPS: {current_rps:.1f} < {self.target_rps:.1f} (цель)")
            else:
                print(f"📉 Текущий RPS: {current_rps:.1f} > {self.target_rps:.1f} (цель)")

            # Сбрасываем флаг если вышли из диапазона
            if self._target_reached:
                self._target_reached = False
                self._start_time = None
                print("⚠️  Вышли из целевого диапазона, продолжаем подстройку")

            return Decision.CONTINUE

    def get_next_users(self, current_users: int, metrics: RawMetrics) -> int:
        """
        Вычислить количество пользователей для достижения target_rps

        Использует плавную корректировку с учетом расстояния до цели:
        1. Вычисляет users_per_rps = current_users / current_rps
        2. Оценивает идеальное количество: ideal_users = target_rps * users_per_rps
        3. Применяет damping factor для плавного приближения
        4. Чем ближе к цели, тем меньше шаг корректировки
        """

        current_rps = metrics.rps

        # Если RPS слишком маленький или 0, удваиваем пользователей
        if current_rps < 1.0:
            next_users = max(current_users * 2, 1)
            print(f"🔄 RPS слишком низкий ({current_rps:.2f}), увеличиваем users: {current_users} → {next_users}")
            return int(next_users)

        # Вычисляем коэффициент users/rps
        users_per_rps = current_users / current_rps

        # Оцениваем идеальное количество пользователей
        ideal_users = self.target_rps * users_per_rps

        # Вычисляем отклонение от цели (в процентах)
        rps_error = abs(current_rps - self.target_rps) / self.target_rps

        # Выбираем коэффициент сглаживания в зависимости от близости к цели
        if rps_error < 0.1:  # Очень близко к цели (< 10% отклонение)
            damping = 0.3  # Очень плавная корректировка
        elif rps_error < 0.25:  # Близко к цели (< 25%)
            damping = 0.5  # Средняя корректировка
        else:  # Далеко от цели
            damping = 0.7  # Более агрессивная корректировка

        # Плавное приближение к идеальному значению
        correction = (ideal_users - current_users) * damping
        next_users_float = current_users + correction

        next_users = max(1, int(next_users_float))

        # Логирование
        direction = "↑" if next_users > current_users else "↓" if next_users < current_users else "="
        print(f"🎯 {current_users} {direction} {next_users} users "
              f"(RPS: {current_rps:.1f}/{self.target_rps:.1f}, "
              f"error: {rps_error*100:.1f}%, damping: {damping:.1f})")

        return next_users

    def get_wait_time(self) -> int:

        return 5

    def reset(self) -> None:
        """Сбросить внутреннее состояние"""
        self._start_time = None
        self._target_reached = False