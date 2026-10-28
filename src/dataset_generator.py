import random
import argparse
from pathlib import Path


def generate_dataset(size, balance=1.0, lower_scope=(1, 1000), upper_scope=(2000, 20000)):
    """Generate a random dataset with adjustable balance."""
    dataset = []

    for _ in range(size):
        if random.random() < balance:
            dataset.append(random.randint(*lower_scope))
        else:
            dataset.append(random.randint(*upper_scope))

    random.shuffle(dataset)
    return dataset


def export_datasets(filename, num_datasets=10, datasets_sizes=[10], balance=1.0, path="examples"):
    """Generate and save datasets to a file."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)

        full_path = Path(path) / filename
        with open(full_path, 'w') as f:
            f.write(f"{num_datasets}\n")

            for i in range(num_datasets):
                size = datasets_sizes[i % len(datasets_sizes)]
                dataset = generate_dataset(size, balance)
                line = " ".join(map(str, dataset))
                f.write(f"{line}\n")

        print(f"Successfully created dataset: {filename}")
    except Exception as e:
        print(f"Error encountered: {e}")


if __name__ == "__main__":
    # Standard datasets
    export_datasets("unit_tests_dataset")
    export_datasets("stress_tests_dataset", 12, [10, 100, 1000, 10000])

    # Unbalanced datasets
    export_datasets("unbalanced_dataset", 10, [100], balance=0.90)
    export_datasets("difficult_datasets", 3, [1000000], balance=0.90)