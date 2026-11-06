"""Choosing the CV threshold of the orchestrator.

The threshold only selects a branch: KK when CV <= threshold, LP+GNP otherwise.
So both branches are run once on every dataset and the result of the
orchestrator for any threshold is read from these records without rerunning
the algorithms.
"""
import bisect
import random
import statistics

from algorithm_kk import algorithm_kk
from dataset_generator import dataset_cv, generate_with_target_cv
from distributions import get_distribution
from experiments import _validate_settings, run_algorithm, run_for_distributions
from orchestrator import orchestrator_partitioning

BASELINE_THRESHOLD = 0.6


def _lp_gnp_branch(time_limit):
    """Return the orchestrator forced into the LP+GNP branch."""
    def lp_gnp(dataset, k):
        # Every dataset with CV > 0 takes the LP+GNP branch.
        return orchestrator_partitioning(dataset, k, cv_threshold=0.0,
                                         time_limit=time_limit)
    return lp_gnp


def collect_branch_results(cvs=None, mean=10_000, n=100, k=4, num_datasets=10,
                           distribution="lognormal", seed=None, time_limit=1.0):
    """Run both orchestrator branches on datasets with many target CV values.
    CV values that the distribution cannot reach are skipped.

    Returns a list of records, one per dataset, with its measured CV and the
    D, D / sum and running time of both branches (prefix `kk_` and `lp_`).
    """
    _validate_settings(mean, n, k, num_datasets)
    dist = get_distribution(distribution)
    if cvs is None:
        cvs = [round(0.1 * i, 1) for i in range(1, 31)]  # 0.1, 0.2, ..., 3.0

    rng = random.Random(seed)
    lp_gnp = _lp_gnp_branch(time_limit)
    records = []

    for cv in cvs:
        if cv > dist.max_cv:
            continue

        for _ in range(num_datasets):
            dataset = generate_with_target_cv(n, cv, dist.name, mean, rng)
            kk = run_algorithm(algorithm_kk, dataset, k)
            lp = run_algorithm(lp_gnp, dataset, k)
            records.append({
                "distribution": dist.name,
                "n": n,
                "k": k,
                "target_cv": cv,
                "measured_cv": dataset_cv(dataset),
                "kk_d": kk["max_diff"],
                "lp_d": lp["max_diff"],
                # D / total sum, comparable between datasets of different scale
                "kk_std_max": kk["std_max"],
                "lp_std_max": lp["std_max"],
                "kk_time": kk["time"],
                "lp_time": lp["time"],
            })

    print(f"Branch results done: {len(records)} datasets ({dist.name}, k={k})")
    return records


def _costs(records, metric, time_weight):
    """Return (CV, KK cost, LP+GNP cost) per record, sorted by CV."""
    return sorted(
        (r["measured_cv"],
         r[f"kk_{metric}"] + time_weight * r["kk_time"],
         r[f"lp_{metric}"] + time_weight * r["lp_time"])
        for r in records
    )


def candidate_thresholds(records):
    """Return thresholds that cover every distinct split of the records by CV:
    0 (always LP+GNP), midpoints between consecutive CVs and the largest CV
    (always KK).
    """
    cvs = sorted({r["measured_cv"] for r in records})
    if not cvs:
        raise ValueError("records cannot be empty.")
    midpoints = [(a + b) / 2 for a, b in zip(cvs, cvs[1:])]
    return [0.0] + midpoints + [cvs[-1]]


def regret_curve(records, thresholds, metric="std_max", time_weight=0.0):
    """Return the mean regret of the orchestrator for every threshold.

    cost   = metric + time_weight * time ("std_max" is D / sum, "d" is D)
    regret = cost of the chosen branch - cost of the better branch
    """
    if not records:
        raise ValueError("records cannot be empty.")
    costs = _costs(records, metric, time_weight)
    cvs = [cv for cv, _, _ in costs]

    # prefix_kk[i] / prefix_lp[i] = summed cost of the i records with the lowest CV
    prefix_kk, prefix_lp = [0.0], [0.0]
    for _, kk, lp in costs:
        prefix_kk.append(prefix_kk[-1] + kk)
        prefix_lp.append(prefix_lp[-1] + lp)
    oracle = sum(min(kk, lp) for _, kk, lp in costs)

    curve = []
    for t in thresholds:
        i = bisect.bisect_right(cvs, t)  # records with CV <= t use KK
        total = prefix_kk[i] + prefix_lp[-1] - prefix_lp[i]
        # clamp rounding noise of the prefix sums, regret is never negative
        curve.append(max(0.0, total - oracle) / len(costs))
    return curve


def _plateau_middle(thresholds, values, rel_tol=1e-9):
    """Return the middle threshold among the ones with the minimal value."""
    best = min(values)
    tol = rel_tol * max(abs(best), 1e-300)
    plateau = [t for t, v in zip(thresholds, values) if v <= best + tol]
    return plateau[len(plateau) // 2]


def best_threshold(records, thresholds=None, metric="std_max", time_weight=0.0):
    """Return (threshold, mean regret) minimising the mean regret.
    Ties are broken by taking the middle of the minimal plateau.
    """
    if thresholds is None:
        thresholds = candidate_thresholds(records)
    curve = regret_curve(records, thresholds, metric, time_weight)
    t = _plateau_middle(thresholds, curve)
    return t, curve[thresholds.index(t)]


def cross_validate_threshold(records, folds=5, metric="std_max", time_weight=0.0,
                             baseline=BASELINE_THRESHOLD, seed=None):
    """Tune the threshold on k-1 folds and measure its regret on the held-out fold.

    Returns a dict with per-fold results and their means; test regret of the
    baseline threshold, always-KK and always-LP+GNP is reported for comparison.
    """
    if not 2 <= folds <= len(records):
        raise ValueError("folds must be between 2 and the number of records.")
    order = list(range(len(records)))
    random.Random(seed).shuffle(order)

    fold_results = []
    for f in range(folds):
        test_idx = set(order[f::folds])
        train = [r for i, r in enumerate(records) if i not in test_idx]
        test = [records[i] for i in test_idx]

        t, train_regret = best_threshold(train, metric=metric, time_weight=time_weight)
        test_tuned, test_baseline, test_kk, test_lp = regret_curve(
            test, [t, baseline, float("inf"), float("-inf")], metric, time_weight)
        fold_results.append({
            "threshold": t,
            "train_regret": train_regret,
            "test_regret": test_tuned,
            "baseline_regret": test_baseline,
            "always_kk_regret": test_kk,
            "always_lp_regret": test_lp,
        })

    summary = {key: statistics.mean(fr[key] for fr in fold_results)
               for key in fold_results[0]}
    summary["threshold_std"] = statistics.pstdev(fr["threshold"] for fr in fold_results)
    return {"folds": fold_results, "mean": summary}


def bootstrap_threshold(records, num_samples=200, metric="std_max", time_weight=0.0,
                        confidence=0.95, seed=None):
    """Resample the records with replacement to measure the uncertainty of the
    best threshold and of the whole regret curve.

    Returns the thresholds, the regret curve on all records, its confidence band
    (`curve_low`, `curve_high`) and the confidence interval of the best threshold.
    """
    rng = random.Random(seed)
    thresholds = candidate_thresholds(records)
    curves, best = [], []
    for _ in range(num_samples):
        sample = rng.choices(records, k=len(records))
        curve = regret_curve(sample, thresholds, metric, time_weight)
        curves.append(curve)
        best.append(_plateau_middle(thresholds, curve))

    alpha = (1 - confidence) / 2

    def quantile(values, q):
        values = sorted(values)
        return values[min(int(q * len(values)), len(values) - 1)]

    columns = list(zip(*curves))
    return {
        "thresholds": thresholds,
        "curve": regret_curve(records, thresholds, metric, time_weight),
        "curve_low": [quantile(c, alpha) for c in columns],
        "curve_high": [quantile(c, 1 - alpha) for c in columns],
        "best_samples": best,
        "best_low": quantile(best, alpha),
        "best_median": statistics.median(best),
        "best_high": quantile(best, 1 - alpha),
    }


def minimax_threshold(scenarios, metric="std_max", time_weight=0.0):
    """Choose one threshold for several scenarios (e.g. distributions or k values).

    `scenarios` is a dict {name: records}. Returns the threshold minimising the
    worst mean regret over the scenarios and the regret of every scenario there.
    """
    pooled = [r for records in scenarios.values() for r in records]
    thresholds = candidate_thresholds(pooled)
    curves = {name: regret_curve(records, thresholds, metric, time_weight)
              for name, records in scenarios.items()}
    worst = [max(values) for values in zip(*curves.values())]

    t = _plateau_middle(thresholds, worst)
    i = thresholds.index(t)
    return {
        "threshold": t,
        "worst_regret": worst[i],
        "regrets": {name: curve[i] for name, curve in curves.items()},
    }


def run_threshold_study(distributions=None, ks=(4,), folds=5, num_bootstrap=200,
                        metric="std_max", time_weight=0.0, seed=None, **collect_kwargs):
    """Collect branch results for every (distribution, k) scenario and choose
    the threshold per scenario, for all scenarios pooled and by minimax.

    `collect_kwargs` are passed to `collect_branch_results` (cvs, mean, n, ...).
    """
    scenarios = {}
    for k in ks:
        per_distribution = run_for_distributions(
            collect_branch_results, distributions, k=k, seed=seed, **collect_kwargs)
        for name, records in per_distribution.items():
            scenarios[f"{name}, k={k}"] = records

    def analyse(records):
        return {
            "best": best_threshold(records, metric=metric, time_weight=time_weight),
            "cv": cross_validate_threshold(records, folds, metric, time_weight, seed=seed),
            "bootstrap": bootstrap_threshold(records, num_bootstrap, metric, time_weight,
                                             seed=seed),
        }

    pooled = [r for records in scenarios.values() for r in records]
    return {
        "metric": metric,
        "time_weight": time_weight,
        "scenarios": {name: analyse(records) for name, records in scenarios.items()},
        "pooled": analyse(pooled),
        "minimax": minimax_threshold(scenarios, metric, time_weight),
        "records": scenarios,
    }


def print_threshold_study(study):
    """Print the chosen thresholds and their held-out regret."""
    print(f"\n=== CV threshold study (cost = {study['metric']}"
          f" + {study['time_weight']} * time) ===")
    print(f"{'Scenario':24}{'t*':>8}{'95% CI':>16}{'test regret':>14}"
          f"{f't={BASELINE_THRESHOLD}':>12}{'all KK':>12}{'all LP':>12}")

    rows = list(study["scenarios"].items()) + [("pooled", study["pooled"])]
    for name, result in rows:
        boot, mean = result["bootstrap"], result["cv"]["mean"]
        ci = f"[{boot['best_low']:.2f}, {boot['best_high']:.2f}]"
        print(f"{name:24}{result['best'][0]:>8.2f}{ci:>16}{mean['test_regret']:>14.2e}"
              f"{mean['baseline_regret']:>12.2e}{mean['always_kk_regret']:>12.2e}"
              f"{mean['always_lp_regret']:>12.2e}")

    minimax = study["minimax"]
    print("-" * 98)
    print(f"Minimax threshold:\t{minimax['threshold']:.2f} "
          f"(worst mean regret {minimax['worst_regret']:.2e})")


if __name__ == "__main__":
    print_threshold_study(run_threshold_study(seed=0))
