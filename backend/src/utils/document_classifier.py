"""
Document Classifier for Investigation Intelligence Platform

Routes documents to appropriate processing pipeline:
- Financial documents → Docling (structure-aware extraction)
- General documents → PyMuPDF (fast text extraction)

Classification based on:
1. Filename patterns (e.g., "financial_report_2024.pdf")
2. Content analysis (first page keyword detection)
3. Document metadata (if available)

Author: Claude Code (Sonnet 4.5)
Date: 2025-11-12
"""

import re
from typing import Literal, Optional
from enum import Enum
import logging

# Type alias for document types
DocumentType = Literal["financial", "general"]

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Classifies documents to route them to appropriate processing pipeline.

    Financial documents get structure-aware processing (Docling) to preserve
    table headers and temporal context critical for investigations.

    General documents get fast text extraction (PyMuPDF) for efficiency.
    """

    # Filename patterns indicating financial documents (case-insensitive)
    FINANCIAL_FILENAME_PATTERNS = [
        r'.*financial[_\s-]*(report|statement).*',
        r'.*sprawozdanie[_\s-]*finansowe.*',  # Polish
        r'.*rachunek[_\s-]*(zysk|strat).*',   # Income statement (Polish)
        r'.*bilans.*',                         # Balance sheet (Polish)
        r'.*annual[_\s-]*report.*',
        r'.*quarterly[_\s-]*report.*',
        r'.*\d{4}[_\s-]*(q[1-4]|report).*',   # Year-based reports
        r'.*10-k.*',                           # SEC filings
        r'.*10-q.*',
        r'.*earnings.*',
        r'.*grupa[_\s-]*azoty.*\d{4}.*',      # Grupa Azoty reports
        r'.*sprawozdanie.*\d{4}.*',           # General Polish reports with year
    ]

    # Keywords indicating financial content (case-insensitive)
    # Polish and English mixed
    FINANCIAL_KEYWORDS = [
        # Polish financial terms
        "sprawozdanie finansowe",
        "rachunek zysków i strat",
        "bilans",
        "przepływy pieniężne",
        "zobowiązania",
        "aktywa",
        "pasywa",
        "przychody ze sprzedaży",
        "wynik finansowy",
        "segment operacyjny",

        # English financial terms
        "financial statement",
        "income statement",
        "balance sheet",
        "cash flow",
        "assets",
        "liabilities",
        "shareholders' equity",
        "revenue",
        "net income",
        "operating segment",

        # Common headers in financial tables
        "31.12.20",  # Date format in Grupa Azoty reports
        "nawozy - agro",  # Segment names
        "tworzywa",
        "energetyka",

        # Regulatory indicators
        "ifrs",
        "gaap",
        "audited",
        "unaudited",
    ]

    # Minimum keyword threshold for content-based classification
    FINANCIAL_KEYWORD_THRESHOLD = 3

    def __init__(self,
                 keyword_threshold: int = 3,
                 enable_content_analysis: bool = True):
        """
        Initialize the document classifier.

        Args:
            keyword_threshold: Minimum number of financial keywords to classify as financial
            enable_content_analysis: If False, only use filename patterns
        """
        self.keyword_threshold = keyword_threshold
        self.enable_content_analysis = enable_content_analysis

        logger.info(
            f"DocumentClassifier initialized: "
            f"keyword_threshold={keyword_threshold}, "
            f"content_analysis={'enabled' if enable_content_analysis else 'disabled'}"
        )

    def classify(self,
                 filename: str,
                 first_page_text: Optional[str] = None) -> DocumentType:
        """
        Classify a document as 'financial' or 'general'.

        Args:
            filename: Original filename of the document
            first_page_text: Optional text from first page for content analysis

        Returns:
            'financial' or 'general'

        Example:
            >>> classifier = DocumentClassifier()
            >>> classifier.classify("grupa_azoty_2024.pdf")
            'financial'
            >>> classifier.classify("meeting_notes.pdf")
            'general'
        """
        filename_lower = filename.lower()

        # Step 1: Check filename patterns (fastest, most reliable)
        for pattern in self.FINANCIAL_FILENAME_PATTERNS:
            if re.match(pattern, filename_lower):
                logger.info(f"Document classified as FINANCIAL (filename pattern): {filename}")
                return "financial"

        # Step 2: Content analysis (if enabled and first page available)
        if self.enable_content_analysis and first_page_text:
            keyword_count = self._count_financial_keywords(first_page_text)

            if keyword_count >= self.keyword_threshold:
                logger.info(
                    f"Document classified as FINANCIAL (content analysis): {filename} "
                    f"({keyword_count} keywords found)"
                )
                return "financial"
            else:
                logger.debug(
                    f"Document content check: {filename} "
                    f"({keyword_count}/{self.keyword_threshold} keywords)"
                )

        # Default: general document
        logger.info(f"Document classified as GENERAL: {filename}")
        return "general"

    def _count_financial_keywords(self, text: str) -> int:
        """
        Count how many financial keywords appear in the text.

        Args:
            text: Text to analyze (typically first page)

        Returns:
            Number of distinct financial keywords found
        """
        text_lower = text.lower()

        # Count unique keywords found
        keywords_found = set()
        for keyword in self.FINANCIAL_KEYWORDS:
            if keyword in text_lower:
                keywords_found.add(keyword)

        return len(keywords_found)

    def explain_classification(self,
                               filename: str,
                               first_page_text: Optional[str] = None) -> dict:
        """
        Classify a document and provide explanation of the decision.

        Useful for debugging and transparency.

        Args:
            filename: Original filename
            first_page_text: Optional first page text

        Returns:
            Dict with classification and reasoning

        Example:
            >>> result = classifier.explain_classification("annual_report_2024.pdf")
            >>> print(result)
            {
                'classification': 'financial',
                'reason': 'filename_pattern',
                'matched_pattern': '.*annual[_\\s-]*report.*',
                'keyword_count': 0
            }
        """
        filename_lower = filename.lower()
        result = {
            'classification': 'general',
            'reason': 'default',
            'matched_pattern': None,
            'keyword_count': 0,
            'keywords_found': []
        }

        # Check filename patterns
        for pattern in self.FINANCIAL_FILENAME_PATTERNS:
            if re.match(pattern, filename_lower):
                result['classification'] = 'financial'
                result['reason'] = 'filename_pattern'
                result['matched_pattern'] = pattern
                return result

        # Check content
        if self.enable_content_analysis and first_page_text:
            text_lower = first_page_text.lower()
            keywords_found = []

            for keyword in self.FINANCIAL_KEYWORDS:
                if keyword in text_lower:
                    keywords_found.append(keyword)

            result['keyword_count'] = len(keywords_found)
            result['keywords_found'] = keywords_found[:10]  # Limit to first 10 for brevity

            if len(keywords_found) >= self.keyword_threshold:
                result['classification'] = 'financial'
                result['reason'] = 'content_keywords'

        return result

    def get_statistics(self) -> dict:
        """
        Get classifier configuration statistics.

        Returns:
            Dict with configuration details
        """
        return {
            'filename_patterns': len(self.FINANCIAL_FILENAME_PATTERNS),
            'keywords': len(self.FINANCIAL_KEYWORDS),
            'keyword_threshold': self.keyword_threshold,
            'content_analysis_enabled': self.enable_content_analysis
        }


# Convenience function for quick classification
def classify_document(filename: str, first_page_text: Optional[str] = None) -> DocumentType:
    """
    Quick classification function without instantiating classifier.

    Args:
        filename: Document filename
        first_page_text: Optional first page text

    Returns:
        'financial' or 'general'

    Example:
        >>> from src.utils import classify_document
        >>> doc_type = classify_document("quarterly_report_q3_2024.pdf")
    """
    classifier = DocumentClassifier()
    return classifier.classify(filename, first_page_text)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Create classifier
    classifier = DocumentClassifier()

    # Test cases
    test_files = [
        ("grupa_azoty_sprawozdanie_2024.pdf", None),
        ("annual_financial_report_2023.pdf", None),
        ("meeting_minutes_nov_2024.pdf", None),
        ("10-k_filing_2024.pdf", None),
        ("random_document.pdf", "This document contains sprawozdanie finansowe and bilans and rachunek zysków i strat"),
        ("another_doc.pdf", "This is just a general document with no financial terms"),
    ]

    print("=" * 80)
    print("DOCUMENT CLASSIFIER TEST")
    print("=" * 80)

    for filename, first_page in test_files:
        result = classifier.explain_classification(filename, first_page)
        print(f"\nFilename: {filename}")
        print(f"Classification: {result['classification'].upper()}")
        print(f"Reason: {result['reason']}")
        if result['matched_pattern']:
            print(f"Pattern: {result['matched_pattern']}")
        if result['keyword_count'] > 0:
            print(f"Keywords: {result['keyword_count']} found")
            print(f"Examples: {', '.join(result['keywords_found'][:3])}")

    print("\n" + "=" * 80)
    print("CLASSIFIER STATISTICS")
    print("=" * 80)
    stats = classifier.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
