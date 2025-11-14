"""
PDF Extraction Validation - Simplified
=======================================

Direct analysis of PDF files for quality, reliability, and BI usefulness

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-14
"""

import json
from pathlib import Path
from pypdf import PdfReader
import re
from typing import Dict, List

def analyze_pdf_for_bi(pdf_path: Path) -> Dict:
    """Analyze PDF for BI analytics usefulness"""
    try:
        reader = PdfReader(str(pdf_path))

        # Extract text
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Financial keywords
        financial_keywords = {}
        for kw in ["revenue", "przycho", "sales", "sprzedaż", "assets", "aktywa",
                   "equity", "kapitał", "liabilities", "zobowiązania", "pasywa",
                   "profit", "zysk", "loss", "strata", "ebitda", "cash flow",
                   "operating income", "wynik operacyjny"]:
            if re.search(rf'\b{kw}', text, re.IGNORECASE):
                financial_keywords[kw] = True

        # Find years/periods
        years = sorted(list(set(re.findall(r'\b(20\d{2})\b', text))))

        # Find numbers (potential metrics)
        numbers = re.findall(r'\d+[,\s]\d+|\d+\.\d+|\d+', text)

        # Company identifiers
        has_company_info = bool(re.search(r'(NIP|REGON|KRS|Sp\.|S\.A\.|Company)', text))

        # Calculate scores
        pages = len(reader.pages)
        text_length = len(text)
        financial_count = len(financial_keywords)
        years_count = len(years)
        numbers_count = len(numbers)

        # BI usefulness score
        bi_score = 0

        # Has multiple years?
        if years_count >= 3:
            bi_score += 30
        elif years_count >= 2:
            bi_score += 20
        elif years_count >= 1:
            bi_score += 10

        # Has financial metrics?
        if financial_count >= 5:
            bi_score += 30
        elif financial_count >= 3:
            bi_score += 20
        elif financial_count >= 1:
            bi_score += 10

        # Has numerical data?
        if numbers_count >= 50:
            bi_score += 20
        elif numbers_count >= 20:
            bi_score += 10

        # Has company info?
        if has_company_info:
            bi_score += 10

        # Has reasonable text?
        if text_length >= 1000:
            bi_score += 10

        ready_for_bi = bi_score >= 60

        return {
            "filename": pdf_path.name,
            "pages": pages,
            "text_length": text_length,
            "financial_metrics": list(financial_keywords.keys()),
            "financial_count": financial_count,
            "years": years,
            "years_count": years_count,
            "numbers_count": numbers_count,
            "has_company_info": has_company_info,
            "bi_usefulness_score": bi_score,
            "ready_for_bi": ready_for_bi,
            "grade": "A" if bi_score >= 80 else "B" if bi_score >= 60 else "C" if bi_score >= 40 else "D",
            "issues": []
        }

    except Exception as e:
        return {
            "filename": pdf_path.name,
            "error": str(e),
            "bi_usefulness_score": 0,
            "ready_for_bi": False,
            "grade": "F"
        }


def main():
    print("=" * 80)
    print("PDF EXTRACTION VALIDATION")
    print("Quality • Reliability • Integrity • BI Analytics Usefulness")
    print("=" * 80)

    uploads_dir = Path("/Users/artur/agents20/projektagenci01/backend/data/uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))

    print(f"\nFound {len(pdf_files)} PDF files\n")
    print("-" * 80)

    reports = []

    for i, pdf_path in enumerate(pdf_files[:10], 1):  # Analyze first 10
        print(f"\n[{i}/10] {pdf_path.name}")
        report = analyze_pdf_for_bi(pdf_path)
        reports.append(report)

        if "error" in report:
            print(f"  ❌ Error: {report['error']}")
            continue

        print(f"  Pages: {report['pages']}")
        print(f"  Text Length: {report['text_length']:,} chars")
        print(f"  Financial Metrics Found: {report['financial_count']}")
        if report['financial_metrics']:
            print(f"    → {', '.join(report['financial_metrics'][:5])}")
        print(f"  Time Periods: {report['years_count']}")
        if report['years']:
            print(f"    → {', '.join(report['years'][:10])}")
        print(f"  Numerical Values: {report['numbers_count']}")
        print(f"  Company Info: {'✅' if report['has_company_info'] else '❌'}")
        print(f"  BI Usefulness Score: {report['bi_usefulness_score']}/100 (Grade: {report['grade']})")
        print(f"  Ready for BI Analytics: {'✅ YES' if report['ready_for_bi'] else '❌ NO'}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    valid_reports = [r for r in reports if "error" not in r]

    if valid_reports:
        avg_score = sum(r['bi_usefulness_score'] for r in valid_reports) / len(valid_reports)
        bi_ready = sum(1 for r in valid_reports if r['ready_for_bi'])

        avg_pages = sum(r['pages'] for r in valid_reports) / len(valid_reports)
        avg_metrics = sum(r['financial_count'] for r in valid_reports) / len(valid_reports)
        avg_years = sum(r['years_count'] for r in valid_reports) / len(valid_reports)

        print(f"\nDocuments Analyzed: {len(valid_reports)}")
        print(f"\nAverage Metrics:")
        print(f"  Pages per Document: {avg_pages:.1f}")
        print(f"  Financial Metrics per Document: {avg_metrics:.1f}")
        print(f"  Time Periods per Document: {avg_years:.1f}")
        print(f"\nBI Analytics Readiness:")
        print(f"  Average Score: {avg_score:.1f}/100")
        print(f"  Ready for BI: {bi_ready}/{len(valid_reports)} ({bi_ready/len(valid_reports)*100:.0f}%)")

        # Grade distribution
        grades = {}
        for r in valid_reports:
            grade = r['grade']
            grades[grade] = grades.get(grade, 0) + 1

        print(f"\nQuality Distribution:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grades.get(grade, 0)
            if count > 0:
                pct = count / len(valid_reports) * 100
                print(f"  Grade {grade}: {count} ({pct:.0f}%)")

        # Assessment
        print(f"\nOVERALL ASSESSMENT:")
        if avg_score >= 70:
            print(f"  ✅ EXCELLENT - System extracts high-quality, BI-ready data")
        elif avg_score >= 50:
            print(f"  ⚠️  GOOD - System extracts useful data, some improvements needed")
        elif avg_score >= 30:
            print(f"  ⚠️  FAIR - System extracts basic data, significant improvements needed")
        else:
            print(f"  ❌ POOR - Extraction needs major improvements for BI use")

        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if avg_metrics < 3:
            print(f"  • Improve financial metric extraction (avg: {avg_metrics:.1f}, target: 5+)")
        if avg_years < 2:
            print(f"  • Improve time period detection (avg: {avg_years:.1f}, target: 3+)")
        if bi_ready / len(valid_reports) < 0.7:
            print(f"  • Focus on table extraction and structured data")

        # Save report
        output_file = "/Users/artur/agents20/projektagenci01/backend/tests/pdf_validation_report.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "documents_analyzed": len(valid_reports),
                    "average_bi_score": round(avg_score, 1),
                    "bi_ready_count": bi_ready,
                    "bi_ready_percentage": round(bi_ready/len(valid_reports)*100, 1),
                    "avg_financial_metrics": round(avg_metrics, 1),
                    "avg_time_periods": round(avg_years, 1)
                },
                "documents": valid_reports
            }, f, indent=2)

        print(f"\n📄 Detailed report saved to: {output_file}")

    else:
        print(f"❌ No valid reports generated")


if __name__ == "__main__":
    main()
