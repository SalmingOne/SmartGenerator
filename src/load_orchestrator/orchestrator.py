import time
from datetime import datetime
from .models import State, StopReason, TestResult, AnalyzedMetrics, Decision
from .config import Config
from .interfaces.IAdapter import IAdapter
from .strategies.base import IStrategy
from .analytics.analyzer import Analyzer


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
        self.analyzer = Analyzer(window_size=config.orchestrator.window_size)

        self.state = State.INIT
        self.current_users = 0
        self.started_at: float | None = None
        self.history: list[AnalyzedMetrics] = []

    def run(self) -> TestResult:
        """
        Запустить тест

        TODO: Реализовать главный цикл:
        1. INIT:
           - adapter.launch()
           - Дождаться adapter.is_ready()
           - Перейти в RUNNING

        2. RUNNING (цикл):
           - time.sleep(stabilization_time)
           - raw_metrics = adapter.get_stats()
           - analyzed = analyzer.analyze(raw_metrics)
           - decision = strategy.decide(analyzed)
           - Сохранить в history

           Если decision == INCREASE:
               - next_users = strategy.get_next_users(current_users, analyzed)
               - adapter.configure(next_users, spawn_rate)
               - current_users = next_users

           Если decision == STOP:
               - Выход из цикла

        3. FINISHED:
           - adapter.stop()
           - adapter.shutdown()
           - Создать TestResult
           - Вернуть результат
        """
        self.started_at = datetime.now().timestamp()
        self.state = State.INIT

        # TODO: Реализовать запуск генератора
        # self.adapter.launch()
        # while not self.adapter.is_ready():
        #     time.sleep(1)

        self.state = State.RUNNING

        # TODO: Реализовать главный цикл
        # while True:
        #     time.sleep(self.config.orchestrator.stabilization_time)
        #     ...

        self.state = State.FINISHED

        # TODO: Создать и вернуть TestResult
        return TestResult(
            started_at=self.started_at,
            finished_at=datetime.now().timestamp(),
            max_stable_users=self.current_users,
            max_stable_rps=0.0,  # TODO: взять из последних метрик
            stop_reason=StopReason.MANUAL,  # TODO: определить причину
            history=self.history
        )

    def stop(self) -> None:
        """
        TODO: Остановить тест вручную

        - Вызвать adapter.stop()
        - Перейти в FINISHED
        """
        pass