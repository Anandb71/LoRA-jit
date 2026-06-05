# LoRA-JIT Documentation

Welcome to the documentation hub for **LoRA-JIT** — a local, benchmark-first system for routing and hot-swapping domain-specific LoRA adapters inside VS Code.

---

## Start here

| Document | Audience | What you'll learn |
|----------|----------|-------------------|
| [OVERVIEW.md](./OVERVIEW.md) | Everyone | What LoRA-JIT is, what it is not, and why it exists |
| [QUICKSTART.md](./QUICKSTART.md) | New users | Install, run tests, start the daemon (Windows, macOS, Linux) |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Engineers | Component design, data flows, runtime tiers |
| [BENCHMARK.md](./BENCHMARK.md) | ML / systems engineers | How to measure routing accuracy and latency |
| [ADAPTER_ONTOLOGY.md](./ADAPTER_ONTOLOGY.md) | Contributors | Canonical adapter ID registry |
| [FAQ.md](./FAQ.md) | Troubleshooters | Common errors and honest capability limits |
| [AUDIT.md](./AUDIT.md) | Reviewers & auditors | Release readiness checklist and known gaps |

---

## Repository map

```
backend/           Python daemon, routing, paging, runtime, benchmarks
vscode-extension/  Editor telemetry client and JIT observability UI
scripts/           CLI workflows (daemon, train, benchmark, verify)
examples/          Sample traces and seed router artifacts
tests/             48-test regression suite (MockRuntime, no GPU)
docs/              You are here
```

---

## Typical workflows

### Evaluate routing without a GPU

1. [QUICKSTART.md](./QUICKSTART.md) → install and run daemon
2. `python scripts/run-benchmark.py examples/sample-trace.json --compare`
3. Read [BENCHMARK.md](./BENCHMARK.md) for full trace-to-score pipeline

### Run real LoRA inference locally

1. Copy [`.env.example`](../.env.example) to `.env`
2. Follow **Real GPU path** in [QUICKSTART.md](./QUICKSTART.md)
3. Train `sql_postgres` adapter with `scripts/train-peft-adapter.py`

### Contribute or audit the codebase

1. [CONTRIBUTING.md](../CONTRIBUTING.md) — dev setup and PR checklist
2. [AUDIT.md](./AUDIT.md) — maturity matrix and release tiers
3. [SECURITY.md](../SECURITY.md) — threat model and reporting

---

## External links

- [GitHub repository](https://github.com/Anandb71/LoRA-jit)
- [OpenAPI docs](http://127.0.0.1:8765/docs) (when daemon is running)
- [CHANGELOG.md](../CHANGELOG.md)
