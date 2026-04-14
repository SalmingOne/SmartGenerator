from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml



@dataclass
class AdapterConfig:
    """Конфигурация адаптера"""
    type: str
    test_file: str
    port: int = 8089
    host: str = "0.0.0.0"


@dataclass
class StrategyConfig:
    """Конфигурация стратегии"""
    type: str
    params: dict[str, Any] | None = None


@dataclass
class OrchestratorConfig:
    """Конфигурация оркестратора"""
    spawn_rate: int = 10
    max_users: int | None = None
    monitoring_interval: int = 5
    max_wait_time: int | None = None

def _resolve_test_file(config_dir, test_file):
    test_path = Path(test_file)
    if test_path.is_absolute():
        if test_path.exists():
            return test_path
        raise ValueError(f'Test file {test_file} does not exist')

    current = config_dir.resolve()
    for parent in [current, *current.parents]:
        candidate = (parent / test_file).resolve()
        if candidate.exists():
            return candidate

@dataclass
class Config:
    """Полная конфигурация"""
    adapter: AdapterConfig
    strategy: StrategyConfig
    orchestrator: OrchestratorConfig

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """
        Загрузить конфигурацию из YAML файла

        Args:
            path: Путь к YAML файлу

        Returns:
            Config объект

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если конфигурация невалидна
        """
        path = Path(path).resolve()
        config_dir = path.parent

        print(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Config file is empty: {path}")

        # Валидация и парсинг adapter
        if 'adapter' not in data:
            raise ValueError("Missing 'adapter' section in config")

        adapter_data = data['adapter']
        if 'type' not in adapter_data:
            raise ValueError("Missing 'type' in adapter config")
        if 'test_file' not in adapter_data:
            raise ValueError("Missing 'test_file' in adapter config")

        test_file_path = _resolve_test_file(config_dir, adapter_data['test_file'])

        if not test_file_path.exists():
            raise ValueError(f"Test file not found: {test_file_path}")

        adapter = AdapterConfig(
            type=adapter_data['type'],
            test_file=adapter_data['test_file'],
            port=adapter_data.get('port', 8089),
            host=adapter_data.get('host', '0.0.0.0')
        )

        # Валидация и парсинг strategy
        if 'strategy' not in data:
            raise ValueError("Missing 'strategy' section in config")

        strategy_data = data['strategy']
        if 'type' not in strategy_data:
            raise ValueError("Missing 'type' in strategy config")

        strategy_params = {k: v for k, v in strategy_data.items() if k != 'type'}

        strategy = StrategyConfig(
            type=strategy_data['type'],
            params=strategy_params if strategy_params else None
        )

        # Парсинг orchestrator (опциональный)
        orchestrator_data = data.get('orchestrator', {})
        orchestrator = OrchestratorConfig(
            spawn_rate=orchestrator_data.get('spawn_rate', 10),
            max_users=orchestrator_data.get('max_users'),
            monitoring_interval=orchestrator_data.get('monitoring_interval', 5),
            max_wait_time=orchestrator_data.get('max_wait_time', None)
        )

        return cls(
            adapter=adapter,
            strategy=strategy,
            orchestrator=orchestrator
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Экспортировать конфигурацию в словарь

        Returns:
            Словарь с конфигурацией
        """
        return {
            'adapter': {
                'type': self.adapter.type,
                'test_file': self.adapter.test_file,
                'port': self.adapter.port,
                'host': self.adapter.host
            },
            'strategy': {
                'type': self.strategy.type,
                **(self.strategy.params or {})
            },
            'orchestrator': {
                'spawn_rate': self.orchestrator.spawn_rate,
                'max_users': self.orchestrator.max_users,
                'monitoring_interval': self.orchestrator.monitoring_interval,
                'max_wait_time': self.orchestrator.max_wait_time
            }
        }

    def to_yaml(self, path: str | Path) -> None:
        """
        Сохранить конфигурацию в YAML файл

        Args:
            path: Путь к YAML файлу
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)