# Frequently Asked Questions

---

## General

### Is LoRA-JIT a Copilot replacement?

No. LoRA-JIT is **adapter routing infrastructure** with observability. Completions exist at the HTTP API level and are logged in the VS Code output channel — they are not inserted as inline ghost text yet.

Use LoRA-JIT when you need to **measure and prove** that your LoRA routing works before building a full coding assistant UX.

### Does it work without a GPU?

Yes. The default `MockRuntime` runs the full routing and paging loop with deterministic stub completions. All 48 tests pass without GPU.

### Is my code sent to the cloud?

No. The daemon binds to `127.0.0.1:8765` only. Telemetry stays on your machine unless you explicitly configure an external LLM API for **offline benchmark annotation** (`LORA_JIT_LLM_API_BASE`).

---

## Installation

### `pip install -e .[dev]` fails on Windows

Ensure Python 3.11+ is installed:

```powershell
py -3.11 --version
```

If `py` is unavailable, use the full path to your Python executable.

### `pip install -e .[runtime]` fails or is very slow

PyTorch wheels are large. Install CPU-only torch first if you have no NVIDIA GPU:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e .[runtime]
```

For CUDA, follow [PyTorch install instructions](https://pytorch.org/get-started/locally/) for your CUDA version, then install `.[runtime]`.

---

## Daemon

### Daemon won't start — port 8765 in use

Another process is bound to port 8765. Find and stop it, or set a different port in your launch script (not yet configurable via env — see [AUDIT.md](./AUDIT.md)).

### `/health` returns OK but routing seems wrong

Check which predictor is active:

```bash
# Default is structural (heuristic keyword matching)
echo $LORA_JIT_PREDICTOR   # or inspect .env
```

For SQL files, switch to the learned router:

```dotenv
LORA_JIT_PREDICTOR=learned
LORA_JIT_ROUTER_MODEL_PATH=examples/router-model.seed.json
```

### First route is slow (~6+ seconds) even with GPU

Cold adapter load. Enable preload:

```dotenv
LORA_JIT_PRELOAD_ADAPTERS=sql_postgres
LORA_JIT_EAGER_LOAD=true
```

Restart the daemon. First route should drop to single-digit milliseconds.

---

## Adapters and training

### Which adapters ship pre-trained?

None in the repository. Adapter weights are gitignored. Only `sql_postgres` has a complete training recipe (`scripts/build-sql-dataset.py` + `scripts/train-peft-adapter.py`).

Other IDs in [ADAPTER_ONTOLOGY.md](./ADAPTER_ONTOLOGY.md) are registry entries for routing and labeling.

### `verify-adapter.py` fails

Common causes:

- Missing `adapter_config.json` or weight files in `adapters/<adapter_id>/`
- Training did not complete — re-run `train-peft-adapter.py`
- Wrong `--adapter-id` passed to training script

### Generation returns stub text on GPU path

Check:

1. `LORA_JIT_RUNTIME_BACKEND=pytorch` in `.env`
2. Daemon was restarted after changing `.env`
3. Adapter was activated via `/jit/route` before `/jit/complete`
4. If `LORA_JIT_STRICT_RUNTIME=false`, failures silently fall back to stub — check daemon logs

---

## VS Code extension

### Status bar shows nothing

1. Confirm daemon is running: **LoRA-JIT: Ping Daemon** command
2. Check `loraJit.telemetry.enabled` is `true` in VS Code settings
3. Open the **LoRA-JIT** output channel for connection errors

### Completions don't appear in the editor

Expected behavior today. Completions are logged to the output channel only. Inline completion is on the roadmap — see [AUDIT.md](./AUDIT.md).

### Extension only works in Extension Development Host

Correct. The extension is not yet published to the VS Code Marketplace. Press **F5** from `vscode-extension/` to launch a dev host.

---

## Benchmarks

### `sample-trace.json` shows 0% accuracy

The sample trace is a **smoke test** with two events. Accuracy depends on whether heuristic predictors match `fastapi_service` labels. Use your own annotated traces for meaningful scores — see [BENCHMARK.md](./BENCHMARK.md).

### Unknown adapter ID error during annotation

All labels must use IDs from [ADAPTER_ONTOLOGY.md](./ADAPTER_ONTOLOGY.md). The auto-labeler rejects unknown IDs.

### Learned router performs worse than structural

The seed model at `examples/router-model.seed.json` was trained on a small corpus. Re-train on your own annotated benchmark:

```bash
python scripts/train-router.py benchmark.annotated.json --output models/router.json
```

---

## Security

### Is authentication required?

No. The daemon is designed for single-user local development. Do not expose port 8765 to the network. See [SECURITY.md](../SECURITY.md).

---

## Still stuck?

1. Check [AUDIT.md](./AUDIT.md) for known limitations
2. Open a [GitHub issue](https://github.com/Anandb71/LoRA-jit/issues) with daemon logs and your `.env` (redact API keys)
3. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for component boundaries
