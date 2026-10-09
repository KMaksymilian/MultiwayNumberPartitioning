# Multiway Number Partitioning

A Python project for solving and evaluating the **Multiway Number Partitioning Problem** using heuristic, optimization-based, and hybrid algorithms.

The project implements three partitioning methods — **Karmarkar–Karp (KK)**, **Greedy Number Partitioning (GNP)**, and **Linear Programming (LP)** — together with an adaptive **orchestrator** that selects algorithms based on the statistical properties of the input data.

## 1. Problem Description

The Multiway Number Partitioning Problem consists of dividing a set of numbers into `k` subsets while keeping their sums as balanced as possible.

Given a dataset:

```text
A = [10, 20, 30, 40, 50, 60]
k = 3
```

An ideal partitioning would be:

```text
Partition 1: [10, 60] → Sum: 70
Partition 2: [20, 50] → Sum: 70
Partition 3: [30, 40] → Sum: 70
```

The objective is to minimize the difference between the largest and smallest partition sums:

\[
\min \left(\max_i S_i-\min_i S_i\right)
\]

where \(S_i\) represents the sum of numbers assigned to partition \(i\).

Each input number must be assigned to exactly one partition, without adding or removing elements.

## 2. Implemented Algorithms

### Karmarkar–Karp (KK)

File: `src/algorithm_kk.py`

A heuristic algorithm based on repeatedly merging partitions with the largest differences between their sums.

The implementation uses a priority queue to select partition structures and combines them by pairing partitions in opposite sum order.

**Characteristics:**
- Deterministic heuristic approach
- Supports multiple partitions
- Does not guarantee an optimal solution
- Uses a heap to manage partition structures

### Greedy Number Partitioning (GNP)

File: `src/algorithm_gnp.py`

A greedy algorithm that assigns numbers to the partition with the smallest current sum.

Numbers are processed in descending order, and a min-heap is used to efficiently identify the least-loaded partition.

**Characteristics:**
- Simple and efficient heuristic
- Supports existing partition sums
- Suitable for distributing remaining numbers
- Does not guarantee an optimal solution

### Linear Programming (LP)

File: `src/algorithm_lp.py`

An optimization-based approach using a Mixed-Integer Linear Programming (MILP) model.

Binary decision variables determine the assignment of each number to a partition. The objective minimizes the difference between the maximum and minimum partition sums.

The implementation uses **PuLP** and the **HiGHS** solver.

**Characteristics:**
- Mathematical optimization model
- Binary assignment variables
- Minimizes the range of partition sums
- Uses a one-second solver time limit
- May fail to produce a valid solution within the time limit

### Adaptive Orchestrator

File: `src/orchestrator.py`

The orchestrator combines the available algorithms and selects a partitioning strategy based on the **Coefficient of Variation (CV)** of the input dataset.

The coefficient is calculated as:

\[
CV = \frac{\sigma}{\mu}
\]

where:
- \(\sigma\) is the standard deviation
- \(\mu\) is the arithmetic mean

The default CV threshold is `0.6`.

**Algorithm selection process:**

1. Calculate the coefficient of variation of the input dataset.
2. If `CV <= 0.6`, apply the KK algorithm directly.
3. Otherwise, divide the dataset into two groups using the threshold:

   \[
   T = \mu + \sigma
   \]

4. Numbers greater than or equal to `T` are classified as large numbers.
5. Calculate the CV of the large-number group.
6. Apply KK or LP to the large-number group, depending on its CV.
7. If LP fails or produces an invalid result, fall back to KK.
8. Distribute the remaining smaller numbers using GNP.
9. Validate the final partitioning result.

The orchestrator is designed to combine the strengths of different methods without changing their underlying implementations.

## 3. Project Structure

```text
MultiwayNumberPartitioning/
├── docs/
├── examples/
│   └── format_guide.md
├── src/
│   ├── algorithm_gnp.py
│   ├── algorithm_kk.py
│   ├── algorithm_lp.py
│   ├── dataset_generator.py
│   ├── main.py
│   ├── orchestrator.py
│   └── testing.py
├── .gitignore
└── README.md
```

| File | Description |
|---|---|
| `algorithm_kk.py` | Karmarkar–Karp partitioning |
| `algorithm_gnp.py` | Greedy partitioning using a min-heap |
| `algorithm_lp.py` | MILP-based partitioning |
| `orchestrator.py` | Adaptive algorithm selection |
| `dataset_generator.py` | Random dataset generation |
| `testing.py` | Validation and performance evaluation |
| `main.py` | Command-line interface and benchmarking |

## 4. Requirements

- Python 3.10 or newer
- PuLP
- HiGHS (`highspy`)

Install the required packages:

```bash
python -m pip install pulp highspy
```

Alternatively, create a `requirements.txt` file containing:

```text
pulp
highspy
```

Then install the dependencies with:

```bash
python -m pip install -r requirements.txt
```

## 5. Usage

All commands should be executed from the project's root directory.

### Generate Test Datasets

```bash
python src/main.py --generate
```

This generates four dataset files inside the `examples/` directory:

| Dataset | Number of instances | Instance sizes |
|---|---:|---|
| `unit_tests_dataset` | 10 | 10 |
| `stress_tests_dataset` | 12 | 10, 100, 1,000, 10,000 |
| `unbalanced_dataset` | 10 | 100 |
| `difficult_datasets` | 3 | 1,000,000 |

The unbalanced datasets contain approximately 90% values from the lower range and 10% from the upper range.

### Run a Single Algorithm

Run Karmarkar–Karp:

```bash
python src/main.py --algorithm kk -k 4
```

Run Greedy Number Partitioning:

```bash
python src/main.py --algorithm gnp -k 4
```

Run Linear Programming:

```bash
python src/main.py --algorithm lp -k 4
```

Run the adaptive orchestrator:

```bash
python src/main.py --algorithm orchestrator -k 4
```

### Compare All Algorithms

```bash
python src/main.py --algorithm all -k 4
```

The program evaluates the algorithms using the same input datasets and displays a comparison of partition quality and execution time.

### Use a Custom Dataset

```bash
python src/main.py --algorithm orchestrator --dataset examples/unbalanced_dataset -k 8
```

The `--dataset` argument specifies the input file, while `-k` determines the number of partitions.

### Command-Line Arguments

| Argument | Description | Default |
|---|---|---|
| `--generate` | Generate predefined test datasets | Disabled |
| `--algorithm` | Select `kk`, `gnp`, `lp`, `orchestrator`, or `all` | `all` |
| `--dataset` | Path to the input dataset file | `examples/unit_tests_dataset` |
| `-k` | Number of partitions | `4` |

**Note:** The benchmarking interface skips standalone LP tests when any dataset instance contains more than 100 numbers. This is a benchmark safeguard, not a limitation of the LP implementation. The orchestrator can still invoke LP internally.

## 6. Dataset Format

Input datasets are stored in plain-text files.

The first line specifies the number of datasets. Each subsequent line contains one dataset represented by space-separated integers.

Example:

```text
3
10 20 30 40 50
5 15 25 35 45
100 200 300 400 500
```

In this example:
- The file contains 3 datasets.
- Each dataset contains 5 numbers.
- Each dataset is processed independently.

## 7. Performance Evaluation

File: `src/testing.py`

The testing module validates partitioning results and measures execution time and partition balance.

### Data Integrity

Every algorithm result is checked to ensure that all original values are preserved, including duplicates.

If the validation fails, testing stops and reports an error.

### Evaluation Metrics

**Maximum Standardized Difference**

\[
D_{\max}=\frac{\max(S_i)-\min(S_i)}{\sum_i S_i}
\]

Measures the difference between the largest and smallest partition sums relative to the total sum.

**Average Standardized Pairwise Difference**

\[
D_{\mathrm{avg}} =
\frac{1}{\binom{k}{2}}
\frac{\sum_{i<j}|S_i-S_j|}{\sum_i S_i}
\]

Measures the average difference between all pairs of partition sums, normalized by the total sum.

**Coefficient of Variation**

\[
CV=\frac{\operatorname{stdev}(S_1,\ldots,S_k)}
{\frac{1}{k}\sum_i S_i}
\]

Measures the relative variability of partition sums.

**Execution Time**

Measured using Python's `time.perf_counter()`.

For the balance metrics, lower values indicate more balanced partitions. A lower execution time indicates faster processing.

### Benchmark Results

The testing module calculates average metrics across the processed datasets and displays a summary report.

When comparing algorithms, the program identifies:
- The algorithm with the lowest average maximum standardized difference
- The algorithm with the lowest average execution time

## 8. Limitations

- The KK and GNP algorithms are heuristic methods and do not guarantee optimal partitions.
- LP can become computationally expensive as the dataset size and number of partitions increase.
- The LP solver has a one-second time limit and may not return a valid solution.
- The orchestrator uses fixed statistical thresholds rather than learned or automatically optimized parameters.
- Large datasets may require significant execution time and memory, particularly with the current KK implementation.
- The orchestrator requires non-negative input values.
- Benchmark results are printed to the terminal and are not automatically saved to files.

## 9. Project Objective

The primary objective of this project is to investigate whether an adaptive algorithm-selection strategy can provide a useful balance between partition quality and computational efficiency.

By comparing individual partitioning algorithms with a hybrid orchestrator, the project evaluates how statistical properties of input datasets can influence algorithm selection and overall performance.


## License

No license has been specified for this project.
