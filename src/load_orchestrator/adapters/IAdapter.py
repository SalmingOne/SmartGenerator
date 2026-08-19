import subprocess
from abc import ABC, abstractmethod

from ..models import RawMetrics


class IAdapter(ABC):
    """Abstract interface for adapters."""

    def __init__(self, test_file: str):
        self.test_file = test_file
        self._process: subprocess.Popen | None = None

    @abstractmethod
    def launch(self, debug):
        """Запуск генератора"""
        pass

    def shutdown(self):
        if self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGINT)
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            self._process = None

    @abstractmethod
    def stop(self):
        """Остановка нагрузочного скрипта"""
        pass

    @abstractmethod
    def get_stats(self) -> RawMetrics:
        """Получение статистики по метрикам"""
        pass

    @abstractmethod
    def configure(self, **kwargs) -> None:
        """Начало или редактирование нагрузки"""

    @abstractmethod
    def is_ready(self) -> bool:
        pass
