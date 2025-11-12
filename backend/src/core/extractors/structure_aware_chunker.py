"""
Structure-Aware Document Chunker with 3-Tier Strategy
Preserves table headers and temporal context during chunking

CRITICAL INNOVATIONS:
1. Tier 1: Keep complete small tables as single chunks (< 2000 chars, < 50 rows)
2. Tier 2: Split large tables with header preservation (>= 2000 chars OR >= 50 rows)
3. Tier 3: Preserve narrative text on pages with tables (no more text loss!)
4. Section-awareness: Use Docling's element structure for better chunking
"""

import logging
import hashlib
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class StructureAwareChunker:
    """
    Chunks documents while preserving structural integrity

    3-TIER STRATEGY:
    - Tier 1: Complete small tables → Single chunk
    - Tier 2: Large tables → Split with headers
    - Tier 3: Mixed pages → Chunk tables AND text separately

    This ensures:
    - Small tables stay complete for LLM analysis
    - Large tables split intelligently with full context
    - Narrative text never lost when tables present
    - Section structure preserved from Docling
    """

    # Tier 1 thresholds
    MAX_COMPLETE_TABLE_CHARS = 2000  # ~400 tokens
    MAX_COMPLETE_TABLE_ROWS = 50

    def __init__(
        self,
        chunk_size: int = 750,
        overlap: int = 120,
        min_chunk_size: int = 200
    ):
        """
        Initialize chunker with size parameters

        Args:
            chunk_size: Maximum characters per chunk (for text and split tables)
            overlap: Characters to overlap between chunks
            min_chunk_size: Minimum chunk size (prevents tiny chunks)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

        logger.info(
            f"StructureAwareChunker initialized with 3-tier strategy: "
            f"chunk_size={chunk_size}, overlap={overlap}, "
            f"max_complete_table={self.MAX_COMPLETE_TABLE_CHARS} chars"
        )

    def chunk_document(self, docling_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk entire document with structure preservation

        NEW ALGORITHM:
        1. For pages without tables → Chunk text normally
        2. For pages WITH tables → Chunk BOTH tables AND surrounding text
        3. Use Docling element structure for section awareness

        Args:
            docling_output: Output from DoclingProcessor.extract_all()

        Returns:
            List of chunks with enhanced metadata
        """
        all_chunks = []

        # Get all tables indexed by page (for efficient lookup)
        tables_by_page = self._index_tables_by_page(docling_output)

        # Process pages
        for page in docling_output.get("pages", []):
            page_num = page["page_num"]
            page_text = page.get("text", "")

            # Check if page has tables
            page_tables = tables_by_page.get(page_num, [])

            if page_tables:
                # TIER 3: Page with tables - chunk BOTH tables AND text
                logger.debug(f"Page {page_num}: Processing {len(page_tables)} tables + narrative text")

                # 1. Chunk all tables (using Tier 1 or Tier 2) with context window
                for table in page_tables:
                    table_chunks = self._chunk_table(table, page_num, page_text)
                    all_chunks.extend(table_chunks)

                # 2. Chunk narrative text (remove table markdown to avoid duplication)
                narrative_text = self._extract_narrative_text(page_text, page_tables)
                if narrative_text and len(narrative_text.strip()) >= self.min_chunk_size:
                    text_chunks = self._chunk_text(narrative_text, page_num)
                    all_chunks.extend(text_chunks)
                    logger.debug(f"Page {page_num}: Extracted {len(text_chunks)} narrative chunks")

            else:
                # Text-only page - chunk normally
                text_chunks = self._chunk_text(page_text, page_num)
                all_chunks.extend(text_chunks)

        # Add chunk_idx and word_count to each chunk (required by storage layer)
        for idx, chunk in enumerate(all_chunks):
            chunk["chunk_idx"] = idx
            chunk["word_count"] = len(chunk["text"].split())

        logger.info(
            f"Document chunked: {len(all_chunks)} chunks created "
            f"from {len(docling_output.get('pages', []))} pages "
            f"({len(docling_output.get('tables', []))} tables processed)"
        )

        return all_chunks

    def _chunk_table(self, table: Dict[str, Any], page_num: int, page_text: str = "") -> List[Dict[str, Any]]:
        """
        TIER 1 & TIER 2: Smart table chunking with context window

        DECISION LOGIC:
        - Small table (< 2000 chars, < 50 rows) → Single complete chunk (TIER 1)
        - Large table (>= 2000 chars OR >= 50 rows) → Split with headers (TIER 2)

        Phase 3 Enhancement: Now adds context window (sentences around table)
        """
        caption = table.get("caption", "")
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        temporal_markers = table.get("temporal_markers", [])
        table_id = table.get("table_id", "unknown")

        # Build complete table text
        complete_table_text = self._build_complete_table_text(caption, headers, rows)
        table_size = len(complete_table_text)
        row_count = len(rows)

        # DECISION POINT: Tier 1 or Tier 2?
        if self._should_keep_table_complete(table_size, row_count):
            # ✅ TIER 1: Keep complete
            logger.debug(
                f"Table {table_id}: TIER 1 (complete) - "
                f"{row_count} rows, {table_size} chars"
            )
            return self._create_complete_table_chunk(
                complete_table_text, table, page_num, page_text
            )

        else:
            # ⚠️ TIER 2: Split with headers
            logger.debug(
                f"Table {table_id}: TIER 2 (split) - "
                f"{row_count} rows, {table_size} chars"
            )
            return self._split_large_table(table, page_num, page_text)

    def _should_keep_table_complete(self, table_size: int, row_count: int) -> bool:
        """
        Decide if table should be kept as single complete chunk

        Rules:
        1. If > MAX_COMPLETE_TABLE_CHARS → Split
        2. If > MAX_COMPLETE_TABLE_ROWS → Split
        3. If slightly over chunk_size but < 30 rows → Keep (worth the overflow)
        4. Otherwise → Keep complete
        """
        # Rule 1: Too many characters
        if table_size > self.MAX_COMPLETE_TABLE_CHARS:
            return False

        # Rule 2: Too many rows
        if row_count > self.MAX_COMPLETE_TABLE_ROWS:
            return False

        # Rule 3: Allow moderate overflow for small row count
        if table_size <= self.chunk_size * 1.5 and row_count <= 30:
            return True

        # Default: Keep complete
        return True

    def _create_complete_table_chunk(
        self,
        table_text: str,
        table: Dict[str, Any],
        page_num: int,
        page_text: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Create single chunk for complete table (TIER 1)

        Phase 3 Enhancement: Now adds context window around table
        """
        # Phase 3: Extract context window
        context = self._extract_table_context(table_text, page_text)

        # Build enhanced chunk text with context
        chunk_parts = []
        if context['before']:
            chunk_parts.append(f"Context: {context['before']}")
            chunk_parts.append("")  # Blank line

        chunk_parts.append(table_text)

        if context['after']:
            chunk_parts.append("")  # Blank line
            chunk_parts.append(f"Context: {context['after']}")

        enhanced_text = "\n".join(chunk_parts)

        chunk = {
            "chunk_id": self._generate_chunk_id(enhanced_text),
            "text": enhanced_text,
            "char_count": len(enhanced_text),
            "page_num": page_num,
            "metadata": {
                "type": "table",
                "table_id": table.get("table_id"),
                "temporal_context": table.get("temporal_markers", []),
                "has_complete_headers": True,
                "is_complete_table": True,  # ← KEY FLAG!
                "chunking_tier": "tier_1_complete",
                "row_count": len(table.get("rows", [])),
                "column_count": len(table.get("headers", [])),
                "has_context_window": bool(context['before'] or context['after'])
            }
        }

        return [chunk]

    def _split_large_table(self, table: Dict[str, Any], page_num: int, page_text: str = "") -> List[Dict[str, Any]]:
        """
        TIER 2: Split large table with header preservation

        Algorithm:
        1. Build header block (caption + headers)
        2. Calculate available space for rows
        3. Batch rows to fit available space
        4. Each chunk = header_block + row_batch

        Phase 3 Enhancement: Add context to first and last chunks

        Result: Every chunk has complete context!
        """
        caption = table.get("caption", "")
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        temporal_markers = table.get("temporal_markers", [])
        table_id = table.get("table_id", "unknown")

        # Phase 3: Extract context window (we'll add to first/last chunks)
        table_text_sample = self._build_header_block(caption, headers)
        context = self._extract_table_context(table_text_sample, page_text)

        # Build header block (ALWAYS included in every chunk)
        header_block = self._build_header_block(caption, headers)
        header_block_size = len(header_block)

        # Calculate available space for data rows
        available_size = self.chunk_size - header_block_size

        if available_size < 100:  # Not enough space for meaningful data
            logger.warning(
                f"Table {table_id} headers too large ({header_block_size} chars). "
                "Increasing chunk size for this table."
            )
            available_size = 300  # Minimum space for data

        # Batch rows to fit available space
        row_batches = self._batch_rows(rows, available_size, headers)

        # Create chunks (each with header_block)
        # Phase 3: Add context to first and last chunks
        chunks = []
        total_batches = len(row_batches)

        for batch_idx, row_batch in enumerate(row_batches, 1):
            chunk_text = header_block + "\n" + self._format_row_batch(headers, row_batch)

            # Phase 3: Add context window to first and last chunks
            is_first = (batch_idx == 1)
            is_last = (batch_idx == total_batches)
            chunk_parts = []

            if is_first and context['before']:
                chunk_parts.append(f"Context: {context['before']}")
                chunk_parts.append("")  # Blank line

            chunk_parts.append(chunk_text)

            if is_last and context['after']:
                chunk_parts.append("")  # Blank line
                chunk_parts.append(f"Context: {context['after']}")

            enhanced_text = "\n".join(chunk_parts)

            chunk = {
                "chunk_id": self._generate_chunk_id(enhanced_text),
                "text": enhanced_text,
                "char_count": len(enhanced_text),
                "page_num": page_num,
                "metadata": {
                    "type": "table",
                    "table_id": table_id,
                    "temporal_context": temporal_markers,
                    "has_complete_headers": True,
                    "is_complete_table": False,  # ← Split table
                    "chunking_tier": "tier_2_split",
                    "table_section": f"{batch_idx}/{total_batches}",
                    "row_count": len(row_batch),
                    "column_count": len(headers),
                    "has_context_window": (is_first and bool(context['before'])) or (is_last and bool(context['after']))
                }
            }

            chunks.append(chunk)

        logger.debug(
            f"Table {table_id} split into {len(chunks)} chunks. "
            f"All chunks have headers + temporal context: {temporal_markers}"
        )

        return chunks

    def _build_complete_table_text(
        self,
        caption: str,
        headers: List[str],
        rows: List[List[str]]
    ) -> str:
        """Build complete table as markdown (for Tier 1 decision)"""
        header_block = self._build_header_block(caption, headers)
        row_text = self._format_row_batch(headers, rows)
        return header_block + "\n" + row_text

    def _build_header_block(self, caption: str, headers: List[str]) -> str:
        """
        Build the header block that will be included in EVERY table chunk

        Format:
        ## Caption with temporal context
        | Header 1 | Header 2 | Header 3 |
        |----------|----------|----------|

        This ensures temporal attribution is never lost!
        """
        lines = []

        # Add caption (contains temporal markers like "2024 roku")
        if caption:
            lines.append(caption.strip())
            lines.append("")  # Blank line

        # Add header row
        if headers:
            header_row = "| " + " | ".join(headers) + " |"
            separator = "|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|"
            lines.append(header_row)
            lines.append(separator)

        return "\n".join(lines)

    def _format_row_batch(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format a batch of table rows in markdown format"""
        lines = []
        for row in rows:
            # Pad row if needed to match header count
            padded_row = row + [""] * (len(headers) - len(row))
            row_text = "| " + " | ".join(padded_row[:len(headers)]) + " |"
            lines.append(row_text)
        return "\n".join(lines)

    def _batch_rows(
        self,
        rows: List[List[str]],
        available_size: int,
        headers: List[str]
    ) -> List[List[List[str]]]:
        """
        Batch rows to fit within available chunk size

        Strategy:
        - Calculate average row size
        - Estimate rows per batch
        - Create batches that fit in available_size

        Returns:
            List of row batches, each fitting in available_size
        """
        if not rows:
            return []

        # Estimate average row size
        sample_rows = rows[:min(10, len(rows))]
        avg_row_size = sum(
            len("| " + " | ".join(row[:len(headers)]) + " |")
            for row in sample_rows
        ) / len(sample_rows)

        # Calculate rows per batch (ensure at least 1 row per batch)
        rows_per_batch = max(1, int(available_size / avg_row_size))

        # Create batches
        batches = []
        for i in range(0, len(rows), rows_per_batch):
            batch = rows[i:i + rows_per_batch]
            batches.append(batch)

        return batches

    def _extract_narrative_text(self, page_text: str, page_tables: List[Dict]) -> str:
        """
        Extract narrative text from page, removing table markdown

        TIER 3 FIX: This ensures we don't lose text on pages with tables!

        Strategy:
        1. Remove all table markdown blocks
        2. Return remaining text (narrative, paragraphs, etc.)
        """
        narrative = page_text

        # Remove table markdown patterns
        # Pattern: | header | header |\n|--------|--------|\n| data | data |
        table_pattern = r'\|[^\n]+\n\|[-|\s]+\n(?:\|[^\n]+\n)+'
        narrative = re.sub(table_pattern, '', narrative, flags=re.MULTILINE)

        # Remove table captions (## headers before tables)
        # Look for headers that appear to be table captions
        for table in page_tables:
            caption = table.get("caption", "")
            if caption:
                narrative = narrative.replace(caption, "")

        # Clean up multiple blank lines
        narrative = re.sub(r'\n{3,}', '\n\n', narrative)

        return narrative.strip()

    def _chunk_text(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Chunk plain text using semantic boundaries

        For non-table content, use standard semantic chunking
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to break at semantic boundary
            if end < len(text):
                # Try paragraph break
                paragraph_break = text.rfind("\n\n", start, end)
                if paragraph_break > start + self.min_chunk_size:
                    end = paragraph_break

                # Try sentence break
                elif (sentence_break := self._find_sentence_break(text, start, end)) > start:
                    end = sentence_break

            chunk_text = text[start:end].strip()

            if len(chunk_text) >= self.min_chunk_size:
                chunk = {
                    "chunk_id": self._generate_chunk_id(chunk_text),
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "page_num": page_num,
                    "metadata": {
                        "type": "text",
                        "temporal_context": self._extract_temporal_markers(chunk_text),
                        "has_complete_headers": False,
                        "chunking_tier": "tier_3_text"
                    }
                }
                chunks.append(chunk)

            # Move forward (with overlap)
            start = max(start + 1, end - self.overlap)

        return chunks

    def _find_sentence_break(self, text: str, start: int, end: int) -> int:
        """Find the last sentence break (. ! ?) before end position"""
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']

        best_break = start
        for ending in sentence_endings:
            pos = text.rfind(ending, start, end)
            if pos > best_break:
                best_break = pos + len(ending)

        return best_break if best_break > start else end

    def _extract_temporal_markers(self, text: str) -> List[str]:
        """
        Extract comprehensive temporal markers from text

        Phase 3 Enhancement: Now detects:
        - Years (2023, 2024, etc.)
        - Quarters (Q1, Q2, I kwartał, II kwartał, etc.)
        - Polish months (styczeń, luty, marzec, etc.)
        """
        markers = []

        # Extract years (20XX)
        years = re.findall(r'\b(20\d{2})\b', text)
        markers.extend(years)

        # Extract quarters (Q1-Q4, English style)
        quarters_en = re.findall(r'\b([QK][1-4])\b', text, re.IGNORECASE)
        markers.extend([q.upper() for q in quarters_en])

        # Extract Polish quarters (I kwartał, II kwartał, etc.)
        quarters_pl = re.findall(
            r'\b([IV]{1,3})\s+kwartał',
            text,
            re.IGNORECASE
        )
        markers.extend([f"{q} kwartał" for q in quarters_pl])

        # Extract Polish months
        polish_months = [
            'styczeń', 'stycznia',
            'luty', 'lutego',
            'marzec', 'marca',
            'kwiecień', 'kwietnia',
            'maj', 'maja',
            'czerwiec', 'czerwca',
            'lipiec', 'lipca',
            'sierpień', 'sierpnia',
            'wrzesień', 'września',
            'październik', 'października',
            'listopad', 'listopada',
            'grudzień', 'grudnia'
        ]

        for month in polish_months:
            if month in text.lower():
                # Normalize to base form (nominative case)
                base_month = month.split()[0] if ' ' in month else month.rstrip('a')
                if base_month not in markers:
                    markers.append(base_month)

        # Deduplicate while preserving order
        return list(dict.fromkeys(markers))

    def _extract_table_context(self, table_text: str, page_text: str) -> Dict[str, str]:
        """
        Extract context window around table (Phase 3 Enhancement)

        Extracts 2-3 sentences before and 1-2 sentences after the table
        to provide narrative context for better retrieval.

        Args:
            table_text: The table text (caption or header block)
            page_text: Full page text

        Returns:
            Dict with 'before' and 'after' context strings
        """
        context = {'before': '', 'after': ''}

        if not page_text or not table_text:
            return context

        # Try to find table position using table start marker (caption or first line)
        table_start_marker = table_text.split('\n')[0][:50]  # Use first 50 chars of first line

        # Find table position in page text
        table_pos = page_text.find(table_start_marker)

        if table_pos == -1:
            # Table not found in page text (could be cleaned/processed differently)
            return context

        # Extract text before table
        text_before = page_text[:table_pos].strip()
        if text_before:
            # Split into sentences (approximate - handles Polish punctuation)
            sentences_before = re.split(r'[.!?]\s+', text_before)
            # Get last 2-3 sentences
            context_sentences = sentences_before[-3:] if len(sentences_before) >= 3 else sentences_before
            context['before'] = ' '.join(context_sentences).strip()
            # Limit to 300 chars
            if len(context['before']) > 300:
                context['before'] = context['before'][-300:].strip()

        # Extract text after table (find end of table markdown)
        # Look for end of table markdown pattern
        remaining_text = page_text[table_pos:]
        table_end_pattern = r'\|[^\n]+\n(?!\|)'  # Last line with | followed by non-| line
        match = re.search(table_end_pattern, remaining_text)

        if match:
            text_after = remaining_text[match.end():].strip()
            if text_after:
                # Split into sentences
                sentences_after = re.split(r'[.!?]\s+', text_after)
                # Get first 1-2 sentences
                context_sentences = sentences_after[:2] if len(sentences_after) >= 2 else sentences_after
                context['after'] = ' '.join(context_sentences).strip()
                # Limit to 200 chars
                if len(context['after']) > 200:
                    context['after'] = context['after'][:200].strip()

        return context

    def _extract_years(self, text: str) -> List[str]:
        """
        Extract year markers (20XX) from text
        Kept for backward compatibility
        """
        years = re.findall(r'\b(20\d{2})\b', text)
        return list(dict.fromkeys(years))  # Deduplicate while preserving order

    def _generate_chunk_id(self, text: str) -> str:
        """Generate unique chunk ID from text content"""
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return f"chunk_{hash_obj.hexdigest()[:12]}"

    def _index_tables_by_page(self, docling_output: Dict[str, Any]) -> Dict[int, List[Dict]]:
        """Index tables by page number for efficient lookup"""
        tables_by_page = {}

        for table in docling_output.get("tables", []):
            page_num = table.get("page_num", 0)

            # Also check if table caption appears in any page
            if page_num == 0:
                caption = table.get("caption", "")
                for page in docling_output.get("pages", []):
                    if caption and caption in page.get("text", ""):
                        page_num = page["page_num"]
                        break

            if page_num > 0:
                if page_num not in tables_by_page:
                    tables_by_page[page_num] = []
                tables_by_page[page_num].append(table)

        return tables_by_page

    def _table_in_page(self, table: Dict, page: Dict) -> bool:
        """Check if table caption appears in page text"""
        caption = table.get("caption", "")
        page_text = page.get("text", "")
        return caption in page_text if caption else False

    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics about the chunks

        Args:
            chunks: List of chunks from chunk_document()

        Returns:
            Dictionary with statistics including tier breakdown
        """
        if not chunks:
            return {
                'chunk_count': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'table_chunks': 0,
                'text_chunks': 0,
                'tier_1_complete_tables': 0,
                'tier_2_split_tables': 0,
                'tier_3_text': 0
            }

        chunk_sizes = [chunk['char_count'] for chunk in chunks]
        table_chunks = sum(
            1 for chunk in chunks
            if chunk.get('metadata', {}).get('type') == 'table'
        )
        text_chunks = len(chunks) - table_chunks

        # Count by tier
        tier_1 = sum(
            1 for chunk in chunks
            if chunk.get('metadata', {}).get('chunking_tier') == 'tier_1_complete'
        )
        tier_2 = sum(
            1 for chunk in chunks
            if chunk.get('metadata', {}).get('chunking_tier') == 'tier_2_split'
        )
        tier_3 = sum(
            1 for chunk in chunks
            if chunk.get('metadata', {}).get('chunking_tier') == 'tier_3_text'
        )

        return {
            'chunk_count': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'table_chunks': table_chunks,
            'text_chunks': text_chunks,
            'tier_1_complete_tables': tier_1,
            'tier_2_split_tables': tier_2,
            'tier_3_text': tier_3
        }


# Convenience function for testing
def chunk_docling_output(docling_output: Dict[str, Any], chunk_size: int = 750) -> List[Dict[str, Any]]:
    """
    Simple chunking interface for testing

    Usage:
        from src.core.extractors.structure_aware_chunker import chunk_docling_output
        from src.core.extractors.docling_processor import extract_pdf

        docling_output = extract_pdf("/path/to/report.pdf")
        chunks = chunk_docling_output(docling_output)

        # Verify 3-tier strategy
        stats = chunks[0].get_chunk_statistics(chunks)
        print(f"Tier 1 (complete tables): {stats['tier_1_complete_tables']}")
        print(f"Tier 2 (split tables): {stats['tier_2_split_tables']}")
        print(f"Tier 3 (text chunks): {stats['tier_3_text']}")
    """
    chunker = StructureAwareChunker(chunk_size=chunk_size)
    return chunker.chunk_document(docling_output)
