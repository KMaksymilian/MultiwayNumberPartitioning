import itertools
import random
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pulp
from algorithm_lp import algorithm_lp
from orchestrator import orchestrator_partitioning


def optimal_range(numbers, k):
    best = sum(numbers)
    for assignment in itertools.product(range(k), repeat=len(numbers)):
        sums = [0] * k
        for number, group in zip(numbers, assignment):
            sums[group] += number
        best = min(best, max(sums) - min(sums))
    return best


class PruningTests(unittest.TestCase):
    def test_pruned_model_preserves_optimum_and_ordered_loads(self):
        rng = random.Random(41)
        cases = [([8, 7, 6, 5, 4], 3), ([0, 0, 0], 3), ([2], 4),
                 ([0, 5, 5, 5, 5], 2), ([3, 7], 1), ([1, 2, 4], 2)]
        cases += [([rng.randrange(10) for _ in range(5)], k)
                  for k in [2, 3, 4] for _ in range(5)]
        for numbers, k in cases:
            with self.subTest(numbers=numbers, k=k):
                metadata = {}
                groups = algorithm_lp(numbers, k, pruning=True, metadata=metadata)
                sums = list(map(sum, groups))
                self.assertEqual(max(sums) - min(sums), optimal_range(numbers, k))
                self.assertEqual(sums, sorted(sums, reverse=True))
                self.assertEqual(len(groups), k)
                self.assertEqual(Counter(x for g in groups for x in g), Counter(numbers))
                self.assertLessEqual(max(sums) - min(sums), metadata["initial_range"])
                self.assertGreaterEqual(min(sums), metadata["sum_lower_bound"])
                self.assertLessEqual(max(sums), metadata["sum_upper_bound"])

    def test_warm_start_satisfies_all_pruning_constraints(self):
        solve = pulp.LpProblem.solve
        checked = []

        def check_start(problem, solver):
            self.assertTrue(solver.optionsDict["warmStart"])
            self.assertTrue(problem.valid(1e-7))
            for name in ["incumbent_range", "sum_lower_0", "sum_upper_0", "ordered_sums_0"]:
                self.assertIsNotNone(problem.get_constraint_by_name(name))
            checked.append(True)
            return solve(problem, solver)

        with patch.object(pulp.LpProblem, "solve", check_start):
            algorithm_lp([0, 5, 5, 8, 8, 13], 3, pruning=True)
        self.assertEqual(checked, [True])

    def test_orchestrator_always_optimizes_extracted_subset(self):
        for numbers, expected in [([1] * 100 + [100, 100], [100, 100]),
                                  ([1] * 100 + [100], [100])]:
            with self.subTest(expected=expected):
                metadata = {}
                with patch("orchestrator.algorithm_lp", wraps=algorithm_lp) as solve:
                    groups = orchestrator_partitioning(numbers, 3, metadata=metadata)
                solve.assert_called_once()
                self.assertEqual(solve.call_args.args[0], expected)
                self.assertTrue(solve.call_args.kwargs["pruning"])
                self.assertEqual(metadata["strategy"], "lp+gnp")
                self.assertEqual(Counter(x for g in groups for x in g), Counter(numbers))
                self.assertLessEqual(metadata["sum_upper_bound"], sum(expected))

    def test_low_variability_still_uses_kk_and_standalone_lp_is_unmodified(self):
        with patch("orchestrator.algorithm_lp") as solve:
            orchestrator_partitioning([10, 10, 10], 2)
        solve.assert_not_called()
        metadata = {}
        algorithm_lp([1, 2, 4], 2, metadata=metadata)
        self.assertFalse(metadata["pruning_enabled"])
        self.assertNotIn("initial_range", metadata)


if __name__ == "__main__":
    unittest.main()
