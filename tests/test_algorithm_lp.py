import sys
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from algorithm_lp import algorithm_lp


class LinearProgrammingTests(unittest.TestCase):
    def test_known_optimal_ranges(self):
        cases = [
            ([10, 20, 30, 40, 50, 60], 3, 0),
            ([1, 2, 4], 2, 1),
            ([5, 5, 5, 5, 0, 0], 2, 0),
            ([0, 0, 0], 2, 0),
            ([3, 7], 1, 0),
            ([2], 3, 2),
        ]
        for numbers, k, expected_range in cases:
            with self.subTest(numbers=numbers, k=k):
                original = numbers.copy()
                partitions = algorithm_lp(numbers, k)
                self.assertEqual(len(partitions), k)
                self.assertEqual(
                    Counter(x for group in partitions for x in group),
                    Counter(original),
                )
                self.assertEqual(numbers, original)
                sums = [sum(group) for group in partitions]
                self.assertEqual(max(sums) - min(sums), expected_range)

    def test_empty_input(self):
        self.assertEqual(algorithm_lp([], 3), [[], [], []])

    def test_solver_without_feasible_solution(self):
        result = SimpleNamespace(has_solution=False, status=SimpleNamespace(name="TimeLimit"))
        with patch("algorithm_lp.pulp.LpProblem.solve", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "TimeLimit"):
                algorithm_lp([1, 2, 4], 2)

    def test_zero_range_skips_model_construction_and_gnp_when_kk_is_perfect(self):
        for numbers, k in [([5, 5, 5, 5, 0, 0], 2), ([0, 0], 3), ([3, 7], 1)]:
            with self.subTest(numbers=numbers, k=k):
                metadata = {}
                with patch("algorithm_lp.pulp.LpProblem") as model, patch("algorithm_lp.algorithm_gnp") as gnp:
                    groups = algorithm_lp(numbers, k, metadata=metadata)
                model.assert_not_called()
                gnp.assert_not_called()
                self.assertEqual(len(groups), k)
                self.assertEqual(Counter(x for group in groups for x in group), Counter(numbers))
                self.assertEqual(len(set(map(sum, groups))), 1)
                self.assertEqual(metadata["lp_status"], "HeuristicOptimal")
                self.assertTrue(metadata["lp_optimal"])
                self.assertFalse(metadata["lp_attempted"])

    def test_gnp_zero_range_also_skips_model(self):
        numbers = [1, 2, 3]
        metadata = {}
        with patch("algorithm_lp.algorithm_kk", return_value=[[1, 2, 3], []]), patch("algorithm_lp.pulp.LpProblem") as model:
            groups = algorithm_lp(numbers, 2, metadata=metadata)
        model.assert_not_called()
        self.assertEqual(sorted(map(sum, groups)), [3, 3])
        self.assertFalse(metadata["lp_attempted"])

    def test_nonzero_range_still_calls_solver(self):
        import pulp

        with patch("algorithm_lp.pulp.LpProblem.solve", autospec=True, side_effect=pulp.LpProblem.solve) as solve:
            metadata = {}
            algorithm_lp([8, 7, 6, 5, 4], 3, metadata=metadata)
        solve.assert_called_once()
        self.assertTrue(metadata["lp_attempted"])

    def test_invalid_inputs(self):
        for numbers, k in [([1], 0), ([], 0), ([1], -1), ([-1], 2)]:
            with self.subTest(numbers=numbers, k=k):
                with self.assertRaises(ValueError):
                    algorithm_lp(numbers, k)


if __name__ == "__main__":
    unittest.main()
