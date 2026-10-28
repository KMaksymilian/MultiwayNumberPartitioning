import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from algorithm_kk import algorithm_kk
from orchestrator import orchestrator_partitioning
from testing import process_single_dataset, run_tests, validate_partitions


class PartitioningTests(unittest.TestCase):
    def test_validator_requires_exact_group_count(self):
        self.assertFalse(validate_partitions([1, 2], [[1, 2]], 2))
        with self.assertRaises(ValueError):
            process_single_dataset([1, 2], lambda a, k: [a], 2, 1)

    def test_validator_preserves_duplicates(self):
        self.assertFalse(validate_partitions([1, 1, 2], [[1], [2, 2]], 2))
        self.assertTrue(validate_partitions([1, 1, 2], [[1, 1], [2]], 2))

    def test_empty_and_invalid_inputs(self):
        for algorithm in [algorithm_kk, orchestrator_partitioning]:
            with self.subTest(algorithm=algorithm.__name__):
                self.assertEqual(algorithm([], 3), [[], [], []])
                for numbers, k in [([1], 0), ([], 0), ([-5], 2)]:
                    with self.assertRaises(ValueError):
                        algorithm(numbers, k)

    def test_lp_failure_is_logged_and_fallback_preserves_data(self):
        numbers = [0] * 1000 + [10] * 10 + [100]
        with patch("orchestrator.algorithm_lp", side_effect=RuntimeError("no solution")) as solver:
            with self.assertLogs("orchestrator", level="WARNING") as logs:
                partitions = orchestrator_partitioning(numbers, 4)
        solver.assert_called_once()
        self.assertIn("no solution", logs.output[0])
        self.assertTrue(validate_partitions(numbers, partitions, 4))

    def test_orchestrator_uses_real_lp(self):
        from algorithm_lp import algorithm_lp

        numbers = [0] * 1000 + [10] * 10 + [100]
        with patch("orchestrator.algorithm_lp", wraps=algorithm_lp) as solver:
            partitions = orchestrator_partitioning(numbers, 4)
        solver.assert_called_once()
        self.assertTrue(validate_partitions(numbers, partitions, 4))

    def test_benchmark_rejects_truncated_file_and_propagates_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data"
            path.write_text("2\n1 2\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "count"):
                run_tests(path, algorithm_kk)
            path.write_text("1\n1 2\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "solver failed"):
                run_tests(path, Mock(side_effect=RuntimeError("solver failed")))


if __name__ == "__main__":
    unittest.main()
