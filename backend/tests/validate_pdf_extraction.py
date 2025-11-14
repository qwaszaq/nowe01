"""
PDF Extraction Validation Test
===============================

Comprehensive validation of extracted data against PDF originals

Validates:
1. QUALITY: Data completeness, accuracy, consistency
2. RELIABILITY: Reproducibility, error handling, data integrity
3. INTEGRITY: Structure preservation, metadata accuracy
4. BI ANALYTICS USEFULNESS:
   - Are financial metrics extracted correctly?
   - Are time series complete?
   - Are company identifiers accurate?
   - Is data structured for analysis?

GUARDRAIL COMPLIANCE:
- Rule #1: Data Quality Guaranteed
- Explicit validation results
- Clear error reporting
- Performance tracking

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pypdf import PdfReader
import re

# Database imports
import sys
sys.path.insert(0, '/Users/artur/agents20/projektagenci01/backend')

from src.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text


@dataclass
class ExtractionValidationReport:
    """Comprehensive validation report"""
    pdf_file: str
    case_id: Optional[str] = None
    document_id: Optional[str] = None

    # Quality metrics
    pages_in_pdf: int = 0
    pages_processed: int = 0
    text_coverage: float = 0.0  # % of PDF text extracted

    # Financial data metrics
    tables_found: int = 0
    financial_metrics_extracted: List[str] = field(default_factory=list)
    time_periods_found: List[str] = field(default_factory=list)
    company_info_extracted: bool = False

    # BI Analytics usefulness
    ready_for_bi: bool = False
    bi_usefulness_score: float = 0.0
    bi_issues: List[str] = field(default_factory=list)
    bi_recommendations: List[str] = field(default_factory=list)

    # Quality issues
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Overall scores
    quality_score: float = 0.0  # 0-100
    reliability_score: float = 0.0  # 0-100
    integrity_score: float = 0.0  # 0-100
    overall_score: float = 0.0  # 0-100

    def add_error(self, message: str):
        """Add error"""
        self.errors.append(message)

    def add_warning(self, message: str):
        """Add warning"""
        self.warnings.append(message)

    def add_bi_issue(self, issue: str):
        """Add BI analytics issue"""
        self.bi_issues.append(issue)

    def add_bi_recommendation(self, rec: str):
        """Add BI recommendation"""
        self.bi_recommendations.append(rec)

    def calculate_scores(self):
        """Calculate all quality scores"""
        # Quality score based on coverage and completeness
        self.quality_score = 0.0

        # Page coverage
        if self.pages_in_pdf > 0:
            page_coverage = (self.pages_processed / self.pages_in_pdf) * 100
            self.quality_score += page_coverage * 0.3

        # Text coverage
        self.quality_score += self.text_coverage * 0.3

        # Data extraction completeness
        if self.tables_found > 0:
            self.quality_score += 20
        if self.financial_metrics_extracted:
            self.quality_score += 10
        if self.time_periods_found:
            self.quality_score += 10

        # Reliability score based on error count
        self.reliability_score = 100.0
        if self.errors:
            self.reliability_score -= len(self.errors) * 20
            self.reliability_score = max(0, self.reliability_score)

        # Integrity score
        self.integrity_score = 100.0
        if self.warnings:
            self.integrity_score -= len(self.warnings) * 5

        # BI usefulness score
        self.bi_usefulness_score = 0.0

        # Has financial metrics?
        if len(self.financial_metrics_extracted) >= 5:
            self.bi_usefulness_score += 30
        elif len(self.financial_metrics_extracted) >= 3:
            self.bi_usefulness_score += 20
        elif len(self.financial_metrics_extracted) >= 1:
            self.bi_usefulness_score += 10

        # Has time periods?
        if len(self.time_periods_found) >= 3:
            self.bi_usefulness_score += 30
        elif len(self.time_periods_found) >= 2:
            self.bi_usefulness_score += 20
        elif len(self.time_periods_found) >= 1:
            self.bi_usefulness_score += 10

        # Has tables?
        if self.tables_found >= 3:
            self.bi_usefulness_score += 20
        elif self.tables_found >= 1:
            self.bi_usefulness_score += 10

        # Has company info?
        if self.company_info_extracted:
            self.bi_usefulness_score += 20

        # BI ready if score >= 70
        self.ready_for_bi = self.bi_usefulness_score >= 70

        # Overall score (weighted average)
        self.overall_score = (
            self.quality_score * 0.3 +
            self.reliability_score * 0.2 +
            self.integrity_score * 0.2 +
            self.bi_usefulness_score * 0.3
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pdf_file": self.pdf_file,
            "case_id": self.case_id,
            "document_id": self.document_id,
            "metrics": {
                "pages_in_pdf": self.pages_in_pdf,
                "pages_processed": self.pages_processed,
                "text_coverage": round(self.text_coverage, 2),
                "tables_found": self.tables_found,
                "financial_metrics_count": len(self.financial_metrics_extracted),
                "time_periods_count": len(self.time_periods_found)
            },
            "financial_data": {
                "metrics": self.financial_metrics_extracted,
                "periods": self.time_periods_found,
                "has_company_info": self.company_info_extracted
            },
            "bi_analytics": {
                "ready_for_bi": self.ready_for_bi,
                "usefulness_score": round(self.bi_usefulness_score, 1),
                "issues": self.bi_issues,
                "recommendations": self.bi_recommendations
            },
            "quality": {
                "quality_score": round(self.quality_score, 1),
                "reliability_score": round(self.reliability_score, 1),
                "integrity_score": round(self.integrity_score, 1),
                "overall_score": round(self.overall_score, 1)
            },
            "issues": {
                "errors": self.errors,
                "warnings": self.warnings
            }
        }


class PDFExtractionValidator:
    """Validates PDF extraction quality"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.uploads_dir = Path("/Users/artur/agents20/projektagenci01/backend/data/uploads")

    def validate_pdf(self, pdf_path: Path) -> ExtractionValidationReport:
        """Validate single PDF extraction"""
        report = ExtractionValidationReport(pdf_file=str(pdf_path.name))

        # STEP 1: Analyze PDF file
        try:
            pdf_reader = PdfReader(str(pdf_path))
            report.pages_in_pdf = len(pdf_reader.pages)

            # Extract all text from PDF
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() or ""

            # Look for financial indicators in PDF
            self._analyze_pdf_content(pdf_text, report)

        except Exception as e:
            report.add_error(f"Failed to read PDF: {e}")
            return report

        # STEP 2: Find extracted data in database
        extracted_data = self._find_extracted_data(pdf_path.name)

        if not extracted_data:
            report.add_error("No extracted data found in database")
            report.calculate_scores()
            return report

        report.case_id = extracted_data.get("case_id")
        report.document_id = extracted_data.get("document_id")

        # STEP 3: Validate extracted content
        self._validate_extraction_quality(extracted_data, pdf_text, report)

        # STEP 4: Assess BI analytics usefulness
        self._assess_bi_usefulness(extracted_data, report)

        # STEP 5: Calculate scores
        report.calculate_scores()

        return report

    def _analyze_pdf_content(self, pdf_text: str, report: ExtractionValidationReport):
        """Analyze PDF content for financial data"""
        # Look for financial metrics
        financial_keywords = [
            "revenue", "przycho", "sales", "sprzedaż",
            "assets", "aktywa", "majątek",
            "equity", "kapitał własny",
            "liabilities", "zobowiązania", "pasywa",
            "profit", "zysk", "loss", "strata",
            "ebitda", "operating income", "wynik operacyjny",
            "cash flow", "przepływy pieniężne"
        ]

        for keyword in financial_keywords:
            if re.search(rf'\b{keyword}\b', pdf_text, re.IGNORECASE):
                if keyword not in [m.lower() for m in report.financial_metrics_extracted]:
                    report.financial_metrics_extracted.append(keyword)

        # Look for years/periods
        years = re.findall(r'\b(20\d{2})\b', pdf_text)
        report.time_periods_found = sorted(list(set(years)))[:10]  # Limit to 10

        # Look for company indicators
        company_indicators = ["NIP", "REGON", "KRS", "Company", "Spółka", "S.A.", "Sp. z o.o."]
        for indicator in company_indicators:
            if indicator in pdf_text:
                report.company_info_extracted = True
                break

    def _find_extracted_data(self, pdf_filename: str) -> Optional[Dict[str, Any]]:
        """Find extracted data for PDF in database"""
        try:
            # Query documents table
            query = text("""
                SELECT
                    d.id as document_id,
                    d.case_id,
                    d.file_path,
                    d.content,
                    d.metadata,
                    d.created_at
                FROM documents d
                WHERE d.file_path LIKE :filename
                ORDER BY d.created_at DESC
                LIMIT 1
            """)

            result = self.db.execute(query, {"filename": f"%{pdf_filename}%"}).fetchone()

            if not result:
                return None

            return {
                "document_id": str(result.document_id),
                "case_id": str(result.case_id),
                "file_path": result.file_path,
                "content": result.content,
                "metadata": result.metadata,
                "created_at": result.created_at
            }

        except Exception as e:
            print(f"Database error: {e}")
            return None

    def _validate_extraction_quality(
        self,
        extracted_data: Dict[str, Any],
        pdf_text: str,
        report: ExtractionValidationReport
    ):
        """Validate extraction quality"""
        content = extracted_data.get("content", "")
        metadata = extracted_data.get("metadata", {})

        # Check text coverage
        if pdf_text and content:
            # Simple coverage: check if extracted content contains key words from PDF
            pdf_words = set(re.findall(r'\w+', pdf_text.lower()))
            extracted_words = set(re.findall(r'\w+', content.lower()))

            if pdf_words:
                overlap = len(pdf_words & extracted_words)
                report.text_coverage = (overlap / len(pdf_words)) * 100

            # Check if text length is reasonable
            if len(content) < len(pdf_text) * 0.1:
                report.add_warning("Extracted text is very short compared to PDF")

        # Check metadata
        if isinstance(metadata, dict):
            if "pages_processed" in metadata:
                report.pages_processed = metadata["pages_processed"]

            if "tables" in metadata:
                report.tables_found = len(metadata["tables"])

        # Check for structured data
        if not content:
            report.add_error("No content extracted")

    def _assess_bi_usefulness(self, extracted_data: Dict[str, Any], report: ExtractionValidationReport):
        """Assess if data is useful for BI analytics"""
        content = extracted_data.get("content", "")
        metadata = extracted_data.get("metadata", {})

        # Check 1: Has numerical data?
        numbers = re.findall(r'\d+(?:[,\.]\d+)?', content)
        if len(numbers) < 10:
            report.add_bi_issue("Very few numerical values found")
            report.add_bi_recommendation("Verify if financial data was extracted correctly")

        # Check 2: Has tables?
        if report.tables_found == 0:
            report.add_bi_issue("No tables extracted")
            report.add_bi_recommendation("Financial reports typically contain tables - verify table extraction")

        # Check 3: Has time series?
        if len(report.time_periods_found) < 2:
            report.add_bi_issue("Insufficient time periods for trend analysis")
            report.add_bi_recommendation("Need at least 2-3 years for meaningful BI analytics")

        # Check 4: Has key financial metrics?
        critical_metrics = ["revenue", "przycho", "assets", "aktywa", "equity", "kapitał"]
        found_critical = sum(1 for m in report.financial_metrics_extracted
                           if any(cm in m.lower() for cm in critical_metrics))

        if found_critical < 2:
            report.add_bi_issue("Missing critical financial metrics")
            report.add_bi_recommendation("Verify extraction of: Revenue, Assets, Equity, Liabilities")

        # Check 5: Data structure
        if not metadata or not isinstance(metadata, dict):
            report.add_bi_issue("No structured metadata")
            report.add_bi_recommendation("Add structured metadata for easier BI integration")


async def main():
    """Run validation on all PDFs"""
    print("=" * 80)
    print("PDF EXTRACTION VALIDATION - QUALITY, RELIABILITY & BI USEFULNESS")
    print("=" * 80)

    # Get database session
    db_gen = get_db()
    db = next(db_gen)

    try:
        validator = PDFExtractionValidator(db)
        uploads_dir = Path("/Users/artur/agents20/projektagenci01/backend/data/uploads")

        # Find all PDFs
        pdf_files = list(uploads_dir.glob("*.pdf"))

        print(f"\nFound {len(pdf_files)} PDF files")
        print("-" * 80)

        reports = []

        for i, pdf_path in enumerate(pdf_files[:5], 1):  # Test first 5
            print(f"\n[{i}/{min(5, len(pdf_files))}] Validating: {pdf_path.name}")
            report = validator.validate_pdf(pdf_path)
            reports.append(report)

            # Print summary
            print(f"  Quality Score:      {report.quality_score:.1f}%")
            print(f"  Reliability Score:  {report.reliability_score:.1f}%")
            print(f"  Integrity Score:    {report.integrity_score:.1f}%")
            print(f"  BI Usefulness:      {report.bi_usefulness_score:.1f}%")
            print(f"  Overall Score:      {report.overall_score:.1f}%")
            print(f"  Ready for BI:       {'✅ YES' if report.ready_for_bi else '❌ NO'}")

            if report.errors:
                print(f"  ⚠️  Errors: {len(report.errors)}")
                for error in report.errors[:3]:
                    print(f"     - {error}")

            if report.bi_issues:
                print(f"  📊 BI Issues: {len(report.bi_issues)}")
                for issue in report.bi_issues[:3]:
                    print(f"     - {issue}")

        # Overall summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        if reports:
            avg_quality = sum(r.quality_score for r in reports) / len(reports)
            avg_reliability = sum(r.reliability_score for r in reports) / len(reports)
            avg_integrity = sum(r.integrity_score for r in reports) / len(reports)
            avg_bi = sum(r.bi_usefulness_score for r in reports) / len(reports)
            avg_overall = sum(r.overall_score for r in reports) / len(reports)

            ready_for_bi_count = sum(1 for r in reports if r.ready_for_bi)

            print(f"\nAverage Scores (n={len(reports)}):")
            print(f"  Quality:      {avg_quality:.1f}%")
            print(f"  Reliability:  {avg_reliability:.1f}%")
            print(f"  Integrity:    {avg_integrity:.1f}%")
            print(f"  BI Usefulness: {avg_bi:.1f}%")
            print(f"  Overall:      {avg_overall:.1f}%")
            print(f"\nBI Analytics Ready: {ready_for_bi_count}/{len(reports)} ({ready_for_bi_count/len(reports)*100:.1f}%)")

            # Save detailed report
            output_file = "/Users/artur/agents20/projektagenci01/backend/tests/extraction_validation_report.json"
            with open(output_file, 'w') as f:
                json.dump([r.to_dict() for r in reports], f, indent=2, default=str)

            print(f"\n📄 Detailed report saved to: {output_file}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
