# Post-push GitHub configuration for @Anandb71
# Run AFTER: gh auth login
# Usage: .\scripts\configure-github-repo.ps1

$ErrorActionPreference = "Stop"
$Repo = "Anandb71/LoRA-jit"

function Require-Gh {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $gh) {
        Write-Host "Install GitHub CLI: winget install GitHub.cli" -ForegroundColor Red
        Write-Host "Then run: gh auth login" -ForegroundColor Yellow
        exit 1
    }
}

Require-Gh

Write-Host "Configuring $Repo ..." -ForegroundColor Cyan

gh repo edit $Repo `
    --description "Context-aware LoRA adapter routing for VS Code — benchmark your routing before you ship completions. MIT." `
    --homepage "https://github.com/Anandb71/LoRA-jit/tree/main/docs" `
    --enable-discussions `
    --add-topic lora `
    --add-topic peft `
    --add-topic vscode `
    --add-topic local-llm `
    --add-topic machine-learning `
    --add-topic code-generation `
    --add-topic fastapi `
    --add-topic open-source

Write-Host "Creating v0.6.0 release ..." -ForegroundColor Cyan
gh release create v0.6.0 `
    --repo $Repo `
    --title "v0.6.0 — Public launch: docs, GTM, community" `
    --notes-file RELEASE_v0.6.0.md `
    --latest

Write-Host "Creating welcome discussion ..." -ForegroundColor Cyan
gh api repos/$Repo/discussions -f title="Welcome to LoRA-JIT — start here" -f body="@Anandb71/open-sourced LoRA-JIT: **measure your LoRA adapter routing before you ship completions.**

**Try in 10 minutes (no GPU):**
\`\`\`bash
pytest tests/ -v
python scripts/run-benchmark.py examples/sample-trace.json --compare
\`\`\`

**Docs:** https://github.com/Anandb71/LoRA-jit/tree/main/docs
**Launch posts:** https://github.com/Anandb71/LoRA-jit/blob/main/docs/SOCIAL.md

What adapter domains do you want next — SQL, React, FastAPI, AWS?" -f category=4 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  (Create welcome discussion manually from Discussions tab)" -ForegroundColor DarkYellow
}

Write-Host "`nDone. Next steps:" -ForegroundColor Green
Write-Host "  1. Pin repo on profile: github.com/Anandb71?tab=repositories"
Write-Host "  2. Enable Pages: Settings -> Pages -> GitHub Actions"
Write-Host "  3. Post HN/Reddit/X from docs/SOCIAL.md"
Write-Host "  4. Profile README: docs/GITHUB_PROFILE_README.md"
