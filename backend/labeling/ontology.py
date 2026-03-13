from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdapterDefinition:
    adapter_id: str
    description: str
    keywords: tuple[str, ...]


ADAPTER_ONTOLOGY: tuple[AdapterDefinition, ...] = (
    AdapterDefinition("python_core", "General Python programming", ("python", "py", "function", "class")),
    AdapterDefinition("sql_postgres", "PostgreSQL queries and schema work", ("sql", "select", "join", "postgres", "psql")),
    AdapterDefinition("react_hooks", "React Hooks and component logic", ("react", "hook", "useeffect", "usestate", "jsx")),
    AdapterDefinition("fastapi_service", "FastAPI endpoints and backend service code", ("fastapi", "router", "endpoint", "uvicorn")),
    AdapterDefinition("aws_boto3", "AWS SDK integration with boto3", ("aws", "boto3", "s3", "lambda", "iam")),
    AdapterDefinition("data_engineering_general", "Pipelines, ETL, and data processing", ("etl", "pipeline", "batch", "spark", "warehouse")),
    AdapterDefinition("typescript_core", "TypeScript language and typing", ("typescript", "ts", "interface", "type", "generic")),
    AdapterDefinition("general", "Fallback general-purpose adapter", ("general",)),
)


def list_adapter_ids() -> list[str]:
    return [item.adapter_id for item in ADAPTER_ONTOLOGY]


def ensure_known_adapter(adapter_id: str) -> str:
    known = set(list_adapter_ids())
    if adapter_id not in known:
        raise ValueError(f"Unknown adapter_id '{adapter_id}'. Must be one of: {sorted(known)}")
    return adapter_id


def ontology_prompt_block() -> str:
    lines = ["Allowed adapters (strict):"]
    for entry in ADAPTER_ONTOLOGY:
        lines.append(f"- {entry.adapter_id}: {entry.description}")
    return "\n".join(lines)
