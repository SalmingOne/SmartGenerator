import time
from datetime import datetime

from .models import State, StopReason, TestResult, RawMetrics, Decision
from .config import Config
from .interfaces.IAdapter import IAdapter
from .strategies.base import IStrategy


class Orchestrator:
    """
    Главный оркестратор нагрузочного тестирования

    Управляет циклом:
    1. INIT - запуск генератора и подготовка
    2. RUNNING - цикл сбора метрик и принятия решений
    3. FINISHED - остановка и формирование результата
    """

    def __init__(self, config: Config, adapter: IAdapter, strategy: IStrategy):
        self.config = config
        self.adapter = adapter
        self.strategy = strategy

        self.state = State.INIT
        self.current_users: int = 0
        self.started_at: float | None = None
        self.finished_at: float | None = None
        self.history: list[RawMetrics] = []
        self.stop_reason: StopReason = StopReason.MANUAL

    def run(self) -> TestResult:
        """
        Запустить тест

        Проходит через 3 фазы:
        1. INIT - запуск генератора и конфигурация начальной нагрузки
        2. RUNNING - главный цикл сбора метрик и принятия решений
        3. FINISHED - остановка генератора и формирование результата
        """
        try:
            self._init_phase()
            self._running_phase()
        except Exception as e:
            self.stop_reason = StopReason.ERROR
            raise
        finally:
            return self._finished_phase()

    def _init_phase(self) -> None:
        """Фаза инициализации: запуск генератора и настройка начальной нагрузки"""
        self.started_at = datetime.now().timestamp()
        self.state = State.INIT

        # Запустить генератор нагрузки
        self.adapter.launch()
        self._wait_until_ready()

        # Получить начальное количество пользователей из стратегии
        self._configure_initial_load()

        time.sleep(10) # стабилизация

        self.state = State.RUNNING

    def _wait_until_ready(self) -> None:
        """Ожидание готовности генератора нагрузки"""
        while not self.adapter.is_ready():
            time.sleep(1)

    def _configure_initial_load(self) -> None:
        """
        Конфигурация начальной нагрузки

        Получает initial_users из стратегии через get_next_users(0, dummy_metrics)
        """
        # Создать dummy metrics для получения initial_users
        dummy_metrics = RawMetrics(
            timestamp=datetime.now().timestamp(),
            users=0,
            rps=0.0,
            rt_avg=0.0,
            p50=0.0,
            p95=0.0,
            p99=0.0,
            failed_requests=0,
            error_rate=0.0,
            total_requests=0
        )

        # Получить начальное количество пользователей из стратегии
        self.current_users = self.strategy.get_next_users(0, dummy_metrics)

        # Настроить генератор
        self.adapter.configure(
            user_count=self.current_users,
            spawn_rate=self.current_users
        )



    def _running_phase(self) -> None:
        """
        Главный цикл: сбор метрик и принятие решений

        Два независимых таймера:
        1. next_monitor_time - сбор метрик и принятие решений стратегией
        2. next_change_time - изменение нагрузки
        """
        next_monitor_time = time.time()
        next_change_time = time.time()  # Время следующего изменения нагрузки

        while self.state == State.RUNNING:
            time.sleep(1)  # Проверяем каждую секунду
            now = time.time()

            # Собираем метрики и принимаем решения по расписанию
            if now >= next_monitor_time:
                metrics = self.adapter.get_stats()
                self.history.append(metrics)

                # Проверяем критические условия оркестратора
                if self._check_critical_conditions(metrics):
                    self.state = State.FINISHED
                    self.stop_reason = StopReason.DEGRADATION
                    break

                # Стратегия принимает решение ПРИ КАЖДОМ мониторинге
                decision = self.strategy.decide(metrics)

                if decision == Decision.STOP:
                    self.state = State.FINISHED
                    self.stop_reason = StopReason.TARGET_REACHED
                    break

                # Изменять нагрузку только если пришло время и решение CONTINUE
                if decision == Decision.CONTINUE and now >= next_change_time:
                    next_users = self.strategy.get_next_users(self.current_users, metrics)
                    self.adapter.configure(
                        user_count=next_users,
                        spawn_rate=self.config.orchestrator.spawn_rate
                    )
                    self.current_users = next_users
                    next_change_time = now + self.strategy.get_wait_time()

                # HOLD - просто не меняем нагрузку

                next_monitor_time = now + self.config.orchestrator.monitoring_interval

    def _check_critical_conditions(self, metrics: RawMetrics) -> bool:
        """
        Проверить критические условия, требующие немедленной остановки

        Проверяет:
        - Катастрофический error rate (>50%)
        - Полная неработоспособность (RPS = 0)
        - Превышение max_users из конфига

        Returns:
            True если обнаружено критическое состояние, False иначе
        """
        # Катастрофический error rate
        if metrics.error_rate >= 50.0:
            return True

        # RPS упал до нуля при наличии пользователей
        if metrics.users > 0 and metrics.rps == 0.0:
            return True

        # Превышен лимит пользователей из конфига
        if self.config.orchestrator.max_users is not None:
            if metrics.users >= self.config.orchestrator.max_users:
                return True

        return False

    def _finished_phase(self) -> TestResult:
        """
        Фаза завершения: остановка генератора и формирование результата

        Returns:
            TestResult с результатами теста
        """
        self.state = State.FINISHED
        self.finished_at = datetime.now().timestamp()

        # Остановить генератор нагрузки
        self.adapter.stop()
        self.adapter.shutdown()

        # Найти максимальную стабильную нагрузку
        max_stable_users = 0
        max_stable_rps = 0.0

        if self.history:
            # Последняя стабильная точка перед остановкой
            max_stable_users = max(m.users for m in self.history)
            max_stable_rps = max(m.rps for m in self.history)

        # Сформировать результат
        return TestResult(
            started_at=self.started_at,
            finished_at=self.finished_at,
            max_stable_users=max_stable_users,
            max_stable_rps=max_stable_rps,
            stop_reason=self.stop_reason,
            history=self.history
        )

    def stop(self) -> None:
        """
        Остановить тест вручную

        Устанавливает причину остановки MANUAL и переводит в состояние FINISHED
        """
        self.stop_reason = StopReason.MANUAL
        self.state = State.FINISHED