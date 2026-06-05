# v0.6.0 — Public launch: docs, GTM, and community infrastructure

**Measure your routing. Then ship your completions.**

## Highlights

- Full documentation hub: OVERVIEW, QUICKSTART, FAQ, AUDIT, GTM
- Launch playbook + copy-paste posts for HN, Reddit, X, LinkedIn (`docs/SOCIAL.md`)
- `.env.example` for GPU onboarding
- GitHub Pages workflow for docs site
- Community: Discussions template, showcase issues, SUPPORT, FUNDING
- HuggingFace model card template for `sql_postgres`
- Profile README template to pin on @Anandb71
- `scripts/launch-smoke.ps1` — one-command demo verification

## Quick try (no GPU)

```bash
git clone https://github.com/Anandb71/LoRA-jit.git
cd LoRA-jit
pip install -e .[dev]
pytest tests/ -v
python scripts/run-benchmark.py examples/sample-trace.json --compare
```

## Measured reference numbers

| Metric | Value |
|--------|-------|
| Warm route (preload) | ~6 ms |
| SQL routing accuracy | ~99 % |
| Tests | 48 / 48 |

## Links

- [Documentation hub](https://github.com/Anandb71/LoRA-jit/tree/main/docs)
- [Launch checklist](https://github.com/Anandb71/LoRA-jit/blob/main/docs/LAUNCH.md)
- [Social copy](https://github.com/Anandb71/LoRA-jit/blob/main/docs/SOCIAL.md)

**Full changelog:** [CHANGELOG.md](https://github.com/Anandb71/LoRA-jit/blob/main/CHANGELOG.md)
