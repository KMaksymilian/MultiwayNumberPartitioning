import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lab_output import write_lab_output


class LabOutputTests(unittest.TestCase):
    def test_writes_groups_in_lexicographic_order_and_preserves_input_order(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "Dane testowe.txt"
            source.write_text("2\n5 8 5 7 5 5\n9\n", encoding="utf-8-sig")

            def partition(dataset, k):
                if len(dataset) == 1:
                    return [[], dataset, []]
                return [[5, 7, 5], [5, 5], [8]]

            result = write_lab_output(source, 3, partition)

            self.assertEqual(result, source.with_name("Dane testowe_output.txt"))
            self.assertEqual(
                result.read_text(encoding="utf-8"),
                "2 3\n\n35 5 8 5 7 5 5\n8 8\n17 7 5 5\n10 5 5\n9\n"
                "\n9 9\n9 9\n0\n0\n9\n",
            )

    def test_preserves_previous_output_if_a_later_partition_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "dane.txt"
            source.write_text("2\n1\n2\n", encoding="utf-8")
            result = source.with_name("dane_output.txt")
            result.write_text("previous result", encoding="utf-8")

            def partition(dataset, k):
                return [[1], []]

            with self.assertRaisesRegex(ValueError, "Invalid partition for dataset 2"):
                write_lab_output(source, 2, partition)

            self.assertEqual(result.read_text(encoding="utf-8"), "previous result")
            self.assertEqual(set(source.parent.iterdir()), {source, result})
