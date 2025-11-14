"""
Data Quality Validation Framework
==================================

Multi-layer quality guarantee system for financial data extraction.

Layers:
1. PDF Quality Validation (pre-processing)
2. Table Structure Validation (extraction)
3. Semantic Content Validation (content)
4. Query-Time Validation (retrieval)

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

from src.validation.quality_framework import (
    QualityLevel,
    ValidationSeverity,
    ValidationIssue,
    QualityReport,
    QualityValidator,
    QualityGuaranteeSystem,
    get_quality_system,
    reset_quality_system
)

from src.validation.pdf_quality_validator import (
    PDFQualityValidator,
    validate_pdf_quality
)

from src.validation.table_quality_validator import (
    TableQualityValidator,
    validate_table_quality
)

from src.validation.semantic_validator import (
    SemanticValidator,
    validate_semantic_content
)

__all__ = [
    # Core framework
    'QualityLevel',
    'ValidationSeverity',
    'ValidationIssue',
    'QualityReport',
    'QualityValidator',
    'QualityGuaranteeSystem',
    'get_quality_system',
    'reset_quality_system',

    # Validators
    'PDFQualityValidator',
    'TableQualityValidator',
    'SemanticValidator',

    # Convenience functions
    'validate_pdf_quality',
    'validate_table_quality',
    'validate_semantic_content',
]
