---
layout: default
title: LoRA-JIT Documentation
---

# LoRA-JIT Documentation

Welcome to the documentation hub for **LoRA-JIT** — a local, benchmark-first system for routing and hot-swapping domain-specific LoRA adapters inside VS Code.

---

## Start here

| Document | Audience | What you'll learn |
|----------|----------|-------------------|
| [Overview](OVERVIEW.md) | Everyone | What LoRA-JIT is, what it is not, and why it exists |
| [Quickstart](QUICKSTART.md) | New users | Install, run tests, start the daemon (Windows, macOS, Linux) |
| [Architecture](ARCHITECTURE.md) | Engineers | Component design, data flows, runtime tiers |
| [Benchmark](BENCHMARK.md) | ML / systems engineers | How to measure routing accuracy and latency |
| [Adapter ontology](ADAPTER_ONTOLOGY.md) | Contributors | Canonical adapter ID registry |
| [FAQ](FAQ.md) | Troubleshooters | Common errors and honest capability limits |
| [Audit](AUDIT.md) | Reviewers & auditors | Release readiness checklist and known gaps |

---

## Quick try (no GPU)

```bash
git clone https://github.com/Anandb71/LoRA-jit.git
cd LoRA-jit
pip install -e .[dev]
pytest tests/ -v
python scripts/run-benchmark.py examples/sample-trace.json --compare
```

---

## External links

- [GitHub repository](https://github.com/Anandb71/LoRA-jit)
- [Contributing](https://github.com/Anandb71/LoRA-jit/blob/main/CONTRIBUTING.md)
- [Changelog](https://github.com/Anandb71/LoRA-jit/blob/main/CHANGELOG.md)
- [Security policy](https://github.com/Anandb71/LoRA-jit/blob/main/SECURITY.md)
