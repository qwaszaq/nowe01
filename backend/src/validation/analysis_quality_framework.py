"""
Analytics Quality Framework
============================

Extends quality_framework.py for analytics validation

Core Principle: Analysis quality = f(data quality, method appropriateness, statistical validity)

Quality Layers for Analytics (Layer 5):
1. Data Sufficiency Validation (pre-flight)
2. Method Confidence Validation (statistical rigor)
3. Statistical Significance Validation (p-values, confidence intervals)
4. Assumption Validation (regression assumptions, etc.)

GUARDRAIL COMPLIANCE:
- All validators have performance budgets
- Two-phase validation (pre-flight + post-analysis)
- Explicit failures (no silent issues)
- Quality scores propagate from data to analysis

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
Addresses: ANALYTICS_QUALITY_CONCERNS.md
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

from src.validation.quality_framework import (
    QualityReport,
    QualityValidator,
    QualityLevel,
    ValidationSeverity,
    ValidationIssue
)
from src.validation.performance_budgets import (
    ValidationLevel,
    PerformanceMonitor,
    BUDGETS,
    get_budget
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Context for analysis quality validation

    Contains all information needed to validate analysis quality:
    - Input data quality reports (from Layers 1-4)
    - Analysis type and parameters
    - Validation level (FAST/STANDARD/THOROUGH)
    - Domain-specific configuration (finance vs operations)

    GUARDRAIL: Full provenance tracking
    """
    data_quality_reports: List[QualityReport]  # From data layer (Layers 1-4)
    analysis_type: str  # "trend_analysis", "forecasting", "comparative_analysis", "ratio_analysis"
    user_params: Dict[str, Any]  # User-provided parameters
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context
    validation_level: ValidationLevel = ValidationLevel.STANDARD  # Performance level
    domain: str = "finance"  # Domain for context-specific thresholds

    def get_average_data_quality(self) -> float:
        """Get average quality score from input data

        Returns:
            Average quality score (0-100), or 0 if no reports

        GUARDRAIL: Explicit handling of no data case
        """
        if not self.data_quality_reports:
            logger.warning("No data quality reports in context")
            return 0.0

        scores = [r.quality_score for r in self.data_quality_reports]
        avg = sum(scores) / len(scores)

        logger.debug(
            f"Average data quality: {avg:.1f}% "
            f"(from {len(scores)} reports)"
        )

        return avg

    def has_low_quality_data(self, threshold: float = 50.0) -> bool:
        """Check if any input data has low quality

        Args:
            threshold: Minimum acceptable quality score

        Returns:
            True if any data below threshold

        GUARDRAIL: Explicit low-quality data detection
        """
        if not self.data_quality_reports:
            return True  # No data = low quality

        for report in self.data_quality_reports:
            if report.quality_score < threshold:
                logger.warning(
                    f"Low quality data detected: {report.entity_id} "
                    f"({report.quality_score:.1f}% < {threshold}%)"
                )
                return True

        return False


@dataclass
class AnalysisQualityReport:
    """Combined quality report for analysis

    Combines multiple quality dimensions:
    - Data quality (input from Layers 1-4)
    - Sufficiency quality (enough data?)
    - Method confidence (statistical rigor)
    - Statistical significance (p-values, R²)
    - Assumption validity (regression assumptions)

    GUARDRAIL: Complete quality breakdown for user
    """
    data_quality: float  # 0-100 (from Layers 1-4)
    sufficiency_quality: float  # 0-100
    method_confidence: float  # 0-100
    statistical_significance: float  # 0-100
    assumption_validity: float  # 0-100
    overall_quality: float  # 0-100 (weighted combination)
    grade: str  # A/B/C/D/F
    reports: List[QualityReport]  # Individual validator reports
    actionable_warnings: List[str]  # User-facing warnings
    performance_stats: Dict[str, Any] = field(default_factory=dict)  # Performance tracking

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses

        GUARDRAIL: All quality information explicit
        """
        return {
            "overall_quality": round(self.overall_quality, 2),
            "grade": self.grade,
            "breakdown": {
                "data_quality": round(self.data_quality, 2),
                "sufficiency_quality": round(self.sufficiency_quality, 2),
                "method_confidence": round(self.method_confidence, 2),
                "statistical_significance": round(self.statistical_significance, 2),
                "assumption_validity": round(self.assumption_validity, 2)
            },
            "warnings": self.actionable_warnings,
            "performance": self.performance_stats,
            "detailed_reports": [r.to_dict() for r in self.reports]
        }


class AnalysisQualityValidator(QualityValidator):
    """Base class for analysis quality validators

    Extends QualityValidator with:
    - Performance monitoring (tiered validation)
    - Two-phase validation support (pre-flight + post)
    - Analysis-specific context

    GUARDRAIL COMPLIANCE:
    - Performance budgets enforced
    - No silent failures
    - Explicit performance tracking
    - Quality propagation from data layer

    Usage:
        class MyValidator(AnalysisQualityValidator):
            def _do_validation(self, analysis_result, context):
                # Check if expensive operation should run
                if not self._should_run_check('expensive_operation'):
                    return report  # Skip in FAST mode

                # ... validation logic ...
                return report

        validator = MyValidator(validation_level=ValidationLevel.STANDARD)
        report = validator.validate(analysis_result, context)
    """

    def __init__(
        self,
        name: str = "AnalysisQualityValidator",
        validation_level: ValidationLevel = ValidationLevel.STANDARD,
        strict_mode: bool = True
    ):
        """Initialize analysis quality validator

        Args:
            name: Validator name
            validation_level: FAST/STANDARD/THOROUGH
            strict_mode: If True, errors cause rejection

        GUARDRAIL: Explicit validation level configuration
        """
        super().__init__(name=name, strict_mode=strict_mode)

        self.validation_level = validation_level
        self.performance_monitor = PerformanceMonitor(validation_level)
        self.budget = get_budget(validation_level)

        logger.info(
            f"Initialized {name} "
            f"(level={validation_level.value}, "
            f"budget={self.budget.max_overhead_ms}ms)"
        )

    def validate(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Validate analysis quality with performance monitoring

        Args:
            analysis_result: Results from analysis (predictions, metrics, etc.)
            context: Analysis context with data quality reports

        Returns:
            QualityReport with validation results

        GUARDRAIL:
        - Performance tracked automatically
        - Budget violations logged explicitly
        - No silent failures
        """
        # Start performance tracking
        self.performance_monitor.start()

        try:
            # Perform validation
            report = self._do_validation(analysis_result, context)

            # Mark validation checkpoint
            self.performance_monitor.checkpoint("validation_complete")

        except Exception as e:
            # GUARDRAIL: Explicit error handling
            logger.error(
                f"{self.name}: Validation failed with exception: {e}",
                exc_info=True
            )

            # Create error report
            report = self._create_report(
                entity_type="analysis",
                entity_id=context.analysis_type if context else "unknown",
                base_score=0.0
            )
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "VALIDATION_EXCEPTION",
                f"Validation failed: {str(e)}"
            )
            report.passed = False

        finally:
            # Record performance stats
            perf_stats = self.performance_monitor.finish()

            # Add performance metadata to report
            if not hasattr(report, 'metadata'):
                report.metadata = {}
            report.metadata['performance'] = perf_stats

            # GUARDRAIL: Warn if budget exceeded
            if not perf_stats.get('within_budget', True):
                logger.warning(
                    f"{self.name}: Performance budget exceeded: "
                    f"{perf_stats['total_ms']:.0f}ms > {perf_stats['budget_ms']}ms"
                )

                # Add performance warning to report
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "PERFORMANCE_BUDGET_EXCEEDED",
                    f"Validation took {perf_stats['total_ms']:.0f}ms "
                    f"(budget: {perf_stats['budget_ms']}ms)",
                    budget_ms=perf_stats['budget_ms'],
                    actual_ms=perf_stats['total_ms']
                )

        return report

    def _do_validation(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Actual validation logic (implemented by subclasses)

        Args:
            analysis_result: Analysis results
            context: Analysis context

        Returns:
            QualityReport

        GUARDRAIL: Must be implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _do_validation()"
        )

    def _should_run_check(self, check_name: str) -> bool:
        """Check if a validation should run based on performance budget

        Args:
            check_name: Name of check (e.g., 'bootstrap_ci', 'statistical_tests')

        Returns:
            True if check enabled at current validation level

        GUARDRAIL: Explicit decision about which checks run
        """
        enabled = self.performance_monitor.should_run_check(check_name)

        if not enabled:
            logger.debug(
                f"{self.name}: Skipping check '{check_name}' "
                f"(disabled in {self.validation_level.value} mode)"
            )

        return enabled

    def _check_input_data_quality(self, context: AnalysisContext) -> float:
        """Check quality of input data from previous layers

        Args:
            context: Analysis context with data quality reports

        Returns:
            Average quality score from input data

        GUARDRAIL: Explicit input quality verification
        """
        if not context or not context.data_quality_reports:
            logger.warning(
                f"{self.name}: No input data quality reports"
            )
            return 0.0

        # Calculate average quality
        avg_quality = context.get_average_data_quality()

        logger.debug(
            f"{self.name}: Input data quality: {avg_quality:.1f}%"
        )

        return avg_quality

    def _propagate_data_quality_issues(
        self,
        report: QualityReport,
        context: AnalysisContext
    ):
        """Propagate quality issues from input data to analysis

        Args:
            report: Analysis quality report
            context: Analysis context with data quality reports

        GUARDRAIL: Quality issues from data layer are never hidden
        """
        if not context or not context.data_quality_reports:
            return

        # Propagate critical and error issues from data layer
        for data_report in context.data_quality_reports:
            for issue in data_report.issues:
                # Only propagate severe issues
                if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]:
                    report.add_issue(
                        ValidationSeverity.WARNING,  # Downgrade to warning in analysis
                        f"INPUT_{issue.code}",
                        f"Input data issue: {issue.message}",
                        source_entity=data_report.entity_id,
                        original_severity=issue.severity.value
                    )

        logger.debug(
            f"{self.name}: Propagated {len(context.data_quality_reports)} "
            f"data quality reports"
        )

    def _checkpoint(self, name: str):
        """Record a performance checkpoint

        Args:
            name: Checkpoint name

        GUARDRAIL: Performance tracking throughout validation
        """
        self.performance_monitor.checkpoint(name)


# Export public API
__all__ = [
    'AnalysisContext',
    'AnalysisQualityReport',
    'AnalysisQualityValidator'
]
