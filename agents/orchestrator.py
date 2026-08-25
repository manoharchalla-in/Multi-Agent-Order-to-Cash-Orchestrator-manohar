# https://github.com/manoharchalla-inor
# #manoharchalla-in

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import config
from models.agent_state import WorkflowState, RiskLevel
from models.order import SalesOrder, OrderItem
from models.results import (
    WorkflowResult,
    AgentHandoffLog,
    WorkflowStepExecution,
    ValidationResult,
    InventoryCheckResult,
    PaymentRiskResult,
)
from services.database import get_connection, save_agent_log
from services.inventory_service import InventoryService
from services.invoice_service import InvoiceService
from agents.order_validation_agent import OrderValidationAgent
from agents.inventory_agent import InventoryAgent
from agents.payment_risk_agent import PaymentRiskAgent


class OrderToCashOrchestrator:
    """
    State Machine Orchestrator for Order-to-Cash Workflow.
    Responsibilities:
    1. Receive sales order
    2. Sequentially delegate tasks to specialist agents (Validation, Inventory, Payment Risk)
    3. Own state transitions and exception path routing
    4. Generate real-time agent handoff timeline
    5. Trigger invoice generation and inventory updates
    6. Record full audit trail in SQLite
    """

    def __init__(self):
        self.validation_agent = OrderValidationAgent()
        self.inventory_agent = InventoryAgent()
        self.payment_risk_agent = PaymentRiskAgent()

    def process_order(self, customer_id: str, items: List[Dict[str, Any]], notes: Optional[str] = None) -> WorkflowResult:
        order_id = f"SO-{uuid.uuid4().hex[:6].upper()}"
        handoff_logs: List[AgentHandoffLog] = []
        step_executions: List[WorkflowStepExecution] = []

        current_state = WorkflowState.ORDER_RECEIVED

        def log_handoff(from_ag: str, to_ag: str, msg: str, st: WorkflowState, status_level: str = "INFO"):
            ts = datetime.now().strftime("%H:%M:%S")
            entry = AgentHandoffLog(
                timestamp=ts,
                from_agent=from_ag,
                to_agent=to_ag,
                message=msg,
                state=st,
                status=status_level
            )
            handoff_logs.append(entry)

        log_handoff("USER", "ORCHESTRATOR", f"Received new sales order request {order_id}", current_state)

        # -------------------------------------------------------------
        # STEP 1: ORDER VALIDATION
        # -------------------------------------------------------------
        current_state = WorkflowState.VALIDATING
        log_handoff("ORCHESTRATOR", "ORDER_VALIDATION_AGENT", f"Validate order input for {order_id}", current_state)

        val_input = {"customer_id": customer_id, "items": items}
        validation_res: ValidationResult = self.validation_agent.process(val_input)

        if validation_res.status == "approved":
            log_handoff(
                "ORDER_VALIDATION_AGENT",
                "ORCHESTRATOR",
                f"Validation passed. Validated total: {config.CURRENCY_SYMBOL}{validation_res.validated_total:,.2f}",
                current_state,
                "SUCCESS"
            )
            step_executions.append(WorkflowStepExecution(
                step_name="Order Validation",
                agent_name="OrderValidationAgent",
                input_data=val_input,
                output_data=validation_res.model_dump(),
                decision="APPROVED",
                reason="Order structure, customer, and catalog products are valid.",
                status="SUCCESS"
            ))
            save_agent_log(
                order_id, "ORDER_VALIDATION_AGENT", "ORCHESTRATOR", "Order Validation",
                val_input, validation_res.model_dump(), "APPROVED", "Order structure valid", "SUCCESS", datetime.now().isoformat()
            )
        else:
            err_msg = "; ".join(validation_res.errors)
            log_handoff(
                "ORDER_VALIDATION_AGENT",
                "ORCHESTRATOR",
                f"Validation failed: {err_msg}",
                WorkflowState.VALIDATION_FAILED,
                "ERROR"
            )
            step_executions.append(WorkflowStepExecution(
                step_name="Order Validation",
                agent_name="OrderValidationAgent",
                input_data=val_input,
                output_data=validation_res.model_dump(),
                decision="REJECTED",
                reason=err_msg,
                status="FAILED"
            ))
            save_agent_log(
                order_id, "ORDER_VALIDATION_AGENT", "ORCHESTRATOR", "Order Validation",
                val_input, validation_res.model_dump(), "REJECTED", err_msg, "FAILED", datetime.now().isoformat()
            )

            current_state = WorkflowState.VALIDATION_FAILED
            self._save_order_to_db(order_id, customer_id, items, validation_res.validated_total, current_state.value, notes)

            summary = f"Order {order_id} was REJECTED during validation due to errors: {err_msg}"
            return WorkflowResult(
                order_id=order_id,
                final_state=current_state,
                is_success=False,
                requires_human_review=False,
                summary_explanation=summary,
                validation_result=validation_res,
                handoff_logs=handoff_logs,
                step_executions=step_executions
            )

        # Build order total
        order_total = validation_res.validated_total

        # -------------------------------------------------------------
        # STEP 2: INVENTORY CHECK
        # -------------------------------------------------------------
        current_state = WorkflowState.INVENTORY_CHECK
        log_handoff("ORCHESTRATOR", "INVENTORY_AGENT", f"Check inventory availability for {len(items)} items", current_state)

        inv_input = {"items": items}
        inventory_res: InventoryCheckResult = self.inventory_agent.process(items)

        if inventory_res.status == "sufficient_inventory":
            log_handoff(
                "INVENTORY_AGENT",
                "ORCHESTRATOR",
                "Inventory verification passed. All items in stock.",
                current_state,
                "SUCCESS"
            )
            step_executions.append(WorkflowStepExecution(
                step_name="Inventory Check",
                agent_name="InventoryAgent",
                input_data=inv_input,
                output_data=inventory_res.model_dump(),
                decision="SUFFICIENT_STOCK",
                reason="All requested product quantities are available in warehouse.",
                status="SUCCESS"
            ))
            save_agent_log(
                order_id, "INVENTORY_AGENT", "ORCHESTRATOR", "Inventory Check",
                inv_input, inventory_res.model_dump(), "SUFFICIENT_STOCK", "All items available", "SUCCESS", datetime.now().isoformat()
            )
        else:
            shortage_details = [
                f"{item.product_name or item.product_id} (Requested: {item.requested}, Available: {item.available}, Shortage: {item.shortage})"
                for item in inventory_res.items
            ]
            shortage_msg = "; ".join(shortage_details)
            log_handoff(
                "INVENTORY_AGENT",
                "ORCHESTRATOR",
                f"Inventory insufficient: {shortage_msg}",
                WorkflowState.INSUFFICIENT_INVENTORY,
                "WARNING"
            )
            step_executions.append(WorkflowStepExecution(
                step_name="Inventory Check",
                agent_name="InventoryAgent",
                input_data=inv_input,
                output_data=inventory_res.model_dump(),
                decision="INSUFFICIENT_STOCK",
                reason=shortage_msg,
                status="ESCALATED"
            ))
            save_agent_log(
                order_id, "INVENTORY_AGENT", "ORCHESTRATOR", "Inventory Check",
                inv_input, inventory_res.model_dump(), "INSUFFICIENT_STOCK", shortage_msg, "ESCALATED", datetime.now().isoformat()
            )

            current_state = WorkflowState.HUMAN_REVIEW
            log_handoff(
                "ORCHESTRATOR",
                "HUMAN_REVIEW",
                "Escalating order to Human Review queue due to inventory shortage.",
                current_state,
                "WARNING"
            )
            self._save_order_to_db(order_id, customer_id, items, order_total, current_state.value, notes)

            summary = self._generate_workflow_summary(
                order_id, customer_id, order_total, "HUMAN_REVIEW",
                f"Inventory shortage detected for requested items ({shortage_msg}). Escalated to operations for manual backorder allocation."
            )

            return WorkflowResult(
                order_id=order_id,
                final_state=current_state,
                is_success=False,
                requires_human_review=True,
                summary_explanation=summary,
                validation_result=validation_res,
                inventory_result=inventory_res,
                handoff_logs=handoff_logs,
                step_executions=step_executions
            )

        # -------------------------------------------------------------
        # STEP 3: PAYMENT RISK CHECK
        # -------------------------------------------------------------
        current_state = WorkflowState.PAYMENT_RISK
        log_handoff("ORCHESTRATOR", "PAYMENT_RISK_AGENT", f"Evaluate payment risk score for customer {customer_id}", current_state)

        risk_input = {"customer_id": customer_id, "order_total": order_total}
        risk_res: PaymentRiskResult = self.payment_risk_agent.process(customer_id, order_total)

        if risk_res.risk_level != RiskLevel.HIGH and risk_res.risk_score < config.PAYMENT_RISK_THRESHOLD:
            log_handoff(
                "PAYMENT_RISK_AGENT",
                "ORCHESTRATOR",
                f"Payment risk acceptable (Level: {risk_res.risk_level.value}, Score: {risk_res.risk_score:.1f}/100)",
                current_state,
                "SUCCESS"
            )
            step_executions.append(WorkflowStepExecution(
                step_name="Payment Risk Assessment",
                agent_name="PaymentRiskAgent",
                input_data=risk_input,
                output_data=risk_res.model_dump(),
                decision="ACCEPTABLE_RISK",
                reason=risk_res.explanation or "; ".join(risk_res.reasons),
                status="SUCCESS"
            ))
            save_agent_log(
                order_id, "PAYMENT_RISK_AGENT", "ORCHESTRATOR", "Payment Risk Assessment",
                risk_input, risk_res.model_dump(), "ACCEPTABLE_RISK", risk_res.explanation or "; ".join(risk_res.reasons), "SUCCESS", datetime.now().isoformat()
            )
        else:
            risk_reasons_msg = "; ".join(risk_res.reasons)
            log_handoff(
                "PAYMENT_RISK_AGENT",
                "ORCHESTRATOR",
                f"HIGH payment risk detected (Score: {risk_res.risk_score:.1f}/100). Reasons: {risk_reasons_msg}",
                WorkflowState.PAYMENT_RISK_ESCALATION,
                "WARNING"
            )
            step_executions.append(WorkflowStepExecution(
                step_name="Payment Risk Assessment",
                agent_name="PaymentRiskAgent",
                input_data=risk_input,
                output_data=risk_res.model_dump(),
                decision="HIGH_RISK_ESCALATED",
                reason=risk_res.explanation or risk_reasons_msg,
                status="ESCALATED"
            ))
            save_agent_log(
                order_id, "PAYMENT_RISK_AGENT", "ORCHESTRATOR", "Payment Risk Assessment",
                risk_input, risk_res.model_dump(), "HIGH_RISK_ESCALATED", risk_reasons_msg, "ESCALATED", datetime.now().isoformat()
            )

            current_state = WorkflowState.HUMAN_REVIEW
            log_handoff(
                "ORCHESTRATOR",
                "HUMAN_REVIEW",
                f"Escalating order {order_id} to credit review team due to risk score {risk_res.risk_score:.1f} >= threshold {config.PAYMENT_RISK_THRESHOLD}.",
                current_state,
                "WARNING"
            )
            self._save_order_to_db(order_id, customer_id, items, order_total, current_state.value, notes)

            summary = self._generate_workflow_summary(
                order_id, customer_id, order_total, "HUMAN_REVIEW",
                f"Payment risk flagged as HIGH (Score: {risk_res.risk_score:.1f}/100). {risk_res.explanation or risk_reasons_msg}"
            )

            return WorkflowResult(
                order_id=order_id,
                final_state=current_state,
                is_success=False,
                requires_human_review=True,
                summary_explanation=summary,
                validation_result=validation_res,
                inventory_result=inventory_res,
                risk_result=risk_res,
                handoff_logs=handoff_logs,
                step_executions=step_executions
            )

        # -------------------------------------------------------------
        # STEP 4: INVOICE GENERATION & ORDER FULFILLMENT
        # -------------------------------------------------------------
        current_state = WorkflowState.INVOICE_GENERATION
        log_handoff("ORCHESTRATOR", "INVOICE_SERVICE", f"Reserving stock & generating invoice for {order_id}", current_state)

        # Reserve Inventory
        InventoryService.reserve_inventory(items)

        # Construct SalesOrder model
        order_model = SalesOrder(
            order_id=order_id,
            customer_id=customer_id,
            items=[OrderItem(**it) for it in items],
            total_amount=order_total,
            status=WorkflowState.COMPLETED.value,
            notes=notes
        )

        invoice = InvoiceService.generate_invoice(order_model)

        log_handoff(
            "INVOICE_SERVICE",
            "ORCHESTRATOR",
            f"Invoice {invoice.invoice_id} created for total {config.CURRENCY_SYMBOL}{invoice.total_amount:,.2f}",
            current_state,
            "SUCCESS"
        )
        step_executions.append(WorkflowStepExecution(
            step_name="Invoice Generation",
            agent_name="InvoiceService",
            input_data={"order_id": order_id, "amount": order_total},
            output_data=invoice.model_dump(),
            decision="INVOICE_ISSUED",
            reason=f"Generated invoice {invoice.invoice_id} with total {config.CURRENCY_SYMBOL}{invoice.total_amount:,.2f}",
            status="SUCCESS"
        ))

        current_state = WorkflowState.COMPLETED
        log_handoff(
            "ORCHESTRATOR",
            "USER",
            f"Workflow COMPLETED successfully for {order_id}. Invoice {invoice.invoice_id} issued.",
            current_state,
            "SUCCESS"
        )

        self._save_order_to_db(order_id, customer_id, items, order_total, current_state.value, notes)

        summary = self._generate_workflow_summary(
            order_id, customer_id, order_total, "COMPLETED",
            f"Order validated, inventory reserved, payment risk verified (Score: {risk_res.risk_score:.1f}), and Invoice {invoice.invoice_id} issued."
        )

        return WorkflowResult(
            order_id=order_id,
            final_state=current_state,
            is_success=True,
            requires_human_review=False,
            summary_explanation=summary,
            validation_result=validation_res,
            inventory_result=inventory_res,
            risk_result=risk_res,
            invoice_id=invoice.invoice_id,
            invoice_total=invoice.total_amount,
            invoice_details=invoice.model_dump(),
            handoff_logs=handoff_logs,
            step_executions=step_executions
        )

    def _save_order_to_db(
        self, order_id: str, customer_id: str, items: List[Dict[str, Any]],
        total_amount: float, status: str, notes: Optional[str]
    ):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (order_id, customer_id, total_amount, status, created_at, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, customer_id, total_amount, status, datetime.now().isoformat(), notes))

            for it in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (order_id, it.get("product_id"), it.get("quantity", 0), it.get("unit_price", 0.0)))

            conn.commit()

    def _generate_workflow_summary(
        self, order_id: str, customer_id: str, total: float, outcome: str, details: str
    ) -> str:
        fallback = f"Order {order_id} Outcome: {outcome}. {details}"

        if not config.OPENAI_API_KEY:
            return fallback

        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            prompt = (
                f"Provide a concise 2-sentence executive summary of this Order-to-Cash workflow run:\n"
                f"- Order ID: {order_id}\n"
                f"- Customer ID: {customer_id}\n"
                f"- Order Total: {config.CURRENCY_SYMBOL}{total:,.2f}\n"
                f"- Final Workflow Outcome: {outcome}\n"
                f"- Operational Details: {details}"
            )
            resp = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an executive enterprise assistant summarizing Order-to-Cash workflows."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=120,
                temperature=0.2
            )
            res_text = resp.choices[0].message.content.strip()
            return res_text if res_text else fallback
        except Exception:
            return fallback
