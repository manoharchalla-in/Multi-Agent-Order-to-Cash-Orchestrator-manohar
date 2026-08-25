# https://github.com/manoharchalla-inor
# #manoharchalla-in

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from models.agent_state import WorkflowState, RiskLevel


class ValidationResult(BaseModel):
    status: str  # "approved" or "rejected"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_total: float = 0.0


class InventoryShortageItem(BaseModel):
    product_id: str
    product_name: str = ""
    requested: int
    available: int
    shortage: int


class InventoryCheckResult(BaseModel):
    status: str  # "sufficient_inventory" or "insufficient_inventory"
    items: List[InventoryShortageItem] = Field(default_factory=list)
    details: List[Dict[str, Any]] = Field(default_factory=list)


class PaymentRiskResult(BaseModel):
    risk_level: RiskLevel
    risk_score: float  # 0 to 100
    reasons: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None  # LLM narration or fallback string


class AgentHandoffLog(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    from_agent: str
    to_agent: str
    message: str
    state: WorkflowState
    status: str = "INFO"  # INFO, WARNING, ERROR, SUCCESS


class WorkflowStepExecution(BaseModel):
    step_name: str
    agent_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    decision: str
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str  # SUCCESS, ESCALATED, FAILED


class WorkflowResult(BaseModel):
    order_id: str
    final_state: WorkflowState
    is_success: bool
    requires_human_review: bool
    summary_explanation: str
    validation_result: Optional[ValidationResult] = None
    inventory_result: Optional[InventoryCheckResult] = None
    risk_result: Optional[PaymentRiskResult] = None
    invoice_id: Optional[str] = None
    invoice_total: Optional[float] = None
    invoice_details: Optional[Dict[str, Any]] = None
    handoff_logs: List[AgentHandoffLog] = Field(default_factory=list)
    step_executions: List[WorkflowStepExecution] = Field(default_factory=list)
