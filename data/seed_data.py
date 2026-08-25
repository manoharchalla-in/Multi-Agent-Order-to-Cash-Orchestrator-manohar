# https://github.com/manoharchalla-inor
# #manoharchalla-in

from services.database import get_connection, init_db


def seed_database():
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Clean existing mock data
        cursor.execute("DELETE FROM customers")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM inventory")
        cursor.execute("DELETE FROM payment_history")

        # Seed Customers
        customers = [
            ("CUST-101", "Apex Global Solutions", "billing@apexglobal.com", "EXCELLENT", 0, 0, 150000.00),
            ("CUST-102", "Beta Logistics Inc", "ap@betalogistics.com", "FAIR", 1, 0, 45000.00),
            ("CUST-103", "Delta Heavy Industries", "finance@deltaheavy.com", "POOR", 3, 1, 12000.00),
        ]
        cursor.executemany("""
            INSERT INTO customers (
                customer_id, company_name, contact_email, credit_rating,
                unpaid_invoices_count, has_overdue_payments, total_lifetime_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, customers)

        # Seed Products
        products = [
            ("P1001", "Industrial Server Rack", 2500.00, "Hardware", "42U Heavy Duty Server Cabinet"),
            ("P1002", "Enterprise Core Switch", 1200.00, "Networking", "48-Port Managed Switch (Limited Stock)"),
            ("P1003", "Fiber Optic Cable Unit", 150.00, "Networking", "100m High Density Fiber Cable"),
            ("P1004", "Smart UPS Battery Pack", 800.00, "Power", "3000VA Rackmount Uninterruptible Power Supply"),
        ]
        cursor.executemany("""
            INSERT INTO products (
                product_id, name, unit_price, category, description
            ) VALUES (?, ?, ?, ?, ?)
        """, products)

        # Seed Inventory
        # Note: P1002 has only 4 available units to test Scenario 2 (Insufficient Inventory)
        inventory = [
            ("P1001", 15, 0, 5),
            ("P1002", 4, 0, 10),
            ("P1003", 200, 0, 20),
            ("P1004", 50, 0, 5),
        ]
        cursor.executemany("""
            INSERT INTO inventory (
                product_id, available_quantity, reserved_quantity, reorder_level
            ) VALUES (?, ?, ?, ?)
        """, inventory)

        # Seed Payment History for risk evaluation
        payment_records = [
            ("CUST-101", "INV-9001", 5000.00, "PAID", "2026-01-15", "2026-01-10"),
            ("CUST-102", "INV-9002", 12000.00, "PAID", "2026-02-01", "2026-01-28"),
            ("CUST-102", "INV-9003", 4500.00, "PENDING", "2026-09-15", None),
            ("CUST-103", "INV-8001", 8500.00, "OVERDUE", "2026-05-01", None),
            ("CUST-103", "INV-8002", 15000.00, "OVERDUE", "2026-06-15", None),
            ("CUST-103", "INV-8003", 9200.00, "OVERDUE", "2026-07-01", None),
        ]
        cursor.executemany("""
            INSERT INTO payment_history (
                customer_id, invoice_id, amount, status, due_date, paid_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, payment_records)

        conn.commit()


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully!")
