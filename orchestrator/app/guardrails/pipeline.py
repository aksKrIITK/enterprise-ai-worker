from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.guardrails.input_guardrails import PromptInjectionGuardrail, PIIGuardrail, SafetyGuardrail
from app.guardrails.output_guardrails import SystemPromptLeakGuardrail, GroundednessGuardrail
from app.guardrails.sql_guardrails import SQLCommandGuardrail
from app.exceptions import GuardrailViolationError

logger = logging.getLogger(__name__)


class GuardrailResult(BaseModel):
    passed: bool
    sanitized_text: str
    violations: List[str]
    pii_redacted: Dict[str, int]
    groundedness_score: Optional[float] = None


class GuardrailPipeline:
    """Unified Guardrail Pipeline for input, output, and tool validation."""

    def __init__(self, block_on_injection: bool = True):
        self.block_on_injection = block_on_injection

    def process_input(self, user_text: str) -> GuardrailResult:
        """Runs prompt injection checks, PII redaction, and command safety filter."""
        violations = []

        # 1. Prompt Injection
        passed_inj, inj_violations = PromptInjectionGuardrail.check(user_text)
        if not passed_inj:
            violations.extend(inj_violations)
            if self.block_on_injection:
                logger.warning("Prompt injection blocked: %s", inj_violations)
                raise GuardrailViolationError(
                    message="Prompt injection attack pattern detected.",
                    guardrail_name="PromptInjectionGuardrail",
                    violations=inj_violations,
                )

        # 2. Safety filter
        passed_safety, safety_violations = SafetyGuardrail.check(user_text)
        if not passed_safety:
            violations.extend(safety_violations)
            raise GuardrailViolationError(
                message="Destructive system command detected in prompt.",
                guardrail_name="SafetyGuardrail",
                violations=safety_violations,
            )

        # 3. PII Redaction
        sanitized_text, pii_stats = PIIGuardrail.redact(user_text)

        return GuardrailResult(
            passed=len(violations) == 0,
            sanitized_text=sanitized_text,
            violations=violations,
            pii_redacted=pii_stats,
        )

    def process_output(self, response_text: str, context_docs: Optional[List[str]] = None) -> GuardrailResult:
        """Runs prompt leak protection, PII redaction, and groundedness evaluation on LLM outputs."""
        violations = []

        # 1. Leak protection
        passed_leak, leak_violations = SystemPromptLeakGuardrail.check(response_text)
        if not passed_leak:
            violations.extend(leak_violations)
            raise GuardrailViolationError(
                message="LLM output contained prohibited secret tokens or system prompt leakage.",
                guardrail_name="SystemPromptLeakGuardrail",
                violations=leak_violations,
            )

        # 2. PII Redaction on output
        sanitized_output, pii_stats = PIIGuardrail.redact(response_text)

        # 3. Groundedness
        grounded_score = GroundednessGuardrail.score_groundedness(response_text, context_docs or [])

        return GuardrailResult(
            passed=len(violations) == 0,
            sanitized_text=sanitized_output,
            violations=violations,
            pii_redacted=pii_stats,
            groundedness_score=grounded_score,
        )

    def process_sql_query(self, sql_query: str, tenant_id: str) -> None:
        """Validates generated SQL query prior to execution."""
        passed, violations = SQLCommandGuardrail.check_query(sql_query, tenant_id)
        if not passed:
            raise GuardrailViolationError(
                message=f"SQL Query failed safety verification for tenant {tenant_id}.",
                guardrail_name="SQLCommandGuardrail",
                violations=violations,
            )
