# LoRA-JIT Launch Playbook

**Owner:** [@Anandb71](https://github.com/Anandb71) · **Repo:** [github.com/Anandb71/LoRA-jit](https://github.com/Anandb71/LoRA-jit)

Use this as your single checklist for the public launch. Copy-paste posts live in [SOCIAL.md](./SOCIAL.md).

---

## Pre-launch (done in repo)

- [x] Documentation hub ([INDEX.md](./INDEX.md))
- [x] Public audit ([AUDIT.md](./AUDIT.md))
- [x] GTM strategy ([GTM.md](./GTM.md))
- [x] `.env.example` for GPU onboarding
- [x] Version aligned to `0.6.0`
- [x] Cross-platform QUICKSTART
- [x] Social preview asset (`docs/assets/demo-teaser.svg`)
- [x] GitHub Pages workflow (docs site)
- [x] Launch copy ([SOCIAL.md](./SOCIAL.md))

## Launch day (you — 30 minutes)

### 1. Verify live repo

```bash
git pull origin main
pytest tests/ -v
python scripts/run-benchmark.py examples/sample-trace.json --compare
```

### 2. Post Show HN

Copy from [SOCIAL.md — Hacker News](./SOCIAL.md#hacker-news-show-hn)

URL: https://news.ycombinator.com/submit

### 3. Post r/LocalLLaMA

Copy from [SOCIAL.md — Reddit](./SOCIAL.md#reddit-rlocalllama)

### 4. Post X / Twitter thread

Copy from [SOCIAL.md — X / Twitter](./SOCIAL.md#x--twitter)

Pin the repo link. Attach `docs/assets/demo-teaser.svg` or a screen recording.

### 5. LinkedIn (optional)

Copy from [SOCIAL.md — LinkedIn](./SOCIAL.md#linkedin)

### 6. HuggingFace (when adapter weights ready)

Follow [huggingface/MODEL_CARD.md](./huggingface/MODEL_CARD.md)

---

## Week 1 follow-through

| Day | Action |
|-----|--------|
| D+0 | Reply to every HN comment within 2 hours |
| D+0 | Enable notifications on GitHub Issues + Discussions |
| D+1 | Post architecture summary (link `docs/ARCHITECTURE.md`) on X |
| D+2 | Submit PR to [awesome-local-llm](https://github.com/jmorgan8790/awesome-local-llm) — template in SOCIAL.md |
| D+3 | Record 60s screen demo: cold_miss → warm_hit + status bar |
| D+7 | Publish "Week 1" metrics thread (stars, clones, issues) |

---

## North star metrics (track weekly)

| Metric | Week 1 target |
|--------|---------------|
| GitHub stars | 200+ |
| Forks | 20+ |
| Unique clones | 100+ |
| Issues / Discussions opened | 5+ |
| External mentions (blogs, Reddit, HN points) | 3+ |

---

## What to say when asked "Is this Copilot?"

> No — LoRA-JIT is open **adapter routing infrastructure**. It measures which LoRA specialist to load based on your editor context, with published benchmarks. Completions are API-level today; inline UX is on the roadmap. Think routing layer, not assistant product.

---

## Support channels

- **Bugs:** GitHub Issues
- **Ideas / showcases:** GitHub Discussions
- **Security:** [SECURITY.md](../SECURITY.md)

---

*Strategy detail: [GTM.md](./GTM.md)*
