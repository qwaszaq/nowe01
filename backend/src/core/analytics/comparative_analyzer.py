"""
Comparative Analysis Module
Period-over-period, entity, and scenario comparisons for BI dashboards
"""

import logging
import statistics
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ComparisonType(str, Enum):
    """Types of comparisons"""
    PERIOD_OVER_PERIOD = "period_over_period"    # Q1 2024 vs Q1 2023
    SEQUENTIAL_PERIOD = "sequential_period"       # Q2 vs Q1
    YEAR_OVER_YEAR = "year_over_year"           # 2024 vs 2023
    MONTH_OVER_MONTH = "month_over_month"       # March vs February
    QUARTER_OVER_QUARTER = "quarter_over_quarter"  # Q2 vs Q1
    ENTITY_COMPARISON = "entity_comparison"      # Company A vs Company B
    SCENARIO_COMPARISON = "scenario_comparison"  # Actual vs Budget
    BENCHMARK_COMPARISON = "benchmark_comparison"  # Company vs Industry


class PerformanceRating(str, Enum):
    """Performance rating in comparison"""
    SIGNIFICANTLY_BETTER = "significantly_better"   # +15% or more
    BETTER = "better"                               # +5% to +15%
    SLIGHTLY_BETTER = "slightly_better"             # +1% to +5%
    SIMILAR = "similar"                             # -1% to +1%
    SLIGHTLY_WORSE = "slightly_worse"               # -5% to -1%
    WORSE = "worse"                                 # -15% to -5%
    SIGNIFICANTLY_WORSE = "significantly_worse"     # -15% or less


class MetricComparison(BaseModel):
    """
    Comparison of a single metric between two entities/periods
    """
    metric_name: str
    metric_category: str = Field(default="general")

    # Entity A (baseline/previous)
    entity_a_label: str
    entity_a_value: float
    entity_a_formatted: str

    # Entity B (comparison/current)
    entity_b_label: str
    entity_b_value: float
    entity_b_formatted: str

    # Difference analysis
    absolute_difference: float
    percent_difference: float
    rating: PerformanceRating

    # Winner
    better_entity: Optional[str] = Field(None, description="Which entity performed better")
    is_higher_better: bool = Field(True, description="Whether higher values are better for this metric")

    # Insights
    interpretation: str = Field(..., description="What this comparison means")


class PeriodComparison(BaseModel):
    """
    Complete comparison between two periods
    """
    comparison_type: ComparisonType
    period_a: str = Field(..., description="Baseline period label")
    period_b: str = Field(..., description="Comparison period label")

    # Metric comparisons
    metrics: List[MetricComparison] = Field(default_factory=list)

    # Summary statistics
    total_metrics: int = 0
    improved_metrics: int = 0
    declined_metrics: int = 0
    stable_metrics: int = 0

    # Overall assessment
    overall_performance: PerformanceRating
    overall_summary: str
    key_improvements: List[str] = Field(default_factory=list)
    key_declines: List[str] = Field(default_factory=list)

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)


class VarianceAnalysis(BaseModel):
    """
    Variance analysis between actual and target/budget
    """
    metric_name: str

    actual_value: float
    target_value: float

    variance: float = Field(..., description="Actual - Target")
    variance_percent: float = Field(..., description="(Actual - Target) / Target * 100")

    # Categorization
    is_favorable: bool = Field(..., description="Whether variance is favorable")
    variance_type: str = Field(..., description="favorable/unfavorable")
    materiality: str = Field(..., description="immaterial/material/significant")

    # Insights
    explanation: str
    action_required: bool = Field(default=False)


class ComparisonResult(BaseModel):
    """
    Comprehensive comparison result with insights
    """
    comparison_id: str
    comparison_type: ComparisonType
    comparison_name: str

    # Entities being compared
    entity_a: Dict = Field(..., description="Baseline entity/period details")
    entity_b: Dict = Field(..., description="Comparison entity/period details")

    # Metric comparisons
    metric_comparisons: List[MetricComparison] = Field(default_factory=list)

    # Variance analysis (if applicable)
    variance_analyses: List[VarianceAnalysis] = Field(default_factory=list)

    # Summary
    summary: str
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Performance breakdown
    performance_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of metrics by performance rating"
    )

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)


class ComparativeAnalyzer:
    """
    Comparative Analysis Engine
    Performs sophisticated comparisons between periods, entities, or scenarios
    """

    def __init__(self):
        """Initialize comparative analyzer"""
        logger.info("ComparativeAnalyzer initialized")

    def compare_periods(
        self,
        period_a_label: str,
        period_a_metrics: Dict[str, float],
        period_b_label: str,
        period_b_metrics: Dict[str, float],
        comparison_type: ComparisonType = ComparisonType.PERIOD_OVER_PERIOD,
        metric_metadata: Optional[Dict[str, Dict]] = None
    ) -> PeriodComparison:
        """
        Compare metrics between two periods

        Args:
            period_a_label: Label for baseline period (e.g., "Q1 2023")
            period_a_metrics: Metrics for period A {metric_name: value}
            period_b_label: Label for comparison period (e.g., "Q1 2024")
            period_b_metrics: Metrics for period B
            comparison_type: Type of comparison being performed
            metric_metadata: Optional metadata about metrics (is_higher_better, category)

        Returns:
            PeriodComparison with detailed analysis
        """
        metric_metadata = metric_metadata or {}

        # Find common metrics
        common_metrics = set(period_a_metrics.keys()) & set(period_b_metrics.keys())

        if not common_metrics:
            return PeriodComparison(
                comparison_type=comparison_type,
                period_a=period_a_label,
                period_b=period_b_label,
                metrics=[],
                total_metrics=0,
                improved_metrics=0,
                declined_metrics=0,
                stable_metrics=0,
                overall_performance=PerformanceRating.SIMILAR,
                overall_summary="No common metrics found for comparison"
            )

        # Compare each metric
        metric_comparisons = []
        improved_count = 0
        declined_count = 0
        stable_count = 0

        for metric_name in common_metrics:
            value_a = period_a_metrics[metric_name]
            value_b = period_b_metrics[metric_name]

            metadata = metric_metadata.get(metric_name, {})
            is_higher_better = metadata.get('is_higher_better', True)
            category = metadata.get('category', 'general')
            unit = metadata.get('unit', 'ratio')

            comparison = self._compare_metric(
                metric_name=metric_name,
                category=category,
                value_a=value_a,
                value_b=value_b,
                entity_a_label=period_a_label,
                entity_b_label=period_b_label,
                is_higher_better=is_higher_better,
                unit=unit
            )

            metric_comparisons.append(comparison)

            # Count improvements/declines
            if comparison.rating in [PerformanceRating.BETTER, PerformanceRating.SIGNIFICANTLY_BETTER]:
                improved_count += 1
            elif comparison.rating in [PerformanceRating.WORSE, PerformanceRating.SIGNIFICANTLY_WORSE]:
                declined_count += 1
            else:
                stable_count += 1

        # Sort by percent difference (most improved first)
        metric_comparisons.sort(key=lambda m: m.percent_difference, reverse=True)

        # Determine overall performance
        overall_performance = self._calculate_overall_performance(
            improved_count, declined_count, stable_count, len(common_metrics)
        )

        # Extract key improvements and declines
        key_improvements = [
            f"{m.metric_name}: +{m.percent_difference:.1f}%"
            for m in metric_comparisons[:3]
            if m.percent_difference > 5
        ]

        key_declines = [
            f"{m.metric_name}: {m.percent_difference:.1f}%"
            for m in metric_comparisons[-3:]
            if m.percent_difference < -5
        ]

        # Generate summary
        overall_summary = self._generate_comparison_summary(
            period_a_label,
            period_b_label,
            overall_performance,
            improved_count,
            declined_count,
            len(common_metrics)
        )

        return PeriodComparison(
            comparison_type=comparison_type,
            period_a=period_a_label,
            period_b=period_b_label,
            metrics=metric_comparisons,
            total_metrics=len(metric_comparisons),
            improved_metrics=improved_count,
            declined_metrics=declined_count,
            stable_metrics=stable_count,
            overall_performance=overall_performance,
            overall_summary=overall_summary,
            key_improvements=key_improvements,
            key_declines=key_declines
        )

    def variance_analysis(
        self,
        metric_name: str,
        actual_value: float,
        target_value: float,
        is_higher_better: bool = True,
        materiality_threshold: float = 5.0
    ) -> VarianceAnalysis:
        """
        Perform variance analysis (Actual vs Target/Budget)

        Args:
            metric_name: Name of metric
            actual_value: Actual achieved value
            target_value: Target/budget value
            is_higher_better: Whether higher is better for this metric
            materiality_threshold: Threshold % for materiality (default: 5%)

        Returns:
            VarianceAnalysis with favorability assessment
        """
        variance = actual_value - target_value
        variance_percent = (variance / target_value * 100) if target_value != 0 else 0.0

        # Determine if variance is favorable
        if is_higher_better:
            is_favorable = variance > 0
        else:
            is_favorable = variance < 0

        variance_type = "favorable" if is_favorable else "unfavorable"

        # Determine materiality
        abs_variance_pct = abs(variance_percent)
        if abs_variance_pct < materiality_threshold:
            materiality = "immaterial"
        elif abs_variance_pct < materiality_threshold * 2:
            materiality = "material"
        else:
            materiality = "significant"

        # Generate explanation
        explanation = self._generate_variance_explanation(
            metric_name,
            variance_percent,
            is_favorable,
            materiality
        )

        # Determine if action required
        action_required = not is_favorable and materiality in ["material", "significant"]

        return VarianceAnalysis(
            metric_name=metric_name,
            actual_value=actual_value,
            target_value=target_value,
            variance=variance,
            variance_percent=variance_percent,
            is_favorable=is_favorable,
            variance_type=variance_type,
            materiality=materiality,
            explanation=explanation,
            action_required=action_required
        )

    def comprehensive_comparison(
        self,
        comparison_name: str,
        entity_a: Dict,
        entity_b: Dict,
        comparison_type: ComparisonType = ComparisonType.ENTITY_COMPARISON,
        include_variance: bool = False,
        targets: Optional[Dict[str, float]] = None
    ) -> ComparisonResult:
        """
        Perform comprehensive comparison with insights

        Args:
            comparison_name: Name of comparison
            entity_a: {name, metrics, metadata} for entity A
            entity_b: {name, metrics, metadata} for entity B
            comparison_type: Type of comparison
            include_variance: Whether to include variance analysis
            targets: Target values for variance analysis

        Returns:
            ComparisonResult with complete analysis
        """
        # Extract metrics
        metrics_a = entity_a.get('metrics', {})
        metrics_b = entity_b.get('metrics', {})

        # Perform period comparison
        period_comparison = self.compare_periods(
            period_a_label=entity_a['name'],
            period_a_metrics=metrics_a,
            period_b_label=entity_b['name'],
            period_b_metrics=metrics_b,
            comparison_type=comparison_type,
            metric_metadata=entity_a.get('metadata', {})
        )

        # Perform variance analysis if requested
        variance_analyses = []
        if include_variance and targets:
            for metric_name, target_value in targets.items():
                if metric_name in metrics_b:
                    actual_value = metrics_b[metric_name]
                    metadata = entity_a.get('metadata', {}).get(metric_name, {})
                    is_higher_better = metadata.get('is_higher_better', True)

                    variance = self.variance_analysis(
                        metric_name=metric_name,
                        actual_value=actual_value,
                        target_value=target_value,
                        is_higher_better=is_higher_better
                    )
                    variance_analyses.append(variance)

        # Count by performance rating
        performance_summary = {}
        for metric in period_comparison.metrics:
            rating = metric.rating.value
            performance_summary[rating] = performance_summary.get(rating, 0) + 1

        # Generate insights
        insights = self._generate_comparison_insights(period_comparison, variance_analyses)

        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(
            period_comparison, variance_analyses
        )

        return ComparisonResult(
            comparison_id=f"{comparison_type.value}_{entity_a['name']}_{entity_b['name']}",
            comparison_type=comparison_type,
            comparison_name=comparison_name,
            entity_a=entity_a,
            entity_b=entity_b,
            metric_comparisons=period_comparison.metrics,
            variance_analyses=variance_analyses,
            summary=period_comparison.overall_summary,
            insights=insights,
            recommendations=recommendations,
            performance_summary=performance_summary
        )

    # ============================================
    # PRIVATE HELPER METHODS
    # ============================================

    def _compare_metric(
        self,
        metric_name: str,
        category: str,
        value_a: float,
        value_b: float,
        entity_a_label: str,
        entity_b_label: str,
        is_higher_better: bool,
        unit: str
    ) -> MetricComparison:
        """Compare a single metric between two entities"""

        # Format values
        if unit == "%":
            formatted_a = f"{value_a:.2f}%"
            formatted_b = f"{value_b:.2f}%"
        elif unit == "times":
            formatted_a = f"{value_a:.2f}×"
            formatted_b = f"{value_b:.2f}×"
        else:
            formatted_a = f"{value_a:.2f}"
            formatted_b = f"{value_b:.2f}"

        # Calculate differences
        absolute_diff = value_b - value_a
        percent_diff = ((value_b - value_a) / value_a * 100) if value_a != 0 else 0.0

        # Determine rating
        rating = self._rate_performance(percent_diff, is_higher_better)

        # Determine better entity
        if rating in [PerformanceRating.SIGNIFICANTLY_BETTER, PerformanceRating.BETTER, PerformanceRating.SLIGHTLY_BETTER]:
            better_entity = entity_b_label
        elif rating in [PerformanceRating.SIGNIFICANTLY_WORSE, PerformanceRating.WORSE, PerformanceRating.SLIGHTLY_WORSE]:
            better_entity = entity_a_label
        else:
            better_entity = None

        # Generate interpretation
        interpretation = self._interpret_metric_comparison(
            metric_name, entity_a_label, entity_b_label, percent_diff, rating, is_higher_better
        )

        return MetricComparison(
            metric_name=metric_name,
            metric_category=category,
            entity_a_label=entity_a_label,
            entity_a_value=value_a,
            entity_a_formatted=formatted_a,
            entity_b_label=entity_b_label,
            entity_b_value=value_b,
            entity_b_formatted=formatted_b,
            absolute_difference=absolute_diff,
            percent_difference=percent_diff,
            rating=rating,
            better_entity=better_entity,
            is_higher_better=is_higher_better,
            interpretation=interpretation
        )

    def _rate_performance(self, percent_change: float, is_higher_better: bool) -> PerformanceRating:
        """Rate performance based on percent change"""
        # Adjust direction if lower is better
        effective_change = percent_change if is_higher_better else -percent_change

        if effective_change >= 15:
            return PerformanceRating.SIGNIFICANTLY_BETTER
        elif effective_change >= 5:
            return PerformanceRating.BETTER
        elif effective_change >= 1:
            return PerformanceRating.SLIGHTLY_BETTER
        elif effective_change >= -1:
            return PerformanceRating.SIMILAR
        elif effective_change >= -5:
            return PerformanceRating.SLIGHTLY_WORSE
        elif effective_change >= -15:
            return PerformanceRating.WORSE
        else:
            return PerformanceRating.SIGNIFICANTLY_WORSE

    def _calculate_overall_performance(
        self,
        improved: int,
        declined: int,
        stable: int,
        total: int
    ) -> PerformanceRating:
        """Calculate overall performance rating"""
        if total == 0:
            return PerformanceRating.SIMILAR

        improved_pct = (improved / total) * 100
        declined_pct = (declined / total) * 100

        net_improvement = improved_pct - declined_pct

        if net_improvement >= 40:
            return PerformanceRating.SIGNIFICANTLY_BETTER
        elif net_improvement >= 20:
            return PerformanceRating.BETTER
        elif net_improvement >= 10:
            return PerformanceRating.SLIGHTLY_BETTER
        elif net_improvement >= -10:
            return PerformanceRating.SIMILAR
        elif net_improvement >= -20:
            return PerformanceRating.SLIGHTLY_WORSE
        elif net_improvement >= -40:
            return PerformanceRating.WORSE
        else:
            return PerformanceRating.SIGNIFICANTLY_WORSE

    def _interpret_metric_comparison(
        self,
        metric_name: str,
        entity_a: str,
        entity_b: str,
        percent_diff: float,
        rating: PerformanceRating,
        is_higher_better: bool
    ) -> str:
        """Generate human-readable interpretation"""
        direction = "increased" if percent_diff > 0 else "decreased"
        abs_diff = abs(percent_diff)

        if rating == PerformanceRating.SIMILAR:
            return f"{metric_name} remained stable between {entity_a} and {entity_b} (±{abs_diff:.1f}%)"

        good_bad = ""
        if rating in [PerformanceRating.SIGNIFICANTLY_BETTER, PerformanceRating.BETTER, PerformanceRating.SLIGHTLY_BETTER]:
            good_bad = "positive improvement"
        else:
            good_bad = "concerning decline"

        return f"{metric_name} {direction} by {abs_diff:.1f}% from {entity_a} to {entity_b} - {good_bad}"

    def _generate_comparison_summary(
        self,
        period_a: str,
        period_b: str,
        overall_performance: PerformanceRating,
        improved: int,
        declined: int,
        total: int
    ) -> str:
        """Generate overall comparison summary"""
        if overall_performance == PerformanceRating.SIGNIFICANTLY_BETTER:
            return (
                f"Strong performance improvement from {period_a} to {period_b}: "
                f"{improved}/{total} metrics improved, {declined} declined"
            )
        elif overall_performance in [PerformanceRating.BETTER, PerformanceRating.SLIGHTLY_BETTER]:
            return (
                f"Performance improved from {period_a} to {period_b}: "
                f"{improved}/{total} metrics improved, {declined} declined"
            )
        elif overall_performance == PerformanceRating.SIMILAR:
            return (
                f"Stable performance from {period_a} to {period_b}: "
                f"{improved} improved, {declined} declined"
            )
        else:
            return (
                f"Performance declined from {period_a} to {period_b}: "
                f"{declined}/{total} metrics worse, {improved} improved"
            )

    def _generate_variance_explanation(
        self,
        metric_name: str,
        variance_percent: float,
        is_favorable: bool,
        materiality: str
    ) -> str:
        """Generate variance explanation"""
        abs_var = abs(variance_percent)
        direction = "above" if variance_percent > 0 else "below"

        if materiality == "immaterial":
            return f"{metric_name} is {abs_var:.1f}% {direction} target - within acceptable range"
        elif materiality == "material":
            status = "favorable" if is_favorable else "unfavorable"
            return f"{metric_name} shows {status} variance of {abs_var:.1f}% {direction} target"
        else:  # significant
            status = "favorable" if is_favorable else "concerning"
            return f"⚠️ {metric_name} shows {status} significant variance of {abs_var:.1f}% {direction} target"

    def _generate_comparison_insights(
        self,
        period_comparison: PeriodComparison,
        variance_analyses: List[VarianceAnalysis]
    ) -> List[str]:
        """Generate insights from comparison"""
        insights = []

        # Insight from improvements
        if period_comparison.key_improvements:
            insights.append(
                f"✅ Top improvements: {', '.join(period_comparison.key_improvements[:2])}"
            )

        # Insight from declines
        if period_comparison.key_declines:
            insights.append(
                f"⚠️ Areas of concern: {', '.join(period_comparison.key_declines[:2])}"
            )

        # Variance insights
        unfavorable_variances = [v for v in variance_analyses if not v.is_favorable and v.materiality == "significant"]
        if unfavorable_variances:
            insights.append(
                f"🚨 {len(unfavorable_variances)} metrics show significant unfavorable variance from target"
            )

        return insights

    def _generate_comparison_recommendations(
        self,
        period_comparison: PeriodComparison,
        variance_analyses: List[VarianceAnalysis]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Recommendations based on declines
        if period_comparison.declined_metrics > period_comparison.total_metrics * 0.3:
            recommendations.append(
                "🔍 Investigate root causes of widespread metric declines"
            )

        # Recommendations from variance
        action_required_metrics = [v.metric_name for v in variance_analyses if v.action_required]
        if action_required_metrics:
            recommendations.append(
                f"⚡ Priority action required for: {', '.join(action_required_metrics[:3])}"
            )

        # Positive recommendation
        if period_comparison.overall_performance in [PerformanceRating.BETTER, PerformanceRating.SIGNIFICANTLY_BETTER]:
            recommendations.append(
                "📈 Capitalize on positive momentum and identify success factors"
            )

        return recommendations
