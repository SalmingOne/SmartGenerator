from src.load_orchestrator.models import RawMetrics, AnalyzedMetrics


class Analyzer:
    """Анализатор метрик для определения деградации системы"""

    def __init__(self, window_size: int):
        self.window_size = window_size
        self.history: list[RawMetrics] = []

    def analyze(self, raw_metrics: RawMetrics) -> AnalyzedMetrics:
        """
        Проанализировать метрики и вернуть AnalyzedMetrics

        Args:
            raw_metrics: Сырые метрики от генератора нагрузки

        Returns:
            AnalyzedMetrics с рассчитанными производными метриками
        """
        # Добавить в историю
        self.history.append(raw_metrics)

        # Ограничить размер истории
        if len(self.history) > self.window_size:
            self.history = self.history[-self.window_size:]

        # Рассчитать метрики
        stability = self._calculate_stability(raw_metrics)
        scaling_efficiency = self._calculate_scaling_efficiency()
        degradation_index = self._calculate_degradation_index(stability, scaling_efficiency, raw_metrics)

        return AnalyzedMetrics(
            raw=raw_metrics,
            stability=stability,
            scaling_efficiency=scaling_efficiency,
            degradation_index=degradation_index
        )

    def _calculate_stability(self, raw_metrics: RawMetrics) -> float:
        """
        Коэффициент стабильности P99/P50

        Источник: Aerospike, OneUptime — если > 3, система нестабильна

        Args:
            raw_metrics: Сырые метрики

        Returns:
            Коэффициент стабильности (чем ближе к 1, тем стабильнее)
        """
        if raw_metrics.p50 == 0:
            return float("inf")  # нет данных
        return raw_metrics.p99 / raw_metrics.p50

    def _calculate_scaling_efficiency(self) -> float:
        """
        Эффективность масштабирования: (rps₂ - rps₁) / (users₂ - users₁)

        Источник: HPC Wiki — эффективность масштабирования

        Returns:
            Эффективность масштабирования (сколько RPS добавляется на каждого пользователя)
        """
        if len(self.history) < 2:
            return 0.0

        prev = self.history[-2]
        curr = self.history[-1]

        delta_users = curr.users - prev.users
        if delta_users == 0:
            return 0.0

        delta_rps = curr.rps - prev.rps
        return delta_rps / delta_users

    def _calculate_degradation_index(
        self,
        stability: float,
        scaling_efficiency: float,
        raw_metrics: RawMetrics
    ) -> float:
        """
        Комплексный индекс деградации (0 — норм, 1 — плохо)

        Взвешенная комбинация факторов:
        - Стабильность (stability)
        - Эффективность масштабирования (scaling_efficiency)
        - Уровень ошибок (error_rate)

        Returns:
            Индекс от 0 (отлично) до 1 (деградация)
        """
        # Нормализация stability (3 - порог нестабильности)
        stability_score = min(stability / 3.0, 1.0) if stability != float("inf") else 1.0

        # Нормализация scaling_efficiency (считаем что < 0.5 это плохо)
        efficiency_score = 1.0 - min(scaling_efficiency / 1.0, 1.0) if scaling_efficiency > 0 else 1.0

        # Нормализация error_rate (> 5% критично)
        error_score = min(raw_metrics.error_rate / 5.0, 1.0)

        # Взвешенная комбинация
        weights = {
            'stability': 0.4,
            'efficiency': 0.4,
            'errors': 0.2
        }

        degradation_index = (
            stability_score * weights['stability'] +
            efficiency_score * weights['efficiency'] +
            error_score * weights['errors']
        )

        return min(degradation_index, 1.0)

    def reset(self) -> None:
        """Сбросить историю для нового теста"""
        self.history.clear()

