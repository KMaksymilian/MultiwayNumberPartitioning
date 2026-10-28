import math
import pulp
from pulp.constants import LpSolveStatus


def algorithm_lp(A: list[int], k: int, *, time_limit=1.0, metadata=None):
    """Partition numbers using linear programming to minimize sum differences."""
    if k < 1:
        raise ValueError("k must be greater than zero.")
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be finite and greater than zero.")
    if metadata is not None:
        metadata.update(lp_status="NotRun", lp_optimal=False)
    if any(number < 0 for number in A):
        raise ValueError("LP requires non-negative data.")
    if not A:
        return [[] for _ in range(k)]

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

    # Solve with a one-second time limit.
    solver = pulp.HiGHS(msg=False, timeLimit=time_limit, threads=1, random_seed=0)
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
