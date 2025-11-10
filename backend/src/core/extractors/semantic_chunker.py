"""
Semantic Text Chunking Module using LangChain
Chunks text based on semantic boundaries (paragraphs, sentences, sections)
"""

import hashlib
from typing import List, Dict, Any
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Semantic text chunking using LangChain's RecursiveCharacterTextSplitter

    Splits by semantic boundaries in this order:
    1. Double newlines (paragraphs)
    2. Single newlines
    3. Spaces (words)
    4. Characters (last resort)

    Optimal for RAG applications - maintains semantic coherence
    """

    def __init__(
        self,
        chunk_size: int = 750,
        chunk_overlap: int = 120,
        min_chunk_size: int = 200
    ):
        """
        Initialize semantic chunker with LangChain

        Args:
            chunk_size: Target characters per chunk (default: 750)
            chunk_overlap: Overlap between chunks (default: 120)
            min_chunk_size: Minimum chunk size (default: 200)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Initialize LangChain's RecursiveCharacterTextSplitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines
                ". ",    # Sentences
                "! ",    # Sentences
                "? ",    # Sentences
                "; ",    # Clauses
                ", ",    # Phrases
                " ",     # Words
                ""       # Characters
            ]
        )

        logger.info(
            f"SemanticChunker initialized (LangChain): chunk_size={chunk_size}, "
            f"overlap={chunk_overlap}, min_size={min_chunk_size}"
        )

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create semantic chunks from extracted pages

        Args:
            pages: List of page dicts from PDFProcessor

        Returns:
            List of chunk dicts with metadata
        """
        all_chunks = []

        for page in pages:
            text = page.get('text', '')
            page_num = page.get('page_num')

            if not text or len(text.strip()) < self.min_chunk_size:
                continue

            # Split page into semantic chunks using LangChain
            page_chunks = self._chunk_page(text, page_num)
            all_chunks.extend(page_chunks)

        logger.info(f"Created {len(all_chunks)} semantic chunks from {len(pages)} pages")
        return all_chunks

    def _chunk_page(
        self,
        text: str,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """
        Chunk single page text using LangChain splitter

        Args:
            text: Text to chunk
            page_num: Page number for metadata

        Returns:
            List of chunks for this page
        """
        # Use LangChain to split text semantically
        text_chunks = self.splitter.split_text(text)

        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunk_text = chunk_text.strip()

            # Skip chunks that are too small
            if len(chunk_text) < self.min_chunk_size:
                logger.debug(f"Skipping small chunk on page {page_num}: {len(chunk_text)} chars")
                continue

            chunk_id = self._generate_chunk_id(chunk_text, page_num, idx)

            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'page_num': page_num,
                'chunk_idx': idx,
                'char_count': len(chunk_text),
                'word_count': len(chunk_text.split()),
                'is_complete_page': False
            })

        return chunks

    def _generate_chunk_id(self, text: str, page_num: int, chunk_idx: int) -> str:
        """
        Generate unique ID for chunk

        Args:
            text: Chunk text
            page_num: Page number
            chunk_idx: Chunk index within page

        Returns:
            8-character hash ID
        """
        content = f"{page_num}_{chunk_idx}_{text}"
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:8]

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
