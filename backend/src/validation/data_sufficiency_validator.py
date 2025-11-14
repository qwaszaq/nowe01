"""
Data Sufficiency Validator
===========================

Pre-flight validation: Check if data is sufficient BEFORE running expensive analysis

Validates:
- Minimum period count (time series length)
- Minimum company count (for comparative analysis)
- Required metrics present
- Time series gaps
- Input data quality

GUARDRAIL COMPLIANCE:
- Fast pre-flight checks prevent wasted computation
- Explicit rejection if data insufficient
- Clear error messages about what's missing
- Performance budgets respected

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
Addresses: ANALYTICS_QUALITY_CONCERNS.md - Circular Dependency
"""

from typing import Dict, Any, Optional, List, Set
import logging

from src.validation.analysis_quality_framework import (
    AnalysisQualityValidator,
    AnalysisContext
)
from src.validation.quality_framework import (
    QualityReport,
    ValidationSeverity
)
from src.validation.performance_budgets import ValidationLevel

logger = logging.getLogger(__name__)


class DataSufficiencyValidator(AnalysisQualityValidator):
    """Validates if data is sufficient for analysis type

    Pre-flight validator: Runs BEFORE expensive analysis to check:
    - Enough periods for time series analysis?
    - Enough companies for comparative analysis?
    - Required metrics present?
    - Data quality acceptable?

    GUARDRAIL: Fail fast if data insufficient (saves expensive computation)

    Usage:
        validator = DataSufficiencyValidator(validation_level=ValidationLevel.STANDARD)

        # Check data before running expensive analysis
        report = validator.validate(
            analysis_result={
                "data": financial_data,
                "companies": ["AAPL", "MSFT"],
                "available_metrics": ["revenue", "assets"],
                "periods": [2021, 2022, 2023]
            },
            context=AnalysisContext(
                data_quality_reports=[...],
                analysis_type="trend_analysis",
                user_params={"metric": "revenue"}
            )
        )

        if not report.passed:
            # Don't run analysis - data insufficient
            return error_response(report)
    """

    # Minimum data requirements per analysis type
    MIN_REQUIREMENTS = {
        "trend_analysis": {
            "min_periods": 3,      # Need at least 3 points for trend
            "min_companies": 1,
            "required_metrics": [],
            "recommended_periods": 5
        },
        "forecasting": {
            "min_periods": 5,      # Need history for forecast
            "min_companies": 1,
            "required_metrics": [],
            "recommended_periods": 10
        },
        "comparative_analysis": {
            "min_periods": 1,
            "min_companies": 2,    # Need multiple companies to compare
            "required_metrics": [],
            "recommended_periods": 3
        },
        "ratio_analysis": {
            "min_periods": 1,
            "min_companies": 1,
            "required_metrics": ["revenue", "assets", "equity", "liabilities"],
            "recommended_periods": 3
        },
        "growth_analysis": {
            "min_periods": 2,      # Need at least 2 periods for growth
            "min_companies": 1,
            "required_metrics": [],
            "recommended_periods": 5
        }
    }

    def __init__(
        self,
        validation_level: ValidationLevel = ValidationLevel.STANDARD,
        strict_mode: bool = True
    ):
        """Initialize data sufficiency validator

        Args:
            validation_level: FAST/STANDARD/THOROUGH
            strict_mode: If True, errors cause rejection

        GUARDRAIL: Explicit configuration
        """
        super().__init__(
            name="DataSufficiencyValidator",
            validation_level=validation_level,
            strict_mode=strict_mode
        )

    def _do_validation(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Validate data sufficiency

        Args:
            analysis_result: Dict with:
                - data: List of data points
                - companies: List of company IDs
                - available_metrics: List of available metrics
                - periods: List of periods (years, quarters, etc.)
            context: Analysis context

        Returns:
            QualityReport

        GUARDRAIL: Explicit checks with clear error messages
        """
        # Create report
        report = self._create_report(
            entity_type="data_sufficiency",
            entity_id=context.analysis_type if context else "unknown",
            base_score=100.0
        )

        if not context:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SUFFICIENCY_NO_CONTEXT",
                "No analysis context provided"
            )
            report.quality_score = 0.0
            return report

        analysis_type = context.analysis_type
        requirements = self.MIN_REQUIREMENTS.get(analysis_type)

        if not requirements:
            # Unknown analysis type - use generic requirements
            logger.warning(
                f"Unknown analysis type: {analysis_type}. Using generic requirements."
            )
            requirements = {
                "min_periods": 2,
                "min_companies": 1,
                "required_metrics": [],
                "recommended_periods": 5
            }

        self._checkpoint("requirements_loaded")

        # STEP 1: Check input data quality (fast)
        input_quality = self._check_input_data_quality(context)

        if input_quality < 50.0:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SUFFICIENCY_LOW_INPUT_QUALITY",
                f"Input data quality too low: {input_quality:.0f}% (minimum: 50%)"
            )
            self._adjust_score(report, 50, "Low input quality")
            report.passed = False

        self._checkpoint("input_quality_checked")

        # STEP 2: Check period count
        period_count = self._count_periods(analysis_result)
        min_periods = requirements["min_periods"]
        recommended_periods = requirements["recommended_periods"]

        if period_count < min_periods:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SUFFICIENCY_INSUFFICIENT_PERIODS",
                f"Only {period_count} periods available, need {min_periods} for {analysis_type}",
                actual=period_count,
                required=min_periods
            )
            self._adjust_score(report, 40, "Insufficient periods")
            report.passed = False

        elif period_count < recommended_periods:
            report.add_issue(
                ValidationSeverity.WARNING,
                "SUFFICIENCY_LIMITED_PERIODS",
                f"Only {period_count} periods available, {recommended_periods} recommended for better results",
                actual=period_count,
                recommended=recommended_periods
            )
            # Minor penalty for limited (but acceptable) data
            penalty = ((recommended_periods - period_count) / recommended_periods) * 15
            self._adjust_score(report, penalty, "Limited periods")

        self._checkpoint("periods_checked")

        # STEP 3: Check company count
        company_count = self._count_companies(analysis_result)
        min_companies = requirements["min_companies"]

        if company_count < min_companies:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SUFFICIENCY_INSUFFICIENT_COMPANIES",
                f"Only {company_count} companies, need {min_companies} for {analysis_type}",
                actual=company_count,
                required=min_companies
            )
            self._adjust_score(report, 40, "Insufficient companies")
            report.passed = False

        self._checkpoint("companies_checked")

        # STEP 4: Check required metrics
        missing_metrics = self._check_required_metrics(
            analysis_result,
            requirements["required_metrics"]
        )

        if missing_metrics:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SUFFICIENCY_MISSING_METRICS",
                f"Missing required metrics: {', '.join(missing_metrics)}",
                missing=missing_metrics
            )
            self._adjust_score(report, 30, "Missing metrics")
            report.passed = False

        self._checkpoint("metrics_checked")

        # STEP 5: Check for time series gaps (if enabled)
        if self._should_run_check('data_gaps'):
            gaps = self._check_time_series_gaps(analysis_result)

            if gaps:
                gap_count = len(gaps)
                severity = ValidationSeverity.ERROR if gap_count > 2 else ValidationSeverity.WARNING

                report.add_issue(
                    severity,
                    "SUFFICIENCY_DATA_GAPS",
                    f"Found {gap_count} gaps in time series: {', '.join(gaps[:3])}{'...' if gap_count > 3 else ''}",
                    gaps=gaps,
                    gap_count=gap_count
                )

                # Penalty based on number of gaps
                penalty = min(gap_count * 5, 20)  # Up to 20 points
                self._adjust_score(report, penalty, "Time series gaps")

            self._checkpoint("gaps_checked")

        # STEP 6: Propagate data quality issues
        self._propagate_data_quality_issues(report, context)

        # STEP 7: Add metrics metadata
        report.metrics.update({
            "period_count": period_count,
            "company_count": company_count,
            "missing_metrics": missing_metrics,
            "input_data_quality": input_quality,
            "analysis_type": analysis_type,
            "requirements": requirements
        })

        logger.info(
            f"Data sufficiency check: {report.quality_level.value} "
            f"({report.quality_score:.1f}%) - "
            f"{period_count} periods, {company_count} companies"
        )

        return report

    def _count_periods(self, analysis_result: Dict[str, Any]) -> int:
        """Count number of periods in data

        Args:
            analysis_result: Analysis result dict

        Returns:
            Number of periods

        GUARDRAIL: Explicit counting, handles various data structures
        """
        # Method 1: Explicit periods list
        if "periods" in analysis_result:
            periods = analysis_result["periods"]
            if isinstance(periods, list):
                return len(periods)

        # Method 2: Count data points
        if "data" in analysis_result:
            data = analysis_result["data"]
            if isinstance(data, list):
                return len(data)

        # Method 3: Extract from data dict
        if isinstance(analysis_result, dict) and "data" in analysis_result:
            data = analysis_result["data"]
            if isinstance(data, dict):
                # Might be keyed by year
                return len(data)

        logger.warning("Could not determine period count from analysis_result")
        return 0

    def _count_companies(self, analysis_result: Dict[str, Any]) -> int:
        """Count number of companies in data

        Args:
            analysis_result: Analysis result dict

        Returns:
            Number of companies

        GUARDRAIL: Defaults to 1 if not specified (single company analysis)
        """
        # Method 1: Explicit companies list
        if "companies" in analysis_result:
            companies = analysis_result["companies"]
            if isinstance(companies, list):
                return len(companies)

        # Method 2: Extract from data
        if "data" in analysis_result:
            data = analysis_result["data"]
            if isinstance(data, list) and len(data) > 0:
                # Try to extract unique company IDs
                companies: Set[str] = set()
                for item in data:
                    if isinstance(item, dict):
                        if "company_id" in item:
                            companies.add(item["company_id"])
                        elif "company" in item:
                            companies.add(item["company"])

                if companies:
                    return len(companies)

        # Default: assume single company
        logger.debug("Could not determine company count, assuming 1")
        return 1

    def _check_required_metrics(
        self,
        analysis_result: Dict[str, Any],
        required: List[str]
    ) -> List[str]:
        """Check for missing required metrics

        Args:
            analysis_result: Analysis result dict
            required: List of required metric names

        Returns:
            List of missing metrics

        GUARDRAIL: Explicit list of what's missing
        """
        if not required:
            return []

        # Method 1: Explicit available_metrics list
        if "available_metrics" in analysis_result:
            available = set(analysis_result["available_metrics"])
            missing = [m for m in required if m not in available]
            return missing

        # Method 2: Check first data point
        if "data" in analysis_result:
            data = analysis_result["data"]
            if isinstance(data, list) and len(data) > 0:
                first_item = data[0]
                if isinstance(first_item, dict):
                    available = set(first_item.keys())
                    missing = [m for m in required if m not in available]
                    return missing

        # If we can't determine, assume all missing (conservative)
        logger.warning(
            f"Could not verify metrics, assuming missing: {required}"
        )
        return required

    def _check_time_series_gaps(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Check for gaps in time series data

        Args:
            analysis_result: Analysis result dict

        Returns:
            List of gap descriptions (e.g., ["2021-2023", "2024-2026"])

        GUARDRAIL: Explicit gap identification for user
        """
        # Extract periods
        periods = []

        if "periods" in analysis_result:
            periods = analysis_result["periods"]
        elif "data" in analysis_result:
            data = analysis_result["data"]
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if "year" in item:
                            periods.append(item["year"])
                        elif "period" in item:
                            periods.append(item["period"])

        if len(periods) < 2:
            return []  # Can't detect gaps with < 2 periods

        # Sort periods
        try:
            periods_sorted = sorted(periods)
        except TypeError:
            # Mixed types or non-comparable
            logger.warning("Could not sort periods for gap detection")
            return []

        # Check for gaps
        gaps = []
        for i in range(len(periods_sorted) - 1):
            current = periods_sorted[i]
            next_period = periods_sorted[i + 1]

            # For numeric periods (years)
            if isinstance(current, (int, float)) and isinstance(next_period, (int, float)):
                if next_period - current > 1:
                    gaps.append(f"{current}-{next_period}")

        return gaps


# Export
__all__ = ['DataSufficiencyValidator']
