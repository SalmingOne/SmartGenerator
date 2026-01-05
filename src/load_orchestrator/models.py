from dataclasses import dataclass, field
from enum import Enum, auto


class Decision(Enum):
    INCREASE = auto()
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
    p50: float
    p95: float
    p99: float
    failed_requests: int
    error_rate: float
    total_requests: int

@dataclass
class AnalyzedMetrics:
    """Метрики после анализа"""
    raw: RawMetrics
    stability: float = 0.0            # P99/P50 — чем ближе к 1, тем стабильнее
    scaling_efficiency: float = 0.0   # delta_rps / delta_users
    degradation_index: float = 0.0    # Комплексный индекс (0 — норм, 1 — плохо)


@dataclass
class TestResult:
    """Результат теста"""
    started_at: float
    finished_at: float | None
    max_stable_users: int
    max_stable_rps: float
    stop_reason: StopReason
    history: list[AnalyzedMetrics] = field(default_factory=list)