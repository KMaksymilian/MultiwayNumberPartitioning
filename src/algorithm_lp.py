import math
from collections import defaultdict, deque
import pulp
from pulp.constants import LpSolveStatus
from algorithm_gnp import algorithm_gnp
from algorithm_kk import algorithm_kk


def algorithm_lp(A: list[int], k: int, *, time_limit=1.0, metadata=None, pruning=False):
    """Partition numbers using linear programming to minimize sum differences."""
    if k < 1:
        raise ValueError("k must be greater than zero.")
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and greater than zero.")
    if metadata is not None:
        metadata.update(lp_status="NotRun", lp_optimal=False, pruning_enabled=pruning)
    if any(number < 0 for number in A):
        raise ValueError("LP requires non-negative data.")
    if not A:
        return [[] for _ in range(k)]

    if pruning:
        candidates = [algorithm_kk(A, k), algorithm_gnp(A, [0] * k)]
        initial = min(candidates, key=lambda groups: max(map(sum, groups)) - min(map(sum, groups)))
        # Use the same labeling convention for the MIP start and symmetry constraints.
        initial = sorted(initial, key=sum, reverse=True)
        initial_sums = list(map(sum, initial))
        upper_range = max(initial_sums) - min(initial_sums)
        total = sum(A)
        lower_sum = max(0, (total - (k - 1) * upper_range + k - 1) // k)
        upper_sum = (total + (k - 1) * upper_range) // k
        if metadata is not None:
            metadata.update(initial_range=upper_range, sum_lower_bound=lower_sum,
                            sum_upper_bound=upper_sum)

    n = len(A)
    rn = range(n)
    rk = range(k)

    prob = pulp.LpProblem("MultiwayNumberPartitioning", pulp.LpMinimize)

    # Binary assignment variables.
    assignments = {
        ik: {
            i: prob.add_variable(f"p_{ik}_{i}", cat=pulp.LpBinary)
            for i in rn
        }
        for ik in rk
    }

    # Assign each number to exactly one partition.
    for i in rn:
        memberships = pulp.lpSum(assignments[ik][i] for ik in rk)
        prob.addConstraint(memberships == 1)

    # Calculate partition sums.
    part_sums = [pulp.lpDot(A, [assignments[ik][i] for i in rn]) for ik in rk]

    # Define minimum and maximum partition sums.
    max_sum = prob.add_variable("max_sum", lowBound=0)
    min_sum = prob.add_variable("min_sum", lowBound=0)

    for s in part_sums:
        prob += max_sum >= s
        prob += min_sum <= s

    # Minimize the difference between partition sums.
    prob += max_sum - min_sum

    if pruning:
        prob += max_sum - min_sum <= upper_range, "incumbent_range"
        for j, part_sum in enumerate(part_sums):
            prob += part_sum >= lower_sum, f"sum_lower_{j}"
            prob += part_sum <= upper_sum, f"sum_upper_{j}"
        for j in range(k - 1):
            prob += part_sums[j] >= part_sums[j + 1], f"ordered_sums_{j}"

        # Map occurrences, rather than unique values, to preserve duplicates and zeros.
        destinations = defaultdict(deque)
        for j, group in enumerate(initial):
            for number in group:
                destinations[number].append(j)
        for i, number in enumerate(A):
            destination = destinations[number].popleft()
            for j in rk:
                assignments[j][i].setInitialValue(int(j == destination))
        max_sum.setInitialValue(initial_sums[0])
        min_sum.setInitialValue(initial_sums[-1])

    # Solve with a one-second time limit.
    solver = pulp.HiGHS(msg=False, timeLimit=time_limit, threads=1, random_seed=0,
                        warmStart=pruning)
    result = prob.solve(solver)
    if metadata is not None:
        metadata.update(
            lp_status=result.status.name,
            lp_optimal=result.status == LpSolveStatus.Optimal,
        )

    if not result.has_solution:
        raise RuntimeError(
            f"Solver returned no feasible solution: {result.status.name}"
        )

    partitions = [[] for _ in range(k)]

    for i in rn:
        values = [pulp.value(assignments[ik][i]) for ik in rk]
        if any(
            val is None or min(abs(val), abs(val - 1)) > 1e-5
            for val in values
        ):
            raise RuntimeError("Solver returned a non-integral assignment.")
        assigned = [ik for ik, val in enumerate(values) if val > 0.5]
        if len(assigned) != 1:
            raise RuntimeError("Solver returned an invalid assignment.")
        partitions[assigned[0]].append(A[i])

    if sorted(x for p in partitions for x in p) != sorted(A):
        raise RuntimeError("Solver returned an incomplete partition.")

    return partitions
