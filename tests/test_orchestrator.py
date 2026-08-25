# https://github.com/manoharchalla-inor
# #manoharchalla-in

import pytest
from data.seed_data import seed_database
from agents.orchestrator import OrderToCashOrchestrator
from models.agent_state import WorkflowState


@pytest.fixture(autouse=True)
def setup_db():
    seed_database()


def test_scenario_1_successful_order():
    """
    Scenario 1: Customer CUST-101 (Low Risk), Product P1001 (Available Qty 15, Requesting 2).
    Expected: Workflow COMPLETED, Invoice Generated, Stock Reserved.
    """
    orchestrator = OrderToCashOrchestrator()
    items = [{"product_id": "P1001", "quantity": 2, "unit_price": 2500.00}]

    result = orchestrator.process_order(customer_id="CUST-101", items=items)

    assert result.is_success is True
    assert result.final_state == WorkflowState.COMPLETED
    assert result.invoice_id is not None
    assert result.invoice_total > 5000.00  # Subtotal 5000 + tax + shipping
    assert result.invoice_details is not None
    assert result.invoice_details["subtotal"] == 5000.00
    assert result.invoice_details["tax_amount"] == 400.00
    assert result.invoice_details["status"] == "ISSUED"
    assert len(result.handoff_logs) >= 5


def test_scenario_2_insufficient_inventory():
    """
    Scenario 2: Customer CUST-101, Product P1002 (Available Qty 4, Requesting 10).
    Expected: Escalated to HUMAN_REVIEW due to shortage, No Invoice.
    """
    orchestrator = OrderToCashOrchestrator()
    items = [{"product_id": "P1002", "quantity": 10, "unit_price": 1200.00}]

    result = orchestrator.process_order(customer_id="CUST-101", items=items)

    assert result.is_success is False
    assert result.requires_human_review is True
    assert result.final_state == WorkflowState.HUMAN_REVIEW
    assert result.invoice_id is None
    assert result.invoice_details is None
    assert result.inventory_result.status == "insufficient_inventory"


def test_scenario_3_high_payment_risk():
    """
    Scenario 3: Customer CUST-103 (POOR credit, 3 unpaid invoices), Product P1001 (Requesting 5 = $12,500 total).
    Expected: Escalated to HUMAN_REVIEW due to Risk Score >= 70, No Invoice.
    """
    orchestrator = OrderToCashOrchestrator()
    items = [{"product_id": "P1001", "quantity": 5, "unit_price": 2500.00}]

    result = orchestrator.process_order(customer_id="CUST-103", items=items)

    assert result.is_success is False
    assert result.requires_human_review is True
    assert result.final_state == WorkflowState.HUMAN_REVIEW
    assert result.invoice_id is None
    assert result.invoice_details is None
    assert result.risk_result.risk_score >= 70.0


def test_validation_failure_path():
    """
    Invalid customer or invalid product triggers instant rejection.
    """
    orchestrator = OrderToCashOrchestrator()
    items = [{"product_id": "INVALID-ID", "quantity": 1, "unit_price": 100.00}]

    result = orchestrator.process_order(customer_id="CUST-101", items=items)

    assert result.is_success is False
    assert result.final_state == WorkflowState.VALIDATION_FAILED
    assert result.invoice_id is None
    assert result.invoice_details is None
