"""
Data Quality Guarantee Framework
=================================

Core Principle: NEVER silently accept bad data
Philosophy: Fail loud, not silent. Rejection is better than corruption.

Quality Layers:
1. PDF Format Validation (pre-processing)
2. Table Structure Validation (extraction)
3. Data Type Validation (cell-level)
4. Semantic Validation (content)
5. Cross-Table Consistency (document)
6. Query-Time Verification (retrieval)

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "A"  # 90-100% - Production ready
    GOOD = "B"       # 70-89% - Usable with minor warnings
    FAIR = "C"       # 50-69% - Usable but needs review
    POOR = "D"       # 30-49% - Manual review required
    FAILED = "F"     # <30% - Rejected

    @classmethod
    def from_score(cls, score: float) -> 'QualityLevel':
        """Convert numeric score to quality level"""
        if score >= 90:
            return cls.EXCELLENT
        elif score >= 70:
            return cls.GOOD
        elif score >= 50:
            return cls.FAIR
        elif score >= 30:
            return cls.POOR
        else:
            return cls.FAILED


class ValidationSeverity(Enum):
    """Severity of validation issues"""
    CRITICAL = "critical"  # Causes rejection
    ERROR = "error"        # Severe issue, should review
    WARNING = "warning"    # Minor issue, informational
    INFO = "info"          # Quality metric, no action needed


@dataclass
class ValidationIssue:
    """Single validation issue"""
    severity: ValidationSeverity
    code: str  # Machine-readable code (e.g., "TABLE_EMPTY_HEADERS")
    message: str  # Human-readable message
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp
        }


@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""
    entity_type: str  # "pdf", "table", "document", "extraction"
    entity_id: str
    quality_score: float  # 0-100
    quality_level: QualityLevel
    passed: bool  # Overall pass/fail
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_issue(self, severity: ValidationSeverity, code: str, message: str, **context):
        """Add validation issue"""
        issue = ValidationIssue(
            severity=severity,
            code=code,
            message=message,
            context=context
        )
        self.issues.append(issue)

        # Critical issues cause failure
        if severity == ValidationSeverity.CRITICAL:
            self.passed = False
            logger.error(f"CRITICAL validation issue: {message} (entity: {self.entity_id})")
        elif severity == ValidationSeverity.ERROR:
            logger.warning(f"ERROR validation issue: {message} (entity: {self.entity_id})")

    def has_critical_issues(self) -> bool:
        """Check if any critical issues exist"""
        return any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)

    def has_errors(self) -> bool:
        """Check if any errors exist"""
        return any(issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
                   for issue in self.issues)

    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues of specific severity"""
        return [issue for issue in self.issues if issue.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "quality_score": round(self.quality_score, 2),
            "quality_level": self.quality_level.value,
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "summary": {
                "total_issues": len(self.issues),
                "critical": len(self.get_issues_by_severity(ValidationSeverity.CRITICAL)),
                "errors": len(self.get_issues_by_severity(ValidationSeverity.ERROR)),
                "warnings": len(self.get_issues_by_severity(ValidationSeverity.WARNING)),
                "info": len(self.get_issues_by_severity(ValidationSeverity.INFO))
            }
        }

    def __str__(self) -> str:
        """Human-readable summary"""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return (
            f"{status} | Quality: {self.quality_level.value} ({self.quality_score:.1f}%) | "
            f"{self.entity_type.upper()}: {self.entity_id} | "
            f"Issues: {len(self.issues)} ({len(self.get_issues_by_severity(ValidationSeverity.CRITICAL))} critical)"
        )


class QualityValidator:
    """Base class for quality validators"""

    def __init__(self, name: str, strict_mode: bool = True):
        """
        Initialize validator

        Args:
            name: Validator name
            strict_mode: If True, errors cause rejection. If False, only critical issues reject.
        """
        self.name = name
        self.strict_mode = strict_mode
        logger.info(f"Initialized {name} validator (strict_mode={strict_mode})")

    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> QualityReport:
        """
        Validate data and return quality report

        Args:
            data: Data to validate
            context: Optional context for validation

        Returns:
            QualityReport with assessment
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def _create_report(self, entity_type: str, entity_id: str, base_score: float = 100.0) -> QualityReport:
        """Create initial quality report"""
        return QualityReport(
            entity_type=entity_type,
            entity_id=entity_id,
            quality_score=base_score,
            quality_level=QualityLevel.from_score(base_score),
            passed=True
        )

    def _adjust_score(self, report: QualityReport, penalty: float, reason: str):
        """
        Adjust quality score downward

        Args:
            report: Quality report to adjust
            penalty: Points to deduct (0-100)
            reason: Reason for penalty
        """
        old_score = report.quality_score
        report.quality_score = max(0, report.quality_score - penalty)
        report.quality_level = QualityLevel.from_score(report.quality_score)

        logger.debug(
            f"Score adjusted: {old_score:.1f} → {report.quality_score:.1f} "
            f"(-{penalty:.1f} points: {reason})"
        )

        # Auto-fail if score too low
        if report.quality_score < 30:
            report.passed = False


class QualityGuaranteeSystem:
    """
    Master quality guarantee system

    Orchestrates all validators and enforces quality guarantees
    """

    def __init__(self, strict_mode: bool = True, min_score: float = 50.0):
        """
        Initialize quality guarantee system

        Args:
            strict_mode: If True, errors cause rejection
            min_score: Minimum acceptable quality score
        """
        self.strict_mode = strict_mode
        self.min_score = min_score
        self.validators: Dict[str, QualityValidator] = {}

        logger.info(
            f"QualityGuaranteeSystem initialized: strict_mode={strict_mode}, "
            f"min_score={min_score}"
        )

    def register_validator(self, stage: str, validator: QualityValidator):
        """Register a validator for specific stage"""
        self.validators[stage] = validator
        logger.info(f"Registered validator for stage: {stage}")

    def validate_stage(self, stage: str, data: Any, context: Optional[Dict[str, Any]] = None) -> QualityReport:
        """
        Validate data at specific stage

        Args:
            stage: Processing stage name
            data: Data to validate
            context: Optional context

        Returns:
            QualityReport

        Raises:
            ValueError: If stage not found
        """
        if stage not in self.validators:
            raise ValueError(f"No validator registered for stage: {stage}")

        validator = self.validators[stage]
        report = validator.validate(data, context)

        # Enforce minimum score
        if report.quality_score < self.min_score:
            report.passed = False
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "QUALITY_SCORE_TOO_LOW",
                f"Quality score {report.quality_score:.1f}% below minimum {self.min_score:.1f}%"
            )

        # Log result
        logger.info(f"Validation complete: {report}")

        return report

    def validate_pipeline(
        self,
        stages_data: List[Tuple[str, Any, Optional[Dict[str, Any]]]]
    ) -> Tuple[bool, List[QualityReport]]:
        """
        Validate data through multiple stages

        Args:
            stages_data: List of (stage_name, data, context) tuples

        Returns:
            (overall_passed, list_of_reports)
        """
        reports = []
        overall_passed = True

        for stage, data, context in stages_data:
            try:
                report = self.validate_stage(stage, data, context)
                reports.append(report)

                if not report.passed:
                    overall_passed = False
                    logger.error(f"Pipeline failed at stage: {stage}")

                    if self.strict_mode:
                        # Stop on first failure in strict mode
                        logger.error("Strict mode: stopping pipeline on failure")
                        break

            except Exception as e:
                logger.error(f"Validation exception at stage {stage}: {e}", exc_info=True)
                overall_passed = False

                # Create error report
                error_report = QualityReport(
                    entity_type="validation_error",
                    entity_id=stage,
                    quality_score=0,
                    quality_level=QualityLevel.FAILED,
                    passed=False
                )
                error_report.add_issue(
                    ValidationSeverity.CRITICAL,
                    "VALIDATION_EXCEPTION",
                    f"Validation failed with exception: {str(e)}"
                )
                reports.append(error_report)
                break

        return overall_passed, reports

    def get_summary(self, reports: List[QualityReport]) -> Dict[str, Any]:
        """Get summary of multiple quality reports"""
        total_issues = sum(len(r.issues) for r in reports)
        failed_reports = [r for r in reports if not r.passed]

        avg_score = sum(r.quality_score for r in reports) / max(len(reports), 1)

        return {
            "total_stages": len(reports),
            "passed_stages": len(reports) - len(failed_reports),
            "failed_stages": len(failed_reports),
            "average_quality_score": round(avg_score, 2),
            "overall_quality_level": QualityLevel.from_score(avg_score).value,
            "total_issues": total_issues,
            "critical_issues": sum(
                len(r.get_issues_by_severity(ValidationSeverity.CRITICAL))
                for r in reports
            ),
            "error_issues": sum(
                len(r.get_issues_by_severity(ValidationSeverity.ERROR))
                for r in reports
            ),
            "reports": [r.to_dict() for r in reports]
        }


# Global quality guarantee system instance
_quality_system: Optional[QualityGuaranteeSystem] = None


def get_quality_system(strict_mode: bool = True, min_score: float = 50.0) -> QualityGuaranteeSystem:
    """Get or create global quality guarantee system"""
    global _quality_system

    if _quality_system is None:
        _quality_system = QualityGuaranteeSystem(strict_mode=strict_mode, min_score=min_score)

    return _quality_system


def reset_quality_system():
    """Reset global quality system (useful for testing)"""
    global _quality_system
    _quality_system = None
