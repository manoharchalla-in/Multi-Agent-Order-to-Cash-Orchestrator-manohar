# https://github.com/manoharchalla-inor
# #manoharchalla-in

import os
import sqlite3
import pandas as pd
import streamlit as st

import config
from data.seed_data import seed_database
from services.database import get_connection, init_db
from agents.orchestrator import OrderToCashOrchestrator
from models.agent_state import WorkflowState

# -------------------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="Order-to-Cash Multi-Agent Orchestrator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# Theme-Adaptive Universal CSS (Seamless in Light & Dark Mode)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hero Banner Header */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .hero-subtitle {
        font-size: 0.96rem;
        color: #94A3B8 !important;
        margin-top: 0.5rem;
        margin-bottom: 0;
        line-height: 1.5;
    }

    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-live {
        background: rgba(16, 185, 129, 0.2);
        color: #34D399 !important;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .badge-llm {
        background: rgba(56, 189, 248, 0.2);
        color: #38BDF8 !important;
        border: 1px solid rgba(56, 189, 248, 0.4);
    }

    /* Sidebar Status Card (Theme Adaptive) */
    .sidebar-status-card {
        background: var(--secondary-background-color, #F1F5F9);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 12px;
        padding: 14px;
        font-size: 0.85rem;
        color: var(--text-color, #0F172A) !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    
    /* Metric Cards (Theme Adaptive) */
    .glossy-metric-card {
        background: var(--secondary-background-color, #F8FAFC);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 14px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .glossy-metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.5);
    }
    
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.2;
    }
    
    .metric-lbl {
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--text-color, #475569) !important;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.35rem;
    }

    /* Professional Invoice Card (Theme Adaptive) */
    .invoice-card {
        background: var(--secondary-background-color, #F8FAFC);
        border: 2px solid #10B981;
        border-radius: 16px;
        padding: 1.6rem 2rem;
        margin-top: 1.5rem;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.1);
    }

    .invoice-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(148, 163, 184, 0.3);
        padding-bottom: 1rem;
        margin-bottom: 1.2rem;
    }

    .invoice-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #059669 !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .invoice-badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: #059669 !important;
        border: 1px solid #10B981;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .invoice-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.2rem;
    }

    .invoice-field-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text-color, #475569) !important;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .invoice-field-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color, #0F172A) !important;
        margin-top: 0.2rem;
    }

    /* Execution Summary Card */
    .summary-card {
        background: var(--secondary-background-color, #F8FAFC);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.5rem;
    }

    /* Step Pipeline Nodes (Theme Adaptive) */
    .pipeline-step-card {
        background: var(--secondary-background-color, #F8FAFC);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 10px;
        padding: 0.9rem 0.4rem;
        text-align: center;
        color: var(--text-color, #0F172A) !important;
    }
    
    .pipeline-step-success { border-top: 4px solid #10B981; }
    .pipeline-step-warning { border-top: 4px solid #F59E0B; }
    .pipeline-step-error { border-top: 4px solid #EF4444; }
    .pipeline-step-skipped { border-top: 4px solid #64748B; }

    /* Handoff Terminal Box */
    .terminal-container {
        background: #090D16;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #E2E8F0 !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        margin-top: 1rem;
        line-height: 1.7;
        overflow-x: auto;
    }

    .log-info { color: #38BDF8 !important; }
    .log-success { color: #34D399 !important; font-weight: 600; }
    .log-warning { color: #FBBF24 !important; font-weight: 600; }
    .log-error { color: #F87171 !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Ensure DB initialized & seeded if empty
init_db()
try:
    with get_connection() as conn:
        c_count = conn.cursor().execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if c_count == 0:
            seed_database()
except Exception:
    seed_database()

# Session State Initialization
if "last_workflow_result" not in st.session_state:
    st.session_state["last_workflow_result"] = None

# Helper DB Query Functions
def fetch_customers():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT customer_id, company_name, credit_rating, unpaid_invoices_count FROM customers", conn)

def fetch_products():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT p.product_id, p.name, p.unit_price, i.available_quantity
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
        """, conn)

def fetch_kpis():
    with get_connection() as conn:
        orders_df = pd.read_sql_query("SELECT status, total_amount FROM orders", conn)
        invoices_df = pd.read_sql_query("SELECT total_amount FROM invoices", conn)

    total_orders = len(orders_df)
    completed_orders = len(orders_df[orders_df["status"] == WorkflowState.COMPLETED.value])
    review_orders = len(orders_df[orders_df["status"] == WorkflowState.HUMAN_REVIEW.value])
    failed_orders = len(orders_df[orders_df["status"] == WorkflowState.VALIDATION_FAILED.value])
    total_revenue = invoices_df["total_amount"].sum() if not invoices_df.empty else 0.0

    return total_orders, completed_orders, review_orders, failed_orders, total_revenue

# -------------------------------------------------------------
# SIDEBAR CONTROL PANEL
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Control Panel")
    st.caption("Multi-Agent State Machine Orchestrator")

    st.divider()

    st.markdown("#### 🟢 System Status")
    st.markdown("""
    <div class="sidebar-status-card">
        <div>🟢 <b>SQLite DB:</b> Connected & Active</div>
        <div style="margin-top:6px;">⚡ <b>Engine:</b> State Machine Orchestrator</div>
        <div style="margin-top:6px;">{} <b>LLM Layer:</b> {}</div>
    </div>
    """.format(
        "🟢" if config.OPENAI_API_KEY else "ℹ️",
        "OpenAI Enabled" if config.OPENAI_API_KEY else "Templated Fallback"
    ), unsafe_allow_html=True)

    st.divider()

    st.markdown("#### 🚀 1-Click Demo Launcher")
    st.caption("Instantly execute pre-configured workflow scenarios:")

    if st.button("1️⃣ Scenario 1: Successful Order", use_container_width=True):
        orchestrator = OrderToCashOrchestrator()
        items = [{"product_id": "P1001", "quantity": 2, "unit_price": 2500.00}]
        res = orchestrator.process_order("CUST-101", items, notes="Demo Scenario 1: Standard low-risk order")
        st.session_state["last_workflow_result"] = res
        st.rerun()

    if st.button("2️⃣ Scenario 2: Inventory Shortage", use_container_width=True):
        orchestrator = OrderToCashOrchestrator()
        items = [{"product_id": "P1002", "quantity": 10, "unit_price": 1200.00}]
        res = orchestrator.process_order("CUST-101", items, notes="Demo Scenario 2: Shortage escalation")
        st.session_state["last_workflow_result"] = res
        st.rerun()

    if st.button("3️⃣ Scenario 3: High Payment Risk", use_container_width=True):
        orchestrator = OrderToCashOrchestrator()
        items = [{"product_id": "P1001", "quantity": 5, "unit_price": 2500.00}]
        res = orchestrator.process_order("CUST-103", items, notes="Demo Scenario 3: High risk escalation")
        st.session_state["last_workflow_result"] = res
        st.rerun()

    st.divider()

    if st.button("🔄 Reset / Re-seed Mock DB", use_container_width=True):
        seed_database()
        st.session_state["last_workflow_result"] = None
        st.success("Database re-seeded successfully!")
        st.rerun()

# -------------------------------------------------------------
# MAIN DASHBOARD HERO HEADER
# -------------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">
        <span>⚡ Order-to-Cash Multi-Agent Orchestrator</span>
    </div>
    <div class="hero-subtitle">
        Autonomous multi-agent orchestration for sales order validation, inventory verification, payment risk scoring, and invoice generation.
    </div>
    <div style="margin-top: 1.2rem; display: flex; gap: 0.6rem;">
        <span class="badge-pill badge-live">● System Active</span>
        <span class="badge-pill badge-llm">Deterministic Engine + LLM Narration</span>
    </div>
</div>
""", unsafe_allow_html=True)

# System Architecture Overview Expander
with st.expander("🏗️ View System Architecture & Agent Responsibilities", expanded=False):
    st.markdown("""
    **Core Multi-Agent Architecture Breakdown:**
    - **Orchestrator (`OrderToCashOrchestrator`)**: State Machine controlling explicit workflow state transitions, agent delegation, exception routing, real-time handoff logs, and audit trail persistence.
    - **Order Validation Agent (`OrderValidationAgent`)**: Specialist agent validating customer presence, required fields, catalog products, quantities (> 0), and price integrity. Pure deterministic logic.
    - **Inventory Agent (`InventoryAgent`)**: Specialist agent verifying stock levels in SQLite and calculating shortages. Pure deterministic arithmetic.
    - **Payment Risk Agent (`PaymentRiskAgent`)**: Specialist agent calculating payment risk score (0-100) based on credit rating, unpaid invoice count, overdue payment history, and order value thresholds.
    - **Invoice Service (`InvoiceService`)**: Deterministic business service generating subtotal, 8% tax, shipping fees, and invoice records after all required validation, inventory, and risk checks pass.
    - **SQLite Database**: Persistent transactional database storing customers, catalog products, inventory stock, order records, issued invoices, and step audit logs (`agent_logs`).
    - **Optional LLM Layer**: OpenAI GPT narration engine producing natural-language executive summaries over verified deterministic results. *(Not used for math, validation, or risk scoring).*
    """)

# Executive Metric KPI Cards Row (Theme Adaptive)
tot_o, comp_o, rev_o, fail_o, total_rev = fetch_kpis()

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.markdown(f'<div class="glossy-metric-card"><div class="metric-val" style="color:#0284C7;">{tot_o}</div><div class="metric-lbl">Total Processed</div></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="glossy-metric-card"><div class="metric-val" style="color:#059669;">{comp_o}</div><div class="metric-lbl">Completed</div></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="glossy-metric-card"><div class="metric-val" style="color:#D97706;">{rev_o}</div><div class="metric-lbl">Human Review</div></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="glossy-metric-card"><div class="metric-val" style="color:#DC2626;">{fail_o}</div><div class="metric-lbl">Validation Failed</div></div>', unsafe_allow_html=True)
with col_m5:
    st.markdown(f'<div class="glossy-metric-card"><div class="metric-val" style="color:#7C3AED;">{config.CURRENCY_SYMBOL}{total_rev:,.0f}</div><div class="metric-lbl">Issued Revenue</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Navigation Tabs
tab_exec, tab_create, tab_audit, tab_data = st.tabs([
    "📊 Workflow Execution & Agent Timeline",
    "➕ Submit Custom Order",
    "🔍 Audit Trail Inspector",
    "💾 Mock Data Explorer"
])

# -------------------------------------------------------------
# TAB 1: WORKFLOW EXECUTION & LIVE AGENT TIMELINE
# -------------------------------------------------------------
with tab_exec:
    result = st.session_state.get("last_workflow_result")

    if not result:
        st.info("👈 Select a **1-Click Demo Scenario** from the sidebar or submit a custom order in the **Submit Custom Order** tab to view live agent orchestration.")
    else:
        # Final Execution Summary Card
        st.markdown("#### 📋 Execution Final Summary")
        
        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
        c_s1.markdown(f"**Order ID:** `{result.order_id}`")
        c_s2.markdown(f"**Final State:** `{result.final_state.value}`")
        c_s3.markdown(f"**Human Review:** `{'YES (Escalated)' if result.requires_human_review else 'NO (Automated)'}`")
        c_s4.markdown(f"**Invoice Status:** `{'ISSUED (' + result.invoice_id + ')' if result.invoice_id else 'NONE (Not Generated)'}`")

        # Dynamic Visual Workflow Diagram & Exception Paths
        st.markdown("#### 🔄 Dynamic Visual Workflow Pipeline")
        st.caption("Real-time pipeline progress & exception branch routing based on current order outcome:")

        pipe_cols = st.columns(6)

        val_status = result.validation_result.status if result.validation_result else "pending"
        inv_status = result.inventory_result.status if result.inventory_result else "pending"
        risk_level = result.risk_result.risk_level.value if result.risk_result else "pending"

        # 1. Received Step
        pipe_cols[0].markdown('<div class="pipeline-step-card pipeline-step-success"><b>✓ Received</b><br><span style="font-size:0.7rem; color:#059669; font-weight:700;">ORDER_RECEIVED</span></div>', unsafe_allow_html=True)

        # 2. Validation Step
        if val_status == "approved":
            pipe_cols[1].markdown('<div class="pipeline-step-card pipeline-step-success"><b>✓ Validation</b><br><span style="font-size:0.7rem; color:#059669; font-weight:700;">PASS</span></div>', unsafe_allow_html=True)
        elif val_status == "rejected":
            pipe_cols[1].markdown('<div class="pipeline-step-card pipeline-step-error"><b>❌ Validation</b><br><span style="font-size:0.7rem; color:#DC2626; font-weight:700;">REJECTED</span></div>', unsafe_allow_html=True)
        else:
            pipe_cols[1].markdown('<div class="pipeline-step-card pipeline-step-skipped"><b>- Validation</b><br><span style="font-size:0.7rem; color:#64748B;">PENDING</span></div>', unsafe_allow_html=True)

        # 3. Inventory Step
        if inv_status == "sufficient_inventory":
            pipe_cols[2].markdown('<div class="pipeline-step-card pipeline-step-success"><b>✓ Inventory</b><br><span style="font-size:0.7rem; color:#059669; font-weight:700;">PASS</span></div>', unsafe_allow_html=True)
        elif inv_status == "insufficient_inventory":
            pipe_cols[2].markdown('<div class="pipeline-step-card pipeline-step-warning"><b>⚠️ Inventory</b><br><span style="font-size:0.7rem; color:#D97706; font-weight:700;">SHORTAGE</span></div>', unsafe_allow_html=True)
        else:
            pipe_cols[2].markdown('<div class="pipeline-step-card pipeline-step-skipped"><b>- Inventory</b><br><span style="font-size:0.7rem; color:#64748B;">SKIPPED</span></div>', unsafe_allow_html=True)

        # 4. Payment Risk Step
        if risk_level in ["LOW", "MEDIUM"]:
            pipe_cols[3].markdown('<div class="pipeline-step-card pipeline-step-success"><b>✓ Payment Risk</b><br><span style="font-size:0.7rem; color:#059669; font-weight:700;">PASS ({})</span></div>'.format(result.risk_result.risk_score), unsafe_allow_html=True)
        elif risk_level == "HIGH":
            pipe_cols[3].markdown('<div class="pipeline-step-card pipeline-step-warning"><b>⚠️ Payment Risk</b><br><span style="font-size:0.7rem; color:#D97706; font-weight:700;">HIGH RISK ({})</span></div>'.format(result.risk_result.risk_score), unsafe_allow_html=True)
        else:
            pipe_cols[3].markdown('<div class="pipeline-step-card pipeline-step-skipped"><b>- Payment Risk</b><br><span style="font-size:0.7rem; color:#64748B;">SKIPPED</span></div>', unsafe_allow_html=True)

        # 5. Invoice Service Step
        if result.invoice_id:
            pipe_cols[4].markdown('<div class="pipeline-step-card pipeline-step-success"><b>✓ Invoicing</b><br><span style="font-size:0.7rem; color:#059669; font-weight:700;">ISSUED</span></div>', unsafe_allow_html=True)
        else:
            pipe_cols[4].markdown('<div class="pipeline-step-card pipeline-step-skipped"><b>- Invoicing</b><br><span style="font-size:0.7rem; color:#64748B;">NO INVOICE</span></div>', unsafe_allow_html=True)

        # 6. Final Decision Step
        if result.is_success:
            pipe_cols[5].markdown('<div class="pipeline-step-card pipeline-step-success"><b>✓ Completed</b><br><span style="font-size:0.7rem; color:#059669; font-weight:700;">COMPLETED</span></div>', unsafe_allow_html=True)
        elif result.requires_human_review:
            pipe_cols[5].markdown('<div class="pipeline-step-card pipeline-step-warning"><b>⚠️ Review</b><br><span style="font-size:0.7rem; color:#D97706; font-weight:700;">ESCALATED</span></div>', unsafe_allow_html=True)
        else:
            pipe_cols[5].markdown('<div class="pipeline-step-card pipeline-step-error"><b>❌ Rejected</b><br><span style="font-size:0.7rem; color:#DC2626; font-weight:700;">REJECTED</span></div>', unsafe_allow_html=True)

        # Branch Routing Explanation
        if result.requires_human_review:
            st.warning("↪️ **Exception Branch Routing Triggered**: Workflow halted prior to invoice generation and routed to **HUMAN REVIEW** queue.")
        elif not result.is_success and not result.requires_human_review:
            st.error("↪️ **Exception Branch Routing Triggered**: Validation failure halted workflow immediately. Order **REJECTED**.")

        st.divider()

        # Requirement 1: Prominent INVOICE GENERATED Card
        inv = getattr(result, "invoice_details", None)
        if not inv and result.invoice_id:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM invoices WHERE invoice_id = ?", (result.invoice_id,))
                row = cursor.fetchone()
                if row:
                    inv = dict(row)

        if result.is_success and inv:
            st.markdown(f"""
            <div class="invoice-card">
                <div class="invoice-header">
                    <div class="invoice-title">
                        🧾 <span>INVOICE GENERATED & ISSUED</span>
                    </div>
                    <div class="invoice-badge-success">● Status: {inv.get('status', 'ISSUED')}</div>
                </div>
                <div class="invoice-grid">
                    <div>
                        <div class="invoice-field-label">Invoice ID</div>
                        <div class="invoice-field-value">{inv.get('invoice_id')}</div>
                    </div>
                    <div>
                        <div class="invoice-field-label">Sales Order ID</div>
                        <div class="invoice-field-value">{inv.get('order_id')}</div>
                    </div>
                    <div>
                        <div class="invoice-field-label">Customer ID</div>
                        <div class="invoice-field-value">{inv.get('customer_id')}</div>
                    </div>
                    <div>
                        <div class="invoice-field-label">Issue Date</div>
                        <div class="invoice-field-value" style="font-size:0.9rem;">{inv.get('issue_date')}</div>
                    </div>
                </div>
                <div class="invoice-grid" style="border-top:1px dashed rgba(148, 163, 184, 0.4); padding-top:1rem;">
                    <div>
                        <div class="invoice-field-label">Subtotal</div>
                        <div class="invoice-field-value">{config.CURRENCY_SYMBOL}{inv.get('subtotal', 0.0):,.2f}</div>
                    </div>
                    <div>
                        <div class="invoice-field-label">Tax (8%)</div>
                        <div class="invoice-field-value">{config.CURRENCY_SYMBOL}{inv.get('tax_amount', 0.0):,.2f}</div>
                    </div>
                    <div>
                        <div class="invoice-field-label">Shipping Fee</div>
                        <div class="invoice-field-value">{config.CURRENCY_SYMBOL}{inv.get('shipping_fee', 0.0):,.2f}</div>
                    </div>
                    <div>
                        <div class="invoice-field-label" style="color:#059669;">Total Invoice Amount</div>
                        <div class="invoice-field-value" style="color:#059669; font-size:1.3rem;">{config.CURRENCY_SYMBOL}{inv.get('total_amount', 0.0):,.2f}</div>
                    </div>
                </div>
                <div style="font-size:0.82rem; color:#059669; margin-top:0.5rem; font-weight:700;">
                    ✓ Invoice successfully generated, stored in SQLite database, and stock reserved. Payment Due Date: {inv.get('due_date')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.divider()

        # Executive Summary / LLM Narrative
        st.markdown("#### 📝 Narrative Workflow Summary")
        st.info(f"**Executive Narration:** {result.summary_explanation}")

        st.divider()

        # Requirement 3: Agent Handoff Timeline Table
        st.markdown("#### 📜 Agent Handoff Log Timeline (Audit Sequence)")
        st.caption("Live agent-to-agent delegation events recorded by the orchestrator at runtime:")

        handoff_data = [
            {
                "Timestamp": log.timestamp,
                "From Agent": log.from_agent,
                "To Agent": log.to_agent,
                "State": log.state.value,
                "Status": log.status,
                "Message / Payload Rationale": log.message
            }
            for log in result.handoff_logs
        ]
        st.dataframe(pd.DataFrame(handoff_data), use_container_width=True)

        st.divider()

        # Step-by-Step Decision Rationale Breakdown
        st.markdown("#### 🔍 Step-by-Step Rationale & Payloads")
        for step in result.step_executions:
            with st.expander(f"🔹 {step.step_name} ({step.agent_name}) — Status: {step.status} — Decision: {step.decision}", expanded=True):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"**Decision Rationale:** {step.reason}")
                    st.markdown(f"**Timestamp:** `{step.timestamp}`")
                with c2:
                    st.markdown("**Output Payload:**")
                    st.json(step.output_data)

# -------------------------------------------------------------
# TAB 2: CREATE CUSTOM ORDER
# -------------------------------------------------------------
with tab_create:
    st.markdown("#### ➕ Submit Interactive Sales Order")
    st.caption("Test custom customer and product combinations against the orchestrator.")

    cust_df = fetch_customers()
    prod_df = fetch_products()

    if cust_df.empty or prod_df.empty:
        seed_database()
        cust_df = fetch_customers()
        prod_df = fetch_products()

    with st.form("custom_order_form_glossy"):
        cust_options = {f"{row['company_name']} ({row['customer_id']}) — Credit Rating: {row['credit_rating']}": row['customer_id'] for _, row in cust_df.iterrows()}
        cust_labels = list(cust_options.keys())
        selected_cust_label = st.selectbox("Select Customer Profile", cust_labels) if cust_labels else None
        selected_cust_id = cust_options.get(selected_cust_label, "CUST-101") if selected_cust_label else "CUST-101"

        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            prod_options = {f"{row['name']} ({row['product_id']}) — ${row['unit_price']:,.2f} [Available Stock: {row['available_quantity']}]": row['product_id'] for _, row in prod_df.iterrows()}
            prod_labels = list(prod_options.keys())
            selected_prod_label = st.selectbox("Select Catalog Product", prod_labels) if prod_labels else None
            selected_prod_id = prod_options.get(selected_prod_label, "P1001") if selected_prod_label else "P1001"
        with col_p2:
            qty = st.number_input("Order Quantity", min_value=1, max_value=500, value=2)

        notes = st.text_input("Order Notes", "Custom order submission via Streamlit UI")
        submit_btn = st.form_submit_button("🚀 Submit to Orchestrator Pipeline", use_container_width=True)

        if submit_btn and selected_cust_id and selected_prod_id:
            matched_prod = prod_df[prod_df["product_id"] == selected_prod_id]
            unit_price = float(matched_prod["unit_price"].values[0]) if not matched_prod.empty else 2500.00
            items = [{"product_id": selected_prod_id, "quantity": qty, "unit_price": unit_price}]

            orchestrator = OrderToCashOrchestrator()
            res = orchestrator.process_order(selected_cust_id, items, notes=notes)
            st.session_state["last_workflow_result"] = res
            st.success(f"Order {res.order_id} processed by orchestrator!")
            st.rerun()

# -------------------------------------------------------------
# TAB 3: AUDIT TRAIL INSPECTOR
# -------------------------------------------------------------
with tab_audit:
    st.markdown("#### 🔍 SQLite Audit Trail Inspector")
    st.caption("Persisted step executions and agent handoff logs in `agent_logs` SQLite table.")

    with get_connection() as conn:
        all_logs = pd.read_sql_query("SELECT * FROM agent_logs ORDER BY id DESC", conn)

    if all_logs.empty:
        st.info("No audit logs found. Run an order to generate audit records.")
    else:
        order_list = ["ALL"] + list(all_logs["order_id"].unique())
        selected_order = st.selectbox("Filter Audit Logs by Order ID", order_list)

        filtered_logs = all_logs if selected_order == "ALL" else all_logs[all_logs["order_id"] == selected_order]
        st.dataframe(filtered_logs, use_container_width=True)

        st.divider()
        st.markdown("#### 🧾 Issued Invoices Database (`invoices`)")
        with get_connection() as conn:
            inv_df = pd.read_sql_query("SELECT * FROM invoices ORDER BY issue_date DESC", conn)
        st.dataframe(inv_df, use_container_width=True)

# -------------------------------------------------------------
# TAB 4: MOCK DATA EXPLORER
# -------------------------------------------------------------
with tab_data:
    st.markdown("#### 💾 Transactional Mock Database Explorer")
    st.caption("Inspect synthetic customer accounts, product catalog prices, available inventory stock, and historical payment records.")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("**Synthetic Customers (`customers`)**")
        with get_connection() as conn:
            st.dataframe(pd.read_sql_query("SELECT * FROM customers", conn), use_container_width=True)

        st.markdown("**Synthetic Inventory Stock (`inventory`)**")
        with get_connection() as conn:
            st.dataframe(pd.read_sql_query("SELECT * FROM inventory", conn), use_container_width=True)

    with col_d2:
        st.markdown("**Synthetic Products Catalog (`products`)**")
        with get_connection() as conn:
            st.dataframe(pd.read_sql_query("SELECT * FROM products", conn), use_container_width=True)

        st.markdown("**Synthetic Payment History (`payment_history`)**")
        with get_connection() as conn:
            st.dataframe(pd.read_sql_query("SELECT * FROM payment_history", conn), use_container_width=True)
