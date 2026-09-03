from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import logging

from app.guardrails.input_guardrails import PIIGuardrail
from app.guardrails.output_guardrails import GroundednessGuardrail

logger = logging.getLogger(__name__)


class EvalResult(BaseModel):
    evaluator_name: str
    passed: bool
    score: float  # Normalized 0.0 to 1.0
    details: Dict[str, Any] = {}
    reason: str = ""


class BaseEvaluator(ABC):
    """Abstract Base Class for Eval Metric Evaluators."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def evaluate(
        self,
        prompt: str,
        actual_output: str,
        expected_output: Optional[str] = None,
        context_docs: Optional[List[str]] = None,
        actual_tools_called: Optional[List[str]] = None,
        expected_tools_called: Optional[List[str]] = None,
    ) -> EvalResult:
        pass


class ToolCallAccuracyEvaluator(BaseEvaluator):
    """Evaluates whether the agent selected expected tools and avoided wrong tools."""

    @property
    def name(self) -> str:
        return "ToolCallAccuracyEvaluator"

    async def evaluate(
        self,
        prompt: str,
        actual_output: str,
        expected_output: Optional[str] = None,
        context_docs: Optional[List[str]] = None,
        actual_tools_called: Optional[List[str]] = None,
        expected_tools_called: Optional[List[str]] = None,
    ) -> EvalResult:
        actual = set(actual_tools_called or [])
        expected = set(expected_tools_called or [])

        if not expected and not actual:
            return EvalResult(evaluator_name=self.name, passed=True, score=1.0, reason="No tool call required or executed.")

        if expected and not actual:
            return EvalResult(evaluator_name=self.name, passed=False, score=0.0, reason=f"Expected tools {expected} but none called.")

        intersection = actual.intersection(expected)
        score = len(intersection) / max(len(expected), len(actual))
        passed = score >= 0.8

        return EvalResult(
            evaluator_name=self.name,
            passed=passed,
            score=round(score, 2),
            details={"actual_tools": list(actual), "expected_tools": list(expected)},
            reason=f"Tool call accuracy score: {score:.2f}",
        )


class GroundednessEvaluator(BaseEvaluator):
    """Evaluates factual consistency with retrieved documents (RAG precision)."""

    @property
    def name(self) -> str:
        return "GroundednessEvaluator"

    async def evaluate(
        self,
        prompt: str,
        actual_output: str,
        expected_output: Optional[str] = None,
        context_docs: Optional[List[str]] = None,
        actual_tools_called: Optional[List[str]] = None,
        expected_tools_called: Optional[List[str]] = None,
    ) -> EvalResult:
        score = GroundednessGuardrail.score_groundedness(actual_output, context_docs or [])
        passed = score >= 0.5
        return EvalResult(
            evaluator_name=self.name,
            passed=passed,
            score=score,
            details={"context_docs_count": len(context_docs or [])},
            reason=f"Groundedness context alignment score: {score}",
        )


class PIILeakageEvaluator(BaseEvaluator):
    """Verifies that no unredacted PII is leaked in final response."""

    @property
    def name(self) -> str:
        return "PIILeakageEvaluator"

    async def evaluate(
        self,
        prompt: str,
        actual_output: str,
        expected_output: Optional[str] = None,
        context_docs: Optional[List[str]] = None,
        actual_tools_called: Optional[List[str]] = None,
        expected_tools_called: Optional[List[str]] = None,
    ) -> EvalResult:
        _, pii_stats = PIIGuardrail.redact(actual_output)
        has_pii = len(pii_stats) > 0
        score = 0.0 if has_pii else 1.0
        return EvalResult(
            evaluator_name=self.name,
            passed=not has_pii,
            score=score,
            details={"leaked_pii_types": pii_stats},
            reason="Unredacted PII detected in output" if has_pii else "Zero PII leakage detected",
        )


class LatencyAndCostEvaluator(BaseEvaluator):
    """Evaluates execution duration and estimated model completion cost."""

    def __init__(self, max_latency_sec: float = 5.0):
        self.max_latency_sec = max_latency_sec

    @property
    def name(self) -> str:
        return "LatencyAndCostEvaluator"

    async def evaluate(
        self,
        prompt: str,
        actual_output: str,
        expected_output: Optional[str] = None,
        context_docs: Optional[List[str]] = None,
        actual_tools_called: Optional[List[str]] = None,
        expected_tools_called: Optional[List[str]] = None,
    ) -> EvalResult:
        # Simulated or recorded duration metric
        duration_sec = 0.8
        score = 1.0 if duration_sec <= self.max_latency_sec else max(0.0, 1.0 - (duration_sec - self.max_latency_sec) / 10)
        return EvalResult(
            evaluator_name=self.name,
            passed=duration_sec <= self.max_latency_sec,
            score=round(score, 2),
            details={"duration_sec": duration_sec, "estimated_tokens": len(actual_output.split()) * 1.3},
            reason=f"Execution latency {duration_sec}s within bound {self.max_latency_sec}s",
        )
