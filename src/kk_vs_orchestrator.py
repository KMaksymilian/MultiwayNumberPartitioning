"""KK vs orchestrator experiments.

Compared thresholds:
    0.6  - the default threshold of the orchestrator,
    4.26 - the minimax threshold from docs/cv_threshold.md.

Usage from the terminal (in src/):
    uv run python kk_vs_orchestrator.py --quick         # check that everything works (~1 min)
    uv run python kk_vs_orchestrator.py --seed 0        # full run (see FULL, about 16 min)
    uv run python kk_vs_orchestrator.py --report-only   # rebuild report.md from results.json

Usage from the Python console (in the project root):
    import sys; sys.path.insert(0, "src")
    import kk_vs_orchestrator as exp
    results = exp.run_experiments(seed=0, quick=True)   # check that everything works (~1 min)
    results = exp.run_experiments(seed=0)               # full run (see FULL, about 16 min)
    exp.regenerate_report()                             # rebuild report.md

Outputs (src/results/kk_vs_orchestrator[/quick]/): results.json, report.md.
"""
import json
import math
import platform
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


THRESHOLDS = (0.6, 4.26)
CV_BINS = (0.0, 0.6, 1.0, 2.0, 3.0, 4.26, math.inf)  # bins of the measured CV
OUT_DIR = Path(__file__).resolve().parent / "results" / "kk_vs_orchestrator"

FULL = {
    "distributions": ("lognormal", "gamma", "uniform"),
    "ns": (100, 1000),
    "ks": (3, 5),
    # 0.1 ... 0.5, then 0.6 ... 6.0 every 0.2 (values a distribution cannot reach are skipped).
    # The measured CV is usually lower than the target one, so the grid goes beyond 4.26.
    "cvs": tuple([round(0.1 * i, 1) for i in range(1, 6)]
                 + [round(0.6 + 0.2 * i, 1) for i in range(28)]),
    "num_datasets": 5,   # datasets per (distribution, n, k, CV)
    "mean": 10_000,
    "time_limit": 1.0,   # LP time limit in the hybrid branch [s]
}
QUICK = {
    "distributions": ("lognormal", "gamma", "uniform"),
    "ns": (50,),
    "ks": (3,),
    "cvs": (0.3, 1.0, 2.5, 4.6),
    "num_datasets": 2,
    "mean": 10_000,
    "time_limit": 1.0,
}


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def _hybrid_branch(time_limit):
    """Orchestrator forced into the hybrid branch (threshold 0); metadata in `.metadata`."""
    from orchestrator import orchestrator_partitioning

    def hybrid(dataset, k):
        hybrid.metadata = {}
        return orchestrator_partitioning(dataset, k, cv_threshold=0.0,
                                         time_limit=time_limit, metadata=hybrid.metadata)
    hybrid.metadata = {}
    return hybrid


def _num_large(dataset):
    """How many numbers the orchestrator sends to LP (numbers >= mean + std)."""
    limit = statistics.mean(dataset) + statistics.stdev(dataset)
    return sum(x >= limit for x in dataset)


def run_scenario(distribution, n, k, cvs, num_datasets, mean, time_limit, seed):
    """Solve datasets of one (distribution, n, k) by KK and by the hybrid branch.

    The random generator is seeded with (seed, distribution, n, k), so every
    scenario gets the same datasets regardless of the other settings.
    """
    # imported here, so that rebuilding the report does not need the LP solver
    from algorithm_kk import algorithm_kk
    from dataset_generator import dataset_cv, generate_with_target_cv
    from distributions import get_distribution
    from experiments import run_algorithm

    dist = get_distribution(distribution)
    rng = random.Random(f"{seed}-{dist.name}-{n}-{k}")
    hybrid = _hybrid_branch(time_limit)
    records = []

    for cv in cvs:
        if cv > dist.max_cv:
            continue
        for _ in range(num_datasets):
            dataset = generate_with_target_cv(n, cv, dist.name, mean, rng)
            kk = run_algorithm(algorithm_kk, dataset, k)
            hyb = run_algorithm(hybrid, dataset, k)
            records.append({
                "distribution": dist.name, "n": n, "k": k,
                "target_cv": cv,
                "measured_cv": dataset_cv(dataset),
                "num_large": _num_large(dataset),
                "num_ones": dataset.count(1),
                "kk_d": kk["max_diff"], "kk_rel": kk["std_max"], "kk_time": kk["time"],
                "hyb_d": hyb["max_diff"], "hyb_rel": hyb["std_max"], "hyb_time": hyb["time"],
                "hyb_strategy": hybrid.metadata.get("strategy", ""),
                "lp_status": hybrid.metadata.get("lp_status", ""),
                "fallback_reason": hybrid.metadata.get("fallback_reason", ""),
            })
    return records


def _environment():
    try:
        from importlib.metadata import version
        pulp_version = version("pulp")
        highspy_version = version("highspy")
    except Exception:  # noqa: BLE001 - only informative
        pulp_version = highspy_version = "?"
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "pulp": pulp_version,
        "highspy": highspy_version,
    }


def run_experiments(seed=0, quick=False, settings=None, out_dir=None):
    """Run all scenarios, save results and print the report.

    `settings` overrides FULL/QUICK (keys as in FULL). Returns the results dict.
    """
    settings = dict(settings or (QUICK if quick else FULL))
    out_dir = Path(out_dir) if out_dir else (OUT_DIR / "quick" if quick else OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [(d, n, k) for d in settings["distributions"]
                 for n in settings["ns"] for k in settings["ks"]]
    records = []
    start = time.perf_counter()
    for i, (distribution, n, k) in enumerate(scenarios, 1):
        t0 = time.perf_counter()
        part = run_scenario(distribution, n, k, settings["cvs"], settings["num_datasets"],
                            settings["mean"], settings["time_limit"], seed)
        records += part
        print(f"[{i}/{len(scenarios)}] {distribution}, n={n}, k={k}: {len(part)} zbiorów, "
              f"{time.perf_counter() - t0:.0f} s (łącznie {time.perf_counter() - start:.0f} s)")

    results = {
        "seed": seed,
        "quick": quick,
        "settings": {key: list(v) if isinstance(v, tuple) else v for key, v in settings.items()},
        "thresholds": list(THRESHOLDS),
        "date": datetime.now().isoformat(timespec="seconds"),
        "duration_s": time.perf_counter() - start,
        "environment": _environment(),
        "records": records,
    }
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)

    report = print_report(results)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"\nWyniki zapisane w: {out_dir}")
    return results


def regenerate_report(path=None):
    """Print the report again from saved results and overwrite report.md."""
    path = Path(path) if path else OUT_DIR / "results.json"
    results = load_results(path)
    (path.parent / "report.md").write_text(print_report(results), encoding="utf-8")
    return results


def load_results(path=None):
    """Load results saved by run_experiments (default: the full run)."""
    path = Path(path) if path else OUT_DIR / "results.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def orchestrator_result(record, threshold):
    """D, D/sum, time and branch of the orchestrator with `threshold` on this dataset."""
    if record["measured_cv"] <= threshold:
        return record["kk_d"], record["kk_rel"], record["kk_time"], "kk"
    return record["hyb_d"], record["hyb_rel"], record["hyb_time"], "hybrid"


def ratio(record):
    """q = (D_LP + 1) / (D_KK + 1), D_LP of the LP+GNP branch: q > 1 means KK is better."""
    return (record["hyb_d"] + 1) / (record["kk_d"] + 1)


def _median(values):
    return statistics.median(values) if values else None


def _quantile(values, q):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))]


def _fmt(value, spec=".2f"):
    if value is None:
        return "–"
    return format(value, spec)


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return lines


def _groups(records, keys):
    groups = {}
    for r in records:
        groups.setdefault(tuple(r[key] for key in keys), []).append(r)
    return groups


def _bin_label(lo, hi):
    return f"({lo:g}; {hi:g}]" if math.isfinite(hi) else f"> {lo:g}"


def _wins(records, d_a, d_b):
    """How many times a < b, a == b, a > b."""
    better = sum(r[d_a] < r[d_b] for r in records)
    ties = sum(r[d_a] == r[d_b] for r in records)
    return better, ties, len(records) - better - ties


def section_settings(results):
    s, env = results["settings"], results["environment"]
    return [
        "## 0. Ustawienia",
        "",
        f"- seed: {results['seed']}, data: {results['date']}, czas całego badania: "
        f"{results['duration_s'] / 60:.1f} min",
        f"- rozkłady: {', '.join(s['distributions'])}; n: {s['ns']}; k: {s['ks']}",
        f"- zadane CV: {s['cvs']}",
        f"- zbiorów na (rozkład, n, k, CV): {s['num_datasets']}; średnia: {s['mean']}; "
        f"limit czasu LP: {s['time_limit']} s",
        f"- liczba wszystkich zbiorów: {len(results['records'])}",
        f"- progi orkiestratora: {results['thresholds']}",
        f"- środowisko: Python {env['python']}, PuLP {env['pulp']}, highspy {env['highspy']}, "
        f"{env['platform']}, {env['processor']}",
    ]


def section_generator(records, thresholds):
    """Measured vs target CV and the share of datasets above each threshold."""
    lines = ["## 1. Zmierzone CV a zadane CV", ""]
    rows = []
    for (dist, n), group in sorted(_groups(records, ("distribution", "n")).items()):
        cvs = [r["measured_cv"] for r in group]
        above = [f"{sum(cv > t for cv in cvs) / len(cvs):.0%}" for t in thresholds]
        ones = statistics.mean(r["num_ones"] / r["n"] for r in group)
        rows.append([dist, n, len(group), _fmt(min(cvs)), _fmt(statistics.median(cvs)),
                     _fmt(max(cvs)), *above, f"{ones:.1%}"])
    lines += _table(["Rozkład", "n", "zbiory", "min CV", "mediana CV", "max CV",
                     *[f"CV > {t}" for t in thresholds], "udział jedynek"], rows)

    lines += ["", "Średnie zmierzone CV dla wybranych zadanych CV:", ""]
    targets = [cv for cv in (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)
               if any(r["target_cv"] == cv for r in records)]
    rows = []
    for (dist, n), group in sorted(_groups(records, ("distribution", "n")).items()):
        row = [dist, n]
        for cv in targets:
            vals = [r["measured_cv"] for r in group if r["target_cv"] == cv]
            row.append(_fmt(statistics.mean(vals)) if vals else "–")
        rows.append(row)
    lines += _table(["Rozkład", "n", *[f"zadane {cv:g}" for cv in targets]], rows)
    return lines


def section_orchestrator(records, thresholds):
    """Main table: orchestrator with each threshold vs KK."""
    lines = ["## 2. Orkiestrator a KK (dla każdego progu)", ""]
    rows = []
    for t in thresholds:
        for (dist, n, k), group in sorted(_groups(records, ("distribution", "n", "k")).items()):
            orch = [orchestrator_result(r, t) for r in group]
            switched = [r for r, o in zip(group, orch) if o[3] == "hybrid"]
            better = sum(o[0] < r["kk_d"] for r, o in zip(group, orch))
            ties = sum(o[0] == r["kk_d"] for r, o in zip(group, orch))
            rows.append([
                t, dist, n, k, len(group), len(switched), better, ties,
                len(group) - better - ties,
                _fmt(statistics.mean(r["kk_rel"] for r in group), ".2e"),
                _fmt(statistics.mean(o[1] for o in orch), ".2e"),
                _fmt(_median([ratio(r) for r in switched]), ".1f"),
                _fmt(1000 * _median([r["kk_time"] for r in group])),
                _fmt(1000 * _median([o[2] for o in orch])),
            ])
    lines += _table(["Próg", "Rozkład", "n", "k", "zbiory", "CV > próg (LP+GNP)",
                     "D_O < D_KK", "D_O = D_KK", "D_O > D_KK", "śr. D/Σ KK",
                     "śr. D/Σ orkiestrator", "mediana q na zbiorach z CV > próg",
                     "mediana czasu KK [ms]", "mediana czasu orkiestratora [ms]"], rows)
    return lines


def section_bins(records):
    """Hybrid branch vs KK in bins of the measured CV (independent of the threshold)."""
    lines = ["## 3. LP+GNP a KK w przedziałach zmierzonego CV", "",
             "Wynik niezależny od progu: na każdym zbiorze porównujemy obie gałęzie.", ""]
    rows = []
    for (dist, n), group in sorted(_groups(records, ("distribution", "n")).items()):
        for lo, hi in zip(CV_BINS, CV_BINS[1:]):
            part = [r for r in group if lo < r["measured_cv"] <= hi]
            if not part:
                continue
            better, ties, worse = _wins(part, "hyb_d", "kk_d")
            ratios = [ratio(r) for r in part]
            rows.append([dist, n, _bin_label(lo, hi), len(part), better, ties, worse,
                         _fmt(_median([r["kk_d"] for r in part]), ".0f"),
                         _fmt(_median([r["hyb_d"] for r in part]), ".0f"),
                         _fmt(_median(ratios), ".1f"), _fmt(min(ratios), ".2f"),
                         _fmt(max(ratios), ".0f"),
                         _fmt(statistics.mean(r["num_large"] for r in part), ".1f")])
    lines += _table(["Rozkład", "n", "CV", "zbiory", "D_LP < D_KK", "D_LP = D_KK",
                     "D_LP > D_KK", "mediana D_KK", "mediana D_LP",
                     "mediana q", "min", "max", "śr. liczba dużych liczb"], rows)
    return lines


def section_k(records):
    """Is the picture different for k = 3 and k = 5?"""
    lines = ["## 4. LP+GNP a KK w zależności od k", ""]
    rows = []
    for (dist, k), group in sorted(_groups(records, ("distribution", "k")).items()):
        better, ties, worse = _wins(group, "hyb_d", "kk_d")
        rows.append([dist, k, len(group), better, ties, worse,
                     _fmt(_median([ratio(r) for r in group]), ".1f"),
                     _fmt(statistics.mean(r["kk_rel"] for r in group), ".2e"),
                     _fmt(statistics.mean(r["hyb_rel"] for r in group), ".2e")])
    lines += _table(["Rozkład", "k", "zbiory", "D_LP < D_KK", "D_LP = D_KK", "D_LP > D_KK",
                     "mediana q", "śr. D/Σ KK", "śr. D/Σ LP+GNP"], rows)
    return lines


def section_time(records):
    # medians and p95 only: robust to single outliers (e.g. the computer going to sleep)
    lines = ["## 5. Czas działania [ms]", ""]
    rows = []
    for (n, k), group in sorted(_groups(records, ("n", "k")).items()):
        kk = [1000 * r["kk_time"] for r in group]
        hyb = [1000 * r["hyb_time"] for r in group]
        rows.append([n, k, len(group), _fmt(_median(kk)), _fmt(_quantile(kk, 0.95)),
                     _fmt(_median(hyb)), _fmt(_quantile(hyb, 0.95))])
    lines += _table(["n", "k", "zbiory", "KK mediana", "KK p95",
                     "LP+GNP mediana", "LP+GNP p95"], rows)
    return lines


def section_lp(records):
    lines = ["## 6. Status LP w ścieżce LP+GNP", ""]
    rows = []
    for (n, k), group in sorted(_groups(records, ("n", "k")).items()):
        statuses = {}
        for r in group:
            key = f"{r['hyb_strategy']} / {r['lp_status']}"
            statuses[key] = statuses.get(key, 0) + 1
        for key, count in sorted(statuses.items()):
            rows.append([n, k, key, count])
    lines += _table(["n", "k", "strategia / status LP", "zbiory"], rows)
    reasons = sorted({r["fallback_reason"] for r in records if r["fallback_reason"]})
    if reasons:
        lines += ["", "Przyczyny przejścia do KK (fallback):", ""]
        lines += [f"- {reason}" for reason in reasons]
    return lines


def section_best_cases(records, top=10):
    """Datasets where the hybrid branch beats KK by the largest factor."""
    lines = ["## 7. Zbiory, na których D_LP < D_KK", ""]
    wins = sorted((r for r in records if r["hyb_d"] < r["kk_d"]), key=ratio)
    lines.append(f"Liczba takich zbiorów: {len(wins)} z {len(records)}.")
    if wins:
        lines.append("")
        lines += _table(["Rozkład", "n", "k", "zmierzone CV", "D_KK", "D_LP",
                         "q", "liczba dużych liczb"],
                        [[r["distribution"], r["n"], r["k"], _fmt(r["measured_cv"]), r["kk_d"],
                          r["hyb_d"], _fmt(ratio(r), ".3f"), r["num_large"]]
                         for r in wins[:top]])
    return lines


def section_summary(records, thresholds):
    better, ties, worse = _wins(records, "hyb_d", "kk_d")
    lines = ["## 8. Podsumowanie", "",
             f"- LP+GNP a KK na wszystkich {len(records)} zbiorach: D_LP < D_KK {better}, "
             f"D_LP = D_KK {ties}, D_LP > D_KK {worse}",
             f"- mediana q: {_fmt(_median([ratio(r) for r in records]), '.1f')}"]
    for t in thresholds:
        orch = [orchestrator_result(r, t) for r in records]
        switched = sum(o[3] == "hybrid" for o in orch)
        o_better = sum(o[0] < r["kk_d"] for r, o in zip(records, orch))
        o_worse = sum(o[0] > r["kk_d"] for r, o in zip(records, orch))
        lines.append(f"- próg {t}: LP+GNP na {switched} zbiorach "
                     f"({switched / len(records):.0%}); D_O < D_KK na {o_better}, "
                     f"D_O > D_KK na {o_worse}; śr. D/Σ: KK "
                     f"{statistics.mean(r['kk_rel'] for r in records):.2e}, orkiestrator "
                     f"{statistics.mean(o[1] for o in orch):.2e}")
    return lines


def print_report(results):
    """Print all tables for the report; return them as Markdown text."""
    records, thresholds = results["records"], results["thresholds"]
    lines = ["# KK a orkiestrator: wyniki", ""]
    for section in (section_settings(results), section_generator(records, thresholds),
                    section_orchestrator(records, thresholds), section_bins(records),
                    section_k(records), section_time(records), section_lp(records),
                    section_best_cases(records), section_summary(records, thresholds)):
        lines += section + [""]
    text = "\n".join(lines)
    print(text)
    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KK vs orchestrator experiments")
    parser.add_argument("--quick", action="store_true", help="small settings, about 1 min")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--report-only", action="store_true",
                        help="do not compute, rebuild report.md from results.json")
    args = parser.parse_args()
    if args.report_only:
        regenerate_report(OUT_DIR / "quick" / "results.json" if args.quick else None)
    else:
        run_experiments(seed=args.seed, quick=args.quick)


if __name__ == "__main__":
    main()
