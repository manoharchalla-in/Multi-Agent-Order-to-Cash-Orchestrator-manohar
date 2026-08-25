<p align="center">
  <img src="https://img.shields.io/badge/⚡_MULTI--AGENT-ORDER--TO--CASH_ORCHESTRATOR-0F172A?style=for-the-badge&logo=workflow&logoColor=38BDF8" alt="O2C Title Banner">
</p>

<p align="center">
  <strong>Supervity Forward Deployed Engineer Technical Assessment (Problem 5)</strong><br>
  <em>An enterprise-grade, deterministic multi-agent state machine orchestrator for sales order validation, inventory verification, credit payment risk scoring, and automated invoicing.</em>
</p>

<p align="center">
  <a href="https://github.com/manoharchalla-in/Multi-Agent-Order-to-Cash-Orchestrator-manohar"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"></a>
  <a href="https://sqlite.org"><img src="https://img.shields.io/badge/SQLite3-Transactional-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"></a>
  <a href="https://docs.pydantic.dev"><img src="https://img.shields.io/badge/Pydantic-v2.5+-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic"></a>
  <a href="https://pytest.org"><img src="https://img.shields.io/badge/Pytest-9/9_Passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest"></a>
  <a href="https://github.com/manoharchalla-in/Multi-Agent-Order-to-Cash-Orchestrator-manohar"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"></a>
</p>

---

## 📌 Navigation & Quick Links

<p align="center">
  <a href="INTERVIEW_GUIDE.md"><img src="https://img.shields.io/badge/🎯_INTERVIEW_DEFENSE_GUIDE-059669?style=for-the-badge&logo=readme&logoColor=white" alt="Interview Guide"></a>
  <a href="#1-problem-statement"><img src="https://img.shields.io/badge/📋_Problem_Statement-0F172A?style=for-the-badge" alt="Problem Statement"></a>
  <a href="#2-system-architecture--delegation-pattern"><img src="https://img.shields.io/badge/🏗️_Architecture-0F172A?style=for-the-badge" alt="Architecture"></a>
  <a href="#3-specialist-agent-ownership"><img src="https://img.shields.io/badge/🤖_Specialist_Agents-0F172A?style=for-the-badge" alt="Specialist Agents"></a>
  <a href="#4-deterministic-logic-vs-llm-reasoning"><img src="https://img.shields.io/badge/⚖️_Design_Tradeoff-0F172A?style=for-the-badge" alt="Design Tradeoff"></a>
  <a href="#5-design-assumptions"><img src="https://img.shields.io/badge/📝_Design_Assumptions-0F172A?style=for-the-badge" alt="Design Assumptions"></a>
  <a href="#6-demo-scenarios-walkthrough"><img src="https://img.shields.io/badge/🚀_Demo_Scenarios-0F172A?style=for-the-badge" alt="Demo Scenarios"></a>
  <a href="#7-5-minute-evaluator-demo-script"><img src="https://img.shields.io/badge/⏱️_Evaluator_Script-0F172A?style=for-the-badge" alt="Evaluator Script"></a>
  <a href="#8-quickstart--installation"><img src="https://img.shields.io/badge/⚡_Quickstart-0F172A?style=for-the-badge" alt="Quickstart"></a>
</p>

> 📖 **Interview Readiness Guide**: For a detailed 30-second pitch, 5-minute live screen-share walkthrough, agent code breakdown, and 12 technical interviewer Q&As, read the **[`INTERVIEW_GUIDE.md`](INTERVIEW_GUIDE.md)** document.

---

## 1. Problem Statement

Processes a sales order end-to-end through specialized steps: validate customer & product data, check inventory stock against a mock database, calculate deterministic payment risk, generate an itemized invoice, and route exception paths (such as stock shortages or high credit risk) to human review queues with complete execution traceability.

```
User → Streamlit UI → Orchestrator → Specialist Agents → Business Services / SQLite → Invoice & Audit Trail
```

---

## 2. System Architecture & Delegation Pattern

```
[User / Streamlit UI Dashboard]
               │
               ▼
┌────────────────────────────────────────────────────────┐
│             Order-to-Cash Orchestrator                 │
│              (Explicit State Machine)                  │
└───────┬───────────────────┬───────────────────┬────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Validation   │   │   Inventory   │   │ Payment Risk  │
│     Agent     │   │     Agent     │   │     Agent     │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
           ┌──────────────────────────────────┐
           │ Business Services & SQLite DB    │
           │ (Inventory, Risk, Invoices, Logs) │
           └──────────────────────────────────┘
```

### Standard Pipeline Execution
```
ORDER_RECEIVED → VALIDATING → INVENTORY_CHECK → PAYMENT_RISK → INVOICE_GENERATION → COMPLETED
```

### Exception Branch Routing
- **Validation Failure** (`VALIDATION_FAILED` → `REJECTED`): Invalid product ID, negative quantity, or missing customer halts execution immediately.
- **Inventory Shortage** (`INSUFFICIENT_INVENTORY` → `HUMAN_REVIEW`): Requested quantity exceeds stock; routes to human review queue without generating an invoice.
- **High Payment Risk** (`PAYMENT_RISK_ESCALATION` → `HUMAN_REVIEW`): Payment risk score ≥ 70.0 routes to human credit review queue without generating an invoice.

---

## 3. Specialist Agent Ownership

| Component | Architecture Role | Discrete Responsibilities |
| :--- | :--- | :--- |
| **Orchestrator** | State Machine | Controls workflow state transitions, sequencing, exception routing, real-time agent handoff logging, and audit trail persistence. Agents never call each other directly. |
| **Order Validation Agent** | Specialist Agent | Validates order structure, customer existence, catalog product IDs, positive quantities, and unit price integrity. Pure deterministic logic. |
| **Inventory Agent** | Specialist Agent | Checks stock levels in SQLite, calculates shortages per item, and determines availability. Pure deterministic arithmetic. |
| **Payment Risk Agent** | Specialist Agent | Calculates deterministic credit risk score (0–100) based on credit rating, unpaid invoice count, overdue payment history, and order value thresholds. |
| **Invoice Service** | Business Service | Generates subtotal, 8% tax, shipping fees, invoice records, and updates customer lifetime value **only after all required validation, inventory, and risk checks pass**. |
| **SQLite Database** | Persistence | Stores synthetic customers, catalog products, inventory stock, order items, issued invoices, and step audit logs (`agent_logs`). |
| **Optional LLM Layer** | Narration Engine | OpenAI GPT model used **exclusively** downstream to produce natural-language executive summaries over verified deterministic results. *(Not used for math, validation, or risk scoring).* |

---

## 4. Deterministic Logic vs. LLM Reasoning

> **Why use a multi-agent state machine instead of one monolithic LLM prompt?**

1. **Mathematical Accuracy**: Invoice totals, tax calculations, stock subtractions, and credit risk scoring require 100% deterministic precision. Monolithic LLMs risk hallucinating math or missing edge validation rules.
2. **Strict Handoff Auditability**: The Orchestrator logs explicit step transitions (`From Agent → To Agent`) with structured JSON inputs and outputs in SQLite.
3. **Fault Isolation**: If inventory stock is insufficient, execution halts immediately without wasting LLM tokens or evaluating credit risk on an unfillable order.
4. **Graceful Degradation**: If no OpenAI API key is configured, 100% of the workflow operates deterministically using templated summaries.

---

## 5. Design Assumptions

* **Synthetic Mock Data**: All customer, product, inventory, and payment records are synthetic data stored in SQLite.
* **Persistence Layer**: SQLite is used as the transactional persistence layer for this MVP.
* **Deterministic Computations**: Inventory checking, shortage calculation, invoice math, and payment risk scoring are 100% deterministic algorithms.
* **Insufficient Inventory Routing**: Orders encountering inventory shortages are routed to Human Review (`HUMAN_REVIEW`).
* **Payment Risk Threshold**: Payment risk scores ≥ 70.0 are automatically routed to Human Review (`HUMAN_REVIEW`).
* **Conditional Invoicing**: Invoice generation occurs **only after** required validation, inventory, and payment risk checks pass cleanly.
* **Optional LLM Usage**: LLM usage is optional and limited to natural-language narration.

---

## 6. Demo Scenarios Walkthrough

The application includes **3 1-Click Demo Scenarios** in the Streamlit UI:

### Scenario 1 — Successful Order
- **Input**: Customer `CUST-101` (Apex Global Solutions, EXCELLENT credit), Product `P1001` (Industrial Server Rack, Qty: 2 = $5,000).
- **Execution**: Validation PASS → Inventory PASS → Risk PASS (0.0/100) → Invoice `INV-XXXXXX` Generated → State: `COMPLETED`.

### Scenario 2 — Insufficient Inventory
- **Input**: Customer `CUST-101`, Product `P1002` (Enterprise Core Switch, Qty Requested: 10, Available: 4).
- **Execution**: Validation PASS → Inventory FAIL (Shortage: 6) → State: `HUMAN_REVIEW` → **No Invoice Generated**.

### Scenario 3 — High Payment Risk
- **Input**: Customer `CUST-103` (Delta Heavy Industries, POOR credit, 3 overdue payments), Product `P1001` (Qty: 5 = $12,500 total).
- **Execution**: Validation PASS → Inventory PASS → Payment Risk HIGH (Score: 85.0/100 ≥ 70) → State: `HUMAN_REVIEW` → **No Invoice Generated**.

---

## 7. 5-Minute Evaluator Demo Script

1. **Architecture & Scope (1 min)**: Explain how the state machine orchestrator delegates to specialist agents while keeping financial/inventory logic 100% deterministic.
2. **Scenario 1 Run (1 min)**: Click **Scenario 1: Successful Order**. View the generated **INVOICE GENERATED** card showing itemized subtotal, tax, shipping, and total. Show the dynamic green pipeline steps.
3. **Scenario 2 Run (1 min)**: Click **Scenario 2: Inventory Shortage**. Note that the pipeline stops at Inventory with a `SHORTAGE` warning and routes to `HUMAN_REVIEW`. Highlight that **no invoice was generated**.
4. **Scenario 3 Run (1 min)**: Click **Scenario 3: High Payment Risk**. Note that the risk score of 85.0/100 triggers `HUMAN_REVIEW`. Highlight the risk factors.
5. **Audit Inspector & Data Explorer (1 min)**: Open **Audit Trail Inspector** tab to view the persisted `agent_logs` SQLite table with From Agent, To Agent, Step, Status, and Timestamp.

---

## 8. Quickstart & Installation

```bash
# 1. Clone repository
git clone https://github.com/manoharchalla-in/Multi-Agent-Order-to-Cash-Orchestrator-manohar.git
cd Multi-Agent-Order-to-Cash-Orchestrator-manohar

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Seed mock database with synthetic records
python data/seed_data.py

# 4. Run automated Pytest suite (9/9 passed)
python -m pytest -v

# 5. Launch Streamlit Web UI
python -m streamlit run app.py
```

---

## 9. Automated Test Verification

```bash
python -m pytest -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.0.3, pluggy-1.6.0
collected 9 items

tests/test_inventory.py::test_sufficient_inventory_check PASSED          [ 11%]
tests/test_inventory.py::test_insufficient_inventory_check PASSED        [ 22%]
tests/test_orchestrator.py::test_scenario_1_successful_order PASSED      [ 33%]
tests/test_orchestrator.py::test_scenario_2_insufficient_inventory PASSED [ 44%]
tests/test_orchestrator.py::test_scenario_3_high_payment_risk PASSED     [ 55%]
tests/test_orchestrator.py::test_validation_failure_path PASSED          [ 66%]
tests/test_validation.py::test_valid_order_validation PASSED             [ 77%]
tests/test_validation.py::test_invalid_customer_validation PASSED        [ 88%]
tests/test_validation.py::test_invalid_product_and_negative_quantity PASSED [100%]

============================== 9 passed in 0.27s ==============================
```

---

## 📄 License & Attribution

Distributed under the MIT License.

- **Author**: Manohar Challa
- **GitHub**: [manoharchalla-in](https://github.com/manoharchalla-in)
- **Repository**: [Multi-Agent-Order-to-Cash-Orchestrator-manohar](https://github.com/manoharchalla-in/Multi-Agent-Order-to-Cash-Orchestrator-manohar)
