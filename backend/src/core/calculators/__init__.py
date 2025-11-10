"""
Financial Ratio Calculators Package

This package provides deterministic financial ratio calculators across multiple categories:
- Liquidity: Measures short-term obligation payment ability
- Profitability: Measures earnings generation efficiency
- Leverage: Measures debt levels and financial risk

All calculators return: (metric_value, interpretation, citation_data)
"""

# Liquidity Ratios
from .liquidity import (
    calculate_current_ratio,
    calculate_quick_ratio,
    calculate_cash_ratio,
    calculate_operating_cash_flow_ratio,
    calculate_defensive_interval_ratio
)

# Profitability Ratios
from .profitability import (
    calculate_gross_margin,
    calculate_operating_margin,
    calculate_net_margin,
    calculate_roa,
    calculate_roe,
    calculate_roic,
    calculate_eps,
    calculate_asset_turnover
)

# Leverage Ratios
from .leverage import (
    calculate_debt_to_equity,
    calculate_debt_to_assets,
    calculate_interest_coverage,
    calculate_debt_service_coverage,
    calculate_equity_multiplier,
    calculate_financial_leverage
)

__all__ = [
    # Liquidity (5 ratios)
    'calculate_current_ratio',
    'calculate_quick_ratio',
    'calculate_cash_ratio',
    'calculate_operating_cash_flow_ratio',
    'calculate_defensive_interval_ratio',

    # Profitability (8 ratios)
    'calculate_gross_margin',
    'calculate_operating_margin',
    'calculate_net_margin',
    'calculate_roa',
    'calculate_roe',
    'calculate_roic',
    'calculate_eps',
    'calculate_asset_turnover',

    # Leverage (6 ratios)
    'calculate_debt_to_equity',
    'calculate_debt_to_assets',
    'calculate_interest_coverage',
    'calculate_debt_service_coverage',
    'calculate_equity_multiplier',
    'calculate_financial_leverage',
]

# Total: 19 ratios implemented
