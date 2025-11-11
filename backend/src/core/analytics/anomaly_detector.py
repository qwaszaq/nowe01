"""
Anomaly Detection System
Advanced anomaly detection for financial metrics using multiple methods
"""

import logging
import statistics
import math
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies"""
    SPIKE = "spike"                    # Sudden increase
    DROP = "drop"                      # Sudden decrease
    OUTLIER = "outlier"                # Statistical outlier
    PATTERN_BREAK = "pattern_break"    # Break in established pattern
    DRIFT = "drift"                    # Gradual drift from baseline
    VOLATILITY_SHIFT = "volatility_shift"  # Change in variance
    MISSING_DATA = "missing_data"      # Data gaps
    ZERO_VALUE = "zero_value"          # Unexpected zero


class AnomalySeverity(str, Enum):
    """Severity classification"""
    CRITICAL = "critical"   # >3 std deviations
    HIGH = "high"           # 2-3 std deviations
    MEDIUM = "medium"       # 1.5-2 std deviations
    LOW = "low"             # 1-1.5 std deviations


class Anomaly(BaseModel):
    """
    Detected anomaly with context
    """
    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    metric_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity

    # Anomaly details
    timestamp: datetime
    period_label: str
    value: float
    expected_value: float = Field(..., description="Expected value based on pattern")
    deviation: float = Field(..., description="Absolute deviation from expected")
    deviation_percent: float = Field(..., description="Percentage deviation")

    # Statistical context
    z_score: float = Field(..., description="Z-score (standard deviations from mean)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")

    # Business impact
    impact_description: str
    requires_investigation: bool = Field(default=False)

    # Metadata
    detection_method: str = Field(default="statistical", description="Method used to detect")
    detected_at: datetime = Field(default_factory=datetime.now)

    # Related anomalies
    related_anomalies: List[str] = Field(default_factory=list, description="Related anomaly IDs")


class AnomalyReport(BaseModel):
    """
    Comprehensive anomaly detection report
    """
    metric_name: str
    analysis_period: str
    total_periods: int

    # Anomalies found
    anomalies: List[Anomaly] = Field(default_factory=list)
    total_anomalies: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Analysis summary
    baseline_mean: float
    baseline_std: float
    anomaly_rate: float = Field(..., description="% of periods with anomalies")

    # Insights
    patterns_detected: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)


class AnomalyDetector:
    """
    Advanced Anomaly Detection Engine
    Detects unusual patterns in financial metrics using multiple statistical methods
    """

    def __init__(
        self,
        z_threshold: float = 2.0,
        iqr_multiplier: float = 1.5,
        min_baseline_periods: int = 5
    ):
        """
        Initialize anomaly detector

        Args:
            z_threshold: Z-score threshold for anomaly detection (default: 2.0)
            iqr_multiplier: IQR multiplier for outlier detection (default: 1.5)
            min_baseline_periods: Minimum periods needed for baseline calculation
        """
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        self.min_baseline_periods = min_baseline_periods

        logger.info(
            f"AnomalyDetector initialized (z_threshold={z_threshold}, "
            f"iqr_multiplier={iqr_multiplier})"
        )

    def detect_anomalies(
        self,
        metric_name: str,
        data_points: List[Dict],
        analysis_period: str = "Recent"
    ) -> AnomalyReport:
        """
        Detect all anomalies in time-series data

        Args:
            metric_name: Name of metric being analyzed
            data_points: List of {timestamp, value, period_label} dicts
            analysis_period: Human-readable period description

        Returns:
            AnomalyReport with all detected anomalies
        """
        if len(data_points) < self.min_baseline_periods:
            return AnomalyReport(
                metric_name=metric_name,
                analysis_period=analysis_period,
                total_periods=len(data_points),
                anomalies=[],
                total_anomalies=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                baseline_mean=0.0,
                baseline_std=0.0,
                anomaly_rate=0.0,
                patterns_detected=[],
                recommendations=["Insufficient data for anomaly detection"]
            )

        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda p: p['timestamp'])
        values = [p['value'] for p in sorted_points]

        # Calculate baseline statistics
        baseline_mean = statistics.mean(values)
        baseline_std = statistics.stdev(values) if len(values) > 1 else 0.0

        # Detect anomalies using multiple methods
        anomalies = []

        # Method 1: Statistical outliers (Z-score)
        statistical_anomalies = self._detect_statistical_outliers(
            metric_name, sorted_points, values, baseline_mean, baseline_std
        )
        anomalies.extend(statistical_anomalies)

        # Method 2: IQR outliers
        iqr_anomalies = self._detect_iqr_outliers(
            metric_name, sorted_points, values
        )
        # Merge with statistical, avoid duplicates
        for anomaly in iqr_anomalies:
            if anomaly.period_label not in [a.period_label for a in anomalies]:
                anomalies.append(anomaly)

        # Method 3: Spikes and drops
        spike_drop_anomalies = self._detect_spikes_and_drops(
            metric_name, sorted_points, values
        )
        for anomaly in spike_drop_anomalies:
            if anomaly.period_label not in [a.period_label for a in anomalies]:
                anomalies.append(anomaly)

        # Method 4: Pattern breaks
        pattern_anomalies = self._detect_pattern_breaks(
            metric_name, sorted_points, values
        )
        for anomaly in pattern_anomalies:
            if anomaly.period_label not in [a.period_label for a in anomalies]:
                anomalies.append(anomaly)

        # Method 5: Zero values (if unexpected)
        zero_anomalies = self._detect_zero_values(
            metric_name, sorted_points
        )
        for anomaly in zero_anomalies:
            if anomaly.period_label not in [a.period_label for a in anomalies]:
                anomalies.append(anomaly)

        # Count by severity
        severity_counts = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 0,
            AnomalySeverity.MEDIUM: 0,
            AnomalySeverity.LOW: 0
        }
        for anomaly in anomalies:
            severity_counts[anomaly.severity] += 1

        # Calculate anomaly rate
        anomaly_rate = (len(anomalies) / len(data_points)) * 100 if data_points else 0.0

        # Detect patterns
        patterns = self._detect_patterns(anomalies, values)

        # Generate recommendations
        recommendations = self._generate_recommendations(anomalies, anomaly_rate, patterns)

        return AnomalyReport(
            metric_name=metric_name,
            analysis_period=analysis_period,
            total_periods=len(data_points),
            anomalies=anomalies,
            total_anomalies=len(anomalies),
            critical_count=severity_counts[AnomalySeverity.CRITICAL],
            high_count=severity_counts[AnomalySeverity.HIGH],
            medium_count=severity_counts[AnomalySeverity.MEDIUM],
            low_count=severity_counts[AnomalySeverity.LOW],
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
            anomaly_rate=anomaly_rate,
            patterns_detected=patterns,
            recommendations=recommendations
        )

    # ============================================
    # DETECTION METHODS
    # ============================================

    def _detect_statistical_outliers(
        self,
        metric_name: str,
        sorted_points: List[Dict],
        values: List[float],
        mean: float,
        std: float
    ) -> List[Anomaly]:
        """Detect outliers using Z-score method"""
        if std == 0:
            return []

        anomalies = []

        for point, value in zip(sorted_points, values):
            z_score = (value - mean) / std

            if abs(z_score) > self.z_threshold:
                # Determine severity
                if abs(z_score) > 3.0:
                    severity = AnomalySeverity.CRITICAL
                elif abs(z_score) > 2.5:
                    severity = AnomalySeverity.HIGH
                elif abs(z_score) > 2.0:
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW

                deviation = value - mean
                deviation_percent = (deviation / mean * 100) if mean != 0 else 0.0

                anomaly = Anomaly(
                    anomaly_id=f"{metric_name}_{point['period_label']}_outlier",
                    metric_name=metric_name,
                    anomaly_type=AnomalyType.OUTLIER,
                    severity=severity,
                    timestamp=point['timestamp'],
                    period_label=point['period_label'],
                    value=value,
                    expected_value=mean,
                    deviation=deviation,
                    deviation_percent=deviation_percent,
                    z_score=z_score,
                    confidence=min(abs(z_score) / 4.0, 1.0),
                    impact_description=f"{abs(deviation_percent):.1f}% deviation from baseline",
                    requires_investigation=severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH],
                    detection_method="z-score"
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_iqr_outliers(
        self,
        metric_name: str,
        sorted_points: List[Dict],
        values: List[float]
    ) -> List[Anomaly]:
        """Detect outliers using Interquartile Range method"""
        if len(values) < 4:
            return []

        sorted_values = sorted(values)
        q1 = sorted_values[len(values) // 4]
        q3 = sorted_values[3 * len(values) // 4]
        iqr = q3 - q1

        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr

        median = statistics.median(values)

        anomalies = []

        for point, value in zip(sorted_points, values):
            if value < lower_bound or value > upper_bound:
                z_score = (value - median) / (iqr / 1.35) if iqr != 0 else 0.0  # Approximate z-score

                severity = AnomalySeverity.HIGH if abs(z_score) > 3 else AnomalySeverity.MEDIUM

                anomaly = Anomaly(
                    anomaly_id=f"{metric_name}_{point['period_label']}_iqr_outlier",
                    metric_name=metric_name,
                    anomaly_type=AnomalyType.OUTLIER,
                    severity=severity,
                    timestamp=point['timestamp'],
                    period_label=point['period_label'],
                    value=value,
                    expected_value=median,
                    deviation=value - median,
                    deviation_percent=((value - median) / median * 100) if median != 0 else 0.0,
                    z_score=z_score,
                    confidence=0.85,
                    impact_description=f"Outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                    requires_investigation=severity == AnomalySeverity.HIGH,
                    detection_method="iqr"
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_spikes_and_drops(
        self,
        metric_name: str,
        sorted_points: List[Dict],
        values: List[float]
    ) -> List[Anomaly]:
        """Detect sudden spikes or drops between consecutive periods"""
        if len(values) < 2:
            return []

        anomalies = []
        spike_threshold = 0.30  # 30% change

        for i in range(1, len(values)):
            prev_value = values[i - 1]
            curr_value = values[i]

            if prev_value == 0:
                continue

            change_percent = ((curr_value - prev_value) / prev_value) * 100

            if abs(change_percent) > spike_threshold * 100:
                anomaly_type = AnomalyType.SPIKE if change_percent > 0 else AnomalyType.DROP

                if abs(change_percent) > 50:
                    severity = AnomalySeverity.CRITICAL
                elif abs(change_percent) > 40:
                    severity = AnomalySeverity.HIGH
                elif abs(change_percent) > 30:
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW

                anomaly = Anomaly(
                    anomaly_id=f"{metric_name}_{sorted_points[i]['period_label']}_{anomaly_type.value}",
                    metric_name=metric_name,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    timestamp=sorted_points[i]['timestamp'],
                    period_label=sorted_points[i]['period_label'],
                    value=curr_value,
                    expected_value=prev_value,
                    deviation=curr_value - prev_value,
                    deviation_percent=change_percent,
                    z_score=0.0,  # Not applicable for this method
                    confidence=0.9,
                    impact_description=f"Sudden {anomaly_type.value} of {abs(change_percent):.1f}% from previous period",
                    requires_investigation=severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH],
                    detection_method="period_comparison"
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_pattern_breaks(
        self,
        metric_name: str,
        sorted_points: List[Dict],
        values: List[float]
    ) -> List[Anomaly]:
        """Detect breaks in established patterns (e.g., trend reversals)"""
        if len(values) < 6:
            return []

        anomalies = []

        # Look for trend reversals using moving windows
        window_size = min(3, len(values) // 3)

        for i in range(window_size, len(values) - window_size):
            # Calculate trend before and after
            before_values = values[i - window_size:i]
            after_values = values[i:i + window_size]

            before_trend = statistics.mean(after_values) - statistics.mean(before_values) if before_values else 0
            after_mean = statistics.mean(after_values)
            before_mean = statistics.mean(before_values)

            # Check for significant trend reversal
            if before_mean != 0:
                trend_change = ((after_mean - before_mean) / before_mean) * 100

                if abs(trend_change) > 25:  # 25% trend change
                    anomaly = Anomaly(
                        anomaly_id=f"{metric_name}_{sorted_points[i]['period_label']}_pattern_break",
                        metric_name=metric_name,
                        anomaly_type=AnomalyType.PATTERN_BREAK,
                        severity=AnomalySeverity.MEDIUM,
                        timestamp=sorted_points[i]['timestamp'],
                        period_label=sorted_points[i]['period_label'],
                        value=values[i],
                        expected_value=before_mean,
                        deviation=after_mean - before_mean,
                        deviation_percent=trend_change,
                        z_score=0.0,
                        confidence=0.75,
                        impact_description=f"Pattern break detected: {abs(trend_change):.1f}% trend reversal",
                        requires_investigation=abs(trend_change) > 40,
                        detection_method="pattern_analysis"
                    )
                    anomalies.append(anomaly)

        return anomalies

    def _detect_zero_values(
        self,
        metric_name: str,
        sorted_points: List[Dict]
    ) -> List[Anomaly]:
        """Detect unexpected zero values"""
        anomalies = []

        for point in sorted_points:
            if point['value'] == 0.0:
                # Zero might be legitimate for some metrics, so mark as low severity
                anomaly = Anomaly(
                    anomaly_id=f"{metric_name}_{point['period_label']}_zero",
                    metric_name=metric_name,
                    anomaly_type=AnomalyType.ZERO_VALUE,
                    severity=AnomalySeverity.LOW,
                    timestamp=point['timestamp'],
                    period_label=point['period_label'],
                    value=0.0,
                    expected_value=0.0,  # Unknown
                    deviation=0.0,
                    deviation_percent=0.0,
                    z_score=0.0,
                    confidence=0.6,
                    impact_description="Zero value detected - verify if expected",
                    requires_investigation=True,  # Always worth checking
                    detection_method="zero_detection"
                )
                anomalies.append(anomaly)

        return anomalies

    # ============================================
    # PATTERN DETECTION
    # ============================================

    def _detect_patterns(self, anomalies: List[Anomaly], values: List[float]) -> List[str]:
        """Detect patterns in anomalies"""
        patterns = []

        if not anomalies:
            patterns.append("✅ No significant anomalies detected")
            return patterns

        # Pattern 1: Clustering
        anomaly_count = len(anomalies)
        total_periods = len(values)
        if anomaly_count > total_periods * 0.3:
            patterns.append("🔴 High anomaly concentration - possible data quality issues")

        # Pattern 2: Type clustering
        type_counts = {}
        for anomaly in anomalies:
            type_counts[anomaly.anomaly_type] = type_counts.get(anomaly.anomaly_type, 0) + 1

        for anom_type, count in type_counts.items():
            if count >= 3:
                patterns.append(f"⚠️ Multiple {anom_type.value} anomalies detected ({count})")

        # Pattern 3: Severity analysis
        critical_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
        if critical_count > 0:
            patterns.append(f"🚨 {critical_count} critical anomalies require immediate attention")

        return patterns

    def _generate_recommendations(
        self,
        anomalies: List[Anomaly],
        anomaly_rate: float,
        patterns: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if not anomalies:
            recommendations.append("✅ Metric appears stable - no anomalies detected")
            return recommendations

        # Recommendation 1: Investigation priority
        critical_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.CRITICAL]
        if critical_anomalies:
            recommendations.append(
                f"🔍 Prioritize investigation of {len(critical_anomalies)} critical anomalies"
            )

        # Recommendation 2: Data quality
        if anomaly_rate > 30:
            recommendations.append(
                "📊 High anomaly rate suggests data quality issues - verify data sources"
            )

        # Recommendation 3: Spike/drop handling
        spikes = [a for a in anomalies if a.anomaly_type == AnomalyType.SPIKE]
        drops = [a for a in anomalies if a.anomaly_type == AnomalyType.DROP]

        if spikes and drops:
            recommendations.append(
                "📉 Both spikes and drops detected - investigate for volatility causes"
            )

        # Recommendation 4: Zero values
        zeros = [a for a in anomalies if a.anomaly_type == AnomalyType.ZERO_VALUE]
        if zeros:
            recommendations.append(
                f"⚠️ {len(zeros)} zero values detected - verify if expected or missing data"
            )

        return recommendations
