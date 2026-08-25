# https://github.com/manoharchalla-inor
# #manoharchalla-in

import uuid
from datetime import datetime, timedelta
import config
from services.database import get_connection
from models.order import Invoice, SalesOrder


class InvoiceService:
    @staticmethod
    def generate_invoice(order: SalesOrder) -> Invoice:
        """
        Generates an invoice with subtotal, tax, shipping, and total calculation.
        Deterministic arithmetic.
        """
        subtotal = order.total_amount
        tax_amount = round(subtotal * config.DEFAULT_TAX_RATE, 2)

        # Shipping fee logic
        if subtotal >= config.HIGH_VALUE_ORDER_THRESHOLD:
            shipping_fee = config.HIGH_VALUE_SHIPPING_FEE
        else:
            shipping_fee = config.STANDARD_SHIPPING_FEE

        total_amount = round(subtotal + tax_amount + shipping_fee, 2)

        invoice_id = f"INV-{uuid.uuid4().hex[:6].upper()}"
        issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        invoice = Invoice(
            invoice_id=invoice_id,
            order_id=order.order_id,
            customer_id=order.customer_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            issue_date=issue_date,
            due_date=due_date,
            status="ISSUED"
        )

        # Persist invoice to DB
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_id, order_id, customer_id, subtotal,
                    tax_amount, shipping_fee, total_amount, issue_date, due_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice.invoice_id,
                invoice.order_id,
                invoice.customer_id,
                invoice.subtotal,
                invoice.tax_amount,
                invoice.shipping_fee,
                invoice.total_amount,
                invoice.issue_date,
                invoice.due_date,
                invoice.status
            ))

            # Update customer total lifetime value
            cursor.execute("""
                UPDATE customers
                SET total_lifetime_value = total_lifetime_value + ?
                WHERE customer_id = ?
            """, (invoice.total_amount, order.customer_id))

            conn.commit()

        return invoice
