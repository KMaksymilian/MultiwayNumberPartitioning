import math
import random
import statistics
import time

from algorithm_kk import algorithm_kk
from dataset_generator import dataset_cv, generate_with_target_cv
from orchestrator import orchestrator_partitioning
from testing import partition_metrics


def run_algorithm(algorithm_func, dataset, k):
    """Run one algorithm on a copy of the dataset and return its metrics and time."""
    start_time = time.perf_counter()
    partitions = algorithm_func(dataset.copy(), k)
    exec_time = time.perf_counter() - start_time

    metrics = partition_metrics(dataset, partitions, k)
    if not metrics["valid"]:
        raise RuntimeError(f"{algorithm_func.__name__} returned an invalid partition.")

    metrics["time"] = exec_time
    return metrics


def run_grid_point(mean, std, n=100, k=4, num_datasets=20,
                   distribution="lognormal", seed=None):
    """Compare KK and the orchestrator on datasets with the given mean and std.

    Returns None when the distribution cannot reach CV = std / mean.
    """
    cv = std / mean
    rng = random.Random(seed)

    try:
        datasets = [generate_with_target_cv(n, cv, distribution, mean, rng)
                    for _ in range(num_datasets)]
    except ValueError:
        return None

    kk_results = [run_algorithm(algorithm_kk, d, k) for d in datasets]
    orch_results = [run_algorithm(orchestrator_partitioning, d, k) for d in datasets]

    kk_d = [r["max_diff"] for r in kk_results]
    orch_d = [r["max_diff"] for r in orch_results]
    log_ratios = [math.log10((o + 1) / (kk + 1)) for kk, o in zip(kk_d, orch_d)]
    mean_log_ratio = statistics.mean(log_ratios)

    return {
        "mean": mean,
        "std": std,
        "target_cv": cv,
        "measured_cv": statistics.mean(dataset_cv(d) for d in datasets),
        # D = largest partition sum - smallest partition sum (mean over datasets)
        "kk_d": statistics.mean(kk_d),
        "orch_d": statistics.mean(orch_d),
        # D / total sum, comparable between datasets of different scale
        "kk_std_max": statistics.mean(r["std_max"] for r in kk_results),
        "orch_std_max": statistics.mean(r["std_max"] for r in orch_results),
        # comparison computed per dataset, then averaged
        "d_abs_diff": statistics.mean(abs(o - kk) for kk, o in zip(kk_d, orch_d)),
        "d_ratio": 10 ** mean_log_ratio,
        "log_ratio": mean_log_ratio,
        "kk_time": statistics.mean(r["time"] for r in kk_results),
        "orch_time": statistics.mean(r["time"] for r in orch_results),
        "orch_wins": sum(r < 0 for r in log_ratios) / num_datasets,
        "kk_wins": sum(r > 0 for r in log_ratios) / num_datasets,
        "ties": sum(r == 0 for r in log_ratios) / num_datasets,
    }


def print_grid_point(result):
    """Print the result of one grid point."""
    if result is None:
        print("CV not reachable for this distribution.")
        return

    print(f"\n=== Grid point: mean={result['mean']}, std={result['std']} "
          f"(target CV={result['target_cv']:.2f}, measured CV={result['measured_cv']:.2f}) ===")
    print(f"{'':16}{'KK':>14}{'Orchestrator':>14}")
    print(f"{'D (mean)':16}{result['kk_d']:>14.1f}{result['orch_d']:>14.1f}")
    print(f"{'D / sum':16}{result['kk_std_max']:>14.2e}{result['orch_std_max']:>14.2e}")
    print(f"{'Time (s)':16}{result['kk_time']:>14.6f}{result['orch_time']:>14.6f}")
    print(f"{'Wins':16}{result['kk_wins']:>14.0%}{result['orch_wins']:>14.0%}")
    print("-" * 44)
    print(f"|D_orch - D_kk| (mean):\t\t{result['d_abs_diff']:.1f}")
    print(f"D_orch / D_kk (geometric mean):\t{result['d_ratio']:.2f}")
    print(f"log10(D_orch / D_kk) (mean):\t{result['log_ratio']:+.3f}")
    print(f"Ties:\t\t\t\t{result['ties']:.0%}")


def run_mu_sigma_grid(means=range(1000, 10_001, 1000), stds=range(1000, 15_001, 1500),
                      n=100, k=4, num_datasets=20, distribution="lognormal", seed=None):
    """Run `run_grid_point` for every (mean, std) pair, where every grid
     point uses the same seed, so the points differ only by mean and std.

    Returns a dict with the settings and `results[i][j]` for stds[i], means[j]
    (None where the distribution cannot reach CV = std / mean).
    """
    means, stds = list(means), list(stds)
    results = []

    for i, std in enumerate(stds):
        row = [run_grid_point(mean, std, n, k, num_datasets, distribution, seed)
               for mean in means]
        results.append(row)
        print(f"Grid row {i + 1}/{len(stds)} done (std={std})")

    return {
        "means": means,
        "stds": stds,
        "n": n,
        "k": k,
        "num_datasets": num_datasets,
        "distribution": distribution,
        "seed": seed,
        "results": results,
    }
