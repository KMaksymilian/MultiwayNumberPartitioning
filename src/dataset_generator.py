import random
import argparse
import statistics
from pathlib import Path

from distributions import get_distribution


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

def dataset_cv(dataset):
	"""Return the sample coefficient of variation."""
	if len(dataset) < 2:
		return 0.0

	mean_val = statistics.mean(dataset)
	if mean_val <= 0:
		return 0.0

	return statistics.stdev(dataset) / mean_val


def params_for_target_cv(distribution, cv, mean=10_000):
	"""Return parameters of `distribution` for the requested CV and mean."""
	if cv <= 0:
		raise ValueError("cv must be positive.")
	if mean <= 0:
		raise ValueError("mean must be positive.")
	return get_distribution(distribution).params_for_cv(cv, mean)


def discretize(value):
	"""Map a real value to a positive integer (natural number)."""
	return max(1, round(value))


def generate_distribution_dataset(size, distribution, rng=None, **params):
	"""Generate `size` positive integers drawn from `distribution` with `params`."""
	if size < 0:
		raise ValueError("size cannot be negative.")

	dist = get_distribution(distribution)
	rng = rng or random
	return [discretize(dist.sample(rng, **params)) for _ in range(size)]


def generate_with_target_cv(size, cv, distribution="lognormal", mean=10_000, rng=None):
	"""Generate a dataset whose CV is APROXIMATELY `cv`, beacuse true CV differs
	 from the target because of sampling noise and discretization
	 (look at discretize(value) and run_generator_tests in testing.py)."""
	params = params_for_target_cv(distribution, cv, mean)
	return generate_distribution_dataset(size, distribution, rng=rng, **params)

if __name__ == "__main__":
    # Standard datasets
    export_datasets("unit_tests_dataset")
    export_datasets("stress_tests_dataset", 12, [10, 100, 1000, 10000])

    # Unbalanced datasets
    export_datasets("unbalanced_dataset", 10, [100], balance=0.90)
    export_datasets("difficult_datasets", 3, [1000000], balance=0.90)
