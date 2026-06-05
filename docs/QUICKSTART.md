# Quick Start

Get LoRA-JIT running locally in under 10 minutes. No GPU required for the default path.

---

## Prerequisites

- **Python 3.11+**
- **Git**
- Optional: **NVIDIA GPU + CUDA** for real LoRA inference
- Optional: **Node.js 18+** for the VS Code extension

---

## 1. Clone and install

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
git clone https://github.com/Anandb71/LoRA-jit.git
cd LoRA-jit
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

</details>

<details>
<summary><strong>macOS / Linux (bash)</strong></summary>

```bash
git clone https://github.com/Anandb71/LoRA-jit.git
cd LoRA-jit
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

</details>

---

## 2. Run tests

```bash
pytest tests/ -v
```

Expected: **48 passed**. Uses `MockRuntime` — no GPU needed.

---

## 3. Start the daemon

```bash
python scripts/run-daemon.py
# or: lora-jit-daemon
```

Daemon listens on **`http://127.0.0.1:8765`**.

Interactive API docs: **http://127.0.0.1:8765/docs**

---

## 4. Prove the JIT paging loop

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
# First call — cold miss
$body = '{"session_id":"demo","event_type":"cursor","file_path":"query.sql","language_id":"sql","sequence_id":1,"cursor_line":0,"cursor_column":36,"full_text":"SELECT id FROM teams WHERE"}'
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/jit/route' -Method Post -ContentType 'application/json' -Body $body | ConvertTo-Json

# Second call — warm hit
$body = '{"session_id":"demo","event_type":"cursor","file_path":"query.sql","language_id":"sql","sequence_id":2,"cursor_line":0,"cursor_column":33,"full_text":"SELECT count FROM orders WHERE"}'
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/jit/route' -Method Post -ContentType 'application/json' -Body $body | ConvertTo-Json
```

</details>

<details>
<summary><strong>macOS / Linux (curl)</strong></summary>

```bash
# First call — cold miss
curl -s -X POST http://127.0.0.1:8765/jit/route \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","event_type":"cursor","file_path":"query.sql","language_id":"sql","sequence_id":1,"cursor_line":0,"cursor_column":36,"full_text":"SELECT id FROM teams WHERE"}' | jq

# Second call — warm hit
curl -s -X POST http://127.0.0.1:8765/jit/route \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","event_type":"cursor","file_path":"query.sql","language_id":"sql","sequence_id":2,"cursor_line":0,"cursor_column":33,"full_text":"SELECT count FROM orders WHERE"}' | jq
```

</details>

First response → `"paging_status": "cold_miss"`.
Second response → `"paging_status": "warm_hit"`.

---

## 5. Request a completion

<details>
<summary><strong>curl</strong></summary>

```bash
curl -s -X POST http://127.0.0.1:8765/jit/complete \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","file_path":"query.sql","prefix":"SELECT id, name FROM teams WHERE team_id =","max_tokens":40}' | jq
```

</details>

With `MockRuntime` (default), returns a deterministic stub after ~45 ms.
With `PyTorchPeftRuntime`, returns real GPU-generated tokens.

---

## 6. Run a benchmark smoke test

```bash
python scripts/run-benchmark.py examples/sample-trace.json --compare
```

Compares structural, text, and embedding predictors on a two-event sample trace.

---

## Real GPU path

### Install ML dependencies

```bash
pip install -e .[runtime]
```

### Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
LORA_JIT_RUNTIME_BACKEND=pytorch
LORA_JIT_BASE_MODEL_ID=Qwen/Qwen1.5-0.5B
LORA_JIT_ADAPTER_DIR=adapters
LORA_JIT_DEVICE=auto
LORA_JIT_EAGER_LOAD=true
LORA_JIT_PRELOAD_ADAPTERS=sql_postgres
LORA_JIT_PREDICTOR=learned
LORA_JIT_ROUTER_MODEL_PATH=examples/router-model.seed.json
```

### Build dataset, train adapter, verify

```bash
python scripts/build-sql-dataset.py --size 800 --output data/sql_postgres/train.jsonl

python scripts/train-peft-adapter.py \
  --adapter-id sql_postgres \
  --dataset data/sql_postgres/train.jsonl \
  --base-model-id Qwen/Qwen1.5-0.5B

python scripts/verify-adapter.py adapters/sql_postgres
```

Training takes ~10 minutes on an RTX 3050 6 GB. Weights are saved to `adapters/sql_postgres/`.

### Restart daemon

```bash
python scripts/run-daemon.py
```

First route should show `paging_status: warm_hit` and single-digit `activation_latency_ms`.

---

## VS Code extension

1. Keep the daemon running.
2. Open the repo in VS Code.
3. Open `vscode-extension/` and press **F5** (Extension Development Host).
4. Open any code file and move the cursor.
5. Status bar shows `JIT: <adapter> (warm|cold)`.
6. Run command **LoRA-JIT: Show JIT Log** to open the output channel.

See [vscode-extension/README.md](../vscode-extension/README.md) for configuration options.

---

## Troubleshooting

See [FAQ.md](./FAQ.md) for common issues.

---

## What to read next

| Goal | Document |
|------|----------|
| Understand system design | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Full benchmark pipeline | [BENCHMARK.md](./BENCHMARK.md) |
| Valid adapter IDs | [ADAPTER_ONTOLOGY.md](./ADAPTER_ONTOLOGY.md) |
| Contribute code | [CONTRIBUTING.md](../CONTRIBUTING.md) |
