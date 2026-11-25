import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main


class LabCVThresholdTests(unittest.TestCase):
    def test_accepts_report_threshold_and_passes_it_to_orchestrator(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = Path(folder) / "dane.txt"
            dataset.write_text("1\n1 2 3\n", encoding="utf-8")
            arguments = ["main", "--lab", "--algorithm", "orchestrator",
                         "--dataset", str(dataset), "-k", "2", "--cv-threshold", "4.26"]
            with patch.object(sys, "argv", arguments), patch.object(main, "write_lab_output") as write:
                main.main()
            self.assertEqual(write.call_args.kwargs["cv_threshold"], 4.26)

    def test_rejects_negative_and_nonfinite_thresholds(self):
        for threshold in ("-0.1", "nan", "inf"):
            with self.subTest(threshold=threshold):
                arguments = ["main", "--lab", "--algorithm", "orchestrator",
                             f"--cv-threshold={threshold}"]
                with patch.object(sys, "argv", arguments), patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                    main.main()
                self.assertEqual(error.exception.code, 2)
