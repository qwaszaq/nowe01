"""
Multi-Document Intelligence Module (Phase 4)

Enables temporal comparisons, trend analysis, and cross-document queries
for financial document analysis.

Author: Claude Code
Date: 2025-11-12
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ComparisonType(Enum):
    """Types of multi-document comparisons"""
    TEMPORAL = "temporal"  # Compare across specific years
    TREND = "trend"  # Analyze trends over time
    MULTI_YEAR = "multi_year"  # Query across all years
    AUTO = "auto"  # Auto-detect based on query


@dataclass
class ComparisonResult:
    """Result of a multi-document comparison"""
    query: str
    comparison_type: ComparisonType
    years_detected: List[str]
    metric_detected: Optional[str]
    results_by_year: Dict[str, List[Dict]]
    comparison_summary: Optional[Dict] = None


class MultiDocumentIntelligence:
    """
    Provides multi-document intelligence capabilities for financial analysis.

    Features:
    - Temporal comparison (2023 vs 2024)
    - Trend analysis (2022-2024)
    - Cross-document aggregation
    - Automatic year detection
    """

    # Comparison keywords (Polish)
    COMPARISON_KEYWORDS = [
        'porównaj', 'porównanie', 'vs', 'versus', 'kontra',
        'różnica', 'zmiana', 'change', 'compare', 'comparison'
    ]

    # Trend keywords (Polish)
    TREND_KEYWORDS = [
        'trend', 'trendy', 'wzrost', 'spadek', 'zmiana',
        'rozwój', 'ewolucja', 'history', 'historia'
    ]

    def __init__(self):
        """Initialize multi-document intelligence module"""
        logger.info("MultiDocumentIntelligence initialized")

    def detect_comparison_intent(self, query: str) -> ComparisonType:
        """
        Detect if query is asking for comparison, trend, or multi-year analysis

        Args:
            query: User query string

        Returns:
            ComparisonType enum value
        """
        query_lower = query.lower()

        # Check for comparison keywords
        has_comparison = any(kw in query_lower for kw in self.COMPARISON_KEYWORDS)

        # Check for trend keywords
        has_trend = any(kw in query_lower for kw in self.TREND_KEYWORDS)

        # Check for year ranges (2022-2024, 2022 do 2024)
        has_year_range = bool(re.search(r'20\d{2}\s*[-–do]\s*20\d{2}', query))

        if has_comparison:
            return ComparisonType.TEMPORAL
        elif has_trend or has_year_range:
            return ComparisonType.TREND
        else:
            return ComparisonType.AUTO

    def extract_years(self, query: str) -> List[str]:
        """
        Extract year values from query

        Args:
            query: User query string

        Returns:
            List of year strings (e.g., ["2023", "2024"])

        Examples:
            "przychody 2023 vs 2024" → ["2023", "2024"]
            "trend 2022-2024" → ["2022", "2023", "2024"]
            "dane za 2023" → ["2023"]
        """
        years = []

        # Extract explicit years (20XX)
        explicit_years = re.findall(r'\b(20\d{2})\b', query)
        years.extend(explicit_years)

        # Check for year ranges (2022-2024)
        range_match = re.search(r'(20\d{2})\s*[-–do]\s*(20\d{2})', query)
        if range_match:
            start_year = int(range_match.group(1))
            end_year = int(range_match.group(2))

            # Generate all years in range
            years = [str(year) for year in range(start_year, end_year + 1)]

        # Deduplicate while preserving order
        seen = set()
        unique_years = []
        for year in years:
            if year not in seen:
                seen.add(year)
                unique_years.append(year)

        # Sort years chronologically
        unique_years.sort()

        logger.debug(f"Extracted years from query: {unique_years}")
        return unique_years

    def extract_metric(self, query: str) -> Optional[str]:
        """
        Extract financial metric being queried

        Args:
            query: User query string

        Returns:
            Detected metric or None

        Examples:
            "przychody 2023" → "przychody"
            "zysk netto vs 2024" → "zysk netto"
        """
        # Common financial metrics (Polish)
        metrics = [
            'przychody ze sprzedaży', 'przychody', 'sprzedaż',
            'zysk netto', 'zysk brutto', 'zysk operacyjny', 'zysk',
            'należności handlowe', 'należności',
            'zobowiązania długoterminowe', 'zobowiązania',
            'aktywa trwałe', 'aktywa',
            'kapitał własny', 'kapitał',
            'środki trwałe', 'środki pieniężne',
            'zadłużenie', 'długi'
        ]

        query_lower = query.lower()

        # Find longest matching metric
        found_metric = None
        max_length = 0

        for metric in metrics:
            if metric in query_lower and len(metric) > max_length:
                found_metric = metric
                max_length = len(metric)

        logger.debug(f"Extracted metric from query: {found_metric}")
        return found_metric

    async def compare_temporal(
        self,
        query: str,
        case_id: str,
        years: List[str],
        search_function: Any,
        limit: int = 5
    ) -> ComparisonResult:
        """
        Perform temporal comparison across specified years

        Args:
            query: Base query (e.g., "przychody ze sprzedaży")
            case_id: Case UUID
            years: List of years to compare
            search_function: Async function to perform semantic search
            limit: Results per year

        Returns:
            ComparisonResult with results grouped by year
        """
        logger.info(f"Performing temporal comparison for query: {query}, years: {years}")

        results_by_year = {}

        # Run search for each year
        for year in years:
            # Construct year-specific query
            year_query = f"{query} {year}"

            logger.debug(f"Searching for year {year}: {year_query}")

            # Perform semantic search with year filter
            try:
                search_results = await search_function(
                    case_id=case_id,
                    query=year_query,
                    years=[year],  # Phase 6 filter
                    limit=limit
                )

                results_by_year[year] = search_results

                logger.debug(f"Found {len(search_results)} results for year {year}")

            except Exception as e:
                logger.error(f"Error searching for year {year}: {e}")
                results_by_year[year] = []

        # Extract detected metric
        metric = self.extract_metric(query)

        return ComparisonResult(
            query=query,
            comparison_type=ComparisonType.TEMPORAL,
            years_detected=years,
            metric_detected=metric,
            results_by_year=results_by_year
        )

    def analyze_trend(
        self,
        results_by_year: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """
        Analyze trend from multi-year results

        Args:
            results_by_year: Results grouped by year

        Returns:
            Trend analysis dict with direction, insights, etc.
        """
        logger.debug("Analyzing trend from multi-year results")

        # Basic trend detection based on result count and scores
        years = sorted(results_by_year.keys())

        if len(years) < 2:
            return {
                "trend_direction": "insufficient_data",
                "insight": "Not enough years to determine trend"
            }

        # Calculate average scores by year
        avg_scores_by_year = {}
        for year, results in results_by_year.items():
            if results:
                scores = [r.get("adjusted_score", r.get("score", 0)) for r in results]
                avg_scores_by_year[year] = sum(scores) / len(scores) if scores else 0
            else:
                avg_scores_by_year[year] = 0

        # Determine trend direction
        first_year_score = avg_scores_by_year.get(years[0], 0)
        last_year_score = avg_scores_by_year.get(years[-1], 0)

        if last_year_score > first_year_score * 1.1:
            trend_direction = "increasing"
            insight = "Data availability/relevance increasing over time"
        elif last_year_score < first_year_score * 0.9:
            trend_direction = "decreasing"
            insight = "Data availability/relevance decreasing over time"
        else:
            trend_direction = "stable"
            insight = "Relatively stable data availability across years"

        return {
            "trend_direction": trend_direction,
            "insight": insight,
            "years_analyzed": years,
            "avg_scores_by_year": avg_scores_by_year
        }

    def format_comparison_response(
        self,
        comparison_result: ComparisonResult,
        include_trend_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Format comparison result for API response

        Args:
            comparison_result: ComparisonResult object
            include_trend_analysis: Whether to include trend analysis

        Returns:
            Formatted dict for API response
        """
        response = {
            "query": comparison_result.query,
            "comparison_type": comparison_result.comparison_type.value,
            "years_detected": comparison_result.years_detected,
            "metric_detected": comparison_result.metric_detected,
            "results_by_year": {}
        }

        # Format results by year
        for year, results in comparison_result.results_by_year.items():
            response["results_by_year"][year] = [
                {
                    "score": r.get("adjusted_score", r.get("score", 0)),
                    "page": r.get("page_num"),
                    "document": r.get("document_name", "Unknown"),
                    "text_preview": r.get("text", "")[:200] + "...",
                    "chunk_type": r.get("chunk_type", "text"),
                    "temporal_context": r.get("temporal_context", [])
                }
                for r in results
            ]

        # Add trend analysis if requested
        if include_trend_analysis:
            trend_analysis = self.analyze_trend(comparison_result.results_by_year)
            response["trend_analysis"] = trend_analysis

        # Add comparison summary
        response["comparison_summary"] = {
            "total_years": len(comparison_result.years_detected),
            "results_per_year": {
                year: len(results)
                for year, results in comparison_result.results_by_year.items()
            },
            "coverage": "complete" if all(
                len(results) > 0 for results in comparison_result.results_by_year.values()
            ) else "partial"
        }

        return response
