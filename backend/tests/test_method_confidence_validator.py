"""
Tests for method confidence validator

GUARDRAIL COMPLIANCE:
- Tests all public APIs
- Tests error conditions
- Tests domain-specific thresholds
- Tests statistical validity checks
- Target: 90%+ coverage

Created: 2025-11-14
"""

import pytest
from src.validation.method_confidence_validator import MethodConfidenceValidator
from src.validation.analysis_quality_framework import AnalysisContext
from src.validation.quality_framework import QualityReport, QualityLevel, ValidationSeverity
from src.validation.performance_budgets import ValidationLevel


class TestMethodConfidenceValidator:
    """Test MethodConfidenceValidator basic functionality"""

    def test_initialization(self):
        """Test validator initialization"""
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.STANDARD,
            domain="finance"
        )

        assert validator.name == "MethodConfidenceValidator"
        assert validator.domain == "finance"
        assert validator.r_squared_thresholds["minimum"] == 0.70

    def test_initialization_different_domains(self):
        """Test domain-specific threshold configuration"""
        finance_validator = MethodConfidenceValidator(domain="finance")
        operations_validator = MethodConfidenceValidator(domain="operations")
        marketing_validator = MethodConfidenceValidator(domain="marketing")

        assert finance_validator.r_squared_thresholds["minimum"] == 0.70
        assert operations_validator.r_squared_thresholds["minimum"] == 0.50
        assert marketing_validator.r_squared_thresholds["minimum"] == 0.40

    def test_initialization_unknown_domain(self):
        """Test unknown domain falls back to default"""
        validator = MethodConfidenceValidator(domain="unknown_domain")

        assert validator.r_squared_thresholds["minimum"] == 0.60  # default


class TestRSquaredValidation:
    """Test R² validation with domain-specific thresholds"""

    def test_excellent_r_squared_finance(self):
        """Test excellent R² for finance domain"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.92,  # Excellent for finance (>= 0.90)
            "p_value": 0.001,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={},
            domain="finance"
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 95  # Should be excellent

    def test_good_r_squared_finance(self):
        """Test good (but not excellent) R² for finance"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.82,  # Good for finance (0.80 <= x < 0.90)
            "p_value": 0.01,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={},
            domain="finance"
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert 85 <= report.quality_score < 95  # Good, not excellent

    def test_minimum_r_squared_finance(self):
        """Test minimum acceptable R² for finance"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.72,  # Just above minimum (0.70)
            "p_value": 0.02,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={},
            domain="finance"
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert 90 <= report.quality_score < 95  # Good score with minor warning
        assert any("MODERATE_R_SQUARED" in issue.code for issue in report.issues)

    def test_low_r_squared_finance(self):
        """Test R² below minimum for finance"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.55,  # Below minimum (0.70)
            "p_value": 0.03,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={},
            domain="finance"
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("LOW_R_SQUARED" in issue.code for issue in report.issues)

    def test_acceptable_r_squared_operations(self):
        """Test that lower R² is acceptable for operations domain"""
        validator = MethodConfidenceValidator(domain="operations")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.55,  # Acceptable for operations (min 0.50)
            "p_value": 0.02,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={},
            domain="operations"
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 70


class TestPValueValidation:
    """Test p-value significance validation"""

    def test_highly_significant_p_value(self):
        """Test highly significant p-value (p < 0.01)"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.003,  # Highly significant
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 90

    def test_significant_p_value(self):
        """Test significant p-value (0.01 <= p < 0.05)"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.03,  # Significant (but not highly)
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert 85 <= report.quality_score < 95

    def test_not_significant_p_value(self):
        """Test non-significant p-value (p >= 0.05)"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.12,  # Not significant
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True  # Still passes, but with warning
        assert any("NOT_SIGNIFICANT" in issue.code for issue in report.issues)
        assert report.quality_score < 90


class TestSampleSizeValidation:
    """Test sample size validation"""

    def test_sufficient_sample_size(self):
        """Test sufficient sample size for trend analysis"""
        validator = MethodConfidenceValidator()

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 30  # Sufficient for trend analysis (min 10)
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True

    def test_insufficient_sample_size(self):
        """Test insufficient sample size"""
        validator = MethodConfidenceValidator()

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 5  # Too small (min 10 for trend)
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("INSUFFICIENT_SAMPLE" in issue.code for issue in report.issues)

    def test_larger_sample_required_for_forecasting(self):
        """Test forecasting requires larger sample size"""
        validator = MethodConfidenceValidator()

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "time_series_forecast",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 15  # Too small for forecasting (min 20)
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="forecasting",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("INSUFFICIENT_SAMPLE" in issue.code for issue in report.issues)


class TestConfidenceIntervalValidation:
    """Test confidence interval validation"""

    def test_narrow_confidence_interval(self):
        """Test narrow (good) confidence interval"""
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.STANDARD
        )

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50,
            "confidence_interval": (95, 105)  # Narrow (10% of midpoint 100)
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        # Should not have warning about wide interval
        assert not any("WIDE_INTERVAL" in issue.code for issue in report.issues)

    def test_wide_confidence_interval(self):
        """Test wide (problematic) confidence interval"""
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.STANDARD
        )

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50,
            "confidence_interval": (50, 250)  # Very wide (200% of midpoint 150)
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True  # Still passes
        # Should have warning about wide interval
        assert any("WIDE_INTERVAL" in issue.code for issue in report.issues)


class TestResidualValidation:
    """Test residual analysis"""

    def test_well_behaved_residuals(self):
        """Test residuals with mean near zero and no outliers"""
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.THOROUGH  # Enables residual analysis
        )

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        # Well-behaved residuals: mean ~0, no outliers
        residuals = [0.1, -0.2, 0.05, -0.15, 0.08, -0.12, 0.03, -0.07, 0.11, -0.09]

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50,
            "residuals": residuals
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        # Should not have warnings about residuals
        assert not any("BIASED_RESIDUALS" in issue.code for issue in report.issues)
        assert not any("RESIDUAL_OUTLIERS" in issue.code for issue in report.issues)

    def test_biased_residuals(self):
        """Test residuals with systematic bias (mean != 0)"""
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.THOROUGH
        )

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        # Biased residuals: all positive (mean >> 0)
        residuals = [0.5, 0.6, 0.4, 0.7, 0.5, 0.6, 0.5, 0.6, 0.5, 0.6]

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50,
            "residuals": residuals
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True  # Still passes
        # Should have warning about biased residuals
        assert any("BIASED_RESIDUALS" in issue.code for issue in report.issues)

    def test_residuals_with_outliers(self):
        """Test residuals with outliers"""
        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.THOROUGH
        )

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        # Residuals with outliers (mostly small, few very large)
        residuals = [0.01, -0.01, 0.02, -0.02, 0.01, -0.01, 0.02, -0.02,
                     10.0, -9.0, 11.0]  # Last 3 are clear outliers

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50,
            "residuals": residuals
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True  # Still passes
        # Should have warning about outliers
        assert any("RESIDUAL_OUTLIERS" in issue.code for issue in report.issues)


class TestMissingFields:
    """Test handling of missing fields"""

    def test_missing_r_squared(self):
        """Test regression method without R² gets warning"""
        validator = MethodConfidenceValidator()

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            # r_squared missing
            "p_value": 0.01,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        # Should have warning about missing R²
        assert any("MISSING_R_SQUARED" in issue.code for issue in report.issues)

    def test_missing_p_value(self):
        """Test missing p-value is handled gracefully"""
        validator = MethodConfidenceValidator()

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            # p_value missing
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        # Should not crash, just skip p-value check


class TestPerformanceCompliance:
    """Test performance compliance"""

    def test_validation_completes_quickly(self):
        """Test validation completes within performance budget"""
        import time

        validator = MethodConfidenceValidator(
            validation_level=ValidationLevel.FAST
        )

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        start = time.time()
        report = validator.validate(analysis_result, context)
        elapsed_ms = (time.time() - start) * 1000

        # FAST mode should complete in <100ms
        assert elapsed_ms < 100
        assert report.metadata['performance']['within_budget'] is True


class TestGuardrailCompliance:
    """Test GUARDRAIL #1 compliance"""

    def test_no_silent_failures(self):
        """Test validation never silently fails"""
        validator = MethodConfidenceValidator()

        # Missing context - should fail explicitly
        analysis_result = {"method": "test"}

        report = validator.validate(analysis_result, None)

        # Failure must be explicit
        assert report.passed is False
        assert report.quality_score == 0.0
        assert len(report.issues) > 0

    def test_clear_error_messages(self):
        """Test error messages are clear and actionable"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.50,  # Too low for finance
            "p_value": 0.12,    # Not significant
            "sample_size": 5    # Too small
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Should have clear, specific error messages
        assert len(report.issues) >= 3
        issue_codes = [i.code for i in report.issues]
        assert "CONFIDENCE_LOW_R_SQUARED" in issue_codes
        assert "CONFIDENCE_NOT_SIGNIFICANT" in issue_codes
        assert "CONFIDENCE_INSUFFICIENT_SAMPLE" in issue_codes

    def test_metrics_include_thresholds(self):
        """Test report metadata includes thresholds for transparency"""
        validator = MethodConfidenceValidator(domain="finance")

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "method": "linear_regression",
            "r_squared": 0.85,
            "p_value": 0.01,
            "sample_size": 50
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Metrics should include thresholds for transparency
        assert "r_squared_threshold" in report.metrics
        assert "domain" in report.metrics
        assert report.metrics["domain"] == "finance"
