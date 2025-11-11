"""
Trend Analysis and Forecasting Module
Time-series analysis, pattern detection, and forecasting for financial metrics
"""

import logging
import statistics
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field
import math

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Trend direction classification"""
    STRONG_UPWARD = "strong_upward"      # +15% or more
    UPWARD = "upward"                    # +5% to +15%
    SLIGHTLY_UPWARD = "slightly_upward"  # +1% to +5%
    STABLE = "stable"                    # -1% to +1%
    SLIGHTLY_DOWNWARD = "slightly_downward"  # -5% to -1%
    DOWNWARD = "downward"                # -15% to -5%
    STRONG_DOWNWARD = "strong_downward"  # -15% or less
    VOLATILE = "volatile"                # High variance
    INSUFFICIENT_DATA = "insufficient_data"


class SeasonalityType(str, Enum):
    """Seasonality pattern types"""
    NONE = "none"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class DataPoint(BaseModel):
    """Single time-series data point"""
    timestamp: datetime
    value: float
    period_label: str = Field(..., description="Human-readable period (e.g., 'Q1 2023')")
    metadata: Dict = Field(default_factory=dict)


class TrendResult(BaseModel):
    """
    Trend analysis result
    """
    metric_name: str
    direction: TrendDirection
    confidence: float = Field(..., ge=0.0, le=1.0, description="Trend confidence (0-1)")

    # Statistical measures
    slope: float = Field(..., description="Linear regression slope")
    correlation: float = Field(..., ge=-1.0, le=1.0, description="Correlation coefficient")
    volatility: float = Field(..., ge=0.0, description="Standard deviation / mean")

    # Changes
    start_value: float
    end_value: float
    total_change: float = Field(..., description="Absolute change")
    total_change_percent: float = Field(..., description="Percentage change")

    # Period analysis
    periods: int = Field(..., description="Number of periods analyzed")
    period_labels: List[str] = Field(default_factory=list)

    # Insights
    summary: str = Field(..., description="Human-readable trend summary")
    insights: List[str] = Field(default_factory=list)

    # Anomalies detected during trend analysis
    anomalous_periods: List[str] = Field(default_factory=list)


class ForecastResult(BaseModel):
    """
    Forecast result with predictions
    """
    metric_name: str
    forecast_periods: int = Field(..., description="Number of periods forecast")

    # Predictions
    predictions: List[DataPoint] = Field(..., description="Predicted values")
    confidence_intervals: List[Tuple[float, float]] = Field(
        ...,
        description="(lower, upper) confidence intervals for each prediction"
    )

    # Forecast quality
    method: str = Field(..., description="Forecast method used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall forecast confidence")
    expected_error: float = Field(..., description="Expected mean absolute percentage error")

    # Historical data quality
    historical_periods: int
    data_quality_score: float = Field(..., ge=0.0, le=1.0)

    # Insights
    summary: str
    warnings: List[str] = Field(default_factory=list)


class TrendAnalyzer:
    """
    Trend Analysis Engine
    Analyzes time-series data for patterns, trends, and generates forecasts
    """

    def __init__(self, min_periods: int = 3):
        """
        Initialize trend analyzer

        Args:
            min_periods: Minimum number of data points required for analysis
        """
        self.min_periods = min_periods
        logger.info(f"TrendAnalyzer initialized (min_periods={min_periods})")

    def analyze_trend(
        self,
        metric_name: str,
        data_points: List[DataPoint],
        detect_anomalies: bool = True
    ) -> TrendResult:
        """
        Analyze trend from time-series data

        Args:
            metric_name: Name of metric being analyzed
            data_points: Time-ordered data points
            detect_anomalies: Whether to detect anomalous periods

        Returns:
            TrendResult with comprehensive trend analysis
        """
        if len(data_points) < self.min_periods:
            return TrendResult(
                metric_name=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                confidence=0.0,
                slope=0.0,
                correlation=0.0,
                volatility=0.0,
                start_value=0.0,
                end_value=0.0,
                total_change=0.0,
                total_change_percent=0.0,
                periods=len(data_points),
                summary=f"Insufficient data: need at least {self.min_periods} periods"
            )

        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda p: p.timestamp)
        values = [p.value for p in sorted_points]
        period_labels = [p.period_label for p in sorted_points]

        # Calculate statistics
        start_value = values[0]
        end_value = values[-1]
        total_change = end_value - start_value
        total_change_percent = (total_change / start_value * 100) if start_value != 0 else 0.0

        # Linear regression
        slope, correlation = self._calculate_linear_regression(values)

        # Volatility
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        volatility = (std_dev / mean_value) if mean_value != 0 else 0.0

        # Determine direction
        direction = self._classify_trend(total_change_percent, volatility)

        # Calculate confidence
        confidence = abs(correlation)

        # Detect anomalies
        anomalous_periods = []
        if detect_anomalies and len(values) > self.min_periods:
            anomalous_periods = self._detect_anomalies(sorted_points, values)

        # Generate insights
        summary, insights = self._generate_trend_insights(
            metric_name,
            direction,
            total_change_percent,
            volatility,
            len(values),
            anomalous_periods
        )

        return TrendResult(
            metric_name=metric_name,
            direction=direction,
            confidence=confidence,
            slope=slope,
            correlation=correlation,
            volatility=volatility,
            start_value=start_value,
            end_value=end_value,
            total_change=total_change,
            total_change_percent=total_change_percent,
            periods=len(values),
            period_labels=period_labels,
            summary=summary,
            insights=insights,
            anomalous_periods=anomalous_periods
        )

    def forecast(
        self,
        metric_name: str,
        data_points: List[DataPoint],
        forecast_periods: int = 3,
        method: str = "linear"
    ) -> ForecastResult:
        """
        Generate forecast for future periods

        Args:
            metric_name: Name of metric to forecast
            data_points: Historical data points
            forecast_periods: Number of periods to forecast
            method: Forecast method ('linear', 'moving_average', 'exponential')

        Returns:
            ForecastResult with predictions and confidence intervals
        """
        if len(data_points) < self.min_periods:
            return ForecastResult(
                metric_name=metric_name,
                forecast_periods=0,
                predictions=[],
                confidence_intervals=[],
                method=method,
                confidence=0.0,
                expected_error=0.0,
                historical_periods=len(data_points),
                data_quality_score=0.0,
                summary=f"Insufficient historical data for forecasting (need {self.min_periods}+ periods)",
                warnings=["Cannot generate forecast with insufficient data"]
            )

        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda p: p.timestamp)
        values = [p.value for p in sorted_points]

        # Calculate data quality
        data_quality = self._assess_data_quality(values)

        # Generate predictions based on method
        if method == "linear":
            predictions, confidence_intervals = self._linear_forecast(sorted_points, forecast_periods)
        elif method == "moving_average":
            predictions, confidence_intervals = self._moving_average_forecast(sorted_points, forecast_periods)
        elif method == "exponential":
            predictions, confidence_intervals = self._exponential_smoothing_forecast(sorted_points, forecast_periods)
        else:
            raise ValueError(f"Unknown forecast method: {method}")

        # Estimate forecast confidence
        slope, correlation = self._calculate_linear_regression(values)
        forecast_confidence = abs(correlation) * data_quality

        # Calculate expected error (simplified MAPE estimation)
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        expected_error = (std_dev / mean_value * 100) if mean_value != 0 else 0.0

        # Generate summary and warnings
        summary = self._generate_forecast_summary(method, forecast_periods, forecast_confidence)
        warnings = self._generate_forecast_warnings(data_quality, expected_error)

        return ForecastResult(
            metric_name=metric_name,
            forecast_periods=len(predictions),
            predictions=predictions,
            confidence_intervals=confidence_intervals,
            method=method,
            confidence=forecast_confidence,
            expected_error=expected_error,
            historical_periods=len(data_points),
            data_quality_score=data_quality,
            summary=summary,
            warnings=warnings
        )

    # ============================================
    # PRIVATE HELPER METHODS
    # ============================================

    def _calculate_linear_regression(self, values: List[float]) -> Tuple[float, float]:
        """
        Calculate linear regression slope and correlation

        Returns:
            (slope, correlation_coefficient)
        """
        n = len(values)
        if n < 2:
            return 0.0, 0.0

        x = list(range(n))
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(values)

        # Calculate slope
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate correlation coefficient
        std_x = statistics.stdev(x) if n > 1 else 0.0
        std_y = statistics.stdev(values) if n > 1 else 0.0

        if std_x != 0 and std_y != 0:
            correlation = numerator / (n * std_x * std_y)
        else:
            correlation = 0.0

        return slope, correlation

    def _classify_trend(self, change_percent: float, volatility: float) -> TrendDirection:
        """Classify trend direction based on change and volatility"""
        if volatility > 0.3:  # High volatility
            return TrendDirection.VOLATILE

        if change_percent >= 15:
            return TrendDirection.STRONG_UPWARD
        elif change_percent >= 5:
            return TrendDirection.UPWARD
        elif change_percent >= 1:
            return TrendDirection.SLIGHTLY_UPWARD
        elif change_percent >= -1:
            return TrendDirection.STABLE
        elif change_percent >= -5:
            return TrendDirection.SLIGHTLY_DOWNWARD
        elif change_percent >= -15:
            return TrendDirection.DOWNWARD
        else:
            return TrendDirection.STRONG_DOWNWARD

    def _detect_anomalies(
        self,
        sorted_points: List[DataPoint],
        values: List[float]
    ) -> List[str]:
        """
        Detect anomalous periods using z-score method

        Args:
            sorted_points: Sorted data points
            values: Extracted values

        Returns:
            List of anomalous period labels
        """
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0

        if std_dev == 0:
            return []

        anomalies = []
        z_threshold = 2.0  # 2 standard deviations

        for point, value in zip(sorted_points, values):
            z_score = abs((value - mean) / std_dev)
            if z_score > z_threshold:
                anomalies.append(point.period_label)

        return anomalies

    def _assess_data_quality(self, values: List[float]) -> float:
        """
        Assess quality of historical data

        Returns:
            Quality score from 0.0 to 1.0
        """
        if len(values) < self.min_periods:
            return 0.0

        quality_factors = []

        # Factor 1: Sufficient data points (max score at 12+ periods)
        data_completeness = min(len(values) / 12.0, 1.0)
        quality_factors.append(data_completeness)

        # Factor 2: Low missing value rate (assuming no missing here, as they're filtered)
        quality_factors.append(1.0)

        # Factor 3: Reasonable volatility (not too volatile)
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        volatility = (std_dev / mean_value) if mean_value != 0 else 0.0
        volatility_score = max(0.0, 1.0 - (volatility / 0.5))  # Penalize volatility > 50%
        quality_factors.append(volatility_score)

        # Factor 4: No extreme outliers
        q1 = sorted(values)[len(values) // 4] if len(values) >= 4 else values[0]
        q3 = sorted(values)[3 * len(values) // 4] if len(values) >= 4 else values[-1]
        iqr = q3 - q1
        outliers = [v for v in values if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr]
        outlier_rate = len(outliers) / len(values)
        outlier_score = max(0.0, 1.0 - outlier_rate * 2)
        quality_factors.append(outlier_score)

        return statistics.mean(quality_factors)

    def _linear_forecast(
        self,
        sorted_points: List[DataPoint],
        forecast_periods: int
    ) -> Tuple[List[DataPoint], List[Tuple[float, float]]]:
        """Generate linear regression forecast"""
        values = [p.value for p in sorted_points]
        slope, _ = self._calculate_linear_regression(values)

        last_point = sorted_points[-1]
        last_value = values[-1]

        # Calculate prediction error for confidence intervals
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        confidence_width = 1.96 * std_dev  # 95% confidence interval

        predictions = []
        confidence_intervals = []

        for i in range(1, forecast_periods + 1):
            predicted_value = last_value + (slope * i)

            # Create forecast data point
            forecast_point = DataPoint(
                timestamp=last_point.timestamp,  # Placeholder - should calculate future date
                value=predicted_value,
                period_label=f"Forecast +{i}"
            )
            predictions.append(forecast_point)

            # Confidence interval widens with forecast horizon
            interval_width = confidence_width * (1 + i * 0.1)  # Widens 10% per period
            lower_bound = predicted_value - interval_width
            upper_bound = predicted_value + interval_width
            confidence_intervals.append((lower_bound, upper_bound))

        return predictions, confidence_intervals

    def _moving_average_forecast(
        self,
        sorted_points: List[DataPoint],
        forecast_periods: int,
        window: int = 3
    ) -> Tuple[List[DataPoint], List[Tuple[float, float]]]:
        """Generate moving average forecast"""
        values = [p.value for p in sorted_points]
        window = min(window, len(values))

        # Calculate moving average
        recent_values = values[-window:]
        ma_value = statistics.mean(recent_values)

        # Prediction error
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        confidence_width = 1.96 * std_dev

        last_point = sorted_points[-1]

        predictions = []
        confidence_intervals = []

        for i in range(1, forecast_periods + 1):
            forecast_point = DataPoint(
                timestamp=last_point.timestamp,
                value=ma_value,
                period_label=f"Forecast +{i}"
            )
            predictions.append(forecast_point)

            interval_width = confidence_width * (1 + i * 0.15)
            lower_bound = ma_value - interval_width
            upper_bound = ma_value + interval_width
            confidence_intervals.append((lower_bound, upper_bound))

        return predictions, confidence_intervals

    def _exponential_smoothing_forecast(
        self,
        sorted_points: List[DataPoint],
        forecast_periods: int,
        alpha: float = 0.3
    ) -> Tuple[List[DataPoint], List[Tuple[float, float]]]:
        """Generate exponential smoothing forecast"""
        values = [p.value for p in sorted_points]

        # Calculate exponentially weighted moving average
        ema = values[0]
        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * ema

        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        confidence_width = 1.96 * std_dev

        last_point = sorted_points[-1]

        predictions = []
        confidence_intervals = []

        for i in range(1, forecast_periods + 1):
            forecast_point = DataPoint(
                timestamp=last_point.timestamp,
                value=ema,
                period_label=f"Forecast +{i}"
            )
            predictions.append(forecast_point)

            interval_width = confidence_width * (1 + i * 0.12)
            lower_bound = ema - interval_width
            upper_bound = ema + interval_width
            confidence_intervals.append((lower_bound, upper_bound))

        return predictions, confidence_intervals

    def _generate_trend_insights(
        self,
        metric_name: str,
        direction: TrendDirection,
        change_percent: float,
        volatility: float,
        periods: int,
        anomalies: List[str]
    ) -> Tuple[str, List[str]]:
        """Generate human-readable trend summary and insights"""

        # Summary
        if direction == TrendDirection.STRONG_UPWARD:
            summary = f"{metric_name} shows strong upward trend (+{change_percent:.1f}% over {periods} periods)"
        elif direction == TrendDirection.UPWARD:
            summary = f"{metric_name} is trending upward (+{change_percent:.1f}%)"
        elif direction == TrendDirection.SLIGHTLY_UPWARD:
            summary = f"{metric_name} shows slight improvement (+{change_percent:.1f}%)"
        elif direction == TrendDirection.STABLE:
            summary = f"{metric_name} remains stable (±{abs(change_percent):.1f}%)"
        elif direction == TrendDirection.SLIGHTLY_DOWNWARD:
            summary = f"{metric_name} shows slight decline ({change_percent:.1f}%)"
        elif direction == TrendDirection.DOWNWARD:
            summary = f"{metric_name} is trending downward ({change_percent:.1f}%)"
        elif direction == TrendDirection.STRONG_DOWNWARD:
            summary = f"{metric_name} shows strong downward trend ({change_percent:.1f}%)"
        elif direction == TrendDirection.VOLATILE:
            summary = f"{metric_name} exhibits high volatility (±{volatility*100:.1f}%)"
        else:
            summary = f"Insufficient data to determine trend for {metric_name}"

        # Insights
        insights = []

        if volatility > 0.2:
            insights.append(f"📊 High volatility detected ({volatility*100:.1f}%) - metric is unstable")

        if anomalies:
            insights.append(f"⚠️ Anomalous periods detected: {', '.join(anomalies)}")

        if abs(change_percent) > 20:
            insights.append(f"🚨 Significant change detected - requires investigation")

        return summary, insights

    def _generate_forecast_summary(
        self,
        method: str,
        periods: int,
        confidence: float
    ) -> str:
        """Generate forecast summary message"""
        confidence_level = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"

        return (
            f"Forecast using {method} method for {periods} periods "
            f"with {confidence_level} confidence ({confidence*100:.0f}%)"
        )

    def _generate_forecast_warnings(
        self,
        data_quality: float,
        expected_error: float
    ) -> List[str]:
        """Generate forecast warnings based on quality"""
        warnings = []

        if data_quality < 0.5:
            warnings.append("⚠️ Low data quality - forecast may be unreliable")

        if expected_error > 20:
            warnings.append(f"⚠️ High expected error ({expected_error:.1f}%) - use forecast with caution")

        return warnings
