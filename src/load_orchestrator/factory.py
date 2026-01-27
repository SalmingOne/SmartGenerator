"""
Factory для создания Orchestrator из конфига

Автоматически создаёт:
- Adapter (LocustAdapter, JMeterAdapter, etc.)
- Strategy (DegradationSearch, Spike, SLAValidation, etc.)
- Orchestrator с правильными зависимостями
"""

from .config import Config
from .orchestrator import Orchestrator
from .adapters.IAdapter import IAdapter
from .strategies.base import IStrategy

# Импорт адаптеров
from .adapters.LocustAdapter import LocustAdapter

# Импорт стратегий
from .strategies.degradation_search import DegradationSearch
from .strategies.break_point import BreakPoint
from .strategies.sla_validation import SLAValidation
from .strategies.target_rps import TargetRPS
from .strategies.spike import Spike
from .strategies.canary import Canary
from .models import SpikeConfig


class OrchestratorFactory:
    """Фабрика для создания Orchestrator из конфига"""

    # Маппинг типов адаптеров на классы
    ADAPTERS = {
        'locust': LocustAdapter,
        # 'jmeter': JMeterAdapter,  # TODO
        # 'gatling': GatlingAdapter,  # TODO
    }

    # Маппинг типов стратегий на классы
    STRATEGIES = {
        'degradation_search': DegradationSearch,
        'break_point': BreakPoint,
        'sla_validation': SLAValidation,
        'target_rps': TargetRPS,
        'spike': Spike,
        'canary': Canary,
    }

    @classmethod
    def create_adapter(cls, config: Config) -> IAdapter:
        """
        Создать адаптер из конфига

        Args:
            config: Конфигурация

        Returns:
            Экземпляр адаптера

        Raises:
            ValueError: Если тип адаптера не поддерживается
        """
        adapter_type = config.adapter.type.lower()

        if adapter_type not in cls.ADAPTERS:
            supported = ', '.join(cls.ADAPTERS.keys())
            raise ValueError(
                f"Unsupported adapter type: '{adapter_type}'. "
                f"Supported types: {supported}"
            )

        adapter_class = cls.ADAPTERS[adapter_type]

        # Создать адаптер с параметрами из конфига
        return adapter_class(
            test_file=config.adapter.test_file,
            host=config.adapter.host,
            port=config.adapter.port
        )

    @classmethod
    def create_strategy(cls, config: Config) -> IStrategy:
        """
        Создать стратегию из конфига

        Args:
            config: Конфигурация

        Returns:
            Экземпляр стратегии

        Raises:
            ValueError: Если тип стратегии не поддерживается или параметры неверны
        """
        strategy_type = config.strategy.type.lower()

        if strategy_type not in cls.STRATEGIES:
            supported = ', '.join(cls.STRATEGIES.keys())
            raise ValueError(
                f"Unsupported strategy type: '{strategy_type}'. "
                f"Supported types: {supported}"
            )

        strategy_class = cls.STRATEGIES[strategy_type]
        params = config.strategy.params or {}

        # Создать стратегию с параметрами из конфига
        try:
            # Особый случай для Spike - требует SpikeConfig
            if strategy_type == 'spike':
                spike_config = SpikeConfig(
                    baseline_users=params.get('baseline_users', 50),
                    baseline_duration=params.get('baseline_duration', 30),
                    spike_users=params.get('spike_users', 500),
                    spike_duration=params.get('spike_duration', 60),
                    recovery_users=params.get('recovery_users', 50),
                    recovery_duration=params.get('recovery_duration', 30),
                )
                return strategy_class(config=spike_config)

            # Все остальные стратегии принимают параметры напрямую
            return strategy_class(**params)

        except TypeError as e:
            raise ValueError(
                f"Invalid parameters for strategy '{strategy_type}': {e}"
            ) from e

    @classmethod
    def create_orchestrator(cls, config: Config) -> Orchestrator:
        """
        Создать полностью настроенный Orchestrator из конфига

        Args:
            config: Конфигурация из YAML

        Returns:
            Готовый к запуску Orchestrator
        """
        adapter = cls.create_adapter(config)
        strategy = cls.create_strategy(config)

        return Orchestrator(
            config=config,
            adapter=adapter,
            strategy=strategy
        )

    @classmethod
    def from_yaml(cls, config_path: str) -> Orchestrator:
        """
        Создать Orchestrator напрямую из YAML файла

        Удобный shortcut для create_orchestrator(Config.from_yaml(...))

        Args:
            config_path: Путь к YAML конфигу

        Returns:
            Готовый к запуску Orchestrator

        """
        config = Config.from_yaml(config_path)
        return cls.create_orchestrator(config)