import math

from ..models import RawMetrics
from dataclasses import dataclass



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
        stability_score = min(stability / 8.0, 1.0) if stability != float("inf") else 1.0

        # Нормализация scaling_efficiency (считаем что < 0.5 это плохо)
        if scaling_efficiency is not None:
            efficiency_score = 1.0 - min(scaling_efficiency / 1.0, 1.0) if scaling_efficiency > 0 else 1.0
        else:
            efficiency_score = 0  # нейтральное значение если нет данных

        # Нормализация error_rate (> 5% критично)
        error_score = min(metrics.error_rate / 15.0, 1.0)

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