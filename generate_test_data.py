"""
generate_test_data.py

Builds a CSV "grid" of synthetic test cases for the eligibility system --
this is the part of the workflow that mirrors filling in a spreadsheet
with made-up demographic, income, and family-size data row by row, except
here it's generated programmatically so the test data is reproducible,
covers deliberate boundary conditions, and can be regenerated instantly
if the rule set changes.

Each row represents one synthetic test "person/household":
    test_id, first_name, last_name, family_size, annual_income, expected_eligibility

Boundary-focused test design: for each eligibility tier boundary (138% FPL,
400% FPL), we generate a case just below, exactly at, and just above the
threshold -- these edge cases are where eligibility bugs are most likely to
hide, far more so than a randomly generated "typical" case.
"""
import csv
import os
import random

from eligibility_rules import (
    determine_eligibility,
    fpl_for_household,
    MEDICAID_EXPANSION_CEILING_PCT,
    SUBSIDY_CEILING_PCT,
)

random.seed(42)

FIRST_NAMES = ["Maria", "James", "Linh", "Carlos", "Aisha", "David", "Priya", "Noah"]
LAST_NAMES = ["Garcia", "Smith", "Nguyen", "Lopez", "Khan", "Johnson", "Patel", "Brown"]

OUTPUT_FILE = "test_data/eligibility_test_cases.csv"


def income_at_pct_of_fpl(pct: float, family_size: int) -> float:
    """Back-calculates an annual income that lands at a given % of FPL."""
    fpl = fpl_for_household(family_size)
    return round(fpl * (pct / 100), 2)


def random_name():
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def build_test_cases(medicaid_ceiling=MEDICAID_EXPANSION_CEILING_PCT, subsidy_ceiling=SUBSIDY_CEILING_PCT):
    cases = []
    test_id = 1

    for family_size in [1, 2, 4, 6]:
        for ceiling_pct in [medicaid_ceiling, subsidy_ceiling]:
            for offset_pct, label in [(-1.0, "below"), (0.0, "at"), (1.0, "above")]:
                pct = ceiling_pct + offset_pct
                income = income_at_pct_of_fpl(pct, family_size)
                first, last = random_name()
                expected = determine_eligibility(income, family_size, medicaid_ceiling, subsidy_ceiling)
                cases.append({
                    "test_id": f"TC{test_id:03d}",
                    "first_name": first,
                    "last_name": last,
                    "family_size": family_size,
                    "annual_income": income,
                    "scenario": f"family_size={family_size}, {label} {ceiling_pct}% FPL boundary",
                    "expected_eligibility": expected,
                })
                test_id += 1

        for typical_pct, tier_label in [(80.0, "well within Medicaid band"),
                                        (250.0, "well within subsidy band"),
                                        (500.0, "well above subsidy ceiling")]:
            income = income_at_pct_of_fpl(typical_pct, family_size)
            first, last = random_name()
            expected = determine_eligibility(income, family_size, medicaid_ceiling, subsidy_ceiling)
            cases.append({
                "test_id": f"TC{test_id:03d}",
                "first_name": first,
                "last_name": last,
                "family_size": family_size,
                "annual_income": income,
                "scenario": f"family_size={family_size}, {tier_label}",
                "expected_eligibility": expected,
            })
            test_id += 1

    invalid_scenarios = [
        ("negative income", 1, -500.00),
        ("zero family size", 0, 25000.00),
        ("negative family size", -2, 30000.00),
        ("non-numeric income string", 2, "not_an_income"),
        ("non-numeric family size string", "two", 40000.00),
    ]

    for label, fam, inc in invalid_scenarios:
        first, last = random_name()
        cases.append({
            "test_id": f"TC{test_id:03d}",
            "first_name": first,
            "last_name": last,
            "family_size": fam,
            "annual_income": inc,
            "scenario": f"input validation: {label}",
            "expected_eligibility": "INVALID_INPUT",
        })
        test_id += 1

    return cases


def write_csv(cases, path: str = OUTPUT_FILE):
    # Client fix implemented: safely build target tree before opening stream
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    fieldnames = [
        "test_id", "first_name", "last_name", "family_size",
        "annual_income", "scenario", "expected_eligibility",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cases)


if __name__ == "__main__":
    cases = build_test_cases()
    write_csv(cases)
    print(f"Generated {len(cases)} synthetic test cases -> {OUTPUT_FILE}")