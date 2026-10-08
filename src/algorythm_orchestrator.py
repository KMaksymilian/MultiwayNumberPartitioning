import statistics

def orchestrator_partitioning(dataset: list[int], k: int, sd_threshold: float = 15.0) -> list[list[int]]:

    if len(dataset) < 2:
        return [dataset] + [[] for _ in range(k - 1)]

    # 1. Obliczenie średniej i odchylenia standardowego dla całego wejścia
    mean_val = statistics.mean(dataset)
    std_dev = statistics.stdev(dataset)

    # 2. Sprawdzenie pierwszego warunku odchylenia
    if std_dev <= sd_threshold:
        # Odchylenie jest MAŁE -> od razu odpalamy k-means
        return kmeans_partitioning(dataset, k)
    
    else:
        # Odchylenie jest DUŻE -> dzielimy na koszyki
        basket1_small = []
        basket2_large = []
        
        # Definicja "dużej liczby" (np. liczby większe niż średnia zbioru)
        for num in dataset:
            if num >= mean_val:
                basket2_large.append(num)
            else:
                basket1_small.append(num)
                
        # Zabezpieczenie na wypadek, gdyby koszyk 2 miał za mało elementów do stdev
        if len(basket2_large) < 2:
            partitions = simplex_partitioning(basket2_large, k)
            return greedy_partitioning(basket1_small, partitions)

        # 3. Analiza drugiego koszyka (dużych liczb)
        mean_b2 = statistics.mean(basket2_large)
        std_dev_b2 = statistics.stdev(basket2_large)

        if std_dev_b2 <= sd_threshold:
            # Odchylenie w koszyku 2 jest MAŁE
            partitions = kmeans_partitioning(basket2_large, k)
        else:
            # Odchylenie w koszyku 2 jest DUŻE
            partitions = simplex_partitioning(basket2_large, k)

        # 4. Wracamy do pierwszego koszyka z małymi liczbami
        # Przekazujemy zainicjowane podzbiory do algorytmu zachłannego
        final_partitions = greedy_partitioning(basket1_small, partitions)
        
        return final_partitions