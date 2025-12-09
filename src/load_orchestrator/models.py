from dataclasses import dataclass
from enum import Enum, auto


class Decision(Enum):
    INCREASE = auto()
    HOLD = auto()
    STOP = auto()

class State(Enum):
    INITIAL = auto()
    RUNNING = auto()
    STOPPED = auto()

class Reason(Enum):
    ERROR = auto()


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
class Metrics:
    stability: float
    scale_factor: float = 0.0
    degradation_index: float = 0.0

@dataclass
class Result:
    started_at: float
    finished_at: float
    max_stable_users: int
    max_stable_rps: float
    stop_reason: Reason
    stability_index: float