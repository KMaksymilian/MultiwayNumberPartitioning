import time
import statistics
from collections import Counter
from itertools import combinations
from pathlib import Path


def validate_partitions(original_dataset, partitions, k):
    """Check whether all original numbers are preserved."""
    flattened_partitions = [item for sublist in partitions for item in sublist]
    return len(partitions) == k and sorted(original_dataset) == sorted(flattened_partitions)


def process_single_dataset(dataset, algorithm_func, k, index, *, metadata=None):
    """Run an algorithm and calculate partition quality metrics."""
    if k < 1:
        raise ValueError("k must be greater than zero.")
    start_time = time.perf_counter()
    if metadata is None:
        partitions = algorithm_func(dataset.copy(), k)
    else:
        partitions = algorithm_func(dataset.copy(), k, metadata=metadata)
    exec_time = time.perf_counter() - start_time

    if not validate_partitions(dataset, partitions, k):
        raise ValueError(f"Invalid partition for dataset {index}: expected {k} groups preserving all numbers.")

    sums = [sum(p) for p in partitions]
    total_sum = sum(sums)
    ideal_sum = total_sum / k

    max_diff = max(sums) - min(sums)
    pairwise_diffs = [abs(a - b) for a, b in combinations(sums, 2)]
    avg_diff = statistics.mean(pairwise_diffs) if pairwise_diffs else 0
    std_of_sums = statistics.stdev(sums) if len(sums) > 1 else 0.0

    if total_sum == 0:
        return exec_time, 0, 0, 0

    std_max = max_diff / total_sum
    std_avg = avg_diff / total_sum
    std_cv = std_of_sums / ideal_sum if ideal_sum != 0 else 0

    print(f"Dataset {index}: Time: {exec_time:.6f}s | Max Diff: {max_diff} | Avg Diff: {avg_diff:.4f} | CV: {std_cv:.4f}")
    return exec_time, std_max, std_avg, std_cv


def print_final_report(filepath, algo_name, n, k, avg_diff, avg_max, avg_cv, avg_time):
    """Display the final performance report."""
    print(f"\n=== Test Report: {Path(filepath).name} ===")
    print(f"Algorithm: {algo_name} | Datasets: {n} | Number of Subsets (k): {k}")
    print("Validation of Subsets:\tPASSED (no values were added or removed)")
    print("-" * 55)
    print(f"Avg Standardized Pairwise Diff:\t{avg_diff:.4f}")
    print(f"Max Standardized Difference:\t{avg_max:.4f}")
    print(f"Coefficient of Variation (CV):\t{avg_cv:.4f}")
    print(f"Average Execution Time:         \t{avg_time:.6f} s")
    print("=======================================================\n")


def run_tests(filepath, algorithm_func, k=2, *, repeats=1, records=None):
    """Test an algorithm on datasets loaded from a file."""
    try:
        if repeats < 1:
            raise ValueError("repeats must be greater than zero.")
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            raise ValueError("File is empty.")

        expected = int(lines[0])
        if expected < 1 or len(lines) - 1 != expected:
            raise ValueError("Dataset count does not match the file header.")

        results = []
        details = []
        for i in range(1, int(lines[0]) + 1):
            dataset = list(map(int, lines[i].split()))
            for repeat in range(1, repeats + 1):
                metadata = {} if records is not None else None
                metrics = process_single_dataset(dataset, algorithm_func, k, i, metadata=metadata)
                results.append(metrics)
                if metadata is not None:
                    details.append(metadata)
                    records.append(dict(dataset_index=i, size=len(dataset), k=k,
                                        repeat=repeat, time_seconds=metrics[0],
                                        standardized_max_difference=metrics[1],
                                        standardized_avg_difference=metrics[2],
                                        cv=metrics[3], **metadata))

        if not results:
            print("No datasets were processed. Exiting.")
            return

        # Calculate average metrics.
        avg_time = statistics.mean([res[0] for res in results])
        avg_max_diff = statistics.mean([res[1] for res in results])
        avg_diff = statistics.mean([res[2] for res in results])
        avg_cv = statistics.mean([res[3] for res in results])

        print_final_report(filepath, algorithm_func.__name__, expected, k, avg_diff, avg_max_diff, avg_cv, avg_time)
        print(f"Repeats per dataset: {repeats}")
        if details:
            print(f"Strategies: {dict(Counter(d.get('strategy', 'unknown') for d in details))}")
            print(f"LP statuses: {dict(Counter(d.get('lp_status', 'NotRun') for d in details))}")
            scopes = sorted({d.get('lp_scope', '') for d in details} - {''})
            if scopes:
                print(f"LP scope: {', '.join(scopes)} (optimality applies only to this scope)")
        return avg_diff, avg_max_diff, avg_cv, avg_time

    except Exception as e:
        raise RuntimeError(f"Benchmark failed for {filepath}: {e}") from e
