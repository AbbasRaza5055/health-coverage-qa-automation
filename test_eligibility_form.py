"""
test_eligibility_form.py

Data-driven Selenium test: reads every row of test_data/eligibility_test_cases.csv
(the synthetic "grid" of demographic/income/family-size data) and, for each
row, drives the eligibility intake form exactly the way a real applicant
would -- filling in first name, last name, family size, and income -- then
asserts the displayed result matches the expected_eligibility column from
the CSV.

This is the automated equivalent of the manual process of filling in a
two-line grid with made-up applicant data row by row to validate an
income-based eligibility determination: same underlying QA pattern
(boundary-focused, data-driven test design), but driven by pytest +
Selenium instead of manual data entry, and with results logged to a
report file instead of eyeballed one row at a time.

Run with:
    python generate_test_data.py        # (re)generate the CSV grid first
    pytest test_eligibility_form.py -v

Requires Chrome + chromedriver (webdriver-manager handles the driver).
"""


import csv
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from eligibility_rules import determine_eligibility_broken

HERE = os.path.dirname(os.path.abspath(__file__))

# --- SMART PATH RESOLUTION ---
_form_sub = os.path.join(HERE, "test_pages", "eligibility_form.html")
_form_flat = os.path.join(HERE, "eligibility_form.html")
FORM_PATH = _form_sub if os.path.exists(_form_sub) else _form_flat
FORM_URL = "file://" + FORM_PATH

_csv_flat = os.path.join(HERE, "eligibility_test_cases.csv")
_csv_sub = os.path.join(HERE, "test_data", "eligibility_test_cases.csv")
CSV_PATH = _csv_flat if os.path.exists(_csv_flat) else _csv_sub

RESULTS_LOG = os.path.join(HERE, "test_results.csv")


def load_test_cases():
    if not os.path.exists(CSV_PATH):
        print(f"\n[Notice] Target grid {CSV_PATH} not found. Auto-generating fresh synthetic dataset...")
        from generate_test_data import build_test_cases, write_csv
        write_csv(build_test_cases(), path=CSV_PATH)

    with open(CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-sh (m-usage")
    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    yield drv
    drv.quit()


@pytest.fixture(scope="module")
def results_logger():
    rows = []
    yield rows
    if rows:
        with open(RESULTS_LOG, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nTest execution log written to: {RESULTS_LOG}")


@pytest.mark.parametrize("case", load_test_cases(), ids=lambda c: c["test_id"])
def test_eligibility_case(driver, results_logger, case):
    driver.get(FORM_URL)

    driver.find_element(By.ID, "first-name-input").send_keys(case["first_name"])
    driver.find_element(By.ID, "last-name-input").send_keys(case["last_name"])
    driver.find_element(By.ID, "family-size-input").send_keys(case["family_size"])
    driver.find_element(By.ID, "income-input").send_keys(case["annual_income"])
    driver.find_element(By.ID, "submit-eligibility-btn").click()

    result_text = driver.find_element(By.ID, "eligibility-result").text
    actual = result_text.replace("Eligibility Result: ", "").strip()
    expected = case["expected_eligibility"]

    passed = actual == expected
    results_logger.append({
        "test_id": case["test_id"],
        "scenario": case["scenario"],
        "family_size": case["family_size"],
        "annual_income": case["annual_income"],
        "expected": expected,
        "actual": actual,
        "result": "PASS" if passed else "FAIL",
    })

    assert passed, (
        f"{case['test_id']} ({case['scenario']}): expected {expected}, got {actual}"
    )


def test_parameterized_policy_change(driver):
    driver.get(f"{FORM_URL}?medicaid=130&subsidy=350")
    driver.find_element(By.ID, "first-name-input").send_keys("Policy")
    driver.find_element(By.ID, "last-name-input").send_keys("Shift")
    driver.find_element(By.ID, "family-size-input").send_keys("1")
    driver.find_element(By.ID, "income-input").send_keys("20331")
    driver.find_element(By.ID, "submit-eligibility-btn").click()

    result = driver.find_element(By.ID, "eligibility-result").text.replace("Eligibility Result: ", "").strip()
    assert result == "SUBSIDY_ELIGIBLE", f"Parameterized rule override failed: got {result}"


# --- LAYER 1: UNIT REGRESSION TEST (Python Logic Catch) ---
def test_broken_rules_engine_regression_caught():
    boundary_income = 20782.8
    fam_size = 1
    broken_outcome = determine_eligibility_broken(boundary_income, fam_size)
    assert broken_outcome == "SUBSIDY_ELIGIBLE", "Broken engine failed to manifest the exact boundary regression!"


# --- LAYER 2: E2E REGRESSION TEST (Selenium UI Catch - Fix) ---
def test_broken_rules_engine_regression_caught_via_ui(driver):
    """
    Drives the actual form in broken mode (?broken=true) using an exact
    boundary test case from the CSV, proving the data-driven Selenium
    suite catches the off-by-one UI regression — not just the Python logic.
    """
    driver.get(f"{FORM_URL}?broken=true")

    # TC002: family_size=1, exactly at 138% FPL boundary -> should be MEDICAID_ELIGIBLE
    driver.find_element(By.ID, "first-name-input").send_keys("Boundary")
    driver.find_element(By.ID, "last-name-input").send_keys("Case")
    driver.find_element(By.ID, "family-size-input").send_keys("1")
    driver.find_element(By.ID, "income-input").send_keys("20782.8")
    driver.find_element(By.ID, "submit-eligibility-btn").click()

    result = driver.find_element(By.ID, "eligibility-result").text.replace(
        "Eligibility Result: ", ""
    ).strip()

    # Broken engine uses strict < instead of <=, so the exact-boundary case
    # incorrectly falls through to SUBSIDY_ELIGIBLE instead of MEDICAID_ELIGIBLE
    assert result == "SUBSIDY_ELIGIBLE", (
        f"Expected the off-by-one regression to misclassify the boundary case, got {result}"
    )