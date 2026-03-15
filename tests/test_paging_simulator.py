from backend.paging.simulator import PagingSimulator


def test_paging_counts_hits_misses_and_evictions() -> None:
    sim = PagingSimulator(max_hot_adapters=2)
    r1 = sim.touch("a")  # miss
    r2 = sim.touch("b")  # miss
    r3 = sim.touch("a")  # hit
    r4 = sim.touch("c")  # miss + eviction

    assert sim.stats.warm_hits == 1
    assert sim.stats.cold_misses == 3
    assert sim.stats.evictions == 1
    assert r1.paging_status == "cold_miss"
    assert r2.paging_status == "cold_miss"
    assert r3.paging_status == "warm_hit"
    assert r4.evicted_adapters == ["b"]


def test_paging_respects_mb_budget_and_evicts_lru() -> None:
    sim = PagingSimulator(
        max_hot_adapters=10,
        max_hot_mb=150.0,
        adapter_sizes_mb={"a": 80.0, "b": 80.0, "c": 60.0},
    )

    sim.touch("a")
    r2 = sim.touch("b")
    r3 = sim.touch("c")

    assert "a" in r2.evicted_adapters
    assert r3.total_hot_mb <= 150.0
