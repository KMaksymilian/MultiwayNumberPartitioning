import logging
import math
import statistics

from algorithm_kk import algorithm_kk
from algorithm_gnp import algorithm_gnp
from algorithm_lp import algorithm_lp

logger = logging.getLogger(__name__)

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
    *,
    time_limit: float = 1.0,
    metadata=None,
) -> list[list[int]]:
    """Select partitioning algorithms based on data variability."""
    if k < 1:
        raise ValueError("k must be greater than zero.")

    if not math.isfinite(cv_threshold) or cv_threshold < 0:
        raise ValueError("cv_threshold cannot be negative.")
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and greater than zero.")
    if metadata is None:
        metadata = {}
    metadata.update(strategy="trivial", lp_scope="large_numbers", lp_attempted=False,
                    lp_status="NotRun", lp_optimal=False, fallback_reason="")

    if any(num < 0 for num in dataset):
        raise ValueError("CV algorithm requires non-negative data.")

    if not dataset:
        return [[] for _ in range(k)]

    if len(dataset) < 2:
        return [list(dataset)] + [[] for _ in range(k - 1)]

    mean_val = statistics.mean(dataset)
    std_dev = statistics.stdev(dataset)

    cv = std_dev / mean_val if mean_val > 0 else 0.0

    if cv <= cv_threshold:
        metadata["strategy"] = "kk"
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
        metadata["strategy"] = "kk"
        return algorithm_kk(dataset, k)

    mean_b2 = statistics.mean(basket2_large)
    std_dev_b2 = statistics.stdev(basket2_large)
    cv_b2 = std_dev_b2 / mean_b2 if mean_b2 > 0 else 0.0

    # Select an algorithm for large numbers.
    if cv_b2 <= cv_threshold:
        metadata["strategy"] = "kk+gnp"
        partitions = algorithm_kk(basket2_large, k)
    else:
        metadata.update(strategy="lp+gnp", lp_attempted=True)
        try:
            partitions = algorithm_lp(basket2_large, k, time_limit=time_limit, metadata=metadata)

            if not _is_valid_partition(
                basket2_large, partitions, k
            ):
                raise RuntimeError("Invalid LP result.")

        except Exception as error:
            if metadata["lp_status"] == "NotRun":
                metadata["lp_status"] = "Error"
            metadata.update(strategy="kk+gnp_fallback", fallback_reason=str(error))
            logger.warning("LP failed; falling back to KK: %s", error)
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
