"""
Performance Profiling for Analytics Quality Validators
========================================================

Verifies that validators meet performance budgets:
- FAST mode: <100ms overhead
- STANDARD mode: <500ms overhead
- THOROUGH mode: <2000ms overhead

GUARDRAIL COMPLIANCE:
- Explicit performance measurement
- Budget violations reported clearly
- Multiple runs for statistical reliability

Created: 2025-11-14
"""

import time
import statistics
from typing import List, Dict, Any

from src.validation.data_sufficiency_validator import DataSufficiencyValidator
from src.validation.analysis_quality_framework import AnalysisContext
from src.validation.quality_framework import QualityReport, QualityLevel
from src.validation.performance_budgets import ValidationLevel


def profile_validator(
    validator_class,
    validation_level: ValidationLevel,
    analysis_result: Dict[str, Any],
    context: AnalysisContext,
    runs: int = 10
) -> Dict[str, Any]:
    """Profile a validator with multiple runs

    Args:
        validator_class: Validator class to profile
        validation_level: FAST/STANDARD/THOROUGH
        analysis_result: Test data
        context: Analysis context
        runs: Number of profiling runs

    Returns:
        Performance statistics
    """
    validator = validator_class(validation_level=validation_level)

    # Warm-up run
    validator.validate(analysis_result, context)

    # Profiling runs
    timings: List[float] = []

    for _ in range(runs):
        start = time.time()
        report = validator.validate(analysis_result, context)
        elapsed_ms = (time.time() - start) * 1000
        timings.append(elapsed_ms)

    # Calculate statistics
    avg_ms = statistics.mean(timings)
    median_ms = statistics.median(timings)
    min_ms = min(timings)
    max_ms = max(timings)
    stddev_ms = statistics.stdev(timings) if len(timings) > 1 else 0

    # Get budget
    budget_map = {
        ValidationLevel.FAST: 100,
        ValidationLevel.STANDARD: 500,
        ValidationLevel.THOROUGH: 2000
    }
    budget_ms = budget_map[validation_level]

    # Check compliance
    within_budget = avg_ms <= budget_ms
    margin = budget_ms - avg_ms
    margin_pct = (margin / budget_ms) * 100

    return {
        "validator": validator_class.__name__,
        "level": validation_level.value,
        "runs": runs,
        "avg_ms": round(avg_ms, 2),
        "median_ms": round(median_ms, 2),
        "min_ms": round(min_ms, 2),
        "max_ms": round(max_ms, 2),
        "stddev_ms": round(stddev_ms, 2),
        "budget_ms": budget_ms,
        "within_budget": within_budget,
        "margin_ms": round(margin, 2),
        "margin_pct": round(margin_pct, 1),
        "all_timings": [round(t, 2) for t in timings]
    }


def print_profile_results(results: Dict[str, Any]):
    """Pretty print profiling results"""
    status = "✅ PASS" if results["within_budget"] else "❌ FAIL"

    print(f"\n{status} {results['validator']} ({results['level'].upper()})")
    print(f"  Budget:     {results['budget_ms']}ms")
    print(f"  Average:    {results['avg_ms']}ms")
    print(f"  Median:     {results['median_ms']}ms")
    print(f"  Range:      {results['min_ms']}ms - {results['max_ms']}ms")
    print(f"  Std Dev:    {results['stddev_ms']}ms")
    print(f"  Margin:     {results['margin_ms']}ms ({results['margin_pct']}%)")

    if not results["within_budget"]:
        print(f"  ⚠️  BUDGET EXCEEDED BY {abs(results['margin_ms'])}ms")


def main():
    """Run performance profiling"""
    print("=" * 70)
    print("ANALYTICS QUALITY VALIDATORS - PERFORMANCE PROFILING")
    print("=" * 70)

    # Create test data
    good_data_report = QualityReport(
        entity_type="table",
        entity_id="table1",
        quality_score=90.0,
        quality_level=QualityLevel.EXCELLENT,
        passed=True
    )

    # Trend analysis test case
    trend_analysis_result = {
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

    trend_context = AnalysisContext(
        data_quality_reports=[good_data_report],
        analysis_type="trend_analysis",
        user_params={"metric": "revenue"}
    )

    # Profile DataSufficiencyValidator
    print("\n📊 DataSufficiencyValidator")
    print("-" * 70)

    # FAST mode
    results_fast = profile_validator(
        DataSufficiencyValidator,
        ValidationLevel.FAST,
        trend_analysis_result,
        trend_context,
        runs=20
    )
    print_profile_results(results_fast)

    # STANDARD mode
    results_standard = profile_validator(
        DataSufficiencyValidator,
        ValidationLevel.STANDARD,
        trend_analysis_result,
        trend_context,
        runs=20
    )
    print_profile_results(results_standard)

    # THOROUGH mode
    results_thorough = profile_validator(
        DataSufficiencyValidator,
        ValidationLevel.THOROUGH,
        trend_analysis_result,
        trend_context,
        runs=20
    )
    print_profile_results(results_thorough)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_results = [results_fast, results_standard, results_thorough]
    all_passed = all(r["within_budget"] for r in all_results)

    if all_passed:
        print("✅ ALL VALIDATORS MEET PERFORMANCE BUDGETS")
    else:
        print("❌ SOME VALIDATORS EXCEED BUDGETS")
        failed = [r for r in all_results if not r["within_budget"]]
        for result in failed:
            print(f"   - {result['validator']} ({result['level']}): "
                  f"{result['avg_ms']}ms > {result['budget_ms']}ms")

    print("\nPerformance budgets:")
    print(f"  FAST:      <100ms   (actual: {results_fast['avg_ms']}ms)")
    print(f"  STANDARD:  <500ms   (actual: {results_standard['avg_ms']}ms)")
    print(f"  THOROUGH:  <2000ms  (actual: {results_thorough['avg_ms']}ms)")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
