# Adapter Ontology (Authoritative)

This file defines the allowed adapter IDs for offline labeling and benchmark scoring.

## Allowed adapters

- `python_core` — general Python programming
- `sql_postgres` — PostgreSQL query/schema/database tasks
- `react_hooks` — React Hooks and component state/effects
- `fastapi_service` — FastAPI endpoint and service-layer backend code
- `aws_boto3` — AWS integrations via boto3
- `data_engineering_general` — ETL/pipeline/data workflow tasks
- `typescript_core` — TypeScript typing and language constructs
- `general` — fallback generic adapter

## Label schema contract

A valid label must be structured as JSON:

- `primary_adapter`: string (must be in ontology)
- `acceptable_alternatives`: string[] (each must be in ontology)
- `confidence`: float in `[0, 1]`
- `reasoning`: string

## Why this exists

Without a fixed ontology, offline labeling can hallucinate adapter IDs and invalidate benchmark comparisons. This file is the single source of truth for label validity.
