import random
import argparse

def generate_dataset(size, balance=1,lower_scope = (1, 100) , upper_scope = (2000, 20000)):
    dataset = []

    for _ in range(size):
        if random.random() < balance:
            dataset.append(random.randint(*lower_scope))      
        else:
            dataset.append(random.randint(*upper_scope)) 
        
    random.shuffle(dataset)
    return dataset

def export_datasets(filename, num_datasets, size_per_dataset, balanced=True):
    try:
        with open(filename, 'w') as f:
            f.write(f"{num_datasets}\n")
            
            for _ in range(num_datasets):
                dataset = generate_dataset(size_per_dataset, balanced)
                line = " ".join(map(str, dataset))
                f.write(f"{line}\n")
                
        typ_danych = "Zbalansowane" if balanced else "Niezbalansowane"
        print(f"[{typ_danych}] Pomyślnie zapisano {num_datasets} zestawów danych do pliku '{filename}'.")
    except Exception as e:
        print(f"Wystąpił błąd podczas zapisu: {e}")

if __name__ == "__main__":
    # --- PRZYKŁAD UŻYCIA ---
    
    # 1. Generujemy standardowe (zbalansowane) zestawy do pliku 'dane_zbalansowane.txt'
    export_datasets(
        filename="dane_zbalansowane.txt", 
        num_datasets=5, 
        size_per_dataset=25, 
        balanced=True
    )
    
    # 2. Generujemy trudniejsze (niezbalansowane) zestawy do pliku 'dane_trudne.txt'
    export_datasets(
        filename="dane_trudne.txt", 
        num_datasets=3, 
        size_per_dataset=30, 
        balanced=False
    )
