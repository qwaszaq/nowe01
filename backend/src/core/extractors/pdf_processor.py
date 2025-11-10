"""
PDF Processing Module
Extracts text, tables, and metadata from PDF documents
Uses PyMuPDF (fitz) for text + Camelot for tables
100% deterministic, no LLM calls
"""

import fitz  # PyMuPDF
import camelot
import hashlib
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Advanced PDF extraction using PyMuPDF + Camelot
    - PyMuPDF: Fast, accurate text extraction with layout awareness
    - Camelot: Precise table extraction
    No LLM calls - pure Python processing
    """

    def __init__(self):
        self.supported_extensions = ['.pdf']

        # Header/Footer detection patterns (common page number patterns)
        self.header_footer_patterns = [
            r'^Page\s+\d+\s+of\s+\d+$',
            r'^Strona\s+\d+\s+z\s+\d+$',  # Polish
            r'^\d+\s+of\s+\d+$',
            r'^\d+\s+/\s+\d+$',
            r'^[IVXivx]+$',  # Roman numerals alone
        ]

        # Company name patterns that appear in headers/footers
        self.repeated_text_patterns = [
            r'Grupa Azoty Spółka Akcyjna',
            r'©.*\d{4}',  # Copyright notices
        ]

    def extract_all(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract everything from PDF using PyMuPDF + Camelot

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with metadata, pages, tables, and extraction stats
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if pdf_path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {pdf_path.suffix}")

        logger.info(f"Starting PDF extraction with PyMuPDF+Camelot: {pdf_path.name}")

        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)

            extracted = {
                'metadata': self._extract_metadata(doc, pdf_path),
                'pages': [],
                'tables': [],
                'text_chunks': [],
                'extraction_stats': {}
            }

            total_chars = 0
            total_tables = 0
            total_pages = len(doc)

            # Process each page
            for page_num in range(total_pages):
                page = doc[page_num]
                actual_page_num = page_num + 1

                logger.debug(f"Processing page {actual_page_num}/{total_pages}")

                # Extract text using PyMuPDF
                text = self._extract_page_text(page)

                # Clean text (remove headers/footers)
                cleaned_text = self._clean_text(text, actual_page_num)

                if cleaned_text:
                    extracted['pages'].append({
                        'page_num': actual_page_num,
                        'text': cleaned_text,
                        'char_count': len(cleaned_text),
                        'word_count': len(cleaned_text.split())
                    })
                    total_chars += len(cleaned_text)

            doc.close()

            # Extract tables using Camelot (separate pass)
            logger.info("Extracting tables with Camelot...")
            try:
                tables = self._extract_tables_camelot(str(pdf_path))
                extracted['tables'] = tables
                total_tables = len(tables)
            except Exception as e:
                logger.warning(f"Camelot table extraction failed: {e}")
                extracted['tables'] = []

            # Statistics
            extracted['extraction_stats'] = {
                'total_pages': total_pages,
                'pages_with_text': len(extracted['pages']),
                'total_tables': total_tables,
                'total_characters': total_chars,
                'average_chars_per_page': total_chars / max(len(extracted['pages']), 1)
            }

            logger.info(
                f"Extraction complete: {total_pages} pages, "
                f"{total_chars} characters, {total_tables} tables"
            )

            return extracted

        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}", exc_info=True)
            raise

    def _extract_page_text(self, page: fitz.Page) -> str:
        """
        Extract text from page using PyMuPDF with layout preservation

        Args:
            page: PyMuPDF page object

        Returns:
            Extracted text with proper reading order
        """
        # Method 1: Get text with layout ("text" mode)
        # This preserves reading order better than pdfplumber
        text = page.get_text("text")

        # Alternative: Use blocks for more semantic extraction
        # blocks = page.get_text("blocks")
        # text = "\n\n".join([block[4] for block in blocks if block[6] == 0])  # block[6]==0 means text block

        return text.strip()

    def _clean_text(self, text: str, page_num: int) -> str:
        """
        Clean extracted text by removing headers, footers, and artifacts

        Args:
            text: Raw extracted text
            page_num: Page number

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip header/footer patterns
            if self._is_header_footer(line):
                logger.debug(f"Filtered header/footer on page {page_num}: {line[:50]}")
                continue

            # Skip very short lines that are likely artifacts (< 3 chars)
            if len(line) < 3:
                continue

            # Skip lines that are mostly dots/spaces (table of contents formatting)
            # e.g., "Title ..................................... 42"
            non_dot_chars = len([c for c in line if c not in '. \t'])
            if len(line) > 20 and non_dot_chars < len(line) * 0.3:  # < 30% actual content
                logger.debug(f"Filtered TOC line on page {page_num}: {line[:50]}")
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _is_header_footer(self, line: str) -> bool:
        """
        Detect if line is likely a header or footer

        Args:
            line: Text line to check

        Returns:
            True if likely header/footer
        """
        line = line.strip()

        # Check against patterns
        for pattern in self.header_footer_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        # Check for repeated company names, etc
        for pattern in self.repeated_text_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True

        # Check if line is ONLY page number pattern
        # e.g., "87", "Page 87", etc. when line is very short
        if len(line) <= 20:
            # Simple page number
            if re.match(r'^[Pp]age\s*\d+', line):
                return True
            # Just a number
            if re.match(r'^\d+$', line) and int(line) < 10000:
                return True

        return False

    def _extract_tables_camelot(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables using Camelot

        Args:
            pdf_path: Path to PDF

        Returns:
            List of tables with metadata
        """
        tables = []

        try:
            # Try lattice mode first (for bordered tables)
            tables_lattice = camelot.read_pdf(
                pdf_path,
                flavor='lattice',
                pages='all',
                suppress_stdout=True
            )

            for idx, table in enumerate(tables_lattice):
                if table.df is not None and not table.df.empty:
                    tables.append({
                        'page_num': table.page,
                        'table_id': f"p{table.page}_t{idx}",
                        'data': table.df.values.tolist(),
                        'rows': len(table.df),
                        'cols': len(table.df.columns),
                        'accuracy': table.accuracy,
                        'extraction_method': 'lattice',
                        'has_header': True  # Assume first row is header
                    })

            # Try stream mode (for borderless tables) if lattice found few tables
            if len(tables_lattice) < 5:
                try:
                    tables_stream = camelot.read_pdf(
                        pdf_path,
                        flavor='stream',
                        pages='all',
                        suppress_stdout=True
                    )

                    for idx, table in enumerate(tables_stream):
                        if table.df is not None and not table.df.empty:
                            # Skip if already extracted by lattice
                            if not any(t['page_num'] == table.page for t in tables):
                                tables.append({
                                    'page_num': table.page,
                                    'table_id': f"p{table.page}_t{idx}_stream",
                                    'data': table.df.values.tolist(),
                                    'rows': len(table.df),
                                    'cols': len(table.df.columns),
                                    'accuracy': table.accuracy,
                                    'extraction_method': 'stream',
                                    'has_header': True
                                })
                except Exception as e:
                    logger.debug(f"Stream mode table extraction failed: {e}")

            logger.info(f"Camelot extracted {len(tables)} tables")

        except Exception as e:
            logger.error(f"Camelot extraction error: {e}")
            return []

        return tables

    def _extract_metadata(self, doc: fitz.Document, pdf_path: Path) -> Dict[str, Any]:
        """Extract PDF metadata using PyMuPDF"""
        metadata = {
            'filename': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'pages_count': len(doc),
            'pdf_metadata': {}
        }

        # PDF internal metadata
        pdf_meta = doc.metadata
        if pdf_meta:
            metadata['pdf_metadata'] = {
                'title': pdf_meta.get('title'),
                'author': pdf_meta.get('author'),
                'subject': pdf_meta.get('subject'),
                'creator': pdf_meta.get('creator'),
                'producer': pdf_meta.get('producer'),
                'creation_date': pdf_meta.get('creationDate'),
                'modification_date': pdf_meta.get('modDate')
            }

        return metadata

    def extract_page_range(
        self,
        pdf_path: str,
        start_page: int,
        end_page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract specific page range

        Args:
            pdf_path: Path to PDF
            start_page: Starting page (1-indexed)
            end_page: Ending page (inclusive), None for all remaining

        Returns:
            Extracted data for page range
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        if start_page < 1 or start_page > total_pages:
            raise ValueError(f"Invalid start_page: {start_page}")

        if end_page is None:
            end_page = total_pages

        if end_page < start_page or end_page > total_pages:
            raise ValueError(f"Invalid end_page: {end_page}")

        extracted = {
            'metadata': {
                'filename': Path(pdf_path).name,
                'page_range': f"{start_page}-{end_page}",
                'total_pages': total_pages
            },
            'pages': [],
            'tables': []
        }

        # Process page range (convert to 0-indexed)
        for page_num in range(start_page - 1, end_page):
            page = doc[page_num]
            actual_page_num = page_num + 1

            text = self._extract_page_text(page)
            cleaned_text = self._clean_text(text, actual_page_num)

            if cleaned_text:
                extracted['pages'].append({
                    'page_num': actual_page_num,
                    'text': cleaned_text,
                    'char_count': len(cleaned_text)
                })

        doc.close()

        # Extract tables for this range
        try:
            page_range_str = f"{start_page}-{end_page}"
            tables = camelot.read_pdf(
                pdf_path,
                flavor='lattice',
                pages=page_range_str,
                suppress_stdout=True
            )

            for idx, table in enumerate(tables):
                if table.df is not None and not table.df.empty:
                    extracted['tables'].append({
                        'page_num': table.page,
                        'table_id': f"p{table.page}_t{idx}",
                        'data': table.df.values.tolist(),
                        'rows': len(table.df),
                        'cols': len(table.df.columns)
                    })
        except Exception as e:
            logger.warning(f"Table extraction failed for page range: {e}")

        return extracted

    def extract_tables_only(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract only tables from PDF using Camelot

        Returns:
            List of tables with metadata
        """
        logger.info(f"Extracting tables only from {pdf_path}")
        tables = self._extract_tables_camelot(pdf_path)
        logger.info(f"Extracted {len(tables)} tables from {pdf_path}")
        return tables

    def get_page_count(self, pdf_path: str) -> int:
        """Quick check of page count without full extraction"""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count

    def validate_pdf(self, pdf_path: str, max_pages: int = 10000) -> Dict[str, Any]:
        """
        Validate PDF before processing

        Returns:
            Dict with validation result and info
        """
        pdf_path = Path(pdf_path)

        validation = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'info': {}
        }

        # Check file exists
        if not pdf_path.exists():
            validation['errors'].append(f"File not found: {pdf_path}")
            return validation

        # Check file extension
        if pdf_path.suffix.lower() not in self.supported_extensions:
            validation['errors'].append(f"Unsupported file type: {pdf_path.suffix}")
            return validation

        # Check file size
        file_size = pdf_path.stat().st_size
        validation['info']['file_size'] = file_size
        validation['info']['file_size_mb'] = round(file_size / (1024 * 1024), 2)

        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            validation['info']['page_count'] = page_count

            # Check page count
            if page_count == 0:
                validation['errors'].append("PDF has no pages")
                doc.close()
                return validation

            if page_count > max_pages:
                validation['errors'].append(
                    f"PDF has {page_count} pages, exceeds limit of {max_pages}"
                )
                doc.close()
                return validation

            if page_count > 5000:
                validation['warnings'].append(
                    f"Large PDF: {page_count} pages, processing may take time"
                )

            # Try to extract from first page
            first_page = doc[0]
            test_text = first_page.get_text("text")

            if not test_text or len(test_text.strip()) < 10:
                validation['warnings'].append("First page has minimal extractable text (may be image-based)")
            else:
                validation['info']['first_page_chars'] = len(test_text)

            validation['valid'] = True
            doc.close()

        except Exception as e:
            validation['errors'].append(f"PDF validation error: {str(e)}")
            return validation

        return validation


def create_file_hash(file_path: str) -> str:
    """Create SHA256 hash of file for deduplication"""
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in 64kb chunks
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()
