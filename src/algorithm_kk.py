import heapq

class SmallPartition:
    """Store numbers and their total sum."""

    def __init__(self, initial):
        self.sum = 0 if initial is None else initial
        self.numbers = [] if initial is None else [initial]

    def add(self, other):
        self.sum += other.sum
        self.numbers.extend(other.numbers)


class BigPartition:
    """Manage and merge partitions while minimizing sum differences."""

    def __init__(self, number, k):
        self.delta = number
        self.partitions = [SmallPartition(None) for _ in range(k - 1)]
        self.partitions.append(SmallPartition(number))

    def __lt__(self, other):
        return self.delta > other.delta

    def sort(self):
        self.partitions.sort(key=lambda x: x.sum)

    def reverse(self):
        self.partitions.reverse()

    def calculate_delta(self):
        self.delta = self.partitions[-1].sum - self.partitions[0].sum

    def merge(self, other):
        other.reverse()
        for i in range(len(self.partitions)):
            self.partitions[i].add(other.partitions[i])
        self.sort()
        self.calculate_delta()


def find_biggest(big_partitions):
    """Return the indices of the two largest partitions."""
    return [
        i for i, partition in
        heapq.nlargest(2, enumerate(big_partitions), key=lambda x: x[1].delta)
    ]


def algorithm_kk(numbers, k):
    """Partition numbers using the Karmarkar-Karp algorithm."""
    heap = []

    for number in numbers:
        heapq.heappush(heap, BigPartition(number, k))

    while len(heap) > 1:
        largest1 = heapq.heappop(heap)
        largest2 = heapq.heappop(heap)
        largest1.merge(largest2)
        heapq.heappush(heap, largest1)

    return [partition.numbers for partition in heap[0].partitions]