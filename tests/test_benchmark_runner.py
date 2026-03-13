from pathlib import Path

from backend.benchmark.runner import BenchmarkRunner


def test_run_trace_supports_all_predictors() -> None:
    trace_path = str(Path("examples") / "sample-trace.json")
    runner = BenchmarkRunner()

    for predictor in ["structural", "text", "embedding"]:
        result = runner.run_trace(trace_path=trace_path, predictor=predictor)
        assert result.predictor == predictor
        assert result.events_processed == 2
        assert 0.0 <= result.top1_accuracy <= 1.0
        assert 0.0 <= result.cache_miss_rate <= 1.0


def test_compare_predictors_returns_winner() -> None:
    trace_path = str(Path("examples") / "sample-trace.json")
    runner = BenchmarkRunner()

    comparison = runner.compare_predictors(trace_path=trace_path)
    assert len(comparison.results) == 3
    assert comparison.winner_by_accuracy in {"structural", "text", "embedding"}
