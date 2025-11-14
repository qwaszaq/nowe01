"""
PDF Extraction Validation via API
==================================

Validates extracted data quality, reliability, integrity, and BI usefulness

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

import requests
import json
from pathlib import Path
from pypdf import PdfReader
import re
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ValidationReport:
    """Validation report for a single document"""
    pdf_filename: str
    case_id: str = None
    document_id: str = None

    # PDF analysis
    pages_in_pdf: int = 0
    pdf_text_length: int = 0
    pdf_financial_keywords: List[str] = field(default_factory=list)
    pdf_years_found: List[str] = field(default_factory=list)

    # Extracted data
    extracted_content_length: int = 0
    extracted_tables: int = 0
    extracted_metrics: List[str] = field(default_factory=list)

    # Quality scores
    text_coverage: float = 0.0  # % of PDF text extracted
    data_completeness: float = 0.0  # Financial data completeness
    bi_usefulness: float = 0.0  # BI analytics usefulness
    overall_quality: float = 0.0  # Overall score

    # Issues
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    bi_issues: List[str] = field(default_factory=list)

    # Verdict
    ready_for_bi: bool = False

    def calculate_scores(self):
        """Calculate all quality scores"""
        # Text coverage
        if self.pdf_text_length > 0:
            self.text_coverage = min(100, (self.extracted_content_length / self.pdf_text_length) * 100)

        # Data completeness (based on financial metrics found)
        expected_metrics = len(self.pdf_financial_keywords)
        found_metrics = len(self.extracted_metrics)

        if expected_metrics > 0:
            self.data_completeness = (found_metrics / expected_metrics) * 100
        elif found_metrics > 0:
            self.data_completeness = 70.0  # Has some data

        # BI usefulness
        bi_score = 0.0

        # Has tables?
        if self.extracted_tables >= 3:
            bi_score += 25
        elif self.extracted_tables >= 1:
            bi_score += 15

        # Has time periods?
        if len(self.pdf_years_found) >= 3:
            bi_score += 25
        elif len(self.pdf_years_found) >= 2:
            bi_score += 15
        elif len(self.pdf_years_found) >= 1:
            bi_score += 5

        # Has financial metrics?
        if found_metrics >= 5:
            bi_score += 30
        elif found_metrics >= 3:
            bi_score += 20
        elif found_metrics >= 1:
            bi_score += 10

        # Has reasonable text coverage?
        if self.text_coverage >= 70:
            bi_score += 20
        elif self.text_coverage >= 40:
            bi_score += 10

        self.bi_usefulness = bi_score
        self.ready_for_bi = bi_score >= 60

        # Overall quality (weighted average)
        self.overall_quality = (
            self.text_coverage * 0.3 +
            self.data_completeness * 0.3 +
            self.bi_usefulness * 0.4
        )


def analyze_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Analyze PDF file"""
    try:
        reader = PdfReader(str(pdf_path))

        # Extract text
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Find financial keywords
        keywords = []
        for kw in ["revenue", "przycho", "sales", "sprzedaż", "assets", "aktywa",
                   "equity", "kapitał", "liabilities", "zobowiązania", "profit", "zysk"]:
            if re.search(rf'\b{kw}', text, re.IGNORECASE):
                keywords.append(kw)

        # Find years
        years = sorted(list(set(re.findall(r'\b(20\d{2})\b', text))))

        return {
            "pages": len(reader.pages),
            "text_length": len(text),
            "financial_keywords": keywords,
            "years": years,
            "text": text
        }
    except Exception as e:
        return {"error": str(e)}


def validate_extraction():
    """Run validation"""
    print("=" * 80)
    print("PDF EXTRACTION VALIDATION - QUALITY & BI USEFULNESS")
    print("=" * 80)

    api_base = "http://localhost:8000/api/v1"
    uploads_dir = Path("/Users/artur/agents20/projektagenci01/backend/data/uploads")

    # Get cases
    print("\nFetching cases from API...")
    try:
        resp = requests.get(f"{api_base}/cases", timeout=5)
        cases = resp.json() if resp.status_code == 200 else []
        print(f"Found {len(cases)} cases")
    except Exception as e:
        print(f"❌ Failed to fetch cases: {e}")
        return

    if not cases:
        print("❌ No cases found in database")
        return

    # Process first 3 cases
    reports = []

    for i, case in enumerate(cases[:3], 1):
        case_id = case.get("id")
        print(f"\n[{i}/3] Case ID: {case_id}")
        print("-" * 80)

        # Get documents for case
        try:
            resp = requests.get(f"{api_base}/documents?case_id={case_id}", timeout=5)
            documents = resp.json() if resp.status_code == 200 else []
            print(f"  Documents: {len(documents)}")
        except Exception as e:
            print(f"  ❌ Failed to fetch documents: {e}")
            continue

        for doc in documents[:2]:  # First 2 docs per case
            doc_id = doc.get("id")
            file_path = doc.get("file_path", "")

            if not file_path or not file_path.endswith('.pdf'):
                continue

            pdf_filename = Path(file_path).name
            pdf_path = uploads_dir / pdf_filename

            if not pdf_path.exists():
                print(f"  ⚠️  PDF not found: {pdf_filename}")
                continue

            print(f"\n  📄 {pdf_filename}")

            # Create report
            report = ValidationReport(pdf_filename=pdf_filename, case_id=case_id, document_id=doc_id)

            # Analyze PDF
            pdf_data = analyze_pdf(pdf_path)
            if "error" in pdf_data:
                report.errors.append(f"PDF read error: {pdf_data['error']}")
            else:
                report.pages_in_pdf = pdf_data["pages"]
                report.pdf_text_length = pdf_data["text_length"]
                report.pdf_financial_keywords = pdf_data["financial_keywords"]
                report.pdf_years_found = pdf_data["years"]

            # Check extracted data
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            report.extracted_content_length = len(content) if content else 0

            if isinstance(metadata, dict):
                report.extracted_tables = len(metadata.get("tables", []))

                # Look for financial metrics in content
                for kw in report.pdf_financial_keywords:
                    if kw.lower() in content.lower():
                        report.extracted_metrics.append(kw)

            # Validate
            if not content:
                report.errors.append("No content extracted")

            if report.extracted_tables == 0:
                report.warnings.append("No tables extracted")
                report.bi_issues.append("Financial reports typically contain tables")

            if len(report.pdf_years_found) < 2:
                report.bi_issues.append("Need 2+ years for trend analysis")

            if len(report.extracted_metrics) < 3:
                report.bi_issues.append("Few financial metrics extracted")

            # Calculate scores
            report.calculate_scores()
            reports.append(report)

            # Print summary
            print(f"    Pages: {report.pages_in_pdf}")
            print(f"    Text Coverage: {report.text_coverage:.1f}%")
            print(f"    Financial Metrics: {len(report.extracted_metrics)}/{len(report.pdf_financial_keywords)}")
            print(f"    Time Periods: {len(report.pdf_years_found)}")
            print(f"    Tables Extracted: {report.extracted_tables}")
            print(f"    BI Usefulness: {report.bi_usefulness:.1f}%")
            print(f"    Overall Quality: {report.overall_quality:.1f}%")
            print(f"    Ready for BI: {'✅ YES' if report.ready_for_bi else '❌ NO'}")

            if report.errors:
                print(f"    ⚠️  Errors: {', '.join(report.errors[:2])}")
            if report.bi_issues:
                print(f"    📊 BI Issues: {', '.join(report.bi_issues[:2])}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if reports:
        avg_text_coverage = sum(r.text_coverage for r in reports) / len(reports)
        avg_data_completeness = sum(r.data_completeness for r in reports) / len(reports)
        avg_bi_usefulness = sum(r.bi_usefulness for r in reports) / len(reports)
        avg_overall = sum(r.overall_quality for r in reports) / len(reports)
        bi_ready_count = sum(1 for r in reports if r.ready_for_bi)

        print(f"\nDocuments Analyzed: {len(reports)}")
        print(f"\nAverage Scores:")
        print(f"  Text Coverage:      {avg_text_coverage:.1f}%")
        print(f"  Data Completeness:  {avg_data_completeness:.1f}%")
        print(f"  BI Usefulness:      {avg_bi_usefulness:.1f}%")
        print(f"  Overall Quality:    {avg_overall:.1f}%")
        print(f"\nBI Analytics Ready: {bi_ready_count}/{len(reports)} ({bi_ready_count/len(reports)*100:.0f}%)")

        # Categorize
        excellent = sum(1 for r in reports if r.overall_quality >= 80)
        good = sum(1 for r in reports if 60 <= r.overall_quality < 80)
        fair = sum(1 for r in reports if 40 <= r.overall_quality < 60)
        poor = sum(1 for r in reports if r.overall_quality < 40)

        print(f"\nQuality Distribution:")
        print(f"  Excellent (80-100%): {excellent}")
        print(f"  Good (60-80%):       {good}")
        print(f"  Fair (40-60%):       {fair}")
        print(f"  Poor (<40%):         {poor}")

        # Save report
        output = {
            "summary": {
                "documents_analyzed": len(reports),
                "avg_text_coverage": round(avg_text_coverage, 1),
                "avg_data_completeness": round(avg_data_completeness, 1),
                "avg_bi_usefulness": round(avg_bi_usefulness, 1),
                "avg_overall_quality": round(avg_overall, 1),
                "bi_ready_count": bi_ready_count,
                "bi_ready_percentage": round(bi_ready_count/len(reports)*100, 1)
            },
            "documents": [
                {
                    "pdf_filename": r.pdf_filename,
                    "case_id": r.case_id,
                    "scores": {
                        "text_coverage": round(r.text_coverage, 1),
                        "data_completeness": round(r.data_completeness, 1),
                        "bi_usefulness": round(r.bi_usefulness, 1),
                        "overall_quality": round(r.overall_quality, 1)
                    },
                    "metrics": {
                        "pages": r.pages_in_pdf,
                        "tables": r.extracted_tables,
                        "financial_metrics": r.extracted_metrics,
                        "time_periods": r.pdf_years_found
                    },
                    "ready_for_bi": r.ready_for_bi,
                    "issues": {
                        "errors": r.errors,
                        "warnings": r.warnings,
                        "bi_issues": r.bi_issues
                    }
                }
                for r in reports
            ]
        }

        output_file = "/Users/artur/agents20/projektagenci01/backend/tests/extraction_validation_report.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n📄 Detailed report saved to: {output_file}")


if __name__ == "__main__":
    validate_extraction()
