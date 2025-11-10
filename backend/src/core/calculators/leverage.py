"""
Leverage Ratio Calculators
Measures company's debt levels and ability to meet financial obligations

All functions return: (metric_value: float, interpretation: str, citation_data: Dict)
"""

from typing import Dict, Tuple, Optional, List
from decimal import Decimal, InvalidOperation


def calculate_debt_to_equity(
    total_debt: float,
    total_equity: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Debt-to-Equity Ratio (D/E)

    Formula: Total Debt / Total Equity

    The D/E ratio measures financial leverage by comparing total debt to
    shareholders' equity. It shows how much the company relies on debt vs.
    equity financing.

    Args:
        total_debt: Total interest-bearing debt (short-term + long-term)
        total_equity: Total shareholders' equity
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (ratio_value, interpretation, citation_data)

    Industry Benchmarks:
        Utilities: 1.0-2.0 (stable cash flows support higher debt)
        Manufacturing: 0.5-1.5
        Technology: 0.0-0.5 (often minimal debt)
        Real Estate: 2.0-4.0 (asset-backed lending)
        Retail: 0.5-1.0

    Risk Levels:
        < 0.5: Conservative (low leverage)
        0.5-1.5: Moderate (balanced)
        1.5-2.5: Aggressive (high leverage)
        > 2.5: Very High (potential distress risk)

    Source: Credit Rating Agency Standards, Corporate Finance Institute
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["total_debt", "total_equity"],
        "formula": "Total Debt / Total Equity"
    }

    if total_equity == 0 or total_equity is None:
        return None, "Cannot calculate: Total equity is zero or missing", citation_data

    if total_equity < 0:
        return None, "⚠️ Negative equity (shareholders' deficit). Company technically insolvent. Cannot calculate meaningful D/E ratio.", citation_data

    if total_debt is None:
        return None, "Cannot calculate: Total debt is missing", citation_data

    try:
        ratio = round(total_debt / total_equity, 2)

        if ratio < 0.5:
            interpretation = f"Conservative leverage ({ratio:.2f}). Low debt levels provide financial flexibility. ${ratio:.2f} debt per $1 of equity."
        elif ratio < 1.0:
            interpretation = f"Moderate leverage ({ratio:.2f}). Balanced capital structure. More equity than debt financing."
        elif ratio < 1.5:
            interpretation = f"Elevated leverage ({ratio:.2f}). Significant debt load. Monitor debt service capacity and interest rate exposure."
        elif ratio < 2.5:
            interpretation = f"⚠️ HIGH LEVERAGE ({ratio:.2f}). Aggressive debt levels. Financial risk increases in economic downturns. Debt exceeds equity."
        else:
            interpretation = f"🚨 VERY HIGH LEVERAGE ({ratio:.2f}). Critical debt burden. ${ratio:.2f} debt per $1 equity. Severe financial distress risk."

        return ratio, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_debt_to_assets(
    total_debt: float,
    total_assets: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Debt-to-Assets Ratio

    Formula: Total Debt / Total Assets

    This ratio shows what percentage of assets are financed by debt.
    It measures financial leverage from an asset coverage perspective.

    Args:
        total_debt: Total interest-bearing debt (short-term + long-term)
        total_assets: Total assets
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (ratio_value, interpretation, citation_data)

    Industry Benchmarks:
        < 0.3 (30%): Low leverage - Conservative
        0.3-0.5: Moderate leverage - Typical
        0.5-0.7: High leverage - Monitor closely
        > 0.7 (70%): Very high leverage - Risk concern

    Interpretation:
        0.40 = 40% of assets financed by debt, 60% by equity

    Related Metric:
        Equity Ratio = 1 - Debt Ratio

    Source: Bankruptcy Prediction Models, Credit Analysis Standards
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["total_debt", "total_assets"],
        "formula": "Total Debt / Total Assets"
    }

    if total_assets == 0 or total_assets is None:
        return None, "Cannot calculate: Total assets is zero or missing", citation_data

    if total_debt is None:
        return None, "Cannot calculate: Total debt is missing", citation_data

    try:
        ratio = round(total_debt / total_assets, 2)
        ratio_pct = round(ratio * 100, 1)
        equity_pct = round((1 - ratio) * 100, 1)

        if ratio < 0.3:
            interpretation = f"Low leverage ({ratio:.2f} or {ratio_pct}%). Conservative financing. {equity_pct}% equity-financed. Strong asset coverage."
        elif ratio < 0.5:
            interpretation = f"Moderate leverage ({ratio:.2f} or {ratio_pct}%). Balanced capital structure. {equity_pct}% equity provides good cushion."
        elif ratio < 0.7:
            interpretation = f"⚠️ HIGH LEVERAGE ({ratio:.2f} or {ratio_pct}%). Significant debt burden. Only {equity_pct}% equity cushion. Monitor debt covenants."
        else:
            interpretation = f"🚨 VERY HIGH LEVERAGE ({ratio:.2f} or {ratio_pct}%). Critical debt levels. Limited {equity_pct}% equity buffer. High default risk."

        return ratio, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_interest_coverage(
    ebit: float,
    interest_expense: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Interest Coverage Ratio (Times Interest Earned)

    Formula: EBIT / Interest Expense

    Interest coverage measures how many times a company can pay its interest
    obligations from operating earnings. Critical for assessing debt safety.

    Args:
        ebit: Earnings Before Interest and Taxes (Operating Income)
        interest_expense: Annual interest expense on debt
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (coverage_ratio, interpretation, citation_data)

    Credit Rating Implications:
        > 8x: AAA/AA rating territory - Excellent
        5-8x: A/BBB rating - Strong
        3-5x: BBB/BB rating - Adequate
        1.5-3x: BB/B rating - Weak, risky
        < 1.5x: CCC or below - Distress zone
        < 1.0x: Cannot cover interest - Default risk

    Investment Grade Threshold: Typically 3.0x or higher

    Source: S&P, Moody's, Fitch Rating Methodologies
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["ebit", "interest_expense"],
        "formula": "EBIT / Interest Expense"
    }

    if interest_expense == 0 or interest_expense is None:
        if ebit and ebit > 0:
            return None, "No interest expense (likely no debt). Company is debt-free.", citation_data
        return None, "Cannot calculate: Interest expense is zero or missing", citation_data

    if ebit is None:
        return None, "Cannot calculate: EBIT is missing", citation_data

    try:
        coverage = round(ebit / interest_expense, 2)

        if coverage > 8:
            interpretation = f"Excellent coverage ({coverage:.2f}x). Strong debt safety. Earnings cover interest {coverage:.2f} times. Investment grade quality."
        elif coverage >= 5:
            interpretation = f"Strong coverage ({coverage:.2f}x). Comfortable debt service capacity. Low risk of default. Solid credit profile."
        elif coverage >= 3:
            interpretation = f"Adequate coverage ({coverage:.2f}x). Meets investment grade threshold. Monitor earnings volatility."
        elif coverage >= 1.5:
            interpretation = f"⚠️ WEAK COVERAGE ({coverage:.2f}x). Tight debt service. Below investment grade. Vulnerable to earnings decline."
        elif coverage >= 1.0:
            interpretation = f"🚨 DISTRESS ZONE ({coverage:.2f}x). Barely covering interest. High default risk. Credit rating likely CCC or below."
        else:
            interpretation = f"🚨 CRITICAL ({coverage:.2f}x). Cannot fully cover interest from operations. Default imminent without restructuring."

        return coverage, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_debt_service_coverage(
    ebitda: float,
    total_debt_service: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Debt Service Coverage Ratio (DSCR)

    Formula: EBITDA / Total Debt Service
    Where: Total Debt Service = Principal Repayments + Interest Expense

    DSCR measures ability to service all debt obligations (both principal and
    interest) from operating cash flow. Widely used by lenders.

    Args:
        ebitda: Earnings Before Interest, Taxes, Depreciation, Amortization
        total_debt_service: Annual principal payments + interest expense
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (dscr_ratio, interpretation, citation_data)

    Lending Standards:
        > 2.0: Excellent - Strong refinancing prospects
        1.5-2.0: Good - Most lenders comfortable
        1.25-1.5: Adequate - Minimum for many lenders
        1.0-1.25: Tight - Special circumstances only
        < 1.0: Insufficient - Loan default risk

    Real Estate: Often requires 1.25x minimum
    Corporate Lending: Typically requires 1.5x minimum

    Source: Commercial Lending Standards, Real Estate Finance Guidelines
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["ebitda", "debt_service"],
        "formula": "EBITDA / Total Debt Service"
    }

    if total_debt_service == 0 or total_debt_service is None:
        return None, "Cannot calculate: Total debt service is zero or missing", citation_data

    if ebitda is None:
        return None, "Cannot calculate: EBITDA is missing", citation_data

    try:
        dscr = round(ebitda / total_debt_service, 2)

        if dscr > 2.0:
            interpretation = f"Excellent DSCR ({dscr:.2f}x). Strong debt service capacity. Lenders view favorably. Easy refinancing."
        elif dscr >= 1.5:
            interpretation = f"Good DSCR ({dscr:.2f}x). Comfortable coverage of all debt obligations. Meets most lending requirements."
        elif dscr >= 1.25:
            interpretation = f"Adequate DSCR ({dscr:.2f}x). Meets minimum thresholds but limited cushion. Monitor cash flow closely."
        elif dscr >= 1.0:
            interpretation = f"⚠️ TIGHT DSCR ({dscr:.2f}x). Barely covering debt service. Below lending standards. Refinancing difficult."
        else:
            interpretation = f"🚨 INSUFFICIENT DSCR ({dscr:.2f}x). Cannot cover debt payments. Loan default risk. Restructuring needed."

        return dscr, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_equity_multiplier(
    total_assets: float,
    total_equity: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Equity Multiplier

    Formula: Total Assets / Total Equity

    The equity multiplier shows how much assets are supported by each dollar
    of equity. Higher values indicate more leverage. Component of DuPont analysis.

    Args:
        total_assets: Total assets
        total_equity: Total shareholders' equity
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (multiplier_value, interpretation, citation_data)

    DuPont Framework:
        ROE = Net Margin × Asset Turnover × Equity Multiplier

    Interpretation:
        2.0x = For every $1 of equity, company has $2 of assets
        Higher multiplier = More leverage

    Industry Benchmarks:
        Banks: 10-15x (highly leveraged)
        Utilities: 3-4x
        Manufacturing: 2-3x
        Technology: 1.5-2.5x

    Relationship:
        Equity Multiplier = 1 + Debt-to-Equity Ratio

    Source: DuPont Analysis, Financial Leverage Theory
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["total_assets", "total_equity"],
        "formula": "Total Assets / Total Equity"
    }

    if total_equity == 0 or total_equity is None:
        return None, "Cannot calculate: Total equity is zero or missing", citation_data

    if total_equity < 0:
        return None, "⚠️ Negative equity (shareholders' deficit). Assets less than liabilities. Technical insolvency.", citation_data

    if total_assets is None:
        return None, "Cannot calculate: Total assets is missing", citation_data

    try:
        multiplier = round(total_assets / total_equity, 2)

        if multiplier < 2.0:
            interpretation = f"Low leverage ({multiplier:.2f}x). Conservative financing. ${multiplier:.2f} assets per $1 equity. Minimal financial risk."
        elif multiplier < 3.0:
            interpretation = f"Moderate leverage ({multiplier:.2f}x). Balanced capital structure typical of many industries."
        elif multiplier < 4.0:
            interpretation = f"Elevated leverage ({multiplier:.2f}x). Significant debt usage. Monitor debt service capacity."
        else:
            interpretation = f"⚠️ HIGH LEVERAGE ({multiplier:.2f}x). Highly leveraged structure. ${multiplier:.2f} assets per $1 equity. Financial risk elevated."

        return multiplier, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data


def calculate_financial_leverage(
    total_debt: float,
    ebitda: float,
    document_id: Optional[str] = None,
    page_numbers: Optional[List[int]] = None
) -> Tuple[Optional[float], str, Dict]:
    """
    Calculate Financial Leverage Ratio (Debt/EBITDA)

    Formula: Total Debt / EBITDA

    This ratio shows how many years of EBITDA would be required to pay off
    all debt, assuming EBITDA is entirely used for debt repayment. Popular
    with private equity and leveraged buyouts.

    Args:
        total_debt: Total interest-bearing debt
        ebitda: Earnings Before Interest, Taxes, Depreciation, Amortization
        document_id: Source document identifier
        page_numbers: List of page numbers where data was found

    Returns:
        Tuple of (leverage_multiple, interpretation, citation_data)

    Credit Rating Benchmarks:
        < 1.0x: Minimal leverage - Conservative
        1.0-3.0x: Low leverage - Investment grade
        3.0-4.0x: Moderate leverage - Borderline IG
        4.0-5.0x: High leverage - Junk bond territory
        > 5.0x: Very high leverage - Distressed

    LBO Standards:
        Typical LBO: 4-6x Debt/EBITDA at entry
        Conservative LBO: 3-4x
        Aggressive LBO: 6-8x

    Source: Leveraged Finance Standards, S&P Leverage Commentary
    """
    citation_data = {
        "document_id": document_id,
        "page_numbers": page_numbers or [],
        "source_fields": ["total_debt", "ebitda"],
        "formula": "Total Debt / EBITDA"
    }

    if ebitda == 0 or ebitda is None:
        return None, "Cannot calculate: EBITDA is zero or missing", citation_data

    if ebitda < 0:
        return None, "⚠️ Negative EBITDA. Company not generating operating cash flow. Cannot assess leverage meaningfully.", citation_data

    if total_debt is None:
        return None, "Cannot calculate: Total debt is missing", citation_data

    try:
        leverage = round(total_debt / ebitda, 2)

        if leverage < 1.0:
            interpretation = f"Minimal leverage ({leverage:.2f}x). Could repay all debt in less than 1 year of EBITDA. Very conservative."
        elif leverage < 3.0:
            interpretation = f"Low leverage ({leverage:.2f}x). {leverage:.1f} years of EBITDA to repay debt. Investment grade territory."
        elif leverage < 4.0:
            interpretation = f"Moderate leverage ({leverage:.2f}x). Borderline investment grade. Typical for stable businesses."
        elif leverage < 5.0:
            interpretation = f"⚠️ HIGH LEVERAGE ({leverage:.2f}x). High yield / junk bond territory. {leverage:.1f} years to delever."
        else:
            interpretation = f"🚨 VERY HIGH LEVERAGE ({leverage:.2f}x). Distressed levels. Over {int(leverage)} years to repay. Refinancing risk."

        return leverage, interpretation, citation_data

    except (TypeError, InvalidOperation, ZeroDivisionError) as e:
        return None, f"Calculation error: {str(e)}", citation_data
