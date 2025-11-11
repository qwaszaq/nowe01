"""
Report Data Models
Pydantic models for structured report generation
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReportFormat(str, Enum):
    """Supported report export formats"""
    PDF = "pdf"
    WORD = "docx"
    JSON = "json"
    HTML = "html"


class Severity(str, Enum):
    """Risk/finding severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TrendDirection(str, Enum):
    """Trend analysis directions"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class Citation(BaseModel):
    """
    Source citation for report claims
    Links findings to specific document pages
    """
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Document filename")
    page_number: int = Field(..., description="Page number in document")
    chunk_id: Optional[str] = Field(None, description="Specific chunk ID if applicable")
    quote: Optional[str] = Field(None, description="Relevant quote from source")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Semantic relevance score")


class Finding(BaseModel):
    """
    Individual analytical finding with supporting evidence
    """
    title: str = Field(..., description="Finding headline")
    description: str = Field(..., description="Detailed explanation")
    severity: Severity = Field(..., description="Finding severity level")
    category: str = Field(..., description="Category (e.g., 'Liquidity', 'Profitability')")
    metric_value: Optional[float] = Field(None, description="Associated metric value")
    metric_name: Optional[str] = Field(None, description="Associated metric name")
    trend: Optional[TrendDirection] = Field(None, description="Trend direction if applicable")
    impact: str = Field(..., description="Business impact explanation")
    recommendation: Optional[str] = Field(None, description="Actionable recommendation")
    citations: List[Citation] = Field(default_factory=list, description="Supporting evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")


class RiskAssessment(BaseModel):
    """
    Risk analysis for a specific category
    """
    category: str = Field(..., description="Risk category (e.g., 'Liquidity Risk')")
    level: Severity = Field(..., description="Overall risk level")
    score: float = Field(..., ge=0.0, le=100.0, description="Risk score (0-100)")
    indicators: List[str] = Field(default_factory=list, description="Key risk indicators")
    mitigation: Optional[str] = Field(None, description="Risk mitigation suggestions")
    trend: Optional[TrendDirection] = Field(None, description="Risk trend direction")


class FinancialHealthScore(BaseModel):
    """
    Overall financial health assessment
    """
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall health score (0-100)")
    liquidity_score: float = Field(..., ge=0.0, le=100.0, description="Liquidity component score")
    profitability_score: float = Field(..., ge=0.0, le=100.0, description="Profitability component score")
    leverage_score: float = Field(..., ge=0.0, le=100.0, description="Leverage component score")

    rating: str = Field(..., description="Letter rating (A+ to F)")
    rating_description: str = Field(..., description="Rating interpretation")

    strengths: List[str] = Field(default_factory=list, description="Key strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Key weaknesses")

    methodology: str = Field(
        default="Composite score based on 19 financial ratios weighted by category",
        description="Scoring methodology explanation"
    )


class MetricAnalysis(BaseModel):
    """
    Detailed analysis of a single financial metric
    """
    metric_name: str = Field(..., description="Metric name")
    category: str = Field(..., description="Category (liquidity/profitability/leverage)")
    value: float = Field(..., description="Current value")
    unit: str = Field(default="ratio", description="Unit of measurement")

    interpretation: str = Field(..., description="What this value means")
    benchmark: Optional[float] = Field(None, description="Industry benchmark if available")
    status: str = Field(..., description="Good/Warning/Poor status")

    trend: Optional[TrendDirection] = Field(None, description="Trend direction")
    trend_explanation: Optional[str] = Field(None, description="Trend analysis")

    ai_insights: List[str] = Field(default_factory=list, description="AI-generated insights")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")


class ReportSection(BaseModel):
    """
    Individual section within a report
    """
    title: str = Field(..., description="Section title")
    order: int = Field(..., description="Section order in report")
    content: str = Field(..., description="Section content (markdown)")
    subsections: List['ReportSection'] = Field(default_factory=list, description="Nested subsections")
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="Chart data")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Table data")


class ExecutiveSummary(BaseModel):
    """
    Executive summary report structure
    """
    case_id: str
    case_name: str
    company_name: Optional[str] = None
    analysis_date: datetime = Field(default_factory=datetime.now)

    # Core components
    key_findings: List[Finding] = Field(..., description="Top 3-5 critical findings")
    financial_health: FinancialHealthScore = Field(..., description="Overall health assessment")
    risk_assessment: List[RiskAssessment] = Field(..., description="Risk analysis by category")

    # Summary metrics
    document_count: int = Field(..., description="Number of documents analyzed")
    page_count: int = Field(..., description="Total pages processed")
    ratios_calculated: int = Field(default=19, description="Number of ratios calculated")

    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, description="Urgent actions needed")
    strategic_recommendations: List[str] = Field(default_factory=list, description="Long-term recommendations")

    # Metadata
    generated_by: str = Field(default="Investigation Intelligence Platform", description="Generator")
    analyst: Optional[str] = Field(None, description="Analyst name if applicable")


class DeepDiveReport(BaseModel):
    """
    Comprehensive deep-dive report structure
    """
    # Header
    case_id: str
    case_name: str
    company_name: Optional[str] = None
    analysis_period: str = Field(..., description="Period covered (e.g., 'FY 2023')")
    analysis_date: datetime = Field(default_factory=datetime.now)

    # Executive summary (embedded)
    executive_summary: ExecutiveSummary

    # Detailed sections
    sections: List[ReportSection] = Field(default_factory=list, description="Report sections")

    # All metrics
    metrics: List[MetricAnalysis] = Field(..., description="All 19 financial ratios")

    # All findings
    findings: List[Finding] = Field(..., description="All analytical findings")

    # Supporting data
    document_metadata: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents")

    # Appendices
    appendix_data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")

    # Metadata
    generated_by: str = Field(default="Investigation Intelligence Platform", description="Generator")
    version: str = Field(default="1.0", description="Report version")
    total_pages: Optional[int] = Field(None, description="Page count for PDF export")


class TrendAnalysis(BaseModel):
    """
    Trend analysis across time periods
    """
    metric_name: str
    periods: List[str] = Field(..., description="Period labels (e.g., 'Q1 2023', 'Q2 2023')")
    values: List[float] = Field(..., description="Values for each period")

    direction: TrendDirection
    change_percent: Optional[float] = Field(None, description="Overall % change")
    volatility: float = Field(..., ge=0.0, le=1.0, description="Volatility score")

    analysis: str = Field(..., description="Trend interpretation")
    anomalies: List[str] = Field(default_factory=list, description="Detected anomalies")


class ComparativeAnalysis(BaseModel):
    """
    Comparison between entities or periods
    """
    comparison_type: str = Field(..., description="Type (e.g., 'Period', 'Industry')")
    entity_a: str
    entity_b: str

    metrics: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Metric comparisons: {metric_name: {entity_a: value, entity_b: value}}"
    )

    differences: List[Finding] = Field(..., description="Significant differences identified")
    winner_metrics: Dict[str, str] = Field(..., description="Which entity performs better per metric")

    summary: str = Field(..., description="Comparison summary")


# Allow forward references
ReportSection.model_rebuild()
