from pathlib import Path
from tempfile import NamedTemporaryFile

from testing import validate_partitions


def _sum_and_values(values):
    return " ".join(map(str, [sum(values), *values]))


def write_lab_output(filepath, k, partition, **options):
    """Save one validated partition per input dataset in the laboratory format."""
    with filepath.open(encoding="utf-8-sig") as source:
        lines = [line.strip() for line in source if line.strip()]
    if not lines:
        raise ValueError("Input file is empty.")
    count = int(lines[0])
    if count < 1 or len(lines) - 1 != count:
        raise ValueError("Dataset count does not match the file header.")

    destination = filepath.with_name(f"{filepath.stem}_output.txt")
    if destination.resolve() == filepath.resolve():
        raise ValueError("The result must not overwrite the input file.")

    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                delete=False) as output:
            temporary = Path(output.name)
            output.write(f"{count} {k}\n")
            for index, line in enumerate(lines[1:], start=1):
                dataset = list(map(int, line.split()))
                if any(value < 0 for value in dataset):
                    raise ValueError(f"Dataset {index} contains a negative number.")
                groups = partition(dataset.copy(), k, **options)
                if not validate_partitions(dataset, groups, k):
                    raise ValueError(f"Invalid partition for dataset {index}.")

                ordered = sorted((sorted(group, reverse=True) for group in groups), reverse=True)
                sums = [sum(group) for group in ordered]
                output.write("\n" + _sum_and_values(dataset) + "\n")
                for group in ordered:
                    output.write(_sum_and_values(group) + "\n")
                output.write(f"{max(sums) - min(sums)}\n")
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination
