# Web-UI: Выделение критичных точек на графиках

Каждая стратегия помечает точки своим уровнем критичности для визуализации в Web-UI.

## Архитектура

### 1. Уровни критичности

```python
# models.py
from enum import Enum

class PointSeverity(str, Enum):
    """Уровень критичности точки на графике"""
    NORMAL = "normal"      # 🟢 Зелёный - всё ок
    WARNING = "warning"    # 🟡 Жёлтый - близко к порогу
    CRITICAL = "critical"  # 🔴 Красный - превышен порог
```

### 2. Расширение RawMetrics

```python
@dataclass
class RawMetrics:
    timestamp: float
    users: int
    rps: float
    p50: float
    p95: float
    p99: float
    failed_requests: int
    error_rate: float
    total_requests: int

    # Аннотации для Web-UI
    severity: PointSeverity = PointSeverity.NORMAL
    severity_reason: str = ""  # "P99 близко к SLA" или "Начало деградации"
```

### 3. Метод в IStrategy

```python
class IStrategy(ABC):
    # ... существующие методы

    def annotate_metrics(self, metrics: RawMetrics) -> None:
        """
        Аннотировать метрики уровнем критичности

        Каждая стратегия определяет что является warning/critical
        Модифицирует metrics.severity и metrics.severity_reason

        Args:
            metrics: Метрики для аннотации (модифицируются in-place)
        """
        # Дефолтная реализация - ничего не делает
        pass
```

### 4. Вызов в Orchestrator

```python
def _running_phase(self) -> None:
    while self.state == State.RUNNING:
        wait_time = self.strategy.get_wait_time()
        time.sleep(wait_time)

        metrics = self.adapter.get_stats()

        # Стратегия помечает критичность точки
        self.strategy.annotate_metrics(metrics)

        self.history.append(metrics)

        decision = self.strategy.decide(metrics)
        # ...
```

---

## Примеры аннотаций для каждой стратегии

### 1. DegradationSearch

**Цель:** Показать как растёт индекс деградации

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    derived = MetricsCalculator.calculate_all(metrics, self._prev_metrics)

    # WARNING: индекс деградации 0.5-0.7
    if 0.5 <= derived['degradation_index'] < 0.7:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Degradation index: {derived['degradation_index']:.2f}"

    # CRITICAL: индекс деградации >= 0.7
    elif derived['degradation_index'] >= 0.7:
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = f"High degradation: {derived['degradation_index']:.2f}"

    # WARNING: падает scaling efficiency
    elif derived['scaling_efficiency'] < 0.5:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Low scaling efficiency: {derived['scaling_efficiency']:.2f}"

    # WARNING: растёт нестабильность
    elif derived['stability'] > 2.0:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Instability detected: P99/P50={derived['stability']:.2f}"
```

**Визуализация:**
- 🟢 Зелёные точки - система масштабируется хорошо (degradation_index < 0.5)
- 🟡 Жёлтые точки - эффективность падает, индекс растёт (0.5-0.7)
- 🔴 Красная точка - деградация обнаружена (>= 0.7, последняя точка)

**Графики:**
1. **RPS vs Users** - цвет показывает деградацию
2. **Degradation Index** - отдельный график с порогами 0.5, 0.7
3. **Scaling Efficiency** - показать падение эффективности

---

### 2. SLAValidation

**Цель:** Показать насколько близко к нарушению SLA

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    # WARNING: P99 близко к SLA (80-100% от лимита)
    if metrics.p99 > self.max_p99 * 0.8:
        if metrics.p99 > self.max_p99:
            metrics.severity = PointSeverity.CRITICAL
            metrics.severity_reason = f"SLA violated: P99={metrics.p99}ms (max: {self.max_p99}ms)"
        else:
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = f"Close to SLA: P99={metrics.p99}ms ({metrics.p99/self.max_p99*100:.0f}%)"

    # WARNING: error_rate близко к SLA
    elif metrics.error_rate > self.max_error_rate * 0.7:
        if metrics.error_rate > self.max_error_rate:
            metrics.severity = PointSeverity.CRITICAL
            metrics.severity_reason = f"SLA violated: errors={metrics.error_rate}%"
        else:
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = f"Errors rising: {metrics.error_rate}%"
```

**Визуализация:**
- 🟢 Зелёные - SLA соблюдается с запасом (< 80% лимита)
- 🟡 Жёлтые - близко к порогу SLA (80-100%)
- 🔴 Красная - SLA нарушен (>= 100%)

**Графики:**
1. **P99 Latency** - с линией SLA threshold, зоны: safe/warning/critical
2. **Error Rate** - с линией SLA threshold
3. **RPS vs Users** - цвет показывает соблюдение SLA

---

### 3. TargetRPS

**Цель:** Показать прогресс к цели и плато

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    target_percent = metrics.rps / self.target_rps * 100

    # WARNING: RPS перестал расти (плато)
    if self._is_plateau():
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"RPS plateau at {metrics.rps:.0f} ({target_percent:.0f}% of target)"

    # WARNING: близко к цели (80-95%)
    elif 0.8 <= target_percent / 100 < 0.95:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Approaching target: {target_percent:.0f}%"

    # CRITICAL: достигли цели!
    elif target_percent >= 95:
        metrics.severity = PointSeverity.CRITICAL  # Не ошибка, просто выделить
        metrics.severity_reason = f"Target reached: {metrics.rps:.0f} RPS ✓"

    # WARNING: деградация началась
    derived = MetricsCalculator.calculate_degradation_index(metrics)
    if derived > 0.5:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Degradation started (index: {derived:.2f})"

def _is_plateau(self) -> bool:
    """RPS не растёт последние 3 итерации"""
    if len(self._rps_history) < 3:
        return False
    recent_rps = self._rps_history[-3:]
    return max(recent_rps) - min(recent_rps) < self.target_rps * 0.05
```

**Визуализация:**
- 🟢 Зелёные - RPS растёт нормально (< 80% цели)
- 🟡 Жёлтые - плато или деградация, либо близко к цели (80-95%)
- 🔴 Красная - цель достигнута! (>= 95%)

**Графики:**
1. **RPS Progress** - прогресс-бар к целевому RPS
2. **RPS vs Time** - с линией target_rps, выделить плато
3. **Users vs RPS** - показать где начался plateau

---

### 4. BreakPoint

**Цель:** Показать критические состояния системы

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    # CRITICAL: система перестала отвечать
    if metrics.rps == 0 and metrics.users > 0:
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = "System stopped responding"

    # CRITICAL: критический уровень ошибок
    elif metrics.error_rate >= 10.0:
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = f"Critical error rate: {metrics.error_rate}%"

    # WARNING: высокий уровень ошибок
    elif metrics.error_rate >= 5.0:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"High error rate: {metrics.error_rate}%"

    # CRITICAL: экстремальная латентность
    elif metrics.p99 > 10000:
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = f"Extreme latency: {metrics.p99}ms"

    # WARNING: высокая латентность
    elif metrics.p99 > 5000:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"High latency: {metrics.p99}ms"

    # WARNING: RPS падает
    if self._prev_rps and metrics.rps < self._prev_rps * 0.8:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"RPS dropping: {metrics.rps:.0f} (was {self._prev_rps:.0f})"
```

**Визуализация:**
- 🟢 Зелёные - система справляется
- 🟡 Жёлтые - ошибки растут, латентность высокая, RPS падает
- 🔴 Красные - система ломается (ошибки > 10%, RPS=0, p99 > 10s)

**Графики:**
1. **Error Rate** - критические зоны: > 5% (warning), > 10% (critical)
2. **P99 Latency** - зоны: > 5s (warning), > 10s (critical)
3. **RPS Trend** - показать падение RPS

---

### 5. StepLoad

**Цель:** Показать стабильность на каждой ступени

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    # WARNING: первая точка на новой ступени
    if len(self._step_metrics) == 1:
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Step {self._current_step} started ({metrics.users} users)"

    # Проверка стабильности на ступени
    elif len(self._step_metrics) >= 3:
        # CRITICAL: нестабильность
        if not self._is_step_stable():
            metrics.severity = PointSeverity.CRITICAL
            metrics.severity_reason = f"Unstable on step {self._current_step}"

        # WARNING: высокая вариация P99
        p99_values = [m.p99 for m in self._step_metrics[-3:]]
        cv = np.std(p99_values) / np.mean(p99_values)
        if cv > 0.15:  # Вариация > 15%
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = f"High P99 variation: {cv*100:.0f}%"

def _is_step_stable(self) -> bool:
    """Коэффициент вариации < 20%"""
    p99_values = [m.p99 for m in self._step_metrics]
    rps_values = [m.rps for m in self._step_metrics]

    p99_cv = np.std(p99_values) / np.mean(p99_values)
    rps_cv = np.std(rps_values) / np.mean(rps_values)

    return p99_cv < 0.2 and rps_cv < 0.2
```

**Визуализация:**
- 🟡 Жёлтые - начало каждой ступени (переход)
- 🟢 Зелёные - стабильные точки на ступени
- 🔴 Красные - нестабильность обнаружена (высокая вариация)

**Графики:**
1. **Step Progression** - ступенчатый график с выделением ступеней
2. **Stability Index** - CV для P99 и RPS на каждой ступени
3. **Metrics Distribution** - box plot для каждой ступени

---

### 6. Spike

**Цель:** Показать фазы и восстановление

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    # Разные критерии для разных фаз

    if self._phase == SpikePhase.BASELINE:
        # Baseline должен быть стабильным
        if metrics.error_rate > 1.0:
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = "Errors during baseline"

        # Выделить последнюю точку baseline
        elapsed = metrics.timestamp - self.phase_start_time
        if elapsed > self.config.baseline_duration * 0.9:
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = "Baseline ending, spike starting soon"

    elif self._phase == SpikePhase.SPIKE:
        # Spike - ожидаем проблемы
        elapsed = metrics.timestamp - self.phase_start_time

        # Выделить начало spike
        if elapsed < 5:  # Первые 5 секунд
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = f"Spike started: {metrics.users} users"

        # CRITICAL: критические ошибки во время spike
        if metrics.error_rate > 20:
            metrics.severity = PointSeverity.CRITICAL
            metrics.severity_reason = f"Critical errors during spike: {metrics.error_rate}%"

        # WARNING: ошибки во время spike (ожидаемо)
        elif metrics.error_rate > 5:
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = f"Errors during spike: {metrics.error_rate}%"

    elif self._phase == SpikePhase.RECOVERY:
        # Recovery - проверяем восстановление
        if self.baseline_metrics:
            rps_recovery = metrics.rps / self.baseline_metrics.rps
            latency_recovery = metrics.p99 / self.baseline_metrics.p99

            # CRITICAL: плохое восстановление RPS (< 70%)
            if rps_recovery < 0.7:
                metrics.severity = PointSeverity.CRITICAL
                metrics.severity_reason = f"Poor RPS recovery: {rps_recovery*100:.0f}%"

            # WARNING: частичное восстановление (70-90%)
            elif rps_recovery < 0.9:
                metrics.severity = PointSeverity.WARNING
                metrics.severity_reason = f"Partial recovery: {rps_recovery*100:.0f}%"

            # WARNING: латентность не восстановилась
            elif latency_recovery > 1.2:
                metrics.severity = PointSeverity.WARNING
                metrics.severity_reason = f"Latency not recovered: {latency_recovery*100:.0f}% of baseline"

            # Выделить последнюю точку recovery
            elapsed = metrics.timestamp - self.phase_start_time
            if elapsed > self.config.recovery_duration * 0.9:
                metrics.severity = PointSeverity.WARNING
                metrics.severity_reason = "Recovery phase ending"
```

**Визуализация:**
- **Baseline:** 🟢 зелёные, 🟡 последняя точка
- **Spike:** 🟡 первая точка, 🟡/🔴 по уровню ошибок
- **Recovery:** 🟢/🟡/🔴 по степени восстановления

**Графики:**
1. **Timeline с фазами** - цветные зоны: baseline/spike/recovery
2. **RPS Comparison** - baseline RPS vs spike RPS vs recovery RPS
3. **Recovery Progress** - процент восстановления RPS и latency

---

### 7. Canary

**Цель:** Быстро показать проблемы

```python
def annotate_metrics(self, metrics: RawMetrics) -> None:
    # CRITICAL: любые ошибки - плохо для canary
    if metrics.error_rate > self.error_threshold:  # Например, 1%
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = f"Errors detected: {metrics.error_rate}%"

    # CRITICAL: латентность слишком высокая
    elif metrics.p99 > 5000:  # 5 секунд
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = f"High latency: {metrics.p99}ms"

    # WARNING: латентность повышена
    elif metrics.p99 > 2000:  # 2 секунды
        metrics.severity = PointSeverity.WARNING
        metrics.severity_reason = f"Elevated latency: {metrics.p99}ms"

    # CRITICAL: система не отвечает
    elif metrics.rps == 0 and metrics.users > 0:
        metrics.severity = PointSeverity.CRITICAL
        metrics.severity_reason = "System not responding"

    # WARNING: прогресс проверки
    elapsed = metrics.timestamp - self._started_at
    progress = elapsed / self.canary_duration * 100

    if progress > 50 and metrics.severity == PointSeverity.NORMAL:
        # Показать прогресс на половине
        if progress < 60:
            metrics.severity = PointSeverity.WARNING
            metrics.severity_reason = f"Canary progress: {progress:.0f}%"
```

**Визуализация:**
- 🟢 Зелёные - всё работает
- 🟡 Жёлтые - половина проверки пройдена, латентность повышена
- 🔴 Красные - ошибки или высокая латентность

**Графики:**
1. **Quick Check** - simple dashboard: ✓/✗ для каждой метрики
2. **Timeline** - прогресс проверки с порогами
3. **Status** - PASS/FAIL с детальной информацией

---

## Web-UI: Визуализация

### График с аннотациями (Plotly.js)

```javascript
const traces = {
  rps: {
    x: timestamps,
    y: rps_values,
    mode: 'lines+markers',
    marker: {
      color: severities.map(s =>
        s === 'critical' ? '#dc2626' :   // red-600
        s === 'warning' ? '#f59e0b' :    // amber-500
        '#10b981'                        // green-500
      ),
      size: severities.map(s =>
        s === 'critical' ? 12 :
        s === 'warning' ? 10 :
        6
      ),
      line: {
        color: 'white',
        width: 1
      }
    },
    line: {
      color: '#6b7280',  // gray-500
      width: 2
    },
    hovertemplate:
      '<b>%{customdata.reason}</b><br>' +
      'Time: %{x}<br>' +
      'RPS: %{y:.0f}<br>' +
      '<extra></extra>',
    customdata: severity_data  // {reason: "...", severity: "..."}
  }
}
```

### Легенда

```html
<div class="legend">
  <div class="legend-item">
    <span class="dot green"></span>
    NORMAL - Система работает стабильно
  </div>
  <div class="legend-item">
    <span class="dot yellow"></span>
    WARNING - Близко к порогу / Требует внимания
  </div>
  <div class="legend-item">
    <span class="dot red"></span>
    CRITICAL - Порог превышен / Критическое состояние
  </div>
</div>
```

### Tooltip при наведении

```html
<div class="tooltip">
  <div class="tooltip-header">
    ⚠️ Close to SLA
  </div>
  <div class="tooltip-body">
    Time: 14:35:22<br>
    Users: 150<br>
    RPS: 1250<br>
    P99: 480ms (96% of limit)<br>
    Error Rate: 0.5%
  </div>
</div>
```

### Боковая панель с статистикой

```html
<div class="stats-panel">
  <h3>Critical Points: 3</h3>
  <ul>
    <li class="critical">
      <strong>14:36:15</strong>
      SLA violated: P99=520ms
    </li>
    <li class="warning">
      <strong>14:35:22</strong>
      Close to SLA: P99=480ms (96%)
    </li>
    <li class="warning">
      <strong>14:34:10</strong>
      Errors rising: 0.8%
    </li>
  </ul>
</div>
```

---

## Сводная таблица аннотаций

| Стратегия | 🟢 NORMAL | 🟡 WARNING | 🔴 CRITICAL |
|-----------|-----------|------------|-------------|
| **DegradationSearch** | degradation < 0.5 | 0.5 ≤ degradation < 0.7<br>efficiency < 0.5<br>stability > 2 | degradation ≥ 0.7 |
| **BreakPoint** | errors < 5% | 5% ≤ errors < 10%<br>p99 > 5s<br>RPS падает | errors ≥ 10%<br>rps = 0<br>p99 > 10s |
| **SLAValidation** | < 80% лимита | 80-100% лимита | > 100% лимита |
| **TargetRPS** | < 80% цели | 80-95% цели<br>plateau<br>degradation > 0.5 | ≥ 95% цели |
| **StepLoad** | Стабильно | Начало ступени<br>CV > 15% | Нестабильно<br>CV > 20% |
| **Spike** | Baseline OK | Переходы<br>Ошибки 5-20%<br>Recovery 70-90% | Ошибки > 20%<br>Recovery < 70% |
| **Canary** | Всё OK | Латентность > 2s<br>Прогресс 50% | Ошибки > 1%<br>Латентность > 5s |

---

## Преимущества подхода

✅ **Каждая стратегия сама решает** что критично для её целей
✅ **Единая структура** - все используют `PointSeverity`
✅ **Контекстные пояснения** - `severity_reason` объясняет причину
✅ **Обратная совместимость** - дефолтная реализация ничего не делает
✅ **Простая интеграция** - Web-UI просто смотрит на `severity` поле
✅ **Информативность** - пользователь сразу видит проблемные участки
✅ **Интерактивность** - hover показывает детали, клик может открыть детальный анализ

## Примеры использования

### 1. Быстрый анализ результатов
Пользователь открывает график и сразу видит:
- Где началась деградация (жёлтые/красные точки)
- Какие метрики стали критичными
- Причины остановки теста

### 2. Сравнение тестов
При сравнении двух запусков видно:
- В какой момент тесты начали различаться
- Какие пороги были достигнуты в каждом

### 3. Экспорт в отчёты
Аннотации можно использовать для генерации текстовых отчётов:
```
Test Summary:
- Started: 14:30:00
- Finished: 14:36:45
- Critical points: 3
  1. [14:36:15] SLA violated: P99=520ms
  2. [14:35:22] Close to SLA: P99=480ms (96%)
  3. [14:34:10] Errors rising: 0.8%
```