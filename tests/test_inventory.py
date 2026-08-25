# https://github.com/manoharchalla-inor
# #manoharchalla-in

import pytest
from data.seed_data import seed_database
from agents.inventory_agent import InventoryAgent


@pytest.fixture(autouse=True)
def setup_db():
    seed_database()


def test_sufficient_inventory_check():
    agent = InventoryAgent()
    items = [{"product_id": "P1001", "quantity": 3, "unit_price": 2500.00}]
    result = agent.process(items)
    assert result.status == "sufficient_inventory"
    assert len(result.items) == 0


def test_insufficient_inventory_check():
    agent = InventoryAgent()
    # P1002 stock is 4 in seed data
    items = [{"product_id": "P1002", "quantity": 10, "unit_price": 1200.00}]
    result = agent.process(items)
    assert result.status == "insufficient_inventory"
    assert len(result.items) == 1
    shortage = result.items[0]
    assert shortage.product_id == "P1002"
    assert shortage.requested == 10
    assert shortage.available == 4
    assert shortage.shortage == 6
