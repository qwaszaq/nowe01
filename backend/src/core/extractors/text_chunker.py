"""
Text Chunking Module
Smart chunking with overlap for embeddings
100% deterministic, no LLM calls
"""

import hashlib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Smart text chunking with configurable size and overlap
    Preserves page numbers and context for citation tracking
    """

    def __init__(self, chunk_size: int = 750, overlap: int = 120):
        """
        Initialize chunker

        Args:
            chunk_size: Target characters per chunk
            overlap: Characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

        if overlap >= chunk_size:
            raise ValueError("Overlap must be smaller than chunk_size")

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create chunks from extracted pages

        Args:
            pages: List of page dicts from PDFProcessor

        Returns:
            List of chunk dicts with metadata
        """
        all_chunks = []

        for page in pages:
            text = page.get('text', '')
            page_num = page.get('page_num')

            if not text:
                continue

            # If page is smaller than chunk_size, keep as single chunk
            if len(text) <= self.chunk_size:
                chunk_id = self._generate_chunk_id(text, page_num, 0)
                all_chunks.append({
                    'chunk_id': chunk_id,
                    'text': text,
                    'page_num': page_num,
                    'chunk_idx': 0,
                    'char_count': len(text),
                    'word_count': len(text.split()),
                    'is_complete_page': True
                })
                continue

            # Chunk with overlap
            page_chunks = self._chunk_text_with_overlap(text, page_num)
            all_chunks.extend(page_chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
        return all_chunks

    def _chunk_text_with_overlap(
        self,
        text: str,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """
        Chunk single page text with overlap

        Args:
            text: Text to chunk
            page_num: Page number for metadata

        Returns:
            List of chunks for this page
        """
        chunks = []
        start = 0
        chunk_idx = 0

        while start < len(text):
            # Determine end position
            end = min(start + self.chunk_size, len(text))

            # Try to break at sentence boundary if possible
            if end < len(text):
                # Look for sentence endings near the boundary
                boundary_window = text[end - 50:end + 50] if end >= 50 else text[end:end + 50]
                sentence_endings = ['. ', '! ', '? ', '\n\n']

                best_break = -1
                for ending in sentence_endings:
                    pos = boundary_window.rfind(ending)
                    if pos != -1:
                        best_break = max(best_break, pos)

                if best_break != -1:
                    # Adjust end to sentence boundary
                    end = (end - 50 if end >= 50 else end) + best_break + 1

            chunk_text = text[start:end].strip()

            if chunk_text:  # Skip empty chunks
                chunk_id = self._generate_chunk_id(chunk_text, page_num, chunk_idx)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'page_num': page_num,
                    'chunk_idx': chunk_idx,
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split()),
                    'is_complete_page': False,
                    'position': {
                        'start': start,
                        'end': end,
                        'total_length': len(text)
                    }
                })

                chunk_idx += 1

            # Move start position (with overlap)
            new_start = end - self.overlap

            # Ensure start always advances to avoid infinite loop
            if new_start <= start:
                new_start = start + 1

            start = new_start

            # Avoid infinite loop
            if start >= len(text):
                break

        return chunks

    def chunk_text(self, text: str, page_num: int = 1) -> List[Dict[str, Any]]:
        """
        Chunk arbitrary text (not from PDF pages)

        Args:
            text: Text to chunk
            page_num: Page number to assign (default 1)

        Returns:
            List of chunks
        """
        return self._chunk_text_with_overlap(text, page_num)

    def _generate_chunk_id(self, text: str, page_num: int, chunk_idx: int) -> str:
        """
        Generate unique ID for chunk based on content

        Args:
            text: Chunk text
            page_num: Page number
            chunk_idx: Chunk index within page

        Returns:
            8-character hash ID
        """
        # Include page and index in hash for uniqueness
        content = f"{page_num}_{chunk_idx}_{text}"
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:8]

    def merge_small_chunks(
        self,
        chunks: List[Dict[str, Any]],
        min_size: int = 200,
        max_size: int = 750
    ) -> List[Dict[str, Any]]:
        """
        Merge consecutive small chunks from same page, respecting max size

        Args:
            chunks: List of chunks
            min_size: Minimum chunk size before merging
            max_size: Maximum chunk size (won't merge if it would exceed this)

        Returns:
            List with merged chunks
        """
        if not chunks:
            return []

        merged = []
        buffer = None

        for chunk in chunks:
            # If chunk is large enough, flush buffer and add chunk
            if chunk['char_count'] >= min_size:
                if buffer:
                    merged.append(buffer)
                    buffer = None
                merged.append(chunk)
                continue

            # If no buffer, start one
            if buffer is None:
                buffer = chunk.copy()
                continue

            # If same page, try to merge into buffer
            if buffer['page_num'] == chunk['page_num']:
                # Check if merging would exceed max_size
                new_size = buffer['char_count'] + chunk['char_count'] + 1  # +1 for space

                if new_size <= max_size:
                    # Safe to merge
                    buffer['text'] += ' ' + chunk['text']
                    buffer['char_count'] = new_size
                    buffer['word_count'] += chunk['word_count']

                    # Update chunk ID
                    buffer['chunk_id'] = self._generate_chunk_id(
                        buffer['text'],
                        buffer['page_num'],
                        buffer['chunk_idx']
                    )
                else:
                    # Would exceed max_size, flush buffer and start new
                    merged.append(buffer)
                    buffer = chunk.copy()
            else:
                # Different page, flush buffer and start new
                merged.append(buffer)
                buffer = chunk.copy()

        # Don't forget last buffer
        if buffer:
            merged.append(buffer)

        logger.info(f"Merged {len(chunks)} chunks into {len(merged)} chunks (min={min_size}, max={max_size})")
        return merged

    def split_large_chunks(
        self,
        chunks: List[Dict[str, Any]],
        max_size: int = 750,
        tolerance: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split chunks that significantly exceed max_size

        Allows small tolerance (e.g., 750 + 50 = 800 chars is OK)
        Only splits chunks that are way over the limit

        Args:
            chunks: List of chunks
            max_size: Target maximum chunk size
            tolerance: Additional chars allowed (default 50)

        Returns:
            List with split chunks
        """
        split_chunks = []
        threshold = max_size + tolerance  # e.g., 800 chars

        for chunk in chunks:
            if chunk['char_count'] <= threshold:
                # Chunk is acceptable (under max + tolerance), keep as-is
                split_chunks.append(chunk)
            else:
                # Chunk is significantly too large, split it
                text = chunk['text']
                page_num = chunk['page_num']

                # Simple split without re-chunking: just split at max_size boundaries
                # This avoids creating many tiny chunks
                current_pos = 0
                chunk_idx = 0

                while current_pos < len(text):
                    end_pos = min(current_pos + max_size, len(text))

                    # Try to break at sentence boundary near end
                    if end_pos < len(text):
                        # Look for sentence endings in last 100 chars
                        search_text = text[max(end_pos - 100, current_pos):end_pos]
                        for ending in ['. ', '! ', '? ', '\n']:
                            last_idx = search_text.rfind(ending)
                            if last_idx != -1:
                                end_pos = max(end_pos - 100, current_pos) + last_idx + len(ending)
                                break

                    chunk_text = text[current_pos:end_pos].strip()

                    if chunk_text:
                        split_chunks.append({
                            'chunk_id': self._generate_chunk_id(chunk_text, page_num, chunk_idx),
                            'text': chunk_text,
                            'page_num': page_num,
                            'chunk_idx': chunk_idx,
                            'char_count': len(chunk_text),
                            'word_count': len(chunk_text.split()),
                            'is_complete_page': False
                        })
                        chunk_idx += 1

                    # Move forward with overlap
                    current_pos = end_pos - self.overlap
                    if current_pos <= end_pos - max_size:
                        current_pos = end_pos

        logger.info(f"Split {len(chunks)} chunks into {len(split_chunks)} chunks (threshold={threshold})")
        return split_chunks

    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics about chunks

        Returns:
            Dict with chunk statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_chars': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0
            }

        char_counts = [c['char_count'] for c in chunks]

        return {
            'total_chunks': len(chunks),
            'total_chars': sum(char_counts),
            'avg_chunk_size': sum(char_counts) / len(char_counts),
            'min_chunk_size': min(char_counts),
            'max_chunk_size': max(char_counts),
            'pages_covered': len(set(c['page_num'] for c in chunks))
        }

    def extract_context_window(
        self,
        chunks: List[Dict[str, Any]],
        target_chunk_id: str,
        window_size: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get chunks around a target chunk for context

        Args:
            chunks: All chunks
            target_chunk_id: ID of target chunk
            window_size: Number of chunks before and after

        Returns:
            List of chunks in context window
        """
        # Find target chunk index
        target_idx = None
        for idx, chunk in enumerate(chunks):
            if chunk['chunk_id'] == target_chunk_id:
                target_idx = idx
                break

        if target_idx is None:
            return []

        # Extract window
        start_idx = max(0, target_idx - window_size)
        end_idx = min(len(chunks), target_idx + window_size + 1)

        return chunks[start_idx:end_idx]


def create_citation_context(
    chunk: Dict[str, Any],
    context_chars: int = 200
) -> Dict[str, str]:
    """
    Create citation context from chunk

    Args:
        chunk: Chunk dict
        context_chars: Characters of context before/after

    Returns:
        Dict with text_excerpt, context_before, context_after
    """
    text = chunk['text']
    mid_point = len(text) // 2

    # Extract around middle of chunk
    start = max(0, mid_point - context_chars // 2)
    end = min(len(text), mid_point + context_chars // 2)

    return {
        'text_excerpt': text[start:end],
        'context_before': text[max(0, start - context_chars):start],
        'context_after': text[end:min(len(text), end + context_chars)],
        'full_text': text,
        'page_num': chunk['page_num']
    }
