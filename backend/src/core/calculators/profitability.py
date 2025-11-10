"""
Profitability Ratio Calculators
Measures company's ability to generate earnings relative to revenue, assets, and equity

All functions return: (metric_value: float, interpretation: str, citation_data: Dict)
"""

from typing import Dict, Tuple, Optional, List
from decimal import Decimal, InvalidOperation


def calculate_gross_margin(
    gross_profit: float,
    revenue: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Gross Profit Margin (%)

    Formula: (Gross Profit / Revenue) × 100
    Alternative: ((Revenue - COGS) / Revenue) × 100

    Gross margin shows the percentage of revenue remaining after deducting
    the cost of goods sold. Higher margins indicate better pricing power
    and production efficiency.

    Args:
        gross_profit: Revenue minus cost of goods sold
        revenue: Total revenue / net sales
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (margin_percentage, interpretation, citation_data)

    Industry Benchmarks:
        Software/SaaS: 70-90%
        Pharmaceuticals: 60-80%
        Retail: 20-40%
        Manufacturing: 20-35%
        Grocery: 10-20%

    Source: Damodaran Industry Data, S&P Capital IQ
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["gross_profit", "revenue"],
        "formula": "(Gross Profit / Revenue) × 100"
    }

    if revenue == 0 or revenue is None:
        return None, "Cannot calculate: Revenue is zero or missing", citation_data

    if gross_profit is None:
        return None, "Cannot calculate: Gross profit is missing", citation_data

    try:
        margin_pct = round((gross_profit / revenue) * 100, 2)

        if margin_pct > 70:
            interpretation = f"Exceptional margin ({margin_pct}%). High-margin business model (typical for software, IP-driven companies). Strong pricing power."
        elif margin_pct >= 40:
            interpretation = f"Strong margin ({margin_pct}%). Healthy profitability with good cost management. Above average for most industries."
        elif margin_pct >= 20:
            interpretation = f"Moderate margin ({margin_pct}%). Typical for manufacturing and retail. Requires volume to drive profitability."
        elif margin_pct >= 0:
            interpretation = f"⚠️ LOW MARGIN ({margin_pct}%). Thin margins require high efficiency. Vulnerable to cost increases and pricing pressure."
        else:
            interpretation = f"🚨 NEGATIVE MARGIN ({margin_pct}%). Selling products below cost. Unsustainable without corrective action."

        return margin_pct, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_operating_margin(
    operating_income: float,
    revenue: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Operating Profit Margin (%)

    Formula: (Operating Income / Revenue) × 100
    Also known as: EBIT Margin

    Operating margin shows profitability after operating expenses but before
    interest and taxes. It reflects operational efficiency and core business performance.

    Args:
        operating_income: EBIT (Earnings Before Interest and Taxes)
        revenue: Total revenue / net sales
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (margin_percentage, interpretation, citation_data)

    Industry Benchmarks:
        Software: 20-40%
        Finance: 20-35%
        Healthcare: 10-20%
        Retail: 2-8%
        Airlines: 5-10%

    Source: McKinsey Benchmarks, Industry Financial Ratios
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["operating_income", "revenue"],
        "formula": "(Operating Income / Revenue) × 100"
    }

    if revenue == 0 or revenue is None:
        return None, "Cannot calculate: Revenue is zero or missing", citation_data

    if operating_income is None:
        return None, "Cannot calculate: Operating income is missing", citation_data

    try:
        margin_pct = round((operating_income / revenue) * 100, 2)

        if margin_pct > 25:
            interpretation = f"Excellent operating efficiency ({margin_pct}%). Strong operational leverage and cost control. Premium business model."
        elif margin_pct >= 15:
            interpretation = f"Strong operating performance ({margin_pct}%). Healthy profitability from core operations. Good competitive position."
        elif margin_pct >= 5:
            interpretation = f"Moderate operating margin ({margin_pct}%). Adequate operational efficiency. Monitor cost trends closely."
        elif margin_pct >= 0:
            interpretation = f"⚠️ LOW OPERATING MARGIN ({margin_pct}%). Limited operational profitability. High breakeven point. Cost structure concerns."
        else:
            interpretation = f"🚨 OPERATING LOSS ({margin_pct}%). Core operations losing money. Immediate restructuring needed."

        return margin_pct, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_net_margin(
    net_income: float,
    revenue: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Net Profit Margin (%)

    Formula: (Net Income / Revenue) × 100

    Net margin is the bottom line - the percentage of revenue that becomes profit
    after all expenses, interest, and taxes. The ultimate measure of profitability.

    Args:
        net_income: Net profit after all expenses, interest, and taxes
        revenue: Total revenue / net sales
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (margin_percentage, interpretation, citation_data)

    Industry Benchmarks:
        Software/Tech: 15-25%
        Banking: 15-30%
        Consumer Goods: 8-15%
        Retail: 2-5%
        Utilities: 5-10%

    Source: Fortune 500 Analysis, CSI Market Data
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["net_income", "revenue"],
        "formula": "(Net Income / Revenue) × 100"
    }

    if revenue == 0 or revenue is None:
        return None, "Cannot calculate: Revenue is zero or missing", citation_data

    if net_income is None:
        return None, "Cannot calculate: Net income is missing", citation_data

    try:
        margin_pct = round((net_income / revenue) * 100, 2)

        if margin_pct > 20:
            interpretation = f"Exceptional profitability ({margin_pct}%). Elite profit margins. Strong competitive moat and pricing power."
        elif margin_pct >= 10:
            interpretation = f"Strong profitability ({margin_pct}%). Healthy bottom line. Well-managed business with good unit economics."
        elif margin_pct >= 5:
            interpretation = f"Moderate profitability ({margin_pct}%). Adequate profits. Room for improvement in efficiency or pricing."
        elif margin_pct >= 0:
            interpretation = f"⚠️ THIN MARGINS ({margin_pct}%). Minimal profitability. Vulnerable to economic downturns or unexpected costs."
        else:
            interpretation = f"🚨 NET LOSS ({margin_pct}%). Company is unprofitable. Assess path to profitability or funding runway."

        return margin_pct, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_roa(
    net_income: float,
    total_assets: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Return on Assets - ROA (%)

    Formula: (Net Income / Total Assets) × 100

    ROA measures how efficiently a company uses its assets to generate profit.
    Higher ROA indicates better asset utilization and management effectiveness.

    Args:
        net_income: Net profit after taxes
        total_assets: Total assets (average of beginning and ending preferred)
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (roa_percentage, interpretation, citation_data)

    Industry Benchmarks:
        Technology: 8-15%
        Finance: 0.5-1.5%
        Retail: 5-10%
        Manufacturing: 3-7%
        Utilities: 2-4%

    Note: Asset-heavy industries naturally have lower ROA. Compare within industry.

    Source: ROA Industry Standards, DuPont Analysis Framework
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["net_income", "total_assets"],
        "formula": "(Net Income / Total Assets) × 100"
    }

    if total_assets == 0 or total_assets is None:
        return None, "Cannot calculate: Total assets is zero or missing", citation_data

    if net_income is None:
        return None, "Cannot calculate: Net income is missing", citation_data

    try:
        roa_pct = round((net_income / total_assets) * 100, 2)

        if roa_pct > 15:
            interpretation = f"Exceptional asset efficiency ({roa_pct}%). Outstanding return on deployed capital. Best-in-class asset utilization."
        elif roa_pct >= 8:
            interpretation = f"Strong ROA ({roa_pct}%). Effective asset management. Company generates solid returns from its asset base."
        elif roa_pct >= 3:
            interpretation = f"Moderate ROA ({roa_pct}%). Adequate asset productivity. Typical for asset-intensive industries."
        elif roa_pct >= 0:
            interpretation = f"⚠️ LOW ROA ({roa_pct}%). Poor asset utilization. Consider asset optimization or divestiture of underperforming assets."
        else:
            interpretation = f"🚨 NEGATIVE ROA ({roa_pct}%). Assets not generating profit. Fundamental business model concerns."

        return roa_pct, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_roe(
    net_income: float,
    shareholders_equity: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Return on Equity - ROE (%)

    Formula: (Net Income / Shareholders' Equity) × 100

    ROE measures the return generated on shareholders' investment. It's the
    most important metric for equity investors. Warren Buffett targets ROE > 15%.

    Args:
        net_income: Net profit after taxes
        shareholders_equity: Total equity (average preferred)
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (roe_percentage, interpretation, citation_data)

    Industry Benchmarks:
        Technology: 15-30%
        Finance: 10-15%
        Consumer Goods: 15-25%
        Utilities: 8-12%
        Manufacturing: 10-20%

    Warning: High ROE with high leverage can be risky. Use DuPont analysis
    to decompose ROE into margin, turnover, and leverage components.

    Source: Warren Buffett Letters, DuPont Analysis, Value Investing Standards
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["net_income", "shareholders_equity"],
        "formula": "(Net Income / Shareholders' Equity) × 100"
    }

    if shareholders_equity == 0 or shareholders_equity is None:
        return None, "Cannot calculate: Shareholders' equity is zero or missing", citation_data

    if shareholders_equity < 0:
        return None, "⚠️ Negative equity (shareholders' deficit). Cannot calculate meaningful ROE.", citation_data

    if net_income is None:
        return None, "Cannot calculate: Net income is missing", citation_data

    try:
        roe_pct = round((net_income / shareholders_equity) * 100, 2)

        if roe_pct > 20:
            interpretation = f"Exceptional ROE ({roe_pct}%). Outstanding returns for shareholders. Verify this isn't driven solely by excessive leverage."
        elif roe_pct >= 15:
            interpretation = f"Strong ROE ({roe_pct}%). Excellent returns meeting Warren Buffett's 15% threshold. Quality business generating wealth for owners."
        elif roe_pct >= 10:
            interpretation = f"Good ROE ({roe_pct}%). Solid returns for shareholders. Above average capital efficiency."
        elif roe_pct >= 0:
            interpretation = f"⚠️ LOW ROE ({roe_pct}%). Below-average returns. Capital could potentially be deployed more effectively elsewhere."
        else:
            interpretation = f"🚨 NEGATIVE ROE ({roe_pct}%). Destroying shareholder value. Losses eroding equity base."

        return roe_pct, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_roic(
    nopat: float,
    invested_capital: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Return on Invested Capital - ROIC (%)

    Formula: (NOPAT / Invested Capital) × 100
    Where: NOPAT = Net Operating Profit After Tax
           Invested Capital = Equity + Debt - Cash

    ROIC measures returns on all capital invested in the business (debt + equity).
    It's arguably the best metric for assessing true economic profitability.

    Args:
        nopat: Net Operating Profit After Tax
        invested_capital: Total capital invested (Equity + Interest-bearing Debt - Excess Cash)
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (roic_percentage, interpretation, citation_data)

    Key Principle:
        ROIC > WACC: Company creates value
        ROIC < WACC: Company destroys value

    Industry Benchmarks:
        Excellent: > 15%
        Good: 10-15%
        Average: 5-10%
        Poor: < 5%

    Source: McKinsey Valuation, Damodaran Investment Valuation
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["nopat", "invested_capital"],
        "formula": "(NOPAT / Invested Capital) × 100"
    }

    if invested_capital == 0 or invested_capital is None:
        return None, "Cannot calculate: Invested capital is zero or missing", citation_data

    if nopat is None:
        return None, "Cannot calculate: NOPAT is missing", citation_data

    try:
        roic_pct = round((nopat / invested_capital) * 100, 2)

        if roic_pct > 15:
            interpretation = f"Exceptional ROIC ({roic_pct}%). High-quality business generating outstanding returns on invested capital. Likely exceeds WACC significantly."
        elif roic_pct >= 10:
            interpretation = f"Strong ROIC ({roic_pct}%). Good capital efficiency. Probably creating shareholder value (verify against WACC)."
        elif roic_pct >= 5:
            interpretation = f"Moderate ROIC ({roic_pct}%). Average capital returns. Compare to WACC to assess value creation."
        elif roic_pct >= 0:
            interpretation = f"⚠️ LOW ROIC ({roic_pct}%). Poor capital efficiency. Likely destroying value if below WACC. Consider capital reallocation."
        else:
            interpretation = f"🚨 NEGATIVE ROIC ({roic_pct}%). Operations losing money. Capital destruction. Fundamental business issues."

        return roic_pct, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_eps(
    net_income: float,
    shares_outstanding: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Earnings Per Share - EPS ($)

    Formula: Net Income / Weighted Average Shares Outstanding

    EPS is the portion of company profit allocated to each share of common stock.
    It's a key metric for valuation (P/E ratio) and evaluating profitability trends.

    Args:
        net_income: Net profit after taxes (available to common shareholders)
        shares_outstanding: Weighted average shares outstanding (diluted preferred)
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (eps_value, interpretation, citation_data)

    Analysis Guidelines:
        - Compare to prior periods to assess growth
        - Compare to analyst estimates (beat/miss)
        - Use diluted shares for conservative calculation
        - Watch for share buybacks inflating EPS

    Note: EPS alone is insufficient. Must consider context:
    - Growth rate
    - Quality of earnings
    - Cash flow backing
    - Share count changes

    Source: GAAP Reporting Standards, SEC Filing Requirements
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["net_income", "shares_outstanding"],
        "formula": "Net Income / Weighted Average Shares Outstanding"
    }

    if shares_outstanding == 0 or shares_outstanding is None:
        return None, "Cannot calculate: Shares outstanding is zero or missing", citation_data

    if net_income is None:
        return None, "Cannot calculate: Net income is missing", citation_data

    try:
        eps = round(net_income / shares_outstanding, 2)

        if eps > 5:
            interpretation = f"Strong EPS (${eps:.2f}). High per-share profitability. Evaluate growth trends and compare to industry peers."
        elif eps > 0:
            interpretation = f"Positive EPS (${eps:.2f}). Profitable on per-share basis. Assess trend direction and growth rate."
        elif eps == 0:
            interpretation = f"Break-even EPS (${eps:.2f}). No profit/loss per share. Monitor path to profitability."
        else:
            interpretation = f"⚠️ NEGATIVE EPS (${eps:.2f}). Loss per share. Company unprofitable. Assess when profitability expected."

        return eps, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_asset_turnover(
    revenue: float,
    total_assets: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Asset Turnover Ratio

    Formula: Revenue / Average Total Assets

    Asset turnover measures how efficiently a company uses its assets to generate
    revenue. Higher turnover indicates better asset utilization.

    Args:
        revenue: Net sales / total revenue
        total_assets: Total assets (average of period preferred)
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (turnover_ratio, interpretation, citation_data)

    Industry Benchmarks:
        Retail: 2.0-3.0x
        Technology: 0.5-1.5x
        Manufacturing: 1.0-2.0x
        Utilities: 0.3-0.5x
        Real Estate: 0.1-0.3x

    DuPont Analysis Component:
        ROA = Net Margin × Asset Turnover
        This ratio is one component of profitability analysis.

    Source: DuPont Analysis, Financial Statement Analysis Standards
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["revenue", "total_assets"],
        "formula": "Revenue / Average Total Assets"
    }

    if total_assets == 0 or total_assets is None:
        return None, "Cannot calculate: Total assets is zero or missing", citation_data

    if revenue is None:
        return None, "Cannot calculate: Revenue is missing", citation_data

    try:
        turnover = round(revenue / total_assets, 2)

        if turnover > 2.0:
            interpretation = f"High asset turnover ({turnover:.2f}x). Excellent asset efficiency. Company generates ${turnover:.2f} in revenue per $1 of assets."
        elif turnover >= 1.0:
            interpretation = f"Good asset turnover ({turnover:.2f}x). Healthy asset utilization. Typical for many industries."
        elif turnover >= 0.5:
            interpretation = f"Moderate turnover ({turnover:.2f}x). Adequate efficiency. Common for capital-intensive businesses."
        else:
            interpretation = f"Low asset turnover ({turnover:.2f}x). Asset-heavy business model. May indicate underutilized assets or industry characteristic."

        return turnover, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data
