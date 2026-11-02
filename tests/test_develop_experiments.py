import contextlib
import importlib.util
import io
import random
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dataset_generator import generate_with_target_cv
from experiments import run_grid_point, run_cv_sweep, print_grid_point
from testing import check_target_cv, compare_distributions, partition_metrics
from algorithm_lp import algorithm_lp
from orchestrator import orchestrator_partitioning


class DevelopExperimentsTests(unittest.TestCase):
    def test_target_cv_generation_for_all_distributions(self):
        for name in ["lognormal", "gamma", "uniform"]:
            with self.subTest(distribution=name):
                a = generate_with_target_cv(20, .3, name, 100, random.Random(4))
                b = generate_with_target_cv(20, .3, name, 100, random.Random(4))
                self.assertEqual(a, b)
                self.assertEqual(len(a), 20)
                self.assertTrue(all(isinstance(x, int) and x >= 1 for x in a))

    def test_partition_metrics_validates_number_of_groups_and_duplicates(self):
        result = partition_metrics([1, 1, 4], [[1, 1], [4]], 2)
        self.assertTrue(result["valid"])
        self.assertEqual(result["max_diff"], 2)
        self.assertAlmostEqual(result["std_max"], 1 / 3)
        self.assertFalse(partition_metrics([1, 1, 4], [[1, 4], [4]], 2)["valid"])
        self.assertFalse(partition_metrics([1, 1, 4], [[1, 1, 4]], 2)["valid"])

    def test_generator_diagnostics(self):
        result = check_target_cv(.3, size=20, seed=5)
        self.assertTrue(result["size_ok"])
        self.assertTrue(result["natural_ok"])
        with contextlib.redirect_stdout(io.StringIO()):
            results = compare_distributions(cvs=[.3], size=20, seed=5)
        self.assertEqual(len(results), 3)

    def test_grid_and_sweep_complete_end_to_end(self):
        result = run_grid_point(100, 30, n=8, k=2, num_datasets=2, seed=7)
        self.assertAlmostEqual(result["orch_wins"] + result["kk_wins"] + result["ties"], 1)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            print_grid_point(result)
            sweep = run_cv_sweep(cvs=[.3, .8], n=8, k=2, num_datasets=2, seed=7)
        self.assertEqual(len(sweep["records"]), 4)

    def test_invalid_experiment_parameters_are_rejected(self):
        for kwargs in [dict(mean=0, std=1), dict(mean=100, std=float("nan")),
                       dict(mean=100, std=30, num_datasets=0), dict(mean=100, std=30, n=1)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                run_grid_point(**kwargs)
        for cv in [float("nan"), float("inf")]:
            with self.subTest(cv=cv), self.assertRaises(ValueError):
                generate_with_target_cv(10, cv)

    def test_ratio_report_labels_the_smoothed_ratio(self):
        with patch("experiments.run_algorithm", side_effect=[
            dict(max_diff=0, std_max=0, time=.1),
            dict(max_diff=1, std_max=.01, time=.2),
        ]):
            result = run_grid_point(100, 30, n=8, k=2, num_datasets=1, seed=7)
        self.assertEqual(result["d_ratio"], 2)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            print_grid_point(result)
        self.assertIn("(D_orch + 1) / (D_kk + 1)", output.getvalue())

    def test_zero_range_subproblem_skips_model_and_reports_actual_strategy(self):
        metadata = {}
        with patch("algorithm_lp.pulp.LpProblem") as model:
            groups = orchestrator_partitioning([1] * 100 + [100, 100], 2, metadata=metadata)
        model.assert_not_called()
        self.assertEqual(list(map(sum, groups)), [150, 150])
        self.assertEqual(metadata["strategy"], "heuristic+gnp")
        self.assertEqual(metadata["lp_status"], "HeuristicOptimal")
        self.assertFalse(metadata["lp_attempted"])
        self.assertTrue(metadata["lp_optimal"])

    def test_zero_range_gnp_candidate_skips_model(self):
        with patch("algorithm_lp.algorithm_kk", return_value=[[1, 2, 3], []]), \
                patch("algorithm_lp.pulp.LpProblem") as model:
            groups = algorithm_lp([1, 2, 3], 2, pruning=True)
        model.assert_not_called()
        self.assertEqual(list(map(sum, groups)), [3, 3])

    def test_invalid_lp_partition_cannot_keep_optimal_flag(self):
        def invalid(numbers, k, **kwargs):
            kwargs["metadata"].update(lp_status="Optimal", lp_optimal=True)
            return [numbers]

        metadata = {}
        with patch("orchestrator.algorithm_lp", side_effect=invalid):
            with self.assertLogs("orchestrator", level="WARNING"):
                orchestrator_partitioning([1] * 100 + [100, 100], 2, metadata=metadata)
        self.assertEqual(metadata["strategy"], "kk+gnp_fallback")
        self.assertFalse(metadata["lp_optimal"])

    @unittest.skipUnless(importlib.util.find_spec("matplotlib"), "Install the plots extra")
    def test_heatmap_and_sweep_figures(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from plots import plot_mu_sigma_heatmap, plot_quality_vs_cv

        result = run_grid_point(100, 30, n=8, k=2, num_datasets=1, seed=7)
        grid = dict(means=[100], stds=[30], results=[[result]],
                    distribution="lognormal", n=8, k=2, num_datasets=1, seed=7)
        with contextlib.redirect_stdout(io.StringIO()):
            sweep = run_cv_sweep(cvs=[.3], n=8, k=2, num_datasets=2, seed=7)
        try:
            self.assertIsNotNone(plot_mu_sigma_heatmap(grid, show=False))
            self.assertIsNotNone(plot_quality_vs_cv(sweep, show=False))
        finally:
            plt.close("all")


if __name__ == "__main__":
    unittest.main()
