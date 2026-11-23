"""Running time and quality of the algorithms against the input size.

Algorithms: KK, GNP, LP, LP with pruning, LP+GNP (the orchestrator with
threshold 0, so its LP branch is always used) and the orchestrator with its
threshold TAU.

Two experiments:
    size   - time and D against the number of elements n (numbers of fixed length),
    digits - time and D against the length of the numbers (number of decimal
             digits), for a fixed n.
The numbers are not bounded: a number may have 50 or 5000 digits, and the cost of
adding or comparing such numbers grows with their length.

Two scenarios (datasets), both exact integers of any length:
    uniform   - integers drawn uniformly from [10^(c-1), 10^c - 1] (exactly c
                digits, CV about 0.5),
    lognormal - lognormal distribution with CV = LOGNORMAL_CV and mean
                5 * 10^(c-1); a float sample x of mean 1 is scaled with integer
                arithmetic and filled with random low digits, so the numbers are
                exact for any c.

Every (scenario, experiment, n, k, c, repetition) has its own seed derived from
`seed`, so all algorithms are run on the same datasets. Each run happens in a
worker process and is stopped after HARD_TIMEOUT seconds (the solver does not
always respect its own time limit); such a run is recorded as an error.

Usage from the terminal (in the project root):
    .venv\\Scripts\\python src\\scaling.py --quick               # check (~1 min)
    .venv\\Scripts\\python src\\scaling.py --seed 0              # full run
    .venv\\Scripts\\python src\\scaling.py --report-only --plots # report.md + figures

Outputs (src/results/scaling[/quick]/): results.json, report.md
(and PNG figures with --plots, which needs matplotlib).
"""
import json
import math
import multiprocessing
import platform
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "results" / "scaling"
TIME_LIMIT = 1.0      # LP time limit [s]
HARD_TIMEOUT = 60.0   # a run without a result after this many seconds is stopped
TAU = 4.26            # orchestrator threshold (minimax value of the threshold study)
LOGNORMAL_CV = 5.0
MIN_RUNS = 3          # a median is reported only when at least this many repetitions are usable

# name -> largest n on which the algorithm is run in the size experiment
ALGORITHMS = {
    "KK": None,
    "GNP": None,
    "LP": 2000,
    "LP z pruningiem": 2000,
    "LP+GNP": 10_000,
    "Orkiestrator": None,
}
SCENARIOS = {
    "uniform": "rozkład jednostajny (liczby o dokładnie c cyfrach)",
    "lognormal": f"rozkład lognormalny, CV = {LOGNORMAL_CV:g} (średnia 5·10^(c−1))",
}

FULL = {
    "size": {"ns": (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10_000, 20_000, 50_000, 100_000),
             "digits": 6, "ks": (3, 5), "repeats": 5},
    "digits": {"ds": (3, 6, 9, 12, 15, 18, 24, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192,
                      16384),
               "n": 1000, "ks": (3, 5), "repeats": 5},
}
QUICK = {
    "size": {"ns": (10, 100, 1000), "digits": 6, "ks": (3,), "repeats": 3},
    "digits": {"ds": (3, 18, 512), "n": 100, "ks": (3,), "repeats": 3},
}


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

def uniform_dataset(n, digits, rng):
    """n integers with exactly `digits` decimal digits, drawn uniformly."""
    low = 10 ** (digits - 1) if digits > 1 else 1
    return [rng.randrange(low, 10 ** digits) for _ in range(n)]


def lognormal_dataset(n, digits, rng, cv=LOGNORMAL_CV):
    """n integers from the lognormal distribution with the given CV and mean
    5 * 10^(digits - 1), exact for any number of digits."""
    sigma = math.sqrt(math.log(1 + cv ** 2))
    mu = -sigma ** 2 / 2  # mean of the float sample = 1
    scale = 5 * 10 ** (digits - 1)
    fill = scale >> 52    # below the float precision: random low digits
    dataset = []
    for _ in range(n):
        num, den = rng.lognormvariate(mu, sigma).as_integer_ratio()
        value = num * scale // den + (rng.randrange(fill) if fill > 0 else 0)
        dataset.append(max(1, value))
    return dataset


DATASETS = {"uniform": uniform_dataset, "lognormal": lognormal_dataset}


def sample_cv(dataset):
    """CV computed with exact integer arithmetic (any length of the numbers)."""
    n = len(dataset)
    total = sum(dataset)
    squares = n * sum(x * x for x in dataset) - total * total  # n^2 * (n-1)/n * variance
    if total == 0 or n < 2:
        return 0.0
    # CV^2 = n * squares / ((n - 1) * total^2); log10 keeps it finite for long numbers
    log_cv2 = math.log10(n) + math.log10(max(squares, 1)) - math.log10(n - 1) \
        - 2 * math.log10(total)
    return 10 ** (log_cv2 / 2)


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def make_algorithm(name):
    """Return f(dataset, k, metadata) for the algorithm `name`."""
    if name == "KK":
        from algorithm_kk import algorithm_kk
        return lambda data, k, metadata: algorithm_kk(data, k)
    if name == "GNP":
        from algorithm_gnp import algorithm_gnp
        return lambda data, k, metadata: algorithm_gnp(data, [0] * k)
    if name in ("LP", "LP z pruningiem"):
        from algorithm_lp import algorithm_lp
        pruning = name == "LP z pruningiem"
        return lambda data, k, metadata: algorithm_lp(data, k, time_limit=TIME_LIMIT,
                                                      metadata=metadata, pruning=pruning)
    if name in ("LP+GNP", "Orkiestrator"):
        from orchestrator import orchestrator_partitioning
        tau = 0.0 if name == "LP+GNP" else TAU
        return lambda data, k, metadata: orchestrator_partitioning(
            data, k, cv_threshold=tau, time_limit=TIME_LIMIT, metadata=metadata)
    raise ValueError(f"unknown algorithm: {name}")


def _log10(value):
    """log10 of a non-negative integer of any length."""
    return math.log10(value) if value > 0 else -math.inf


def run_one(name, dataset, k):
    """Run one algorithm on one dataset; errors are recorded, not raised."""
    algorithm = make_algorithm(name)
    metadata = {}
    start = time.perf_counter()
    try:
        partitions = algorithm(list(dataset), k, metadata)
        elapsed = time.perf_counter() - start
    except Exception as error:  # noqa: BLE001 - an error is a result here
        return {"algorithm": name, "time": time.perf_counter() - start,
                "status": f"error: {type(error).__name__}: {error}"[:200]}

    if len(partitions) != k or sorted(x for p in partitions for x in p) != sorted(dataset):
        return {"algorithm": name, "time": elapsed, "status": "error: invalid partition"}

    sums = [sum(p) for p in partitions]
    d = max(sums) - min(sums)
    return {
        "algorithm": name,
        "time": elapsed,
        "status": "ok",
        "d": d if d < 10 ** 18 else None,  # exact D only when it is short (JSON-friendly)
        "log10_d1": _log10(d + 1),
        "log10_rel": _log10(d + 1) - _log10(sum(dataset)),  # log10((D + 1) / sum)
        "strategy": metadata.get("strategy", ""),
        "lp_status": metadata.get("lp_status", ""),
        "lp_optimal": metadata.get("lp_optimal"),
    }


class Runner:
    """Runs algorithms in a worker process, stopping runs that take too long."""

    def __init__(self):
        self.pool = None

    def run(self, name, dataset, k):
        if self.pool is None:
            self.pool = multiprocessing.Pool(1)
        job = self.pool.apply_async(run_one, (name, dataset, k))
        try:
            return job.get(HARD_TIMEOUT)
        except multiprocessing.TimeoutError:
            self.close()
            return {"algorithm": name, "time": HARD_TIMEOUT,
                    "status": f"error: Timeout: brak wyniku po {HARD_TIMEOUT:.0f} s"}

    def close(self):
        if self.pool is not None:
            self.pool.terminate()
            self.pool.join()
            self.pool = None


def run_config(runner, scenario, experiment, n, k, digits, repeats, seed, max_n):
    """All algorithms on `repeats` datasets of one (scenario, n, k, digits)."""
    records = []
    for rep in range(repeats):
        rng = random.Random(f"{seed}-{scenario}-{experiment}-{n}-{k}-{digits}-{rep}")
        dataset = DATASETS[scenario](n, digits, rng)
        info = {"scenario": scenario, "experiment": experiment, "n": n, "k": k,
                "digits": digits, "rep": rep, "cv": sample_cv(dataset),
                "log10_sum": _log10(sum(dataset))}
        for name in ALGORITHMS:
            limit = max_n.get(name)
            if limit is not None and n > limit:
                continue
            record = runner.run(name, dataset, k)
            record.update(info)
            records.append(record)
    return records


def _environment():
    try:
        from importlib.metadata import version
        pulp_version, highspy_version = version("pulp"), version("highspy")
    except Exception:  # noqa: BLE001 - only informative
        pulp_version = highspy_version = "?"
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "pulp": pulp_version, "highspy": highspy_version}


def run_experiments(seed=0, quick=False, settings=None, out_dir=None, plots=False):
    """Run both experiments in both scenarios, save results.json and report.md."""
    settings = settings or (QUICK if quick else FULL)
    out_dir = Path(out_dir) if out_dir else (OUT_DIR / "quick" if quick else OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    records = []

    size, digits = settings["size"], settings["digits"]
    configs = []
    for scenario in SCENARIOS:
        configs += [(scenario, "size", n, k, size["digits"]) for k in size["ks"]
                    for n in size["ns"]]
        configs += [(scenario, "digits", digits["n"], k, d) for k in digits["ks"]
                    for d in digits["ds"]]

    runner = Runner()
    try:
        for i, (scenario, experiment, n, k, d) in enumerate(configs, 1):
            t0 = time.perf_counter()
            # the digits experiment runs every algorithm on the same n
            max_n = ALGORITHMS if experiment == "size" else {}
            records += run_config(runner, scenario, experiment, n, k, d,
                                  settings[experiment]["repeats"], seed, max_n)
            print(f"[{i}/{len(configs)}] {scenario}, {experiment}: n={n}, k={k}, cyfry={d}: "
                  f"{time.perf_counter() - t0:.0f} s (łącznie {time.perf_counter() - start:.0f} s)",
                  flush=True)
    finally:
        runner.close()

    results = {
        "seed": seed,
        "quick": quick,
        "settings": json.loads(json.dumps(settings)),
        "scenarios": SCENARIOS,
        "algorithms": list(ALGORITHMS),
        "tau": TAU,
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


def load_results(path=None):
    path = Path(path) if path else OUT_DIR / "results.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def regenerate_report(path=None, plots=False):
    """Rebuild report.md (and the figures) from saved results without computing."""
    path = Path(path) if path else OUT_DIR / "results.json"
    results = load_results(path)
    (path.parent / "report.md").write_text(print_report(results), encoding="utf-8")
    if plots:
        save_figures(results, path.parent)
    return results


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def usable(r):
    """Successful run that really used its algorithm (no LP -> KK fallback)."""
    return r["status"] == "ok" and r.get("strategy") != "kk+gnp_fallback"


def series(records, scenario, experiment, k, algorithm, x_key, value_key):
    """{x: [values of usable runs]}; x with fewer than MIN_RUNS usable runs is dropped."""
    out = {}
    for r in records:
        if (r["scenario"], r["experiment"], r["k"], r["algorithm"]) == \
                (scenario, experiment, k, algorithm) and usable(r):
            out.setdefault(r[x_key], []).append(r[value_key])
    return {x: ys for x, ys in sorted(out.items()) if len(ys) >= MIN_RUNS}


def fitted_exponent(points, x_min):
    """Least-squares slope of log(median) against log(x) for x >= x_min (None if < 3 points)."""
    pts = [(math.log(x), math.log(statistics.median(ys))) for x, ys in points.items()
           if x >= x_min and statistics.median(ys) > 0]
    if len(pts) < 3:
        return None
    mx = statistics.mean(p[0] for p in pts)
    my = statistics.mean(p[1] for p in pts)
    return sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)


def _fmt(value, spec):
    return "–" if value is None else format(value, spec)


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return lines + ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]


def _median_table(records, scenario, experiment, k, x_key, value_key, algorithms, transform,
                  spec):
    xs = sorted({r[x_key] for r in records
                 if (r["scenario"], r["experiment"], r["k"]) == (scenario, experiment, k)})
    curves = {a: series(records, scenario, experiment, k, a, x_key, value_key)
              for a in algorithms}
    rows = []
    for x in xs:
        row = [x]
        for a in algorithms:
            ys = curves[a].get(x)
            row.append(_fmt(transform(statistics.median(ys)), spec) if ys else "–")
        rows.append(row)
    return rows, curves


def print_report(results):
    records, algorithms = results["records"], results["algorithms"]
    s, env = results["settings"], results["environment"]
    lines = ["# Czas i jakość w zależności od rozmiaru wejścia", "",
             "## 0. Ustawienia", "",
             f"- seed: {results['seed']}, data: {results['date']}, "
             f"czas badania: {results['duration_s'] / 60:.1f} min",
             f"- LP+GNP: orkiestrator z progiem 0 (zawsze gałąź LP); Orkiestrator: próg "
             f"τ = {results['tau']}; limit czasu LP: {results['time_limit']} s; uruchomienie "
             f"bez wyniku po {results['hard_timeout']:.0f} s jest przerywane",
             *[f"- scenariusz {name}: {label}" for name, label in results["scenarios"].items()],
             f"- badanie 1 (n): n = {s['size']['ns']}, cyfry = {s['size']['digits']}, "
             f"k = {s['size']['ks']}, powtórzeń = {s['size']['repeats']}",
             f"- badanie 2 (cyfry): c = {s['digits']['ds']}, n = {s['digits']['n']}, "
             f"k = {s['digits']['ks']}, powtórzeń = {s['digits']['repeats']}",
             f"- mediany z co najmniej {MIN_RUNS} udanych powtórzeń; uruchomienia, w których "
             "LP zawiodło i orkiestrator przeszedł na KK, są pominięte (patrz ostatnia sekcja)",
             f"- środowisko: Python {env['python']}, PuLP {env['pulp']}, "
             f"highspy {env['highspy']}, {env['platform']}, {env['processor']}", ""]

    ms = lambda t: 1000 * t  # noqa: E731
    for scenario, label in results["scenarios"].items():
        lines += [f"# Scenariusz: {label}", ""]
        for k in s["size"]["ks"]:
            rows, curves = _median_table(records, scenario, "size", k, "n", "time", algorithms,
                                         ms, ".3f")
            lines += [f"## Czas [ms] a liczba elementów n (k = {k}, mediana)", "",
                      *_table(["n", *algorithms], rows), ""]
            exps = [f"{a}: {e:.2f}" for a in algorithms
                    if (e := fitted_exponent(curves[a], 1000)) is not None]
            if exps:
                lines += ["Wykładnik α w czas ∝ n^α (dopasowanie dla n ≥ 1000): "
                          + ", ".join(exps), ""]
            rows, _ = _median_table(records, scenario, "size", k, "n", "log10_rel", algorithms,
                                    lambda v: v, ".1f")
            lines += [f"## Jakość a n: mediana log10((D + 1) / Σ) (k = {k})", "",
                      *_table(["n", *algorithms], rows), ""]
        for k in s["digits"]["ks"]:
            rows, curves = _median_table(records, scenario, "digits", k, "digits", "time",
                                         algorithms, ms, ".3f")
            lines += [f"## Czas [ms] a liczba cyfr c (n = {s['digits']['n']}, k = {k}, mediana)",
                      "", *_table(["c", *algorithms], rows), ""]
            exps = [f"{a}: {e:.2f}" for a in algorithms
                    if (e := fitted_exponent(curves[a], 1024)) is not None]
            if exps:
                lines += ["Wykładnik β w czas ∝ c^β (dopasowanie dla c ≥ 1024): "
                          + ", ".join(exps), ""]
            rows, _ = _median_table(records, scenario, "digits", k, "digits", "log10_rel",
                                    algorithms, lambda v: v, ".1f")
            lines += [f"## Jakość a c: mediana log10((D + 1) / Σ) (n = {s['digits']['n']}, "
                      f"k = {k})", "", *_table(["c", *algorithms], rows), ""]

    lines += ["# Błędy, strategie i status LP", ""]
    rows = []
    for scenario in results["scenarios"]:
        for experiment in ("size", "digits"):
            for a in algorithms:
                runs = [r for r in records if (r["scenario"], r["experiment"], r["algorithm"])
                        == (scenario, experiment, a)]
                if not runs:
                    continue
                errors = [r for r in runs if r["status"] != "ok"]
                strategies = {}
                for r in runs:
                    if r["status"] == "ok" and r.get("strategy"):
                        strategies[r["strategy"]] = strategies.get(r["strategy"], 0) + 1
                first = (f"{errors[0]['status']} (n={errors[0]['n']}, c={errors[0]['digits']})"
                         if errors else "")
                rows.append([scenario, experiment, a, len(runs), len(errors),
                             ", ".join(f"{key} {v}" for key, v in sorted(strategies.items()))
                             or "–",
                             sum(1 for r in runs if r.get("lp_optimal") is True)
                             if a not in ("KK", "GNP") else "–", first])
    lines += _table(["scenariusz", "badanie", "algorytm", "uruchomienia", "błędy",
                     "strategie orkiestratora", "LP z dowodem optymalności", "pierwszy błąd"],
                    rows)

    text = "\n".join(lines) + "\n"
    print(text)
    return text


def save_figures(results, out_dir):
    """Figures for the report (needs matplotlib)."""
    from plots import plot_scaling
    out_dir = Path(out_dir)
    import matplotlib.pyplot as plt
    for experiment, name in (("size", "n"), ("digits", "c")):
        for metric in ("time", "quality"):
            for scenario in results["scenarios"]:
                for k in results["settings"][experiment]["ks"]:
                    fig = plot_scaling(results, experiment, metric, scenario, k, show=False,
                                       save_path=out_dir / f"{metric}_vs_{name}_{scenario}_k{k}.png")
                    plt.close(fig)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Time and quality against the input size")
    parser.add_argument("--quick", action="store_true", help="small settings, about 1 min")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--report-only", action="store_true",
                        help="do not compute, rebuild report.md from results.json")
    parser.add_argument("--plots", action="store_true", help="also save figures (matplotlib)")
    args = parser.parse_args()
    if args.report_only:
        regenerate_report(OUT_DIR / "quick" / "results.json" if args.quick else None,
                          plots=args.plots)
    else:
        run_experiments(seed=args.seed, quick=args.quick, plots=args.plots)


if __name__ == "__main__":
    main()
