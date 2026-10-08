import time 
import statistics
from itertools import combinations
from pathlib import Path


def validate_partitions(original_dataset, partitions):
    flattened_partitions = [item for sublist in partitions for item in sublist]
    return sorted(original_dataset) == sorted(flattened_partitions)



def process_single_dataset(dataset, algorithm_func, k, index):
    start_time = time.perf_counter()
    partitions = algorithm_func(dataset.copy(), k)
    exec_time = time.perf_counter() - start_time

    if not validate_partitions(dataset, partitions):
        print(f"\n[Critical Error] Data integrity check failed for dataset {index}!")
        return None

    sums = [sum(p) for p in partitions]
    total_sum = sum(sums)
    ideal_sum = total_sum / k
    
    max_diff = max(sums) - min(sums)
    pairwise_diffs = [abs(a - b) for a, b in combinations(sums, 2)]
    avg_diff = statistics.mean(pairwise_diffs) if pairwise_diffs else 0
    std_of_sums = statistics.stdev(sums) if len(sums) > 1 else 0.0

    if total_sum == 0:
        return exec_time, 0, 0, 0

    std_max = max_diff / total_sum
    std_avg = avg_diff / total_sum
    std_cv = std_of_sums / ideal_sum if ideal_sum != 0 else 0

    print(f"Dataset {index}: Time: {exec_time:.6f}s | Max Diff: {max_diff} | Avg Diff: {avg_diff:.4f} | CV: {std_cv:.4f}")
    return exec_time, std_max, std_avg, std_cv

def print_final_report(filepath, algo_name, n, k, avg_diff, avg_max, avg_cv, avg_time):
    print(f"\n=== Test Report: {Path(filepath).name} ===")
    print(f"Algorithm: {algo_name} | Datasets: {n} | Number of Subsets (k): {k}")
    print("Validation of Subsets:\tPASSED (no values were added or removed)")
    print("-" * 55)
    print(f"Avg Standardized Pairwise Diff:\t{avg_diff:.4f}")
    print(f"Max Standardized Difference:\t{avg_max:.4f}")
    print(f"Coefficient of Variation (CV):\t{avg_cv:.4f}")
    print(f"Average Execution Time:         \t{avg_time:.6f} s")
    print("=======================================================\n")

def run_tests(filepath, algorithm_func, k=2):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            
        if not lines:
            print("File is empty.")
            return

        results = []
        for i in range(1, int(lines[0]) + 1):
            if i >= len(lines):
                break 
            
            dataset = list(map(int, lines[i].split()))
            metrics = process_single_dataset(dataset, algorithm_func, k, i)
            
            if metrics is None:
                return # Przerywamy w przypadku błędu integralności danych
            results.append(metrics)

        if not results:
            print("No datasets were processed. Exiting.")
            return

        # Wyciągamy średnie z zebranych wyników
        avg_time = statistics.mean([res[0] for res in results])
        avg_max_diff = statistics.mean([res[1] for res in results])
        avg_diff = statistics.mean([res[2] for res in results])
        avg_cv = statistics.mean([res[3] for res in results])

        print_final_report(filepath, algorithm_func.__name__, len(results), k, avg_diff, avg_max_diff, avg_cv, avg_time)
        return avg_diff, avg_max_diff, avg_cv, avg_time

    except Exception as e:
        print(f"An error occurred: {e}")
