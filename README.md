# Multi-Agent Order-to-Cash (O2C) Orchestrator

> **Supervity Forward Deployed Engineer Technical Assessment (Problem 5)**  
> An enterprise-grade, deterministic multi-agent system built with Python, Streamlit, SQLite, and Pydantic for end-to-end sales order processing, inventory checking, payment risk evaluation, and automated invoicing.

---

## 1. Problem Statement

Processes a sales order end-to-end through specialized steps: validate the order, check inventory against mock database stock, calculate credit payment risk, generate an invoice when appropriate, and route exceptions (such as insufficient inventory or high credit risk) to human review queues with complete execution traceability.

---

## 2. Architecture & Component Roles

```
User / Streamlit UI
       ↓
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

### Component Ownership

* **Orchestrator (`OrderToCashOrchestrator`)**: Controls workflow state transitions, sequencing, exception routing, real-time agent handoffs, and audit logging. Agents never call each other directly.
* **Order Validation Agent (`OrderValidationAgent`)**: Specialist agent that validates order structure, customer existence, catalog product IDs, positive quantities, and unit price integrity.
* **Inventory Agent (`InventoryAgent`)**: Specialist agent that checks stock levels in SQLite, calculates shortages per item, and determines availability.
* **Payment Risk Agent (`PaymentRiskAgent`)**: Specialist agent that calculates a deterministic credit risk score (0–100) based on credit rating, unpaid invoice count, overdue payment history, and order value thresholds.
* **Invoice Service (`InvoiceService`)**: Business service that calculates subtotals, 8% tax, shipping fees, generates invoice records, and updates customer lifetime value **only after all validation, inventory, and risk checks pass**.
* **SQLite Database**: Persistent relational database storing synthetic customers, catalog products, inventory stock, order items, issued invoices, and step audit logs (`agent_logs`).
* **Optional LLM Narration**: OpenAI GPT model used **exclusively** downstream to produce natural-language executive summaries over verified deterministic facts. *(Not used for math, validation, risk scoring, or financial logic; do not claim every component is an AI agent).*

---

## 3. Workflow State Machine & Exception Paths

### Standard Workflow Pipeline
```
ORDER_RECEIVED → VALIDATING → INVENTORY_CHECK → PAYMENT_RISK → INVOICE_GENERATION → COMPLETED
```

### Exception Branch Routing
1. **Validation Failure** (`VALIDATION_FAILED` → `REJECTED`):
   - Trigger: Invalid product ID, negative quantity, missing customer.
   - Outcome: Order is immediately `REJECTED`. Execution stops before inventory or payment risk evaluation.
2. **Insufficient Inventory** (`INSUFFICIENT_INVENTORY` → `HUMAN_REVIEW`):
   - Trigger: Requested quantity > available stock (e.g. requesting 10 switches when stock is 4).
   - Outcome: Order is escalated to `HUMAN_REVIEW`. Stock is not reserved, and **no invoice is generated**.
3. **High Payment Risk** (`PAYMENT_RISK_ESCALATION` → `HUMAN_REVIEW`):
   - Trigger: Payment risk score $\ge 70.0$ (configured threshold).
   - Outcome: Order is escalated to `HUMAN_REVIEW` credit queue. **No invoice is generated**.

---

## 4. Design Assumptions

* **Synthetic Mock Data**: All customer, product, inventory, and payment records are synthetic/mock data stored in SQLite.
* **Persistence Layer**: SQLite is used as the transactional persistence layer for this MVP.
* **Deterministic Computations**: Inventory checking, shortage calculation, invoice math, and payment risk scoring are 100% deterministic algorithms.
* **Insufficient Inventory Routing**: Orders encountering inventory shortages are routed to Human Review (`HUMAN_REVIEW`).
* **Payment Risk Threshold**: Payment risk scores $\ge 70.0$ are automatically routed to Human Review (`HUMAN_REVIEW`).
* **Conditional Invoicing**: Invoice generation occurs **only after** required validation, inventory, and payment risk checks pass cleanly.
* **Optional LLM Usage**: LLM usage is optional and limited to natural-language narration. If no API key is present, the app gracefully degrades to templated narrative summaries.

---

## 5. Technology Stack

- **Python 3.11+**
- **Streamlit** (Web UI & Executive Dashboard)
- **SQLite3** (Transactional Mock Database & Audit Trail)
- **Pydantic v2** (Structured Data Schemas & Models)
- **Pandas** (Tabular Data Explorer & Metric Displays)
- **Pytest** (Automated Unit & Integration Test Suite)
- **OpenAI API** (Optional natural-language narration)

---

## 6. Setup & Execution Instructions

### Installation
```bash
# 1. Navigate to project root
cd "e:/Multi-Agent Order-to-Cash Orchestrator -by manohar"

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Seed mock database with synthetic test records
python data/seed_data.py

# 4. Run automated test suite (9/9 passed)
python -m pytest -v

# 5. Launch Streamlit Web UI
python -m streamlit run app.py
```

### Environment Variables
Copy `.env.example` to `.env` (optional):
```env
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 7. Demo Scenarios (1-Click Launchers in UI)

* **Scenario 1: Successful Order**
  - Customer: `CUST-101` (Apex Global Solutions, EXCELLENT credit)
  - Product: `P1001` (Industrial Server Rack, Qty: 2)
  - Result: Validation PASS $\rightarrow$ Inventory PASS $\rightarrow$ Risk PASS $\rightarrow$ Invoice `INV-XXXXXX` Issued $\rightarrow$ State: `COMPLETED`.
* **Scenario 2: Insufficient Inventory**
  - Customer: `CUST-101`
  - Product: `P1002` (Enterprise Core Switch, Qty Requested: 10, Available: 4)
  - Result: Validation PASS $\rightarrow$ Inventory SHORTAGE (Shortage: 6) $\rightarrow$ State: `HUMAN_REVIEW` $\rightarrow$ No Invoice Issued.
* **Scenario 3: High Payment Risk**
  - Customer: `CUST-103` (Delta Heavy Industries, POOR credit, 3 overdue payments)
  - Product: `P1001` (Qty: 5 = $12,500 total)
  - Result: Validation PASS $\rightarrow$ Inventory PASS $\rightarrow$ Payment Risk HIGH (Score: 85.0/100 $\ge 70$) $\rightarrow$ State: `HUMAN_REVIEW` $\rightarrow$ No Invoice Issued.

---

## 8. 5-Minute Evaluator Demo Script

1. **Architecture & Scope (1 min)**: Point out the state machine orchestrator delegating to specialist agents while keeping financial/inventory logic 100% deterministic.
2. **Scenario 1 Run (1 min)**: Click **Scenario 1: Successful Order**. View the generated **INVOICE GENERATED** card showing itemized subtotal, tax, shipping, and total. Show the dynamic green pipeline steps.
3. **Scenario 2 Run (1 min)**: Click **Scenario 2: Inventory Shortage**. Note that the pipeline stops at Inventory with a `SHORTAGE` warning and routes to `HUMAN_REVIEW`. Highlight that **no invoice was generated**.
4. **Scenario 3 Run (1 min)**: Click **Scenario 3: High Payment Risk**. Note that the risk score of 85.0/100 triggers `HUMAN_REVIEW`. Highlight the risk factors.
5. **Audit Inspector & Data Explorer (1 min)**: Open **Audit Trail Inspector** tab to view the persisted `agent_logs` SQLite table with From Agent, To Agent, Step, Status, and Timestamp.

---

## 9. Why Genuine Multi-Agent Architecture vs. Monolithic LLM Prompt

1. **Mathematical Accuracy**: In enterprise Order-to-Cash workflows, invoice totals, tax calculations, stock subtractions, and credit risk scoring cannot tolerate LLM hallucinations or rounding drift.
2. **Strict Handoff Auditability**: The Orchestrator logs explicit step transitions (`From Agent → To Agent`) with structured JSON inputs and outputs in SQLite.
3. **Fault Isolation**: If inventory stock is insufficient, execution halts immediately without wasting tokens or evaluating credit risk on an unfillable order.
