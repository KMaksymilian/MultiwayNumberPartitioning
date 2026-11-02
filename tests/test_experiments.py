import csv
import io
import itertools
import random
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pulp
from pulp.constants import LpSolveStatus
from algorithm_lp import algorithm_lp
from algorithm_kk import algorithm_kk
from algorithm_gnp import algorithm_gnp
from dataset_generator import export_datasets
from orchestrator import orchestrator_partitioning


def exhaustive_optimum(numbers, k):
    """Independent oracle: enumerate every assignment, including empty groups."""
    best = sum(numbers)
    for assignment in itertools.product(range(k), repeat=len(numbers)):
        sums = [0] * k
        for number, group in zip(numbers, assignment):
            sums[group] += number
        best = min(best, max(sums) - min(sums))
    return best


class ExperimentTests(unittest.TestCase):
    def test_small_partitions_against_exhaustive_oracle(self):
        rng = random.Random(17)
        cases = [([0, 0], 3), ([2], 3), ([1, 1, 3], 2)]
        cases += [([rng.randrange(10) for _ in range(5)], k)
                  for k in [2, 3] for _ in range(4)]
        for numbers, k in cases:
            optimum = exhaustive_optimum(numbers, k)
            with self.subTest(numbers=numbers, k=k):
                metadata = {}
                partitions = algorithm_lp(numbers, k, metadata=metadata)
                sums = list(map(sum, partitions))
                self.assertTrue(metadata["lp_optimal"])
                self.assertEqual(max(sums) - min(sums), optimum)
                for heuristic in [algorithm_kk, orchestrator_partitioning,
                                  lambda a, k: algorithm_gnp(a, [0] * k)]:
                    groups = heuristic(numbers, k)
                    sums = list(map(sum, groups))
                    self.assertGreaterEqual(max(sums) - min(sums), optimum)

    def test_feasible_time_limit_is_not_reported_as_optimal(self):
        solve = pulp.LpProblem.solve

        def limited(problem, solver):
            solve(problem, solver)
            return SimpleNamespace(has_solution=True, status=LpSolveStatus.TimeLimit)

        metadata = {}
        with patch.object(pulp.LpProblem, "solve", limited):
            algorithm_lp([1, 2, 3], 2, metadata=metadata)
        self.assertEqual(metadata["lp_status"], "TimeLimit")
        self.assertFalse(metadata["lp_optimal"])

    def test_fallback_metadata(self):
        metadata = {}
        with patch("orchestrator.algorithm_lp", side_effect=RuntimeError("test failure")):
            with self.assertLogs("orchestrator", level="WARNING"):
                orchestrator_partitioning([0] * 1000 + [10] * 10 + [100], 4,
                                         metadata=metadata)
        self.assertEqual(metadata["strategy"], "kk+gnp_fallback")
        self.assertTrue(metadata["lp_attempted"])
        self.assertEqual(metadata["fallback_reason"], "test failure")
        self.assertFalse(metadata["lp_optimal"])

    def test_seeded_exports_and_csv_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            with redirect_stdout(io.StringIO()):
                for name in ["a", "b"]:
                    export_datasets(name, num_datasets=2, datasets_sizes=[5],
                                    seed=42, path=directory)
            self.assertEqual((directory / "a").read_bytes(), (directory / "b").read_bytes())
            source = directory / "input"
            source.write_text("1\n1 1 1 100\n", encoding="utf-8")
            output = directory / "results.csv"
            root = Path(__file__).resolve().parents[1]
            result = subprocess.run(
                [sys.executable, "-B", str(root / "src/main.py"), "--dataset", str(source),
                 "--algorithm", "all", "-k", "2", "--repeats", "2", "--csv", str(output)],
                cwd=root, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 8)
            self.assertEqual({row["repeat"] for row in rows}, {"1", "2"})
            self.assertEqual({row["algorithm"] for row in rows}, {"kk", "gnp", "lp", "orchestrator"})
            for row in rows:
                self.assertTrue(row["pulp_version"])
                self.assertEqual(len(row["dataset_sha256"]), 64)
                self.assertEqual(row["size"], "4")
                if row["algorithm"] == "lp":
                    self.assertEqual(row["lp_status"], "Optimal")
                    self.assertEqual(row["lp_scope"], "full_dataset")
                if row["algorithm"] == "orchestrator":
                    self.assertEqual(row["pruning_enabled"], "True")
                    self.assertEqual(row["strategy"], "lp+gnp")
                    self.assertTrue(row["initial_range"])


if __name__ == "__main__":
    unittest.main()
