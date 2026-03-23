from dataclasses import dataclass
from typing import Any


@dataclass
class FieldDef:
    name: str
    label: str
    field_type: str  # "int", "float"
    default: Any
    required: bool = False


STRATEGY_PARAMS: dict[str, list[FieldDef]] = {
    "degradation_search": [
        FieldDef("initial_users", "Initial Users", "int", 10),
        FieldDef("step_multiplier", "Step Multiplier", "float", 1.5),
        FieldDef("step_size", "Step Size (linear)", "int", None),
        FieldDef("window_size", "Window Size", "int", 5),
        FieldDef("threshold_count", "Threshold Count", "int", 3),
    ],
    "break_point": [
        FieldDef("initial_users", "Initial Users", "int", 10),
        FieldDef("step_multiplier", "Step Multiplier", "float", 2.0),
        FieldDef("error_threshold", "Error Threshold (%)", "float", 10.0),
    ],
    "sla_validation": [
        FieldDef("max_p99", "Max P99 (ms)", "float", 5000, required=True),
        FieldDef("max_error_rate", "Max Error Rate (%)", "float", 10.0, required=True),
        FieldDef("initial_users", "Initial Users", "int", 10),
        FieldDef("step_multiplier", "Step Multiplier", "float", 1.5),
    ],
    "target_rps": [
        FieldDef("target_rps", "Target RPS", "float", 500, required=True),
        FieldDef("test_duration", "Test Duration (sec)", "int", 300),
        FieldDef("tolerance", "Tolerance", "float", 0.05),
    ],
    "spike": [
        FieldDef("baseline_users", "Baseline Users", "int", 50),
        FieldDef("baseline_duration", "Baseline Duration (sec)", "float", 30),
        FieldDef("spike_users", "Spike Users", "int", 500),
        FieldDef("spike_duration", "Spike Duration (sec)", "float", 60),
        FieldDef("recovery_users", "Recovery Users", "int", 50),
        FieldDef("recovery_duration", "Recovery Duration (sec)", "float", 30),
    ],
    "canary": [
        FieldDef("canary_users", "Canary Users", "int", 5),
        FieldDef("canary_duration", "Canary Duration (sec)", "int", 30),
        FieldDef("error_threshold", "Error Threshold (%)", "float", 1.0),
        FieldDef("percentile_threshold", "Percentile (p95) Threshold (ms)", "float", 5000),
    ],
}

STRATEGY_TYPES = list(STRATEGY_PARAMS.keys())
ADAPTER_TYPES = ["locust"]