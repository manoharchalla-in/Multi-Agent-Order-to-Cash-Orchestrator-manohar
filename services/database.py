# https://github.com/manoharchalla-inor
# #manoharchalla-in

import sqlite3
import json
from typing import Dict, Any, List, Optional
import config


def get_connection():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Customers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                credit_rating TEXT NOT NULL,
                unpaid_invoices_count INTEGER DEFAULT 0,
                has_overdue_payments INTEGER DEFAULT 0,
                total_lifetime_value REAL DEFAULT 0.0
            )
        """)

        # Products Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                unit_price REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT DEFAULT ''
            )
        """)

        # Inventory Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                product_id TEXT PRIMARY KEY,
                available_quantity INTEGER NOT NULL,
                reserved_quantity INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)

        # Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        """)

        # Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)

        # Payment History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                invoice_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL, -- PAID, OVERDUE, PENDING
                due_date TEXT NOT NULL,
                paid_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        """)

        # Invoices Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                subtotal REAL NOT NULL,
                tax_amount REAL NOT NULL,
                shipping_fee REAL NOT NULL,
                total_amount REAL NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        """)

        # Agent Logs Table (Audit Trail)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                step_name TEXT NOT NULL,
                input_payload TEXT,
                output_payload TEXT,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        conn.commit()


def save_agent_log(
    order_id: str,
    from_agent: str,
    to_agent: str,
    step_name: str,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    decision: str,
    reason: str,
    status: str,
    timestamp: str
):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_logs (
                order_id, timestamp, from_agent, to_agent, step_name,
                input_payload, output_payload, decision, reason, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            timestamp,
            from_agent,
            to_agent,
            step_name,
            json.dumps(input_payload),
            json.dumps(output_payload),
            decision,
            reason,
            status
        ))
        conn.commit()


def get_agent_logs_by_order(order_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_logs WHERE order_id = ? ORDER BY id ASC", (order_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["input_payload"] = json.loads(d["input_payload"]) if d["input_payload"] else {}
            except Exception:
                pass
            try:
                d["output_payload"] = json.loads(d["output_payload"]) if d["output_payload"] else {}
            except Exception:
                pass
            result.append(d)
        return result
