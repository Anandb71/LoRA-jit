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


def test_multilabel_scoring_grants_partial_credit(tmp_path: Path) -> None:
        trace_path = tmp_path / "rows.json"
        trace_path.write_text(
                """
[
    {
        "event": {
            "session_id": "s1",
            "file_path": "src/typescript_core/module.ts",
            "language_id": "typescript",
            "cursor_line": 0,
            "cursor_column": 0,
            "symbols_in_scope": ["typescript_core", "Widget"],
            "metadata": {"query": "type annotations"}
        },
        "expected_adapter": "sql_postgres",
        "expected_label": {
            "primary_adapter": "sql_postgres",
            "acceptable_alternatives": ["typescript_core"],
            "confidence": 0.91,
            "reasoning": "mixed context"
        }
    }
]
""".strip(),
                encoding="utf-8",
        )

        runner = BenchmarkRunner()
        result = runner.run_trace(trace_path=str(trace_path), predictor="structural")
        assert result.top1_accuracy == 0.5
