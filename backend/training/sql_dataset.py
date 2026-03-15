from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SqlExampleTemplate:
    instruction: str
    input_template: str
    response_template: str


_SQL_INTENTS = [
    "optimize this PostgreSQL query",
    "debug this SQL statement",
    "rewrite this query for better performance",
    "fix correctness issues in this query",
    "improve readability and indexing strategy",
]

_SQL_SCHEMAS = [
    "users(id, email, created_at), orders(id, user_id, total, status, created_at)",
    "accounts(id, plan, region), invoices(id, account_id, amount, paid_at)",
    "products(id, sku, category), line_items(id, order_id, product_id, qty, price)",
    "sessions(id, user_id, started_at), events(id, session_id, event_type, created_at)",
    "teams(id, org_id), memberships(id, team_id, user_id, role)",
]

_SQL_TEMPLATES: tuple[SqlExampleTemplate, ...] = (
    SqlExampleTemplate(
        instruction="{intent}. Focus on JOIN strategy and indexes.",
        input_template=(
            "Schema: {schema}\n"
            "Query:\n"
            "SELECT u.id, COUNT(o.id) AS orders_count\n"
            "FROM users u LEFT JOIN orders o ON o.user_id = u.id\n"
            "WHERE o.status = 'paid' AND o.created_at >= NOW() - INTERVAL '30 days'\n"
            "GROUP BY u.id\n"
            "ORDER BY orders_count DESC\n"
            "LIMIT 50;"
        ),
        response_template=(
            "Use an INNER JOIN after pushing the status/date filters into a subquery to preserve index usage, "
            "and add a partial index on orders(user_id, created_at) WHERE status='paid'.\n"
            "\n"
            "Rewritten query:\n"
            "SELECT o.user_id AS id, COUNT(*) AS orders_count\n"
            "FROM orders o\n"
            "WHERE o.status = 'paid'\n"
            "  AND o.created_at >= NOW() - INTERVAL '30 days'\n"
            "GROUP BY o.user_id\n"
            "ORDER BY orders_count DESC\n"
            "LIMIT 50;"
        ),
    ),
    SqlExampleTemplate(
        instruction="{intent}. Fix null-handling and aggregation correctness.",
        input_template=(
            "Schema: {schema}\n"
            "Query:\n"
            "SELECT account_id, SUM(amount) / COUNT(*) AS avg_invoice\n"
            "FROM invoices\n"
            "WHERE paid_at >= DATE_TRUNC('month', NOW())\n"
            "GROUP BY account_id;"
        ),
        response_template=(
            "Guard against division by zero and use AVG directly for clarity.\n"
            "\n"
            "Rewritten query:\n"
            "SELECT account_id, AVG(amount) AS avg_invoice\n"
            "FROM invoices\n"
            "WHERE paid_at >= DATE_TRUNC('month', NOW())\n"
            "GROUP BY account_id;"
        ),
    ),
    SqlExampleTemplate(
        instruction="{intent}. Improve pagination and determinism.",
        input_template=(
            "Schema: {schema}\n"
            "Query:\n"
            "SELECT id, email, created_at\n"
            "FROM users\n"
            "ORDER BY created_at DESC\n"
            "LIMIT 100 OFFSET 10000;"
        ),
        response_template=(
            "Prefer keyset pagination to avoid large OFFSET scans.\n"
            "\n"
            "Rewritten query:\n"
            "SELECT id, email, created_at\n"
            "FROM users\n"
            "WHERE created_at < :cursor_created_at\n"
            "ORDER BY created_at DESC\n"
            "LIMIT 100;"
        ),
    ),
    SqlExampleTemplate(
        instruction="{intent}. Reduce expensive DISTINCT usage.",
        input_template=(
            "Schema: {schema}\n"
            "Query:\n"
            "SELECT DISTINCT p.category\n"
            "FROM products p\n"
            "JOIN line_items li ON li.product_id = p.id\n"
            "JOIN orders o ON o.id = li.order_id\n"
            "WHERE o.created_at >= NOW() - INTERVAL '90 days';"
        ),
        response_template=(
            "Use EXISTS for semi-join semantics to avoid duplicate expansion.\n"
            "\n"
            "Rewritten query:\n"
            "SELECT p.category\n"
            "FROM products p\n"
            "WHERE EXISTS (\n"
            "  SELECT 1\n"
            "  FROM line_items li\n"
            "  JOIN orders o ON o.id = li.order_id\n"
            "  WHERE li.product_id = p.id\n"
            "    AND o.created_at >= NOW() - INTERVAL '90 days'\n"
            ");"
        ),
    ),
)


def format_chat_example(instruction: str, sql_input: str, response: str) -> str:
    return (
        "<|system|>You are a PostgreSQL query optimization assistant.</s>"
        f"<|user|>{instruction}\n\n{sql_input}</s>"
        f"<|assistant|>{response}</s>"
    )


def generate_sql_postgres_examples(*, size: int = 800, seed: int = 17) -> list[dict[str, str]]:
    if size <= 0:
        raise ValueError("size must be > 0")

    rng = random.Random(seed)
    rows: list[dict[str, str]] = []

    for _ in range(size):
        template = rng.choice(_SQL_TEMPLATES)
        intent = rng.choice(_SQL_INTENTS)
        schema = rng.choice(_SQL_SCHEMAS)

        instruction = template.instruction.format(intent=intent)
        sql_input = template.input_template.format(schema=schema)
        response = template.response_template
        text = format_chat_example(instruction, sql_input, response)

        rows.append(
            {
                "domain": "sql_postgres",
                "instruction": instruction,
                "input": sql_input,
                "response": response,
                "text": text,
            }
        )

    return rows


def write_jsonl(rows: list[dict[str, str]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path
