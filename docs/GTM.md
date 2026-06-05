# Go-To-Market Strategy

**LoRA-JIT — Category creation for measurable, local LoRA adapter routing**

Document version: 1.0 · June 2026 · Internal + public strategy reference

---

## Table of contents

1. [Strategic thesis](#1-strategic-thesis)
2. [Market landscape](#2-market-landscape)
3. [Positioning and category](#3-positioning-and-category)
4. [Target segments and personas](#4-target-segments-and-personas)
5. [Value proposition canvas](#5-value-proposition-canvas)
6. [Competitive moat](#6-competitive-moat)
7. [Product wedge and expansion path](#7-product-wedge-and-expansion-path)
8. [Launch narrative](#8-launch-narrative)
9. [Channel strategy](#9-channel-strategy)
10. [Content and community flywheel](#10-content-and-community-flywheel)
11. [Partnership map](#11-partnership-map)
12. [Pricing and monetization](#12-pricing-and-monetization)
13. [90-day execution plan](#13-90-day-execution-plan)
14. [Metrics and north stars](#14-metrics-and-north-stars)
15. [Risks and mitigations](#15-risks-and-mitigations)
16. [The one big bet](#16-the-one-big-bet)

---

## 1. Strategic thesis

### The insight

The AI coding assistant market is converging on **one big model in the cloud**. Meanwhile, the ML engineering world is converging on **many small specialists** (LoRA adapters on shared bases) running **locally** for privacy, cost, and control.

Nobody owns the **middle layer**: the orchestration that decides *which* specialist to load, *when*, based on *what the developer is actually doing* — with **published benchmarks** proving it works.

LoRA-JIT can become that layer.

### The opportunity window (2026–2028)

| Trend | Why it matters for LoRA-JIT |
|-------|----------------------------|
| Local LLM adoption (Ollama, LM Studio, llama.cpp) | Developers already run models locally; they hit the "one model can't do everything" wall |
| PEFT / LoRA maturity (HuggingFace, Unsloth) | Training domain adapters is democratized; routing is the new bottleneck |
| Enterprise AI privacy mandates | Regulated industries need on-prem code AI; cloud Copilot is a non-starter |
| IDE fragmentation (Cursor, Windsurf, VS Code + extensions) | Routing infrastructure that is IDE-agnostic (HTTP API) wins over monolithic assistants |
| Benchmark culture in ML (MMLU, HumanEval) | No standard benchmark exists for **adapter routing** — first mover defines the category |

### What we are selling (in order)

1. **Trust** — "Here are the numbers: 99% routing accuracy, 6 ms warm latency"
2. **Infrastructure** — daemon + router + paging + benchmark harness
3. **Experience** — VS Code extension with visible JIT decisions
4. **Ecosystem** — pre-built adapters, integrations, marketplace

Do not lead with #4. Lead with #1.

---

## 2. Market landscape

### Competitive map

```
                    CLOUD                          LOCAL
              ┌─────────────────┐         ┌─────────────────────────┐
   Single     │ GitHub Copilot  │         │ Ollama / LM Studio      │
   model      │ Cursor / Cody   │         │ Continue.dev (1 model)  │
              └─────────────────┘         └─────────────────────────┘
                    │                              │
                    │         ┌────────────────────┘
                    │         │
   Multi-     ┌────▼─────────▼────┐
   adapter    │   ★ LoRA-JIT ★    │  ← open, benchmarked, IDE-integrated
   routing    │  (this project)     │
              └───────────────────┘
                    │
              ┌─────▼─────────────┐
   Server-    │ vLLM multi-LoRA   │  ← server-side, not IDE-context-aware
   side       │ TGI LoRA serving  │
              └───────────────────┘
```

### Alternative-by-alternative positioning

| Alternative | Their pitch | LoRA-JIT counter |
|-------------|-------------|------------------|
| **GitHub Copilot** | Fast, integrated, zero setup | "Copilot picks one model. We pick the right specialist — locally, measurably." |
| **Cursor** | AI-native IDE | "Cursor is the product. LoRA-JIT is the routing layer any IDE can plug into." |
| **Continue.dev** | Open, local, flexible | "Continue runs one model. LoRA-JIT orchestrates many — with paging and benchmarks." |
| **Ollama** | Dead-simple local inference | "Ollama serves models. LoRA-JIT routes to the right LoRA based on your cursor." |
| **vLLM multi-LoRA** | Production serving at scale | "vLLM is server infrastructure. LoRA-JIT is developer-context routing in the IDE." |
| **Manual LoRA swap** | Full control | "You shouldn't manually pick adapters. Your editor already knows what domain you're in." |

### Market sizing (TAM → SAM → SOM)

| Layer | Estimate | Rationale |
|-------|----------|-----------|
| **TAM** | ~30M professional developers globally | Any dev using AI-assisted coding |
| **SAM** | ~3M developers running local LLMs or training LoRA | Ollama download stats, HF PEFT usage, privacy-sensitive orgs |
| **SOM (Year 1)** | 5 000–15 000 GitHub stars, 500 active daemon users, 50 contributors | Realistic for a focused OSS launch with strong benchmark narrative |

Revenue SOM (if monetized Year 2): 20–50 enterprise pilots at $15–50K ACV = $300K–$2.5M ARR potential.

---

## 3. Positioning and category

### Category name (proposed)

**"JIT Adapter Routing"** or **"Context-Aware LoRA Orchestration"**

Avoid competing in "AI code completion" — you will lose on UX against Copilot on day one. Own a **new category** where benchmarks are the product.

### Positioning statement

> For ML engineers and privacy-conscious development teams who need domain-specific code AI without cloud dependency, **LoRA-JIT** is the **open adapter routing infrastructure** that automatically selects and hot-swaps LoRA specialists based on live editor context — unlike Copilot or Ollama, LoRA-JIT **proves routing quality with published benchmarks** before you ship completions.

### Tagline options (ranked)

1. **"Measure your routing. Then ship your completions."** ← recommended launch tagline
2. "The JIT compiler for LoRA adapters"
3. "One base model. Many domain experts. Zero manual switching."
4. "Local code AI with receipts"

### Messaging hierarchy

| Level | Message |
|-------|---------|
| **Headline** | Context-aware LoRA adapter routing for VS Code |
| **Subhead** | Route, page, and hot-swap domain specialists locally — with benchmarked accuracy |
| **Proof** | 99% SQL routing accuracy · 6 ms warm latency · 48/48 tests · MIT open source |
| **CTA** | Clone → benchmark in 10 minutes → train your first adapter |

---

## 4. Target segments and personas

### Primary beachhead: "The Local-First ML Engineer"

**Demographics:** 25–40, backend/ML systems role, already uses PyTorch/PEFT/Ollama

**Pain:**

- Trained 3 LoRA adapters (SQL, FastAPI, React) but runs one at a time manually
- No way to measure if routing heuristics actually work
- Frustrated that Copilot sends code to the cloud

**Jobs to be done:**

1. Automatically pick the right adapter while coding
2. Prove routing accuracy with numbers before demoing to team
3. Keep everything on localhost

**Where they hang out:** Hacker News, r/LocalLLaMA, HuggingFace forums, ML Twitter/X, PyTorch Discord

**Acquisition hook:** "I benchmarked adapter routing on my repo — here's the JSON"

---

### Secondary: "The Regulated-Industry Platform Team"

**Demographics:** Staff engineer at fintech, healthcare, defense contractor

**Pain:**

- Legal blocked Copilot
- Internal LLM pilot stuck at "one general model"
- Need audit trail for which model saw which code

**Jobs to be done:**

1. On-prem code assistance with domain specialists
2. Observable routing decisions for compliance
3. Reproducible benchmark reports for security review

**Acquisition hook:** [AUDIT.md](./AUDIT.md) + local-only architecture + trace recording

---

### Tertiary: "The DevTools Founder"

**Demographics:** Building an AI-native IDE or extension startup

**Pain:**

- Routing is hard; they don't want to build paging + benchmarks from scratch
- Need differentiation vs Copilot clone positioning

**Jobs to be done:**

1. Embed adapter routing via HTTP API
2. White-label benchmark harness for their marketing

**Acquisition hook:** MIT license + clean API + modular architecture

---

### Anti-personas (do not optimize for yet)

- Casual developers who want zero-setup ghost text (they should use Copilot)
- Teams without GPU budget expecting instant local inference
- Enterprise buyers needing SOC2-certified hosted SaaS today

---

## 5. Value proposition canvas

| Customer job | Pain | Gain | LoRA-JIT feature | Metric |
|--------------|------|------|------------------|--------|
| Pick right model while coding | Manual adapter switching | Automatic domain detection | `JitRouter` + editor telemetry | top1_accuracy |
| Fast enough to feel instant | 6+ s cold loads | Warm adapter in ms | Preload + paging simulator | warm_hit latency |
| Trust the routing | Black-box model selection | Logged decisions + confidence | Output channel + API response | confidence score |
| Prove it to team | "It feels right" | Benchmark report JSON | `BenchmarkRunner` + compare | benchmark artifact |
| Keep code private | Cloud exfiltration risk | 127.0.0.1 daemon | Local-first architecture | zero egress |
| Train domain experts | General model weak on SQL | LoRA fine-tune pipeline | `train-peft-adapter.py` | adapter artifact |

---

## 6. Competitive moat

### Defensible advantages (build these deliberately)

| Moat | How to deepen |
|------|---------------|
| **Benchmark corpus** | Publish LoRA-JIT-Trace-1K: 1000 annotated editor sessions as a standard routing dataset |
| **Ontology registry** | Become the de facto adapter ID schema (like MIME types for LoRA domains) |
| **Learned router artifact** | Lightweight JSON model — easy to ship, hard to replicate without your benchmark data |
| **JIT observability UX** | Status bar + structured logs — developers *see* routing; competitors hide it |
| **Full-stack open source** | Extension + daemon + training + benchmark in one repo — integration cost for forks |
| **First benchmark publication** | arXiv paper: "Benchmarking Context-Aware LoRA Routing in IDEs" |

### Non-moats (do not rely on)

- Heuristic structural router (trivial to copy)
- MockRuntime (testing utility, not differentiation)
- Single sql_postgres training recipe (commodity PEFT)

---

## 7. Product wedge and expansion path

### Wedge: Benchmark harness (works Day 1, no GPU)

```
Clone repo → pytest passes → run-benchmark --compare → screenshot JSON → tweet
```

**Why this wedge:**

- Zero friction (no GPU, no training, no Marketplace)
- Demonstrates core differentiation immediately
- Attracts ML engineers who become contributors
- Creates shareable artifacts (benchmark scores)

### Expansion ladder

```
Phase 0 (now)     Benchmark + mock routing + docs
       ↓
Phase 1 (M1)      VS Code Marketplace + daemonUrl config + demo video
       ↓
Phase 2 (M2)      sql_postgres adapter on HuggingFace + inline completions
       ↓
Phase 3 (M3)      3 adapter recipes + Continue.dev integration guide
       ↓
Phase 4 (M4)      LoRA-JIT-Trace benchmark dataset + arXiv paper
       ↓
Phase 5 (M6)      Enterprise daemon (auth, multi-user) + support contracts
       ↓
Phase 6 (M12)     Adapter marketplace + certified routing scores
```

### The "aha moment" funnel

| Step | Time | User feeling |
|------|------|--------------|
| `pytest` → 48 passed | 2 min | "This is real engineering" |
| cold_miss → warm_hit curl demo | 5 min | "JIT paging actually works" |
| `--compare` benchmark | 7 min | "I can measure routing" |
| F5 extension → status bar | 15 min | "I can *see* routing live" |
| Train sql_postgres + real completion | 2 hr | "This generates real SQL locally" |

Optimize onboarding to reach step 3 in **under 10 minutes**.

---

## 8. Launch narrative

### Primary launch story (Hacker News / Show HN)

**Title:** *Show HN: LoRA-JIT – benchmark your LoRA adapter routing before you ship code completions*

**Body structure:**

1. Problem: one local model can't do SQL and React equally well
2. Insight: routing matters as much as model quality — but nobody measures it
3. Demo: cold_miss (6700ms) → warm_hit (6ms) GIF
4. Benchmark: 99% SQL routing accuracy on learned router
5. Honest limit: completions logged, not inline yet — this is routing infrastructure
6. Ask: star repo, try benchmark, contribute traces

**Why this works on HN:** technical, measurable, honest about limitations, open source, novel category.

### Secondary narratives (channel-specific)

| Channel | Angle |
|---------|-------|
| **r/LocalLLaMA** | "I built automatic LoRA switching for VS Code — 6ms warm latency on RTX 3050" |
| **HuggingFace** | Model card for sql_postgres adapter + link to routing benchmark |
| **Dev Twitter/X** | 30s screen recording: status bar changing adapters as you switch files |
| **YouTube** | 8-min architecture walkthrough + live benchmark |
| **Conference (NeurIPS workshop / PyCon)** | "Benchmarking Context-Aware Adapter Routing" poster + live demo |
| **Enterprise blog** | "Why we can't use Copilot and what we built instead" (guest post) |

### Launch week calendar

| Day | Action |
|-----|--------|
| D-7 | Teaser thread: "Why I'm open-sourcing adapter routing benchmarks" |
| D-3 | Publish AUDIT.md + QUICKSTART.md, tag v0.6.0 release |
| D-1 | Record 60s demo GIF, prep HN post |
| D0 | Show HN + r/LocalLLaMA + HF model card |
| D+1 | Respond to every comment within 2 hours |
| D+2 | Publish architecture blog post |
| D+3 | Outreach to 10 ML newsletters (TLDR AI, The Batch, etc.) |
| D+7 | "Week 1 metrics" transparent post (stars, clones, issues) |

---

## 9. Channel strategy

### Channel priority matrix

| Channel | Cost | Reach | Conversion | Priority |
|---------|------|-------|------------|----------|
| GitHub (OSS) | Free | High (ML devs) | Medium | **P0** |
| Hacker News | Free | Very high (launch spike) | High | **P0** |
| r/LocalLLaMA | Free | High (exact ICP) | Very high | **P0** |
| HuggingFace Hub | Free | Medium | High | **P1** |
| VS Code Marketplace | Free | High | Medium (after inline UX) | **P1** |
| PyPI | Free | Medium | Medium | **P2** |
| YouTube | Time | Medium | Medium | **P1** |
| Paid ads | $$$ | Broad | Low | **P4 (skip Year 1)** |
| Enterprise outbound | Time | Narrow | Very high ACV | **P2 (Month 6+)** |

### GitHub growth tactics

- Pin repo with benchmark GIF in README
- Enable GitHub Discussions (Q&A + showcase)
- `good first issue` labels on docs and sample traces
- Submit to awesome lists: `awesome-local-llm`, `awesome-vscode`, `awesome-peft`
- GitHub Sponsors with tier: "Priority issue response"

### VS Code Marketplace (Phase 1 gate)

Requirements before listing:

- Icon + banner
- `vscode:prepublish` script
- `loraJit.daemonUrl` setting
- README with install steps
- Keywords: `lora`, `local ai`, `peft`, `routing`, `ml`

---

## 10. Content and community flywheel

```
Contributors add traces → benchmark corpus grows →
router accuracy improves → published scores →
social proof → new users → new contributors
```

### Content pillars (repeat monthly)

1. **Benchmark reports** — "Routing accuracy on 500 real editor sessions"
2. **Adapter recipes** — "How we trained react_hooks in 2 hours on RTX 4090"
3. **Architecture deep dives** — paging, learned router, PEFT hot-swap
4. **Comparison posts** — "LoRA-JIT vs manual Ollama model switching"
5. **User showcases** — "Team X routed 4 adapters with 94% accuracy"

### Community infrastructure

| Asset | Purpose |
|-------|---------|
| GitHub Discussions | Support + ideas + showcases |
| Discord (optional Month 3) | Real-time help for GPU path |
| Monthly community call | Demo new adapters, review benchmarks |
| `CONTRIBUTORS.md` | Recognize trace and adapter contributors |

### The benchmark dataset as media asset

Publish **LoRA-JIT-Trace-1K** on HuggingFace Datasets:

- 1000 annotated editor routing examples
- Ontology-constrained labels
- Train/val/test splits
- Leaderboard: submit your router, compare top1_accuracy

This is the **ImageNet moment** for adapter routing — whoever publishes the standard dataset owns the category narrative.

---

## 11. Partnership map

| Partner | Integration | Value exchange |
|---------|-------------|----------------|
| **HuggingFace** | Host adapters + dataset + Spaces demo | Distribution to PEFT audience |
| **Continue.dev** | LoRA-JIT as routing backend option | Their users get multi-adapter routing |
| **Ollama** | Document adapter workflow (even if not native) | Capture their user base |
| **Unsloth / Axolotl** | Export format compatibility | Training pipeline referrals |
| **Weights & Biases** | Benchmark logging integration | ML engineer credibility |
| **VS Code team** | Featured extension (long shot) | Marketplace discovery |

### Integration priority: Continue.dev

Continue already supports local models and multiple providers. A `LoRA-JIT` provider plugin that calls `/jit/route` + `/jit/complete` would:

- Skip building inline completion UX from scratch initially
- Put LoRA-JIT in front of Continue's existing user base
- Validate the HTTP API as the product boundary

---

## 12. Pricing and monetization

### Open core model (recommended)

| Tier | Price | Includes |
|------|-------|----------|
| **Community (MIT)** | Free | Daemon, extension, benchmarks, training scripts, 1 adapter recipe |
| **Pro (future)** | $12/mo individual | Pre-built adapter bundle, priority Discord, cloud benchmark sync |
| **Team** | $49/seat/mo | Shared trace corpus, team router training, SSO daemon |
| **Enterprise** | Custom ACV | Multi-user daemon, audit exports, SLA, on-prem support |

### Year 1 recommendation: **no paid tier**

Focus on stars, contributors, and benchmark adoption. Monetize in Year 2 once Tier 2 product gaps close.

### Enterprise wedge (Month 6+)

Pitch to regulated industries:

> "LoRA-JIT gives you auditable, local code AI with measurable routing — here is the benchmark report your security team can review."

Deliverables: AUDIT.md + on-site deployment guide + custom adapter training workshop.

---

## 13. 90-day execution plan

### Month 1: Foundation launch

| Week | Deliverable | Owner |
|------|-------------|-------|
| W1 | Align version metadata, `.env.example`, docs hub (INDEX, QUICKSTART, FAQ, AUDIT, GTM) | Done |
| W1 | Fix sample-trace ontology, cross-platform README snippets | Done |
| W2 | Record 60s cold→warm GIF, add to README | |
| W2 | Tag `v0.6.0` GitHub Release | |
| W3 | Show HN + r/LocalLLaMA launch | |
| W4 | Enable GitHub Discussions, respond to all issues <24h | |

**M1 success criteria:** 500+ GitHub stars, 50+ forks, 10+ issues/discussions

### Month 2: Developer preview

| Week | Deliverable |
|------|-------------|
| W5 | `loraJit.daemonUrl` + extension marketplace prep |
| W6 | Publish `sql_postgres` adapter to HuggingFace |
| W7 | Minimal inline completion provider (ghost text MVP) |
| W8 | VS Code Marketplace publish |

**M2 success criteria:** 200 Marketplace installs, 3 external contributor PRs

### Month 3: Ecosystem seed

| Week | Deliverable |
|------|-------------|
| W9 | `react_hooks` or `fastapi_service` second training recipe |
| W10 | Continue.dev integration guide + sample config |
| W11 | Draft LoRA-JIT-Trace-100 (100 annotated sessions) |
| W12 | Architecture blog + newsletter outreach |

**M3 success criteria:** 2000 stars, benchmark dataset published, 1 external integration blog post

---

## 14. Metrics and north stars

### North star metric

**Weekly active benchmark runs** (proxy for real evaluation/adoption)

### Supporting metrics

| Metric | Target (90 days) | Tool |
|--------|------------------|------|
| GitHub stars | 2 000 | GitHub |
| Forks | 150 | GitHub |
| Unique daemon clones (npm/pip post-publish) | 500 | telemetry opt-in |
| Annotated traces contributed | 100 | HF dataset |
| Marketplace installs | 500 | VS Code |
| External blog mentions | 5 | Google Alerts |
| Enterprise inbound inquiries | 3 | GitHub Issues |

### Anti-metrics (do not optimize)

- Raw star count without engagement
- Twitter impressions without GitHub conversion
- Feature count before inline completion works

---

## 15. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| "Just use Copilot" dismissal | High | Medium | Lead with benchmark + privacy angle, not completion UX |
| Copilot adds multi-adapter routing | Low (24 mo) | High | Own open benchmark standard first; be the routing layer they integrate |
| GPU setup friction kills adoption | High | High | MockRuntime wedge; HF pre-built adapter; one-click docker |
| Extension UX disappointment | High | High | Honest README; inline completions in M2; Continue.dev bridge |
| Low contributor engagement | Medium | Medium | good-first-issue traces; benchmark leaderboard |
| Patent/IP concerns from big tech | Low | Medium | MIT license, public prior art via dated releases |
| Paging simulator seen as "fake" | Medium | Medium | Document clearly; add real VRAM telemetry in M3 |

---

## 16. The one big bet

**Bet:** The next wave of code AI is not one bigger model — it is **many small specialists orchestrated intelligently**, and the team that owns the **routing benchmark standard** owns the category.

LoRA-JIT should not try to out-Copilot Copilot in Year 1.

It should become the **SQLite of adapter routing**: small, embeddable, benchmark-proven, everywhere — until "did you benchmark your routing?" becomes a standard question in every local-AI code assistant evaluation.

### The famous-repo path

Famous open-source repos share traits LoRA-JIT already has or can add quickly:

| Trait | LoRA-JIT status | Action |
|-------|-----------------|--------|
| Solves a real pain | ✅ Multi-adapter local routing | Sharpen messaging |
| Works in 10 minutes | ✅ MockRuntime path | QUICKSTART.md |
| Unique visual demo | ⚠️ Status bar only | GIF + demo video |
| Benchmark numbers | ✅ 99% / 6ms | Lead all launch content |
| Honest docs | ✅ AUDIT.md gaps | Keep updating |
| Community on-ramp | ⚠️ No Discussions yet | Enable + good first issues |
| Media moment | ❌ Not yet launched | Show HN Week 3 |
| Standard dataset | ❌ Not yet | LoRA-JIT-Trace-1K Month 3 |

**The launch sentence:**

> *"Before you ship local code AI, benchmark your LoRA routing. LoRA-JIT is the open harness that proves it works."*

Ship that sentence everywhere. Build everything else around it.

---

## Appendix: swipe file

### Tweet (280 chars)

> I open-sourced LoRA-JIT: automatic LoRA adapter routing for VS Code.
>
> Cold load: 6.7s → warm route: 6ms
> SQL routing accuracy: 99%
> 48 tests, MIT license
>
> Benchmark your routing before you ship completions.
>
> github.com/Anandb71/LoRA-jit

### Email subject lines

- "We measured LoRA routing accuracy — here's what we found"
- "Your local LLM needs a router, not a bigger model"
- "Open source: benchmark adapter routing in 10 minutes"

### Press boilerplate

LoRA-JIT is an open-source, MIT-licensed system for context-aware LoRA adapter routing in VS Code. It automatically selects and hot-swaps domain-specific fine-tuned models based on live editor telemetry, with published benchmarks for routing accuracy and latency. Built for ML engineers and privacy-conscious teams who need measurable local code AI.

---

*Related: [OVERVIEW.md](./OVERVIEW.md) · [AUDIT.md](./AUDIT.md) · [QUICKSTART.md](./QUICKSTART.md)*
