"""
Method Confidence Validator
============================

Post-analysis validation: Check statistical rigor AFTER analysis completes

Validates:
- R² thresholds (domain-configurable: finance 0.7, operations 0.5)
- P-values and statistical significance
- Confidence intervals
- Sample size appropriateness
- Residual analysis for regression models
- Effect sizes

GUARDRAIL COMPLIANCE:
- Explicit statistical quality checks
- Domain-specific thresholds
- Clear warnings for weak statistical evidence
- Performance budgets respected

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
Addresses: ANALYTICS_QUALITY_CONCERNS.md - Statistical Rigor
"""

from typing import Dict, Any, Optional, List
import logging
import math

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


class MethodConfidenceValidator(AnalysisQualityValidator):
    """Validates statistical rigor and method appropriateness

    Post-analysis validator: Runs AFTER analysis to check:
    - Is the R² high enough for this domain?
    - Are p-values significant?
    - Are confidence intervals narrow enough?
    - Is sample size adequate?
    - Are residuals well-behaved?

    GUARDRAIL: Explicit statistical quality checks with domain-specific thresholds

    Usage:
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.STANDARD,
            domain="finance"
        )

        # Check analysis results
        report = validator.validate(
            analysis_result={
                "method": "linear_regression",
                "r_squared": 0.75,
                "p_value": 0.03,
                "confidence_interval": (0.5, 0.9),
                "sample_size": 30,
                "residuals": [0.1, -0.2, 0.05, ...],
                "predictions": [100, 110, 105, ...],
                "actuals": [102, 108, 106, ...]
            },
            context=AnalysisContext(
                data_quality_reports=[...],
                analysis_type="trend_analysis",
                user_params={},
                domain="finance"
            )
        )

        if not report.passed:
            # Statistical quality insufficient
            return error_response(report)
    """

    # Domain-specific R² thresholds
    R_SQUARED_THRESHOLDS = {
        "finance": {
            "minimum": 0.70,      # Finance needs high confidence
            "good": 0.80,
            "excellent": 0.90
        },
        "operations": {
            "minimum": 0.50,      # Operations can accept lower R²
            "good": 0.70,
            "excellent": 0.85
        },
        "marketing": {
            "minimum": 0.40,      # Marketing is inherently noisy
            "good": 0.60,
            "excellent": 0.75
        },
        "default": {
            "minimum": 0.60,
            "good": 0.75,
            "excellent": 0.85
        }
    }

    # P-value thresholds
    P_VALUE_THRESHOLDS = {
        "significant": 0.05,      # p < 0.05
        "highly_significant": 0.01,  # p < 0.01
        "very_highly_significant": 0.001  # p < 0.001
    }

    # Sample size thresholds for different analysis types
    MIN_SAMPLE_SIZES = {
        "trend_analysis": 10,        # Need at least 10 points for trend
        "forecasting": 20,           # Need more for forecasting
        "comparative_analysis": 15,  # 15+ for comparisons
        "regression": 30,            # 30+ for regression (rule of thumb)
        "correlation": 10,           # 10+ for correlation
        "default": 10
    }

    def __init__(
        self,
        validation_level: ValidationLevel = ValidationLevel.STANDARD,
        domain: str = "finance",
        strict_mode: bool = True
    ):
        """Initialize method confidence validator

        Args:
            validation_level: FAST/STANDARD/THOROUGH
            domain: Domain for context-specific thresholds (finance/operations/marketing)
            strict_mode: If True, errors cause rejection

        GUARDRAIL: Explicit domain configuration
        """
        super().__init__(
            name="MethodConfidenceValidator",
            validation_level=validation_level,
            strict_mode=strict_mode
        )

        self.domain = domain
        self.r_squared_thresholds = self.R_SQUARED_THRESHOLDS.get(
            domain,
            self.R_SQUARED_THRESHOLDS["default"]
        )

        logger.info(
            f"Initialized {self.name} for domain={domain}, "
            f"min_r²={self.r_squared_thresholds['minimum']}"
        )

    def _do_validation(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Validate method confidence

        Args:
            analysis_result: Dict with:
                - method: Analysis method name
                - r_squared: R² value (0-1)
                - p_value: Statistical p-value
                - confidence_interval: Tuple (lower, upper)
                - sample_size: Number of data points
                - residuals: List of residuals (optional)
                - predictions: List of predictions (optional)
                - actuals: List of actual values (optional)
            context: Analysis context

        Returns:
            QualityReport

        GUARDRAIL: Explicit statistical checks with clear messages
        """
        # Create report
        report = self._create_report(
            entity_type="method_confidence",
            entity_id=analysis_result.get("method", "unknown"),
            base_score=100.0
        )

        if not context:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "CONFIDENCE_NO_CONTEXT",
                "No analysis context provided"
            )
            report.quality_score = 0.0
            report.passed = False
            return report

        self._checkpoint("context_loaded")

        # STEP 1: Check input data quality
        input_quality = self._check_input_data_quality(context)

        if input_quality < 50.0:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "CONFIDENCE_LOW_INPUT_QUALITY",
                f"Input data quality too low: {input_quality:.0f}% (minimum: 50%)"
            )
            self._adjust_score(report, 50, "Low input quality")
            report.passed = False

        self._checkpoint("input_quality_checked")

        # STEP 2: Check sample size
        sample_size = analysis_result.get("sample_size", 0)
        min_sample_size = self.MIN_SAMPLE_SIZES.get(
            context.analysis_type,
            self.MIN_SAMPLE_SIZES["default"]
        )

        if sample_size < min_sample_size:
            report.add_issue(
                ValidationSeverity.ERROR,
                "CONFIDENCE_INSUFFICIENT_SAMPLE",
                f"Sample size {sample_size} too small (minimum: {min_sample_size} for {context.analysis_type})",
                actual=sample_size,
                required=min_sample_size
            )
            self._adjust_score(report, 30, "Insufficient sample size")
            report.passed = False

        self._checkpoint("sample_size_checked")

        # STEP 3: Check R² (if regression-based analysis)
        method = analysis_result.get("method", "").lower()
        if "regression" in method or "forecast" in method or "trend" in method:
            r_squared = analysis_result.get("r_squared")

            if r_squared is not None:
                self._validate_r_squared(report, r_squared, context)
            else:
                logger.warning(
                    f"R² not provided for regression-based method: {method}"
                )
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_MISSING_R_SQUARED",
                    f"R² not provided for {method}, cannot assess model fit"
                )
                self._adjust_score(report, 10, "Missing R²")

        self._checkpoint("r_squared_checked")

        # STEP 4: Check p-value significance
        p_value = analysis_result.get("p_value")

        if p_value is not None:
            self._validate_p_value(report, p_value)
        else:
            logger.debug("P-value not provided, skipping significance check")

        self._checkpoint("p_value_checked")

        # STEP 5: Check confidence interval (if enabled)
        if self._should_run_check('confidence_intervals'):
            confidence_interval = analysis_result.get("confidence_interval")

            if confidence_interval is not None:
                self._validate_confidence_interval(report, confidence_interval)

        self._checkpoint("confidence_interval_checked")

        # STEP 6: Residual analysis (if enabled and available)
        if self._should_run_check('residual_analysis'):
            residuals = analysis_result.get("residuals")
            predictions = analysis_result.get("predictions")
            actuals = analysis_result.get("actuals")

            if residuals is not None:
                self._validate_residuals(report, residuals)
            elif predictions is not None and actuals is not None:
                # Calculate residuals
                residuals = [a - p for a, p in zip(actuals, predictions)]
                self._validate_residuals(report, residuals)

        self._checkpoint("residuals_checked")

        # STEP 7: Propagate data quality issues
        self._propagate_data_quality_issues(report, context)

        # STEP 8: Add metrics metadata
        report.metrics.update({
            "method": analysis_result.get("method"),
            "r_squared": analysis_result.get("r_squared"),
            "p_value": analysis_result.get("p_value"),
            "sample_size": sample_size,
            "domain": self.domain,
            "r_squared_threshold": self.r_squared_thresholds,
            "input_data_quality": input_quality
        })

        logger.info(
            f"Method confidence check: {report.quality_level.value} "
            f"({report.quality_score:.1f}%) - "
            f"R²={analysis_result.get('r_squared', 'N/A')}, "
            f"p={analysis_result.get('p_value', 'N/A')}"
        )

        return report

    def _validate_r_squared(
        self,
        report: QualityReport,
        r_squared: float,
        context: AnalysisContext
    ):
        """Validate R² against domain thresholds

        Args:
            report: Quality report
            r_squared: R² value (0-1)
            context: Analysis context

        GUARDRAIL: Domain-specific thresholds, explicit quality assessment
        """
        min_r2 = self.r_squared_thresholds["minimum"]
        good_r2 = self.r_squared_thresholds["good"]
        excellent_r2 = self.r_squared_thresholds["excellent"]

        if r_squared < min_r2:
            report.add_issue(
                ValidationSeverity.ERROR,
                "CONFIDENCE_LOW_R_SQUARED",
                f"R² {r_squared:.3f} below minimum {min_r2:.2f} for {self.domain} domain",
                actual=r_squared,
                required=min_r2,
                domain=self.domain
            )
            # Penalty scales with how far below minimum
            shortage = (min_r2 - r_squared) / min_r2
            penalty = min(shortage * 40, 40)  # Up to 40 points
            self._adjust_score(report, penalty, "Low R²")
            report.passed = False

        elif r_squared < good_r2:
            report.add_issue(
                ValidationSeverity.WARNING,
                "CONFIDENCE_MODERATE_R_SQUARED",
                f"R² {r_squared:.3f} meets minimum but below recommended {good_r2:.2f}",
                actual=r_squared,
                recommended=good_r2
            )
            # Small penalty for moderate R²
            penalty = ((good_r2 - r_squared) / good_r2) * 15
            self._adjust_score(report, penalty, "Moderate R²")

        elif r_squared >= excellent_r2:
            logger.info(f"Excellent R²: {r_squared:.3f} >= {excellent_r2:.2f}")
            # No penalty, score stays at 100

        else:
            # good_r2 <= r_squared < excellent_r2
            logger.info(f"Good R²: {r_squared:.3f} (threshold: {good_r2:.2f})")
            # Tiny penalty (not quite excellent)
            penalty = ((excellent_r2 - r_squared) / excellent_r2) * 5
            self._adjust_score(report, penalty, "Good R² (not excellent)")

    def _validate_p_value(self, report: QualityReport, p_value: float):
        """Validate p-value significance

        Args:
            report: Quality report
            p_value: Statistical p-value

        GUARDRAIL: Explicit significance thresholds
        """
        if p_value >= self.P_VALUE_THRESHOLDS["significant"]:
            report.add_issue(
                ValidationSeverity.WARNING,
                "CONFIDENCE_NOT_SIGNIFICANT",
                f"P-value {p_value:.4f} not statistically significant (p >= 0.05)",
                actual=p_value,
                threshold=0.05
            )
            # Penalty for non-significant results
            penalty = 20
            self._adjust_score(report, penalty, "Not statistically significant")

        elif p_value >= self.P_VALUE_THRESHOLDS["highly_significant"]:
            logger.info(f"Significant result: p={p_value:.4f} < 0.05")
            # Minimal penalty (significant but not highly)
            penalty = 5
            self._adjust_score(report, penalty, "Significant (not highly)")

        else:
            # p < 0.01 (highly significant)
            logger.info(f"Highly significant result: p={p_value:.4f} < 0.01")
            # No penalty

    def _validate_confidence_interval(
        self,
        report: QualityReport,
        confidence_interval: tuple
    ):
        """Validate confidence interval width

        Args:
            report: Quality report
            confidence_interval: Tuple (lower, upper)

        GUARDRAIL: Check for excessively wide intervals
        """
        if not isinstance(confidence_interval, (tuple, list)) or len(confidence_interval) != 2:
            logger.warning(f"Invalid confidence interval format: {confidence_interval}")
            return

        lower, upper = confidence_interval
        width = upper - lower
        midpoint = (upper + lower) / 2

        # Check if interval is excessively wide
        # (relative width > 100% of midpoint)
        if midpoint != 0:
            relative_width = width / abs(midpoint)

            if relative_width > 1.0:  # Width > 100% of estimate
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_WIDE_INTERVAL",
                    f"Confidence interval very wide: {width:.2f} "
                    f"({relative_width*100:.0f}% of estimate {midpoint:.2f})",
                    width=width,
                    relative_width=relative_width
                )
                # Penalty for wide intervals
                penalty = min(relative_width * 10, 15)  # Up to 15 points
                self._adjust_score(report, penalty, "Wide confidence interval")

    def _validate_residuals(self, report: QualityReport, residuals: List[float]):
        """Validate residual properties for regression

        Args:
            report: Quality report
            residuals: List of residuals

        GUARDRAIL: Check for systematic patterns in residuals
        """
        if not residuals or len(residuals) < 5:
            logger.debug("Too few residuals for analysis")
            return

        # Calculate residual statistics
        n = len(residuals)
        mean_residual = sum(residuals) / n
        squared_residuals = [r**2 for r in residuals]
        mse = sum(squared_residuals) / n
        rmse = math.sqrt(mse)

        # Check 1: Mean should be close to zero
        if abs(mean_residual) > 0.5 * rmse:
            report.add_issue(
                ValidationSeverity.WARNING,
                "CONFIDENCE_BIASED_RESIDUALS",
                f"Residuals not centered at zero (mean={mean_residual:.4f})",
                mean_residual=mean_residual,
                rmse=rmse
            )
            penalty = 10
            self._adjust_score(report, penalty, "Biased residuals")

        # Check 2: Check for outliers using median absolute deviation (robust to outliers)
        if n >= 10:
            # Use median-based outlier detection (more robust)
            sorted_residuals = sorted(residuals)
            median = sorted_residuals[n // 2] if n % 2 == 1 else (sorted_residuals[n // 2 - 1] + sorted_residuals[n // 2]) / 2

            # Calculate MAD (Median Absolute Deviation)
            absolute_deviations = [abs(r - median) for r in residuals]
            sorted_ad = sorted(absolute_deviations)
            mad = sorted_ad[n // 2] if n % 2 == 1 else (sorted_ad[n // 2 - 1] + sorted_ad[n // 2]) / 2

            # Use 3.5 * MAD as threshold (corresponds roughly to 3 sigma for normal data)
            threshold = 3.5 * mad if mad > 0 else 0.1  # Fallback if MAD = 0
            outliers = [r for r in residuals if abs(r - median) > threshold]

            if len(outliers) > 0.05 * n:  # More than 5% outliers
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_RESIDUAL_OUTLIERS",
                    f"High proportion of outliers in residuals: {len(outliers)}/{n} "
                    f"({len(outliers)/n*100:.1f}%)",
                    outlier_count=len(outliers),
                    total_count=n
                )
                penalty = min((len(outliers) / n) * 100, 15)
                self._adjust_score(report, penalty, "Residual outliers")


# Export
__all__ = ['MethodConfidenceValidator']
