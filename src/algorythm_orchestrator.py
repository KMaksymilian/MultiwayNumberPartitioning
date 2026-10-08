import statistics


def orchestrator_partitioning(dataset: list[int], k: int, cv_threshold: float = 15.0) -> list[list[int]]:
    if len(dataset) < 2:
        return [dataset] + [[] for _ in range(k - 1)]

    mean_val = statistics.mean(dataset)
    std_dev = statistics.stdev(dataset)

    cv = std_dev / mean_val if mean_val > 0 else 0

    if cv <= cv_threshold:
        return algorithm_kk(dataset, k)
    else:
        basket1_small = []
        basket2_large = []

        threshold_large = mean_val + std_dev

        for num in dataset:
            if num >= threshold_large:
                basket2_large.append(num) 
            else:
                basket1_small.append(num)
                
        if len(basket2_large) < 2:
            partitions = simplex_partitioning(basket2_large, k)
            return algorithm_gnp(basket1_small, partitions)

        std_dev_b2 = statistics.stdev(basket2_large)

        if std_dev_b2 <= sd_threshold:
            partitions = algorithm_kk(basket2_large, k)
        else:
            partitions = simplex_partitioning(basket2_large, k)

        return algorithm_gnp(basket1_small, partitions)