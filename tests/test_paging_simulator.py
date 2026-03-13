from backend.paging.simulator import PagingSimulator


def test_paging_counts_hits_misses_and_evictions() -> None:
    sim = PagingSimulator(max_hot_adapters=2)
    sim.touch("a")  # miss
    sim.touch("b")  # miss
    sim.touch("a")  # hit
    sim.touch("c")  # miss + eviction

    assert sim.stats.warm_hits == 1
    assert sim.stats.cold_misses == 3
    assert sim.stats.evictions == 1
