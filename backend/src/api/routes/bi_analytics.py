"""
BI Analytics API Routes
Business Intelligence endpoints for KPIs, trends, anomalies, and comparisons
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from src.core.analytics.kpi_engine import (
    KPIEngine, KPIResult, KPIDashboard, KPICategory
)
from src.core.analytics.trend_analyzer import (
    TrendAnalyzer, TrendResult, ForecastResult, DataPoint
)
from src.core.analytics.anomaly_detector import (
    AnomalyDetector, AnomalyReport, Anomaly
)
from src.core.analytics.comparative_analyzer import (
    ComparativeAnalyzer, PeriodComparison, ComparisonResult, ComparisonType
)
from src.core.analytics.drill_down import (
    DrillDownEngine, DrillDownResult, AggregationLevel, AggregationType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["BI Analytics"])

# Initialize analytics engines
kpi_engine = KPIEngine()
trend_analyzer = TrendAnalyzer()
anomaly_detector = AnomalyDetector()
comparative_analyzer = ComparativeAnalyzer()
drill_down_engine = DrillDownEngine()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class KPICalculationRequest(BaseModel):
    """Request to calculate specific KPIs"""
    metrics: Dict[str, float] = Field(..., description="Current metric values {kpi_id: value}")
    previous_metrics: Optional[Dict[str, float]] = Field(None, description="Previous period for comparison")
    case_id: Optional[str] = None
    period: Optional[str] = None


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis"""
    metric_name: str
    data_points: List[Dict[str, Any]] = Field(
        ...,
        description="List of {timestamp, value, period_label} data points"
    )
    detect_anomalies: bool = Field(default=True)


class ForecastRequest(BaseModel):
    """Request for forecasting"""
    metric_name: str
    data_points: List[Dict[str, Any]]
    forecast_periods: int = Field(default=3, ge=1, le=12)
    method: str = Field(default="linear", pattern="^(linear|moving_average|exponential)$")


class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection"""
    metric_name: str
    data_points: List[Dict[str, Any]]
    analysis_period: str = Field(default="Recent")


class PeriodComparisonRequest(BaseModel):
    """Request for period-over-period comparison"""
    period_a_label: str
    period_a_metrics: Dict[str, float]
    period_b_label: str
    period_b_metrics: Dict[str, float]
    comparison_type: str = Field(default="period_over_period")
    metric_metadata: Optional[Dict[str, Dict]] = None


# ============================================================================
# KPI ENDPOINTS
# ============================================================================

@router.get(
    "/kpis/definitions",
    response_model=List[Dict],
    summary="List KPI Definitions",
    description="Get all registered KPI definitions with thresholds and targets"
)
async def list_kpi_definitions(
    category: Optional[str] = Query(None, description="Filter by KPI category")
) -> List[Dict]:
    """
    List all KPI definitions

    Returns KPI metadata including:
    - Thresholds (critical, warning, target)
    - Formula and calculation method
    - Display preferences (icons, colors, chart types)
    - Category classification
    """
    try:
        category_filter = KPICategory(category) if category else None
        kpis = kpi_engine.list_kpis(category_filter)

        return [kpi.model_dump() for kpi in kpis]

    except Exception as e:
        logger.error(f"Error listing KPI definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/kpis/calculate",
    response_model=KPIDashboard,
    summary="Calculate KPI Dashboard",
    description="Calculate all KPIs with status evaluation and alerts"
)
async def calculate_kpi_dashboard(request: KPICalculationRequest) -> KPIDashboard:
    """
    Calculate complete KPI dashboard

    Evaluates each KPI against:
    - Critical thresholds (red alert)
    - Warning thresholds (yellow warning)
    - Target values (green excellent)

    Returns dashboard with:
    - Individual KPI results with status
    - Summary statistics by status
    - Critical and warning alerts
    - Period-over-period comparisons
    """
    try:
        dashboard = kpi_engine.calculate_dashboard(
            metrics=request.metrics,
            previous_metrics=request.previous_metrics,
            case_id=request.case_id,
            period=request.period
        )

        logger.info(
            f"KPI Dashboard calculated: {dashboard.total_kpis} KPIs, "
            f"{dashboard.critical_count} critical, {dashboard.warning_count} warnings"
        )

        return dashboard

    except Exception as e:
        logger.error(f"Error calculating KPI dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/kpis/{kpi_id}/definition",
    response_model=Dict,
    summary="Get KPI Definition",
    description="Get detailed definition for a specific KPI"
)
async def get_kpi_definition(kpi_id: str) -> Dict:
    """Get definition for a specific KPI"""
    try:
        kpi_def = kpi_engine.get_kpi_definition(kpi_id)

        if not kpi_def:
            raise HTTPException(status_code=404, detail=f"KPI '{kpi_id}' not found")

        return kpi_def.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting KPI definition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TREND ANALYSIS ENDPOINTS
# ============================================================================

@router.post(
    "/trends/analyze",
    response_model=TrendResult,
    summary="Analyze Trend",
    description="Perform comprehensive trend analysis on time-series data"
)
async def analyze_trend(request: TrendAnalysisRequest) -> TrendResult:
    """
    Analyze trend in time-series data

    Provides:
    - Trend direction classification (upward, downward, stable, volatile)
    - Linear regression analysis
    - Volatility measurement
    - Anomaly detection (if enabled)
    - Statistical confidence metrics
    - Human-readable insights
    """
    try:
        # Convert dicts to DataPoint objects
        data_points = [
            DataPoint(
                timestamp=datetime.fromisoformat(p['timestamp']) if isinstance(p['timestamp'], str) else p['timestamp'],
                value=p['value'],
                period_label=p['period_label']
            )
            for p in request.data_points
        ]

        result = trend_analyzer.analyze_trend(
            metric_name=request.metric_name,
            data_points=data_points,
            detect_anomalies=request.detect_anomalies
        )

        logger.info(f"Trend analysis completed: {request.metric_name} - {result.direction.value}")

        return result

    except Exception as e:
        logger.error(f"Error analyzing trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/trends/forecast",
    response_model=ForecastResult,
    summary="Generate Forecast",
    description="Forecast future values using time-series analysis"
)
async def generate_forecast(request: ForecastRequest) -> ForecastResult:
    """
    Generate forecast for future periods

    Forecasting methods:
    - **linear**: Linear regression extrapolation
    - **moving_average**: Simple moving average
    - **exponential**: Exponential smoothing

    Returns:
    - Predicted values for each future period
    - Confidence intervals (95%)
    - Forecast quality metrics
    - Data quality assessment
    - Warnings and recommendations
    """
    try:
        # Convert to DataPoint objects
        data_points = [
            DataPoint(
                timestamp=datetime.fromisoformat(p['timestamp']) if isinstance(p['timestamp'], str) else p['timestamp'],
                value=p['value'],
                period_label=p['period_label']
            )
            for p in request.data_points
        ]

        result = trend_analyzer.forecast(
            metric_name=request.metric_name,
            data_points=data_points,
            forecast_periods=request.forecast_periods,
            method=request.method
        )

        logger.info(
            f"Forecast generated: {request.metric_name}, {request.forecast_periods} periods, "
            f"confidence={result.confidence:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANOMALY DETECTION ENDPOINTS
# ============================================================================

@router.post(
    "/anomalies/detect",
    response_model=AnomalyReport,
    summary="Detect Anomalies",
    description="Detect anomalies using multiple statistical methods"
)
async def detect_anomalies(request: AnomalyDetectionRequest) -> AnomalyReport:
    """
    Detect anomalies in time-series data

    Detection methods:
    - Statistical outliers (Z-score)
    - IQR outliers
    - Spikes and drops (period-to-period changes)
    - Pattern breaks (trend reversals)
    - Zero values (unexpected zeros)

    Returns:
    - All detected anomalies with severity classification
    - Baseline statistics
    - Pattern analysis
    - Actionable recommendations
    """
    try:
        result = anomaly_detector.detect_anomalies(
            metric_name=request.metric_name,
            data_points=request.data_points,
            analysis_period=request.analysis_period
        )

        logger.info(
            f"Anomaly detection completed: {request.metric_name}, "
            f"{result.total_anomalies} anomalies found ({result.critical_count} critical)"
        )

        return result

    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/anomalies/summary",
    response_model=Dict[str, Any],
    summary="Anomaly Summary",
    description="Get summary statistics about detected anomalies"
)
async def get_anomaly_summary(
    case_id: Optional[str] = Query(None),
    period: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get anomaly summary statistics

    Provides overview of:
    - Total anomalies by severity
    - Anomaly types distribution
    - Metrics with most anomalies
    - Time periods with anomalies
    """
    # This would integrate with actual data storage
    # For now, return placeholder
    return {
        "case_id": case_id,
        "period": period,
        "total_anomalies": 0,
        "by_severity": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "by_type": {},
        "metrics_affected": [],
        "message": "Anomaly summary endpoint - integrate with data storage"
    }


# ============================================================================
# COMPARATIVE ANALYSIS ENDPOINTS
# ============================================================================

@router.post(
    "/compare/periods",
    response_model=PeriodComparison,
    summary="Compare Periods",
    description="Compare metrics between two time periods"
)
async def compare_periods(request: PeriodComparisonRequest) -> PeriodComparison:
    """
    Compare financial metrics between two periods

    Comparison types:
    - Period-over-period (e.g., Q1 2024 vs Q1 2023)
    - Sequential period (e.g., Q2 vs Q1)
    - Year-over-year
    - Month-over-month

    Returns:
    - Metric-by-metric comparison
    - Performance ratings (better/worse/similar)
    - Overall performance assessment
    - Key improvements and declines
    - Insights and recommendations
    """
    try:
        comparison_type = ComparisonType(request.comparison_type)

        result = comparative_analyzer.compare_periods(
            period_a_label=request.period_a_label,
            period_a_metrics=request.period_a_metrics,
            period_b_label=request.period_b_label,
            period_b_metrics=request.period_b_metrics,
            comparison_type=comparison_type,
            metric_metadata=request.metric_metadata
        )

        logger.info(
            f"Period comparison completed: {request.period_a_label} vs {request.period_b_label}, "
            f"{result.total_metrics} metrics compared"
        )

        return result

    except Exception as e:
        logger.error(f"Error comparing periods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/compare/benchmark",
    response_model=Dict[str, Any],
    summary="Benchmark Comparison",
    description="Compare against industry benchmarks"
)
async def benchmark_comparison(
    case_id: str = Query(...),
    industry: Optional[str] = Query(None),
    period: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Compare company metrics against industry benchmarks

    Would integrate with:
    - Industry benchmark databases
    - Peer company data
    - Market standards
    """
    return {
        "case_id": case_id,
        "industry": industry or "General",
        "period": period,
        "message": "Benchmark comparison - requires industry data integration",
        "status": "placeholder"
    }


# ============================================================================
# DRILL-DOWN ENDPOINTS
# ============================================================================

@router.get(
    "/drilldown/hierarchy",
    response_model=Dict[str, List[str]],
    summary="Get Drill-Down Hierarchies",
    description="List available drill-down hierarchies"
)
async def get_hierarchies() -> Dict[str, List[str]]:
    """
    Get available drill-down hierarchies

    Returns hierarchies for:
    - Time (year → quarter → month → week → day)
    - Organization (company → division → department)
    - Metrics (category → group → individual)
    - Documents (set → document → pages → page)
    """
    hierarchies = {
        name: [level.value for level in levels]
        for name, levels in drill_down_engine.hierarchy_definitions.items()
    }
    return hierarchies


@router.post(
    "/drilldown/aggregate",
    response_model=List[Dict],
    summary="Aggregate Metrics",
    description="Aggregate metrics at specified hierarchical level"
)
async def aggregate_metrics(
    metric_name: str = Query(...),
    level: str = Query(..., description="Aggregation level"),
    aggregation_type: str = Query(default="average", pattern="^(sum|average|median|min|max|count)$"),
    group_by: Optional[str] = Query(None)
) -> List[Dict]:
    """
    Aggregate metrics at specified level

    Aggregation types:
    - sum: Total of all values
    - average: Mean value
    - median: Median value
    - min: Minimum value
    - max: Maximum value
    - count: Count of data points
    """
    try:
        agg_level = AggregationLevel(level)
        agg_type = AggregationType(aggregation_type)

        # This would integrate with actual data retrieval
        # For now, return placeholder
        return [{
            "metric_name": metric_name,
            "aggregation_level": level,
            "aggregation_type": aggregation_type,
            "message": "Drill-down aggregation - integrate with data storage"
        }]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Error aggregating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTEGRATED ANALYTICS ENDPOINTS
# ============================================================================

@router.get(
    "/dashboard/overview",
    response_model=Dict[str, Any],
    summary="BI Dashboard Overview",
    description="Get complete BI dashboard with all analytics"
)
async def get_dashboard_overview(
    case_id: str = Query(...),
    period: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get comprehensive BI dashboard overview

    Combines:
    - KPI dashboard with current status
    - Recent trends
    - Active anomalies
    - Period comparisons
    - Key insights and alerts
    """
    try:
        # This would integrate with actual data and analysis engines
        # For now, return structure
        return {
            "case_id": case_id,
            "period": period or "Current",
            "generated_at": datetime.now().isoformat(),
            "kpis": {
                "total": 10,
                "excellent": 0,
                "good": 0,
                "warning": 0,
                "critical": 0
            },
            "trends": {
                "total_metrics_analyzed": 0,
                "upward_trends": 0,
                "downward_trends": 0,
                "stable": 0
            },
            "anomalies": {
                "total": 0,
                "critical": 0,
                "requires_investigation": 0
            },
            "insights": [],
            "alerts": [],
            "message": "Dashboard overview - integrate with data and engines"
        }

    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    summary="Analytics Engine Health",
    description="Check health of analytics engines"
)
async def analytics_health() -> Dict[str, Any]:
    """Check health of all analytics engines"""
    return {
        "status": "healthy",
        "engines": {
            "kpi_engine": {
                "status": "operational",
                "kpis_registered": len(kpi_engine.kpi_definitions)
            },
            "trend_analyzer": {
                "status": "operational",
                "min_periods": trend_analyzer.min_periods
            },
            "anomaly_detector": {
                "status": "operational",
                "z_threshold": anomaly_detector.z_threshold
            },
            "comparative_analyzer": {
                "status": "operational"
            },
            "drill_down_engine": {
                "status": "operational",
                "hierarchies": list(drill_down_engine.hierarchy_definitions.keys())
            }
        },
        "timestamp": datetime.now().isoformat()
    }
