"""
Fallback Rules for Micro-Agents
Provides rule-based classification when LM Studio is unavailable
Simple threshold logic for financial metrics
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class FallbackRules:
    """
    Rule-based classification for financial metrics

    Used as fallback when LM Studio is unavailable or times out.
    Implements simple threshold logic for deterministic classification.
    """

    @staticmethod
    def classify_debt_level(debt_ratio: float) -> str:
        """
        Classify debt level based on Debt/Equity ratio

        Args:
            debt_ratio: Debt to Equity ratio

        Returns:
            Classification: "low", "moderate", "high", or "critical"
        """
        if debt_ratio < 0.5:
            return "low"
        elif debt_ratio < 1.5:
            return "moderate"
        elif debt_ratio < 3.0:
            return "high"
        else:
            return "critical"

    @staticmethod
    def classify_liquidity(current_ratio: float, quick_ratio: float) -> str:
        """
        Classify liquidity status

        Args:
            current_ratio: Current assets / Current liabilities
            quick_ratio: Quick assets / Current liabilities

        Returns:
            Classification: "strong", "adequate", or "weak"
        """
        # Weighted score (current ratio 60%, quick ratio 40%)
        score = (current_ratio * 0.6) + (quick_ratio * 0.4)

        if score >= 2.0:
            return "strong"
        elif score >= 1.0:
            return "adequate"
        else:
            return "weak"

    @staticmethod
    def classify_profitability_trend(roe_values: List[float]) -> str:
        """
        Classify profitability trend from ROE values

        Args:
            roe_values: List of ROE values over time (oldest to newest)

        Returns:
            Classification: "improving", "stable", or "declining"
        """
        if len(roe_values) < 2:
            return "stable"

        # Calculate trend (average change)
        changes = [roe_values[i] - roe_values[i-1] for i in range(1, len(roe_values))]
        avg_change = sum(changes) / len(changes)

        if avg_change > 2.0:  # More than 2% average improvement
            return "improving"
        elif avg_change < -2.0:  # More than 2% average decline
            return "declining"
        else:
            return "stable"

    @staticmethod
    def assess_risk(debt: float, liquidity: float, profit: float) -> str:
        """
        Assess overall risk level

        Args:
            debt: Debt/Equity ratio
            liquidity: Current ratio
            profit: Net profit margin (as percentage)

        Returns:
            Risk level: "low", "medium", or "high"
        """
        risk_score = 0

        # Debt component (weight: 40%)
        if debt > 2.5:
            risk_score += 40
        elif debt > 1.5:
            risk_score += 25
        elif debt > 0.8:
            risk_score += 10

        # Liquidity component (weight: 30%)
        if liquidity < 1.0:
            risk_score += 30
        elif liquidity < 1.5:
            risk_score += 15

        # Profitability component (weight: 30%)
        if profit < 0:
            risk_score += 30
        elif profit < 5:
            risk_score += 15

        # Classify based on total risk score
        if risk_score >= 60:
            return "high"
        elif risk_score >= 30:
            return "medium"
        else:
            return "low"

    @staticmethod
    def classify_revenue_growth(growth_rate: float) -> str:
        """
        Classify revenue growth rate

        Args:
            growth_rate: YoY revenue growth rate (as percentage)

        Returns:
            Classification: "strong", "moderate", "weak", or "negative"
        """
        if growth_rate >= 15.0:
            return "strong"
        elif growth_rate >= 5.0:
            return "moderate"
        elif growth_rate >= 0:
            return "weak"
        else:
            return "negative"

    @staticmethod
    def classify_margin_quality(gross_margin: float, net_margin: float) -> str:
        """
        Classify margin quality

        Args:
            gross_margin: Gross profit margin (%)
            net_margin: Net profit margin (%)

        Returns:
            Classification: "excellent", "good", "average", or "poor"
        """
        # Combined score
        score = (gross_margin * 0.4) + (net_margin * 0.6)

        if score >= 20.0:
            return "excellent"
        elif score >= 10.0:
            return "good"
        elif score >= 5.0:
            return "average"
        else:
            return "poor"

    @staticmethod
    def classify_asset_turnover(turnover_ratio: float) -> str:
        """
        Classify asset utilization efficiency

        Args:
            turnover_ratio: Revenue / Total Assets

        Returns:
            Classification: "high", "moderate", or "low"
        """
        if turnover_ratio >= 1.5:
            return "high"
        elif turnover_ratio >= 0.8:
            return "moderate"
        else:
            return "low"

    @staticmethod
    def classify_working_capital(working_capital_ratio: float) -> str:
        """
        Classify working capital position

        Args:
            working_capital_ratio: (Current Assets - Current Liabilities) / Total Assets

        Returns:
            Classification: "strong", "adequate", "tight", or "negative"
        """
        if working_capital_ratio >= 0.3:
            return "strong"
        elif working_capital_ratio >= 0.15:
            return "adequate"
        elif working_capital_ratio >= 0:
            return "tight"
        else:
            return "negative"

    @staticmethod
    def classify_interest_coverage(coverage_ratio: float) -> str:
        """
        Classify interest coverage ability

        Args:
            coverage_ratio: EBIT / Interest Expense

        Returns:
            Classification: "strong", "adequate", "weak", or "critical"
        """
        if coverage_ratio >= 5.0:
            return "strong"
        elif coverage_ratio >= 2.5:
            return "adequate"
        elif coverage_ratio >= 1.0:
            return "weak"
        else:
            return "critical"

    @staticmethod
    def classify_cash_position(cash_ratio: float) -> str:
        """
        Classify cash position strength

        Args:
            cash_ratio: Cash / Current Liabilities

        Returns:
            Classification: "strong", "adequate", or "weak"
        """
        if cash_ratio >= 0.5:
            return "strong"
        elif cash_ratio >= 0.2:
            return "adequate"
        else:
            return "weak"

    @staticmethod
    def classify_equity_ratio(equity_ratio: float) -> str:
        """
        Classify equity position

        Args:
            equity_ratio: Total Equity / Total Assets

        Returns:
            Classification: "strong", "moderate", or "weak"
        """
        if equity_ratio >= 0.6:
            return "strong"
        elif equity_ratio >= 0.4:
            return "moderate"
        else:
            return "weak"

    @staticmethod
    def classify_operating_margin(operating_margin: float) -> str:
        """
        Classify operating efficiency

        Args:
            operating_margin: Operating Income / Revenue (%)

        Returns:
            Classification: "excellent", "good", "average", or "poor"
        """
        if operating_margin >= 20.0:
            return "excellent"
        elif operating_margin >= 10.0:
            return "good"
        elif operating_margin >= 5.0:
            return "average"
        else:
            return "poor"

    @staticmethod
    def classify_inventory_turnover(turnover: float) -> str:
        """
        Classify inventory management efficiency

        Args:
            turnover: Cost of Goods Sold / Average Inventory

        Returns:
            Classification: "fast", "moderate", or "slow"
        """
        if turnover >= 8.0:
            return "fast"
        elif turnover >= 4.0:
            return "moderate"
        else:
            return "slow"

    @staticmethod
    def classify_receivables_days(days: float) -> str:
        """
        Classify accounts receivable collection efficiency

        Args:
            days: Days Sales Outstanding (DSO)

        Returns:
            Classification: "excellent", "good", "average", or "slow"
        """
        if days <= 30:
            return "excellent"
        elif days <= 45:
            return "good"
        elif days <= 60:
            return "average"
        else:
            return "slow"

    @staticmethod
    def classify_dividend_payout(payout_ratio: float) -> str:
        """
        Classify dividend policy

        Args:
            payout_ratio: Dividends / Net Income (%)

        Returns:
            Classification: "generous", "moderate", "conservative", or "none"
        """
        if payout_ratio >= 60.0:
            return "generous"
        elif payout_ratio >= 30.0:
            return "moderate"
        elif payout_ratio > 0:
            return "conservative"
        else:
            return "none"

    @staticmethod
    def classify_growth_stability(growth_std_dev: float) -> str:
        """
        Classify revenue growth stability

        Args:
            growth_std_dev: Standard deviation of growth rates

        Returns:
            Classification: "stable", "moderate", or "volatile"
        """
        if growth_std_dev <= 5.0:
            return "stable"
        elif growth_std_dev <= 15.0:
            return "moderate"
        else:
            return "volatile"

    @staticmethod
    def classify_market_position(market_share: float) -> str:
        """
        Classify competitive market position

        Args:
            market_share: Company's market share (%)

        Returns:
            Classification: "dominant", "strong", "moderate", or "weak"
        """
        if market_share >= 30.0:
            return "dominant"
        elif market_share >= 15.0:
            return "strong"
        elif market_share >= 5.0:
            return "moderate"
        else:
            return "weak"


# Log when fallback rules are used
def log_fallback_usage(agent_name: str, reason: str = "LM Studio unavailable"):
    """
    Log when fallback rules are used instead of LLM

    Args:
        agent_name: Name of the micro-agent
        reason: Reason for using fallback
    """
    logger.warning(f"Using fallback rules for {agent_name}: {reason}")
