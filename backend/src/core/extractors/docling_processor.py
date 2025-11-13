"""
Docling-based PDF Processor with Structure Awareness
Addresses the temporal attribution problem by preserving table headers and context
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None

logger = logging.getLogger(__name__)


class DoclingProcessor:
    """
    Structure-aware PDF processor using IBM Granite-Docling-258M

    Key Features:
    - Preserves table structure (headers + data)
    - Extracts temporal markers from captions
    - Maintains reading order
    - Provides backward-compatible output format

    Addresses Priority 1 Issue:
    Multi-column comparative tables lose temporal context when chunked.
    Docling preserves table captions (e.g., "31 grudnia 2024 roku") with data.
    """

    def __init__(self, python_path: str = "python3.11"):
        """
        Initialize Docling processor

        Args:
            python_path: Path to Python 3.11 executable (required for Docling)
        """
        self.python_path = python_path
        self.converter = None
        logger.info("DoclingProcessor initialized")

    def _ensure_converter(self):
        """Lazy-load the DocumentConverter (model download on first use)"""
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling is not available. Install it with: pip install docling"
            )
        if self.converter is None:
            logger.info("Initializing DocumentConverter...")
            start = time.time()
            self.converter = DocumentConverter()
            elapsed = time.time() - start
            logger.info(f"DocumentConverter initialized in {elapsed:.2f}s")

    def extract_all(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract PDF with full structure preservation

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with structured extraction results:
            {
                "metadata": {...},
                "pages": [
                    {
                        "page_num": int,
                        "text": str,  # For backward compatibility
                        "elements": [  # NEW: structured elements
                            {
                                "type": "text" | "table" | "picture",
                                "content": str | dict,
                                "metadata": {
                                    "temporal_context": List[str],
                                    "has_headers": bool
                                }
                            }
                        ]
                    }
                ],
                "tables": [  # Enhanced table info
                    {
                        "page_num": int,
                        "caption": str,  # Temporal context here!
                        "headers": List[str],
                        "rows": List[List[str]],
                        "temporal_markers": List[str]
                    }
                ],
                "processing_time": float
            }
        """
        logger.info(f"Processing PDF with Docling: {pdf_path}")
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Ensure converter is initialized
        self._ensure_converter()

        # Convert document
        start_time = time.time()
        try:
            result = self.converter.convert(str(pdf_path))
            processing_time = time.time() - start_time
            logger.info(f"Conversion complete in {processing_time:.2f}s")
        except Exception as e:
            logger.error(f"Docling conversion failed: {e}", exc_info=True)
            raise

        # Structure output
        try:
            structured_output = self._structure_output(result, processing_time)
            logger.info(
                f"Extraction complete: {len(structured_output['pages'])} pages, "
                f"{len(structured_output['tables'])} tables"
            )
            return structured_output
        except Exception as e:
            logger.error(f"Output structuring failed: {e}", exc_info=True)
            raise

    def _structure_output(self, docling_result, processing_time: float) -> Dict[str, Any]:
        """
        Convert Docling output to IIP-compatible format

        Args:
            docling_result: Result from DocumentConverter.convert()
            processing_time: Time taken for conversion

        Returns:
            Structured dictionary with pages, tables, and metadata
        """
        doc = docling_result.document

        # Extract metadata
        metadata = {
            "filename": doc.name if hasattr(doc, 'name') else "unknown",
            "processing_time": processing_time,
            "extractor": "docling",
            "docling_version": "1.8.0"  # From PoC JSON output
        }

        # Get markdown and JSON exports for analysis
        markdown_text = doc.export_to_markdown()
        json_data = doc.export_to_dict()

        # Extract pages with structure
        pages = self._extract_pages(markdown_text, json_data)

        # Extract tables with enhanced metadata
        tables = self._extract_tables(markdown_text, json_data)

        # Calculate extraction statistics (for compatibility with PDFProcessor)
        total_chars = sum(len(page.get('text', '')) for page in pages)
        extraction_stats = {
            'total_pages': len(pages),
            'pages_with_text': len([p for p in pages if p.get('text', '').strip()]),
            'total_tables': len(tables),
            'total_characters': total_chars,
            'average_chars_per_page': total_chars / max(len(pages), 1)
        }

        return {
            "metadata": metadata,
            "pages": pages,
            "tables": tables,
            "extraction_stats": extraction_stats,
            "processing_time": processing_time,
            "raw_markdown": markdown_text,  # For debugging/inspection
            "raw_json": json_data  # For debugging/inspection
        }

    def _extract_pages(self, markdown_text: str, json_data: Dict) -> List[Dict[str, Any]]:
        """
        Extract page-level information

        Strategy:
        - Use markdown for human-readable content
        - Use JSON for structured metadata
        - Combine both for rich page representation
        """
        # Split markdown by major sections (approximates pages)
        # Note: Docling doesn't explicitly mark page boundaries in markdown,
        # so we'll use section headers as logical page breaks

        sections = []
        current_section = {"text": "", "elements": []}

        for line in markdown_text.split('\n'):
            if line.startswith('## '):  # H2 headers mark major sections
                if current_section["text"]:
                    sections.append(current_section)
                current_section = {
                    "text": line + "\n",
                    "elements": [{"type": "heading", "content": line}]
                }
            else:
                current_section["text"] += line + "\n"

        if current_section["text"]:
            sections.append(current_section)

        # Convert sections to pages
        pages = []
        for idx, section in enumerate(sections, 1):
            pages.append({
                "page_num": idx,
                "text": section["text"],
                "elements": section["elements"],
                "metadata": {
                    "has_tables": self._section_has_tables(section["text"]),
                    "temporal_context": self._extract_temporal_markers(section["text"])
                }
            })

        logger.info(f"Extracted {len(pages)} logical pages")
        return pages

    def _extract_tables(self, markdown_text: str, json_data: Dict) -> List[Dict[str, Any]]:
        """
        Extract tables with full context preservation

        This is the CRITICAL method that solves the temporal attribution problem!
        """
        tables = []

        # Find all tables in markdown
        table_pattern = r'(## [^\n]+\n\n)?\|([^\n]+)\n\|[-|\s]+\n((?:\|[^\n]+\n)+)'
        matches = re.finditer(table_pattern, markdown_text, re.MULTILINE)

        for idx, match in enumerate(matches, 1):
            caption = match.group(1).strip() if match.group(1) else ""
            header_line = match.group(2)
            data_lines = match.group(3)

            # Parse headers
            headers = [h.strip() for h in header_line.split('|') if h.strip()]

            # Parse rows
            rows = []
            for line in data_lines.strip().split('\n'):
                if line.startswith('|'):
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if cells:
                        rows.append(cells)

            # Extract temporal markers from caption
            temporal_markers = self._extract_temporal_markers(caption)

            table_dict = {
                "table_id": f"table_{idx}",
                "page_num": 0,  # Will be updated if we can determine page
                "caption": caption,
                "headers": headers,
                "rows": rows,
                "temporal_markers": temporal_markers,
                "metadata": {
                    "has_complete_headers": bool(headers),
                    "has_temporal_context": bool(temporal_markers),
                    "row_count": len(rows),
                    "column_count": len(headers)
                }
            }

            tables.append(table_dict)
            logger.debug(
                f"Extracted table {idx}: {len(headers)} columns, {len(rows)} rows, "
                f"temporal markers: {temporal_markers}"
            )

        logger.info(f"Extracted {len(tables)} tables with structure preserved")
        return tables

    def _extract_temporal_markers(self, text: str) -> List[str]:
        """
        Extract year markers and temporal context from text

        Patterns:
        - "31 grudnia 2024 roku" → ["2024"]
        - "2024 roku" → ["2024"]
        - "2024-12-31" → ["2024"]
        - Any 4-digit year 20XX → ["20XX"]
        """
        markers = []

        # Find all 4-digit years starting with 20
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, text)
        markers.extend(years)

        # Deduplicate while preserving order
        seen = set()
        unique_markers = []
        for marker in markers:
            if marker not in seen:
                seen.add(marker)
                unique_markers.append(marker)

        return unique_markers

    def _section_has_tables(self, text: str) -> bool:
        """Check if a section contains tables (markdown table format)"""
        return '|' in text and '---' in text

    def extract_page_range(
        self,
        pdf_path: str,
        start_page: int,
        end_page: int
    ) -> Dict[str, Any]:
        """
        Extract specific page range (for testing/debugging)

        Note: Docling processes entire document, so this is a post-processing filter
        """
        full_result = self.extract_all(pdf_path)

        # Filter pages
        filtered_pages = [
            page for page in full_result["pages"]
            if start_page <= page["page_num"] <= end_page
        ]

        # Filter tables (approximate - based on caption content)
        filtered_tables = [
            table for table in full_result["tables"]
            if start_page <= table["page_num"] <= end_page
        ]

        return {
            **full_result,
            "pages": filtered_pages,
            "tables": filtered_tables
        }

    def get_table_with_context(self, table_id: str, all_tables: List[Dict]) -> Dict[str, Any]:
        """
        Get a specific table with full temporal context

        This method ensures investigators always have year context!
        """
        table = next((t for t in all_tables if t["table_id"] == table_id), None)

        if not table:
            raise ValueError(f"Table {table_id} not found")

        # Enrich with explicit warning if temporal context missing
        if not table["temporal_markers"]:
            logger.warning(
                f"Table {table_id} has no temporal markers! "
                "Investigation conclusions may be ambiguous."
            )
            table["metadata"]["temporal_warning"] = (
                "No year identification found in table caption"
            )

        return table


# Convenience function for backward compatibility
def extract_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Simple extraction interface for testing

    Usage:
        from src.core.extractors.docling_processor import extract_pdf
        result = extract_pdf("/path/to/report.pdf")
        print(f"Found {len(result['tables'])} tables")
    """
    processor = DoclingProcessor()
    return processor.extract_all(pdf_path)
