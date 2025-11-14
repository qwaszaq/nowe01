"""
Table Quality Validator (Layer 2)
==================================

Validates extracted table structure and content quality.
Detects extraction artifacts and data quality issues.

Validates:
- Table structure (headers, rows, cells)
- Data completeness
- Data type consistency
- Merged cell artifacts
- Empty/null data

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

import re
from typing import Dict, Any, Optional, List
import logging

from src.validation.quality_framework import (
    QualityValidator,
    QualityReport,
    ValidationSeverity,
    QualityLevel
)

logger = logging.getLogger(__name__)


class TableQualityValidator(QualityValidator):
    """
    Validates extracted table quality

    Rejection criteria:
    - CRITICAL: Empty table, no headers, all nulls
    - ERROR: Missing data, inconsistent structure
    - WARNING: Suspicious patterns, potential artifacts
    """

    # Thresholds
    MIN_HEADERS = 2
    MIN_ROWS = 1
    MAX_EMPTY_CELL_RATIO = 0.5  # Max 50% empty cells
    MAX_DUPLICATE_ROW_RATIO = 0.3  # Max 30% duplicate rows

    def __init__(self, strict_mode: bool = True, is_financial: bool = True):
        """
        Initialize table quality validator

        Args:
            strict_mode: If True, errors cause rejection
            is_financial: If True, apply financial table rules
        """
        super().__init__("TableQualityValidator", strict_mode)
        self.is_financial = is_financial

    def validate(self, table: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> QualityReport:
        """
        Validate table quality

        Args:
            table: Table dict with keys: headers, rows, caption, page_num
            context: Optional context (document_id, table_index, etc.)

        Returns:
            QualityReport
        """
        context = context or {}
        table_id = context.get("table_id", f"page_{table.get('page_num', 0)}")

        # Create initial report
        report = self._create_report("table", table_id, base_score=100.0)

        # Extract table components
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        caption = table.get("caption", "")
        page_num = table.get("page_num", 0)

        report.metrics["page_num"] = page_num
        report.metrics["caption"] = caption
        report.metrics["header_count"] = len(headers)
        report.metrics["row_count"] = len(rows)

        # ========================================
        # VALIDATION 1: Structure
        # ========================================

        # Check headers exist
        if not headers or len(headers) < self.MIN_HEADERS:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "TABLE_INSUFFICIENT_HEADERS",
                f"Table has {len(headers)} headers, minimum {self.MIN_HEADERS} required",
                header_count=len(headers)
            )
            self._adjust_score(report, 50, "Insufficient headers")

        # Check rows exist
        if not rows or len(rows) < self.MIN_ROWS:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "TABLE_NO_ROWS",
                f"Table has {len(rows)} rows, minimum {self.MIN_ROWS} required",
                row_count=len(rows)
            )
            self._adjust_score(report, 50, "No rows")

        if not headers or not rows:
            # Can't continue validation without basic structure
            return report

        # ========================================
        # VALIDATION 2: Header Quality
        # ========================================

        empty_headers = sum(1 for h in headers if not str(h).strip())
        if empty_headers > 0:
            ratio = empty_headers / len(headers)
            report.add_issue(
                ValidationSeverity.ERROR,
                "TABLE_EMPTY_HEADERS",
                f"{empty_headers} of {len(headers)} headers are empty",
                empty_headers=empty_headers,
                ratio=round(ratio, 2)
            )
            self._adjust_score(report, 20 * ratio, "Empty headers")

        # Check for duplicate headers
        header_strs = [str(h).strip().lower() for h in headers if str(h).strip()]
        duplicate_headers = len(header_strs) - len(set(header_strs))
        if duplicate_headers > 0:
            report.add_issue(
                ValidationSeverity.WARNING,
                "TABLE_DUPLICATE_HEADERS",
                f"{duplicate_headers} duplicate headers detected (may indicate merged cells)",
                duplicate_count=duplicate_headers
            )
            self._adjust_score(report, 10, "Duplicate headers")

        # Check for suspicious header patterns (artifacts from merged cells)
        suspicious_patterns = [r'^\s*$', r'^\.+$', r'^\-+$', r'^\|+$']
        suspicious_headers = 0
        for header in headers:
            header_str = str(header).strip()
            if any(re.match(pattern, header_str) for pattern in suspicious_patterns):
                suspicious_headers += 1

        if suspicious_headers > 0:
            report.add_issue(
                ValidationSeverity.WARNING,
                "TABLE_SUSPICIOUS_HEADERS",
                f"{suspicious_headers} headers contain suspicious patterns (likely extraction artifacts)",
                suspicious_count=suspicious_headers
            )
            self._adjust_score(report, 5 * suspicious_headers, "Suspicious headers")

        # ========================================
        # VALIDATION 3: Row Quality
        # ========================================

        # Check column consistency
        inconsistent_rows = 0
        for idx, row in enumerate(rows):
            if len(row) != len(headers):
                inconsistent_rows += 1

        if inconsistent_rows > 0:
            ratio = inconsistent_rows / len(rows)
            report.add_issue(
                ValidationSeverity.ERROR,
                "TABLE_INCONSISTENT_COLUMNS",
                f"{inconsistent_rows} of {len(rows)} rows have mismatched column count",
                inconsistent_rows=inconsistent_rows,
                ratio=round(ratio, 2)
            )
            self._adjust_score(report, 30 * ratio, "Inconsistent columns")

        # Calculate empty cell ratio
        total_cells = sum(len(row) for row in rows)
        empty_cells = sum(
            1 for row in rows for cell in row
            if not str(cell).strip() or str(cell).strip() in ['-', '—', 'N/A', 'n/a']
        )

        empty_cell_ratio = empty_cells / max(total_cells, 1)
        report.metrics["empty_cell_ratio"] = round(empty_cell_ratio, 2)

        if empty_cell_ratio > self.MAX_EMPTY_CELL_RATIO:
            report.add_issue(
                ValidationSeverity.ERROR,
                "TABLE_HIGH_EMPTY_CELLS",
                f"{empty_cell_ratio:.0%} of cells are empty (max {self.MAX_EMPTY_CELL_RATIO:.0%})",
                empty_cell_ratio=round(empty_cell_ratio, 2)
            )
            self._adjust_score(report, 25, "High empty cell ratio")

        # Check for duplicate rows (may indicate extraction error)
        row_strs = ["|".join(str(cell).strip() for cell in row) for row in rows]
        unique_rows = len(set(row_strs))
        duplicate_rows = len(rows) - unique_rows

        if duplicate_rows > 0:
            ratio = duplicate_rows / len(rows)
            if ratio > self.MAX_DUPLICATE_ROW_RATIO:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "TABLE_DUPLICATE_ROWS",
                    f"{duplicate_rows} duplicate rows detected ({ratio:.0%} of table)",
                    duplicate_rows=duplicate_rows,
                    ratio=round(ratio, 2)
                )
                self._adjust_score(report, 15, "Duplicate rows")

        # ========================================
        # VALIDATION 4: Financial Table Specific
        # ========================================

        if self.is_financial:
            # Check for numeric data in non-header columns
            numeric_columns = self._identify_numeric_columns(headers, rows)
            report.metrics["numeric_columns"] = len(numeric_columns)

            if len(numeric_columns) == 0:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "TABLE_NO_NUMERIC_DATA",
                    "No numeric columns detected in financial table",
                    header_count=len(headers)
                )
                self._adjust_score(report, 10, "No numeric data")

            # Check for year markers in headers
            year_pattern = r'\b20\d{2}\b'
            year_headers = [h for h in headers if re.search(year_pattern, str(h))]
            report.metrics["year_headers"] = len(year_headers)

            if len(year_headers) == 0 and len(numeric_columns) > 1:
                report.add_issue(
                    ValidationSeverity.INFO,
                    "TABLE_NO_YEAR_MARKERS",
                    "No year markers found in headers (may be non-comparative table)"
                )

            # Check for currency/unit indicators
            unit_patterns = [
                r'tys\.',
                r'mln',
                r'PLN',
                r'EUR',
                r'USD',
                r'thousand',
                r'million'
            ]

            has_unit_indicator = (
                any(re.search(pattern, caption, re.IGNORECASE) for pattern in unit_patterns) or
                any(
                    any(re.search(pattern, str(h), re.IGNORECASE) for pattern in unit_patterns)
                    for h in headers
                )
            )

            report.metrics["has_unit_indicator"] = has_unit_indicator

            if not has_unit_indicator:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "TABLE_NO_UNIT_INDICATOR",
                    "No unit/currency indicator found in caption or headers"
                )
                self._adjust_score(report, 5, "No unit indicator")

        # ========================================
        # VALIDATION 5: Overall Assessment
        # ========================================

        # Check if table is completely empty
        all_cells_empty = all(
            not str(cell).strip()
            for row in rows
            for cell in row
        )

        if all_cells_empty:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "TABLE_ALL_EMPTY",
                "All table cells are empty"
            )
            report.quality_score = 0
            return report

        # Final quality level
        report.quality_level = QualityLevel.from_score(report.quality_score)

        # Log result
        logger.info(
            f"Table quality validated: {table_id} | "
            f"Score: {report.quality_score:.1f}% | "
            f"Headers: {len(headers)} | "
            f"Rows: {len(rows)} | "
            f"Empty ratio: {empty_cell_ratio:.1%}"
        )

        return report

    def _identify_numeric_columns(self, headers: List[str], rows: List[List[str]]) -> List[int]:
        """
        Identify which columns contain primarily numeric data

        Returns:
            List of column indices
        """
        if not rows or not headers:
            return []

        numeric_columns = []

        for col_idx in range(len(headers)):
            numeric_count = 0
            total_count = 0

            for row in rows:
                if col_idx >= len(row):
                    continue

                cell = str(row[col_idx]).strip()

                if not cell or cell in ['-', '—', 'N/A', 'n/a']:
                    continue

                total_count += 1

                # Check if numeric (with or without separators)
                numeric_pattern = r'^-?[\d\s,\.]+$'
                if re.match(numeric_pattern, cell):
                    numeric_count += 1

            # Column is numeric if >70% of non-empty cells are numeric
            if total_count > 0 and numeric_count / total_count > 0.7:
                numeric_columns.append(col_idx)

        return numeric_columns


def validate_table_quality(
    table: Dict[str, Any],
    is_financial: bool = True,
    strict_mode: bool = True
) -> QualityReport:
    """
    Convenience function to validate table quality

    Args:
        table: Table dict
        is_financial: Apply financial table rules
        strict_mode: Errors cause rejection

    Returns:
        QualityReport
    """
    validator = TableQualityValidator(
        strict_mode=strict_mode,
        is_financial=is_financial
    )
    return validator.validate(table)
