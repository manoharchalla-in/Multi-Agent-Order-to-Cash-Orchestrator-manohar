# https://github.com/manoharchalla-inor
# #manoharchalla-in

import pytest
from data.seed_data import seed_database
from agents.order_validation_agent import OrderValidationAgent


@pytest.fixture(autouse=True)
def setup_db():
    seed_database()


def test_valid_order_validation():
    agent = OrderValidationAgent()
    val_input = {
        "customer_id": "CUST-101",
        "items": [
            {"product_id": "P1001", "quantity": 2, "unit_price": 2500.00}
        ]
    }
    result = agent.process(val_input)
    assert result.status == "approved"
    assert len(result.errors) == 0
    assert result.validated_total == 5000.00


def test_invalid_customer_validation():
    agent = OrderValidationAgent()
    val_input = {
        "customer_id": "CUST-NONEXISTENT",
        "items": [
            {"product_id": "P1001", "quantity": 1, "unit_price": 2500.00}
        ]
    }
    result = agent.process(val_input)
    assert result.status == "rejected"
    assert any("does not exist in database" in err for err in result.errors)


def test_invalid_product_and_negative_quantity():
    agent = OrderValidationAgent()
    val_input = {
        "customer_id": "CUST-101",
        "items": [
            {"product_id": "P9999", "quantity": -5, "unit_price": 100.00}
        ]
    }
    result = agent.process(val_input)
    assert result.status == "rejected"
    assert len(result.errors) >= 2
