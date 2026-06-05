# Social Launch Copy

Ready-to-post content for [@Anandb71](https://github.com/Anandb71). Replace nothing except optional personal notes.

**Repo URL:** https://github.com/Anandb71/LoRA-jit

---

## Hacker News (Show HN)

**Title:**

```
Show HN: LoRA-JIT – benchmark your LoRA adapter routing before you ship completions
```

**Body:**

```
I built LoRA-JIT because one local model can't do SQL and React equally well — but manually swapping LoRA adapters is painful and nobody measures whether routing actually works.

LoRA-JIT is an open (MIT) system that:
- Watches VS Code editor context (file path, symbols, cursor)
- Routes to the right domain LoRA adapter automatically
- Pages adapters warm/cold with measurable latency
- Runs fully on localhost (FastAPI daemon + optional PEFT runtime)

Numbers on my RTX 3050 6GB (Qwen1.5-0.5B + sql_postgres LoRA):
- Cold adapter load: ~6.7s
- Warm route after preload: ~6ms
- SQL routing accuracy (learned router): ~99%
- 48/48 tests, no GPU required for the default mock path

Honest limits: this is routing infrastructure, not Copilot. Completions exist via API and are logged in VS Code — inline ghost text is next. Paging tracks simulated hot-set state; activation latency is real.

Try it in 10 minutes:
git clone → pytest → python scripts/run-benchmark.py examples/sample-trace.json --compare

Repo: https://github.com/Anandb71/LoRA-jit
Docs: https://github.com/Anandb71/LoRA-jit/tree/main/docs

I'd love feedback on the benchmark harness and what adapter domains matter most to you.
```

---

## Reddit r/LocalLLaMA

**Title:**

```
[I built] LoRA-JIT — automatic LoRA adapter routing in VS Code with benchmarked accuracy (6ms warm routes, MIT)
```

**Body:**

```
Hey r/LocalLLaMA,

If you've trained multiple LoRA adapters (SQL, FastAPI, React, etc.) you probably run one at a time or swap manually. LoRA-JIT automates that from live editor context.

Stack:
- Python FastAPI daemon on localhost:8765
- Pluggable routers (heuristic + trainable Naive Bayes)
- Paging simulator with warm/cold tracking
- Optional PyTorch/PEFT runtime for real hot-swap
- VS Code extension for telemetry + visible routing decisions

Benchmarks (RTX 3050 6GB, Qwen1.5-0.5B):
- Warm route: 6–20ms with preload
- Cold miss: ~6.7s without preload
- 99% routing confidence on SQL files

No GPU needed to evaluate — mock runtime runs the full loop for CI.

GitHub: https://github.com/Anandb71/LoRA-jit

Not trying to replace Ollama — this is the routing/orchestration layer on top. Would love contributors for trace datasets and adapter recipes.

What domains would you want pre-built adapters for?
```

---

## X / Twitter

**Tweet 1 (hook):**

```
I open-sourced LoRA-JIT: automatic LoRA adapter routing for VS Code.

One base model. Many domain experts. Zero manual switching.

Cold load: 6.7s → warm route: 6ms
SQL routing accuracy: 99%
48 tests · MIT · fully local

Benchmark your routing before you ship completions ↓
https://github.com/Anandb71/LoRA-jit
```

**Tweet 2 (thread):**

```
The problem: one local LLM is mediocre at everything.

The fix isn't always a bigger model — it's the right LoRA specialist at the right time.

But who measures routing accuracy? Copilot doesn't publish numbers. Ollama doesn't route by editor context.

LoRA-JIT does — with a full benchmark harness.
```

**Tweet 3 (thread):**

```
Architecture:
Editor telemetry → intent classification → adapter paging → PEFT hot-swap → completion

Every step is logged:
[ROUTER] adapter + confidence
[PAGING] warm_hit / cold_miss
[TIMING] route + generation ms

Status bar in VS Code shows which adapter is active. Nothing is invisible.
```

**Tweet 4 (thread):**

```
Try it without a GPU:

git clone https://github.com/Anandb71/LoRA-jit
pytest tests/ -v
python scripts/run-benchmark.py examples/sample-trace.json --compare

Honest caveat: inline completions aren't in the editor yet — this is routing infra first.

Stars + issues help me prioritize the roadmap 🙏
```

---

## LinkedIn

```
I just open-sourced LoRA-JIT — a local-first system for context-aware LoRA adapter routing in VS Code.

Most code AI today is one big cloud model. But ML engineers training domain LoRA adapters (SQL, FastAPI, React) face a different problem: how do you automatically pick the right specialist while coding — and prove it works?

LoRA-JIT answers that with:
• Editor-context routing (file path, symbols, cursor)
• JIT adapter paging with measurable warm/cold latency
• A benchmark harness (top1 accuracy, cache miss rate)
• Full localhost operation — no code leaves your machine

On a consumer GPU (RTX 3050 6GB), warm routes hit ~6ms after preload with 99% SQL routing accuracy.

This is routing infrastructure, not a Copilot clone — but I believe measurable orchestration is what local code AI needs next.

MIT licensed. Would love feedback from ML systems and platform engineers.

🔗 https://github.com/Anandb71/LoRA-jit
```

---

## Dev.to / Medium (short post)

**Title:** *Measure Your LoRA Routing Before You Ship Code Completions*

**Body:** Link to `docs/OVERVIEW.md` and `docs/BENCHMARK.md`. Lead with the cold_miss → warm_hit demo. End with clone instructions.

---

## Awesome list PR (awesome-local-llm)

**File change:** Add under "Tools" or "IDE Integration":

```markdown
- [LoRA-JIT](https://github.com/Anandb71/LoRA-jit) - Context-aware LoRA adapter routing and benchmarking for VS Code; local FastAPI daemon with PEFT hot-swap and measurable routing accuracy.
```

**PR title:** `Add LoRA-JIT - local LoRA adapter routing for VS Code`

---

## HuggingFace dataset card (future — LoRA-JIT-Trace)

**Title:** `Anandb71/LoRA-JIT-Trace`

**Description snippet:**

```
Annotated editor telemetry traces for benchmarking context-aware LoRA adapter routing.
Part of the LoRA-JIT open routing infrastructure project.
https://github.com/Anandb71/LoRA-jit
```

---

## Email / DM template (ML newsletters, podcast hosts)

```
Subject: Open-source benchmark harness for LoRA adapter routing in IDEs

Hi [Name],

I built LoRA-JIT (https://github.com/Anandb71/LoRA-jit) — MIT-licensed infrastructure that routes domain-specific LoRA adapters based on live VS Code context, with published routing benchmarks.

Differentiator: nobody else ships measurable adapter routing (top1 accuracy, warm/cold latency) as an open IDE loop. It's local-first and audit-friendly.

Happy to share architecture details or demo data if useful for [newsletter/podcast/audience].

— Anand (@Anandb71)
```

---

## Hashtags (pick 2–3 max on X)

`#LocalLLM` `#LoRA` `#PEFT` `#OpenSource` `#MLEngineering` `#VSCode`
