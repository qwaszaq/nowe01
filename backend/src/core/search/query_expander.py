"""
Query Understanding & Expansion
Improves query interpretation through synonym expansion, term normalization, and temporal handling
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Expands and normalizes queries for better semantic search coverage

    Features:
    - Polish financial term synonyms
    - Financial concept normalization
    - Year range and quarter handling
    - Multi-term query expansion
    """

    # Polish financial synonyms (term → list of synonyms including the term itself)
    FINANCIAL_SYNONYMS = {
        # Revenue/Income
        'przychody': ['przychody', 'przychody ze sprzedaży', 'sprzedaż', 'revenue'],
        'sprzedaż': ['sprzedaż', 'przychody ze sprzedaży', 'przychody'],
        'przychody ze sprzedaży': ['przychody ze sprzedaży', 'przychody', 'sprzedaż'],

        # Receivables
        'należności': ['należności', 'należności handlowe', 'należności z tytułu dostaw', 'wierzytelności', 'receivables'],
        'należności handlowe': ['należności handlowe', 'należności', 'należności z tytułu dostaw i usług'],
        'wierzytelności': ['wierzytelności', 'należności', 'należności handlowe'],

        # Liabilities
        'zobowiązania': ['zobowiązania', 'zobowiązania handlowe', 'zobowiązania z tytułu dostaw', 'długi', 'liabilities'],
        'zobowiązania handlowe': ['zobowiązania handlowe', 'zobowiązania', 'zobowiązania z tytułu dostaw i usług'],
        'zobowiązania długoterminowe': ['zobowiązania długoterminowe', 'zobowiązania długookresowe', 'długi długoterminowe'],
        'zobowiązania krótkoterminowe': ['zobowiązania krótkoterminowe', 'zobowiązania krótkookresowe', 'bieżące zobowiązania'],
        'długi': ['długi', 'zobowiązania', 'zadłużenie', 'kredyty', 'pożyczki'],

        # Assets
        'aktywa': ['aktywa', 'majątek', 'assets'],
        'aktywa trwałe': ['aktywa trwałe', 'aktywa długoterminowe', 'aktywa niemobilne', 'środki trwałe'],
        'aktywa obrotowe': ['aktywa obrotowe', 'aktywa krótkoterminowe', 'aktywa bieżące'],
        'środki trwałe': ['środki trwałe', 'rzeczowe aktywa trwałe', 'aktywa trwałe', 'środki produkcji'],
        'zapasy': ['zapasy', 'stany magazynowe', 'inventory'],

        # Equity
        'kapitał': ['kapitał', 'kapitał własny', 'equity'],
        'kapitał własny': ['kapitał własny', 'kapitał', 'fundusze własne', 'equity'],
        'kapitał zakładowy': ['kapitał zakładowy', 'kapitał akcyjny', 'share capital'],

        # Profit/Loss
        'zysk': ['zysk', 'dochód', 'profit'],
        'zysk netto': ['zysk netto', 'zysk po opodatkowaniu', 'net profit', 'wynik netto'],
        'zysk brutto': ['zysk brutto', 'zysk przed opodatkowaniem', 'gross profit'],
        'zysk operacyjny': ['zysk operacyjny', 'wynik operacyjny', 'EBIT'],
        'strata': ['strata', 'loss', 'ujemny wynik'],
        'wynik': ['wynik', 'zysk', 'strata', 'wynik finansowy'],

        # Costs
        'koszty': ['koszty', 'wydatki', 'expenses', 'costs'],
        'koszty operacyjne': ['koszty operacyjne', 'koszty działalności operacyjnej'],

        # Cash flow
        'przepływy': ['przepływy pieniężne', 'cash flow', 'przepływy środków pieniężnych'],
        'przepływy pieniężne': ['przepływy pieniężne', 'cash flow', 'rachunek przepływów'],

        # Credits/Loans
        'kredyty': ['kredyty', 'pożyczki', 'zadłużenie', 'loans'],
        'pożyczki': ['pożyczki', 'kredyty', 'zadłużenie'],

        # Depreciation
        'amortyzacja': ['amortyzacja', 'depreciation', 'umorzenie'],

        # Investment
        'inwestycje': ['inwestycje', 'investments', 'lokaty'],
    }

    # Financial concept normalization (base form → expanded forms)
    CONCEPT_EXPANSION = {
        'zysk': ['zysk netto', 'zysk brutto', 'zysk operacyjny', 'wynik finansowy'],
        'przychody': ['przychody ze sprzedaży', 'pozostałe przychody', 'przychody operacyjne'],
        'koszty': ['koszty sprzedaży', 'koszty ogólnego zarządu', 'koszty operacyjne'],
        'zobowiązania': ['zobowiązania handlowe', 'zobowiązania finansowe', 'zobowiązania z tytułu kredytów'],
        'należności': ['należności handlowe', 'należności z tytułu dostaw i usług', 'pozostałe należności'],
        'aktywa': ['aktywa trwałe', 'aktywa obrotowe'],
    }

    # Quarter patterns
    QUARTER_MAP = {
        'Q1': ['styczeń', 'luty', 'marzec', 'I kwartał'],
        'Q2': ['kwiecień', 'maj', 'czerwiec', 'II kwartał'],
        'Q3': ['lipiec', 'sierpień', 'wrzesień', 'III kwartał'],
        'Q4': ['październik', 'listopad', 'grudzień', 'IV kwartał'],
    }

    # Year pattern
    YEAR_PATTERN = r'\b(20\d{2})\b'
    YEAR_RANGE_PATTERN = r'\b(20\d{2})\s*[-–—]\s*(20\d{2})\b'
    QUARTER_PATTERN = r'\b[QK][1-4]\s*(20\d{2})\b'

    def __init__(self):
        """Initialize query expander"""
        logger.info("QueryExpander initialized with Polish financial synonyms")

    def expand_query(self, query: str, expand_concepts: bool = True,
                     expand_temporal: bool = True) -> Dict[str, any]:
        """
        Expand query with synonyms and related terms

        Args:
            query: Original search query
            expand_concepts: Whether to expand financial concepts
            expand_temporal: Whether to expand temporal terms

        Returns:
            Dict with:
                - original: Original query
                - expanded: List of expanded query variants
                - temporal_context: Extracted years/quarters
                - detected_concepts: Financial concepts found
        """
        query_lower = query.lower()

        result = {
            'original': query,
            'expanded': [query],  # Always include original
            'temporal_context': [],
            'detected_concepts': []
        }

        # Extract temporal context
        if expand_temporal:
            temporal = self._extract_temporal_context(query)
            result['temporal_context'] = temporal['years']

            # Add temporal expansions
            if temporal['expansions']:
                result['expanded'].extend(temporal['expansions'])

        # Expand financial terms with synonyms
        expanded_queries = self._expand_with_synonyms(query_lower)
        result['expanded'].extend(expanded_queries)

        # Expand financial concepts (e.g., "zysk" → "zysk netto", "zysk brutto")
        if expand_concepts:
            concept_queries = self._expand_concepts(query_lower)
            result['expanded'].extend(concept_queries)
            result['detected_concepts'] = self._detect_concepts(query_lower)

        # Remove duplicates while preserving order
        seen = set()
        unique_expanded = []
        for q in result['expanded']:
            if q not in seen:
                seen.add(q)
                unique_expanded.append(q)

        result['expanded'] = unique_expanded

        logger.info(f"Query expansion: '{query}' → {len(result['expanded'])} variants, "
                   f"{len(result['temporal_context'])} temporal, "
                   f"{len(result['detected_concepts'])} concepts")

        return result

    def _expand_with_synonyms(self, query: str) -> List[str]:
        """Expand query by replacing terms with their synonyms"""
        expanded = []

        # Find all financial terms in the query
        found_terms = []
        for term, synonyms in self.FINANCIAL_SYNONYMS.items():
            if term in query:
                found_terms.append((term, synonyms))

        # If no terms found, return empty
        if not found_terms:
            return expanded

        # Generate variants by replacing each term with its synonyms
        for term, synonyms in found_terms:
            for synonym in synonyms:
                if synonym != term:  # Don't add the same query
                    variant = query.replace(term, synonym)
                    if variant != query:
                        expanded.append(variant)

        return expanded[:5]  # Limit to top 5 synonym variants

    def _expand_concepts(self, query: str) -> List[str]:
        """Expand financial concepts to their specific forms"""
        expanded = []

        for base_concept, specific_forms in self.CONCEPT_EXPANSION.items():
            # Check if base concept appears as standalone word
            pattern = r'\b' + re.escape(base_concept) + r'\b'
            if re.search(pattern, query):
                # Create variants with specific forms
                for specific in specific_forms:
                    variant = re.sub(pattern, specific, query)
                    if variant != query:
                        expanded.append(variant)

        return expanded[:3]  # Limit to top 3 concept expansions

    def _extract_temporal_context(self, query: str) -> Dict[str, any]:
        """
        Extract temporal context (years, quarters, ranges)

        Returns:
            Dict with:
                - years: List of years found
                - quarters: List of quarters found
                - expansions: Additional query variants with temporal expansions
        """
        result = {
            'years': [],
            'quarters': [],
            'expansions': []
        }

        # Extract year ranges (e.g., "2023-2024")
        year_ranges = re.findall(self.YEAR_RANGE_PATTERN, query)
        if year_ranges:
            for start_year, end_year in year_ranges:
                start = int(start_year)
                end = int(end_year)
                # Add all years in range
                for year in range(start, end + 1):
                    result['years'].append(str(year))

                # Create separate queries for each year in range
                for year in range(start, end + 1):
                    variant = re.sub(self.YEAR_RANGE_PATTERN, str(year), query)
                    result['expansions'].append(variant)

        # Extract standalone years
        standalone_years = re.findall(self.YEAR_PATTERN, query)
        for year in standalone_years:
            if year not in result['years']:
                result['years'].append(year)

        # Extract quarters (e.g., "Q4 2024")
        quarters = re.findall(self.QUARTER_PATTERN, query, re.IGNORECASE)
        if quarters:
            for quarter_match in quarters:
                quarter = quarter_match[0].upper()
                year = quarter_match[1] if len(quarter_match) > 1 else None

                # Add quarter terms as expansion
                if quarter in self.QUARTER_MAP:
                    quarter_terms = self.QUARTER_MAP[quarter]
                    for term in quarter_terms:
                        if year:
                            result['expansions'].append(f"{term} {year}")
                        else:
                            result['expansions'].append(term)

                    result['quarters'].append(f"{quarter} {year}" if year else quarter)

        return result

    def _detect_concepts(self, query: str) -> List[str]:
        """Detect financial concepts present in query"""
        concepts = []

        for concept in self.CONCEPT_EXPANSION.keys():
            pattern = r'\b' + re.escape(concept) + r'\b'
            if re.search(pattern, query):
                concepts.append(concept)

        return concepts

    def get_search_boost_hints(self, expansion_result: Dict) -> Dict[str, float]:
        """
        Provide boost hints based on query expansion analysis

        Args:
            expansion_result: Result from expand_query()

        Returns:
            Dict of hints for search re-ranking:
                - has_temporal: Whether query has temporal context
                - concept_specificity: How specific the concept is (0.0-1.0)
                - suggested_boost: Suggested boost multiplier
        """
        hints = {
            'has_temporal': len(expansion_result['temporal_context']) > 0,
            'concept_specificity': 0.5,  # Default
            'suggested_boost': 1.0
        }

        # Increase specificity if query has multiple concepts
        if len(expansion_result['detected_concepts']) >= 2:
            hints['concept_specificity'] = 0.8
            hints['suggested_boost'] = 1.1

        # Increase boost if temporal context is specific
        if len(expansion_result['temporal_context']) == 1:
            hints['suggested_boost'] *= 1.05

        return hints


def combine_expanded_queries(expanded_queries: List[str], max_length: int = 500) -> str:
    """
    Combine multiple expanded queries into a single search string
    Useful for multi-vector search or query augmentation

    Args:
        expanded_queries: List of query variants
        max_length: Maximum combined length

    Returns:
        Combined query string
    """
    if not expanded_queries:
        return ""

    # Start with original (first query)
    combined = expanded_queries[0]

    # Add variants until max length
    for variant in expanded_queries[1:]:
        test_combined = f"{combined} {variant}"
        if len(test_combined) <= max_length:
            combined = test_combined
        else:
            break

    return combined
