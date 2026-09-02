from fastapi import APIRouter, Depends, Header, HTTPException
from typing import List, Optional
import logging

from app.evals.dataset import DatasetLoader, BenchmarkTestCase
from app.evals.benchmark_runner import BenchmarkRunner, BenchmarkSummaryReport
from app.api.chat import verify_service_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])


@router.get("/benchmarks", response_model=List[BenchmarkTestCase])
async def get_benchmark_test_cases(authenticated: bool = Depends(verify_service_token)):
    """Retrieves all benchmark evaluation test cases."""
    return DatasetLoader.get_benchmark_cases()


@router.post("/run", response_model=BenchmarkSummaryReport)
async def run_evaluation_benchmark(
    custom_cases: Optional[List[BenchmarkTestCase]] = None,
    authenticated: bool = Depends(verify_service_token),
):
    """
    Executes the automated evaluation benchmark suite across evaluators
    (Tool Call Accuracy, Groundedness RAG Precision, PII Leakage, Latency/Cost).
    """
    logger.info("Executing evaluation benchmark suite...")
    runner = BenchmarkRunner()
    report = await runner.run_benchmark(test_cases=custom_cases)
    logger.info(
        "Benchmark complete: %d/%d passed (Accuracy: %.2f%%)",
        report.passed_count,
        report.total_test_cases,
        report.accuracy_percentage,
    )
    return report
