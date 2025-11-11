"""
Business Intelligence Analytics Module
BI-style analytics engine with KPIs, trends, and drill-down capabilities
"""

from .kpi_engine import KPIEngine, KPIDefinition, KPIResult
from .trend_analyzer import TrendAnalyzer, TrendResult, ForecastResult
from .anomaly_detector import AnomalyDetector, Anomaly, AnomalyType
from .comparative_analyzer import ComparativeAnalyzer, ComparisonResult
from .drill_down import DrillDownEngine, AggregationLevel

__all__ = [
    'KPIEngine',
    'KPIDefinition',
    'KPIResult',
    'TrendAnalyzer',
    'TrendResult',
    'ForecastResult',
    'AnomalyDetector',
    'Anomaly',
    'AnomalyType',
    'ComparativeAnalyzer',
    'ComparisonResult',
    'DrillDownEngine',
    'AggregationLevel'
]
