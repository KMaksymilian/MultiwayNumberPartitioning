import math
import time 
import statistics
from itertools import combinations
from pathlib import Path

def validate_partitions(original_dataset, partitions):
   
    flattened_partitions = [item for sublist in partitions for item in sublist]
    return sorted(original_dataset) == sorted(flattened_partitions)

def run_tests(filepath, algorithm_func, k=2):
   
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            
        if not lines:
            print("Plik jest pusty.")
            return

        num_datasets = int(lines[0])
        standardized_max_diff = []
        standardized_avg_diff = []
        standardized_std_diff = []

        for i in range(1, num_datasets + 1):
            if i >= len(lines):
                break 
            
            dataset = list(map(int, lines[i].split()))

            start_time = time.perf_counter()
            partitions = algorithm_func(dataset.copy(), k)
            end_time = time.perf_counter()

            print(f"Dataset {i}: Execution time: {end_time - start_time:.6f} seconds")

            if not validate_partitions(dataset, partitions):
                print(f"\n[Critical Error] Data integrity check failed for dataset {i}!")
                return
            
            sums = [sum(p) for p in partitions]
            max_diff = max(sums) - min(sums)
            pairwise_diffs = [abs(suma_a - suma_b) for suma_a, suma_b in combinations(sums, 2)]
            avg_diff = statistics.mean(sums) if sums else 0
            std_diff = statistics.stdev(pairwise_diffs) if pairwise_diffs else 0

            standardized_max_diff.append(max_diff / sum(sums) if sum(sums) != 0 else 0)
            standardized_avg_diff.append(avg_diff / sum(sums) if sum(sums) != 0 else 0)
            standardized_std_diff.append(std_diff / sum(sums) if sum(sums) != 0 else 0)

        n = len(standardized_max_diff)
        if n == 0:
            print("No datasets were processed. Exiting.")
            return

        avg_diff = statistics.mean(standardized_avg_diff)
        avg_max_diff = statistics.mean(standardized_max_diff)
        avg_std_diff = statistics.mean(standardized_std_diff)

        print(f"\n=== Test Report: {Path(filepath).name} ===")
        print(f"Algorithm: {algorithm_func.__name__} | Datasets: {n} | Number of Subsets (k): {k}")
        print("Validation of Subsets:\tPASSED (no values were added or removed)")
        print("-" * 50)
        print(f"Average Difference:\t{avg_diff:.2f}")
        print(f"Maximum Difference:\t{avg_max_diff:.2f}")
        print(f"Standard Deviation:\t{avg_std_diff:.2f}")
        print("================================================\n")
        
        return avg_diff, avg_max_diff, avg_std_diff

    except FileNotFoundError:
        print(f"Error: File not found '{filepath}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
