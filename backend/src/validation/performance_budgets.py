"""
Performance budgets for analytics quality validation

GUARDRAIL: Quality validation MUST NOT make system unusable
Target: Validation overhead < 25% of analysis time

This module defines performance budgets for three validation levels:
- FAST: < 100ms overhead (minimal checks, exploratory analysis)
- STANDARD: < 500ms overhead (recommended, normal use)
- THOROUGH: < 2000ms overhead (full validation, high-stakes decisions)

Created: 2025-11-14
Addresses: ANALYTICS_QUALITY_CONCERNS.md - Performance Degradation Risk
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import time
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation thoroughness levels

    FAST: Minimal checks for quick exploratory analysis
    STANDARD: Recommended level with balanced checks
    THOROUGH: Full validation for high-stakes decisions
    """
    FAST = "fast"
    STANDARD = "standard"
    THOROUGH = "thorough"


@dataclass
class PerformanceBudget:
    """Performance budget for a validation level

    Defines maximum allowed overhead and which checks are enabled
    """
    level: ValidationLevel
    max_overhead_ms: int        # Maximum validation overhead
    max_total_ms: Optional[int] # Maximum total analysis time (including validation)
    checks_enabled: Dict[str, bool]  # Which checks to run

    def is_check_enabled(self, check_name: str) -> bool:
        """Check if a specific validation is enabled at this level"""
        return self.checks_enabled.get(check_name, False)


# PERFORMANCE BUDGETS (measured in milliseconds)
BUDGETS = {
    ValidationLevel.FAST: PerformanceBudget(
        level=ValidationLevel.FAST,
        max_overhead_ms=100,
        max_total_ms=500,
        checks_enabled={
            'input_quality': True,        # Always check input quality
            'sample_size': True,          # Always check sample size
            'data_gaps': False,           # Skip: too slow (~50ms)
            'statistical_tests': False,   # Skip: too slow (~100-200ms)
            'assumption_validation': False,  # Skip: too slow (~150ms)
            'bootstrap_ci': False,        # Skip: very slow (~500ms+)
            'multiple_testing_correction': False,
            'detailed_diagnostics': False
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
            'assumption_validation': False,  # Skip detailed assumption checks
            'bootstrap_ci': False,        # Use parametric CIs (faster)
            'confidence_intervals': True,  # Check CI width
            'residual_analysis': False,    # Skip in STANDARD
            'multiple_testing_correction': True,
            'detailed_diagnostics': False
        }
    ),
    ValidationLevel.THOROUGH: PerformanceBudget(
        level=ValidationLevel.THOROUGH,
        max_overhead_ms=2000,
        max_total_ms=None,  # No limit on total time
        checks_enabled={
            'input_quality': True,
            'sample_size': True,
            'data_gaps': True,
            'statistical_tests': True,
            'assumption_validation': True,  # Full validation
            'bootstrap_ci': True,           # Non-parametric CIs
            'confidence_intervals': True,   # Check CI width
            'residual_analysis': True,      # Full residual diagnostics
            'multiple_testing_correction': True,
            'detailed_diagnostics': True
        }
    )
}


@dataclass
class PerformanceCheckpoint:
    """A single performance checkpoint measurement"""
    name: str
    elapsed_ms: float
    timestamp: float


class PerformanceMonitor:
    """Monitor and enforce performance budgets

    Usage:
        monitor = PerformanceMonitor(ValidationLevel.STANDARD)
        monitor.start()

        # ... do some work ...
        monitor.checkpoint("input_validation")

        # ... do more work ...
        monitor.checkpoint("statistical_tests")

        stats = monitor.finish()
        if not stats['within_budget']:
            logger.warning(f"Budget exceeded: {stats['total_ms']}ms")

    GUARDRAIL COMPLIANCE:
    - Explicit performance tracking (no silent slowness)
    - Automatic warnings when budget exceeded
    - Detailed breakdown for optimization
    """

    def __init__(self, level: ValidationLevel):
        """Initialize performance monitor for a validation level

        Args:
            level: Validation level (FAST/STANDARD/THOROUGH)
        """
        if level not in BUDGETS:
            raise ValueError(
                f"Invalid validation level: {level}. "
                f"Must be one of {list(BUDGETS.keys())}"
            )

        self.budget = BUDGETS[level]
        self.start_time: Optional[float] = None
        self.checkpoints: List[PerformanceCheckpoint] = []
        self._finished = False

    def start(self):
        """Start performance monitoring

        GUARDRAIL: Must be called before any validation work
        """
        if self.start_time is not None:
            logger.warning(
                "PerformanceMonitor.start() called twice. "
                "Resetting to new start time."
            )

        self.start_time = time.time()
        self.checkpoints = []
        self._finished = False

    def checkpoint(self, name: str):
        """Record a checkpoint with elapsed time

        Args:
            name: Descriptive name for this checkpoint

        GUARDRAIL: Automatically warns if budget exceeded at checkpoint
        """
        if self.start_time is None:
            logger.error(
                "PerformanceMonitor.checkpoint() called before start(). "
                "Call start() first."
            )
            return

        current_time = time.time()
        elapsed_ms = (current_time - self.start_time) * 1000

        checkpoint = PerformanceCheckpoint(
            name=name,
            elapsed_ms=elapsed_ms,
            timestamp=current_time
        )
        self.checkpoints.append(checkpoint)

        # Check if we're exceeding budget
        if elapsed_ms > self.budget.max_overhead_ms:
            logger.warning(
                f"⚠️ Performance budget exceeded at checkpoint '{name}': "
                f"{elapsed_ms:.0f}ms > {self.budget.max_overhead_ms}ms "
                f"(level: {self.budget.level.value})"
            )

    def finish(self) -> Dict[str, any]:
        """Finish monitoring and return performance statistics

        Returns:
            Dict with:
                - total_ms: Total elapsed time
                - budget_ms: Budget limit
                - within_budget: True if within budget
                - checkpoints: List of checkpoint times
                - violations: List of budget violations

        GUARDRAIL: Explicit error if budget violated
        """
        if self.start_time is None:
            logger.error("PerformanceMonitor.finish() called before start()")
            return {
                'total_ms': 0.0,
                'budget_ms': self.budget.max_overhead_ms,
                'within_budget': False,
                'error': 'Not started',
                'checkpoints': {}
            }

        if self._finished:
            logger.warning("PerformanceMonitor.finish() called twice")

        total_ms = (time.time() - self.start_time) * 1000
        within_budget = total_ms <= self.budget.max_overhead_ms

        # Build checkpoint summary
        checkpoint_summary = {}
        for i, cp in enumerate(self.checkpoints):
            # Calculate time since last checkpoint
            if i == 0:
                duration = cp.elapsed_ms
            else:
                duration = cp.elapsed_ms - self.checkpoints[i-1].elapsed_ms

            checkpoint_summary[cp.name] = {
                'elapsed_total_ms': cp.elapsed_ms,
                'duration_ms': duration
            }

        # Find violations
        violations = []
        if not within_budget:
            violations.append({
                'checkpoint': 'total',
                'actual_ms': total_ms,
                'budget_ms': self.budget.max_overhead_ms,
                'excess_ms': total_ms - self.budget.max_overhead_ms
            })

        # Log final result
        if not within_budget:
            logger.error(
                f"🔴 PERFORMANCE BUDGET VIOLATED: "
                f"{total_ms:.0f}ms > {self.budget.max_overhead_ms}ms "
                f"(level: {self.budget.level.value}). "
                f"Checkpoints: {list(checkpoint_summary.keys())}"
            )
        else:
            logger.debug(
                f"✅ Performance budget met: "
                f"{total_ms:.0f}ms <= {self.budget.max_overhead_ms}ms "
                f"(level: {self.budget.level.value})"
            )

        self._finished = True

        return {
            'total_ms': total_ms,
            'budget_ms': self.budget.max_overhead_ms,
            'within_budget': within_budget,
            'validation_level': self.budget.level.value,
            'checkpoints': checkpoint_summary,
            'violations': violations,
            'budget_utilization': (total_ms / self.budget.max_overhead_ms) * 100
        }

    def should_run_check(self, check_name: str) -> bool:
        """Check if a validation should run based on performance budget

        Args:
            check_name: Name of the check (e.g., 'bootstrap_ci', 'statistical_tests')

        Returns:
            True if check should run, False if skipped for performance

        GUARDRAIL: Explicit decision tracking for which checks run
        """
        enabled = self.budget.is_check_enabled(check_name)

        if not enabled:
            logger.debug(
                f"Skipping check '{check_name}' "
                f"(disabled in {self.budget.level.value} mode)"
            )

        return enabled


def get_budget(level: ValidationLevel) -> PerformanceBudget:
    """Get performance budget for a validation level

    Args:
        level: Validation level

    Returns:
        PerformanceBudget instance

    Raises:
        ValueError: If level is invalid
    """
    if level not in BUDGETS:
        raise ValueError(
            f"Invalid validation level: {level}. "
            f"Must be one of {list(BUDGETS.keys())}"
        )

    return BUDGETS[level]


# Export public API
__all__ = [
    'ValidationLevel',
    'PerformanceBudget',
    'PerformanceMonitor',
    'PerformanceCheckpoint',
    'BUDGETS',
    'get_budget'
]
