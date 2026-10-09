import argparse
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


def generate_datasets():
    """Generate standard and unbalanced test datasets."""
    export_datasets("unit_tests_dataset")
    export_datasets(
        "stress_tests_dataset",
        num_datasets=12,
        datasets_sizes=[10, 100, 1000, 10000],
    )
    export_datasets(
        "unbalanced_dataset",
        num_datasets=10,
        datasets_sizes=[100],
        balance=0.90,
    )
    export_datasets(
        "difficult_datasets",
        num_datasets=3,
        datasets_sizes=[1000000],
        balance=0.90,
    )


def test_algorithm(name, filepath, k):
    """Test a selected algorithm."""
    algorithm = ALGORITHMS[name]

    print(f"\nRunning {name.upper()} on {filepath}")
    return run_tests(filepath, algorithm, k)


def compare_algorithms(filepath, k):
    """Compare algorithms using the same dataset."""
    results = {}

    for name in ALGORITHMS:
        # LP is intended for smaller datasets.
        if name == "lp" and is_large_dataset(filepath):
            print("\nSkipping LP for large datasets.")
            continue

        result = test_algorithm(name, filepath, k)

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

    args = parser.parse_args()

    if args.k < 1:
        parser.error("k must be greater than zero.")

    if args.generate:
        generate_datasets()
        print("\nDataset generation completed.")
        return

    filepath = Path(args.dataset)

    if not filepath.is_file():
        parser.error(
            f"Dataset file not found: {filepath}\n"
            "Generate datasets first using --generate."
        )

    if args.algorithm == "all":
        compare_algorithms(filepath, args.k)
    else:
        if args.algorithm == "lp" and is_large_dataset(filepath):
            parser.error(
                "Dataset is too large for LP benchmarking. "
                "Use a dataset with at most 100 numbers per instance."
            )

        test_algorithm(args.algorithm, filepath, args.k)


if __name__ == "__main__":
    main()