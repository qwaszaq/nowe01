"""
Liquidity Ratio Calculators
Measures company's ability to pay short-term obligations

All functions return: (metric_value: float, interpretation: str, citation_data: Dict)
"""

from typing import Dict, Tuple, Optional, List
from decimal import Decimal, InvalidOperation


def calculate_current_ratio(
    current_assets: float,
    current_liabilities: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Current Ratio (liquidity metric)

    Formula: Current Assets / Current Liabilities

    The current ratio measures a company's ability to pay short-term obligations
    due within one year with assets that can be converted to cash within that period.

    Args:
        current_assets: Total current assets (cash, receivables, inventory, etc.)
        current_liabilities: Total current liabilities (payables, short-term debt)
        document_id: Source document identifier for citation tracking
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (ratio_value, interpretation, citation_data)

    Industry Benchmarks:
        > 2.0: Strong liquidity (conservative companies)
        1.5-2.0: Healthy liquidity (most industries)
        1.0-1.5: Adequate liquidity (requires monitoring)
        < 1.0: Liquidity risk (unable to meet short-term obligations)

    Source: Corporate Finance Institute, CFA Standards
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["current_assets", "current_liabilities"],
        "formula": "Current Assets / Current Liabilities"
    }

    # Handle division by zero
    if current_liabilities == 0 or current_liabilities is None:
        return None, "Cannot calculate: Current liabilities is zero or missing", citation_data

    if current_assets is None:
        return None, "Cannot calculate: Current assets is missing", citation_data

    try:
        ratio = round(current_assets / current_liabilities, 2)

        # Generate interpretation based on industry benchmarks
        if ratio > 2.0:
            interpretation = f"Strong liquidity ({ratio:.2f}). Company has ${ratio:.2f} in current assets for every $1 of current liabilities. Well-positioned to meet short-term obligations."
        elif ratio >= 1.5:
            interpretation = f"Healthy liquidity ({ratio:.2f}). Company maintains adequate working capital to cover short-term obligations."
        elif ratio >= 1.0:
            interpretation = f"Adequate liquidity ({ratio:.2f}). Company can meet obligations but should be monitored closely. Limited cushion for unexpected events."
        else:
            interpretation = f"⚠️ LIQUIDITY RISK ({ratio:.2f}). Current assets insufficient to cover current liabilities. May struggle to meet short-term obligations."

        return ratio, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_quick_ratio(
    current_assets: float,
    inventory: float,
    current_liabilities: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Quick Ratio / Acid-Test Ratio (conservative liquidity metric)

    Formula: (Current Assets - Inventory) / Current Liabilities

    The quick ratio is a more conservative measure that excludes inventory,
    which may not be easily converted to cash.

    Args:
        current_assets: Total current assets
        inventory: Total inventory value
        current_liabilities: Total current liabilities
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (ratio_value, interpretation, citation_data)

    Industry Benchmarks:
        > 1.5: Excellent liquidity without relying on inventory
        1.0-1.5: Good liquidity position
        0.5-1.0: Moderate liquidity (monitor inventory turnover)
        < 0.5: Poor liquidity (heavily reliant on inventory sales)

    Source: Financial Accounting Standards, Investopedia
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["current_assets", "inventory", "current_liabilities"],
        "formula": "(Current Assets - Inventory) / Current Liabilities"
    }

    if current_liabilities == 0 or current_liabilities is None:
        return None, "Cannot calculate: Current liabilities is zero or missing", citation_data

    if current_assets is None or inventory is None:
        return None, "Cannot calculate: Required values missing", citation_data

    try:
        quick_assets = current_assets - inventory
        ratio = round(quick_assets / current_liabilities, 2)

        if ratio > 1.5:
            interpretation = f"Excellent liquidity ({ratio:.2f}). Company can meet obligations without selling inventory. Strong financial flexibility."
        elif ratio >= 1.0:
            interpretation = f"Good liquidity ({ratio:.2f}). Adequate liquid assets to cover current liabilities without inventory liquidation."
        elif ratio >= 0.5:
            interpretation = f"Moderate liquidity ({ratio:.2f}). Some reliance on inventory conversion. Monitor inventory turnover closely."
        else:
            interpretation = f"⚠️ POOR LIQUIDITY ({ratio:.2f}). Heavily dependent on inventory sales to meet obligations. High risk if inventory doesn't move."

        return ratio, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_cash_ratio(
    cash_and_equivalents: float,
    current_liabilities: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Cash Ratio (most conservative liquidity metric)

    Formula: Cash and Cash Equivalents / Current Liabilities

    The cash ratio is the most stringent liquidity test, measuring only
    the most liquid assets against current obligations.

    Args:
        cash_and_equivalents: Cash + marketable securities
        current_liabilities: Total current liabilities
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (ratio_value, interpretation, citation_data)

    Industry Benchmarks:
        > 1.0: Exceptional liquidity (can pay all obligations with cash)
        0.5-1.0: Strong cash position
        0.2-0.5: Adequate cash reserves
        < 0.2: Limited cash reserves (normal for some industries)

    Note: Many healthy companies operate with low cash ratios by design,
    investing cash in operations rather than holding idle reserves.

    Source: CFA Institute, Corporate Finance Principles
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["cash_and_equivalents", "current_liabilities"],
        "formula": "Cash and Cash Equivalents / Current Liabilities"
    }

    if current_liabilities == 0 or current_liabilities is None:
        return None, "Cannot calculate: Current liabilities is zero or missing", citation_data

    if cash_and_equivalents is None:
        return None, "Cannot calculate: Cash value is missing", citation_data

    try:
        ratio = round(cash_and_equivalents / current_liabilities, 2)

        if ratio > 1.0:
            interpretation = f"Exceptional liquidity ({ratio:.2f}). Company holds enough cash to pay all current liabilities immediately. Very conservative position."
        elif ratio >= 0.5:
            interpretation = f"Strong cash position ({ratio:.2f}). Substantial cash reserves provide flexibility during downturns."
        elif ratio >= 0.2:
            interpretation = f"Adequate cash reserves ({ratio:.2f}). Typical for growth companies that invest cash in operations."
        else:
            interpretation = f"Limited cash reserves ({ratio:.2f}). Relies on cash flow generation and asset conversion. Context-dependent risk."

        return ratio, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_operating_cash_flow_ratio(
    operating_cash_flow: float,
    current_liabilities: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Operating Cash Flow Ratio

    Formula: Operating Cash Flow / Current Liabilities

    This ratio measures how well current liabilities are covered by cash flow
    generated from operations. It's a dynamic measure that shows cash generation
    ability rather than static balance sheet positions.

    Args:
        operating_cash_flow: Cash flow from operating activities (from cash flow statement)
        current_liabilities: Total current liabilities
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (ratio_value, interpretation, citation_data)

    Industry Benchmarks:
        > 1.0: Excellent - Operations generate more than enough cash
        0.5-1.0: Good - Healthy cash generation
        0.25-0.5: Fair - Adequate but monitor trends
        < 0.25: Weak - Insufficient cash generation from operations

    Note: Seasonal businesses may show volatility. Analyze trends over multiple periods.

    Source: Cash Flow Analysis Standards, Financial Management Association
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["operating_cash_flow", "current_liabilities"],
        "formula": "Operating Cash Flow / Current Liabilities"
    }

    if current_liabilities == 0 or current_liabilities is None:
        return None, "Cannot calculate: Current liabilities is zero or missing", citation_data

    if operating_cash_flow is None:
        return None, "Cannot calculate: Operating cash flow is missing", citation_data

    try:
        ratio = round(operating_cash_flow / current_liabilities, 2)

        if ratio > 1.0:
            interpretation = f"Excellent cash generation ({ratio:.2f}). Operations produce more than enough cash to cover all current liabilities. Strong operational efficiency."
        elif ratio >= 0.5:
            interpretation = f"Good cash generation ({ratio:.2f}). Healthy operational cash flow provides solid coverage of short-term obligations."
        elif ratio >= 0.25:
            interpretation = f"Fair cash generation ({ratio:.2f}). Operations generate adequate cash but monitor trends. May need external financing for growth."
        elif ratio >= 0:
            interpretation = f"⚠️ WEAK CASH GENERATION ({ratio:.2f}). Insufficient operational cash flow. May rely on financing or asset sales to meet obligations."
        else:
            interpretation = f"🚨 NEGATIVE CASH FLOW ({ratio:.2f}). Operations consuming cash. Serious liquidity concerns. Immediate attention required."

        return ratio, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_defensive_interval_ratio(
    liquid_assets: float,
    daily_operating_expenses: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Defensive Interval Ratio (Days)

    Formula: Liquid Assets / Daily Operating Expenses

    This ratio measures how many days a company can operate using only its
    liquid assets without any additional revenue. Also known as "runway."

    Args:
        liquid_assets: Cash + marketable securities + receivables
        daily_operating_expenses: Annual operating expenses / 365
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (days, interpretation, citation_data)

    Industry Benchmarks:
        > 180 days: Excellent defensive position
        90-180 days: Good liquidity buffer
        30-90 days: Adequate but monitor closely
        < 30 days: Critical - immediate action needed

    Context: Startups target 18-24 months. Mature companies may operate
    with 60-90 days given predictable cash flows.

    Source: Financial Planning Standards, Startup Finance Best Practices
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["liquid_assets", "operating_expenses"],
        "formula": "Liquid Assets / Daily Operating Expenses"
    }

    if daily_operating_expenses == 0 or daily_operating_expenses is None:
        return None, "Cannot calculate: Daily operating expenses is zero or missing", citation_data

    if liquid_assets is None:
        return None, "Cannot calculate: Liquid assets value is missing", citation_data

    try:
        days = round(liquid_assets / daily_operating_expenses, 0)

        if days > 180:
            interpretation = f"Excellent defensive position ({int(days)} days). Company can operate for {int(days/30):.1f} months without revenue. Strong resilience to disruptions."
        elif days >= 90:
            interpretation = f"Good liquidity buffer ({int(days)} days). Approximately {int(days/30):.1f} months of runway provides adequate protection against revenue shocks."
        elif days >= 30:
            interpretation = f"Adequate runway ({int(days)} days). About {int(days/30):.1f} months of operations covered. Monitor cash flow closely and maintain revenue generation."
        else:
            interpretation = f"🚨 CRITICAL LIQUIDITY ({int(days)} days). Less than 1 month of runway. Immediate action needed to secure financing or increase cash generation."

        return days, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data
