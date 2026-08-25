# https://github.com/manoharchalla-inor
# #manoharchalla-in

from typing import Dict, Any
import config
from services.risk_service import RiskService
from models.results import PaymentRiskResult


class PaymentRiskAgent:
    """
    Specialist Agent 3: Payment Risk Agent
    Responsibility: Calculate mock payment-risk score deterministically (order value + customer risk history).
    Classify LOW / MEDIUM / HIGH.
    LLM Usage: Optional narration of deterministic results into human-readable explanation.
    """
    def __init__(self):
        self.agent_name = "PAYMENT_RISK_AGENT"

    def process(self, customer_id: str, order_total: float) -> PaymentRiskResult:
        # 1. Deterministic risk calculation
        result = RiskService.calculate_payment_risk(customer_id, order_total)

        # 2. Optional LLM narration over deterministic facts
        explanation = self._generate_explanation(result, customer_id, order_total)
        result.explanation = explanation

        return result

    def _generate_explanation(self, result: PaymentRiskResult, customer_id: str, order_total: float) -> str:
        fallback_text = (
            f"Payment Risk Evaluation for Customer {customer_id}: "
            f"Risk Level is {result.risk_level.value} (Score: {result.risk_score:.1f}/100). "
            f"Factors: {'; '.join(result.reasons)}."
        )

        if not config.OPENAI_API_KEY:
            return fallback_text

        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            prompt = (
                f"You are a credit analyst summarizing an automated payment risk check for an enterprise Order-to-Cash system.\n"
                f"DO NOT invent any numbers or risk factors. Synthesize these exact facts into a concise 2-sentence executive summary:\n"
                f"- Customer ID: {customer_id}\n"
                f"- Order Total: {config.CURRENCY_SYMBOL}{order_total:,.2f}\n"
                f"- Calculated Risk Score: {result.risk_score:.1f} / 100\n"
                f"- Classified Risk Level: {result.risk_level.value}\n"
                f"- Key Deterministic Factors: {', '.join(result.reasons)}"
            )

            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional financial risk analyst narration engine."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            narrative = response.choices[0].message.content.strip()
            return narrative if narrative else fallback_text
        except Exception:
            return fallback_text
