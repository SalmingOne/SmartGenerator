# Проверки для стратегий нагрузочного тестирования

Каждая стратегия должна иметь **свои критерии успеха/провала**, соответствующие её цели.

## 1. DegradationSearch - Найти начало деградации

**Цель:** Найти точку где система начинает терять эффективность

**Проверки:**
```python
def decide(self, metrics: RawMetrics) -> Decision:
    # Рассчитать производные метрики
    derived = MetricsCalculator.calculate_all(metrics, self._prev_metrics)

    # 1. Комплексный индекс деградации (основной критерий)
    if derived['degradation_index'] >= 0.7:  # Начало деградации
        self.stop_reason = "Degradation detected"
        return Decision.STOP

    # 2. Падение эффективности масштабирования
    if derived['scaling_efficiency'] < 0.3:  # RPS на юзера упал
        self.stop_reason = "Scaling efficiency degraded"
        return Decision.STOP

    # 3. Рост нестабильности (разброс латентности)
    if derived['stability'] > 3.0:  # P99/P50 > 3
        self.stop_reason = "System became unstable"
        return Decision.STOP

    # 4. Базовые ошибки (страховка)
    if metrics.error_rate > 5.0:  # 5% - ещё терпимо для поиска деградации
        self.stop_reason = "Error rate too high"
        return Decision.STOP

    return Decision.CONTINUE
```

**Ключевое отличие:** Использует **сложные индексы** и **относительные метрики** (эффективность масштабирования, стабильность).

---

## 2. BreakPoint - Найти точку полного отказа

**Цель:** Доломать систему до полного отказа

**Проверки:**
```python
def decide(self, metrics: RawMetrics) -> Decision:
    # 1. Критический уровень ошибок
    if metrics.error_rate >= 10.0:  # 10% - система не справляется
        self.stop_reason = "Critical error rate"
        return Decision.STOP

    # 2. Система перестала отвечать
    if metrics.rps == 0 and metrics.users > 0:
        self.stop_reason = "System stopped responding"
        return Decision.STOP

    # 3. Экстремальная латентность (система зависла)
    if metrics.p99 > 10000:  # 10 секунд - практически таймаут
        self.stop_reason = "Extreme latency detected"
        return Decision.STOP

    # 4. RPS начал падать (под нагрузкой throughput снижается)
    if self._prev_rps and metrics.rps < self._prev_rps * 0.5:
        self.stop_reason = "RPS dropped by 50%"
        return Decision.STOP

    return Decision.CONTINUE
```

**Ключевое отличие:** **Агрессивные пороги**, проверка **критических состояний** (система мертва/зависла).

---

## 3. SLAValidation - Проверить соблюдение SLA

**Цель:** Найти максимальную нагрузку при соблюдении SLA

**Проверки:**
```python
def decide(self, metrics: RawMetrics) -> Decision:
    # 1. Проверка SLA по латентности
    if metrics.p99 > self.max_p99:  # Например, 500ms
        self.stop_reason = f"SLA violated: P99={metrics.p99}ms > {self.max_p99}ms"
        return Decision.STOP

    # 2. Проверка SLA по ошибкам
    if metrics.error_rate > self.max_error_rate:  # Например, 1%
        self.stop_reason = f"SLA violated: error_rate={metrics.error_rate}% > {self.max_error_rate}%"
        return Decision.STOP

    # 3. Достигли лимита (SLA соблюдается!)
    if metrics.users >= self.max_users:
        self.stop_reason = f"SLA passed at {metrics.users} users"
        return Decision.STOP

    # Опционально: проверить p95 тоже
    if self.max_p95 and metrics.p95 > self.max_p95:
        self.stop_reason = f"SLA violated: P95={metrics.p95}ms"
        return Decision.STOP

    return Decision.CONTINUE
```

**Ключевое отличие:** **Конкретные пороги SLA**, никаких индексов, только **простые метрики** (p99, error_rate).

---

## 4. TargetRPS - Достичь целевого RPS

**Цель:** Проверить может ли система выдать N rps

**Проверки:**
```python
def decide(self, metrics: RawMetrics) -> Decision:
    # 1. Цель достигнута!
    target_with_tolerance = self.target_rps * (1 - self.tolerance)
    if metrics.rps >= target_with_tolerance:
        self.stop_reason = f"Target reached: {metrics.rps} RPS"
        return Decision.STOP

    # 2. RPS перестал расти (упёрлись в потолок)
    if self._check_rps_plateau(metrics):
        self.stop_reason = f"RPS plateau at {metrics.rps}, target {self.target_rps}"
        return Decision.STOP

    # 3. Началась деградация (не дойдём до цели)
    derived = MetricsCalculator.calculate_degradation_index(metrics)
    if derived > 0.6:
        self.stop_reason = f"Degradation before target: {metrics.rps}/{self.target_rps} RPS"
        return Decision.STOP

    # 4. Базовые проверки
    if metrics.error_rate > 5.0:
        self.stop_reason = "Too many errors before target"
        return Decision.STOP

    return Decision.CONTINUE

def _check_rps_plateau(self, metrics: RawMetrics) -> bool:
    """RPS не растёт последние N итераций"""
    if len(self._rps_history) < 3:
        return False

    recent_rps = self._rps_history[-3:]
    # Если рост < 5% за 3 итерации
    return max(recent_rps) - min(recent_rps) < self.target_rps * 0.05
```

**Ключевое отличие:** Фокус на **достижении цели** (target_rps), проверка **плато** (RPS перестал расти).

---

## 5. StepLoad - Ступенчатая нагрузка

**Цель:** Проверить стабильность на каждой ступени

**Проверки:**
```python
def decide(self, metrics: RawMetrics) -> Decision:
    self._step_metrics.append(metrics)

    # Если держим ступень достаточно долго, проверяем стабильность
    if len(self._step_metrics) >= 3:  # Минимум 3 проверки

        # 1. Проверка стабильности метрик на ступени
        if not self._is_step_stable():
            self.stop_reason = f"Unstable at step {self._current_step}"
            return Decision.STOP

        # 2. Проверка деградации на ступени
        avg_degradation = self._calculate_step_degradation()
        if avg_degradation > 0.6:
            self.stop_reason = f"Degradation on step {self._current_step}"
            return Decision.STOP

        # 3. Достигли max_users
        if metrics.users >= self.max_users:
            self.stop_reason = f"Max users reached"
            return Decision.STOP

        # Ступень стабильна - переход на следующую
        self._current_step += 1
        self._step_metrics = []
        return Decision.CONTINUE

    # Ещё держим текущую ступень
    return Decision.HOLD

def _is_step_stable(self) -> bool:
    """Проверка стабильности метрик на ступени (низкая вариация)"""
    p99_values = [m.p99 for m in self._step_metrics]
    rps_values = [m.rps for m in self._step_metrics]

    # Коэффициент вариации < 20% (стабильно)
    p99_cv = np.std(p99_values) / np.mean(p99_values)
    rps_cv = np.std(rps_values) / np.mean(rps_values)

    return p99_cv < 0.2 and rps_cv < 0.2
```

**Ключевое отличие:** Проверка **вариации метрик** на ступени (стабильность во времени), работа с **историей ступени**.

---

## 6. Spike - Проверка восстановления после скачка

**Цель:** Проверить восстанавливается ли система после резкого скачка

**Проверки:**
```python
def _handle_spike(self, metrics: RawMetrics, elapsed: float) -> Decision:
    # 1. Критический отказ во время spike
    if metrics.error_rate > 50:
        self.stop_reason = "System failed during spike"
        return Decision.STOP

    # 2. Система перестала отвечать
    if metrics.rps == 0:
        self.stop_reason = "System stopped responding"
        return Decision.STOP

    # Фаза spike завершена
    if elapsed >= self.config.spike_duration:
        self._phase = SpikePhase.RECOVERY
        return Decision.CONTINUE

    return Decision.HOLD

def _handle_recovery(self, metrics: RawMetrics, elapsed: float) -> Decision:
    if elapsed >= self.config.recovery_duration:
        # Анализ восстановления
        recovery_result = self._analyze_recovery()

        # 1. Проверка восстановления RPS
        if recovery_result['rps_recovered'] < 0.9:  # Не восстановился на 90%
            self.stop_reason = f"Poor RPS recovery: {recovery_result['rps_recovered']*100}%"

        # 2. Проверка восстановления латентности
        elif recovery_result['latency_recovered']:
            self.stop_reason = f"Latency not recovered: P99={metrics.p99}ms vs baseline={self.baseline_metrics.p99}ms"

        # 3. Проверка ошибок после spike
        elif metrics.error_rate > self.baseline_metrics.error_rate * 2:
            self.stop_reason = f"Error rate increased after spike"

        else:
            self.stop_reason = "Spike test completed successfully"

        return Decision.STOP

    return Decision.HOLD

def _analyze_recovery(self) -> dict:
    """Сравнить recovery с baseline"""
    recovery_avg = self._calculate_avg_metrics(self.recovery_metrics)

    return {
        'rps_recovered': recovery_avg.rps / self.baseline_metrics.rps,
        'latency_recovered': recovery_avg.p99 <= self.baseline_metrics.p99 * 1.2,
        'errors_ok': recovery_avg.error_rate <= self.baseline_metrics.error_rate * 1.5
    }
```

**Ключевое отличие:** **Сравнение baseline vs recovery**, проверка **восстановления** (RPS вернулся, латентность нормализовалась).

---

## 7. Canary - Быстрая smoke-проверка

**Цель:** Быстро проверить что система вообще работает

**Проверки:**
```python
def decide(self, metrics: RawMetrics) -> Decision:
    # 1. Любые ошибки - плохо для canary
    if metrics.error_rate > self.error_threshold:  # Например, 1%
        self.stop_reason = f"Errors detected: {metrics.error_rate}%"
        return Decision.STOP

    # 2. Латентность слишком высокая
    if metrics.p99 > 5000:  # 5 секунд - явно проблема
        self.stop_reason = f"High latency: {metrics.p99}ms"
        return Decision.STOP

    # 3. Система не отвечает
    if metrics.rps == 0 and metrics.users > 0:
        self.stop_reason = "System not responding"
        return Decision.STOP

    # 4. Прошло достаточно времени - всё OK
    elapsed = metrics.timestamp - self._started_at
    if elapsed >= self.canary_duration:
        self.stop_reason = "Canary passed"
        return Decision.STOP

    return Decision.HOLD
```

**Ключевое отличие:** **Строгие пороги** (даже 1% ошибок это плохо), **быстрая проверка** (30-60 сек), никаких сложных индексов.

---

## Сводная таблица

| Стратегия | Основные проверки | Особенность |
|-----------|------------------|-------------|
| **DegradationSearch** | degradation_index, scaling_efficiency, stability | Сложные индексы, относительные метрики |
| **BreakPoint** | error_rate > 10%, rps == 0, p99 > 10s | Агрессивные пороги, критические состояния |
| **SLAValidation** | p99 < max_p99, error_rate < max_error_rate | Конкретные SLA пороги |
| **TargetRPS** | rps >= target, plateau detection, degradation | Проверка достижения цели и плато |
| **StepLoad** | Вариация метрик на ступени, стабильность | Статистика по истории ступени |
| **Spike** | Сравнение baseline vs recovery | Проверка восстановления |
| **Canary** | error_rate > 1%, p99 > 5s | Строгие пороги, быстро |

## Общие принципы

### Каждая стратегия проверяет:
1. **Основной критерий** - соответствует цели стратегии
2. **Критические состояния** - система мертва/зависла (страховка)
3. **Специфические метрики** - уникальные для каждой стратегии

### Философия проверок:

- **DegradationSearch**: "Когда **начинается** ухудшение?"
- **BreakPoint**: "Когда система **полностью ломается**?"
- **SLAValidation**: "Соблюдается ли **SLA**?"
- **TargetRPS**: "Можем ли достичь **цели**?"
- **StepLoad**: "**Стабильна** ли каждая ступень?"
- **Spike**: "**Восстанавливается** ли после скачка?"
- **Canary**: "**Работает** ли вообще?"