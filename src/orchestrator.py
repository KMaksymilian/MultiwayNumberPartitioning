import statistics

from algorithm_kk import algorithm_kk
from algorithm_gnp import algorithm_gnp
from algorithm_lp import algorithm_lp


def _is_valid_partition(
    dataset: list[int],
    partitions: list[list[int]],
    k: int,
) -> bool:
    """Check whether all numbers are assigned correctly."""
    return (
        len(partitions) == k
        and sorted(num for part in partitions for num in part)
        == sorted(dataset)
    )


def orchestrator_partitioning(
    dataset: list[int],
    k: int,
    cv_threshold: float = 0.6,
) -> list[list[int]]:
    """Select partitioning algorithms based on data variability."""
    if k < 1:
        raise ValueError("k must be greater than zero.")

    if cv_threshold < 0:
        raise ValueError("cv_threshold cannot be negative.")

    if not dataset:
        return [[] for _ in range(k)]

    if len(dataset) < 2:
        return [list(dataset)] + [[] for _ in range(k - 1)]

    if any(num < 0 for num in dataset):
        raise ValueError("CV algorithm requires non-negative data.")

    mean_val = statistics.mean(dataset)
    std_dev = statistics.stdev(dataset)

    cv = std_dev / mean_val if mean_val > 0 else 0.0

    if cv <= cv_threshold:
        return algorithm_kk(dataset, k)

    # Separate large and small numbers.
    threshold_large = mean_val + std_dev

    basket2_large = [
        num for num in dataset if num >= threshold_large
    ]
    basket1_small = [
        num for num in dataset if num < threshold_large
    ]

    if len(basket2_large) < 2:
        return algorithm_kk(dataset, k)

    mean_b2 = statistics.mean(basket2_large)
    std_dev_b2 = statistics.stdev(basket2_large)
    cv_b2 = std_dev_b2 / mean_b2 if mean_b2 > 0 else 0.0

    # Select an algorithm for large numbers.
    if cv_b2 <= cv_threshold:
        partitions = algorithm_kk(basket2_large, k)
    else:
        try:
            partitions = algorithm_lp(basket2_large, k)

            if not _is_valid_partition(
                basket2_large, partitions, k
            ):
                raise RuntimeError("Invalid LP result.")

        except Exception:
            partitions = algorithm_kk(basket2_large, k)

    # Distribute remaining numbers.
    leftovers = algorithm_gnp(
        basket1_small,
        [sum(part) for part in partitions],
    )

    for i in range(k):
        partitions[i].extend(leftovers[i])

    if not _is_valid_partition(dataset, partitions, k):
        raise RuntimeError("Invalid final partition.")

    return partitions