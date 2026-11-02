import argparse
import csv
import hashlib
import math
import platform
from importlib.metadata import version
from pathlib import Path

from algorithm_kk import algorithm_kk
from algorithm_lp import algorithm_lp
from algorithm_gnp import algorithm_gnp
from orchestrator import orchestrator_partitioning
from dataset_generator import export_datasets
from testing import run_tests


def run_gnp(dataset, k):
    """Run GNP with empty initial partitions."""
    return algorithm_gnp(dataset, [0] * k)


ALGORITHMS = {
    "kk": algorithm_kk,
    "gnp": run_gnp,
    "lp": algorithm_lp,
    "orchestrator": orchestrator_partitioning,
}


def generate_datasets(seed=0):
    """Generate standard and unbalanced test datasets."""
    export_datasets("unit_tests_dataset", seed=seed)
    export_datasets(
        "stress_tests_dataset",
        num_datasets=12,
        datasets_sizes=[10, 100, 1000, 10000],
        seed=seed,
    )
    export_datasets(
        "unbalanced_dataset",
        num_datasets=10,
        datasets_sizes=[100],
        balance=0.90,
        seed=seed,
    )
    export_datasets(
        "difficult_datasets",
        num_datasets=3,
        datasets_sizes=[1000000],
        balance=0.90,
        seed=seed,
    )


def test_algorithm(name, filepath, k, *, repeats=1, cv_threshold=0.6, time_limit=1.0, records=None):
    """Test a selected algorithm."""
    algorithm = ALGORITHMS[name]

    def configured(dataset, k, *, metadata):
        metadata.update(strategy=name, lp_scope="full_dataset" if name == "lp" else "",
                        lp_attempted=name == "lp", lp_status="NotRun",
                        lp_optimal=False, fallback_reason="")
        if name == "lp":
            return algorithm(dataset, k, time_limit=time_limit, metadata=metadata)
        if name == "orchestrator":
            return algorithm(dataset, k, cv_threshold=cv_threshold,
                             time_limit=time_limit, metadata=metadata)
        return algorithm(dataset, k)

    configured.__name__ = name
    rows = []

    print(f"\nRunning {name.upper()} on {filepath}")
    result = run_tests(filepath, configured, k, repeats=repeats, records=rows)
    if records is not None:
        for row in rows:
            row.update(algorithm=name, cv_threshold=cv_threshold, time_limit=time_limit,
                       repeats=repeats, solver_seed=0, solver_threads=1)
        records.extend(rows)
    return result


def compare_algorithms(filepath, k, **options):
    """Compare algorithms using the same dataset."""
    results = {}

    for name in ALGORITHMS:
        # LP is intended for smaller datasets.
        if name == "lp" and is_large_dataset(filepath):
            print("\nSkipping LP for large datasets.")
            continue

        result = test_algorithm(name, filepath, k, **options)

        if result is not None:
            results[name] = result

    if not results:
        print("No valid results.")
        return

    print("\n" + "=" * 75)
    print("ALGORITHM COMPARISON")
    print("=" * 75)

    print(
        f"{'Algorithm':<15}"
        f"{'Avg Diff':>12}"
        f"{'Max Diff':>12}"
        f"{'CV':>12}"
        f"{'Time (s)':>14}"
    )

    print("-" * 75)

    for name, (avg_diff, max_diff, cv, exec_time) in results.items():
        print(
            f"{name:<15}"
            f"{avg_diff:>12.6f}"
            f"{max_diff:>12.6f}"
            f"{cv:>12.6f}"
            f"{exec_time:>14.6f}"
        )

    best_quality = min(results, key=lambda name: results[name][1])
    fastest = min(results, key=lambda name: results[name][3])

    print("-" * 75)
    print(f"Best balance: {best_quality.upper()}")
    print(f"Fastest:      {fastest.upper()}")


def is_large_dataset(filepath, limit=100):
    """Check whether any dataset exceeds the LP size limit."""
    with open(filepath, "r", encoding="utf-8") as file:
        next(file, None)

        for line in file:
            if len(line.split()) > limit:
                return True

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Multiway Number Partitioning - Algorithm Benchmark"
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate test datasets",
    )

    parser.add_argument(
        "--algorithm",
        choices=[*ALGORITHMS, "all"],
        default="all",
        help="Algorithm to test (default: all)",
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="examples/unit_tests_dataset",
        help="Path to the dataset file",
    )

    parser.add_argument(
        "-k",
        type=int,
        default=4,
        help="Number of partitions (default: 4)",
    )

    parser.add_argument("--repeats", type=int, default=3, help="Runs per dataset (default: 3)")
    parser.add_argument("--cv-threshold", type=float, default=0.6)
    parser.add_argument("--time-limit", type=float, default=1.0, help="Solver time limit in seconds")
    parser.add_argument("--seed", type=int, default=0, help="Dataset generation seed (default: 0)")
    parser.add_argument("--csv", type=Path, help="Write per-run results to CSV (overwrites file)")
    args = parser.parse_args()

    if args.k < 1:
        parser.error("k must be greater than zero.")
    if args.repeats < 1:
        parser.error("repeats must be greater than zero.")
    if not math.isfinite(args.time_limit) or args.time_limit <= 0:
        parser.error("time-limit must be finite and greater than zero.")
    if not math.isfinite(args.cv_threshold) or args.cv_threshold < 0:
        parser.error("cv-threshold must be finite and non-negative.")

    if args.generate:
        generate_datasets(args.seed)
        print("\nDataset generation completed.")
        return

    filepath = Path(args.dataset)

    if not filepath.is_file():
        parser.error(
            f"Dataset file not found: {filepath}\n"
            "Generate datasets first using --generate."
        )

    if args.csv and args.csv.resolve() == filepath.resolve():
        parser.error("CSV output must not overwrite the input dataset.")
    records = []
    options = dict(repeats=args.repeats, cv_threshold=args.cv_threshold,
                   time_limit=args.time_limit, records=records)
    if args.algorithm == "all":
        compare_algorithms(filepath, args.k, **options)
    else:
        if args.algorithm == "lp" and is_large_dataset(filepath):
            parser.error(
                "Dataset is too large for LP benchmarking. "
                "Use a dataset with at most 100 numbers per instance."
            )

        test_algorithm(args.algorithm, filepath, args.k, **options)

    if args.csv:
        provenance = dict(dataset_file=str(filepath),
                          dataset_sha256=hashlib.sha256(filepath.read_bytes()).hexdigest(),
                          python_version=platform.python_version(),
                          pulp_version=version("pulp"), highs_version=version("highspy"))
        for row in records:
            row.update(provenance)
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        print(f"Results saved to {args.csv}")


if __name__ == "__main__":
    main()
