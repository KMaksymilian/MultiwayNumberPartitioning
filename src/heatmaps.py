"""Orchestrator vs KK on a grid of mean and standard deviation of the data.

For every distribution and every cell (mean, std) of the grid, `repeats`
datasets with CV = std / mean are generated. Each dataset is partitioned once by
KK and once by the LP+GNP branch (the orchestrator with threshold 0). The
threshold only decides which branch is used, so the result of the orchestrator
with any threshold tau is known without running it again:
    D_O = D_KK      when the measured CV of the dataset is <= tau,
    D_O = D_LP+GNP  otherwise.
For every tau in TAUS a heatmap shows, per cell, the median of
q = (D_O + 1) / (D_KK + 1)   (q = 1: the same result as KK).

Every (distribution, n, k, mean, std, repetition) has its own seed derived from
`seed`. Each run happens in a worker process and is stopped after
scaling.HARD_TIMEOUT seconds; such a run is recorded as an error.

Usage from the terminal (in the project root):
    .venv\\Scripts\\python src\\heatmaps.py --quick               # check (~1 min)
    .venv\\Scripts\\python src\\heatmaps.py --seed 0 --plots      # full run
    .venv\\Scripts\\python src\\heatmaps.py --report-only --plots # report.md + figures

Outputs (src/results/heatmaps/n<n>_k<k>[/quick]/): results.json, report.md
(and PNG heatmaps with --plots, which needs matplotlib).
"""
import json
import math
import random
import statistics
import time
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "results" / "heatmaps"
TAUS = (0.0, 0.6, 4.26)  # 0: LP+GNP on every dataset
MIN_RUNS = 3             # a cell is reported only when at least this many datasets are usable
BRANCHES = ("KK", "LP+GNP")

FULL = {"distributions": ("lognormal", "gamma", "uniform"),
        "means": tuple(range(1000, 10_001, 1000)),
        "stds": tuple(range(1000, 15_001, 1500)),
        "repeats": 5}
QUICK = {"distributions": ("lognormal", "uniform"),
         "means": (1000, 5000, 10_000),
         "stds": (1000, 7000, 13_000),
         "repeats": 3}


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def run_cell(runner, distribution, mean, std, n, k, repeats, seed):
    """Both branches on `repeats` datasets of one grid cell (None if CV is unreachable)."""
    from dataset_generator import dataset_cv, generate_with_target_cv
    from distributions import get_distribution
    target_cv = std / mean
    if target_cv > get_distribution(distribution).max_cv:
        return None
    records = []
    for rep in range(repeats):
        rng = random.Random(f"{seed}-{distribution}-{n}-{k}-{mean}-{std}-{rep}")
        dataset = generate_with_target_cv(n, target_cv, distribution, mean, rng)
        record = {"distribution": distribution, "mean": mean, "std": std,
                  "target_cv": target_cv, "rep": rep, "cv": dataset_cv(dataset)}
        for name in BRANCHES:
            record[name] = runner.run(name, dataset, k)
        records.append(record)
    return records


def output_dir(n, k, quick):
    out = OUT_DIR / f"n{n}_k{k}"
    return out / "quick" if quick else out


def run_experiment(seed=0, n=100, k=3, quick=False, settings=None, plots=False):
    """Run the grid for every distribution, save results.json and report.md."""
    from scaling import Runner, TIME_LIMIT, HARD_TIMEOUT, _environment
    settings = settings or (QUICK if quick else FULL)
    out_dir = output_dir(n, k, quick)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    records = []

    cells = [(d, m, s) for d in settings["distributions"]
             for s in settings["stds"] for m in settings["means"]]
    runner = Runner()
    try:
        for i, (distribution, mean, std) in enumerate(cells, 1):
            t0 = time.perf_counter()
            cell = run_cell(runner, distribution, mean, std, n, k, settings["repeats"], seed)
            records += cell or []
            note = "CV nieosiągalne" if cell is None else f"{time.perf_counter() - t0:.0f} s"
            print(f"[{i}/{len(cells)}] {distribution}: średnia={mean}, odchylenie={std}: {note} "
                  f"(łącznie {time.perf_counter() - start:.0f} s)", flush=True)
    finally:
        runner.close()

    results = {
        "seed": seed, "quick": quick, "n": n, "k": k,
        "settings": json.loads(json.dumps(settings)),
        "taus": list(TAUS),
        "time_limit": TIME_LIMIT,
        "hard_timeout": HARD_TIMEOUT,
        "date": datetime.now().isoformat(timespec="seconds"),
        "duration_s": time.perf_counter() - start,
        "environment": _environment(),
        "records": records,
    }
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    (out_dir / "report.md").write_text(print_report(results), encoding="utf-8")
    if plots:
        save_figures(results, out_dir)
    print(f"\nWyniki zapisane w: {out_dir}")
    return results


def load_results(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def regenerate_report(path, plots=False):
    """Rebuild report.md (and the figures) from saved results without computing."""
    path = Path(path)
    results = load_results(path)
    (path.parent / "report.md").write_text(print_report(results), encoding="utf-8")
    if plots:
        save_figures(results, path.parent)
    return results


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def usable(record):
    """Both branches finished without an error."""
    return all(record[name]["status"] == "ok" for name in BRANCHES)


def orchestrator_d(record, tau):
    """D of the orchestrator with threshold tau (KK when CV <= tau)."""
    return record["KK"]["d"] if record["cv"] <= tau else record["LP+GNP"]["d"]


def ratio(record, tau):
    """q = (D_O + 1) / (D_KK + 1)."""
    return (orchestrator_d(record, tau) + 1) / (record["KK"]["d"] + 1)


def cell_values(results, distribution, tau):
    """{(mean, std): median q} over cells with at least MIN_RUNS usable datasets."""
    cells = {}
    for r in results["records"]:
        if r["distribution"] == distribution and usable(r):
            cells.setdefault((r["mean"], r["std"]), []).append(ratio(r, tau))
    return {cell: statistics.median(qs) for cell, qs in cells.items() if len(qs) >= MIN_RUNS}


def _fmt(value, spec):
    return format(value, spec).replace(".", ",")


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return lines + ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]


def _grid_table(results, values, spec):
    s = results["settings"]
    rows = [[std] + [_fmt(values[(m, std)], spec) if (m, std) in values else "–"
                     for m in s["means"]] for std in s["stds"]]
    return _table(["odchylenie \\ średnia", *map(str, s["means"])], rows)


def print_report(results):
    s, env = results["settings"], results["environment"]
    records = results["records"]
    lines = ["# Orkiestrator a KK na siatce średniej i odchylenia standardowego", "",
             "## 0. Ustawienia", "",
             f"- seed: {results['seed']}, data: {results['date']}, "
             f"czas badania: {results['duration_s'] / 60:.1f} min",
             f"- n = {results['n']}, k = {results['k']}, zbiorów na komórkę: {s['repeats']}, "
             f"limit czasu LP: {results['time_limit']} s",
             f"- średnie: {s['means']}, odchylenia: {s['stds']}",
             f"- progi τ: {results['taus']} (τ = 0: LP+GNP na każdym zbiorze)",
             f"- q = (D_O + 1) / (D_KK + 1); w komórce mediana q z co najmniej {MIN_RUNS} zbiorów",
             f"- środowisko: Python {env['python']}, PuLP {env['pulp']}, "
             f"highspy {env['highspy']}, {env['platform']}, {env['processor']}", ""]

    lines += ["## 1. Podsumowanie", ""]
    rows = []
    for distribution in s["distributions"]:
        runs = [r for r in records if r["distribution"] == distribution and usable(r)]
        for tau in results["taus"]:
            switched = [r for r in runs if r["cv"] > tau]
            better = sum(orchestrator_d(r, tau) < r["KK"]["d"] for r in switched)
            worse = sum(orchestrator_d(r, tau) > r["KK"]["d"] for r in switched)
            median_q = (_fmt(statistics.median(ratio(r, tau) for r in switched), ".1f")
                        if switched else "–")
            rows.append([distribution, _fmt(tau, "g"), len(runs), len(switched), better,
                         len(switched) - better - worse, worse, median_q])
    lines += _table(["rozkład", "τ", "zbiory", "CV > τ", "D_O < D_KK", "D_O = D_KK",
                     "D_O > D_KK", "mediana q (CV > τ)"], rows) + [""]

    for distribution in s["distributions"]:
        runs = [r for r in records if r["distribution"] == distribution and usable(r)]
        if not runs:
            continue
        cv_cells = {}
        for r in runs:
            cv_cells.setdefault((r["mean"], r["std"]), []).append(r["cv"])
        lines += [f"## Rozkład {distribution}: średnie zmierzone CV w komórkach", "",
                  *_grid_table(results, {c: statistics.mean(v) for c, v in cv_cells.items()},
                               ".2f"), ""]
        for tau in results["taus"]:
            lines += [f"## Rozkład {distribution}, τ = {_fmt(tau, 'g')}: mediana q", "",
                      *_grid_table(results, cell_values(results, distribution, tau), ".1f"), ""]

    lines += ["## Czas, błędy i przejścia awaryjne", ""]
    rows = []
    for distribution in s["distributions"]:
        runs = [r for r in records if r["distribution"] == distribution]
        for name in BRANCHES:
            ok = [r[name] for r in runs if r[name]["status"] == "ok"]
            errors = [r[name]["status"] for r in runs if r[name]["status"] != "ok"]
            times = sorted(x["time"] for x in ok)
            rows.append([distribution, name, len(runs),
                         _fmt(1000 * statistics.median(times), ".2f") if times else "–",
                         _fmt(1000 * times[min(len(times) - 1, int(0.95 * len(times)))], ".2f")
                         if times else "–",
                         sum(1 for x in ok if x.get("strategy") == "kk+gnp_fallback")
                         if name == "LP+GNP" else "–",
                         sum(1 for x in ok if x.get("lp_optimal") is True)
                         if name == "LP+GNP" else "–",
                         len(errors), errors[0] if errors else ""])
    lines += _table(["rozkład", "gałąź", "zbiory", "czas, mediana [ms]", "czas, p95 [ms]",
                     "LP → KK (fallback)", "LP z dowodem optymalności", "błędy",
                     "pierwszy błąd"], rows)

    text = "\n".join(lines) + "\n"
    print(text)
    return text


def save_figures(results, out_dir):
    """One heatmap per (distribution, tau), with a common color scale (needs matplotlib)."""
    import matplotlib.pyplot as plt
    from plots import plot_orchestrator_heatmap
    out_dir = Path(out_dir)
    all_values = [cell_values(results, d, tau) for d in results["settings"]["distributions"]
                  for tau in results["taus"]]
    limit = max((abs(math.log10(q)) for values in all_values for q in values.values()),
                default=1.0)
    limit = max(limit, 0.1)
    for distribution in results["settings"]["distributions"]:
        for tau in results["taus"]:
            name = f"heatmap_{distribution}_tau{str(tau).replace('.', '_')}.png"
            fig = plot_orchestrator_heatmap(results, distribution, tau, cell_values(
                results, distribution, tau), limit=limit, save_path=out_dir / name, show=False)
            plt.close(fig)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Orchestrator vs KK on a mean-std grid")
    parser.add_argument("--quick", action="store_true", help="small grid, about 1 min")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--report-only", action="store_true",
                        help="do not compute, rebuild report.md from results.json")
    parser.add_argument("--plots", action="store_true", help="also save heatmaps (matplotlib)")
    args = parser.parse_args()
    if args.report_only:
        regenerate_report(output_dir(args.n, args.k, args.quick) / "results.json",
                          plots=args.plots)
    else:
        run_experiment(seed=args.seed, n=args.n, k=args.k, quick=args.quick, plots=args.plots)


if __name__ == "__main__":
    main()
