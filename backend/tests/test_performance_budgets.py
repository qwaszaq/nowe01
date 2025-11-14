"""
Tests for performance budgets module

GUARDRAIL COMPLIANCE:
- Tests all public APIs
- Tests error conditions
- Tests budget enforcement
- Ensures no silent failures
- Target: 90%+ coverage

Created: 2025-11-14
"""

import pytest
import time
from src.validation.performance_budgets import (
    ValidationLevel,
    PerformanceBudget,
    PerformanceMonitor,
    BUDGETS,
    get_budget
)


class TestValidationLevel:
    """Test ValidationLevel enum"""

    def test_validation_levels_exist(self):
        """Test all validation levels are defined"""
        assert ValidationLevel.FAST is not None
        assert ValidationLevel.STANDARD is not None
        assert ValidationLevel.THOROUGH is not None

    def test_validation_level_values(self):
        """Test validation level string values"""
        assert ValidationLevel.FAST.value == "fast"
        assert ValidationLevel.STANDARD.value == "standard"
        assert ValidationLevel.THOROUGH.value == "thorough"


class TestPerformanceBudget:
    """Test PerformanceBudget dataclass"""

    def test_fast_budget_exists(self):
        """Test FAST budget is configured"""
        budget = BUDGETS[ValidationLevel.FAST]
        assert budget.level == ValidationLevel.FAST
        assert budget.max_overhead_ms == 100
        assert budget.max_total_ms == 500

    def test_standard_budget_exists(self):
        """Test STANDARD budget is configured"""
        budget = BUDGETS[ValidationLevel.STANDARD]
        assert budget.level == ValidationLevel.STANDARD
        assert budget.max_overhead_ms == 500
        assert budget.max_total_ms == 2000

    def test_thorough_budget_exists(self):
        """Test THOROUGH budget is configured"""
        budget = BUDGETS[ValidationLevel.THOROUGH]
        assert budget.level == ValidationLevel.THOROUGH
        assert budget.max_overhead_ms == 2000
        assert budget.max_total_ms is None  # No limit

    def test_fast_mode_minimal_checks(self):
        """Test FAST mode has minimal checks enabled"""
        budget = BUDGETS[ValidationLevel.FAST]

        # These should be enabled
        assert budget.is_check_enabled('input_quality') is True
        assert budget.is_check_enabled('sample_size') is True

        # These should be disabled (too slow)
        assert budget.is_check_enabled('data_gaps') is False
        assert budget.is_check_enabled('statistical_tests') is False
        assert budget.is_check_enabled('bootstrap_ci') is False

    def test_standard_mode_balanced_checks(self):
        """Test STANDARD mode has balanced checks"""
        budget = BUDGETS[ValidationLevel.STANDARD]

        # Basic checks enabled
        assert budget.is_check_enabled('input_quality') is True
        assert budget.is_check_enabled('sample_size') is True
        assert budget.is_check_enabled('data_gaps') is True
        assert budget.is_check_enabled('statistical_tests') is True

        # Expensive checks disabled
        assert budget.is_check_enabled('bootstrap_ci') is False
        assert budget.is_check_enabled('assumption_validation') is False

    def test_thorough_mode_all_checks(self):
        """Test THOROUGH mode has all checks enabled"""
        budget = BUDGETS[ValidationLevel.THOROUGH]

        # All checks enabled
        assert budget.is_check_enabled('input_quality') is True
        assert budget.is_check_enabled('sample_size') is True
        assert budget.is_check_enabled('data_gaps') is True
        assert budget.is_check_enabled('statistical_tests') is True
        assert budget.is_check_enabled('bootstrap_ci') is True
        assert budget.is_check_enabled('assumption_validation') is True

    def test_is_check_enabled_unknown_check(self):
        """Test is_check_enabled returns False for unknown checks"""
        budget = BUDGETS[ValidationLevel.STANDARD]
        assert budget.is_check_enabled('unknown_check_xyz') is False


class TestPerformanceMonitor:
    """Test PerformanceMonitor class"""

    def test_initialization(self):
        """Test monitor initialization"""
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)
        assert monitor.budget.level == ValidationLevel.STANDARD
        assert monitor.start_time is None
        assert len(monitor.checkpoints) == 0

    def test_initialization_invalid_level(self):
        """Test monitor rejects invalid validation level"""
        with pytest.raises(ValueError, match="Invalid validation level"):
            PerformanceMonitor("invalid_level")

    def test_start(self):
        """Test starting performance monitoring"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()

        assert monitor.start_time is not None
        assert len(monitor.checkpoints) == 0
        assert monitor._finished is False

    def test_checkpoint(self):
        """Test recording checkpoints"""
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)
        monitor.start()

        time.sleep(0.01)  # 10ms
        monitor.checkpoint("first")

        time.sleep(0.01)  # Another 10ms
        monitor.checkpoint("second")

        assert len(monitor.checkpoints) == 2
        assert monitor.checkpoints[0].name == "first"
        assert monitor.checkpoints[1].name == "second"
        assert monitor.checkpoints[1].elapsed_ms > monitor.checkpoints[0].elapsed_ms

    def test_checkpoint_before_start(self):
        """Test checkpoint fails gracefully if called before start"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        # Don't call start()

        monitor.checkpoint("should_fail")

        # Should not raise, but should log error
        assert len(monitor.checkpoints) == 0

    def test_finish_returns_stats(self):
        """Test finish returns performance statistics"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()

        time.sleep(0.02)  # 20ms
        monitor.checkpoint("test")

        stats = monitor.finish()

        assert 'total_ms' in stats
        assert 'budget_ms' in stats
        assert 'within_budget' in stats
        assert 'validation_level' in stats
        assert 'checkpoints' in stats
        assert 'violations' in stats

        assert stats['budget_ms'] == 100  # FAST budget
        assert stats['validation_level'] == 'fast'

    def test_finish_within_budget(self):
        """Test finish correctly identifies within-budget execution"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()

        time.sleep(0.02)  # 20ms (well under 100ms budget)

        stats = monitor.finish()

        assert stats['within_budget'] is True
        assert stats['total_ms'] < 100
        assert len(stats['violations']) == 0

    def test_finish_budget_exceeded(self):
        """Test finish correctly identifies budget violations"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()

        time.sleep(0.15)  # 150ms (exceeds 100ms budget)

        stats = monitor.finish()

        assert stats['within_budget'] is False
        assert stats['total_ms'] > 100
        assert len(stats['violations']) > 0
        assert stats['violations'][0]['checkpoint'] == 'total'

    def test_finish_before_start(self):
        """Test finish fails gracefully if called before start"""
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)
        # Don't call start()

        stats = monitor.finish()

        assert 'error' in stats
        assert stats['error'] == 'Not started'
        assert stats['within_budget'] is False

    def test_checkpoint_summary_includes_durations(self):
        """Test checkpoint summary includes individual durations"""
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)
        monitor.start()

        time.sleep(0.01)  # 10ms
        monitor.checkpoint("first")

        time.sleep(0.02)  # 20ms
        monitor.checkpoint("second")

        stats = monitor.finish()

        assert 'first' in stats['checkpoints']
        assert 'second' in stats['checkpoints']

        first_cp = stats['checkpoints']['first']
        second_cp = stats['checkpoints']['second']

        # First checkpoint duration = elapsed total
        assert first_cp['duration_ms'] == first_cp['elapsed_total_ms']

        # Second checkpoint duration = time since first
        assert second_cp['duration_ms'] > 0
        assert second_cp['duration_ms'] < second_cp['elapsed_total_ms']

    def test_should_run_check_respects_budget(self):
        """Test should_run_check respects budget configuration"""
        monitor_fast = PerformanceMonitor(ValidationLevel.FAST)
        monitor_thorough = PerformanceMonitor(ValidationLevel.THOROUGH)

        # FAST mode: bootstrap CI disabled
        assert monitor_fast.should_run_check('bootstrap_ci') is False

        # THOROUGH mode: bootstrap CI enabled
        assert monitor_thorough.should_run_check('bootstrap_ci') is True

    def test_budget_utilization_calculated(self):
        """Test budget utilization percentage is calculated"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()

        time.sleep(0.05)  # 50ms (50% of 100ms budget)

        stats = monitor.finish()

        assert 'budget_utilization' in stats
        # Should be around 50%
        assert 40 < stats['budget_utilization'] < 60

    def test_multiple_start_calls_reset(self):
        """Test multiple start() calls reset the monitor"""
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)

        monitor.start()
        time.sleep(0.01)
        monitor.checkpoint("first")

        # Start again (should reset)
        monitor.start()

        assert len(monitor.checkpoints) == 0
        assert monitor._finished is False


class TestGetBudget:
    """Test get_budget function"""

    def test_get_budget_fast(self):
        """Test getting FAST budget"""
        budget = get_budget(ValidationLevel.FAST)
        assert budget.level == ValidationLevel.FAST
        assert budget.max_overhead_ms == 100

    def test_get_budget_standard(self):
        """Test getting STANDARD budget"""
        budget = get_budget(ValidationLevel.STANDARD)
        assert budget.level == ValidationLevel.STANDARD
        assert budget.max_overhead_ms == 500

    def test_get_budget_thorough(self):
        """Test getting THOROUGH budget"""
        budget = get_budget(ValidationLevel.THOROUGH)
        assert budget.level == ValidationLevel.THOROUGH
        assert budget.max_overhead_ms == 2000

    def test_get_budget_invalid_level(self):
        """Test get_budget raises error for invalid level"""
        with pytest.raises(ValueError, match="Invalid validation level"):
            get_budget("invalid_level")


class TestBudgetProgression:
    """Test that budgets form a logical progression"""

    def test_budget_progression_overhead(self):
        """Test budgets increase from FAST to THOROUGH"""
        fast = BUDGETS[ValidationLevel.FAST]
        standard = BUDGETS[ValidationLevel.STANDARD]
        thorough = BUDGETS[ValidationLevel.THOROUGH]

        assert fast.max_overhead_ms < standard.max_overhead_ms
        assert standard.max_overhead_ms < thorough.max_overhead_ms

    def test_budget_progression_checks(self):
        """Test more checks enabled as level increases"""
        fast = BUDGETS[ValidationLevel.FAST]
        standard = BUDGETS[ValidationLevel.STANDARD]
        thorough = BUDGETS[ValidationLevel.THOROUGH]

        fast_enabled = sum(fast.checks_enabled.values())
        standard_enabled = sum(standard.checks_enabled.values())
        thorough_enabled = sum(thorough.checks_enabled.values())

        assert fast_enabled < standard_enabled
        assert standard_enabled < thorough_enabled


class TestGuardrailCompliance:
    """Test GUARDRAIL #1 compliance"""

    def test_no_silent_failures(self):
        """Test all errors are logged/raised, not silently swallowed"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)

        # These should not raise, but should log errors
        monitor.checkpoint("before_start")  # Error logged
        stats = monitor.finish()  # Error logged

        # Error should be explicit in response
        assert 'error' in stats or not stats['within_budget']

    def test_budget_violations_explicit(self):
        """Test budget violations are explicitly reported"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()
        time.sleep(0.15)  # Exceed budget

        stats = monitor.finish()

        # Violation must be explicit
        assert stats['within_budget'] is False
        assert len(stats['violations']) > 0
        assert stats['violations'][0]['excess_ms'] > 0

    def test_performance_tracking_mandatory(self):
        """Test performance is always tracked (no bypass)"""
        monitor = PerformanceMonitor(ValidationLevel.THOROUGH)
        monitor.start()
        time.sleep(0.01)

        stats = monitor.finish()

        # Performance MUST be tracked
        assert 'total_ms' in stats
        assert stats['total_ms'] > 0
        assert 'budget_ms' in stats

    def test_check_decisions_traceable(self):
        """Test decisions about which checks run are traceable"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)

        # Decision should be explicit (returns True/False, not None)
        decision = monitor.should_run_check('bootstrap_ci')
        assert decision is not None
        assert isinstance(decision, bool)


# Performance benchmark tests
class TestPerformanceBenchmarks:
    """Benchmark tests to verify overhead is acceptable"""

    def test_monitor_overhead_negligible(self):
        """Test performance monitoring itself has negligible overhead"""
        # Measure time with monitoring
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)
        start = time.time()
        monitor.start()
        monitor.checkpoint("test1")
        monitor.checkpoint("test2")
        monitor.finish()
        duration_with_monitoring = (time.time() - start) * 1000

        # Should be < 5ms
        assert duration_with_monitoring < 5, \
            f"Monitor overhead too high: {duration_with_monitoring:.2f}ms"

    def test_checkpoint_call_fast(self):
        """Test individual checkpoint() calls are fast"""
        monitor = PerformanceMonitor(ValidationLevel.FAST)
        monitor.start()

        # Measure checkpoint call time
        checkpoint_times = []
        for i in range(10):
            start = time.time()
            monitor.checkpoint(f"test_{i}")
            checkpoint_times.append((time.time() - start) * 1000)

        avg_checkpoint_time = sum(checkpoint_times) / len(checkpoint_times)

        # Each checkpoint should be < 1ms
        assert avg_checkpoint_time < 1, \
            f"Checkpoint calls too slow: {avg_checkpoint_time:.2f}ms average"
