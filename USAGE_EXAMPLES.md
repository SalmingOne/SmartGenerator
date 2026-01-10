# Примеры использования Load Orchestrator

## Быстрый старт

### 1. Запуск через CLI

```bash
# Spike тест
python run_test.py configs/spike.yaml

# Поиск деградации
python run_test.py configs/degradation.yaml

# SLA валидация
python run_test.py configs/sla_validation.yaml
```

### 2. Использование в коде

```python
from src.load_orchestrator import OrchestratorFactory

# Один лайнер - создать и запустить
orchestrator = OrchestratorFactory.from_yaml('configs/spike.yaml')
result = orchestrator.run()

print(f"Max stable users: {result.max_stable_users}")
print(f"Max stable RPS: {result.max_stable_rps}")
```

## До и После фабрики

### ❌ Было (вручную создавать всё)

```python
from src.load_orchestrator.config import Config
from src.load_orchestrator.adapters.LocustAdapter import LocustAdapter
from src.load_orchestrator.models import SpikeConfig
from src.load_orchestrator.strategies.spike import Spike
from src.load_orchestrator.orchestrator import Orchestrator

# Загрузить конфиг
config = Config.from_yaml('configs/spike.yaml')

# Создать адаптер вручную
adapter = LocustAdapter(
    test_file=config.adapter.test_file,
    host=config.adapter.host,
    port=config.adapter.port
)

# Создать стратегию вручную (нужно знать все параметры!)
spike_config = SpikeConfig(
    baseline_users=config.strategy.params.get('baseline_users'),
    baseline_duration=config.strategy.params.get('baseline_duration'),
    spike_users=config.strategy.params.get('spike_users'),
    spike_duration=config.strategy.params.get('spike_duration'),
    recovery_users=config.strategy.params.get('recovery_users'),
    recovery_duration=config.strategy.params.get('recovery_duration'),
)
strategy = Spike(config=spike_config)

# Создать оркестратор
orchestrator = Orchestrator(config, adapter, strategy)

# Запустить
result = orchestrator.run()
```

### ✅ Стало (фабрика делает всё сама)

```python
from src.load_orchestrator import OrchestratorFactory

# Всё в одну строку!
orchestrator = OrchestratorFactory.from_yaml('configs/spike.yaml')
result = orchestrator.run()
```

## Примеры конфигов

### Spike Test (configs/spike.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py
  host: 0.0.0.0
  port: 8089

strategy:
  type: spike
  baseline_users: 50
  baseline_duration: 30
  spike_users: 500
  spike_duration: 60
  recovery_users: 50
  recovery_duration: 30

orchestrator:
  spawn_rate: 10
  max_users: 1000
  monitoring_interval: 5  # Интервал сбора метрик в секундах
```

### Degradation Search (configs/degradation.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py

strategy:
  type: degradation_search
  initial_users: 10
  step_multiplier: 1.5
  max_users: 1000
  degradation_threshold: 0.7

orchestrator:
  spawn_rate: 10
```

### SLA Validation (configs/sla_validation.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py

strategy:
  type: sla_validation
  max_p99: 500  # ms
  max_error_rate: 1.0  # %
  initial_users: 10
  step_size: 50
  max_users: 1000

orchestrator:
  spawn_rate: 10
```

### Target RPS (configs/target_rps.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py

strategy:
  type: target_rps
  target_rps: 10000
  tolerance: 0.05  # 5%
  initial_users: 100
  step_size: 100

orchestrator:
  spawn_rate: 20
```

### Step Load (configs/step_load.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py

strategy:
  type: step_load
  step_size: 50
  step_duration: 60  # секунд
  initial_users: 10
  max_users: 1000

orchestrator:
  spawn_rate: 10
```

### Break Point (configs/break_point.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py

strategy:
  type: break_point
  initial_users: 50
  step_multiplier: 2.0  # Агрессивно
  error_threshold: 10.0  # %

orchestrator:
  spawn_rate: 50
```

### Canary Test (configs/canary.yaml)

```yaml
adapter:
  type: locust
  test_file: tests/locustfile.py

strategy:
  type: canary
  canary_users: 5
  canary_duration: 30  # секунд
  error_threshold: 1.0  # %

orchestrator:
  spawn_rate: 5
```

## Программный API

### Создание с кастомными параметрами

```python
from src.load_orchestrator import Config, OrchestratorFactory

# Загрузить конфиг
config = Config.from_yaml('configs/spike.yaml')

# Переопределить параметры программно
config.strategy.params['spike_users'] = 1000
config.orchestrator.spawn_rate = 50

# Создать orchestrator
orchestrator = OrchestratorFactory.create_orchestrator(config)
result = orchestrator.run()
```

### Создание адаптера и стратегии отдельно

```python
from src.load_orchestrator import Config, OrchestratorFactory, Orchestrator

config = Config.from_yaml('configs/spike.yaml')

# Создать только адаптер
adapter = OrchestratorFactory.create_adapter(config)

# Создать только стратегию
strategy = OrchestratorFactory.create_strategy(config)

# Создать orchestrator вручную
orchestrator = Orchestrator(config, adapter, strategy)
result = orchestrator.run()
```

### Обработка результатов

```python
from src.load_orchestrator import OrchestratorFactory

orchestrator = OrchestratorFactory.from_yaml('configs/spike.yaml')
result = orchestrator.run()

# Метаданные теста
print(f"Duration: {result.finished_at - result.started_at:.1f}s")
print(f"Stop reason: {result.stop_reason.name}")

# Результаты
print(f"Max stable users: {result.max_stable_users}")
print(f"Max stable RPS: {result.max_stable_rps:.1f}")

# История метрик
for i, metrics in enumerate(result.history):
    print(
        f"Step {i}: "
        f"users={metrics.users}, "
        f"rps={metrics.rps:.1f}, "
        f"p99={metrics.p99:.1f}ms, "
        f"errors={metrics.error_rate:.2f}%"
    )

# Анализ результатов
from src.load_orchestrator.analytics.metrics_calculator import MetricsCalculator

for i in range(1, len(result.history)):
    curr = result.history[i]
    prev = result.history[i-1]

    derived = MetricsCalculator.calculate_all(curr, prev)

    print(
        f"Step {i}: "
        f"degradation={derived['degradation_index']:.2f}, "
        f"stability={derived['stability']:.2f}, "
        f"efficiency={derived['scaling_efficiency']:.2f}"
    )
```

## Добавление новых адаптеров и стратегий

### Регистрация нового адаптера

```python
# В factory.py
from .adapters.JMeterAdapter import JMeterAdapter

class OrchestratorFactory:
    ADAPTERS = {
        'locust': LocustAdapter,
        'jmeter': JMeterAdapter,  # Добавить сюда
    }
```

### Регистрация новой стратегии

```python
# В factory.py
from .strategies.my_strategy import MyStrategy

class OrchestratorFactory:
    STRATEGIES = {
        'degradation_search': DegradationSearch,
        'my_strategy': MyStrategy,  # Добавить сюда
    }
```

## Error Handling

```python
from src.load_orchestrator import OrchestratorFactory

try:
    orchestrator = OrchestratorFactory.from_yaml('configs/spike.yaml')
    result = orchestrator.run()

except FileNotFoundError:
    print("Config file not found")

except ValueError as e:
    # Ошибки конфигурации: неподдерживаемый тип, неверные параметры
    print(f"Config error: {e}")

except KeyboardInterrupt:
    print("Test interrupted by user")
    orchestrator.stop()

except Exception as e:
    print(f"Unexpected error: {e}")
```

## Преимущества фабрики

✅ **Один конфиг** - вся настройка в YAML
✅ **Не нужно знать конструкторы** - фабрика сама создаёт объекты
✅ **Меньше кода** - 1 строка вместо 30+
✅ **Легко переключаться** - просто меняешь конфиг
✅ **Автоматическая валидация** - фабрика проверяет параметры
✅ **Расширяемость** - просто добавь в ADAPTERS/STRATEGIES

## Интеграция с Web-UI

Web-UI использует фабрику для создания orchestrator:

```python
# В web/api.py
from src.load_orchestrator import OrchestratorFactory

@app.post("/api/start")
async def start_test(config_path: str):
    orchestrator = OrchestratorFactory.from_yaml(config_path)
    result = orchestrator.run()
    return result
```