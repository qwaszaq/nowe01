"""
Tests for Data Sufficiency Validator

GUARDRAIL COMPLIANCE:
- Tests all analysis types
- Tests pre-flight validation
- Tests error conditions
- Tests performance budgets
- Target: 90%+ coverage

Created: 2025-11-14
"""

import pytest
from src.validation.data_sufficiency_validator import DataSufficiencyValidator
from src.validation.analysis_quality_framework import AnalysisContext
from src.validation.quality_framework import (
    QualityReport,
    QualityLevel,
    ValidationSeverity
)
from src.validation.performance_budgets import ValidationLevel


class TestDataSufficiencyValidator:
    """Test DataSufficiencyValidator"""

    def test_initialization(self):
        """Test validator initialization"""
        validator = DataSufficiencyValidator(
            validation_level=ValidationLevel.STANDARD
        )

        assert validator.name == "DataSufficiencyValidator"
        assert validator.validation_level == ValidationLevel.STANDARD

    def test_min_requirements_defined(self):
        """Test minimum requirements are defined for all analysis types"""
        validator = DataSufficiencyValidator()

        # Check key analysis types
        assert "trend_analysis" in validator.MIN_REQUIREMENTS
        assert "forecasting" in validator.MIN_REQUIREMENTS
        assert "comparative_analysis" in validator.MIN_REQUIREMENTS
        assert "ratio_analysis" in validator.MIN_REQUIREMENTS


class TestTrendAnalysis:
    """Test sufficiency validation for trend analysis"""

    def test_trend_analysis_sufficient_data(self):
        """Test trend analysis with sufficient data"""
        validator = DataSufficiencyValidator()

        # Create high quality data report
        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        # 5 periods - sufficient for trend
        analysis_result = {
            "data": [
                {"year": 2019, "revenue": 100},
                {"year": 2020, "revenue": 110},
                {"year": 2021, "revenue": 120},
                {"year": 2022, "revenue": 130},
                {"year": 2023, "revenue": 140}
            ],
            "periods": [2019, 2020, 2021, 2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={"metric": "revenue"}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 90  # Excellent data
        assert report.quality_level == QualityLevel.EXCELLENT

    def test_trend_analysis_insufficient_periods(self):
        """Test trend analysis with insufficient periods"""
        validator = DataSufficiencyValidator()

        # Only 2 periods - need 3 minimum
        analysis_result = {
            "data": [
                {"year": 2022, "revenue": 130},
                {"year": 2023, "revenue": 140}
            ],
            "periods": [2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert report.quality_score < 70
        # Should have critical issue
        assert any("INSUFFICIENT_PERIODS" in issue.code for issue in report.issues)

    def test_trend_analysis_limited_periods_warning(self):
        """Test trend analysis with limited but acceptable periods"""
        validator = DataSufficiencyValidator()

        # 3 periods - minimum, but less than recommended 5
        analysis_result = {
            "data": [
                {"year": 2021, "revenue": 120},
                {"year": 2022, "revenue": 130},
                {"year": 2023, "revenue": 140}
            ],
            "periods": [2021, 2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True  # Passes, but with warning
        assert 85 <= report.quality_score < 100  # Excellent with minor penalty
        # Should have warning about limited periods
        assert any("LIMITED_PERIODS" in issue.code for issue in report.issues)


class TestForecastingAnalysis:
    """Test sufficiency validation for forecasting"""

    def test_forecasting_sufficient_data(self):
        """Test forecasting with sufficient historical data"""
        validator = DataSufficiencyValidator()

        # 10 periods - good for forecasting
        analysis_result = {
            "data": [{"year": y, "revenue": 100 + y} for y in range(2014, 2024)],
            "periods": list(range(2014, 2024)),
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="forecasting",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 90

    def test_forecasting_insufficient_history(self):
        """Test forecasting with insufficient historical data"""
        validator = DataSufficiencyValidator()

        # Only 3 periods - need 5 minimum
        analysis_result = {
            "data": [
                {"year": 2021, "revenue": 120},
                {"year": 2022, "revenue": 130},
                {"year": 2023, "revenue": 140}
            ],
            "periods": [2021, 2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="forecasting",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("INSUFFICIENT_PERIODS" in issue.code for issue in report.issues)


class TestComparativeAnalysis:
    """Test sufficiency validation for comparative analysis"""

    def test_comparative_analysis_multiple_companies(self):
        """Test comparative analysis with multiple companies"""
        validator = DataSufficiencyValidator()

        analysis_result = {
            "data": [
                {"year": 2023, "company_id": "AAPL", "revenue": 100},
                {"year": 2023, "company_id": "MSFT", "revenue": 110},
                {"year": 2023, "company_id": "GOOGL", "revenue": 105}
            ],
            "periods": [2023],
            "companies": ["AAPL", "MSFT", "GOOGL"],
            "available_metrics": ["revenue"]
        }

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="comparative_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 70

    def test_comparative_analysis_single_company(self):
        """Test comparative analysis requires multiple companies"""
        validator = DataSufficiencyValidator()

        # Only 1 company - need 2 minimum
        analysis_result = {
            "data": [{"year": 2023, "company_id": "AAPL", "revenue": 100}],
            "periods": [2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="comparative_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("INSUFFICIENT_COMPANIES" in issue.code for issue in report.issues)


class TestRatioAnalysis:
    """Test sufficiency validation for ratio analysis"""

    def test_ratio_analysis_all_metrics_present(self):
        """Test ratio analysis with all required metrics"""
        validator = DataSufficiencyValidator()

        analysis_result = {
            "data": [{
                "year": 2023,
                "revenue": 100,
                "assets": 500,
                "equity": 300,
                "liabilities": 200
            }],
            "periods": [2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue", "assets", "equity", "liabilities"]
        }

        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="ratio_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert report.quality_score >= 70

    def test_ratio_analysis_missing_metrics(self):
        """Test ratio analysis with missing required metrics"""
        validator = DataSufficiencyValidator()

        # Missing liabilities and equity
        analysis_result = {
            "data": [{"year": 2023, "revenue": 100, "assets": 500}],
            "periods": [2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue", "assets"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="ratio_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("MISSING_METRICS" in issue.code for issue in report.issues)

        # Check that missing metrics are listed
        missing_issue = [i for i in report.issues if "MISSING_METRICS" in i.code][0]
        assert "equity" in missing_issue.message.lower()
        assert "liabilities" in missing_issue.message.lower()


class TestTimeSeriesGaps:
    """Test time series gap detection"""

    def test_no_gaps_in_continuous_series(self):
        """Test continuous time series has no gaps"""
        validator = DataSufficiencyValidator(
            validation_level=ValidationLevel.STANDARD  # Enables gap checking
        )

        analysis_result = {
            "data": [
                {"year": 2020, "revenue": 100},
                {"year": 2021, "revenue": 110},
                {"year": 2022, "revenue": 120},
                {"year": 2023, "revenue": 130}
            ],
            "periods": [2020, 2021, 2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Should not have gap issues
        assert not any("DATA_GAPS" in issue.code for issue in report.issues)

    def test_detects_gaps_in_series(self):
        """Test detection of gaps in time series"""
        validator = DataSufficiencyValidator(
            validation_level=ValidationLevel.STANDARD
        )

        # Gap between 2020 and 2023
        analysis_result = {
            "data": [
                {"year": 2020, "revenue": 100},
                {"year": 2023, "revenue": 130},
                {"year": 2024, "revenue": 140}
            ],
            "periods": [2020, 2023, 2024],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Should have gap warning
        assert any("DATA_GAPS" in issue.code for issue in report.issues)

        # Check gap is identified
        gap_issue = [i for i in report.issues if "DATA_GAPS" in i.code][0]
        assert "2020-2023" in gap_issue.message

    def test_fast_mode_skips_gap_checking(self):
        """Test FAST mode skips expensive gap checking"""
        validator = DataSufficiencyValidator(
            validation_level=ValidationLevel.FAST  # Disables gap checking
        )

        # Has gaps, but FAST mode shouldn't check
        analysis_result = {
            "data": [
                {"year": 2020, "revenue": 100},
                {"year": 2023, "revenue": 130}
            ],
            "periods": [2020, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Should NOT have gap checking in FAST mode
        assert not any("DATA_GAPS" in issue.code for issue in report.issues)


class TestInputDataQuality:
    """Test input data quality validation"""

    def test_high_quality_input_data(self):
        """Test validation passes with high quality input"""
        validator = DataSufficiencyValidator()

        # Create high quality data report
        good_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=90.0,
            quality_level=QualityLevel.EXCELLENT,
            passed=True
        )

        analysis_result = {
            "data": [
                {"year": 2021, "revenue": 120},
                {"year": 2022, "revenue": 130},
                {"year": 2023, "revenue": 140}
            ],
            "periods": [2021, 2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[good_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is True
        assert "input_data_quality" in report.metrics
        assert report.metrics["input_data_quality"] == 90.0

    def test_low_quality_input_data_rejection(self):
        """Test validation rejects low quality input data"""
        validator = DataSufficiencyValidator()

        # Create low quality data report
        bad_data_report = QualityReport(
            entity_type="table",
            entity_id="table1",
            quality_score=30.0,  # Below 50% threshold
            quality_level=QualityLevel.POOR,
            passed=False
        )

        analysis_result = {
            "data": [
                {"year": 2021, "revenue": 120},
                {"year": 2022, "revenue": 130},
                {"year": 2023, "revenue": 140}
            ],
            "periods": [2021, 2022, 2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[bad_data_report],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        assert report.passed is False
        assert any("LOW_INPUT_QUALITY" in issue.code for issue in report.issues)


class TestDataStructureHandling:
    """Test handling of various data structures"""

    def test_count_periods_from_explicit_list(self):
        """Test counting periods from explicit periods list"""
        validator = DataSufficiencyValidator()

        result = validator._count_periods({
            "periods": [2020, 2021, 2022, 2023]
        })

        assert result == 4

    def test_count_periods_from_data_list(self):
        """Test counting periods from data list"""
        validator = DataSufficiencyValidator()

        result = validator._count_periods({
            "data": [
                {"year": 2020},
                {"year": 2021},
                {"year": 2022}
            ]
        })

        assert result == 3

    def test_count_companies_from_explicit_list(self):
        """Test counting companies from explicit list"""
        validator = DataSufficiencyValidator()

        result = validator._count_companies({
            "companies": ["AAPL", "MSFT", "GOOGL"]
        })

        assert result == 3

    def test_count_companies_from_data(self):
        """Test extracting unique companies from data"""
        validator = DataSufficiencyValidator()

        result = validator._count_companies({
            "data": [
                {"company_id": "AAPL"},
                {"company_id": "MSFT"},
                {"company_id": "AAPL"}  # Duplicate
            ]
        })

        assert result == 2  # AAPL, MSFT (unique)

    def test_count_companies_defaults_to_one(self):
        """Test company count defaults to 1 if unknown"""
        validator = DataSufficiencyValidator()

        result = validator._count_companies({
            "data": []
        })

        assert result == 1


class TestPerformanceCompliance:
    """Test performance budget compliance"""

    def test_validation_completes_quickly(self):
        """Test validation completes within budget"""
        validator = DataSufficiencyValidator(
            validation_level=ValidationLevel.STANDARD
        )

        analysis_result = {
            "data": [{"year": y, "revenue": y * 100} for y in range(2014, 2024)],
            "periods": list(range(2014, 2024)),
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Check performance
        assert "performance" in report.metadata
        perf = report.metadata["performance"]
        assert perf["within_budget"] is True
        # Should be fast (< 100ms for STANDARD mode)
        assert perf["total_ms"] < 500


class TestGuardrailCompliance:
    """Test GUARDRAIL #1 compliance"""

    def test_no_silent_failures(self):
        """Test all failures are explicit"""
        validator = DataSufficiencyValidator()

        # Insufficient data
        analysis_result = {
            "data": [{"year": 2023}],
            "periods": [2023],
            "companies": [],
            "available_metrics": []
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="forecasting",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Failure must be explicit
        assert report.passed is False
        assert len(report.issues) > 0
        assert report.quality_score < 70

    def test_clear_error_messages(self):
        """Test error messages are actionable"""
        validator = DataSufficiencyValidator()

        analysis_result = {
            "data": [{"year": 2023}],
            "periods": [2023],
            "companies": ["AAPL"],
            "available_metrics": []
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="ratio_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Should have clear message about missing metrics
        missing_issue = [i for i in report.issues if "MISSING_METRICS" in i.code][0]
        assert "revenue" in missing_issue.message.lower()
        assert "assets" in missing_issue.message.lower()

    def test_metadata_includes_requirements(self):
        """Test metadata includes requirements for transparency"""
        validator = DataSufficiencyValidator()

        analysis_result = {
            "data": [{"year": 2023, "revenue": 100}],
            "periods": [2023],
            "companies": ["AAPL"],
            "available_metrics": ["revenue"]
        }

        context = AnalysisContext(
            data_quality_reports=[],
            analysis_type="trend_analysis",
            user_params={}
        )

        report = validator.validate(analysis_result, context)

        # Should include requirements in metrics
        assert "requirements" in report.metrics
        assert "min_periods" in report.metrics["requirements"]
