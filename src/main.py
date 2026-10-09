from typing import cast

import pulp
solver = pulp.HiGHS(msg=False)

def main(A: list[int], k: int):
	n = len(A)
	rn = range(n)
	rk = range(k)

	prob = pulp.LpProblem("MultiwayNumberPartitioning", pulp.LpMinimize)
	vars = prob.add_variable_dicts(
		name="p",
		indices=(rk, rn),
		lowBound=0,
		upBound=1,
		cat="Continuous"
	)

	# Dany element powinien należeć do dokładnie jednej partycji.
	for i in rn:
		memberships = pulp.lpSum(vars[ik][i] for ik in rk)
		prob.addConstraint(memberships == 1)
	
	# Suma elementów per partycja.
	part_sums = [ pulp.lpDot(A, [vars[ik][i] for i in rn]) for ik in rk ]

	# Dla każdej pary sum różnica powinna być ograniczona pewną zmienną pomocniczą...
	abs_vals: list[pulp.LpVariable] = []
	for (ik, jk) in pulp.combination(rk, 2):
		abs_val = prob.add_variable(name=f"abs_{ik}_{jk}")
		abs_vals.append(abs_val)

		diff = part_sums[ik] - part_sums[jk]
		prob.addConstraint(diff <= +abs_val)
		prob.addConstraint(diff >= -abs_val)
	
	# ...a suma tych zmiennych ograniczających powinna być minimalizowana.
	prob.setObjective(pulp.lpSum(abs_vals))

	result = prob.solve(solver)
	
	# Teraz drukowanie:
	print(result)
	print()

	for ik in rk:
		for i in rn:
			v = cast(pulp.LpVariable, vars[ik][i])
			print(f"{v.name} = {v.value()}")
		print()
	
	print("Powinno zostać zredukowane do zera:")
	for abs_val in abs_vals:
		print(f"{abs_val.name} = {abs_val.value()}")

if __name__ == "__main__":
	main([12, 8, 3, 4, 8, 5, 7, 1, 2, 11], 3)
