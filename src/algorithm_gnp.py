import heapq


def algorithm_gnp(to_insert: list[int], sums: list[int]) -> list[list[int]]:
    """Distribute numbers among partitions using a greedy min-heap approach."""
    if not sums:
        if to_insert:
            raise ValueError("Liczba partycji musi być większa od zera.")
        return []

    buckets = [[] for _ in sums]

    heap = [(total, i) for i, total in enumerate(sums)]
    heapq.heapify(heap)

    for num in sorted(to_insert, reverse=True):
        current_sum, idx = heapq.heappop(heap)

        buckets[idx].append(num)

        heapq.heappush(heap, (current_sum + num, idx))

    return buckets

