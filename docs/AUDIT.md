# Public Release Audit

This document is for **reviewers, auditors, and potential adopters** evaluating LoRA-JIT for production use, open-source contribution, or commercial integration.

Last reviewed: **2026-06-06**

---

## Executive summary

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Code quality & tests | **A** | 48 passing tests, ruff lint, TypeScript type-check, CI on every push |
| Architecture & docs | **A** | Clear separation of concerns, comprehensive ARCHITECTURE and BENCHMARK docs |
| Security posture | **B+** | Local-only binding, documented threat model; no auth by design |
| End-user UX | **C** | Extension is observability-first; no inline completions or marketplace listing |
| ML production readiness | **B-** | Real PEFT path works; paging is simulated; one training recipe shipped |
| Release hygiene | **B** | MIT license, CHANGELOG, issue templates; version metadata recently aligned |

**Verdict:** LoRA-JIT is **audit-ready as an open research/engineering repository**. It is **not yet audit-ready as a consumer coding assistant product**.

---

## What is production-grade today

### Backend control plane

- FastAPI daemon with OpenAPI at `/docs`
- Pydantic v2 contracts shared across all layers
- `JitRouter`: predict → page → activate loop with structured decision objects
- Four pluggable predictors (structural, text, embedding, learned)
- `PagingSimulator` with LRU eviction and optional MB budget
- `MockRuntime` and `PyTorchPeftRuntime` behind a common interface
- Trace recording, telemetry buffering, gap detection
- Full benchmark harness with predictor comparison

### Testing and CI

- 48 pytest tests covering routing, paging, runtime, benchmarks, labeling
- GitHub Actions: Python lint + test + extension TypeScript check
- No GPU required for CI — `MockRuntime` default

### Documentation and governance

- README, ARCHITECTURE, BENCHMARK, ADAPTER_ONTOLOGY
- CONTRIBUTING, SECURITY, CODE_OF_CONDUCT
- Issue templates (bug, feature), PR template
- `.env.example` for GPU path configuration
- MIT LICENSE

### Measured performance (documented, reproducible)

Reference: RTX 3050 6 GB, Qwen1.5-0.5B + sql_postgres LoRA

- Warm route latency: 6–20 ms (with preload)
- Cold route latency: ~6 700 ms (without preload)
- Router confidence on SQL: ~99 % (learned predictor)

---

## Known gaps (honest inventory)

### Critical — blocks "product" positioning

| Gap | Risk | Mitigation path |
|-----|------|-----------------|
| No inline VS Code completions | Users expect ghost text; extension only logs | Add `InlineCompletionItemProvider` |
| Extension not on Marketplace | Requires dev-host F5 | Publish with icon, README, prepublish script |
| No pre-built adapter weights | High friction before seeing real value | Ship `sql_postgres` on HuggingFace + LFS |
| Hardcoded daemon URL in extension | Cannot point at remote/custom port | Add `loraJit.daemonUrl` setting |

### Important — blocks polished OSS launch

| Gap | Risk | Mitigation path |
|-----|------|-----------------|
| Paging is simulated, not VRAM-backed | "JIT paging" claim needs qualification | Integrate nvidia-smi or torch memory stats |
| Only one training recipe (`sql_postgres`) | 7 other ontology adapters are registry-only | Add dataset builders per adapter |
| No PyPI publish | `pip install lora-jit` unavailable | Add publish workflow + classifiers |
| No Docker image | Harder reproducible demos | Add docker-compose for daemon |
| No GPU CI smoke test | PyTorch path untested in CI | Nightly workflow with self-hosted GPU runner |

### Architectural limitations (by design or deferred)

| Limitation | Detail |
|------------|--------|
| Single-user localhost | Daemon binds 127.0.0.1, no auth |
| Single base model | No multi-model routing |
| Generation latency | Seconds on consumer GPU, not Copilot-speed |
| Structural router | Keyword heuristics, not semantic understanding |
| LLM labeling optional | Offline annotation requires external API |

---

## Release tiers

### Tier 1 — Research / OSS (current)

**Status: Ready**

- Clone, test, benchmark, train one adapter, observe routing in VS Code dev host
- Audience: ML engineers, researchers, OSS contributors
- Launch: GitHub public repo, HN "Show HN", benchmark narrative

### Tier 2 — Developer preview

**Status: Not ready — 4–6 weeks estimated**

Requirements:

- [ ] VS Code Marketplace extension
- [ ] `loraJit.daemonUrl` configuration
- [ ] Inline completion provider (minimum viable)
- [ ] Pre-built `sql_postgres` adapter on HuggingFace
- [ ] 60-second demo video
- [ ] GitHub Release with tagged version

### Tier 3 — Product / platform

**Status: Not ready — 3–6 months estimated**

Requirements:

- [ ] 3+ adapter training recipes with published weights
- [ ] Real VRAM telemetry
- [ ] PyPI package
- [ ] Continue.dev / Ollama integration adapters
- [ ] Multi-user daemon mode (optional, authenticated)

---

## Audit checklist for integrators

Use this checklist when embedding LoRA-JIT into another product:

### Security

- [ ] Daemon is not exposed beyond localhost
- [ ] No secrets in `.env` committed to version control
- [ ] `LORA_JIT_STRICT_RUNTIME=true` in production GPU paths
- [ ] Reviewed [SECURITY.md](../SECURITY.md) threat model

### Functional

- [ ] Predictor choice documented for your domain (`structural` vs `learned`)
- [ ] Benchmark run on representative traces before go-live
- [ ] Adapter artifacts verified with `verify-adapter.py`
- [ ] Preload configured for latency-sensitive adapters
- [ ] Fallback behavior understood (stub vs HTTP 500)

### Operational

- [ ] GPU memory budget assessed (base model + hot adapter count)
- [ ] Cold-miss latency acceptable for your UX
- [ ] Trace retention policy for `traces/` directory
- [ ] CI parity: tests pass with `MockRuntime` in your fork

### Legal

- [ ] MIT license compatible with your product
- [ ] HuggingFace model license reviewed for base model (`Qwen/Qwen1.5-0.5B`)
- [ ] Training data provenance documented for custom adapters

---

## Component maturity matrix

| Component | Maturity | Test coverage | Docs |
|-----------|----------|---------------|------|
| `JitRouter` | Stable | High | ARCHITECTURE |
| `PagingSimulator` | Stable (simulated) | High | ARCHITECTURE |
| `MockRuntime` | Stable | High | README |
| `PyTorchPeftRuntime` | Beta | Medium | README, QUICKSTART |
| Structural predictor | Stable | High | BENCHMARK |
| Learned predictor | Beta | High | BENCHMARK |
| Benchmark harness | Stable | High | BENCHMARK |
| Trace compiler | Stable | Medium | BENCHMARK |
| Auto-labeler | Beta | Medium | ADAPTER_ONTOLOGY |
| VS Code extension | Alpha | None (manual) | vscode-extension/README |
| PEFT training pipeline | Beta | Medium | QUICKSTART |

---

## How to reproduce audit claims

```bash
# 1. Clone and verify tests
git clone https://github.com/Anandb71/LoRA-jit.git && cd LoRA-jit
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest tests/ -v                    # expect 48 passed

# 2. Verify paging loop (mock runtime)
python scripts/run-daemon.py &
curl -s http://127.0.0.1:8765/health

# 3. Benchmark smoke test
python scripts/run-benchmark.py examples/sample-trace.json --compare

# 4. GPU path (optional, requires NVIDIA GPU)
pip install -e .[runtime]
cp .env.example .env
# configure pytorch backend, train adapter per QUICKSTART.md
```

---

## Contact

- Security issues: see [SECURITY.md](../SECURITY.md)
- General questions: [GitHub Discussions](https://github.com/Anandb71/LoRA-jit/discussions) or Issues
- Commercial inquiries: open a GitHub Issue with label `partnership`
