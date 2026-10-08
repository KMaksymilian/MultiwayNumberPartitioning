def algorithm_gnp(to_insert, sums):
    buckets = [[] for _ in range(len(sums))]
    to_insert.sort(reverse=True)

    while len(to_insert) != 0:
        curr = to_insert.pop(0)
        min_idx = min(range(len(sums)), key=lambda i: sums[i])
        sums[min_idx] += curr
        buckets[min_idx].append(curr)

    return buckets