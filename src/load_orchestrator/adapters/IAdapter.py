import subprocess
from abc import ABC, abstractmethod


class IAdapter(ABC):
    """Abstract interface for adapters."""

    def __init__(self, test_file: str):
        self.test_file = test_file
        self._process: subprocess.Popen | None = None

    @abstractmethod
    def launch(self):
        """Запуск генератора"""
        pass

    def shutdown(self):
        """Остановка генератора"""
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None

    @abstractmethod
    def stop(self):
        """Остановка нагрузочного скрипта"""
        pass

    @abstractmethod
    def get_stats(self):
        """Получение статистики по метрикам"""
        pass

    @abstractmethod
    def configure(self, **kwargs):
        """Начало или редактирование нагрузки"""

    @abstractmethod
    def is_ready(self):
        pass
