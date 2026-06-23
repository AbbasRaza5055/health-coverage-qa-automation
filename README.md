# 🏥 Health Coverage Intake — E2E QA Automation Suite

![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Selenium](https://img.shields.io/badge/Selenium-4.18+-brightgreen.svg)
![Pytest](https://img.shields.io/badge/Pytest-8.0+-yellow.svg)
![Architecture](https://img.shields.io/badge/Pattern-Data--Driven%20BVA-purple.svg)

An enterprise-grade, data-driven test automation framework built with **Pytest** and **Selenium WebDriver** to validate synthetic health insurance coverage intake portals. 

This framework exercises frontend intake validation, dynamic policy shift overrides, and strict Federal Poverty Level (FPL) qualifying logic against **Boundary-Value Analysis (BVA)** matrices.

---

## 🏗️ System Architecture & Workflow

```text
  [ generate_test_data.py ] ──> ( eligibility_test_cases.csv ) 
                                              │
                                       [ Pytest Engine ]
                                              │ (drives via Selenium)
                                     [ Headless Chrome ] ──> [ eligibility_form.html ]
                                              │
                                     ( Evaluates DOM Output )
                                              │
                                     [ test_results.csv ] (Compiled E2E Execution Log)
```

### Core Testing Pillars

1. **Strict Boundary-Value Analysis (BVA):** The test grid deliberately targets the exact mathematical edges of the 138% (Medicaid) and 400% (Subsidy) FPL ceilings. For every household size, it tests points at precisely **`-1.0% (below)`**, **`0.0% (exact boundary)`**, and **`+1.0% (above)`**.
2. **Dual-Layer Regression Trapping:** Features a dedicated E2E regression trap (`?broken=true` DOM injection) asserting that exact-boundary data catches off-by-one comparison bugs (`<` vs `<=`) at the UI level.
3. **Topology-Agnostic & Auto-Healing:** Engineered to survive flattened batch downloads and fresh, empty git clones. If invoked on a blank machine missing the input data grid, **the Pytest collection hook intercepts the `FileNotFoundError` and auto-compiles the 41-case CSV matrix on the fly.**
4. **Negative & Type Validation Trapping:** Injects negative integers, zero-person households, and non-numeric garbage strings (`"not_an_income"`) to audit frontend `NaN` exception handling.

---

## 📂 Topology

```text
.
├── eligibility_rules.py         # Reference Python rules engine (Ground Truth math)
├── generate_test_data.py        # Programmatic CSV matrix builder (41 scenarios)
├── test_eligibility_form.py     # Master Pytest + Selenium E2E test runner
├── requirements.txt             # Environment dependencies
├── README.md                    # Framework documentation
└── test_pages/
    └── eligibility_form.html    # Standalone intake UI (JS engine & Broken Branch)
```

---

## 🚀 Quickstart

### 1. Environment Spin-up

```bash
git clone https://github.com/YourUsername/health-coverage-qa-automation.git
cd health-coverage-qa-automation

# Initialize virtual environment
python -m venv venv
source venv/bin/activate  # On Windows OS: venv\Scripts\activate

# Install WebDriver & Pytest framework
pip install -r requirements.txt
```

### 2. Execution Playbook

The framework offers four distinct execution hooks depending on the audit target:

#### Option A: Total E2E Sweep (Standard Run)
Generates the matrix and executes all 41 applicants, policy overrides, and unit/UI regression checks.
```bash
pytest test_eligibility_form.py -v
```

#### Option B: The "Chaos Clone" Audit (Tests Auto-Healing)
Deletes the underlying test dataset entirely, then forces Pytest to invoke a test. Proves the test runner catches the missing grid, reconstructs the OS directories, builds the dataset, and passes the test.
```bash
rm -rf test_data/ eligibility_test_cases.csv
pytest test_eligibility_form.py -k "TC001" -s
```

#### Option C: Legislative Policy Shift Audit
Simulates a state policy update overriding standard FPL thresholds (shifting Medicaid to `130%` and Subsidies to `350%`) via URL parameterization to prove the frontend logic responds dynamically to backend state changes.
```bash
pytest test_eligibility_form.py -k "test_parameterized_policy_change" -v
```

#### Option D: UI Regression Trapping Audit
Forces the browser into the `?broken=true` branch (containing an intentional `<` operator regression) to prove that TC002's exact boundary data ($20,782.80) correctly forces an `AssertionError` on DOM misclassification.
```bash
pytest test_eligibility_form.py -k "test_broken_rules_engine_regression_caught_via_ui" -v
```

---

## 📊 The 41-Case Matrix Breakdown

When `generate_test_data.py` is invoked, it structures a synthetic population of 41 applicants distributed across four household tiers `[1, 2, 4, 6]`:

* **12x Happy-Path Cases:** Standard in-band applicants well within Medicaid, Subsidy, or Non-Eligible income brackets.
* **24x Boundary-Inflection Cases:** The core QA asset. Targets the exact ±1% threshold edges where mathematical off-by-one logic failures occur.
* **5x Negative Injections:** Tests system response to `$0.00` family sizes, `-$500.00` incomes, and string-to-float injection attacks.

### Compiled Execution Artifact (`test_results.csv`)
Upon completion of a test run, the framework compiles an artifact in the root directory tracking DOM parity:

| test_id | scenario | expected | actual | result |
| :--- | :--- | :--- | :--- | :--- |
| **TC001** | `family_size=1, below 138% boundary` | `MEDICAID_ELIGIBLE` | `MEDICAID_ELIGIBLE` | `PASS` |
| **TC002** | `family_size=1, at 138% boundary` | `MEDICAID_ELIGIBLE` | `MEDICAID_ELIGIBLE` | `PASS` |
| **TC037** | `input validation: negative income` | `INVALID_INPUT` | `INVALID_INPUT` | `PASS` |

---

## 👨‍💻 Author

**Abbas Raza** *Machine Learning Engineer* * **Specialization:** Autonomous Agent Workflows, Pytest Frameworks, Computer Vision, Deep Learning.
