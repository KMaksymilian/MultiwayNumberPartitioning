import random
import argparse
from pathlib import Path

def generate_dataset(size, balance=1,lower_scope = (1, 100) , upper_scope = (2000, 20000)):
    dataset = []

    for _ in range(size):
        if random.random() < balance:
            dataset.append(random.randint(*lower_scope))      
        else:
            dataset.append(random.randint(*upper_scope)) 
        
    random.shuffle(dataset)
    return dataset

def export_datasets(filename, num_datasets = 10, datasets_sizes = [10], balanced=True, path = "examples"):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        
        full_path = Path(path) / filename
        with open(full_path, 'w') as f:
            f.write(f"{num_datasets}\n")
            
            for i in range(num_datasets):
                size = datasets_sizes[  i % len(datasets_sizes)]
                dataset = generate_dataset(size, balanced)
                line = " ".join(map(str, dataset))
                f.write(f"{line}\n")
                
        
        print(f"Successfully created dataset.")
    except Exception as e:
        print(f"Error encoutered: {e}")

if __name__ == "__main__":
    export_datasets("unit_tests_dataset")
    export_datasets("stress_tests_dataset", 12, [10,100,1000,10000])
    export_datasets("unbalanced_tests_dataset", 10, [100], balanced=False )
    export_datasets("hard_tests", 3, [10000], balanced=False)