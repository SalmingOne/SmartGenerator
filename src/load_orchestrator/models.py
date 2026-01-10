from dataclasses import dataclass, field
from enum import Enum, auto


class Decision(Enum):
    CONTINUE = auto()
    HOLD = auto()
    STOP = auto()

class State(Enum):
    INIT = auto()
    RUNNING = auto()
    FINISHED = auto()


class StopReason(Enum):
    """Причины остановки"""
    DEGRADATION = auto()     # Найдена деградация
    BREAK_POINT = auto()     # Система сломалась
    TARGET_REACHED = auto()  # Цель достигнута
    SLA_VIOLATED = auto()    # SLA нарушен
    MAX_USERS = auto()       # Достигнут лимит юзеров
    TIMEOUT = auto()         # Таймаут теста
    MANUAL = auto()          # Ручная остановка
    ERROR = auto()           # Ошибка


@dataclass
class RawMetrics:
    timestamp: float
    users: int
    rps: float
    rt_avg: float  # Среднее время ответа (ms) - для Locust-SDI
    p50: float
    p95: float
    p99: float
    failed_requests: int
    error_rate: float
    total_requests: int

@dataclass
class TestResult:
    """Результат теста"""
    started_at: float
    finished_at: float | None
    max_stable_users: int
    max_stable_rps: float
    stop_reason: StopReason
    history: list[RawMetrics] = field(default_factory=list)


class SpikePhase(Enum):
    BASELINE = auto()      # Начальная нагрузка
    SPIKE = auto()         # Резкий скачок
    RECOVERY = auto()      # Восстановление
    FINISHED = auto()


@dataclass
class SpikeConfig:
    baseline_users: int = 50
    baseline_duration: float = 30
    spike_users: int = 500
    spike_duration: float = 60
    recovery_users: int = 50
    recovery_duration: float = 30