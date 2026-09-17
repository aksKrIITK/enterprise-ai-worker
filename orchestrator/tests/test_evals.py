import pytest
from app.evals import (
    ToolCallAccuracyEvaluator,
    GroundednessEvaluator,
    PIILeakageEvaluator,
    LatencyAndCostEvaluator,
    BenchmarkRunner,
    DatasetLoader,
)


@pytest.mark.asyncio
async def test_tool_call_accuracy_evaluator():
    evaluator = ToolCallAccuracyEvaluator()
    res = await evaluator.evaluate(
        prompt="Query sales table",
        actual_output="Done",
        actual_tools_called=["sql_query"],
        expected_tools_called=["sql_query"],
    )
    assert res.passed
    assert res.score == 1.0


@pytest.mark.asyncio
async def test_groundedness_evaluator():
    evaluator = GroundednessEvaluator()
    res = await evaluator.evaluate(
        prompt="What is remote policy?",
        actual_output="Employees work remotely 3 days per week",
        context_docs=["Employees work remotely 3 days per week with manager approval"],
    )
    assert res.passed
    assert res.score > 0.5


@pytest.mark.asyncio
async def test_pii_leakage_evaluator():
    evaluator = PIILeakageEvaluator()
    res_clean = await evaluator.evaluate(prompt="Hi", actual_output="No sensitive data here")
    assert res_clean.passed
    assert res_clean.score == 1.0

    res_leak = await evaluator.evaluate(prompt="Hi", actual_output="Contact john@doe.com for info")
    assert not res_leak.passed
    assert res_leak.score == 0.0


@pytest.mark.asyncio
async def test_benchmark_runner():
    runner = BenchmarkRunner()
    report = await runner.run_benchmark()
    assert report.total_test_cases > 0
    assert report.accuracy_percentage >= 0.0
    assert report.avg_groundedness_score >= 0.0
    assert report.pii_safety_pass_rate >= 0.0
