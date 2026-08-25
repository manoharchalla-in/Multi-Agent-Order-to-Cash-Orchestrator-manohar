# https://github.com/manoharchalla-inor
# #manoharchalla-in

from typing import Dict, Any, List
from services.database import get_connection
from models.results import ValidationResult


class OrderValidationAgent:
    """
    Specialist Agent 1: Order Validation Agent
    Responsibility: Validate customer info, product IDs, quantities, prices, required fields.
    Rule: Pure deterministic validation — NO LLM.
    """
    def __init__(self):
        self.agent_name = "ORDER_VALIDATION_AGENT"

    def process(self, order_data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        validated_total = 0.0

        customer_id = order_data.get("customer_id")
        items = order_data.get("items", [])

        # 1. Customer Check
        if not customer_id:
            errors.append("Customer ID is missing from order request.")
        else:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT customer_id, company_name FROM customers WHERE customer_id = ?", (customer_id,))
                customer = cursor.fetchone()
                if not customer:
                    errors.append(f"Customer ID '{customer_id}' does not exist in database.")

        # 2. Items List Check
        if not items or len(items) == 0:
            errors.append("Order must contain at least one item.")
        else:
            with get_connection() as conn:
                cursor = conn.cursor()
                for idx, item in enumerate(items, 1):
                    product_id = item.get("product_id")
                    quantity = item.get("quantity", 0)
                    unit_price = item.get("unit_price", 0.0)

                    if not product_id:
                        errors.append(f"Item #{idx}: Product ID is missing.")
                        continue

                    if quantity <= 0:
                        errors.append(f"Item #{idx} ({product_id}): Quantity must be greater than 0. Found {quantity}.")

                    if unit_price <= 0:
                        errors.append(f"Item #{idx} ({product_id}): Unit price must be greater than 0. Found {unit_price}.")

                    # Validate Product in DB
                    cursor.execute("SELECT name, unit_price FROM products WHERE product_id = ?", (product_id,))
                    product = cursor.fetchone()
                    if not product:
                        errors.append(f"Item #{idx}: Product '{product_id}' does not exist in catalog.")
                    else:
                        expected_price = product["unit_price"]
                        if abs(unit_price - expected_price) > 0.01:
                            warnings.append(
                                f"Item #{idx} ({product_id}): Submitted unit price ({unit_price}) differs from catalog price ({expected_price})."
                            )

                    if quantity > 0 and unit_price > 0:
                        validated_total += round(quantity * unit_price, 2)

        status = "approved" if len(errors) == 0 else "rejected"
        return ValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
            validated_total=round(validated_total, 2)
        )
