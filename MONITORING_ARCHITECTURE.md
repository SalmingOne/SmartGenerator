# Архитектура мониторинга с двумя таймерами

## Проблема

Раньше метрики собирались только при изменении нагрузки или истечении времени фазы. Это приводило к:
- Пропуску критических событий (внезапный рост ошибок)
- Невозможности быстро среагировать на проблемы
- Недостаточной детализации истории метрик
- Стратегия узнавала о деградации поздно (только при вызове `decide()`)

## Решение

Разделили два процесса с независимыми таймерами и добавили быструю проверку `should_stop()`:

### 1. **Мониторинг метрик** (каждые N секунд)
- **Интервал**: `monitoring_interval` из конфига (по умолчанию 5 секунд)
- **Действия**:
  - Сбор метрик через `adapter.get_stats()`
  - Добавление в историю `history.append(metrics)`
  - Проверка критических условий

### 2. **Принятие решений стратегией** (по расписанию стратегии)
- **Интервал**: `strategy.get_wait_time()` (зависит от стратегии)
- **Действия**:
  - Получение последних метрик из истории
  - Вызов `strategy.decide(metrics)`
  - Изменение нагрузки при необходимости

## Реализация

```python
def _running_phase(self) -> None:
    next_monitor_time = time.time()
    next_decision_time = time.time()

    while self.state == State.RUNNING:
        time.sleep(1)  # Проверяем каждую секунду
        now = time.time()

        # Таймер 1: Мониторинг
        if now >= next_monitor_time:
            metrics = self.adapter.get_stats()
            self.history.append(metrics)

            if self._check_critical_conditions(metrics):
                self.stop_reason = StopReason.DEGRADED
                break

            next_monitor_time = now + self.config.orchestrator.monitoring_interval

        # Таймер 2: Решения стратегии
        if now >= next_decision_time:
            metrics = self._get_latest_metrics()
            decision = self.strategy.decide(metrics)
            self._handle_decision(decision, metrics)
            next_decision_time = now + self.strategy.get_wait_time()
```

## Критические условия

### 1. Критические условия Orchestrator

Проверяются **при каждом сборе метрик** через `_check_critical_conditions()`:

```python
def _check_critical_conditions(self, metrics: RawMetrics) -> bool:
    # Катастрофический error rate (>50%)
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
```

### 2. Критические условия стратегии

Проверяются **при каждом сборе метрик** через `strategy.should_stop()`:

```python
# В Orchestrator при мониторинге:
if self.strategy.should_stop(metrics):
    self.state = State.FINISHED
    self.stop_reason = StopReason.DEGRADED
    break
```

Каждая стратегия реализует свои проверки:

**DegradationSearch:**
```python
def should_stop(self, metrics: RawMetrics) -> bool:
    degradation_index = MetricsCalculator.calculate_degradation_index(metrics)

    if degradation_index >= self.degradation_threshold:  # По умолчанию 0.7
        return True

    if metrics.error_rate > 10.0:  # Критический уровень ошибок
        return True

    return False
```

**BreakPoint:**
```python
def should_stop(self, metrics: RawMetrics) -> bool:
    if metrics.error_rate >= self.error_threshold:  # По умолчанию 10%
        return True

    if metrics.rps == 0 and metrics.users > 0:
        return True

    if metrics.p99 > 10000:  # > 10 секунд
        return True

    return False
```

**SLAValidation:**
```python
def should_stop(self, metrics: RawMetrics) -> bool:
    if metrics.p99 > self.max_p99:
        return True

    if metrics.error_rate > self.max_error_rate:
        return True

    if metrics.users >= self.max_users:  # Успешная валидация
        return True

    return False
```

### Зачем два уровня проверок?

1. **Orchestrator** проверяет универсальные катастрофические условия (>50% ошибок, RPS=0)
2. **Strategy** проверяет специфичные для стратегии условия (деградация, SLA, break point)

Это позволяет:
- Каждой стратегии иметь свою логику определения проблем
- Orchestrator гарантирует минимальную защиту от катастроф
- Быстро обнаруживать проблемы без ожидания `decide()`

## Примеры работы

### Spike стратегия

```yaml
orchestrator:
  monitoring_interval: 5  # Метрики каждые 5 секунд
```

- **Мониторинг**: каждые **5 секунд** собирает метрики
- **Решения**: каждую **1 секунду** (`get_wait_time()=1`) проверяет фазы
- **Результат**: Детальная история + быстрое переключение фаз

### DegradationSearch стратегия

```yaml
orchestrator:
  monitoring_interval: 5  # Метрики каждые 5 секунд
```

- **Мониторинг**: каждые **5 секунд** собирает метрики и проверяет критические условия
- **Решения**: каждые **30 секунд** (`get_wait_time()=30`) делает шаг увеличения нагрузки
- **Результат**: Если за 30 секунд error_rate станет 50%, тест остановится немедленно

## Конфигурация

```yaml
orchestrator:
  spawn_rate: 10               # Скорость набора пользователей
  max_users: 1000              # Максимум пользователей (критическое условие)
  monitoring_interval: 5       # Интервал сбора метрик в секундах
```

### Параметры:

- **spawn_rate**: Как быстро добавлять/убирать пользователей при изменении нагрузки
- **max_users**: Жёсткий лимит (при достижении тест останавливается)
- **monitoring_interval**: Частота сбора метрик и проверки критических условий

## Преимущества

✅ **Не пропускаем проблемы** - метрики собираются независимо от решений стратегии
✅ **Быстрая реакция** - критические условия проверяются каждые N секунд
✅ **Детальная история** - больше точек данных для анализа
✅ **Гибкость** - каждая стратегия контролирует свой темп принятия решений
✅ **Простота** - один цикл с двумя таймерами, без многопоточности

## Зачем без многопоточности?

В Python есть GIL (Global Interpreter Lock):
- Потоки не работают параллельно для CPU операций
- Для I/O (HTTP, sleep) потоки работают, но усложняют код
- **Решение с таймерами** проще, понятнее и достаточно эффективно

## Время реакции

С `monitoring_interval=5`:
- **Критическая проблема** обнаруживается за 1-6 секунд (в среднем 3.5с)
- **Накладные расходы**: ~1 HTTP запрос + проверки каждые 5 секунд
- **CPU/Memory**: Минимальные (~0.01% CPU, несколько KB памяти)

## Пример сценария (DegradationSearch)

**Конфигурация:**
- `monitoring_interval = 5` секунд
- `get_wait_time() = 30` секунд
- `degradation_threshold = 0.7`

**Таймлайн:**

```
T=0s    Старт теста, 100 users
        → Мониторинг: T=0s, Решения: T=0s

T=5s    Мониторинг: собрали метрики, проверили should_stop() → OK
        → Мониторинг: T=10s, Решения: T=30s

T=10s   Мониторинг: собрали метрики, проверили should_stop() → OK
        → Мониторинг: T=15s, Решения: T=30s

T=15s   Мониторинг: degradation_index=0.75! should_stop()=True
        ⚠️  STOP! Деградация обнаружена через 15 секунд

        БЕЗ should_stop(): узнали бы о деградации только в T=30s!
        Выигрыш: на 15 секунд раньше ✅
```

**Что происходит:**
1. **T=0-15s**: Нагрузка увеличивается, система деградирует
2. **T=15s**: Мониторинг обнаруживает degradation_index=0.75
3. **T=15s**: `should_stop()` возвращает True → STOP
4. **Без should_stop()**: ждали бы до T=30s (вызов `decide()`)

**Результат:** Тест остановился на 15 секунд раньше, не перегружая систему еще больше!