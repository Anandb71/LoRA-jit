---
license: mit
language:
- en
tags:
- lora
- peft
- code-generation
- routing
- vscode
- local-llm
- sql
library_name: peft
base_model: Qwen/Qwen1.5-0.5B
---

# sql_postgres — LoRA-JIT domain adapter

**Author:** [@Anandb71](https://github.com/Anandb71)  
**Project:** [LoRA-JIT](https://github.com/Anandb71/LoRA-jit)  
**Adapter ID:** `sql_postgres` (see [Adapter Ontology](https://github.com/Anandb71/LoRA-jit/blob/main/docs/ADAPTER_ONTOLOGY.md))

PostgreSQL-focused LoRA adapter for the LoRA-JIT routing system. Trained for parameterised SQL, schema-aware queries, and Postgres idioms on top of `Qwen/Qwen1.5-0.5B`.

---

## How to use with LoRA-JIT

1. Clone [LoRA-JIT](https://github.com/Anandb71/LoRA-jit)
2. Place adapter weights in `adapters/sql_postgres/`
3. Configure `.env`:

```dotenv
LORA_JIT_RUNTIME_BACKEND=pytorch
LORA_JIT_PRELOAD_ADAPTERS=sql_postgres
LORA_JIT_PREDICTOR=learned
LORA_JIT_ROUTER_MODEL_PATH=examples/router-model.seed.json
```

4. Start daemon: `python scripts/run-daemon.py`
5. Route + complete via `/jit/route` and `/jit/complete`

Full guide: [docs/QUICKSTART.md](https://github.com/Anandb71/LoRA-jit/blob/main/docs/QUICKSTART.md)

---

## Train your own (reproduce weights)

```bash
python scripts/build-sql-dataset.py --size 800 --output data/sql_postgres/train.jsonl
python scripts/train-peft-adapter.py \
  --adapter-id sql_postgres \
  --dataset data/sql_postgres/train.jsonl \
  --base-model-id Qwen/Qwen1.5-0.5B
python scripts/verify-adapter.py adapters/sql_postgres
```

~10 minutes on RTX 3050 6 GB.

---

## Routing benchmarks (reference hardware)

| Metric | Value |
|--------|-------|
| Warm route latency | 6–20 ms |
| SQL routing confidence | ~99 % |
| 40-token generation | ~7.5 s |

Measured as part of LoRA-JIT's benchmark harness — not a standalone model leaderboard claim.

---

## License

MIT — same as [LoRA-JIT](https://github.com/Anandb71/LoRA-jit/blob/main/LICENSE).

Base model subject to [Qwen license terms](https://huggingface.co/Qwen/Qwen1.5-0.5B).

---

## Citation

```bibtex
@software{lora_jit_2026,
  author = {Anand B},
  title = {LoRA-JIT: Context-Aware LoRA Adapter Routing for VS Code},
  year = {2026},
  url = {https://github.com/Anandb71/LoRA-jit}
}
```
