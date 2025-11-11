"""
KPI Calculation Engine
Business Intelligence KPI system with thresholds, targets, and alerts
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KPIStatus(str, Enum):
    """KPI performance status"""
    EXCELLENT = "excellent"      # Exceeds target
    GOOD = "good"               # Meets target
    WARNING = "warning"         # Approaching threshold
    CRITICAL = "critical"       # Below threshold
    UNKNOWN = "unknown"         # Insufficient data


class KPICategory(str, Enum):
    """KPI categories for organization"""
    LIQUIDITY = "liquidity"
    PROFITABILITY = "profitability"
    LEVERAGE = "leverage"
    EFFICIENCY = "efficiency"
    GROWTH = "growth"
    RISK = "risk"


class ThresholdType(str, Enum):
    """Threshold comparison types"""
    GREATER_THAN = "greater_than"      # Value should be > threshold
    LESS_THAN = "less_than"           # Value should be < threshold
    BETWEEN = "between"               # Value should be in range
    EQUALS = "equals"                 # Value should equal target


class KPIDefinition(BaseModel):
    """
    Defines a KPI with calculation rules and thresholds
    """
    kpi_id: str = Field(..., description="Unique KPI identifier")
    name: str = Field(..., description="KPI display name")
    description: str = Field(..., description="What this KPI measures")
    category: KPICategory = Field(..., description="KPI category")

    # Calculation
    formula: str = Field(..., description="Formula description or calculation method")
    unit: str = Field(default="ratio", description="Unit of measurement (%, $, ratio, etc.)")
    decimal_places: int = Field(default=2, description="Decimal precision for display")

    # Thresholds
    threshold_type: ThresholdType = Field(..., description="How to evaluate performance")
    critical_threshold: Optional[float] = Field(None, description="Critical (red) threshold")
    warning_threshold: Optional[float] = Field(None, description="Warning (yellow) threshold")
    target: Optional[float] = Field(None, description="Target (green) value")
    upper_bound: Optional[float] = Field(None, description="Upper bound for BETWEEN type")

    # Metadata
    data_source: str = Field(default="financial_ratios", description="Where data comes from")
    frequency: str = Field(default="monthly", description="Update frequency")
    is_higher_better: bool = Field(True, description="True if higher values are better")

    # Display
    icon: Optional[str] = Field(None, description="Icon identifier for UI")
    color: Optional[str] = Field(None, description="Primary color for visualizations")
    chart_type: str = Field(default="line", description="Preferred chart type")


class KPIResult(BaseModel):
    """
    Calculated KPI result with status and context
    """
    kpi_id: str
    kpi_name: str
    category: KPICategory

    # Current value
    value: float = Field(..., description="Current KPI value")
    formatted_value: str = Field(..., description="Formatted for display")
    unit: str

    # Status
    status: KPIStatus = Field(..., description="Performance status")
    status_message: str = Field(..., description="Human-readable status explanation")

    # Comparison
    target: Optional[float] = None
    target_diff: Optional[float] = Field(None, description="Difference from target")
    target_diff_percent: Optional[float] = Field(None, description="% difference from target")

    previous_value: Optional[float] = Field(None, description="Previous period value")
    change: Optional[float] = Field(None, description="Change from previous period")
    change_percent: Optional[float] = Field(None, description="% change from previous")

    # Thresholds
    critical_threshold: Optional[float] = None
    warning_threshold: Optional[float] = None

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.now)
    data_points: int = Field(default=1, description="Number of data points used")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Calculation confidence")

    # Insights
    insights: List[str] = Field(default_factory=list, description="AI-generated insights")
    alerts: List[str] = Field(default_factory=list, description="Threshold alerts")


class KPIDashboard(BaseModel):
    """
    Collection of KPIs for dashboard display
    """
    dashboard_id: str
    name: str
    description: str

    # KPI Results
    kpis: List[KPIResult] = Field(default_factory=list)

    # Summary Statistics
    total_kpis: int = 0
    excellent_count: int = 0
    good_count: int = 0
    warning_count: int = 0
    critical_count: int = 0

    # Alerts
    critical_alerts: List[str] = Field(default_factory=list)
    warning_alerts: List[str] = Field(default_factory=list)

    # Metadata
    case_id: Optional[str] = None
    period: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)


class KPIEngine:
    """
    Business Intelligence KPI Engine
    Calculates, evaluates, and tracks KPIs with thresholds
    """

    def __init__(self):
        """Initialize KPI engine with predefined financial KPIs"""
        self.kpi_definitions: Dict[str, KPIDefinition] = {}
        self._initialize_financial_kpis()
        logger.info("KPI Engine initialized with predefined financial KPIs")

    def _initialize_financial_kpis(self):
        """Initialize standard financial KPIs"""

        # ============================================
        # LIQUIDITY KPIs
        # ============================================

        self.register_kpi(KPIDefinition(
            kpi_id="current_ratio",
            name="Current Ratio",
            description="Ability to pay short-term obligations (Current Assets / Current Liabilities)",
            category=KPICategory.LIQUIDITY,
            formula="Current Assets / Current Liabilities",
            unit="ratio",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=1.0,
            warning_threshold=1.5,
            target=2.0,
            is_higher_better=True,
            icon="💧",
            color="#3b82f6",
            chart_type="gauge"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="quick_ratio",
            name="Quick Ratio (Acid Test)",
            description="Ability to pay short-term obligations with liquid assets",
            category=KPICategory.LIQUIDITY,
            formula="(Current Assets - Inventory) / Current Liabilities",
            unit="ratio",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=0.5,
            warning_threshold=0.8,
            target=1.0,
            is_higher_better=True,
            icon="⚡",
            color="#06b6d4",
            chart_type="gauge"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="cash_ratio",
            name="Cash Ratio",
            description="Most conservative liquidity measure",
            category=KPICategory.LIQUIDITY,
            formula="(Cash + Cash Equivalents) / Current Liabilities",
            unit="ratio",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=0.2,
            warning_threshold=0.3,
            target=0.5,
            is_higher_better=True,
            icon="💵",
            color="#0891b2",
            chart_type="gauge"
        ))

        # ============================================
        # PROFITABILITY KPIs
        # ============================================

        self.register_kpi(KPIDefinition(
            kpi_id="net_profit_margin",
            name="Net Profit Margin",
            description="Net profit as percentage of revenue",
            category=KPICategory.PROFITABILITY,
            formula="(Net Income / Revenue) × 100",
            unit="%",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=0.0,
            warning_threshold=5.0,
            target=10.0,
            is_higher_better=True,
            icon="📈",
            color="#10b981",
            chart_type="line"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="roa",
            name="Return on Assets (ROA)",
            description="How efficiently assets generate profit",
            category=KPICategory.PROFITABILITY,
            formula="(Net Income / Total Assets) × 100",
            unit="%",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=0.0,
            warning_threshold=5.0,
            target=10.0,
            is_higher_better=True,
            icon="💰",
            color="#059669",
            chart_type="line"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="roe",
            name="Return on Equity (ROE)",
            description="Return generated on shareholders' equity",
            category=KPICategory.PROFITABILITY,
            formula="(Net Income / Shareholders' Equity) × 100",
            unit="%",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=0.0,
            warning_threshold=10.0,
            target=15.0,
            is_higher_better=True,
            icon="🎯",
            color="#047857",
            chart_type="line"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="gross_profit_margin",
            name="Gross Profit Margin",
            description="Gross profit as percentage of revenue",
            category=KPICategory.PROFITABILITY,
            formula="(Gross Profit / Revenue) × 100",
            unit="%",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=10.0,
            warning_threshold=20.0,
            target=30.0,
            is_higher_better=True,
            icon="📊",
            color="#22c55e",
            chart_type="line"
        ))

        # ============================================
        # LEVERAGE KPIs
        # ============================================

        self.register_kpi(KPIDefinition(
            kpi_id="debt_to_equity",
            name="Debt-to-Equity Ratio",
            description="Financial leverage measure",
            category=KPICategory.LEVERAGE,
            formula="Total Debt / Total Equity",
            unit="ratio",
            threshold_type=ThresholdType.LESS_THAN,
            critical_threshold=2.0,
            warning_threshold=1.5,
            target=1.0,
            is_higher_better=False,
            icon="⚖️",
            color="#ef4444",
            chart_type="bar"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="debt_ratio",
            name="Debt Ratio",
            description="Proportion of assets financed by debt",
            category=KPICategory.LEVERAGE,
            formula="(Total Debt / Total Assets) × 100",
            unit="%",
            threshold_type=ThresholdType.LESS_THAN,
            critical_threshold=70.0,
            warning_threshold=60.0,
            target=50.0,
            is_higher_better=False,
            icon="📉",
            color="#dc2626",
            chart_type="bar"
        ))

        self.register_kpi(KPIDefinition(
            kpi_id="interest_coverage",
            name="Interest Coverage Ratio",
            description="Ability to pay interest on outstanding debt",
            category=KPICategory.LEVERAGE,
            formula="EBIT / Interest Expense",
            unit="times",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=1.5,
            warning_threshold=2.5,
            target=5.0,
            is_higher_better=True,
            icon="🛡️",
            color="#f97316",
            chart_type="gauge"
        ))

        # ============================================
        # EFFICIENCY KPIs
        # ============================================

        self.register_kpi(KPIDefinition(
            kpi_id="asset_turnover",
            name="Asset Turnover Ratio",
            description="How efficiently assets generate revenue",
            category=KPICategory.EFFICIENCY,
            formula="Revenue / Total Assets",
            unit="times",
            threshold_type=ThresholdType.GREATER_THAN,
            critical_threshold=0.5,
            warning_threshold=0.8,
            target=1.2,
            is_higher_better=True,
            icon="🔄",
            color="#8b5cf6",
            chart_type="line"
        ))

        logger.info(f"Initialized {len(self.kpi_definitions)} financial KPIs")

    def register_kpi(self, kpi_def: KPIDefinition):
        """
        Register a new KPI definition

        Args:
            kpi_def: KPI definition to register
        """
        self.kpi_definitions[kpi_def.kpi_id] = kpi_def
        logger.debug(f"Registered KPI: {kpi_def.kpi_id} - {kpi_def.name}")

    def calculate_kpi(
        self,
        kpi_id: str,
        value: float,
        previous_value: Optional[float] = None,
        custom_target: Optional[float] = None
    ) -> KPIResult:
        """
        Calculate KPI result with status evaluation

        Args:
            kpi_id: KPI identifier
            value: Current KPI value
            previous_value: Previous period value for comparison
            custom_target: Override default target

        Returns:
            KPIResult with calculated status and insights
        """
        if kpi_id not in self.kpi_definitions:
            raise ValueError(f"Unknown KPI: {kpi_id}")

        kpi_def = self.kpi_definitions[kpi_id]

        # Format value for display
        if kpi_def.unit == "%":
            formatted_value = f"{value:.{kpi_def.decimal_places}f}%"
        elif kpi_def.unit == "times":
            formatted_value = f"{value:.{kpi_def.decimal_places}f}×"
        else:
            formatted_value = f"{value:.{kpi_def.decimal_places}f}"

        # Determine target
        target = custom_target if custom_target is not None else kpi_def.target

        # Calculate status
        status, status_message, alerts = self._evaluate_status(value, kpi_def)

        # Calculate comparisons
        target_diff = None
        target_diff_percent = None
        if target is not None:
            target_diff = value - target
            target_diff_percent = ((value - target) / target) * 100 if target != 0 else None

        change = None
        change_percent = None
        if previous_value is not None:
            change = value - previous_value
            change_percent = ((value - previous_value) / previous_value) * 100 if previous_value != 0 else None

        # Generate insights
        insights = self._generate_kpi_insights(value, kpi_def, previous_value, target)

        return KPIResult(
            kpi_id=kpi_id,
            kpi_name=kpi_def.name,
            category=kpi_def.category,
            value=value,
            formatted_value=formatted_value,
            unit=kpi_def.unit,
            status=status,
            status_message=status_message,
            target=target,
            target_diff=target_diff,
            target_diff_percent=target_diff_percent,
            previous_value=previous_value,
            change=change,
            change_percent=change_percent,
            critical_threshold=kpi_def.critical_threshold,
            warning_threshold=kpi_def.warning_threshold,
            insights=insights,
            alerts=alerts
        )

    def _evaluate_status(
        self,
        value: float,
        kpi_def: KPIDefinition
    ) -> tuple[KPIStatus, str, List[str]]:
        """
        Evaluate KPI performance status

        Returns:
            Tuple of (status, message, alerts)
        """
        alerts = []

        if kpi_def.threshold_type == ThresholdType.GREATER_THAN:
            if kpi_def.target and value >= kpi_def.target:
                return (
                    KPIStatus.EXCELLENT,
                    f"Exceeds target of {kpi_def.target:.2f}",
                    []
                )
            elif kpi_def.warning_threshold and value >= kpi_def.warning_threshold:
                return (
                    KPIStatus.GOOD,
                    f"Meets expectations (above {kpi_def.warning_threshold:.2f})",
                    []
                )
            elif kpi_def.critical_threshold and value >= kpi_def.critical_threshold:
                alerts.append(f"⚠️ Below target but above critical threshold")
                return (
                    KPIStatus.WARNING,
                    f"Below target but manageable",
                    alerts
                )
            else:
                alerts.append(f"🚨 CRITICAL: Below {kpi_def.critical_threshold:.2f} threshold")
                return (
                    KPIStatus.CRITICAL,
                    f"Below critical threshold",
                    alerts
                )

        elif kpi_def.threshold_type == ThresholdType.LESS_THAN:
            if kpi_def.target and value <= kpi_def.target:
                return (
                    KPIStatus.EXCELLENT,
                    f"Below target of {kpi_def.target:.2f}",
                    []
                )
            elif kpi_def.warning_threshold and value <= kpi_def.warning_threshold:
                return (
                    KPIStatus.GOOD,
                    f"Meets expectations (below {kpi_def.warning_threshold:.2f})",
                    []
                )
            elif kpi_def.critical_threshold and value <= kpi_def.critical_threshold:
                alerts.append(f"⚠️ Above target but below critical threshold")
                return (
                    KPIStatus.WARNING,
                    f"Above target but manageable",
                    alerts
                )
            else:
                alerts.append(f"🚨 CRITICAL: Above {kpi_def.critical_threshold:.2f} threshold")
                return (
                    KPIStatus.CRITICAL,
                    f"Above critical threshold",
                    alerts
                )

        return (KPIStatus.UNKNOWN, "Insufficient data", [])

    def _generate_kpi_insights(
        self,
        value: float,
        kpi_def: KPIDefinition,
        previous_value: Optional[float],
        target: Optional[float]
    ) -> List[str]:
        """Generate AI-style insights for KPI"""
        insights = []

        # Trend insights
        if previous_value is not None:
            change_pct = ((value - previous_value) / previous_value) * 100 if previous_value != 0 else 0
            if abs(change_pct) > 10:
                direction = "increased" if change_pct > 0 else "decreased"
                good_bad = "positive" if (change_pct > 0) == kpi_def.is_higher_better else "negative"
                insights.append(
                    f"📊 {kpi_def.name} has {direction} by {abs(change_pct):.1f}% - {good_bad} trend"
                )

        # Target insights
        if target is not None:
            diff_pct = ((value - target) / target) * 100 if target != 0 else 0
            if abs(diff_pct) > 5:
                if diff_pct > 0 and kpi_def.is_higher_better:
                    insights.append(f"✅ Performing {abs(diff_pct):.1f}% above target")
                elif diff_pct < 0 and not kpi_def.is_higher_better:
                    insights.append(f"✅ Performing {abs(diff_pct):.1f}% below target")
                else:
                    insights.append(f"⚠️ Off target by {abs(diff_pct):.1f}%")

        return insights

    def calculate_dashboard(
        self,
        metrics: Dict[str, float],
        previous_metrics: Optional[Dict[str, float]] = None,
        case_id: Optional[str] = None,
        period: Optional[str] = None
    ) -> KPIDashboard:
        """
        Calculate complete KPI dashboard

        Args:
            metrics: Current metric values {kpi_id: value}
            previous_metrics: Previous period metrics for comparison
            case_id: Associated case ID
            period: Time period label

        Returns:
            Complete KPI dashboard with all results
        """
        kpi_results = []
        status_counts = {
            KPIStatus.EXCELLENT: 0,
            KPIStatus.GOOD: 0,
            KPIStatus.WARNING: 0,
            KPIStatus.CRITICAL: 0,
            KPIStatus.UNKNOWN: 0
        }
        critical_alerts = []
        warning_alerts = []

        for kpi_id, value in metrics.items():
            if kpi_id not in self.kpi_definitions:
                logger.warning(f"Unknown KPI ID: {kpi_id}, skipping")
                continue

            prev_value = previous_metrics.get(kpi_id) if previous_metrics else None
            result = self.calculate_kpi(kpi_id, value, prev_value)

            kpi_results.append(result)
            status_counts[result.status] += 1

            if result.status == KPIStatus.CRITICAL:
                critical_alerts.extend(result.alerts)
            elif result.status == KPIStatus.WARNING:
                warning_alerts.extend(result.alerts)

        dashboard = KPIDashboard(
            dashboard_id=f"dashboard_{case_id}_{period}" if case_id and period else "dashboard",
            name=f"Financial KPI Dashboard" + (f" - {period}" if period else ""),
            description="Key financial performance indicators with status evaluation",
            kpis=kpi_results,
            total_kpis=len(kpi_results),
            excellent_count=status_counts[KPIStatus.EXCELLENT],
            good_count=status_counts[KPIStatus.GOOD],
            warning_count=status_counts[KPIStatus.WARNING],
            critical_count=status_counts[KPIStatus.CRITICAL],
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts,
            case_id=case_id,
            period=period
        )

        logger.info(
            f"KPI Dashboard calculated: {dashboard.total_kpis} KPIs, "
            f"{dashboard.critical_count} critical, {dashboard.warning_count} warnings"
        )

        return dashboard

    def get_kpi_definition(self, kpi_id: str) -> Optional[KPIDefinition]:
        """Get KPI definition by ID"""
        return self.kpi_definitions.get(kpi_id)

    def list_kpis(self, category: Optional[KPICategory] = None) -> List[KPIDefinition]:
        """
        List all registered KPIs, optionally filtered by category

        Args:
            category: Filter by KPI category

        Returns:
            List of KPI definitions
        """
        kpis = list(self.kpi_definitions.values())
        if category:
            kpis = [kpi for kpi in kpis if kpi.category == category]
        return kpis
