"""
PDF Quality Validator (Layer 1)
================================

Validates PDF quality BEFORE extraction begins.
Detects issues that will cause extraction failures.

Validates:
- PDF format and structure
- Scanned vs digital PDF
- Encryption/protection
- Layout complexity
- Size and page count

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from src.validation.quality_framework import (
    QualityValidator,
    QualityReport,
    ValidationSeverity,
    QualityLevel
)

logger = logging.getLogger(__name__)


class PDFQualityValidator(QualityValidator):
    """
    Validates PDF quality before extraction

    Rejection criteria:
    - CRITICAL: Encrypted, corrupted, or scanned PDFs (without OCR)
    - ERROR: Poor text extractability, complex layouts
    - WARNING: Large file size, many pages
    """

    # Thresholds
    MIN_TEXT_DENSITY = 50  # chars per page minimum for digital PDF
    MAX_PAGES = 10000
    MAX_FILE_SIZE_MB = 500
    WARN_FILE_SIZE_MB = 100
    WARN_PAGES = 1000

    def __init__(self, strict_mode: bool = True, require_digital: bool = True):
        """
        Initialize PDF quality validator

        Args:
            strict_mode: If True, errors cause rejection
            require_digital: If True, reject scanned PDFs
        """
        super().__init__("PDFQualityValidator", strict_mode)
        self.require_digital = require_digital

    def validate(self, pdf_path: str, context: Optional[Dict[str, Any]] = None) -> QualityReport:
        """
        Validate PDF quality

        Args:
            pdf_path: Path to PDF file
            context: Optional context (document_id, etc.)

        Returns:
            QualityReport
        """
        pdf_path = Path(pdf_path)
        context = context or {}
        document_id = context.get("document_id", str(pdf_path.name))

        # Create initial report
        report = self._create_report("pdf", document_id, base_score=100.0)

        # Check file exists
        if not pdf_path.exists():
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "PDF_NOT_FOUND",
                f"PDF file not found: {pdf_path}"
            )
            report.quality_score = 0
            return report

        # Get file stats
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        report.metrics["file_size_mb"] = round(file_size_mb, 2)

        # Validate file size
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "PDF_TOO_LARGE",
                f"PDF size {file_size_mb:.1f}MB exceeds maximum {self.MAX_FILE_SIZE_MB}MB",
                file_size_mb=file_size_mb
            )
            self._adjust_score(report, 100, "File too large")
            return report

        elif file_size_mb > self.WARN_FILE_SIZE_MB:
            report.add_issue(
                ValidationSeverity.WARNING,
                "PDF_LARGE_FILE",
                f"Large PDF file ({file_size_mb:.1f}MB), processing may take time",
                file_size_mb=file_size_mb
            )
            self._adjust_score(report, 5, "Large file")

        # Open PDF
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            report.add_issue(
                ValidationSeverity.CRITICAL,
                "PDF_OPEN_FAILED",
                f"Failed to open PDF: {str(e)}",
                error=str(e)
            )
            report.quality_score = 0
            return report

        try:
            # Validate page count
            page_count = len(doc)
            report.metrics["page_count"] = page_count

            if page_count == 0:
                report.add_issue(
                    ValidationSeverity.CRITICAL,
                    "PDF_NO_PAGES",
                    "PDF has no pages"
                )
                report.quality_score = 0
                return report

            if page_count > self.MAX_PAGES:
                report.add_issue(
                    ValidationSeverity.CRITICAL,
                    "PDF_TOO_MANY_PAGES",
                    f"PDF has {page_count} pages, exceeds maximum {self.MAX_PAGES}",
                    page_count=page_count
                )
                self._adjust_score(report, 100, "Too many pages")
                return report

            if page_count > self.WARN_PAGES:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "PDF_MANY_PAGES",
                    f"Large PDF with {page_count} pages, processing may take time",
                    page_count=page_count
                )
                self._adjust_score(report, 5, "Many pages")

            # Check encryption
            if doc.is_encrypted:
                report.add_issue(
                    ValidationSeverity.CRITICAL,
                    "PDF_ENCRYPTED",
                    "PDF is encrypted/password-protected"
                )
                self._adjust_score(report, 100, "Encrypted")
                return report

            # Sample first 5 pages for quality assessment
            sample_size = min(5, page_count)
            total_chars = 0
            total_images = 0
            pages_with_text = 0
            pages_with_images = 0

            for page_num in range(sample_size):
                page = doc[page_num]

                # Extract text
                text = page.get_text("text")
                char_count = len(text.strip())
                total_chars += char_count

                if char_count > 10:
                    pages_with_text += 1

                # Count images
                image_list = page.get_images()
                if image_list:
                    total_images += len(image_list)
                    pages_with_images += 1

            # Calculate metrics
            avg_chars_per_page = total_chars / sample_size
            text_density_ratio = pages_with_text / sample_size
            image_density_ratio = pages_with_images / sample_size

            report.metrics["avg_chars_per_page"] = round(avg_chars_per_page, 1)
            report.metrics["text_density_ratio"] = round(text_density_ratio, 2)
            report.metrics["image_density_ratio"] = round(image_density_ratio, 2)
            report.metrics["total_images_sampled"] = total_images

            # Detect scanned PDF
            is_scanned = (
                avg_chars_per_page < self.MIN_TEXT_DENSITY or
                text_density_ratio < 0.5 or
                (image_density_ratio > 0.8 and avg_chars_per_page < 200)
            )

            report.metrics["is_scanned"] = is_scanned

            if is_scanned:
                if self.require_digital:
                    report.add_issue(
                        ValidationSeverity.CRITICAL,
                        "PDF_SCANNED",
                        f"PDF appears to be scanned (avg {avg_chars_per_page:.0f} chars/page, "
                        f"{text_density_ratio:.0%} pages with text). OCR not supported.",
                        avg_chars_per_page=avg_chars_per_page,
                        text_density_ratio=text_density_ratio
                    )
                    self._adjust_score(report, 100, "Scanned PDF")
                else:
                    report.add_issue(
                        ValidationSeverity.WARNING,
                        "PDF_POSSIBLY_SCANNED",
                        f"PDF may be scanned (low text density: {avg_chars_per_page:.0f} chars/page)",
                        avg_chars_per_page=avg_chars_per_page
                    )
                    self._adjust_score(report, 30, "Possibly scanned")

            # Check text extractability on first page
            if pages_with_text == 0:
                report.add_issue(
                    ValidationSeverity.CRITICAL,
                    "PDF_NO_TEXT",
                    "No extractable text found in sample pages"
                )
                self._adjust_score(report, 100, "No extractable text")

            elif text_density_ratio < 0.8:
                report.add_issue(
                    ValidationSeverity.WARNING,
                    "PDF_LOW_TEXT_DENSITY",
                    f"Only {text_density_ratio:.0%} of sample pages have significant text",
                    text_density_ratio=text_density_ratio
                )
                self._adjust_score(report, 15, "Low text density")

            # Assess complexity (high image ratio may indicate complex layout)
            if image_density_ratio > 0.6 and not is_scanned:
                report.add_issue(
                    ValidationSeverity.INFO,
                    "PDF_COMPLEX_LAYOUT",
                    f"PDF has many images ({image_density_ratio:.0%} of pages), may have complex layout",
                    image_density_ratio=image_density_ratio
                )
                self._adjust_score(report, 5, "Complex layout")

            # Final quality assessment
            report.quality_level = QualityLevel.from_score(report.quality_score)

            # Log result
            logger.info(
                f"PDF quality validated: {pdf_path.name} | "
                f"Score: {report.quality_score:.1f}% | "
                f"Pages: {page_count} | "
                f"Chars/page: {avg_chars_per_page:.0f} | "
                f"Scanned: {is_scanned}"
            )

        finally:
            doc.close()

        return report


def validate_pdf_quality(
    pdf_path: str,
    require_digital: bool = True,
    strict_mode: bool = True
) -> QualityReport:
    """
    Convenience function to validate PDF quality

    Args:
        pdf_path: Path to PDF
        require_digital: Reject scanned PDFs
        strict_mode: Errors cause rejection

    Returns:
        QualityReport
    """
    validator = PDFQualityValidator(
        strict_mode=strict_mode,
        require_digital=require_digital
    )
    return validator.validate(pdf_path)
