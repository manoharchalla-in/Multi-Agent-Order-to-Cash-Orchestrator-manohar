# https://github.com/manoharchalla-inor
# #manoharchalla-in

from typing import List, Dict, Any, Tuple
import config
from services.database import get_connection
from models.agent_state import RiskLevel
from models.results import PaymentRiskResult


class RiskService:
    @staticmethod
    def calculate_payment_risk(customer_id: str, order_total: float) -> PaymentRiskResult:
        """
        Calculate payment risk score (0 - 100) deterministically.
        Inputs: Customer credit rating, unpaid invoices, overdue status, order value threshold.
        No LLM is used to compute the score.
        """
        score = 0.0
        reasons: List[str] = []

        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Fetch customer details
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
            customer = cursor.fetchone()

            if not customer:
                return PaymentRiskResult(
                    risk_level=RiskLevel.HIGH,
                    risk_score=100.0,
                    reasons=["Customer record not found in system"],
                    explanation="High risk flagged because customer ID is unverified or missing."
                )

            # Credit Rating base score additions
            credit_rating = customer["credit_rating"]
            if credit_rating == "POOR":
                score += 40.0
                reasons.append("Customer credit rating is POOR (+40 pts)")
            elif credit_rating == "FAIR":
                score += 20.0
                reasons.append("Customer credit rating is FAIR (+20 pts)")
            elif credit_rating == "GOOD":
                score += 5.0

            # Unpaid Invoices
            unpaid_count = customer["unpaid_invoices_count"]
            if unpaid_count > config.MAX_UNPAID_INVOICES_LIMIT:
                score += 30.0
                reasons.append(f"Customer has {unpaid_count} unpaid invoices exceeding threshold of {config.MAX_UNPAID_INVOICES_LIMIT} (+30 pts)")
            elif unpaid_count > 0:
                score += (unpaid_count * 10.0)
                reasons.append(f"Customer has {unpaid_count} active unpaid invoice(s) (+{unpaid_count * 10} pts)")

            # Overdue Payments flag
            has_overdue = bool(customer["has_overdue_payments"])
            if has_overdue:
                score += 25.0
                reasons.append("Customer has flagged overdue payment history (+25 pts)")

            # 2. Check overdue records in payment_history table
            cursor.execute("""
                SELECT COUNT(*) as count FROM payment_history
                WHERE customer_id = ? AND status = 'OVERDUE'
            """, (customer_id,))
            overdue_row = cursor.fetchone()
            overdue_count = overdue_row["count"] if overdue_row else 0
            if overdue_count > 0 and not has_overdue:
                score += 15.0
                reasons.append(f"Found {overdue_count} overdue payment transaction(s) in history (+15 pts)")

            # 3. Order Value Threshold Check
            if order_total > config.HIGH_VALUE_ORDER_THRESHOLD:
                score += 20.0
                reasons.append(f"Order total ({config.CURRENCY_SYMBOL}{order_total:,.2f}) exceeds high-value threshold of {config.CURRENCY_SYMBOL}{config.HIGH_VALUE_ORDER_THRESHOLD:,.2f} (+20 pts)")

        # Cap score at 100
        score = min(100.0, score)

        # Classify Risk Level
        if score >= config.PAYMENT_RISK_THRESHOLD:
            risk_level = RiskLevel.HIGH
        elif score >= 40.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        if not reasons:
            reasons.append("Customer has clean payment history and low order value.")

        return PaymentRiskResult(
            risk_level=risk_level,
            risk_score=score,
            reasons=reasons,
            explanation=None
        )
