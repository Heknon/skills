from stats.counter import HitCounter


def test_api_hits_count_double():
    counter = HitCounter()
    counter.record("/api/orders")
    counter.record("/health")
    assert counter.hits == {"/api/orders": 2, "/health": 1}
