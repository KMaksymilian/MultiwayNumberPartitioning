from typing import cast
import pulp


def algorithm_lp(A: list[int], k: int):
    """Partition numbers using linear programming to minimize sum differences."""
    n = len(A)
    rn = range(n)
    rk = range(k)

    prob = pulp.LpProblem("MultiwayNumberPartitioning", pulp.LpMinimize)

    # Binary assignment variables.
    vars = pulp.LpVariable.dicts(
        name="p",
        indices=(rk, rn),
        cat=pulp.LpBinary,
    )

    # Assign each number to exactly one partition.
    for i in rn:
        memberships = pulp.lpSum(vars[ik][i] for ik in rk)
        prob.addConstraint(memberships == 1)

    # Calculate partition sums.
    part_sums = [pulp.lpDot(A, [vars[ik][i] for i in rn]) for ik in rk]

    # Define minimum and maximum partition sums.
    max_sum = pulp.LpVariable("max_sum", lowBound=0)
    min_sum = pulp.LpVariable("min_sum", lowBound=0)

    for s in part_sums:
        prob += max_sum >= s
        prob += min_sum <= s

    # Minimize the difference between partition sums.
    prob += max_sum - min_sum

    # Solve with a one-second time limit.
    solver = pulp.HiGHS(msg=False, timeLimit=1)
    status = prob.solve(solver)

    if pulp.LpStatus[status] not in ("Optimal", "Not Solved"):
        raise RuntimeError(
            f"Solver has failed: "
            f"{pulp.LpStatus[status]}"
        )

    partitions = [[] for _ in range(k)]

    for ik in rk:
        for i in rn:
            val = pulp.value(vars[ik][i])
            if val is not None and val > 0.5:
                partitions[ik].append(A[i])

    if sorted(x for p in partitions for x in p) != sorted(A):
        raise RuntimeError("Solver returned an incomplete partition.")

    return partitions