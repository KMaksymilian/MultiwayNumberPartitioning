import time
import random
import statistics
from itertools import combinations
from pathlib import Path

from dataset_generator import generate_with_target_cv, dataset_cv
from distributions import DISTRIBUTIONS


def validate_partitions(original_dataset, partitions):
    """Check whether all original numbers are preserved."""
    flattened_partitions = [item for sublist in partitions for item in sublist]
    return sorted(original_dataset) == sorted(flattened_partitions)


def process_single_dataset(dataset, algorithm_func, k, index):
    """Run an algorithm and calculate partition quality metrics."""
    start_time = time.perf_counter()
    partitions = algorithm_func(dataset.copy(), k)
    exec_time = time.perf_counter() - start_time

    if not validate_partitions(dataset, partitions):
        print(f"\n[Critical Error] Data integrity check failed for dataset {index}!")
        return None

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


def run_tests(filepath, algorithm_func, k=2):
    """Test an algorithm on datasets loaded from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            print("File is empty.")
            return

        results = []
        for i in range(1, int(lines[0]) + 1):
            if i >= len(lines):
                break

            dataset = list(map(int, lines[i].split()))
            metrics = process_single_dataset(dataset, algorithm_func, k, i)

            if metrics is None:
                return  # Stop if data integrity validation fails.

            results.append(metrics)

        if not results:
            print("No datasets were processed. Exiting.")
            return

        # Calculate average metrics.
        avg_time = statistics.mean([res[0] for res in results])
        avg_max_diff = statistics.mean([res[1] for res in results])
        avg_diff = statistics.mean([res[2] for res in results])
        avg_cv = statistics.mean([res[3] for res in results])

        print_final_report(filepath, algorithm_func.__name__, len(results), k, avg_diff, avg_max_diff, avg_cv, avg_time)
        return avg_diff, avg_max_diff, avg_cv, avg_time

    except Exception as e:
        print(f"An error occurred: {e}")


def validate_generated_dataset(dataset, expected_size):
	"""Check that a generated dataset has the expected size and contains only natural numbers."""
	size_ok = len(dataset) == expected_size
	natural_ok = all(isinstance(x, int) and x >= 1 for x in dataset)
	return size_ok, natural_ok


def check_target_cv(cv, size=100_000, distribution="lognormal", mean=10_000, seed=None):
	"""Generate one dataset with a target CV and compare it with the measured CV.

	Returns None when the distribution cannot reach the requested CV.
	"""
	rng = random.Random(seed)
	try:
		dataset = generate_with_target_cv(size, cv, distribution, mean, rng)
	except ValueError:
		return None

	size_ok, natural_ok = validate_generated_dataset(dataset, size)
	measured_cv = dataset_cv(dataset)
	abs_diff = abs(measured_cv - cv)
	rel_diff = abs_diff / cv
	# With mean 10 000 a value of 1 practically only comes from clipping in discretize().
	ones_share = dataset.count(1) / size if size else 0.0

	return {
		"distribution": distribution,
		"target_cv": cv,
		"measured_cv": measured_cv,
		"abs_diff": abs_diff,
		"rel_diff": rel_diff,
		"ones_share": ones_share,
		"size_ok": size_ok,
		"natural_ok": natural_ok,
	}


def print_generator_validation(results, size):
	"""Print size and natural-number validation for a list of generator results."""
	size_failed = [(r["distribution"], r["target_cv"]) for r in results if not r["size_ok"]]
	natural_failed = [(r["distribution"], r["target_cv"]) for r in results if not r["natural_ok"]]

	if size_failed:
		print(f"Validation of Size:\t\tFAILED for (distribution, CV): {size_failed}")
	else:
		print(f"Validation of Size:\t\tPASSED (every dataset has {size} numbers)")

	if natural_failed:
		print(f"Validation of Values:\tFAILED for (distribution, CV): {natural_failed}")
	else:
		print("Validation of Values:\tPASSED (all numbers are natural, >= 1)")


def run_generator_tests(cvs=(0.3, 0.6, 1.0, 1.5, 2.0, 3.0), size=100_000,
                        distribution="lognormal", mean=10_000, seed=None):
	"""Check the target-CV generator of one distribution for several CV values."""
	results = {cv: check_target_cv(cv, size, distribution, mean, seed) for cv in cvs}
	valid = [r for r in results.values() if r is not None]

	print(f"\n=== Generator Test: {distribution} | Size: {size} | Mean: {mean} | Seed: {seed} ===")
	print_generator_validation(valid, size)

	print("-" * 54)
	print(f"{'Target CV':>10}{'Measured CV':>13}{'Abs Diff':>11}{'Rel Diff':>10}{'Ones':>10}")
	print("-" * 54)

	for cv, result in results.items():
		if result is None:
			print(f"{cv:>10.2f}{'not reachable for ' + distribution:>44}")
			continue

		print(f"{result['target_cv']:>10.2f}"
		      f"{result['measured_cv']:>13.4f}"
		      f"{result['abs_diff']:>11.4f}"
		      f"{result['rel_diff']:>10.2%}"
		      f"{result['ones_share']:>10.2%}")

	print("=" * 54 + "\n")
	return valid


def compare_distributions(cvs=(0.3, 0.6, 1.0, 1.5, 2.0, 3.0), distributions=None,
                          size=100_000, mean=10_000, seed=None):
	"""Compare the measured CV of several distributions for the same target CVs and seed.

	Prints two tables: the measured CV and the share of values clipped to 1.
	"-" means the distribution cannot reach that CV.
	"""
	distributions = distributions or sorted(DISTRIBUTIONS)
	results = {
		(name, cv): check_target_cv(cv, size, name, mean, seed)
		for name in distributions
		for cv in cvs
	}
	valid = [r for r in results.values() if r is not None]
	width = 10 + 12 * len(distributions)

	def print_table(title, key, fmt):
		print(title)
		print("-" * width)
		print(f"{'Target CV':>10}" + "".join(f"{name:>12}" for name in distributions))
		print("-" * width)
		for cv in cvs:
			row = f"{cv:>10.2f}"
			for name in distributions:
				result = results[(name, cv)]
				row += f"{'-':>12}" if result is None else f"{result[key]:>12{fmt}}"
			print(row)
		print("-" * width)

	print(f"\n=== Distribution Comparison | Size: {size} | Mean: {mean} | Seed: {seed} ===")
	print_generator_validation(valid, size)
	print()
	print_table("Measured CV:", "measured_cv", ".4f")
	print()
	print_table("Values clipped to 1 (share of dataset):", "ones_share", ".2%")
	print("=" * width + "\n")
	return valid


def partition_metrics(dataset, partitions, k):
	"""Return partition quality metrics:
	max_diff   – largest partition sum minus smallest partition sum
	std_max    – max_diff / total sum (same as in process_single_dataset)
	valid      – whether all original numbers are preserved
	"""
	valid = len(partitions) == k and validate_partitions(dataset, partitions)

	sums = [sum(p) for p in partitions]
	total_sum = sum(sums)
	max_diff = max(sums) - min(sums) if sums else 0

	return {
		"valid": valid,
		"max_diff": max_diff,
		"std_max": max_diff / total_sum if total_sum else 0.0,
	}
