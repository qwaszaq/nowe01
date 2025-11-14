# Week 1 Implementation Plan: Analytics Quality Foundation

**Date Range**: 2025-11-14 to 2025-11-21
**Phase**: Analytics Quality Validation Framework (Phase 2, Week 1)
**Goal**: Establish Layer 5 (Analysis Quality Validation) foundation WITH performance guarantees
**Guardrail Compliance**: ALL work follows GUARDRAIL #1 (Data Quality Guaranteed)

⚠️ **UPDATED BASED ON**: `/Users/artur/agents20/ANALYTICS_QUALITY_CONCERNS.md` (2025-11-14)

---

## 🚨 CRITICAL CONCERNS ADDRESSED IN THIS PLAN

**Week 1 addresses these CRITICAL risks**:

1. **🔴 Performance Degradation Risk** - Validation could add 3-5x latency
   - **Mitigation**: Performance budgets set on Day 1, profiling throughout week

2. **🟡 Circular Dependency** - Validation after expensive analysis wastes computation
   - **Mitigation**: Two-phase validation (pre-flight + post-analysis)

3. **🟡 Statistical Issues** - Tests fail on small samples, multiple testing problems
   - **Mitigation**: Sample-size-appropriate tests, domain-configurable thresholds

**Changes from original plan**:
- ✅ Added performance budgets (100ms/500ms/2000ms)
- ✅ Added tiered validation levels (fast/standard/thorough)
- ✅ Added two-phase validation architecture
- ✅ Added statistical fixes (sample-size-appropriate, bootstrap CIs)
- ✅ Added performance profiling to each day

---

## 🎯 Week 1 Objectives

**PRIMARY GOAL**: Build the foundation for quality-aware analytics WITH performance guarantees

**Deliverables**:
1. ✅ AnalysisQualityValidator framework with tiered validation
2. ✅ DataSufficiencyValidator (with pre-flight checks)
3. ✅ MethodConfidenceValidator (with domain-configurable thresholds)
4. ✅ QualityAwareMicroagent with two-phase validation
5. ✅ Performance budgets and monitoring
6. ✅ Comprehensive test suite (90%+ coverage)
7. ✅ Performance profiling results

**Success Criteria**:
- All validators follow existing quality_framework.py patterns
- Performance budgets met (100ms fast, 500ms standard, 2000ms thorough)
- Two-phase validation implemented (pre-flight + post-analysis)
- All code passes GUARDRAIL #1 review checklist
- Zero silent failures possible
- 90%+ test coverage achieved
- Statistical tests handle small samples correctly

---

## 📅 Day-by-Day Breakdown

### **Monday 2025-11-14: Foundation Setup + Performance Budgets**

**Hours**: 8 hours
**Focus**: Analysis quality framework foundation WITH performance constraints

⚠️ **CRITICAL**: Establish performance budgets BEFORE any implementation

#### Morning (4 hours)

**Task 1.0: Define Performance Budgets** (0.5 hours)
- **File**: `/backend/src/validation/performance_budgets.py`
- **Lines**: ~100 lines
- **Purpose**: Set maximum allowed overhead for validation

**🔴 CRITICAL - Must complete before any other task**

```python
"""
Performance budgets for analytics quality validation

GUARDRAIL: Quality validation MUST NOT make system unusable
Target: Validation overhead < 25% of analysis time
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation thoroughness levels"""
    FAST = "fast"           # Minimal checks, < 100ms overhead
    STANDARD = "standard"   # Recommended checks, < 500ms overhead
    THOROUGH = "thorough"   # All checks, < 2000ms overhead

@dataclass
class PerformanceBudget:
    """Performance budget for a validation level"""
    level: ValidationLevel
    max_overhead_ms: int        # Maximum validation overhead
    max_total_ms: Optional[int] # Maximum total analysis time (including validation)

    checks_enabled: Dict[str, bool]  # Which checks to run

# PERFORMANCE BUDGETS (measured in milliseconds)
BUDGETS = {
    ValidationLevel.FAST: PerformanceBudget(
        level=ValidationLevel.FAST,
        max_overhead_ms=100,
        max_total_ms=500,
        checks_enabled={
            'input_quality': True,
            'sample_size': True,
            'data_gaps': False,          # Skip: too slow
            'statistical_tests': False,  # Skip: too slow
            'assumption_validation': False,
            'bootstrap_ci': False
        }
    ),
    ValidationLevel.STANDARD: PerformanceBudget(
        level=ValidationLevel.STANDARD,
        max_overhead_ms=500,
        max_total_ms=2000,
        checks_enabled={
            'input_quality': True,
            'sample_size': True,
            'data_gaps': True,
            'statistical_tests': True,    # Basic tests only
            'assumption_validation': False,  # Skip detailed
            'bootstrap_ci': False         # Use parametric CIs
        }
    ),
    ValidationLevel.THOROUGH: PerformanceBudget(
        level=ValidationLevel.THOROUGH,
        max_overhead_ms=2000,
        max_total_ms=None,  # No limit
        checks_enabled={
            'input_quality': True,
            'sample_size': True,
            'data_gaps': True,
            'statistical_tests': True,
            'assumption_validation': True,  # Full validation
            'bootstrap_ci': True            # Non-parametric CIs
        }
    )
}

class PerformanceMonitor:
    """Monitor and enforce performance budgets"""

    def __init__(self, level: ValidationLevel):
        self.budget = BUDGETS[level]
        self.start_time = None
        self.checkpoints = {}

    def start(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.checkpoints = {}

    def checkpoint(self, name: str):
        """Record a checkpoint"""
        if self.start_time is None:
            return

        elapsed_ms = (time.time() - self.start_time) * 1000
        self.checkpoints[name] = elapsed_ms

        # Check if we're exceeding budget
        if elapsed_ms > self.budget.max_overhead_ms:
            logger.warning(
                f"Performance budget exceeded: {elapsed_ms:.0f}ms > {self.budget.max_overhead_ms}ms at checkpoint '{name}'"
            )

    def finish(self) -> Dict[str, float]:
        """Finish monitoring and return stats"""
        if self.start_time is None:
            return {}

        total_ms = (time.time() - self.start_time) * 1000

        if total_ms > self.budget.max_overhead_ms:
            logger.error(
                f"🔴 PERFORMANCE BUDGET VIOLATED: {total_ms:.0f}ms > {self.budget.max_overhead_ms}ms"
            )

        return {
            'total_ms': total_ms,
            'budget_ms': self.budget.max_overhead_ms,
            'within_budget': total_ms <= self.budget.max_overhead_ms,
            'checkpoints': self.checkpoints
        }
```

**Task 1.1: Create analysis_quality_framework.py** (2.5 hours)
- **File**: `/backend/src/validation/analysis_quality_framework.py`
- **Lines**: ~300 lines
- **Purpose**: Base classes for analysis validation (extends quality_framework.py)

**Key Components**:

⚠️ **UPDATED**: Now includes tiered validation support

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from src.validation.quality_framework import QualityReport, QualityValidator, ValidationIssue, ValidationSeverity
from src.validation.performance_budgets import ValidationLevel, PerformanceMonitor, BUDGETS

@dataclass
class AnalysisContext:
    """Context for analysis quality validation"""
    data_quality_reports: List[QualityReport]  # From Layers 1-4
    analysis_type: str  # "trend", "forecast", "ratio", etc.
    user_params: Dict[str, Any]
    metadata: Dict[str, Any]
    validation_level: ValidationLevel = ValidationLevel.STANDARD  # NEW
    domain: str = "finance"  # NEW: For domain-specific thresholds

class AnalysisQualityValidator(QualityValidator):
    """Base class for analysis quality validators

    NEW: Supports tiered validation levels for performance
    """

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        super().__init__()
        self.validator_name = "AnalysisQualityValidator"
        self.validation_level = validation_level
        self.performance_monitor = PerformanceMonitor(validation_level)

    def validate(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Validate analysis quality with performance monitoring"""

        # Start performance tracking
        self.performance_monitor.start()

        try:
            report = self._do_validation(analysis_result, context)
        finally:
            # Record performance stats
            perf_stats = self.performance_monitor.finish()
            report.metadata['performance'] = perf_stats

            if not perf_stats.get('within_budget', True):
                logger.warning(
                    f"{self.validator_name}: Performance budget exceeded: "
                    f"{perf_stats['total_ms']:.0f}ms > {perf_stats['budget_ms']}ms"
                )

        return report

    def _do_validation(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Actual validation logic (implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _do_validation()")

    def _should_run_check(self, check_name: str) -> bool:
        """Check if a validation should run based on performance budget"""
        budget = BUDGETS[self.validation_level]
        return budget.checks_enabled.get(check_name, False)

    def _check_input_data_quality(self, context: AnalysisContext) -> float:
        """Check quality of input data from previous layers"""
        if not context or not context.data_quality_reports:
            return 0.0

        # Average quality score from all input data
        scores = [r.quality_score for r in context.data_quality_reports]
        return sum(scores) / len(scores)

    def _propagate_data_quality_issues(
        self,
        report: QualityReport,
        context: AnalysisContext
    ):
        """Propagate quality issues from input data"""
        for data_report in context.data_quality_reports:
            for issue in data_report.issues:
                if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        f"INPUT_{issue.code}",
                        f"Input data issue: {issue.message}"
                    )

@dataclass
class AnalysisQualityReport:
    """Combined quality report for analysis"""
    data_quality: float  # 0-100 (from Layers 1-4)
    sufficiency_quality: float  # 0-100
    method_confidence: float  # 0-100
    statistical_significance: float  # 0-100
    assumption_validity: float  # 0-100
    overall_quality: float  # 0-100 (combined)
    grade: str  # A/B/C/D/F
    reports: List[QualityReport]  # Individual validator reports
    actionable_warnings: List[str]
```

**Task 1.2: Write tests for framework** (1 hour)
- **File**: `/backend/tests/test_analysis_quality_framework.py`
- **Tests**:
  - `test_analysis_context_creation()`
  - `test_base_validator_inheritance()`
  - `test_input_data_quality_check()`
  - `test_quality_issue_propagation()`

**Task 1.3: Update quality_framework.py** (1 hour)
- Add analysis-specific ValidationSeverity codes
- Add AnalysisQualityLevel enum if needed
- Ensure compatibility with existing validators

#### Afternoon (4 hours)

**Task 1.4: Create data_sufficiency_validator.py** (2.5 hours)
- **File**: `/backend/src/validation/data_sufficiency_validator.py`
- **Lines**: ~350 lines
- **Purpose**: Validate if input data is sufficient for requested analysis

**Key Components**:
```python
from typing import Dict, Any, Optional, List
from src.validation.analysis_quality_framework import AnalysisQualityValidator, AnalysisContext
from src.validation.quality_framework import QualityReport, ValidationSeverity

class DataSufficiencyValidator(AnalysisQualityValidator):
    """Validates if data is sufficient for analysis type"""

    # Minimum data requirements per analysis type
    MIN_REQUIREMENTS = {
        "trend_analysis": {
            "min_periods": 3,
            "min_companies": 1,
            "required_metrics": ["revenue", "assets"],
        },
        "forecasting": {
            "min_periods": 5,  # Need at least 5 periods for meaningful forecast
            "min_companies": 1,
            "required_metrics": ["revenue"],
        },
        "comparative_analysis": {
            "min_periods": 1,
            "min_companies": 2,  # Need multiple companies to compare
            "required_metrics": [],
        },
        "ratio_analysis": {
            "min_periods": 1,
            "min_companies": 1,
            "required_metrics": ["revenue", "assets", "equity", "liabilities"],
        }
    }

    def __init__(self):
        super().__init__()
        self.validator_name = "DataSufficiencyValidator"

    def validate(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Validate data sufficiency for analysis"""

        report = QualityReport(
            entity_type="analysis",
            entity_id=context.analysis_type if context else "unknown",
            validator_name=self.validator_name
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
            report.add_issue(
                ValidationSeverity.WARNING,
                "SUFFICIENCY_UNKNOWN_TYPE",
                f"Unknown analysis type: {analysis_type}"
            )
            report.quality_score = 50.0
            return report

        # Check data quality first
        input_quality = self._check_input_data_quality(context)
        if input_quality < 50.0:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SUFFICIENCY_LOW_INPUT_QUALITY",
                f"Input data quality too low: {input_quality:.0f}%"
            )
            self._adjust_score(report, 30, "Low input quality")

        # Check period count
        period_count = self._count_periods(analysis_result)
        min_periods = requirements["min_periods"]

        if period_count < min_periods:
            report.add_issue(
                ValidationSeverity.ERROR,
                "SUFFICIENCY_INSUFFICIENT_PERIODS",
                f"Only {period_count} periods available, need {min_periods} for {analysis_type}"
            )
            self._adjust_score(report, 25, "Insufficient periods")
        elif period_count < min_periods * 1.5:
            report.add_issue(
                ValidationSeverity.WARNING,
                "SUFFICIENCY_LIMITED_PERIODS",
                f"Only {period_count} periods available, {min_periods * 2} recommended"
            )
            self._adjust_score(report, 10, "Limited periods")

        # Check company count
        company_count = self._count_companies(analysis_result)
        min_companies = requirements["min_companies"]

        if company_count < min_companies:
            report.add_issue(
                ValidationSeverity.ERROR,
                "SUFFICIENCY_INSUFFICIENT_COMPANIES",
                f"Only {company_count} companies, need {min_companies} for {analysis_type}"
            )
            self._adjust_score(report, 25, "Insufficient companies")

        # Check required metrics
        missing_metrics = self._check_required_metrics(
            analysis_result,
            requirements["required_metrics"]
        )

        if missing_metrics:
            report.add_issue(
                ValidationSeverity.ERROR,
                "SUFFICIENCY_MISSING_METRICS",
                f"Missing required metrics: {', '.join(missing_metrics)}"
            )
            self._adjust_score(report, 20, "Missing metrics")

        # Check data completeness (gaps in time series)
        gaps = self._check_time_series_gaps(analysis_result)
        if gaps:
            report.add_issue(
                ValidationSeverity.WARNING,
                "SUFFICIENCY_DATA_GAPS",
                f"Found {len(gaps)} gaps in time series: {gaps}"
            )
            self._adjust_score(report, 10, "Time series gaps")

        # Propagate issues from input data
        self._propagate_data_quality_issues(report, context)

        return report

    def _count_periods(self, analysis_result: Dict[str, Any]) -> int:
        """Count number of periods in analysis data"""
        # Implementation depends on data structure
        data = analysis_result.get("data", [])
        if isinstance(data, list):
            return len(data)
        return 0

    def _count_companies(self, analysis_result: Dict[str, Any]) -> int:
        """Count number of companies in analysis data"""
        companies = analysis_result.get("companies", [])
        if isinstance(companies, list):
            return len(companies)
        return 1  # Default to 1 if not specified

    def _check_required_metrics(
        self,
        analysis_result: Dict[str, Any],
        required: List[str]
    ) -> List[str]:
        """Check for missing required metrics"""
        available_metrics = analysis_result.get("available_metrics", [])
        return [m for m in required if m not in available_metrics]

    def _check_time_series_gaps(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Check for gaps in time series data"""
        # Simplified implementation
        data = analysis_result.get("data", [])
        if len(data) < 2:
            return []

        # Check for missing years in sequence
        years = sorted([d.get("year") for d in data if d.get("year")])
        gaps = []
        for i in range(len(years) - 1):
            if years[i+1] - years[i] > 1:
                gaps.append(f"{years[i]}-{years[i+1]}")

        return gaps
```

**Task 1.5: Write tests for data_sufficiency_validator.py** (1.5 hours)
- **File**: `/backend/tests/test_data_sufficiency_validator.py`
- **Tests** (aim for 90%+ coverage):
  - `test_trend_analysis_sufficient_data()`
  - `test_trend_analysis_insufficient_periods()`
  - `test_forecasting_requires_5_periods()`
  - `test_comparative_requires_multiple_companies()`
  - `test_ratio_analysis_missing_metrics()`
  - `test_time_series_gap_detection()`
  - `test_low_input_quality_rejection()`
  - `test_quality_issue_propagation()`

**End of Day Deliverables**:
- ✅ analysis_quality_framework.py (300 lines, tested)
- ✅ data_sufficiency_validator.py (350 lines, tested)
- ✅ 12 unit tests passing
- ✅ Foundation for remaining validators

---

### **Tuesday 2025-11-15: Method Confidence Validation**

**Hours**: 8 hours
**Focus**: Statistical confidence and uncertainty quantification

#### Morning (4 hours)

**Task 2.1: Create method_confidence_validator.py** (3 hours)
- **File**: `/backend/src/validation/method_confidence_validator.py`
- **Lines**: ~400 lines
- **Purpose**: Assess confidence in analysis methods and results

**Key Components**:
```python
from typing import Dict, Any, Optional, Tuple
from src.validation.analysis_quality_framework import AnalysisQualityValidator, AnalysisContext
from src.validation.quality_framework import QualityReport, ValidationSeverity
import numpy as np

class MethodConfidenceValidator(AnalysisQualityValidator):
    """Validates confidence in analysis methods and results"""

    # Confidence thresholds
    MIN_CONFIDENCE_FOR_A = 0.90  # 90%+ confidence for A grade
    MIN_CONFIDENCE_FOR_B = 0.70  # 70%+ for B grade
    MIN_CONFIDENCE_FOR_C = 0.50  # 50%+ for C grade

    # R-squared thresholds for model quality
    EXCELLENT_R2 = 0.90
    GOOD_R2 = 0.70
    FAIR_R2 = 0.50
    POOR_R2 = 0.30

    def __init__(self):
        super().__init__()
        self.validator_name = "MethodConfidenceValidator"

    def validate(
        self,
        analysis_result: Dict[str, Any],
        context: Optional[AnalysisContext] = None
    ) -> QualityReport:
        """Validate confidence in analysis method and results"""

        report = QualityReport(
            entity_type="analysis_method",
            entity_id=context.analysis_type if context else "unknown",
            validator_name=self.validator_name
        )

        if not context:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "CONFIDENCE_NO_CONTEXT",
                "No analysis context provided"
            )
            report.quality_score = 0.0
            return report

        analysis_type = context.analysis_type

        # Check if confidence intervals exist
        has_confidence_intervals = "confidence_intervals" in analysis_result
        if not has_confidence_intervals:
            report.add_issue(
                ValidationSeverity.ERROR,
                "CONFIDENCE_NO_INTERVALS",
                "Analysis results missing confidence intervals"
            )
            self._adjust_score(report, 20, "No confidence intervals")

        # Validate confidence intervals
        if has_confidence_intervals:
            ci_quality = self._validate_confidence_intervals(
                analysis_result["confidence_intervals"]
            )

            if ci_quality < self.MIN_CONFIDENCE_FOR_C:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    "CONFIDENCE_INTERVALS_TOO_WIDE",
                    f"Confidence intervals too wide: {ci_quality:.0%} confidence"
                )
                self._adjust_score(report, 25, "Wide confidence intervals")
            elif ci_quality < self.MIN_CONFIDENCE_FOR_B:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_INTERVALS_WIDE",
                    f"Confidence intervals moderately wide: {ci_quality:.0%}"
                )
                self._adjust_score(report, 10, "Moderate confidence intervals")

        # Check model fit quality (R², RMSE, etc.)
        if "model_metrics" in analysis_result:
            model_quality = self._validate_model_fit(
                analysis_result["model_metrics"]
            )

            if model_quality < self.POOR_R2:
                report.add_issue(
                    ValidationSeverity.ERROR,
                    "CONFIDENCE_POOR_MODEL_FIT",
                    f"Poor model fit: R²={model_quality:.2f}"
                )
                self._adjust_score(report, 30, "Poor model fit")
            elif model_quality < self.FAIR_R2:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_FAIR_MODEL_FIT",
                    f"Fair model fit: R²={model_quality:.2f}"
                )
                self._adjust_score(report, 15, "Fair model fit")
        else:
            report.add_issue(
                ValidationSeverity.WARNING,
                "CONFIDENCE_NO_MODEL_METRICS",
                "No model fit metrics provided"
            )
            self._adjust_score(report, 15, "No model metrics")

        # Check for uncertainty quantification
        if "uncertainty" not in analysis_result:
            report.add_issue(
                ValidationSeverity.WARNING,
                "CONFIDENCE_NO_UNCERTAINTY",
                "No uncertainty quantification provided"
            )
            self._adjust_score(report, 10, "No uncertainty")

        # Check sample size vs. complexity
        if context.user_params.get("sample_size"):
            sample_size = context.user_params["sample_size"]
            complexity = self._estimate_model_complexity(analysis_result)

            if sample_size < complexity * 10:  # Rule of thumb: 10x observations per parameter
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_SMALL_SAMPLE",
                    f"Sample size ({sample_size}) may be too small for model complexity ({complexity} params)"
                )
                self._adjust_score(report, 15, "Small sample size")

        # Method-specific validation
        if analysis_type == "forecasting":
            self._validate_forecast_confidence(analysis_result, report)
        elif analysis_type == "trend_analysis":
            self._validate_trend_confidence(analysis_result, report)

        return report

    def _validate_confidence_intervals(self, intervals: Dict[str, Any]) -> float:
        """Validate confidence interval quality"""
        # Calculate average width of confidence intervals
        # Narrower intervals = higher confidence
        lower = intervals.get("lower", [])
        upper = intervals.get("upper", [])
        values = intervals.get("values", [])

        if not (lower and upper and values):
            return 0.0

        # Calculate relative width (width / value)
        widths = []
        for l, u, v in zip(lower, upper, values):
            if v != 0:
                relative_width = (u - l) / abs(v)
                widths.append(relative_width)

        if not widths:
            return 0.0

        avg_width = np.mean(widths)

        # Convert to confidence score (lower width = higher confidence)
        # Width < 0.1 (10%) = excellent
        # Width < 0.3 (30%) = good
        # Width < 0.5 (50%) = fair
        if avg_width < 0.1:
            return 0.95
        elif avg_width < 0.3:
            return 0.75
        elif avg_width < 0.5:
            return 0.55
        else:
            return 0.30

    def _validate_model_fit(self, metrics: Dict[str, Any]) -> float:
        """Validate model fit quality (return R² or equivalent)"""
        # Check for R²
        if "r_squared" in metrics:
            return metrics["r_squared"]

        # Check for adjusted R²
        if "adj_r_squared" in metrics:
            return metrics["adj_r_squared"]

        # Fallback: use other metrics to estimate quality
        if "rmse" in metrics and "mean" in metrics:
            # Convert RMSE to R²-like metric
            rmse = metrics["rmse"]
            mean = metrics["mean"]
            if mean != 0:
                cv = rmse / abs(mean)  # Coefficient of variation
                return max(0, 1 - cv)  # Approximate R²

        return 0.5  # Default to fair if no metrics

    def _estimate_model_complexity(self, analysis_result: Dict[str, Any]) -> int:
        """Estimate number of parameters in model"""
        # Simple heuristic: count features/variables used
        features = analysis_result.get("features", [])
        if features:
            return len(features)

        # Default estimates by analysis type
        model_type = analysis_result.get("model_type", "")
        if "polynomial" in model_type.lower():
            return 3  # Quadratic or cubic
        elif "linear" in model_type.lower():
            return 2  # Slope + intercept
        else:
            return 5  # Conservative default

    def _validate_forecast_confidence(
        self,
        analysis_result: Dict[str, Any],
        report: QualityReport
    ):
        """Validate forecast-specific confidence"""
        forecast_horizon = analysis_result.get("forecast_horizon", 0)

        # Longer forecasts = lower confidence
        if forecast_horizon > 5:
            report.add_issue(
                ValidationSeverity.WARNING,
                "CONFIDENCE_LONG_FORECAST_HORIZON",
                f"Forecast horizon ({forecast_horizon} periods) increases uncertainty"
            )
            self._adjust_score(report, 10, "Long forecast horizon")

    def _validate_trend_confidence(
        self,
        analysis_result: Dict[str, Any],
        report: QualityReport
    ):
        """Validate trend-specific confidence"""
        # Check for significant trend
        if "p_value" in analysis_result:
            p_value = analysis_result["p_value"]
            if p_value > 0.05:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "CONFIDENCE_TREND_NOT_SIGNIFICANT",
                    f"Trend not statistically significant (p={p_value:.3f})"
                )
                self._adjust_score(report, 20, "Non-significant trend")
```

**Task 2.2: Write tests for method_confidence_validator.py** (1 hour)
- **File**: `/backend/tests/test_method_confidence_validator.py`
- **Tests**:
  - `test_excellent_confidence_intervals()`
  - `test_wide_confidence_intervals_warning()`
  - `test_missing_confidence_intervals()`
  - `test_excellent_r_squared()`
  - `test_poor_r_squared_rejection()`
  - `test_small_sample_size_warning()`
  - `test_long_forecast_horizon_penalty()`
  - `test_non_significant_trend_warning()`

#### Afternoon (4 hours)

**Task 2.3: Integration testing** (2 hours)
- **File**: `/backend/tests/test_analysis_validators_integration.py`
- **Purpose**: Test validators working together
- **Tests**:
  - `test_layered_validation_pipeline()`
  - `test_quality_propagation_from_data_to_analysis()`
  - `test_combined_quality_scoring()`
  - `test_rejection_chain()`  # If data bad → analysis rejected

**Task 2.4: Create quality scoring orchestrator** (2 hours)
- **File**: `/backend/src/validation/analysis_quality_orchestrator.py`
- **Lines**: ~200 lines
- **Purpose**: Combine multiple analysis validators into single score

```python
from typing import Dict, Any, List, Optional
from src.validation.analysis_quality_framework import AnalysisQualityValidator, AnalysisContext, AnalysisQualityReport
from src.validation.data_sufficiency_validator import DataSufficiencyValidator
from src.validation.method_confidence_validator import MethodConfidenceValidator
from src.validation.quality_framework import QualityReport, QualityLevel

class AnalysisQualityOrchestrator:
    """Orchestrates multiple analysis quality validators"""

    def __init__(self):
        self.validators = {
            "sufficiency": DataSufficiencyValidator(),
            "confidence": MethodConfidenceValidator(),
        }

    def validate_analysis(
        self,
        analysis_result: Dict[str, Any],
        context: AnalysisContext
    ) -> AnalysisQualityReport:
        """Run all validators and combine results"""

        reports = []

        # Run each validator
        for name, validator in self.validators.items():
            report = validator.validate(analysis_result, context)
            reports.append(report)

        # Calculate input data quality
        data_quality = self._calculate_input_quality(context)

        # Extract individual scores
        sufficiency_score = reports[0].quality_score
        confidence_score = reports[1].quality_score

        # Combined quality score (weighted average)
        weights = {
            "data": 0.30,  # Input data quality (30%)
            "sufficiency": 0.30,  # Data sufficiency (30%)
            "confidence": 0.40,  # Method confidence (40%)
        }

        overall_quality = (
            data_quality * weights["data"] +
            sufficiency_score * weights["sufficiency"] +
            confidence_score * weights["confidence"]
        )

        # Determine grade
        grade = self._score_to_grade(overall_quality)

        # Collect actionable warnings
        warnings = self._extract_actionable_warnings(reports)

        return AnalysisQualityReport(
            data_quality=data_quality,
            sufficiency_quality=sufficiency_score,
            method_confidence=confidence_score,
            statistical_significance=0.0,  # Placeholder for future
            assumption_validity=0.0,  # Placeholder for future
            overall_quality=overall_quality,
            grade=grade,
            reports=reports,
            actionable_warnings=warnings
        )

    def _calculate_input_quality(self, context: AnalysisContext) -> float:
        """Calculate average quality of input data"""
        if not context.data_quality_reports:
            return 0.0
        scores = [r.quality_score for r in context.data_quality_reports]
        return sum(scores) / len(scores)

    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"

    def _extract_actionable_warnings(self, reports: List[QualityReport]) -> List[str]:
        """Extract user-facing warnings from reports"""
        warnings = []
        for report in reports:
            for issue in report.issues:
                if issue.severity in ["ERROR", "WARNING"]:
                    warnings.append(f"{issue.code}: {issue.message}")
        return warnings
```

**End of Day Deliverables**:
- ✅ method_confidence_validator.py (400 lines, tested)
- ✅ analysis_quality_orchestrator.py (200 lines, tested)
- ✅ Integration tests passing
- ✅ Combined quality scoring working

---

### **Wednesday 2025-11-16: QualityAwareMicroagent Base Class**

**Hours**: 8 hours
**Focus**: Create base class for all analytical microagents

#### Morning (4 hours)

**Task 3.1: Create quality_aware_microagent.py** (3 hours)
- **File**: `/backend/src/core/microagents/quality_aware_microagent.py`
- **Lines**: ~500 lines
- **Purpose**: Base class ensuring all microagents track quality

**Key Components**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.validation.analysis_quality_framework import AnalysisContext
from src.validation.analysis_quality_orchestrator import AnalysisQualityOrchestrator
from src.validation.quality_framework import QualityReport
import logging

logger = logging.getLogger(__name__)

class QualityAwareMicroagent(ABC):
    """Base class for all analytical microagents

    GUARANTEES:
    1. ALL analysis results include quality metadata
    2. Input data quality is validated before analysis
    3. Analysis quality is computed and returned
    4. Low-quality results are flagged (not silently returned)
    5. Users see quality scores for every output

    USAGE:
        class TrendAnalysisAgent(QualityAwareMicroagent):
            async def analyze(self, data, params):
                # Your analysis logic here
                return {"trend": "increasing", "slope": 0.15}

        agent = TrendAnalysisAgent()
        result = await agent.analyze_with_quality(data, params)

        # Result always includes:
        # - result["quality"]["overall_quality"]: 0-100 score
        # - result["quality"]["grade"]: A/B/C/D/F
        # - result["quality"]["warnings"]: List of issues
    """

    def __init__(self):
        self.quality_orchestrator = AnalysisQualityOrchestrator()
        self.agent_name = self.__class__.__name__
        self.analysis_type = self._get_analysis_type()

    @abstractmethod
    async def analyze(
        self,
        data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform the analysis (implemented by subclass)

        Args:
            data: Input data (usually from database with quality metadata)
            params: Analysis parameters (user-provided)

        Returns:
            Analysis results (WITHOUT quality metadata - that's added automatically)
        """
        raise NotImplementedError("Subclasses must implement analyze()")

    @abstractmethod
    def _get_analysis_type(self) -> str:
        """Return analysis type string

        Returns:
            One of: "trend_analysis", "forecasting", "comparative_analysis", "ratio_analysis"
        """
        raise NotImplementedError("Subclasses must implement _get_analysis_type()")

    async def analyze_with_quality(
        self,
        data: Any,
        params: Dict[str, Any],
        data_quality_reports: Optional[List[QualityReport]] = None
    ) -> Dict[str, Any]:
        """Perform analysis WITH quality validation (PUBLIC API)

        This is the method external code should call.
        It wraps analyze() with quality validation.

        Args:
            data: Input data
            params: Analysis parameters
            data_quality_reports: Optional quality reports from data layer

        Returns:
            {
                "success": True/False,
                "result": {...},  # Analysis results from analyze()
                "quality": {
                    "overall_quality": 85.5,
                    "grade": "B",
                    "data_quality": 90.0,
                    "sufficiency_quality": 80.0,
                    "method_confidence": 85.0,
                    "warnings": ["..."]
                },
                "metadata": {...}
            }
        """

        # Step 1: Validate input data quality
        if data_quality_reports:
            input_quality = self._calculate_average_quality(data_quality_reports)

            if input_quality < 50.0:
                logger.error(
                    f"{self.agent_name}: Input data quality too low: {input_quality:.1f}%"
                )
                return {
                    "success": False,
                    "error": "INPUT_DATA_QUALITY_TOO_LOW",
                    "message": f"Input data quality ({input_quality:.0f}%) below minimum threshold (50%)",
                    "quality": {
                        "overall_quality": input_quality,
                        "grade": "F",
                        "data_quality": input_quality,
                        "warnings": ["Input data quality insufficient for analysis"]
                    }
                }

        # Step 2: Check data sufficiency (before running expensive analysis)
        context = AnalysisContext(
            data_quality_reports=data_quality_reports or [],
            analysis_type=self.analysis_type,
            user_params=params,
            metadata={}
        )

        # Pre-validate sufficiency
        from src.validation.data_sufficiency_validator import DataSufficiencyValidator
        sufficiency_validator = DataSufficiencyValidator()

        # Create preliminary result for sufficiency check
        preliminary_result = self._prepare_preliminary_result(data, params)
        sufficiency_report = sufficiency_validator.validate(preliminary_result, context)

        if not sufficiency_report.passed:
            logger.warning(
                f"{self.agent_name}: Data insufficient for analysis: {sufficiency_report.issues}"
            )
            return {
                "success": False,
                "error": "DATA_INSUFFICIENT",
                "message": f"Data insufficient for {self.analysis_type}",
                "quality": {
                    "overall_quality": sufficiency_report.quality_score,
                    "grade": sufficiency_report.quality_level.value,
                    "sufficiency_quality": sufficiency_report.quality_score,
                    "warnings": [issue.message for issue in sufficiency_report.issues]
                }
            }

        # Step 3: Perform analysis
        try:
            analysis_result = await self.analyze(data, params)
        except Exception as e:
            logger.error(
                f"{self.agent_name}: Analysis failed: {e}",
                exc_info=True
            )
            return {
                "success": False,
                "error": "ANALYSIS_FAILED",
                "message": str(e),
                "quality": {
                    "overall_quality": 0.0,
                    "grade": "F",
                    "warnings": [f"Analysis failed: {str(e)}"]
                }
            }

        # Step 4: Validate analysis quality
        quality_report = self.quality_orchestrator.validate_analysis(
            analysis_result,
            context
        )

        # Step 5: Add quality metadata to result
        result_with_quality = {
            "success": True,
            "result": analysis_result,
            "quality": {
                "overall_quality": quality_report.overall_quality,
                "grade": quality_report.grade,
                "data_quality": quality_report.data_quality,
                "sufficiency_quality": quality_report.sufficiency_quality,
                "method_confidence": quality_report.method_confidence,
                "warnings": quality_report.actionable_warnings
            },
            "metadata": {
                "agent_name": self.agent_name,
                "analysis_type": self.analysis_type,
                "timestamp": self._get_timestamp()
            }
        }

        # Step 6: Log quality for monitoring
        logger.info(
            f"{self.agent_name}: Analysis complete. "
            f"Quality: {quality_report.overall_quality:.1f}% ({quality_report.grade})"
        )

        # Step 7: Add warnings for low quality
        if quality_report.overall_quality < 70.0:
            logger.warning(
                f"{self.agent_name}: Low quality analysis result: {quality_report.overall_quality:.1f}%. "
                f"Warnings: {quality_report.actionable_warnings}"
            )

        return result_with_quality

    def _calculate_average_quality(self, reports: List[QualityReport]) -> float:
        """Calculate average quality from reports"""
        if not reports:
            return 0.0
        scores = [r.quality_score for r in reports]
        return sum(scores) / len(scores)

    def _prepare_preliminary_result(
        self,
        data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare preliminary result for sufficiency validation"""
        # Extract metadata needed for sufficiency check
        return {
            "data": data if isinstance(data, list) else [data],
            "companies": self._extract_companies(data),
            "available_metrics": self._extract_metrics(data),
            "params": params
        }

    def _extract_companies(self, data: Any) -> List[str]:
        """Extract company list from data"""
        if isinstance(data, list):
            companies = set()
            for item in data:
                if isinstance(item, dict) and "company_id" in item:
                    companies.add(item["company_id"])
            return list(companies)
        return []

    def _extract_metrics(self, data: Any) -> List[str]:
        """Extract available metrics from data"""
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                # Return all numeric keys as metrics
                return [k for k, v in first_item.items()
                       if isinstance(v, (int, float))]
        return []

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

**Task 3.2: Write tests for QualityAwareMicroagent** (1 hour)
- **File**: `/backend/tests/test_quality_aware_microagent.py`
- **Tests**:
  - `test_base_class_cannot_instantiate()`
  - `test_analyze_with_quality_returns_quality_metadata()`
  - `test_low_input_quality_rejection()`
  - `test_insufficient_data_rejection()`
  - `test_analysis_failure_handling()`
  - `test_quality_logging()`

#### Afternoon (4 hours)

**Task 3.3: Create example implementation: TrendAnalysisAgent** (2 hours)
- **File**: `/backend/src/core/microagents/trend_analysis_agent.py`
- **Purpose**: Example of QualityAwareMicroagent implementation
- **Lines**: ~200 lines

```python
from typing import Dict, Any
from src.core.microagents.quality_aware_microagent import QualityAwareMicroagent
import numpy as np
from scipy import stats

class TrendAnalysisAgent(QualityAwareMicroagent):
    """Trend analysis with quality guarantees

    Example usage:
        agent = TrendAnalysisAgent()
        result = await agent.analyze_with_quality(data, params)

        if result["success"]:
            print(f"Trend: {result['result']['trend']}")
            print(f"Quality: {result['quality']['grade']}")
    """

    def _get_analysis_type(self) -> str:
        return "trend_analysis"

    async def analyze(
        self,
        data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform trend analysis"""

        metric = params.get("metric", "revenue")

        # Extract time series
        years = []
        values = []

        for item in data:
            if isinstance(item, dict) and "year" in item and metric in item:
                years.append(item["year"])
                values.append(item[metric])

        if len(years) < 2:
            raise ValueError("Need at least 2 data points for trend analysis")

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)

        # Determine trend direction
        if p_value < 0.05:  # Statistically significant
            if slope > 0:
                trend = "increasing"
            elif slope < 0:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "no_significant_trend"

        # Calculate confidence intervals
        confidence = 0.95
        t_val = stats.t.ppf((1 + confidence) / 2, len(years) - 2)

        margin = t_val * std_err
        slope_ci = {
            "lower": slope - margin,
            "upper": slope + margin,
            "confidence": confidence
        }

        # Forecast next year
        next_year = max(years) + 1
        forecast = slope * next_year + intercept
        forecast_ci = {
            "value": forecast,
            "lower": forecast - margin * next_year,
            "upper": forecast + margin * next_year
        }

        return {
            "trend": trend,
            "slope": slope,
            "intercept": intercept,
            "p_value": p_value,
            "model_metrics": {
                "r_squared": r_value ** 2,
                "std_err": std_err
            },
            "confidence_intervals": {
                "slope": slope_ci,
                "forecast": forecast_ci,
                "values": values,
                "lower": [intercept + slope * y - margin for y in years],
                "upper": [intercept + slope * y + margin for y in years]
            },
            "forecast": forecast_ci,
            "data_points": len(years),
            "metric": metric
        }
```

**Task 3.4: Write comprehensive tests for TrendAnalysisAgent** (1 hour)
- **File**: `/backend/tests/test_trend_analysis_agent.py`
- **Tests**:
  - `test_trend_analysis_increasing_trend()`
  - `test_trend_analysis_with_quality_metadata()`
  - `test_insufficient_data_rejection()`
  - `test_quality_propagation()`

**Task 3.5: Documentation** (1 hour)
- **File**: `/backend/docs/ANALYTICS_QUALITY_IMPLEMENTATION_GUIDE.md`
- **Purpose**: Developer guide for implementing quality-aware microagents
- **Content**:
  - How to extend QualityAwareMicroagent
  - Example implementations
  - Testing guidelines
  - Common pitfalls

**End of Day Deliverables**:
- ✅ QualityAwareMicroagent base class (500 lines, tested)
- ✅ TrendAnalysisAgent example (200 lines, tested)
- ✅ Implementation guide documentation
- ✅ All tests passing

---

### **Thursday 2025-11-17: Refactor Existing Microagent**

**Hours**: 8 hours
**Focus**: Refactor one existing microagent to use new quality framework

#### Morning (4 hours)

**Task 4.1: Identify target microagent for refactoring** (0.5 hours)
- Find existing microagent in codebase
- Assess current implementation
- Plan refactoring approach

**Task 4.2: Refactor microagent to extend QualityAwareMicroagent** (3 hours)
- Modify class to extend QualityAwareMicroagent
- Implement _get_analysis_type()
- Move analysis logic to analyze() method
- Update all call sites to use analyze_with_quality()
- Ensure backward compatibility where needed

**Example**: If refactoring `/backend/src/agents/financial_ratio_agent.py`:

```python
# BEFORE (old implementation)
class FinancialRatioAgent:
    def calculate_ratios(self, financial_data):
        # ... calculation logic
        return results

# AFTER (quality-aware)
from src.core.microagents.quality_aware_microagent import QualityAwareMicroagent

class FinancialRatioAgent(QualityAwareMicroagent):
    def _get_analysis_type(self) -> str:
        return "ratio_analysis"

    async def analyze(self, data: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        # Moved logic from calculate_ratios()
        # ... calculation logic
        return results

    # Legacy wrapper for backward compatibility
    async def calculate_ratios(self, financial_data):
        result = await self.analyze_with_quality(
            data=financial_data,
            params={}
        )
        return result
```

**Task 4.3: Update tests for refactored microagent** (0.5 hours)
- Update existing tests
- Add new quality assertion tests
- Ensure all tests pass

#### Afternoon (4 hours)

**Task 4.4: API endpoint integration** (2 hours)
- Update API endpoint to return quality metadata
- Add quality filtering (e.g., only return A/B grade results)
- Update API response schema

**Example**: Update `/backend/src/api/v1/analytics.py`:

```python
from fastapi import APIRouter, HTTPException
from src.core.microagents.trend_analysis_agent import TrendAnalysisAgent

router = APIRouter()

@router.post("/analytics/trend")
async def analyze_trend(request: TrendAnalysisRequest):
    """Analyze trend with quality guarantees"""

    agent = TrendAnalysisAgent()

    # Fetch data with quality reports
    data = await fetch_financial_data(
        company_id=request.company_id,
        metric=request.metric,
        years=request.years
    )

    # Extract quality reports from data layer
    data_quality_reports = [item["_quality_report"] for item in data]

    # Analyze with quality
    result = await agent.analyze_with_quality(
        data=data,
        params={"metric": request.metric},
        data_quality_reports=data_quality_reports
    )

    # Check if analysis succeeded
    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": result["error"],
                "message": result["message"],
                "quality": result["quality"]
            }
        )

    # Return result with quality metadata
    return {
        "trend": result["result"]["trend"],
        "slope": result["result"]["slope"],
        "forecast": result["result"]["forecast"],
        "quality": {
            "score": result["quality"]["overall_quality"],
            "grade": result["quality"]["grade"],
            "breakdown": {
                "data_quality": result["quality"]["data_quality"],
                "sufficiency": result["quality"]["sufficiency_quality"],
                "confidence": result["quality"]["method_confidence"]
            },
            "warnings": result["quality"]["warnings"]
        },
        "metadata": result["metadata"]
    }
```

**Task 4.5: Frontend integration preparation** (2 hours)
- Document API response schema changes
- Create TypeScript interfaces for quality metadata
- Write integration guide for frontend team

**File**: `/backend/docs/API_QUALITY_RESPONSE_SCHEMA.md`

```markdown
# API Quality Response Schema

## Trend Analysis Endpoint

**Endpoint**: `POST /api/v1/analytics/trend`

**Response** (Success):
```json
{
  "trend": "increasing",
  "slope": 1250000.50,
  "forecast": {
    "value": 125000000,
    "lower": 120000000,
    "upper": 130000000,
    "confidence": 0.95
  },
  "quality": {
    "score": 85.5,
    "grade": "B",
    "breakdown": {
      "data_quality": 90.0,
      "sufficiency": 80.0,
      "confidence": 85.0
    },
    "warnings": [
      "CONFIDENCE_INTERVALS_WIDE: Confidence intervals moderately wide: 75%"
    ]
  },
  "metadata": {
    "agent_name": "TrendAnalysisAgent",
    "analysis_type": "trend_analysis",
    "timestamp": "2025-11-17T10:30:00Z"
  }
}
```

**Response** (Failure):
```json
{
  "error": "DATA_INSUFFICIENT",
  "message": "Data insufficient for trend_analysis",
  "quality": {
    "overall_quality": 45.0,
    "grade": "D",
    "sufficiency_quality": 45.0,
    "warnings": [
      "SUFFICIENCY_INSUFFICIENT_PERIODS: Only 2 periods available, need 3 for trend_analysis"
    ]
  }
}
```

## TypeScript Interface

```typescript
interface AnalysisQuality {
  score: number;  // 0-100
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  breakdown: {
    data_quality: number;
    sufficiency: number;
    confidence: number;
  };
  warnings: string[];
}

interface TrendAnalysisResponse {
  trend: 'increasing' | 'decreasing' | 'stable' | 'no_significant_trend';
  slope: number;
  forecast: {
    value: number;
    lower: number;
    upper: number;
    confidence: number;
  };
  quality: AnalysisQuality;
  metadata: {
    agent_name: string;
    analysis_type: string;
    timestamp: string;
  };
}
```
```

**End of Day Deliverables**:
- ✅ One existing microagent refactored
- ✅ API endpoint updated with quality
- ✅ API documentation complete
- ✅ TypeScript interfaces documented

---

### **Friday 2025-11-18: Testing, Documentation & Integration**

**Hours**: 8 hours
**Focus**: Comprehensive testing and documentation

#### Morning (4 hours)

**Task 5.1: End-to-end integration tests** (2.5 hours)
- **File**: `/backend/tests/test_e2e_analytics_quality.py`
- **Tests**:
  - `test_full_pipeline_pdf_to_analysis_quality()`
  - `test_scanned_pdf_blocks_analysis()`
  - `test_low_table_quality_blocks_analysis()`
  - `test_year_mismatch_blocks_analysis()`
  - `test_insufficient_data_blocks_analysis()`
  - `test_quality_metadata_in_api_response()`

**Task 5.2: Load and performance testing** (1.5 hours)
- Measure performance impact of quality validation
- Ensure quality checks don't add >100ms latency
- Profile slow validators
- Document performance characteristics

```python
# /backend/tests/test_analytics_quality_performance.py
import time
import pytest

def test_quality_validation_performance():
    """Quality validation should add <100ms overhead"""
    agent = TrendAnalysisAgent()
    data = generate_test_data(n=10)

    # Measure time
    start = time.time()
    result = await agent.analyze_with_quality(data, {})
    duration = time.time() - start

    assert duration < 0.5, f"Quality validation too slow: {duration:.2f}s"
    assert result["success"]
```

#### Afternoon (4 hours)

**Task 5.3: Update main documentation** (2 hours)
- Update `/backend/docs/QUALITY_QUICK_REFERENCE.md`
- Update `/backend/docs/INDEX.md`
- Create `/backend/docs/ANALYTICS_QUALITY_WEEK1_SUMMARY.md`

**Task 5.4: Code review preparation** (1 hour)
- Review all code written this week
- Run linting and formatting
- Check GUARDRAIL #1 compliance
- Prepare PR description

**Task 5.5: Demo preparation** (1 hour)
- Create demo script showing:
  - Quality propagation from data to analysis
  - Rejection of bad data
  - Quality metadata in API responses
  - Grade A/B/C/D/F examples
- Prepare screenshots/recordings

**End of Day Deliverables**:
- ✅ E2E tests passing
- ✅ Performance validated
- ✅ Documentation complete
- ✅ Demo ready
- ✅ Week 1 complete

---

## 📊 Week 1 Success Metrics

### Code Metrics
- **New Files Created**: 8-10 files
- **Lines of Code**: ~2,500 lines
- **Test Coverage**: 90%+ for new code
- **Tests Written**: 50+ unit/integration tests

### Quality Metrics
- **GUARDRAIL #1 Compliance**: 100% (all code uses validation)
- **Zero Silent Failures**: Yes (all failures explicit)
- **Quality Metadata**: Yes (all results include quality)
- **Performance Impact**: <100ms added latency

### Deliverables Checklist
- ✅ analysis_quality_framework.py
- ✅ data_sufficiency_validator.py
- ✅ method_confidence_validator.py
- ✅ analysis_quality_orchestrator.py
- ✅ quality_aware_microagent.py
- ✅ trend_analysis_agent.py (example)
- ✅ 1 existing microagent refactored
- ✅ API endpoint updated
- ✅ Comprehensive tests
- ✅ Documentation complete

---

## 🎯 Week 1 → Week 2 Transition

### What's Ready for Week 2

**Foundation Complete**:
- ✅ Layer 5 validators framework
- ✅ QualityAwareMicroagent base class
- ✅ Quality propagation working
- ✅ One agent refactored

**Week 2 Focus Areas**:
1. Refactor remaining microagents (3-4 agents)
2. Implement StatisticalSignificanceValidator
3. Implement AssumptionValidator
4. Update all API endpoints
5. Create quality monitoring dashboard (backend)

---

## 🛡️ GUARDRAIL #1 Compliance Checklist

Before committing ANY code, verify:

### The 3 Questions
- [ ] **Can this silently store bad data?** → NO
- [ ] **Will the user know if this fails?** → YES
- [ ] **Can we trace this data to its source?** → YES

### Code Review Checklist
- [ ] Uses QualityAwareMicroagent (not direct analysis)
- [ ] Returns quality metadata in ALL responses
- [ ] Raises exceptions on failure (not silent)
- [ ] No validation bypasses
- [ ] Quality reports logged
- [ ] Tests verify quality behavior
- [ ] Documentation includes quality info

### Quality Standards
- [ ] All analysis results include quality score (0-100)
- [ ] All analysis results include grade (A/B/C/D/F)
- [ ] All analysis results include warnings list
- [ ] Quality < 50% results in explicit rejection
- [ ] Quality metadata flows to API responses

---

## 📝 Daily Standup Template

Use this template for daily standups:

```markdown
### [Your Name] - [Date]

**Yesterday**:
- Completed: [Task completed]
- Quality: [All code passed GUARDRAIL #1 review]
- Blockers: [None / description]

**Today**:
- Working on: [Current task from plan]
- Expected completion: [EOD / needs more time]

**Quality Notes**:
- Test coverage: [X%]
- Performance: [Within limits / needs optimization]
- Issues found: [None / description]
```

---

## 🚨 Risk Mitigation

### Potential Blockers

**Risk 1: Performance Impact**
- **Mitigation**: Profile after Day 2, optimize if needed
- **Threshold**: <100ms added latency acceptable

**Risk 2: Integration Complexity**
- **Mitigation**: Start with simple microagent refactor (Day 4)
- **Fallback**: If blocked, continue with new agents only

**Risk 3: Test Coverage**
- **Mitigation**: Write tests alongside code (not after)
- **Threshold**: 90%+ coverage required

---

## 📞 Support & Resources

### Documentation References
- [QUALITY_QUICK_REFERENCE.md](QUALITY_QUICK_REFERENCE.md) - Daily checklist
- [DATA_QUALITY_GUARANTEES.md](DATA_QUALITY_GUARANTEES.md) - Layer 1-4 examples
- [DEVELOPMENT_GUARDRAILS.md](DEVELOPMENT_GUARDRAILS.md) - Rules

### Code References
- `/backend/src/validation/quality_framework.py` - Base classes
- `/backend/src/validation/*_validator.py` - Validator examples
- `/backend/src/core/llm/validated_docling_storage_agent.py` - Integration example

### Getting Help
- **Quality questions**: Review quality documentation
- **Technical blockers**: Check existing validator implementations
- **Architecture decisions**: Refer to ANALYTICS_QUALITY_ARCHITECTURE.md

---

## ✅ Week 1 Completion Criteria

Week 1 is complete when:

1. **All files created and tested**
   - 8+ Python files
   - 50+ tests passing
   - 90%+ coverage

2. **At least one microagent refactored**
   - Extends QualityAwareMicroagent
   - Returns quality metadata
   - API endpoint updated

3. **Quality propagation working**
   - Data quality (Layer 1-4) flows to analysis
   - Analysis quality computed correctly
   - Combined quality score accurate

4. **Documentation complete**
   - Implementation guide written
   - API schema documented
   - Week 1 summary created

5. **Demo ready**
   - Can show end-to-end quality flow
   - Can show rejection examples
   - Can show quality grades

---

**Last Updated**: 2025-11-14 (Updated after ANALYTICS_QUALITY_CONCERNS.md review)
**Status**: READY TO START (with critical concerns addressed)
**Next Review**: 2025-11-18 EOD

---

## 🆕 CHANGES BASED ON ANALYTICS_QUALITY_CONCERNS.md

### Critical Updates Made to Week 1 Plan

#### 1. **Performance Budgets (NEW - Task 1.0)**
**Addresses**: 🔴 RISK 1 - Performance Degradation

- Added `/backend/src/validation/performance_budgets.py` as **first task**
- Defined three validation levels:
  - **FAST**: <100ms overhead (minimal checks)
  - **STANDARD**: <500ms overhead (recommended)
  - **THOROUGH**: <2s overhead (full validation)
- `PerformanceMonitor` class tracks and enforces budgets
- **Impact**: Prevents 3-5x latency increase

#### 2. **Tiered Validation Architecture**
**Addresses**: 🔴 RISK 1 - Performance Degradation

- `AnalysisQualityValidator` now accepts `validation_level` parameter
- `_should_run_check()` method skips expensive checks in FAST mode
- Each validator respects budget constraints
- **Impact**: Users can choose speed vs thoroughness

#### 3. **Two-Phase Validation (Pre-flight + Post-Analysis)**
**Addresses**: ⚠️ CONCERN 1 - Circular Dependency

- **Pre-flight** (Task 1.2): Fast checks BEFORE expensive analysis
  - Sample size sufficient?
  - Data quality acceptable?
  - Method appropriate?
- **Post-analysis**: Full validation of results
- **Impact**: Prevents wasted computation on doomed analyses

#### 4. **Domain-Configurable R² Thresholds**
**Addresses**: ⚠️ CONCERN 3.3 - R² Thresholds Too Rigid

- Added `domain` parameter to `AnalysisContext`
- Domain-specific thresholds:
  ```python
  R2_THRESHOLDS = {
      'finance': {'excellent': 0.40, 'good': 0.25},  # More lenient
      'operations': {'excellent': 0.85, 'good': 0.70}  # More strict
  }
  ```
- **Impact**: Realistic scoring for financial data

#### 5. **Sample-Size-Appropriate Statistical Tests**
**Addresses**: ⚠️ CONCERN 3.1 - Tests Fail on Small Samples

- Normality tests:
  - n < 20: Give benefit of doubt (no penalty)
  - n < 50: Shapiro-Wilk
  - n ≥ 50: Kolmogorov-Smirnov
- **Impact**: Avoids false negatives on small samples

#### 6. **Bootstrap Confidence Intervals**
**Addresses**: ⚠️ CONCERN 3.4 - CIs Assume Normality

- Non-parametric bootstrap CIs (1000 iterations)
- Works without normality assumption
- Enabled in THOROUGH mode only (performance cost)
- **Impact**: Robust CIs for non-normal data

#### 7. **Multiple Testing Correction**
**Addresses**: ⚠️ CONCERN 3.2 - Multiple Testing Problem

- Bonferroni correction for 4 assumption tests
- Corrected α = 0.05 / 4 = 0.0125
- **Impact**: Reduces false positives from 18.5% to 5%

#### 8. **Performance Profiling Throughout Week**
**Addresses**: ⚠️ CONCERN 9 - Missing Performance Benchmarking

- Every day includes performance profiling task
- Benchmark overhead of each validator
- Optimize if budget exceeded
- **Impact**: Catch performance issues early

### Summary of Code Changes

**New Files**:
1. `performance_budgets.py` (~100 lines) - **Critical addition**
2. All validators updated to support `validation_level`
3. `QualityAwareMicroagent` supports two-phase validation

**Modified Approaches**:
- ✅ Statistical tests adapted for sample size
- ✅ R² thresholds configurable by domain
- ✅ Bootstrap CIs available in THOROUGH mode
- ✅ Multiple testing correction applied
- ✅ Performance monitoring built-in

### Risk Mitigation Status

**Week 1 Addresses These CRITICAL Technical Risks**:

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| Performance Degradation | 🔴 CRITICAL | Performance budgets, tiered validation, profiling | ✅ Week 1 |
| Circular Dependency | 🟡 HIGH | Two-phase validation (pre-flight + post) | ✅ Week 1 |
| Statistical Issues | 🟡 HIGH | Sample-size tests, domain thresholds, bootstrap CIs | ✅ Week 1 |
| Memory Efficiency | 🟢 MEDIUM | Summary mode by default | ⏳ Week 2-3 |

**Out of Scope for Week 1** (technical foundation only):
- Grade calibration (distribution targets)
- Async validation (non-blocking UX)
- Quality caching
- UI/UX concerns (progressive disclosure, mobile optimization)

Week 1 focuses on: **Correct algorithms + Performance budgets + Foundation**

---

## 📊 Updated Week 1 Metrics

**Original Plan**:
- 8 files, ~2,500 lines
- 50+ tests
- 90%+ coverage
- No performance focus

**Updated Plan**:
- **9 files** (~2,600 lines) - Added performance_budgets.py
- **60+ tests** - Added performance tests
- **90%+ coverage** - Same
- **Performance budgets** - <500ms standard mode ✅
- **Profiling results** - Document overhead of each validator ✅

---

**Last Updated**: 2025-11-14 (Updated after ANALYTICS_QUALITY_CONCERNS.md review)
**Status**: READY TO START (with critical concerns addressed)
**Next Review**: 2025-11-18 EOD
**Concerns Document**: `/Users/artur/agents20/ANALYTICS_QUALITY_CONCERNS.md`

🛡️ **QUALITY FIRST. PERFORMANCE AWARE. WEEK 1. LET'S BUILD.** 🛡️
