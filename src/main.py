from algorythm_orchestrator import orchestrator_partitioning
from running_tests import run_tests


if __name__ == "__main__":
    run_tests(
        filepath="unit_tests_dataset.txt", 
        algorithm_func=orchestrator_partitioning, 
        k=3
    )