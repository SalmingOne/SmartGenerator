from src.load_orchestrator.models import RawMetrics
from dataclasses import dataclass


@dataclass
class ReferenceMetrics:
    """
    Эталонные и критические значения метрик для нормализации Locust-SDI

    Берутся экспериментально из первых минут теста или из SLA.
    """
    # Эталонные значения (при малой нагрузке)
    rt_avg_ref: float = 50.0
    rt_95_ref: float = 100.0
    rt_99_ref: float = 150.0
    error_rate_ref: float = 0.0
    rps_ref: float = 1000.0

    # Критические значения (SLA или наблюдаемые)
    rt_avg_crit: float = 500.0
    rt_95_crit: float = 1000.0
    rt_99_crit: float = 2000.0
    error_rate_crit: float = 5.0
    rps_crit: float = 100.0


@dataclass
class DegradationComponents:
    """Компоненты деградации для метрики"""
    amplitude: float  # D^(A) - амплитудная деградация [0..1]
    trend: float      # D^(T) - трендовая деградация [0..1]
    spike: float      # D^(S) - нестабильность [0..1]


class MetricsCalculator:
    """Утилиты для расчёта производных метрик из RawMetrics"""

    @staticmethod
    def calculate_stability(metrics: RawMetrics) -> float:
        """
        Коэффициент стабильности P99/P50

        Источник: Aerospike, OneUptime — если > 3, система нестабильна

        Args:
            metrics: Сырые метрики

        Returns:
            Коэффициент стабильности (чем ближе к 1, тем стабильнее)
            float("inf") если p50 == 0
        """
        if metrics.p50 == 0:
            return float("inf")
        return metrics.p99 / metrics.p50

    @staticmethod
    def calculate_scaling_efficiency(
        prev_metrics: RawMetrics,
        curr_metrics: RawMetrics
    ) -> float:
        """
        Эффективность масштабирования: (rps₂ - rps₁) / (users₂ - users₁)

        Источник: HPC Wiki — эффективность масштабирования

        Args:
            prev_metrics: Предыдущие метрики
            curr_metrics: Текущие метрики

        Returns:
            Эффективность масштабирования (сколько RPS добавляется на каждого пользователя)
            0.0 если delta_users == 0
        """
        delta_users = curr_metrics.users - prev_metrics.users
        if delta_users == 0:
            return 0.0

        delta_rps = curr_metrics.rps - prev_metrics.rps
        return delta_rps / delta_users

    @staticmethod
    def _calculate_degradation_index(
        metrics: RawMetrics,
        stability: float | None = None,
        scaling_efficiency: float | None = None
    ) -> float:
        """
        Комплексный индекс деградации (0 — норм, 1 — плохо)

        Взвешенная комбинация факторов:
        - Стабильность (stability): P99/P50
        - Эффективность масштабирования (scaling_efficiency)
        - Уровень ошибок (error_rate)

        Args:
            metrics: Сырые метрики
            stability: Предрассчитанный коэффициент стабильности (опционально)
            scaling_efficiency: Предрассчитанная эффективность масштабирования (опционально)

        Returns:
            Индекс от 0 (отлично) до 1 (деградация)
        """
        # Рассчитать stability если не передан
        if stability is None:
            stability = MetricsCalculator.calculate_stability(metrics)

        # Нормализация stability (3 - порог нестабильности)
        stability_score = min(stability / 3.0, 1.0) if stability != float("inf") else 1.0

        # Нормализация scaling_efficiency (считаем что < 0.5 это плохо)
        if scaling_efficiency is not None:
            efficiency_score = 1.0 - min(scaling_efficiency / 1.0, 1.0) if scaling_efficiency > 0 else 1.0
        else:
            efficiency_score = 0  # нейтральное значение если нет данных

        # Нормализация error_rate (> 5% критично)
        error_score = min(metrics.error_rate / 5.0, 1.0)

        # Взвешенная комбинация
        weights = {
            'stability': 0.5,
            'efficiency': 0.3,
            'errors': 0.2
        }

        degradation_index = (
            stability_score * weights['stability'] +
            efficiency_score * weights['efficiency'] +
            error_score * weights['errors']
        )

        print(f"""
        stability: {stability_score}
        efficiency: {efficiency_score}
        errors: {error_score}
        """)

        return min(degradation_index, 1.0)

    @staticmethod
    def calculate_degradation_index(
        curr_metrics: RawMetrics,
        prev_metrics: RawMetrics | None = None
    ) -> float:
        """
        Рассчитать все производные метрики за один раз

        Args:
            curr_metrics: Текущие метрики
            prev_metrics: Предыдущие метрики (для расчёта scaling_efficiency)

        Returns:
            Словарь с рассчитанными метриками:
            {
                'stability': float,
                'scaling_efficiency': float,
                'degradation_index': float
            }
        """
        stability = MetricsCalculator.calculate_stability(curr_metrics)

        scaling_efficiency = None
        if prev_metrics is not None:
            scaling_efficiency = MetricsCalculator.calculate_scaling_efficiency(
                prev_metrics, curr_metrics
            )

        degradation_index = MetricsCalculator._calculate_degradation_index(
            curr_metrics, stability, scaling_efficiency
        )

        return degradation_index

    # ========================================================================
    # Locust-SDI: Индекс деградации системы по метрикам Locust
    # ========================================================================

    @staticmethod
    def normalize_metric_growth(value, ref_value, crit_value):
        if crit_value == ref_value:
            return 0.0
        x = (value - ref_value) / (crit_value - ref_value)
        return max(0.0, min(1.0, x))

    @staticmethod
    def normalize_metric_drop(value, ref_value, crit_value):
        if ref_value == crit_value:
            return 0.0
        x = (ref_value - value) / (ref_value - crit_value)
        return max(0.0, min(1.0, x))

    @staticmethod
    def calculate_amplitude_degradation(curr, ref):
        return {
            'rt_avg': MetricsCalculator.normalize_metric_growth(
                curr.rt_avg, ref.rt_avg_ref, ref.rt_avg_crit
            ),
            'rt_95': MetricsCalculator.normalize_metric_growth(
                curr.p95, ref.rt_95_ref, ref.rt_95_crit
            ),
            'rt_99': MetricsCalculator.normalize_metric_growth(
                curr.p99, ref.rt_99_ref, ref.rt_99_crit
            ),
            'error_rate': MetricsCalculator.normalize_metric_growth(
                curr.error_rate, ref.error_rate_ref, ref.error_rate_crit
            ),
            'rps': MetricsCalculator.normalize_metric_drop(
                curr.rps, ref.rps_ref, ref.rps_crit
            ),
        }

    @staticmethod
    def calculate_trend_degradation(curr, prev, ref, delta_t=1.0):
        if prev is None:
            return {k: 0.0 for k in ['rt_avg', 'rt_95', 'rt_99', 'error_rate', 'rps']}

        def norm(delta, ref_val, crit_val):
            if crit_val == ref_val:
                return 0.0
            x = delta / (crit_val - ref_val)
            return max(0.0, min(1.0, x))

        return {
            'rt_avg': norm(curr.rt_avg - prev.rt_avg,
                           ref.rt_avg_ref, ref.rt_avg_crit),

            'rt_95': norm(curr.p95 - prev.p95,
                          ref.rt_95_ref, ref.rt_95_crit),

            'rt_99': norm(curr.p99 - prev.p99,
                          ref.rt_99_ref, ref.rt_99_crit),

            'error_rate': norm(curr.error_rate - prev.error_rate,
                               ref.error_rate_ref, ref.error_rate_crit),

            # инверсия для RPS
            'rps': norm(prev.rps - curr.rps,
                        ref.rps_crit, ref.rps_ref),
        }

    @staticmethod
    def calculate_spike_degradation(curr, history, window_size=10):
        if len(history) < window_size:
            return {k: 0.0 for k in ['rt_avg', 'rt_95', 'rt_99', 'error_rate', 'rps']}

        eps = 1e-6
        window = history[-window_size:]

        # spike = abs(curr - mean) / (std + eps)
        # spike = min(1.0, spike)

        def spike(curr_val, values):
            mean = sum(values) / len(values)
            var = sum((v - mean) ** 2 for v in values) / len(values)
            std = var ** 0.5
            return min(1.0, abs(curr_val - mean) / (std + eps))

        return {
            'rt_avg': spike(curr.rt_avg, [m.rt_avg for m in window]),
            'rt_95': spike(curr.p95, [m.p95 for m in window]),
            'rt_99': spike(curr.p99, [m.p99 for m in window]),
            'error_rate': spike(curr.error_rate, [m.error_rate for m in window]),
            'rps': spike(curr.rps, [m.rps for m in window]),
        }

    @staticmethod
    def calculate_locust_sdi(
            curr, prev, history, ref,
            alpha=0.4, beta=0.3, gamma=0.3
    ):
        amplitude = MetricsCalculator.calculate_amplitude_degradation(curr, ref)
        print("Amplitude degradation:", amplitude)
        trend = MetricsCalculator.calculate_trend_degradation(curr, prev, ref)
        print("Trend degradation:", trend)
        spike = MetricsCalculator.calculate_spike_degradation(curr, history)
        print("Spike degradation:", spike)

        weights = {
            'rt_95': 0.30,
            'rt_99': 0.25,
            'error_rate': 0.25,
            'rps': 0.15,
            'rt_avg': 0.05,
        }

        sdi = 0.0
        for key, w in weights.items():
            d = alpha * amplitude[key] + beta * trend[key] + gamma * spike[key]
            sdi += w * min(1.0, d)

        return min(1.0, max(0.0, sdi))


if __name__ == '__main__':
    MetricsCalculator.calculate_locust_sdi(ref=ReferenceMetrics(), curr=RawMetrics(0,0,0,0,0,0,0,0,0), )