# https://github.com/manoharchalla-inor
# #manoharchalla-in

from typing import List, Dict, Any
from services.inventory_service import InventoryService
from models.results import InventoryCheckResult


class InventoryAgent:
    """
    Specialist Agent 2: Inventory Agent
    Responsibility: Check requested quantities against mock inventory and identify shortages.
    Rule: Pure deterministic lookup/arithmetic — NO LLM.
    """
    def __init__(self):
        self.agent_name = "INVENTORY_AGENT"

    def process(self, order_items: List[Dict[str, Any]]) -> InventoryCheckResult:
        return InventoryService.check_inventory(order_items)
