from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import logging

from app.evals.dataset import DatasetLoader, BenchmarkTestCase
from app.evals.evaluators import (
    BaseEvaluator,
    ToolCallAccuracyEvaluator,
    GroundednessEvaluator,
    PIILeakageEvaluator,
    LatencyAndCostEvaluator,
    EvalResult,
)
from app.guardrails.pipeline import GuardrailPipeline

logger = logging.getLogger(__name__)


class TestCaseEvalResult(BaseModel):
    test_case_id: str
    category: str
    prompt: str
    actual_output: str
    evaluations: List[EvalResult]
    passed_all: bool
    overall_score: float


class BenchmarkSummaryReport(BaseModel):
    total_test_cases: int
    passed_count: int
    failed_count: int
    accuracy_percentage: float
    avg_groundedness_score: float
    pii_safety_pass_rate: float
    total_duration_sec: float
    test_case_results: List[TestCaseEvalResult]


class BenchmarkRunner:
    """Async Benchmark Runner executing evaluation metrics across benchmark test sets."""

    def __init__(self, evaluators: Optional[List[BaseEvaluator]] = None):
        self.evaluators = evaluators or [
            ToolCallAccuracyEvaluator(),
            GroundednessEvaluator(),
            PIILeakageEvaluator(),
            LatencyAndCostEvaluator(),
        ]
        self.guardrail_pipeline = GuardrailPipeline(block_on_injection=False)

    async def run_benchmark(
        self, test_cases: Optional[List[BenchmarkTestCase]] = None
    ) -> BenchmarkSummaryReport:
        cases = test_cases or DatasetLoader.get_benchmark_cases()
        start_time = time.time()

        case_results = []
        passed_count = 0
        groundedness_scores = []
        pii_pass_count = 0

        for tc in cases:
            # Run input guardrail + mock execution response simulation
            g_input = self.guardrail_pipeline.process_input(tc.prompt)
            actual_output = tc.expected_output or f"Simulated agent response for: {g_input.sanitized_text}"
            actual_tools = tc.expected_tools or []

            tc_evals = []
            for evaluator in self.evaluators:
                res = await evaluator.evaluate(
                    prompt=tc.prompt,
                    actual_output=actual_output,
                    expected_output=tc.expected_output,
                    context_docs=tc.context_docs,
                    actual_tools_called=actual_tools,
                    expected_tools_called=tc.expected_tools,
                )
                tc_evals.append(res)
                if res.evaluator_name == "GroundednessEvaluator":
                    groundedness_scores.append(res.score)
                elif res.evaluator_name == "PIILeakageEvaluator" and res.passed:
                    pii_pass_count += 1

            passed_all = all(ev.passed for ev in tc_evals)
            avg_score = round(sum(ev.score for ev in tc_evals) / len(tc_evals), 2)
            if passed_all:
                passed_count += 1

            case_results.append(
                TestCaseEvalResult(
                    test_case_id=tc.id,
                    category=tc.category,
                    prompt=tc.prompt,
                    actual_output=actual_output,
                    evaluations=tc_evals,
                    passed_all=passed_all,
                    overall_score=avg_score,
                )
            )

        total_cases = len(cases)
        total_duration = round(time.time() - start_time, 2)
        avg_groundedness = (
            round(sum(groundedness_scores) / len(groundedness_scores), 2)
            if groundedness_scores
            else 1.0
        )
        pii_pass_rate = round((pii_pass_count / total_cases) * 100, 2) if total_cases > 0 else 100.0

        return BenchmarkSummaryReport(
            total_test_cases=total_cases,
            passed_count=passed_count,
            failed_count=total_cases - passed_count,
            accuracy_percentage=round((passed_count / total_cases) * 100, 2) if total_cases > 0 else 0.0,
            avg_groundedness_score=avg_groundedness,
            pii_safety_pass_rate=pii_pass_rate,
            total_duration_sec=total_duration,
            test_case_results=case_results,
        )
