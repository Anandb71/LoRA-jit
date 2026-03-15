# Security Policy

## Supported versions

Security fixes are applied to the `main` branch. There are no separate maintained release branches
at this stage of the project.

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report privately by emailing the maintainer or opening a GitHub private security advisory at:
`https://github.com/Anandb71/LoRA-jit/security/advisories/new`

Your report should include:

- A clear description of the vulnerability
- Steps to reproduce
- Affected component (daemon endpoint, extension, labeling pipeline, …)
- Potential impact
- Suggested remediation if known

You will receive an acknowledgement within **7 days** and a resolution timeline within **14 days**
of triage.

## Threat model

LoRA-JIT is designed to run **locally** on a developer machine.
The daemon binds only to `127.0.0.1` by default.

Known limitations to be aware of:

- The daemon does **not** implement authentication or authorisation. Do not expose port 8765
  to untrusted networks.
- Adapter paths and model IDs are read from `.env` and resolved on the local filesystem.
  Untrusted `.env` files should not be used.
- `LlmLabelProvider` sends code context to an external API endpoint. Review `LORA_JIT_LLM_API_BASE`
  before enabling in shared or sensitive environments.
