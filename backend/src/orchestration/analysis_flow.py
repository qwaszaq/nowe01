"""
Analysis Flow Orchestration Layer
Coordinates semantic search, financial calculators, micro-agents, and storage
for comprehensive document financial analysis
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, asdict
from datetime import datetime

from src.core.search.semantic_search import SemanticSearch
from src.core.llm.micro_agents import MicroAgents
from src.core.calculators import (
    # Liquidity (5 ratios)
    calculate_current_ratio,
    calculate_quick_ratio,
    calculate_cash_ratio,
    calculate_operating_cash_flow_ratio,
    calculate_defensive_interval_ratio,
    # Profitability (8 ratios)
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roa,
    calculate_roe,
    calculate_roic,
    calculate_eps,
    calculate_asset_turnover,
    # Leverage (6 ratios)
    calculate_debt_to_equity,
    calculate_debt_to_assets,
    calculate_interest_coverage,
    calculate_debt_service_coverage,
    calculate_equity_multiplier,
    calculate_financial_leverage,
)
from src.storage.postgres_store import PostgresStore
from src.storage.redis_store import RedisStore

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SearchResult:
    """Individual search result with context"""
    chunk_id: str
    document_id: UUID
    case_id: UUID
    page_num: int
    text: str
    score: float
    char_count: int
    chunk_idx: Optional[int] = None
    context: Optional[Dict[str, List[Dict]]] = None


@dataclass
class MetricResult:
    """Individual financial metric calculation result"""
    metric_name: str
    metric_value: Optional[float]
    metric_unit: Optional[str]
    interpretation: str
    citation_data: Dict[str, Any]
    classification: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class MetricsResult:
    """Collection of calculated metrics"""
    liquidity_ratios: List[MetricResult]
    profitability_ratios: List[MetricResult]
    leverage_ratios: List[MetricResult]
    total_calculated: int
    total_failed: int
    calculation_time_ms: float


@dataclass
class InsightsResult:
    """Aggregated insights from micro-agent classifications"""
    risk_assessment: str
    liquidity_position: str
    profitability_trends: str
    leverage_analysis: str
    overall_health: str
    key_concerns: List[str]
    key_strengths: List[str]
    classification_count: int


@dataclass
class AnalysisResult:
    """Complete analysis result with all components"""
    document_id: UUID
    analysis_type: str
    metrics: MetricsResult
    insights: InsightsResult
    citations: List[Dict[str, Any]]
    financial_data_extracted: Dict[str, Any]
    quality_score: float
    timestamp: datetime
    cached: bool = False


# ============================================================================
# ANALYSIS FLOW ORCHESTRATOR
# ============================================================================

class AnalysisFlow:
    """
    Orchestrates comprehensive financial analysis workflow

    Coordinates:
    - SemanticSearch for data extraction
    - Financial calculators for ratio computation
    - Micro-agents for classification and insights
    - PostgresStore for persistence
    - RedisStore for caching

    Supports multiple analysis types:
    - comprehensive: All 19 ratios + all micro-agents
    - liquidity: 5 liquidity ratios only
    - profitability: 8 profitability ratios only
    - leverage: 6 leverage ratios only
    - quick: Key ratios (current, ROE, debt-to-equity)
    """

    # Cache TTL configuration
    CACHE_TTL_SECONDS = 3600  # 1 hour

    # Analysis type definitions
    ANALYSIS_TYPES = {
        'comprehensive': {
            'liquidity': True,
            'profitability': True,
            'leverage': True,
            'micro_agents': True,
        },
        'liquidity': {
            'liquidity': True,
            'profitability': False,
            'leverage': False,
            'micro_agents': False,
        },
        'profitability': {
            'liquidity': False,
            'profitability': True,
            'leverage': False,
            'micro_agents': False,
        },
        'leverage': {
            'liquidity': False,
            'profitability': False,
            'leverage': True,
            'micro_agents': False,
        },
        'quick': {
            'liquidity': ['current_ratio'],
            'profitability': ['roe'],
            'leverage': ['debt_to_equity'],
            'micro_agents': False,
        }
    }

    def __init__(
        self,
        semantic_search: SemanticSearch,
        micro_agents: MicroAgents,
        postgres_store: PostgresStore,
        redis_store: RedisStore
    ):
        """
        Initialize analysis flow orchestrator

        Args:
            semantic_search: SemanticSearch instance
            micro_agents: MicroAgents instance
            postgres_store: PostgresStore instance
            redis_store: RedisStore instance
        """
        self.search = semantic_search
        self.agents = micro_agents
        self.postgres = postgres_store
        self.redis = redis_store

        logger.info("AnalysisFlow orchestrator initialized")

    async def analyze_document(
        self,
        document_id: UUID,
        analysis_type: str = "comprehensive"
    ) -> AnalysisResult:
        """
        Perform comprehensive financial analysis on document

        Workflow:
        1. Check cache for existing results
        2. Query document for financial data (semantic search)
        3. Extract financial statement values from search results
        4. Calculate applicable ratios based on analysis_type
        5. Run micro-agent classifications (if enabled)
        6. Store metrics in PostgresStore with citations
        7. Cache results in Redis
        8. Return AnalysisResult

        Args:
            document_id: Document UUID to analyze
            analysis_type: Type of analysis ("comprehensive", "liquidity", etc.)

        Returns:
            AnalysisResult with all metrics, insights, and citations

        Raises:
            ValueError: If analysis_type is invalid
            Exception: If critical workflow step fails

        Example:
            >>> result = await flow.analyze_document(
            ...     document_id=UUID("123..."),
            ...     analysis_type="comprehensive"
            ... )
            >>> print(f"Calculated {result.metrics.total_calculated} ratios")
            >>> print(f"Risk assessment: {result.insights.risk_assessment}")
        """
        start_time = datetime.now()

        # Validate analysis type
        if analysis_type not in self.ANALYSIS_TYPES:
            raise ValueError(
                f"Invalid analysis_type: {analysis_type}. "
                f"Must be one of: {list(self.ANALYSIS_TYPES.keys())}"
            )

        logger.info(f"Starting {analysis_type} analysis for document {document_id}")

        # Step 1: Check cache
        cache_key = f"analysis:{document_id}:{analysis_type}"
        cached_result = self.redis.get(cache_key)

        if cached_result:
            logger.info(f"Cache HIT for {cache_key}")
            result_dict = json.loads(cached_result)
            result_dict['cached'] = True
            # Reconstruct dataclass from dict
            return self._reconstruct_analysis_result(result_dict)

        logger.info(f"Cache MISS for {cache_key} - performing analysis")

        try:
            # Step 2: Query for financial data
            financial_data = await self._extract_financial_data(document_id)

            # Step 3: Calculate ratios based on analysis type
            metrics = await self._calculate_metrics(
                document_id=document_id,
                financial_data=financial_data,
                analysis_type=analysis_type
            )

            # Step 4: Generate insights (if micro-agents enabled)
            insights = await self._generate_insights(
                metrics=metrics,
                analysis_type=analysis_type
            )

            # Step 5: Collect all citations
            citations = self._collect_citations(metrics)

            # Step 6: Calculate quality score
            quality_score = self._calculate_quality_score(
                metrics=metrics,
                financial_data=financial_data
            )

            # Step 7: Store metrics in Postgres
            await self._store_metrics(document_id, metrics)

            # Step 8: Build result
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000

            result = AnalysisResult(
                document_id=document_id,
                analysis_type=analysis_type,
                metrics=metrics,
                insights=insights,
                citations=citations,
                financial_data_extracted=financial_data,
                quality_score=quality_score,
                timestamp=datetime.now(),
                cached=False
            )

            # Step 9: Cache result
            self._cache_result(cache_key, result)

            logger.info(
                f"Analysis complete: {metrics.total_calculated} ratios calculated "
                f"in {calculation_time:.0f}ms (quality: {quality_score:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"Analysis failed for document {document_id}: {e}", exc_info=True)
            raise

    async def query_case(
        self,
        case_id: UUID,
        query: str,
        context_window: int = 1
    ) -> List[SearchResult]:
        """
        Semantic search across all documents in a case

        Args:
            case_id: Case UUID to search
            query: Natural language search query
            context_window: Number of chunks before/after to include

        Returns:
            List of SearchResult objects with ranked results and context

        Example:
            >>> results = await flow.query_case(
            ...     case_id=UUID("abc..."),
            ...     query="What is the company's revenue growth?",
            ...     context_window=2
            ... )
            >>> for r in results[:3]:
            ...     print(f"Page {r.page_num}: {r.text[:100]}... (score: {r.score})")
        """
        logger.info(f"Querying case {case_id} with: '{query[:50]}...'")

        try:
            # Perform semantic search with context
            # Use lower threshold (0.3) and get more results (20) for re-ranking
            if context_window > 0:
                raw_results = await self.search.search_with_context(
                    query=query,
                    case_id=case_id,
                    window_size=context_window,
                    limit=20,
                    score_threshold=0.3
                )
            else:
                raw_results = await self.search.search(
                    query=query,
                    case_id=case_id,
                    limit=20,
                    score_threshold=0.3
                )

            # Convert to SearchResult dataclass
            # Include metadata fields for result enhancement
            results = []
            for r in raw_results:
                result = SearchResult(
                    chunk_id=r['chunk_id'],
                    document_id=r['document_id'],
                    case_id=r['case_id'],
                    page_num=r['page_num'],
                    text=r['text'],
                    score=r['score'],
                    char_count=r['char_count'],
                    chunk_idx=r.get('chunk_idx'),
                    context=r.get('context')
                )
                # Add metadata as dynamic attributes for enhancer
                result.chunk_type = r.get('chunk_type', 'text')
                result.temporal_context = r.get('temporal_context', [])
                results.append(result)

            logger.info(f"Found {len(results)} results for case query")
            return results

        except Exception as e:
            logger.error(f"Case query failed: {e}", exc_info=True)
            raise

    async def calculate_metrics_from_data(
        self,
        financial_data: Dict[str, Any]
    ) -> MetricsResult:
        """
        Calculate all applicable ratios from extracted financial data

        Takes pre-extracted financial statement values and computes
        all ratios where sufficient data is available.

        Args:
            financial_data: Dictionary with financial statement values:
                {
                    'current_assets': float,
                    'current_liabilities': float,
                    'total_assets': float,
                    'total_debt': float,
                    'revenue': float,
                    'net_income': float,
                    ... (see _extract_financial_data for full schema)
                }

        Returns:
            MetricsResult with all calculated ratios and interpretations

        Example:
            >>> data = {
            ...     'current_assets': 500000,
            ...     'current_liabilities': 300000,
            ...     'revenue': 1000000,
            ...     'net_income': 150000
            ... }
            >>> metrics = await flow.calculate_metrics_from_data(data)
            >>> print(f"Current Ratio: {metrics.liquidity_ratios[0].metric_value}")
        """
        logger.info("Calculating metrics from provided financial data")

        start_time = datetime.now()

        try:
            # Calculate all ratio categories
            liquidity = await self._calculate_liquidity_ratios(financial_data, None)
            profitability = await self._calculate_profitability_ratios(financial_data, None)
            leverage = await self._calculate_leverage_ratios(financial_data, None)

            total_calculated = (
                len([r for r in liquidity if r.metric_value is not None]) +
                len([r for r in profitability if r.metric_value is not None]) +
                len([r for r in leverage if r.metric_value is not None])
            )

            total_failed = (
                len([r for r in liquidity if r.metric_value is None]) +
                len([r for r in profitability if r.metric_value is None]) +
                len([r for r in leverage if r.metric_value is None])
            )

            calculation_time = (datetime.now() - start_time).total_seconds() * 1000

            result = MetricsResult(
                liquidity_ratios=liquidity,
                profitability_ratios=profitability,
                leverage_ratios=leverage,
                total_calculated=total_calculated,
                total_failed=total_failed,
                calculation_time_ms=calculation_time
            )

            logger.info(
                f"Calculated {total_calculated} ratios ({total_failed} failed) "
                f"in {calculation_time:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Metric calculation failed: {e}", exc_info=True)
            raise

    async def generate_insights(
        self,
        document_id: UUID
    ) -> InsightsResult:
        """
        Run micro-agent classifiers on calculated metrics

        Retrieves stored metrics for document and generates
        insights using micro-agent classifications.

        Args:
            document_id: Document UUID to analyze

        Returns:
            InsightsResult with risk assessment, liquidity position,
            profitability trends, and aggregated insights

        Example:
            >>> insights = await flow.generate_insights(UUID("123..."))
            >>> print(insights.risk_assessment)
            'low'
            >>> print(insights.key_concerns)
            ['High leverage ratio exceeds industry benchmarks']
        """
        logger.info(f"Generating insights for document {document_id}")

        try:
            # Retrieve metrics from Postgres
            stored_metrics = self.postgres.get_metrics(document_id)

            if not stored_metrics:
                logger.warning(f"No metrics found for document {document_id}")
                return self._empty_insights()

            # Convert to dict for easier lookup
            metrics_dict = {m['metric_name']: m['metric_value'] for m in stored_metrics}

            # Run micro-agent classifications
            classifications = []

            # Liquidity classification
            if 'current_ratio' in metrics_dict and 'quick_ratio' in metrics_dict:
                liquidity_class = await self.agents.classify_liquidity(
                    current_ratio=metrics_dict['current_ratio'],
                    quick_ratio=metrics_dict['quick_ratio']
                )
                classifications.append(('liquidity', liquidity_class))
            else:
                liquidity_class = "insufficient_data"

            # Debt level classification
            if 'debt_to_equity' in metrics_dict:
                debt_class = await self.agents.classify_debt_level(
                    debt_ratio=metrics_dict['debt_to_equity']
                )
                classifications.append(('debt', debt_class))
            else:
                debt_class = "insufficient_data"

            # Profitability trend (needs time series - placeholder)
            profit_trend = "stable"  # Would need historical data

            # Risk assessment
            if all(k in metrics_dict for k in ['debt_to_equity', 'current_ratio', 'net_margin']):
                risk_level = await self.agents.assess_risk(
                    debt=metrics_dict['debt_to_equity'],
                    liquidity=metrics_dict['current_ratio'],
                    profit=metrics_dict.get('net_margin', 0)
                )
                classifications.append(('risk', risk_level))
            else:
                risk_level = "insufficient_data"

            # Aggregate concerns and strengths
            concerns = self._identify_concerns(metrics_dict)
            strengths = self._identify_strengths(metrics_dict)

            # Overall health assessment
            overall_health = self._assess_overall_health(
                risk_level, liquidity_class, debt_class
            )

            result = InsightsResult(
                risk_assessment=risk_level,
                liquidity_position=liquidity_class,
                profitability_trends=profit_trend,
                leverage_analysis=debt_class,
                overall_health=overall_health,
                key_concerns=concerns,
                key_strengths=strengths,
                classification_count=len(classifications)
            )

            logger.info(
                f"Generated insights: {len(classifications)} classifications, "
                f"health={overall_health}"
            )

            return result

        except Exception as e:
            logger.error(f"Insight generation failed: {e}", exc_info=True)
            # Return degraded result instead of failing
            return self._empty_insights()

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _extract_financial_data(self, document_id: UUID) -> Dict[str, Any]:
        """
        Extract financial statement values using semantic search

        Queries document for key financial metrics and extracts values
        from search results.
        """
        logger.info(f"Extracting financial data from document {document_id}")

        # Define search queries for financial data
        queries = {
            'current_assets': "What are the current assets?",
            'current_liabilities': "What are the current liabilities?",
            'total_assets': "What are the total assets?",
            'total_equity': "What is the shareholders' equity or total equity?",
            'total_debt': "What is the total debt or long-term debt?",
            'revenue': "What is the total revenue or net sales?",
            'gross_profit': "What is the gross profit?",
            'operating_income': "What is the operating income or EBIT?",
            'net_income': "What is the net income or net profit?",
            'cash': "What is the cash and cash equivalents?",
            'inventory': "What is the inventory value?",
            'operating_cash_flow': "What is the operating cash flow?",
        }

        extracted_data = {}

        # Search for each financial metric
        for field, query in queries.items():
            try:
                results = await self.search.search(
                    query=query,
                    document_id=document_id,
                    limit=3,
                    score_threshold=0.7
                )

                if results:
                    # Extract numeric value from top result
                    # This is simplified - production would use NER or regex
                    value = self._extract_numeric_value(results[0]['text'])
                    if value is not None:
                        extracted_data[field] = value
                        logger.debug(f"Extracted {field}: {value}")

            except Exception as e:
                logger.warning(f"Failed to extract {field}: {e}")
                continue

        logger.info(f"Extracted {len(extracted_data)} financial data points")
        return extracted_data

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extract numeric value from text

        Simplified implementation - production would use NER or LLM
        """
        import re

        # Look for patterns like "$1,234,567" or "1,234.56"
        pattern = r'\$?([\d,]+\.?\d*)'
        matches = re.findall(pattern, text)

        if matches:
            try:
                # Take first match, remove commas, convert to float
                value_str = matches[0].replace(',', '')
                return float(value_str)
            except ValueError:
                return None

        return None

    async def _calculate_metrics(
        self,
        document_id: UUID,
        financial_data: Dict[str, Any],
        analysis_type: str
    ) -> MetricsResult:
        """Calculate metrics based on analysis type configuration"""
        start_time = datetime.now()

        config = self.ANALYSIS_TYPES[analysis_type]

        liquidity = []
        profitability = []
        leverage = []

        # Calculate liquidity ratios
        if config.get('liquidity'):
            if isinstance(config['liquidity'], list):
                # Specific ratios only
                liquidity = await self._calculate_specific_liquidity(
                    financial_data, document_id, config['liquidity']
                )
            else:
                # All liquidity ratios
                liquidity = await self._calculate_liquidity_ratios(
                    financial_data, document_id
                )

        # Calculate profitability ratios
        if config.get('profitability'):
            if isinstance(config['profitability'], list):
                profitability = await self._calculate_specific_profitability(
                    financial_data, document_id, config['profitability']
                )
            else:
                profitability = await self._calculate_profitability_ratios(
                    financial_data, document_id
                )

        # Calculate leverage ratios
        if config.get('leverage'):
            if isinstance(config['leverage'], list):
                leverage = await self._calculate_specific_leverage(
                    financial_data, document_id, config['leverage']
                )
            else:
                leverage = await self._calculate_leverage_ratios(
                    financial_data, document_id
                )

        total_calculated = (
            len([r for r in liquidity if r.metric_value is not None]) +
            len([r for r in profitability if r.metric_value is not None]) +
            len([r for r in leverage if r.metric_value is not None])
        )

        total_failed = (
            len([r for r in liquidity if r.metric_value is None]) +
            len([r for r in profitability if r.metric_value is None]) +
            len([r for r in leverage if r.metric_value is None])
        )

        calculation_time = (datetime.now() - start_time).total_seconds() * 1000

        return MetricsResult(
            liquidity_ratios=liquidity,
            profitability_ratios=profitability,
            leverage_ratios=leverage,
            total_calculated=total_calculated,
            total_failed=total_failed,
            calculation_time_ms=calculation_time
        )

    async def _calculate_liquidity_ratios(
        self,
        data: Dict[str, Any],
        document_id: Optional[UUID]
    ) -> List[MetricResult]:
        """Calculate all 5 liquidity ratios"""
        results = []
        doc_id_str = str(document_id) if document_id else None

        # Current Ratio
        if 'current_assets' in data and 'current_liabilities' in data:
            value, interp, citation = calculate_current_ratio(
                current_assets=data['current_assets'],
                current_liabilities=data['current_liabilities'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='current_ratio',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        # Quick Ratio
        if all(k in data for k in ['current_assets', 'inventory', 'current_liabilities']):
            value, interp, citation = calculate_quick_ratio(
                current_assets=data['current_assets'],
                inventory=data['inventory'],
                current_liabilities=data['current_liabilities'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='quick_ratio',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        # Cash Ratio
        if 'cash' in data and 'current_liabilities' in data:
            value, interp, citation = calculate_cash_ratio(
                cash_and_equivalents=data['cash'],
                current_liabilities=data['current_liabilities'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='cash_ratio',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        # Operating Cash Flow Ratio
        if 'operating_cash_flow' in data and 'current_liabilities' in data:
            value, interp, citation = calculate_operating_cash_flow_ratio(
                operating_cash_flow=data['operating_cash_flow'],
                current_liabilities=data['current_liabilities'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='operating_cash_flow_ratio',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        return results

    async def _calculate_profitability_ratios(
        self,
        data: Dict[str, Any],
        document_id: Optional[UUID]
    ) -> List[MetricResult]:
        """Calculate all 8 profitability ratios"""
        results = []
        doc_id_str = str(document_id) if document_id else None

        # Gross Margin
        if 'gross_profit' in data and 'revenue' in data:
            value, interp, citation = calculate_gross_margin(
                gross_profit=data['gross_profit'],
                revenue=data['revenue'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='gross_margin',
                metric_value=value,
                metric_unit='percent',
                interpretation=interp,
                citation_data=citation
            ))

        # Operating Margin
        if 'operating_income' in data and 'revenue' in data:
            value, interp, citation = calculate_operating_margin(
                operating_income=data['operating_income'],
                revenue=data['revenue'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='operating_margin',
                metric_value=value,
                metric_unit='percent',
                interpretation=interp,
                citation_data=citation
            ))

        # Net Margin
        if 'net_income' in data and 'revenue' in data:
            value, interp, citation = calculate_net_margin(
                net_income=data['net_income'],
                revenue=data['revenue'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='net_margin',
                metric_value=value,
                metric_unit='percent',
                interpretation=interp,
                citation_data=citation
            ))

        # ROA
        if 'net_income' in data and 'total_assets' in data:
            value, interp, citation = calculate_roa(
                net_income=data['net_income'],
                total_assets=data['total_assets'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='roa',
                metric_value=value,
                metric_unit='percent',
                interpretation=interp,
                citation_data=citation
            ))

        # ROE
        if 'net_income' in data and 'total_equity' in data:
            value, interp, citation = calculate_roe(
                net_income=data['net_income'],
                shareholders_equity=data['total_equity'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='roe',
                metric_value=value,
                metric_unit='percent',
                interpretation=interp,
                citation_data=citation
            ))

        # Asset Turnover
        if 'revenue' in data and 'total_assets' in data:
            value, interp, citation = calculate_asset_turnover(
                revenue=data['revenue'],
                total_assets=data['total_assets'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='asset_turnover',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        return results

    async def _calculate_leverage_ratios(
        self,
        data: Dict[str, Any],
        document_id: Optional[UUID]
    ) -> List[MetricResult]:
        """Calculate all 6 leverage ratios"""
        results = []
        doc_id_str = str(document_id) if document_id else None

        # Debt-to-Equity
        if 'total_debt' in data and 'total_equity' in data:
            value, interp, citation = calculate_debt_to_equity(
                total_debt=data['total_debt'],
                total_equity=data['total_equity'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='debt_to_equity',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        # Debt-to-Assets
        if 'total_debt' in data and 'total_assets' in data:
            value, interp, citation = calculate_debt_to_assets(
                total_debt=data['total_debt'],
                total_assets=data['total_assets'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='debt_to_assets',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        # Interest Coverage
        if 'operating_income' in data and 'interest_expense' in data:
            value, interp, citation = calculate_interest_coverage(
                ebit=data['operating_income'],
                interest_expense=data['interest_expense'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='interest_coverage',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        # Equity Multiplier
        if 'total_assets' in data and 'total_equity' in data:
            value, interp, citation = calculate_equity_multiplier(
                total_assets=data['total_assets'],
                total_equity=data['total_equity'],
                document_id=doc_id_str
            )
            results.append(MetricResult(
                metric_name='equity_multiplier',
                metric_value=value,
                metric_unit='ratio',
                interpretation=interp,
                citation_data=citation
            ))

        return results

    async def _calculate_specific_liquidity(
        self,
        data: Dict[str, Any],
        document_id: Optional[UUID],
        ratio_names: List[str]
    ) -> List[MetricResult]:
        """Calculate specific liquidity ratios"""
        all_ratios = await self._calculate_liquidity_ratios(data, document_id)
        return [r for r in all_ratios if r.metric_name in ratio_names]

    async def _calculate_specific_profitability(
        self,
        data: Dict[str, Any],
        document_id: Optional[UUID],
        ratio_names: List[str]
    ) -> List[MetricResult]:
        """Calculate specific profitability ratios"""
        all_ratios = await self._calculate_profitability_ratios(data, document_id)
        return [r for r in all_ratios if r.metric_name in ratio_names]

    async def _calculate_specific_leverage(
        self,
        data: Dict[str, Any],
        document_id: Optional[UUID],
        ratio_names: List[str]
    ) -> List[MetricResult]:
        """Calculate specific leverage ratios"""
        all_ratios = await self._calculate_leverage_ratios(data, document_id)
        return [r for r in all_ratios if r.metric_name in ratio_names]

    async def _generate_insights(
        self,
        metrics: MetricsResult,
        analysis_type: str
    ) -> InsightsResult:
        """Generate insights from calculated metrics"""
        config = self.ANALYSIS_TYPES[analysis_type]

        if not config.get('micro_agents'):
            return self._empty_insights()

        # Extract key metric values
        metrics_dict = {}
        for ratio in (metrics.liquidity_ratios +
                     metrics.profitability_ratios +
                     metrics.leverage_ratios):
            if ratio.metric_value is not None:
                metrics_dict[ratio.metric_name] = ratio.metric_value

        # Run classifications
        classifications = []

        # Liquidity
        if 'current_ratio' in metrics_dict and 'quick_ratio' in metrics_dict:
            liquidity_class = await self.agents.classify_liquidity(
                current_ratio=metrics_dict['current_ratio'],
                quick_ratio=metrics_dict['quick_ratio']
            )
            classifications.append(('liquidity', liquidity_class))
        else:
            liquidity_class = "insufficient_data"

        # Debt level
        if 'debt_to_equity' in metrics_dict:
            debt_class = await self.agents.classify_debt_level(
                debt_ratio=metrics_dict['debt_to_equity']
            )
            classifications.append(('debt', debt_class))
        else:
            debt_class = "insufficient_data"

        # Risk assessment
        if all(k in metrics_dict for k in ['debt_to_equity', 'current_ratio']):
            net_margin = metrics_dict.get('net_margin', 0)
            risk_level = await self.agents.assess_risk(
                debt=metrics_dict['debt_to_equity'],
                liquidity=metrics_dict['current_ratio'],
                profit=net_margin
            )
            classifications.append(('risk', risk_level))
        else:
            risk_level = "insufficient_data"

        # Identify concerns and strengths
        concerns = self._identify_concerns(metrics_dict)
        strengths = self._identify_strengths(metrics_dict)

        # Overall health
        overall_health = self._assess_overall_health(
            risk_level, liquidity_class, debt_class
        )

        return InsightsResult(
            risk_assessment=risk_level,
            liquidity_position=liquidity_class,
            profitability_trends="stable",
            leverage_analysis=debt_class,
            overall_health=overall_health,
            key_concerns=concerns,
            key_strengths=strengths,
            classification_count=len(classifications)
        )

    def _identify_concerns(self, metrics: Dict[str, float]) -> List[str]:
        """Identify key financial concerns from metrics"""
        concerns = []

        # Check liquidity concerns
        if metrics.get('current_ratio', 999) < 1.0:
            concerns.append("Current ratio below 1.0 - liquidity risk")

        if metrics.get('quick_ratio', 999) < 0.5:
            concerns.append("Quick ratio below 0.5 - heavy reliance on inventory")

        # Check leverage concerns
        if metrics.get('debt_to_equity', 0) > 2.5:
            concerns.append("Debt-to-equity ratio exceeds 2.5 - high leverage risk")

        if metrics.get('interest_coverage', 999) < 3.0:
            concerns.append("Interest coverage below 3.0x - debt service concerns")

        # Check profitability concerns
        if metrics.get('net_margin', 999) < 5.0:
            concerns.append("Net margin below 5% - thin profitability")

        if metrics.get('roe', 999) < 10.0:
            concerns.append("ROE below 10% - below-average shareholder returns")

        return concerns

    def _identify_strengths(self, metrics: Dict[str, float]) -> List[str]:
        """Identify key financial strengths from metrics"""
        strengths = []

        # Check liquidity strengths
        if metrics.get('current_ratio', 0) > 2.0:
            strengths.append("Strong liquidity position (current ratio > 2.0)")

        if metrics.get('cash_ratio', 0) > 0.5:
            strengths.append("Excellent cash reserves (cash ratio > 0.5)")

        # Check profitability strengths
        if metrics.get('net_margin', 0) > 15.0:
            strengths.append("Exceptional profitability (net margin > 15%)")

        if metrics.get('roe', 0) > 20.0:
            strengths.append("Outstanding ROE (> 20%)")

        # Check leverage strengths
        if metrics.get('debt_to_equity', 999) < 0.5:
            strengths.append("Conservative leverage (D/E < 0.5)")

        if metrics.get('interest_coverage', 0) > 8.0:
            strengths.append("Excellent debt service capacity (coverage > 8x)")

        return strengths

    def _assess_overall_health(
        self,
        risk: str,
        liquidity: str,
        leverage: str
    ) -> str:
        """Assess overall financial health from classifications"""
        # Simplified scoring system
        health_score = 0

        if risk == "low":
            health_score += 3
        elif risk == "medium":
            health_score += 2
        elif risk == "high":
            health_score += 0

        if liquidity == "strong":
            health_score += 3
        elif liquidity == "adequate":
            health_score += 2
        elif liquidity == "weak":
            health_score += 0

        if leverage in ["low", "moderate"]:
            health_score += 3
        elif leverage == "high":
            health_score += 1
        elif leverage == "critical":
            health_score += 0

        # Map score to health level
        if health_score >= 8:
            return "excellent"
        elif health_score >= 6:
            return "good"
        elif health_score >= 4:
            return "fair"
        else:
            return "poor"

    def _empty_insights(self) -> InsightsResult:
        """Return empty insights result"""
        return InsightsResult(
            risk_assessment="insufficient_data",
            liquidity_position="insufficient_data",
            profitability_trends="insufficient_data",
            leverage_analysis="insufficient_data",
            overall_health="insufficient_data",
            key_concerns=[],
            key_strengths=[],
            classification_count=0
        )

    def _collect_citations(self, metrics: MetricsResult) -> List[Dict[str, Any]]:
        """Collect all citations from calculated metrics"""
        citations = []

        for ratio in (metrics.liquidity_ratios +
                     metrics.profitability_ratios +
                     metrics.leverage_ratios):
            if ratio.citation_data:
                citations.append({
                    'metric_name': ratio.metric_name,
                    **ratio.citation_data
                })

        return citations

    def _calculate_quality_score(
        self,
        metrics: MetricsResult,
        financial_data: Dict[str, Any]
    ) -> float:
        """
        Calculate quality score for analysis

        Based on:
        - Percentage of ratios successfully calculated
        - Number of financial data points extracted
        - Average confidence (if available)
        """
        # Component 1: Ratio calculation success rate
        total_possible = 19  # All ratios
        calculation_rate = metrics.total_calculated / total_possible

        # Component 2: Data extraction completeness
        required_fields = [
            'current_assets', 'current_liabilities', 'total_assets',
            'total_equity', 'total_debt', 'revenue', 'net_income'
        ]
        data_completeness = len([f for f in required_fields if f in financial_data]) / len(required_fields)

        # Weighted average
        quality_score = (calculation_rate * 0.6) + (data_completeness * 0.4)

        return round(quality_score * 100, 2)  # Return as percentage

    async def _store_metrics(
        self,
        document_id: UUID,
        metrics: MetricsResult
    ) -> None:
        """Store calculated metrics in PostgreSQL"""
        all_metrics = []

        for ratio in (metrics.liquidity_ratios +
                     metrics.profitability_ratios +
                     metrics.leverage_ratios):
            if ratio.metric_value is not None:
                all_metrics.append({
                    'metric_name': ratio.metric_name,
                    'metric_value': ratio.metric_value,
                    'metric_unit': ratio.metric_unit,
                    'page_number': ratio.citation_data.get('page_numbers', [None])[0],
                    'confidence': ratio.confidence,
                    'calculation_method': ratio.citation_data.get('formula')
                })

        if all_metrics:
            stored_count = self.postgres.store_metrics(document_id, all_metrics)
            logger.info(f"Stored {stored_count} metrics in Postgres")

    def _cache_result(self, cache_key: str, result: AnalysisResult) -> None:
        """Cache analysis result in Redis"""
        try:
            # Convert to dict (excluding cached flag)
            result_dict = asdict(result)
            result_dict['timestamp'] = result.timestamp.isoformat()

            # Serialize to JSON
            result_json = json.dumps(result_dict)

            # Cache with TTL
            self.redis.setex(cache_key, self.CACHE_TTL_SECONDS, result_json)
            logger.info(f"Cached result: {cache_key} (TTL: {self.CACHE_TTL_SECONDS}s)")

        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
            # Non-critical - continue without caching

    def _reconstruct_analysis_result(self, result_dict: Dict) -> AnalysisResult:
        """Reconstruct AnalysisResult from cached dict"""
        # Reconstruct nested dataclasses
        metrics = MetricsResult(
            liquidity_ratios=[
                MetricResult(**m) for m in result_dict['metrics']['liquidity_ratios']
            ],
            profitability_ratios=[
                MetricResult(**m) for m in result_dict['metrics']['profitability_ratios']
            ],
            leverage_ratios=[
                MetricResult(**m) for m in result_dict['metrics']['leverage_ratios']
            ],
            total_calculated=result_dict['metrics']['total_calculated'],
            total_failed=result_dict['metrics']['total_failed'],
            calculation_time_ms=result_dict['metrics']['calculation_time_ms']
        )

        insights = InsightsResult(**result_dict['insights'])

        return AnalysisResult(
            document_id=UUID(result_dict['document_id']),
            analysis_type=result_dict['analysis_type'],
            metrics=metrics,
            insights=insights,
            citations=result_dict['citations'],
            financial_data_extracted=result_dict['financial_data_extracted'],
            quality_score=result_dict['quality_score'],
            timestamp=datetime.fromisoformat(result_dict['timestamp']),
            cached=True
        )


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_analysis_flow(
    semantic_search: SemanticSearch,
    micro_agents: MicroAgents,
    postgres_store: PostgresStore,
    redis_store: RedisStore
) -> AnalysisFlow:
    """
    Factory function to create AnalysisFlow instance

    Args:
        semantic_search: Initialized SemanticSearch instance
        micro_agents: Initialized MicroAgents instance
        postgres_store: Initialized PostgresStore instance
        redis_store: Initialized RedisStore instance

    Returns:
        Configured AnalysisFlow orchestrator

    Example:
        >>> flow = create_analysis_flow(
        ...     semantic_search=search,
        ...     micro_agents=agents,
        ...     postgres_store=pg,
        ...     redis_store=redis
        ... )
        >>> result = await flow.analyze_document(doc_id)
    """
    return AnalysisFlow(
        semantic_search=semantic_search,
        micro_agents=micro_agents,
        postgres_store=postgres_store,
        redis_store=redis_store
    )
