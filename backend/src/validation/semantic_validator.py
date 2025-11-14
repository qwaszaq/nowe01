"""
Semantic Content Validator (Layer 3)
====================================

Validates semantic correctness of financial data.
Checks business rules, temporal consistency, and financial logic.

Validates:
- Year extraction and matching
- Statement type detection
- Currency and unit detection
- Financial equation balance
- Temporal consistency
- Value reasonableness

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

import re
from typing import Dict, Any, Optional, List, Tuple
import logging

from src.validation.quality_framework import (
    QualityValidator,
    QualityReport,
    ValidationSeverity,
    QualityLevel
)

logger = logging.getLogger(__name__)


class SemanticValidator(QualityValidator):
    """
    Validates semantic correctness of financial data

    Rejection criteria:
    - CRITICAL: Year mismatch, wrong statement type
    - ERROR: Missing units, suspicious values
    - WARNING: Inconsistencies, anomalies
    """

    # Statement type keywords
    BALANCE_SHEET_KEYWORDS = [
        "bilans", "balance sheet", "sytuacji finansowej",
        "aktywa", "pasywa", "assets", "liabilities"
    ]

    INCOME_STATEMENT_KEYWORDS = [
        "rachunek wyników", "income statement", "profit and loss",
        "przychody", "koszty", "zysk", "strata", "revenue", "expenses"
    ]

    CASH_FLOW_KEYWORDS = [
        "przepływy pieniężne", "cash flow",
        "środki pieniężne", "cash and cash"
    ]

    # Year patterns
    YEAR_PATTERNS = [
        r'\b(20\d{2})\b',  # 2023
        r'31\.12\.(20\d{2})',  # 31.12.2023
        r'grudnia\s+(20\d{2})',  # grudnia 2023
        r'grudzień\s+(20\d{2})',  # grudzień 2023
        r'December\s+31,?\s+(20\d{2})',  # December 31, 2023
        r'FY\s*(20\d{2})',  # FY 2023
        r'Q[1-4]\s+(20\d{2})',  # Q4 2023
    ]

    # Currency patterns
    CURRENCY_PATTERNS = {
        'PLN': [r'pln', r'zł', r'zloty', r'złotych'],
        'EUR': [r'eur', r'€', r'euro'],
        'USD': [r'usd', r'\$', r'dollar', r'dolar'],
    }

    # Unit patterns
    UNIT_PATTERNS = {
        'thousands': [r'tys\.?', r'tysiącach', r'tysięcy', r'thousand'],
        'millions': [r'mln', r'milion', r'million'],
    }

    def __init__(self, strict_mode: bool = True):
        super().__init__("SemanticValidator", strict_mode)

    def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> QualityReport:
        """
        Validate semantic correctness

        Args:
            data: Dict with keys:
                - table: Table data
                - extracted_year: Year extracted from table
                - extracted_statement_type: Statement type detected
                - extracted_unit: Unit detected
                - extracted_currency: Currency detected
            context: Optional context (expected_year, document_year, etc.)

        Returns:
            QualityReport
        """
        context = context or {}
        table = data.get("table", {})
        table_id = context.get("table_id", f"page_{table.get('page_num', 0)}")

        # Create initial report
        report = self._create_report("semantic", table_id, base_score=100.0)

        # ========================================
        # VALIDATION 1: Year Extraction
        # ========================================

        extracted_year = data.get("extracted_year")
        expected_year = context.get("expected_year")
        document_year = context.get("document_year")

        report.metrics["extracted_year"] = extracted_year
        report.metrics["expected_year"] = expected_year
        report.metrics["document_year"] = document_year

        if not extracted_year:
            report.add_issue(
                ValidationSeverity.WARNING,
                "SEMANTIC_NO_YEAR",
                "No year could be extracted from table",
                caption=table.get("caption", "")
            )
            self._adjust_score(report, 15, "No year extracted")

        elif expected_year and extracted_year != expected_year:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "SEMANTIC_YEAR_MISMATCH",
                f"Extracted year {extracted_year} does not match expected year {expected_year}",
                extracted_year=extracted_year,
                expected_year=expected_year
            )
            self._adjust_score(report, 50, "Year mismatch")

        elif document_year:
            # Check if year is within reasonable range of document year
            year_diff = abs(int(extracted_year) - int(document_year))
            if year_diff > 5:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "SEMANTIC_YEAR_FAR_FROM_DOCUMENT",
                    f"Extracted year {extracted_year} is {year_diff} years from document year {document_year}",
                    extracted_year=extracted_year,
                    document_year=document_year,
                    year_diff=year_diff
                )
                self._adjust_score(report, 10, "Year far from document")

        # ========================================
        # VALIDATION 2: Statement Type
        # ========================================

        extracted_statement_type = data.get("extracted_statement_type", "other")
        expected_statement_type = context.get("expected_statement_type")

        report.metrics["extracted_statement_type"] = extracted_statement_type
        report.metrics["expected_statement_type"] = expected_statement_type

        if expected_statement_type and extracted_statement_type != expected_statement_type:
            # Only error if strong mismatch (e.g., looking for balance sheet but found income statement)
            if (expected_statement_type == "balance_sheet" and
                extracted_statement_type == "income_statement") or \
               (expected_statement_type == "income_statement" and
                extracted_statement_type == "balance_sheet"):
                report.add_issue(
                    ValidationSeverity.ERROR,
                    "SEMANTIC_STATEMENT_TYPE_MISMATCH",
                    f"Expected {expected_statement_type} but found {extracted_statement_type}",
                    extracted=extracted_statement_type,
                    expected=expected_statement_type
                )
                self._adjust_score(report, 30, "Statement type mismatch")
            else:
                report.add_issue(
                    ValidationSeverity.INFO,
                    "SEMANTIC_STATEMENT_TYPE_DIFFERENT",
                    f"Statement type {extracted_statement_type} differs from expected {expected_statement_type}",
                    extracted=extracted_statement_type,
                    expected=expected_statement_type
                )

        # ========================================
        # VALIDATION 3: Currency and Units
        # ========================================

        extracted_currency = data.get("extracted_currency")
        extracted_unit = data.get("extracted_unit")
        unit_multiplier = data.get("unit_multiplier", 1)

        report.metrics["extracted_currency"] = extracted_currency
        report.metrics["extracted_unit"] = extracted_unit
        report.metrics["unit_multiplier"] = unit_multiplier

        if not extracted_currency:
            report.add_issue(
                ValidationSeverity.WARNING,
                "SEMANTIC_NO_CURRENCY",
                "No currency indicator found in table",
                caption=table.get("caption", "")
            )
            self._adjust_score(report, 10, "No currency")

        if not extracted_unit or extracted_unit == "units":
            report.add_issue(
                ValidationSeverity.WARNING,
                "SEMANTIC_NO_UNIT_MULTIPLIER",
                "No unit multiplier (thousands/millions) found",
                caption=table.get("caption", "")
            )
            self._adjust_score(report, 10, "No unit multiplier")

        # ========================================
        # VALIDATION 4: Financial Logic (if applicable)
        # ========================================

        if extracted_statement_type == "balance_sheet":
            balance_check = self._validate_balance_sheet_equation(table)
            if balance_check:
                is_balanced, assets, liabilities_equity, diff = balance_check

                if not is_balanced:
                    tolerance = 0.01  # 1% tolerance
                    if assets > 0 and abs(diff / assets) > tolerance:
                        report.add_issue(
                            ValidationSeverity.ERROR,
                            "SEMANTIC_BALANCE_SHEET_UNBALANCED",
                            f"Balance sheet equation doesn't balance: "
                            f"Assets={assets:,.0f}, Liabilities+Equity={liabilities_equity:,.0f}, "
                            f"Diff={diff:,.0f}",
                            assets=assets,
                            liabilities_equity=liabilities_equity,
                            difference=diff
                        )
                        self._adjust_score(report, 25, "Unbalanced balance sheet")
                    else:
                        report.add_issue(
                            ValidationSeverity.INFO,
                            "SEMANTIC_BALANCE_SHEET_MINOR_IMBALANCE",
                            f"Minor balance sheet imbalance (within tolerance): Diff={diff:,.0f}",
                            assets=assets,
                            liabilities_equity=liabilities_equity,
                            difference=diff
                        )

        # ========================================
        # VALIDATION 5: Value Reasonableness
        # ========================================

        numeric_values = self._extract_numeric_values(table)
        if numeric_values:
            # Check for suspicious patterns
            zero_count = sum(1 for v in numeric_values if v == 0)
            if zero_count / len(numeric_values) > 0.8:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "SEMANTIC_MOSTLY_ZEROS",
                    f"{zero_count} of {len(numeric_values)} numeric values are zero",
                    zero_ratio=round(zero_count / len(numeric_values), 2)
                )
                self._adjust_score(report, 15, "Mostly zeros")

            # Check for unreasonably large values (likely extraction error)
            max_value = max(numeric_values)
            if unit_multiplier == 1000 and max_value > 1e12:  # >1 trillion in thousands
                report.add_issue(
                    ValidationSeverity.ERROR,
                    "SEMANTIC_UNREASONABLE_VALUE",
                    f"Suspiciously large value detected: {max_value:,.0f}",
                    max_value=max_value
                )
                self._adjust_score(report, 20, "Unreasonable value")

        # Final quality level
        report.quality_level = QualityLevel.from_score(report.quality_score)

        logger.info(
            f"Semantic validation complete: {table_id} | "
            f"Score: {report.quality_score:.1f}% | "
            f"Year: {extracted_year} | "
            f"Type: {extracted_statement_type}"
        )

        return report

    def _validate_balance_sheet_equation(
        self,
        table: Dict[str, Any]
    ) -> Optional[Tuple[bool, float, float, float]]:
        """
        Validate balance sheet equation: Assets = Liabilities + Equity

        Returns:
            (is_balanced, assets, liabilities_equity, difference) or None
        """
        headers = table.get("headers", [])
        rows = table.get("rows", [])

        # Look for total assets, total liabilities, and total equity rows
        assets_total = None
        liabilities_total = None
        equity_total = None

        for row in rows:
            if not row:
                continue

            row_label = str(row[0]).lower()

            # Find assets total
            if any(keyword in row_label for keyword in ["aktywa razem", "total assets", "aktywa ogółem"]):
                assets_total = self._parse_numeric_value(row[-1])  # Last column often has total

            # Find liabilities total
            if any(keyword in row_label for keyword in [
                "zobowiązania razem", "total liabilities", "zobowiązania ogółem"
            ]):
                liabilities_total = self._parse_numeric_value(row[-1])

            # Find equity total
            if any(keyword in row_label for keyword in [
                "kapitał własny", "equity", "shareholders' equity", "kapitał ogółem"
            ]):
                equity_total = self._parse_numeric_value(row[-1])

        # Check if we found the necessary values
        if assets_total and (liabilities_total or equity_total):
            liabilities_equity = (liabilities_total or 0) + (equity_total or 0)
            diff = abs(assets_total - liabilities_equity)
            is_balanced = diff < 100  # Allow small rounding differences

            return is_balanced, assets_total, liabilities_equity, diff

        return None

    def _extract_numeric_values(self, table: Dict[str, Any]) -> List[float]:
        """Extract all numeric values from table"""
        rows = table.get("rows", [])
        values = []

        for row in rows:
            for cell in row[1:]:  # Skip first column (labels)
                value = self._parse_numeric_value(cell)
                if value is not None:
                    values.append(value)

        return values

    def _parse_numeric_value(self, value_str: Any) -> Optional[float]:
        """Parse numeric value from string"""
        if value_str is None:
            return None

        value_str = str(value_str).strip()

        if not value_str or value_str in ['-', '—', 'N/A', 'n/a']:
            return None

        # Remove spaces and common separators
        cleaned = value_str.replace(' ', '').replace(',', '').replace('.', '')

        try:
            return float(cleaned)
        except ValueError:
            return None


def validate_semantic_content(
    table: Dict[str, Any],
    extracted_metadata: Dict[str, Any],
    expected_metadata: Optional[Dict[str, Any]] = None,
    strict_mode: bool = True
) -> QualityReport:
    """
    Convenience function to validate semantic content

    Args:
        table: Table data
        extracted_metadata: Extracted metadata (year, type, unit, currency)
        expected_metadata: Expected metadata for comparison
        strict_mode: Errors cause rejection

    Returns:
        QualityReport
    """
    validator = SemanticValidator(strict_mode=strict_mode)

    data = {
        "table": table,
        **extracted_metadata
    }

    context = expected_metadata or {}

    return validator.validate(data, context)
