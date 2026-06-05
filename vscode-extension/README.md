# LoRA-JIT VS Code Extension

Telemetry client and JIT observability UI for the [LoRA-JIT daemon](https://github.com/Anandb71/LoRA-jit).

The extension streams editor events to the local daemon, triggers routing on cursor and typing activity, and surfaces adapter decisions in the status bar and output channel.

---

## What it does today

- Streams cursor, text-change, and symbol events to `http://127.0.0.1:8765`
- Calls `POST /jit/route` on cursor movement (debounced)
- Calls `POST /jit/complete` after typing stops (280 ms debounce)
- Status bar: `JIT: <adapter_id> (warm|cold)`
- Output channel: structured log lines (`[ROUTER]`, `[PAGING]`, `[INFER]`, `[TIMING]`)

## What it does not do (yet)

- **Inline ghost-text completions** — completions are logged, not inserted in the editor
- **Marketplace one-click install** — run via Extension Development Host (`F5`) during development

See [docs/AUDIT.md](../docs/AUDIT.md) for the full maturity matrix.

---

## Development setup

### Prerequisites

- LoRA-JIT daemon running (`python scripts/run-daemon.py` from repo root)
- Node.js 18+

### Install and run

```bash
cd vscode-extension
npm install
```

Press **F5** in VS Code to launch an Extension Development Host.

Open any code file, move the cursor, and watch the status bar update.

---

## Commands

| Command | Description |
|---------|-------------|
| **LoRA-JIT: Ping Daemon** | Health check against the daemon |
| **LoRA-JIT: Send Sample Telemetry** | Send a test event batch |
| **LoRA-JIT: Show JIT Log** | Open the output channel |

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `loraJit.telemetry.enabled` | `true` | Stream events to daemon |
| `loraJit.telemetry.tickMs` | `75` | Debounce interval for batch flush (ms) |
| `loraJit.telemetry.maxBatchSize` | `200` | Max queued events before immediate flush |
| `loraJit.telemetry.hardBufferLimit` | `1000` | Memory queue cap; drops events when reached |
| `loraJit.telemetry.heartbeatEveryNChanges` | `40` | Full-text heartbeat interval for desync recovery |

---

## Output channel format

```
[14:02:05] [ROUTER] Intent: sql_postgres (99%) — seq #1
[14:02:05] [PAGING] sql_postgres: warm_hit | hot-set: [sql_postgres]
[14:02:05] [INFER]  Active: sql_postgres | Backend: pytorch-peft
[14:02:05] [TIMING] Route: 5.9 ms | Generation: 7561 ms
```

---

## Architecture

```
extension.ts
  ├── TelemetryQueue → POST /telemetry/stream
  ├── onDidChangeTextEditorSelection → POST /jit/route
  └── onDidChangeTextDocument → POST /jit/complete (debounced)
```

The daemon URL is currently hardcoded to `http://127.0.0.1:8765`. A configurable `loraJit.daemonUrl` setting is planned — track progress in [docs/AUDIT.md](../docs/AUDIT.md).

---

## Related documentation

- [docs/QUICKSTART.md](../docs/QUICKSTART.md) — full setup guide
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — system design
- [CONTRIBUTING.md](../CONTRIBUTING.md) — PR checklist
