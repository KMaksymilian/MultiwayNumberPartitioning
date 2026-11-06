import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from experiments_cv import (best_threshold, candidate_thresholds, collect_branch_results,
                            cross_validate_threshold, minimax_threshold, regret_curve)


def record(cv, kk, lp):
    return {"measured_cv": cv, "kk_std_max": kk, "lp_std_max": lp,
            "kk_time": 0.0, "lp_time": 0.0}


# KK is better for CV <= 0.5, LP+GNP for CV >= 1.0.
RECORDS = [record(0.2, 1, 3), record(0.5, 2, 4), record(1.0, 5, 1), record(1.5, 6, 2)]


class ThresholdTests(unittest.TestCase):
    def test_regret_curve_matches_branch_choice(self):
        thresholds = [float("-inf"), 0.5, float("inf")]
        # always LP: 2 + 2 + 0 + 0; split at 0.5: 0; always KK: 0 + 0 + 4 + 4
        self.assertEqual(regret_curve(RECORDS, thresholds), [1.0, 0.0, 2.0])

    def test_best_threshold_lies_between_branches(self):
        t, regret = best_threshold(RECORDS)
        self.assertEqual(regret, 0.0)
        self.assertGreaterEqual(t, 0.5)
        self.assertLess(t, 1.0)

    def test_candidates_cover_both_extremes(self):
        thresholds = candidate_thresholds(RECORDS)
        self.assertEqual(thresholds[0], 0.0)
        self.assertEqual(thresholds[-1], 1.5)

    def test_cross_validation_and_minimax(self):
        records = RECORDS * 5
        result = cross_validate_threshold(records, folds=4, seed=0)
        self.assertEqual(result["mean"]["test_regret"], 0.0)
        minimax = minimax_threshold({"a": RECORDS, "b": RECORDS})
        self.assertEqual(minimax["worst_regret"], 0.0)

    def test_collect_branch_results(self):
        records = collect_branch_results(cvs=[0.3, 2.0], n=20, k=3, num_datasets=2,
                                         seed=0, time_limit=0.5)
        self.assertEqual(len(records), 4)
        self.assertTrue(all(r["kk_d"] >= 0 and r["lp_d"] >= 0 for r in records))


if __name__ == "__main__":
    unittest.main()
