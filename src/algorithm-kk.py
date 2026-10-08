import heapq

class SmallPartition:
    def __init__(self, initial):
        if initial is None:
            self.sum = 0
            self.numbers = []
        else:
            self.sum = initial
            self.numbers = [initial]

    def add(self, other):
        self.sum += other.sum
        self.numbers.extend(other.numbers)


class BigPartition:
    def __init__(self, number, k):
        self.delta = number
        self.partitions = []
        for _ in range(k - 1):
            self.partitions.append(SmallPartition(None))
        self.partitions.append(SmallPartition(number))

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
    return [i for i, partition in heapq.nlargest(2, enumerate(big_partitions), key=lambda x: x[1].delta)]
    

def algorithm_kk(numbers, k):
    big_partitions = []

    for number in numbers:
        big_partitions.append(BigPartition(number, k))

    while len(big_partitions) != 1:
        indexes  = find_biggest(big_partitions)
        idx_1 = indexes [0]
        idx_2 = indexes [1]

        big_partitions[idx_1].merge(big_partitions[idx_2])
        big_partitions.pop(idx_2)

    buckets = []
    for small_partition in big_partitions[0].partitions:
        buckets.append(small_partition.numbers)

    return buckets