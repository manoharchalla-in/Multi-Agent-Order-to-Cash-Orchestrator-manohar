# https://github.com/manoharchalla-inor
# #manoharchalla-in

from typing import List, Dict, Any
from services.database import get_connection
from models.results import InventoryCheckResult, InventoryShortageItem


class InventoryService:
    @staticmethod
    def check_inventory(order_items: List[Dict[str, Any]]) -> InventoryCheckResult:
        """
        Check requested quantities against available stock in SQLite.
        Pure deterministic lookup & arithmetic. No LLM.
        """
        shortages: List[InventoryShortageItem] = []
        details: List[Dict[str, Any]] = []

        with get_connection() as conn:
            cursor = conn.cursor()

            for item in order_items:
                product_id = item.get("product_id")
                requested_qty = item.get("quantity", 0)

                cursor.execute("""
                    SELECT p.name, i.available_quantity, i.reserved_quantity
                    FROM inventory i
                    JOIN products p ON i.product_id = p.product_id
                    WHERE i.product_id = ?
                """, (product_id,))
                row = cursor.fetchone()

                if not row:
                    shortages.append(InventoryShortageItem(
                        product_id=product_id,
                        product_name="Unknown Product",
                        requested=requested_qty,
                        available=0,
                        shortage=requested_qty
                    ))
                    details.append({
                        "product_id": product_id,
                        "product_name": "Unknown Product",
                        "requested": requested_qty,
                        "available": 0,
                        "status": "NOT_FOUND"
                    })
                else:
                    product_name = row["name"]
                    available_qty = row["available_quantity"]

                    if requested_qty > available_qty:
                        shortage_qty = requested_qty - available_qty
                        shortages.append(InventoryShortageItem(
                            product_id=product_id,
                            product_name=product_name,
                            requested=requested_qty,
                            available=available_qty,
                            shortage=shortage_qty
                        ))
                        details.append({
                            "product_id": product_id,
                            "product_name": product_name,
                            "requested": requested_qty,
                            "available": available_qty,
                            "shortage": shortage_qty,
                            "status": "SHORTAGE"
                        })
                    else:
                        details.append({
                            "product_id": product_id,
                            "product_name": product_name,
                            "requested": requested_qty,
                            "available": available_qty,
                            "status": "SUFFICIENT"
                        })

        status = "insufficient_inventory" if len(shortages) > 0 else "sufficient_inventory"
        return InventoryCheckResult(
            status=status,
            items=shortages,
            details=details
        )

    @staticmethod
    def reserve_inventory(order_items: List[Dict[str, Any]]) -> bool:
        """
        Deduct available stock and increase reserved stock for fulfilled items.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            for item in order_items:
                product_id = item.get("product_id")
                qty = item.get("quantity", 0)

                cursor.execute("""
                    UPDATE inventory
                    SET available_quantity = available_quantity - ?,
                        reserved_quantity = reserved_quantity + ?
                    WHERE product_id = ? AND available_quantity >= ?
                """, (qty, qty, product_id, qty))

            conn.commit()
            return True
