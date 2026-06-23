"""
eligibility_rules.py

A SIMPLIFIED, ILLUSTRATIVE income-based eligibility rule engine, modeled
loosely on how subsidized health coverage programs (e.g. Medicaid expansion /
marketplace subsidy programs) determine eligibility using household size and
income relative to the Federal Poverty Level (FPL).

IMPORTANT: This is NOT the actual business logic of any real government
or client system. It exists purely to give the test automation demo
something realistic to test against. Real eligibility systems incorporate
many more factors (immigration status, existing coverage, state-specific
rules, age, disability status, etc.) that are intentionally omitted here.

2024 federal poverty guidelines (48 contiguous states), used here only as
realistic example numbers:
    Household of 1: $15,060
    Each additional person: +$5,380
"""

from __future__ import annotations
from typing import Union

FPL_BASE = 15060
FPL_PER_ADDITIONAL_PERSON = 5380

MEDICAID_EXPANSION_CEILING_PCT = 138   
SUBSIDY_CEILING_PCT = 400              


def fpl_for_household(family_size: int) -> int:
    """Returns the FPL dollar amount for a given household size."""
    if family_size < 1:
        raise ValueError("family_size must be at least 1")
    return FPL_BASE + FPL_PER_ADDITIONAL_PERSON * (family_size - 1)


def income_as_pct_of_fpl(annual_income: float, family_size: int) -> float:
    fpl = fpl_for_household(family_size)
    return round((annual_income / fpl) * 100, 1)


def determine_eligibility(
    annual_income: Union[float, str], 
    family_size: Union[int, str],
    medicaid_ceiling: float = MEDICAID_EXPANSION_CEILING_PCT,
    subsidy_ceiling: float = SUBSIDY_CEILING_PCT
) -> str:
    """
    Requirement 1 & 2: Added input type validation for invalid values and 
    parameterized ceilings to evaluate alternative policy thresholds.
    """
    # Validate negative numbers, zero household size, or non-numeric strings
    try:
        ann_inc = float(annual_income)
        fam_size = int(family_size)
        if ann_inc < 0 or fam_size < 1:
            return "INVALID_INPUT"
    except (ValueError, TypeError):
        return "INVALID_INPUT"

    pct = income_as_pct_of_fpl(ann_inc, fam_size)

    if pct <= medicaid_ceiling:
        return "MEDICAID_ELIGIBLE"
    elif pct <= subsidy_ceiling:
        return "SUBSIDY_ELIGIBLE"
    else:
        return "NOT_ELIGIBLE"


def determine_eligibility_broken(
    annual_income: Union[float, str], 
    family_size: Union[int, str]
) -> str:
    """
    Requirement 3: Deliberately broken rules engine containing an off-by-one 
    regression (< instead of <=) on the boundary threshold check.
    """
    try:
        ann_inc = float(annual_income)
        fam_size = int(family_size)
        if ann_inc < 0 or fam_size < 1:
            return "INVALID_INPUT"
    except (ValueError, TypeError):
        return "INVALID_INPUT"

    pct = income_as_pct_of_fpl(ann_inc, fam_size)

    # DELIBERATE REGRESSION: Using strictly less-than (<) fails on exact boundary matches
    if pct < MEDICAID_EXPANSION_CEILING_PCT:
        return "MEDICAID_ELIGIBLE"
    elif pct < SUBSIDY_CEILING_PCT:
        return "SUBSIDY_ELIGIBLE"
    else:
        return "NOT_ELIGIBLE"