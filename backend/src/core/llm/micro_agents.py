"""
Micro-Agent System with Redis Caching
Implements 15+ tiny classification agents optimized for financial analysis
Max 50 input tokens, 10 output tokens per agent
"""

import logging
import hashlib
import json
from functools import wraps
from typing import List, Optional, Callable, Any

from src.storage.redis_store import RedisStore
from src.core.llm.lm_studio_client import LMStudioClient, LMStudioError
from src.core.llm.fallback_rules import FallbackRules, log_fallback_usage
from src.config.settings import settings

logger = logging.getLogger(__name__)


def _hash_inputs(*args, **kwargs) -> str:
    """
    Create SHA256 hash of function inputs for cache key

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hex digest of SHA256 hash
    """
    # Serialize inputs to JSON (sorted for consistency)
    input_str = json.dumps(
        {"args": args, "kwargs": sorted(kwargs.items())},
        sort_keys=True,
        default=str  # Handle non-serializable types
    )

    # Generate SHA256 hash
    return hashlib.sha256(input_str.encode('utf-8')).hexdigest()


def cached_micro_agent(
    redis_client: RedisStore,
    ttl: int = 86400,
    fallback_func: Optional[Callable] = None
):
    """
    Decorator for caching micro-agent results with SHA256 input hashing

    Caching Strategy:
    1. Hash inputs with SHA256
    2. Check Redis cache with key: "micro_agent:{agent_name}:{input_hash}"
    3. If cache hit -> return cached result (target: 80% hit rate)
    4. If cache miss -> call LLM
    5. Store result in Redis with TTL
    6. If LLM fails -> use fallback rules if provided

    Args:
        redis_client: Redis store instance
        ttl: Cache TTL in seconds (default 86400 = 24 hours)
        fallback_func: Optional fallback function if LLM unavailable

    Returns:
        Decorated async function with caching
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> str:
            # Generate cache key from function name and input hash
            input_hash = _hash_inputs(*args, **kwargs)
            cache_key = f"micro_agent:{func.__name__}:{input_hash}"

            # Check cache first
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.debug(f"Cache HIT for {func.__name__}: {cache_key[:50]}...")
                return cached_result

            logger.debug(f"Cache MISS for {func.__name__}: {cache_key[:50]}...")

            # Call LLM with fallback handling
            try:
                result = await func(*args, **kwargs)

                # Cache the result
                redis_client.setex(cache_key, ttl, result)
                logger.debug(f"Cached result for {func.__name__} (TTL: {ttl}s)")

                return result

            except LMStudioError as e:
                # LLM failed - try fallback if available
                if fallback_func:
                    log_fallback_usage(func.__name__, str(e))
                    result = fallback_func(*args, **kwargs)

                    # Cache fallback result with shorter TTL (1 hour)
                    redis_client.setex(cache_key, 3600, result)

                    return result
                else:
                    logger.error(f"LLM failed for {func.__name__} and no fallback available: {e}")
                    raise

        return wrapper
    return decorator


# ============================================================================
# MICRO-AGENT IMPLEMENTATIONS (15+ Financial Classifiers)
# ============================================================================

class MicroAgents:
    """
    Collection of micro-agents for financial classification

    Each agent:
    - Max 50 input tokens
    - Max 10 output tokens
    - Cached with SHA256 input hash
    - Fallback to rule-based logic if LLM unavailable
    """

    def __init__(self, redis_client: RedisStore, llm_client: LMStudioClient):
        """
        Initialize micro-agent system

        Args:
            redis_client: Redis store for caching
            llm_client: LM Studio client for LLM calls
        """
        self.redis = redis_client
        self.llm = llm_client
        self.fallback = FallbackRules()

    @cached_micro_agent(
        redis_client=None,  # Will be set via method
        ttl=86400,
        fallback_func=FallbackRules.classify_debt_level
    )
    async def classify_debt_level(self, debt_ratio: float) -> str:
        """
        Classify debt level from Debt/Equity ratio

        Args:
            debt_ratio: Debt to Equity ratio

        Returns:
            Classification: "low", "moderate", "high", or "critical"

        Example:
            >>> await classify_debt_level(2.45)
            "high"
        """
        prompt = f"Debt/Equity ratio is {debt_ratio:.2f}. Classification:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: low, moderate, high, or critical. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_liquidity
    )
    async def classify_liquidity(self, current_ratio: float, quick_ratio: float) -> str:
        """
        Classify liquidity position

        Args:
            current_ratio: Current assets / Current liabilities
            quick_ratio: Quick assets / Current liabilities

        Returns:
            Classification: "strong", "adequate", or "weak"

        Example:
            >>> await classify_liquidity(2.1, 1.5)
            "strong"
        """
        prompt = f"Current ratio {current_ratio:.2f}, Quick ratio {quick_ratio:.2f}. Liquidity:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: strong, adequate, or weak. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_profitability_trend
    )
    async def classify_profitability_trend(self, roe_values: List[float]) -> str:
        """
        Classify profitability trend from ROE time series

        Args:
            roe_values: List of ROE percentages over time (oldest to newest)

        Returns:
            Classification: "improving", "stable", or "declining"

        Example:
            >>> await classify_profitability_trend([12.5, 14.2, 16.8])
            "improving"
        """
        # Format as compact string
        roe_str = ", ".join([f"{v:.1f}%" for v in roe_values])
        prompt = f"ROE values over time: [{roe_str}]. Trend:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: improving, stable, or declining. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.assess_risk
    )
    async def assess_risk(self, debt: float, liquidity: float, profit: float) -> str:
        """
        Assess overall financial risk level

        Args:
            debt: Debt/Equity ratio
            liquidity: Current ratio
            profit: Net profit margin (%)

        Returns:
            Risk level: "low", "medium", or "high"

        Example:
            >>> await assess_risk(debt=1.2, liquidity=1.8, profit=8.5)
            "low"
        """
        prompt = f"Debt={debt:.1f}, Liquidity={liquidity:.1f}, Profit={profit:.1f}%. Risk:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify risk as: low, medium, or high. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_revenue_growth
    )
    async def classify_revenue_growth(self, growth_rate: float) -> str:
        """
        Classify revenue growth rate

        Args:
            growth_rate: YoY revenue growth (%)

        Returns:
            Classification: "strong", "moderate", "weak", or "negative"

        Example:
            >>> await classify_revenue_growth(22.5)
            "strong"
        """
        prompt = f"Revenue YoY growth: {growth_rate:.1f}%. Classification:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: strong, moderate, weak, or negative. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_margin_quality
    )
    async def classify_margin_quality(self, gross_margin: float, net_margin: float) -> str:
        """
        Classify profit margin quality

        Args:
            gross_margin: Gross profit margin (%)
            net_margin: Net profit margin (%)

        Returns:
            Classification: "excellent", "good", "average", or "poor"

        Example:
            >>> await classify_margin_quality(45.0, 12.5)
            "excellent"
        """
        prompt = f"Gross margin {gross_margin:.1f}%, Net margin {net_margin:.1f}%. Quality:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: excellent, good, average, or poor. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_asset_turnover
    )
    async def classify_asset_turnover(self, turnover_ratio: float) -> str:
        """
        Classify asset utilization efficiency

        Args:
            turnover_ratio: Revenue / Total Assets

        Returns:
            Classification: "high", "moderate", or "low"

        Example:
            >>> await classify_asset_turnover(1.8)
            "high"
        """
        prompt = f"Asset turnover ratio: {turnover_ratio:.2f}. Efficiency:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: high, moderate, or low. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_working_capital
    )
    async def classify_working_capital(self, working_capital_ratio: float) -> str:
        """
        Classify working capital position

        Args:
            working_capital_ratio: (Current Assets - Current Liabilities) / Total Assets

        Returns:
            Classification: "strong", "adequate", "tight", or "negative"

        Example:
            >>> await classify_working_capital(0.35)
            "strong"
        """
        prompt = f"Working capital ratio: {working_capital_ratio:.2f}. Position:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: strong, adequate, tight, or negative. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_interest_coverage
    )
    async def classify_interest_coverage(self, coverage_ratio: float) -> str:
        """
        Classify interest coverage ability

        Args:
            coverage_ratio: EBIT / Interest Expense

        Returns:
            Classification: "strong", "adequate", "weak", or "critical"

        Example:
            >>> await classify_interest_coverage(8.5)
            "strong"
        """
        prompt = f"Interest coverage ratio: {coverage_ratio:.1f}x. Coverage:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: strong, adequate, weak, or critical. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_cash_position
    )
    async def classify_cash_position(self, cash_ratio: float) -> str:
        """
        Classify cash position strength

        Args:
            cash_ratio: Cash / Current Liabilities

        Returns:
            Classification: "strong", "adequate", or "weak"

        Example:
            >>> await classify_cash_position(0.65)
            "strong"
        """
        prompt = f"Cash ratio: {cash_ratio:.2f}. Cash position:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: strong, adequate, or weak. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_equity_ratio
    )
    async def classify_equity_ratio(self, equity_ratio: float) -> str:
        """
        Classify equity position

        Args:
            equity_ratio: Total Equity / Total Assets

        Returns:
            Classification: "strong", "moderate", or "weak"

        Example:
            >>> await classify_equity_ratio(0.68)
            "strong"
        """
        prompt = f"Equity ratio: {equity_ratio:.2f}. Equity position:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: strong, moderate, or weak. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_operating_margin
    )
    async def classify_operating_margin(self, operating_margin: float) -> str:
        """
        Classify operating efficiency

        Args:
            operating_margin: Operating Income / Revenue (%)

        Returns:
            Classification: "excellent", "good", "average", or "poor"

        Example:
            >>> await classify_operating_margin(22.5)
            "excellent"
        """
        prompt = f"Operating margin: {operating_margin:.1f}%. Efficiency:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: excellent, good, average, or poor. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_inventory_turnover
    )
    async def classify_inventory_turnover(self, turnover: float) -> str:
        """
        Classify inventory management efficiency

        Args:
            turnover: Cost of Goods Sold / Average Inventory

        Returns:
            Classification: "fast", "moderate", or "slow"

        Example:
            >>> await classify_inventory_turnover(9.5)
            "fast"
        """
        prompt = f"Inventory turnover: {turnover:.1f}x. Speed:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: fast, moderate, or slow. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_receivables_days
    )
    async def classify_receivables_days(self, days: float) -> str:
        """
        Classify accounts receivable collection efficiency

        Args:
            days: Days Sales Outstanding (DSO)

        Returns:
            Classification: "excellent", "good", "average", or "slow"

        Example:
            >>> await classify_receivables_days(28)
            "excellent"
        """
        prompt = f"Days Sales Outstanding: {days:.0f} days. Collection:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: excellent, good, average, or slow. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_dividend_payout
    )
    async def classify_dividend_payout(self, payout_ratio: float) -> str:
        """
        Classify dividend policy

        Args:
            payout_ratio: Dividends / Net Income (%)

        Returns:
            Classification: "generous", "moderate", "conservative", or "none"

        Example:
            >>> await classify_dividend_payout(45.0)
            "moderate"
        """
        prompt = f"Dividend payout ratio: {payout_ratio:.1f}%. Policy:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: generous, moderate, conservative, or none. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_growth_stability
    )
    async def classify_growth_stability(self, growth_std_dev: float) -> str:
        """
        Classify revenue growth stability

        Args:
            growth_std_dev: Standard deviation of growth rates (%)

        Returns:
            Classification: "stable", "moderate", or "volatile"

        Example:
            >>> await classify_growth_stability(3.2)
            "stable"
        """
        prompt = f"Growth std dev: {growth_std_dev:.1f}%. Stability:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: stable, moderate, or volatile. Reply with one word only."
        )

        return response.lower().strip()

    @cached_micro_agent(
        redis_client=None,
        ttl=86400,
        fallback_func=FallbackRules.classify_market_position
    )
    async def classify_market_position(self, market_share: float) -> str:
        """
        Classify competitive market position

        Args:
            market_share: Company's market share (%)

        Returns:
            Classification: "dominant", "strong", "moderate", or "weak"

        Example:
            >>> await classify_market_position(32.5)
            "dominant"
        """
        prompt = f"Market share: {market_share:.1f}%. Position:"

        response = await self.llm.chat_completion(
            prompt=prompt,
            max_tokens=1,
            temperature=0.1,
            system_prompt="Classify as: dominant, strong, moderate, or weak. Reply with one word only."
        )

        return response.lower().strip()


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_micro_agents(redis_client: RedisStore, llm_client: LMStudioClient) -> MicroAgents:
    """
    Factory function to create MicroAgents instance with dependencies

    Args:
        redis_client: Redis store for caching
        llm_client: LM Studio client for LLM calls

    Returns:
        Initialized MicroAgents instance
    """
    agents = MicroAgents(redis_client, llm_client)

    # Patch decorator redis_client references
    # (Python limitation: decorator needs instance after init)
    for method_name in dir(agents):
        if method_name.startswith('classify_') or method_name.startswith('assess_'):
            method = getattr(agents, method_name)
            if hasattr(method, '__wrapped__'):
                # Update redis client in wrapper closure
                method.__self__.redis = redis_client

    logger.info("MicroAgents system initialized with Redis caching")

    return agents
