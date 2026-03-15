# Adapter Ontology

This file is the **authoritative registry** of valid adapter IDs for the LoRA-JIT system.

All offline labels, benchmark rows, and runtime adapter directories must use IDs from this list.
The auto-labeler and benchmark scorer both validate against this ontology and reject unknown IDs.

---

## Registered adapters

| Adapter ID | Domain |
|------------|--------|
| `python_core` | General Python programming — stdlib, common patterns, idiomatic Python |
| `sql_postgres` | PostgreSQL queries, schema design, migrations, parameterised SQL |
| `react_hooks` | React Hooks, component state, effects, context, and lifecycle patterns |
| `fastapi_service` | FastAPI endpoint design, dependency injection, Pydantic models |
| `aws_boto3` | AWS service integrations via the `boto3` SDK |
| `data_engineering_general` | ETL pipelines, data transforms, workflow orchestration |
| `typescript_core` | TypeScript type system, generics, utility types, type narrowing |
| `general` | Fallback generic adapter for mixed or unclassifiable context |

---

## Label schema

A valid label object must be structured as follows:

```json
{
  "primary_adapter": "sql_postgres",
  "acceptable_alternatives": ["data_engineering_general"],
  "confidence": 0.92,
  "reasoning": "File contains parameterised PostgreSQL SELECT statements with JOIN clauses"
}
```

| Field | Type | Constraint |
|-------|------|------------|
| `primary_adapter` | `string` | Must be in the registered adapter table above |
| `acceptable_alternatives` | `string[]` | Each entry must be in the registered table |
| `confidence` | `float` | Must be in `[0.0, 1.0]` |
| `reasoning` | `string` | Free text; used for audit and debugging |

---

## Adding a new adapter

To register a new adapter:

1. Add a row to the **Registered adapters** table above.
2. Update the heuristic rules in `backend/labeling/ontology.py`.
3. Build a training dataset under `data/<adapter_id>/train.jsonl`.
4. Train and export with `scripts/train-peft-adapter.py`.
5. Re-train the learned router on any updated benchmark corpus.
6. Update `docs/BENCHMARK.md` if the new adapter changes scoring interpretation.

Changes to this file are considered **breaking changes** for any stored benchmark datasets
that reference the old ontology.
