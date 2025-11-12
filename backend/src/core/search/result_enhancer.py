"""
Search Result Enhancement - Phase 1 Improvements
Provides re-ranking and snippet generation for better user experience
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SearchResultEnhancer:
    """
    Enhances semantic search results with:
    - Metadata-based re-ranking (boost tables for financial queries)
    - Quality penalty for low-information chunks
    - Better snippet generation for user display
    """

    # Polish financial terminology that suggests tables are needed
    FINANCIAL_TERMS = [
        'przychody', 'należności', 'zobowiązania', 'aktywa',
        'kapitał', 'zysk', 'kredyty', 'pożyczki', 'zapasy',
        'koszty', 'amortyzacja', 'przepływy', 'sprzedaż',
        'środki', 'trwałe', 'obrotowe', 'kapitałowy', 'własny',
        'netto', 'brutto', 'długoterminowe', 'krótkoterminowe'
    ]

    # Year patterns for temporal queries
    YEAR_PATTERN = r'\b(202[0-9]|201[0-9])\b'

    def rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results based on quality signals

        Args:
            results: List of search results from Qdrant
            query: User's search query

        Returns:
            Re-ranked list of results
        """
        if not results:
            return results

        # Detect query intent
        needs_tables = self._detect_table_need(query)
        has_year = bool(re.search(self.YEAR_PATTERN, query))

        logger.debug(
            f"Re-ranking {len(results)} results: "
            f"needs_tables={needs_tables}, has_year={has_year}"
        )

        # Apply ranking adjustments
        ranked_results = []
        for result in results:
            original_score = result['score']
            adjusted_score = original_score

            # Get metadata
            chunk_type = result.get('chunk_type', 'text')
            text = result.get('text', '')
            temporal_context = result.get('temporal_context', [])

            # Boost tables for financial queries
            if needs_tables and chunk_type == 'table':
                adjusted_score *= 1.15
                logger.debug(
                    f"  Table boost: {original_score:.3f} → {adjusted_score:.3f}"
                )

            # Penalize low-quality chunks (lots of markdown formatting)
            dash_ratio = text.count('-') / max(len(text), 1)
            if dash_ratio > 0.3:
                adjusted_score *= 0.85
                logger.debug(
                    f"  Quality penalty (dash_ratio={dash_ratio:.2f}): "
                    f"{original_score:.3f} → {adjusted_score:.3f}"
                )

            # Boost temporal context for time-specific queries
            if has_year and temporal_context:
                query_years = re.findall(self.YEAR_PATTERN, query)
                # Extra boost if years match
                if any(year in temporal_context for year in query_years):
                    adjusted_score *= 1.20
                    logger.debug(
                        f"  Temporal match boost: "
                        f"{original_score:.3f} → {adjusted_score:.3f}"
                    )
                else:
                    # Small boost for any temporal context
                    adjusted_score *= 1.05

            # Store both scores
            result['original_score'] = original_score
            result['adjusted_score'] = adjusted_score
            ranked_results.append(result)

        # Sort by adjusted score
        ranked_results.sort(key=lambda x: x['adjusted_score'], reverse=True)

        # Log ranking changes
        for i, result in enumerate(ranked_results[:5], 1):
            logger.debug(
                f"  Rank {i}: page={result.get('page_num')}, "
                f"type={result.get('chunk_type')}, "
                f"score={result['adjusted_score']:.3f} "
                f"(orig={result['original_score']:.3f})"
            )

        return ranked_results

    def generate_snippet(
        self,
        result: Dict[str, Any],
        query: str,
        max_length: int = 200
    ) -> str:
        """
        Generate informative snippet for search result

        Args:
            result: Search result dict
            query: User's search query
            max_length: Maximum snippet length

        Returns:
            Human-readable snippet
        """
        text = result.get('text', '')
        chunk_type = result.get('chunk_type', 'text')

        # For tables: extract caption + first data row
        if chunk_type == 'table':
            return self._generate_table_snippet(text, max_length)

        # For text: find most relevant sentence
        return self._generate_text_snippet(text, query, max_length)

    def _generate_table_snippet(self, text: str, max_length: int) -> str:
        """Generate snippet for table chunk"""
        lines = text.split('\n')

        # Extract caption (usually starts with ##)
        caption = ""
        for line in lines:
            if line.strip().startswith('##'):
                caption = line.strip().replace('##', '').strip()
                break

        # Find first data row (skip headers and separator)
        data_lines = []
        for line in lines:
            stripped = line.strip()
            if (stripped and
                stripped.startswith('|') and
                not stripped.startswith('|---') and
                not stripped.startswith('##')):
                # Clean up the line
                clean_line = stripped.replace('|', ' | ').strip()
                data_lines.append(clean_line)
                if len(data_lines) >= 2:  # Header + first row
                    break

        if caption and data_lines:
            snippet = f"{caption}: {' '.join(data_lines[:2])}"
        elif caption:
            snippet = caption
        elif data_lines:
            snippet = ' '.join(data_lines[:2])
        else:
            # Fallback: clean text
            snippet = self._clean_text(text)

        return snippet[:max_length] + ("..." if len(snippet) > max_length else "")

    def _generate_text_snippet(
        self,
        text: str,
        query: str,
        max_length: int
    ) -> str:
        """Generate snippet for text chunk"""
        # Clean the text first
        clean = self._clean_text(text)

        if len(clean) <= max_length:
            return clean

        # Try to find most relevant sentence
        sentences = re.split(r'[.!?]\s+', clean)
        query_terms = query.lower().split()

        # Score sentences by query term overlap
        best_sentence = None
        best_score = 0

        for sentence in sentences:
            if len(sentence) < 20:  # Skip very short sentences
                continue

            score = sum(
                1 for term in query_terms
                if term.lower() in sentence.lower()
            )

            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_sentence:
            snippet = best_sentence.strip()
            return snippet[:max_length] + ("..." if len(snippet) > max_length else "")

        # Fallback: first N characters
        return clean[:max_length] + "..."

    def _clean_text(self, text: str) -> str:
        """Remove markdown formatting and clean text"""
        # Remove markdown table syntax
        text = re.sub(r'\|[-|\s]+\|', ' ', text)
        text = re.sub(r'\|', ' ', text)

        # Remove excessive dashes
        text = re.sub(r'-{3,}', ' ', text)

        # Remove markdown headers
        text = re.sub(r'#{1,6}\s*', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _detect_table_need(self, query: str) -> bool:
        """Detect if query likely needs table results"""
        query_lower = query.lower()
        return any(term in query_lower for term in self.FINANCIAL_TERMS)

    def enhance_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Full enhancement pipeline: re-rank and add snippets

        Args:
            results: Raw search results
            query: User's search query

        Returns:
            Enhanced and re-ranked results with snippets
        """
        if not results:
            return results

        logger.info(f"Enhancing {len(results)} search results for query: '{query[:50]}...'")

        # Step 1: Re-rank
        ranked = self.rerank_results(results, query)

        # Step 2: Generate snippets
        for result in ranked:
            result['snippet'] = self.generate_snippet(result, query)

        logger.info(f"Enhancement complete. Top score: {ranked[0]['adjusted_score']:.3f}")

        return ranked
