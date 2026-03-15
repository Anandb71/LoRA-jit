# Contributing to LoRA-JIT

Thank you for considering a contribution.

---

## Development setup

### Backend

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

### VS Code extension

```powershell
cd vscode-extension
npm install
```

---

## Running tests and lint

```powershell
# All backend tests (no GPU required)
pytest tests/ -v

# Python lint
python -m ruff check .

# TypeScript type-check
cd vscode-extension && npm run lint
```

All of the above must pass before opening a pull request.

---

## Pull request checklist

- [ ] Changes are focused and atomic — one logical concern per PR
- [ ] New or changed behaviour is covered by tests
- [ ] Lint and tests pass locally
- [ ] API or workflow changes are reflected in the relevant `docs/` file
- [ ] Related issues are referenced in the PR description

---

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When to use |
|--------|-------------|
| `feat:` | New functionality |
| `fix:` | Bug fixes |
| `docs:` | Documentation-only changes |
| `test:` | Test-only changes |
| `chore:` | Maintenance, dependencies, tooling |
| `refactor:` | Code restructuring without behaviour change |
| `perf:` | Performance improvements |

Scope the commit to a subsystem where helpful:
`feat(runtime):`, `fix(router):`, `docs(benchmark):`, etc.

---

## Code review

- Be specific and constructive — cite the relevant code rather than speaking in generalities.
- Discuss trade-offs before requesting large rewrites.
- Correctness, maintainability, and reproducibility take priority over style preferences.
- Approving a PR is a statement that you have read it and believe it is safe to merge.

---

## Adding a new adapter

1. Add the adapter ID to `docs/ADAPTER_ONTOLOGY.md`.
2. Build a training dataset under `data/<adapter_id>/train.jsonl`.
3. Train with `scripts/train-peft-adapter.py`.
4. Validate with `scripts/verify-adapter.py`.
5. Update the labeling heuristics in `backend/labeling/ontology.py` if needed.

---

## Adding a new predictor

1. Implement the `predict(event: TelemetryEvent) -> RoutingDecision` interface.
2. Register it in `backend/routing/factory.py`.
3. Add a benchmark test in `tests/test_benchmark_runner.py`.
4. Document it in `docs/BENCHMARK.md`.
