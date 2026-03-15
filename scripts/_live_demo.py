import json
import time
import urllib.request

BASE = "http://127.0.0.1:8765"


def post(path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


print("=" * 60)
print("  LoRA-JIT  --  LIVE END-TO-END DEMO")
print("=" * 60)

PREFIX = "SELECT id, team_name, created_at FROM teams WHERE team_id ="

# TelemetryStreamEvent is what /jit/route expects
route_event = {
    "session_id": "demo-live-001",
    "event_type": "cursor",
    "file_path": "src/db/queries.sql",
    "language_id": "sql",
    "sequence_id": 1,
    "full_text": PREFIX,
    "cursor_line": 0,
    "cursor_column": len(PREFIX),
    "symbol_path": ["queries"],
}

# CompletionRequest is what /jit/complete expects
complete_req = {
    "session_id": "demo-live-001",
    "file_path": "src/db/queries.sql",
    "prefix": PREFIX,
    "suffix": "",
    "max_tokens": 40,
}

print()
print("SCENARIO")
print("  User opens : src/db/queries.sql  (SQL file)")
print("  Typed so far:", repr(PREFIX))
print()

# ── STEP 1: route ─────────────────────────────────────────────
print("STEP 1  POST /jit/route  (which adapter should handle this?)")
t0 = time.perf_counter()
route = post("/jit/route", route_event)
ms = (time.perf_counter() - t0) * 1000
print(f"  adapter selected : {route['adapter_id']}")
print(f"  confidence       : {route['confidence']:.3f}")
print(f"  paging status    : {route['paging_status']}")
print(f"  activation ms    : {route['activation_latency_ms']:.1f} ms")
print(f"  round-trip ms    : {ms:.1f} ms")
print()

# ── STEP 2: complete ──────────────────────────────────────────
print("STEP 2  POST /jit/complete  (generate the next tokens)")
print("  Calling model.generate() on GPU — may take several seconds...")
t1 = time.perf_counter()
comp = post("/jit/complete", complete_req)
print(f"  adapter used    : {comp['active_adapter_used']}")
print(f"  generation ms   : {comp['generation_latency_ms']:.0f} ms")
print()
print("  COMPLETION TEXT:")
print("  " + "-" * 50)
for line in comp["completion_text"].split("\n")[:8]:
    print("  |  " + line)
print("  " + "-" * 50)
print()

# ── STEP 3: second route (warm hit) ───────────────────────────
print("STEP 3  POST /jit/route again (same session -> should be warm)")
route_event2 = dict(route_event)
route_event2["sequence_id"] = 2
route_event2["full_text"] = "SELECT count(*) FROM orders WHERE status ="
route_event2["cursor_column"] = len(route_event2["full_text"])
t2 = time.perf_counter()
route2 = post("/jit/route", route_event2)
ms2 = (time.perf_counter() - t2) * 1000
print(f"  adapter selected : {route2['adapter_id']}")
print(f"  paging status    : {route2['paging_status']}")
print(f"  activation ms    : {route2['activation_latency_ms']:.1f} ms")
print(f"  round-trip ms    : {ms2:.1f} ms")
print()
print("=" * 60)
print("  DEMO COMPLETE")
print("=" * 60)
