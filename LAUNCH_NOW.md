# 🚀 LAUNCH NOW — @Anandb71

Everything is **pushed to GitHub** (`main` + tag `v0.6.0`).

Do these **in order** — total time ~45 minutes.

---

## ✅ Already done (by automation)

- [x] Public docs hub, GTM, audit, FAQ, quickstart
- [x] Social copy for HN, Reddit, X, LinkedIn → [docs/SOCIAL.md](./docs/SOCIAL.md)
- [x] GitHub community files (Discussions template, showcase issues, Pages workflow)
- [x] Pushed to https://github.com/Anandb71/LoRA-jit
- [x] Tagged `v0.6.0`

---

## Step 1 — GitHub repo settings (5 min)

Open each link and apply:

| Action | Link |
|--------|------|
| **Enable Discussions** | [Settings → General → Features → Discussions](https://github.com/Anandb71/LoRA-jit/settings) |
| **Enable GitHub Pages** | [Settings → Pages → Source: GitHub Actions](https://github.com/Anandb71/LoRA-jit/settings/pages) |
| **Add topics** | Settings → General → Topics: `lora`, `peft`, `vscode`, `local-llm`, `machine-learning`, `code-generation`, `fastapi` |
| **Edit description** | `Context-aware LoRA adapter routing for VS Code — benchmark your routing before you ship completions` |
| **Pin repository** | [Your profile → Customize pins](https://github.com/Anandb71?tab=repositories) |

### Or run after `gh auth login`:

```powershell
.\scripts\configure-github-repo.ps1
```

---

## Step 2 — Create GitHub Release (2 min)

Tag exists; attach release notes:

1. Open https://github.com/Anandb71/LoRA-jit/releases/new?tag=v0.6.0
2. Title: `v0.6.0 — Public launch: docs, GTM, community`
3. Paste body from [RELEASE_v0.6.0.md](./RELEASE_v0.6.0.md)
4. Check **Set as latest release** → Publish

---

## Step 3 — Profile README (5 min)

Follow [docs/GITHUB_PROFILE_README.md](./docs/GITHUB_PROFILE_README.md) to create `anandb71/anandb71` repo and pin LoRA-JIT on your profile.

---

## Step 4 — Post everywhere (30 min)

Copy from [docs/SOCIAL.md](./docs/SOCIAL.md):

| Platform | Submit URL |
|----------|------------|
| **Hacker News** | https://news.ycombinator.com/submit |
| **r/LocalLLaMA** | https://www.reddit.com/r/LocalLLaMA/submit |
| **X / Twitter** | Post 4-tweet thread from SOCIAL.md |
| **LinkedIn** | Paste LinkedIn section |

**Attach:** `docs/assets/demo-teaser.svg` or record screen with `scripts/launch-smoke.ps1`

---

## Step 5 — Welcome Discussion (2 min)

After enabling Discussions:

1. https://github.com/Anandb71/LoRA-jit/discussions/new?category=general
2. Title: `Welcome to LoRA-JIT — start here`
3. Pin the discussion

---

## Optional — HuggingFace (when weights ready)

Upload `adapters/sql_postgres/` using model card from [docs/huggingface/MODEL_CARD.md](./docs/huggingface/MODEL_CARD.md)

---

## Verify smoke test

```powershell
.\scripts\launch-smoke.ps1
```

---

**Give me your `gh auth login` or HuggingFace token and I can automate Steps 1–2 + welcome discussion on the next run.**
