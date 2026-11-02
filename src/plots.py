import math
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

from distributions import DISTRIBUTIONS, get_distribution

# Diverging palette: blue = orchestrator better, gray = tie, red = KK better.
DIVERGING = LinearSegmentedColormap.from_list("orch_vs_kk", ["#2a78d6", "#f0efec", "#e34948"])
UNREACHABLE_COLOR = "#d9d8d3"
CV_THRESHOLD = 0.6


def _cell_edges(values):
    """Return cell borders for centers given in `values` (equal or unequal spacing)."""
    edges = [(a + b) / 2 for a, b in zip(values, values[1:])]
    first = values[0] - (edges[0] - values[0]) if edges else values[0] - 0.5
    last = values[-1] + (values[-1] - edges[-1]) if edges else values[-1] + 0.5
    return [first, *edges, last]


def _color_limit(grids):
    """Largest |log_ratio| over all cells of the given grids (at least 0.1)."""
    finite = [abs(r["log_ratio"]) for grid in grids for row in grid["results"]
              for r in row if r is not None]
    return max(max(finite, default=1.0), 0.1)


def plot_mu_sigma_heatmap(grid, save_path=None, show=True, annotate=True, limit=None):
    """Heatmap of log10(D_orch / D_kk) over the (mean, std) grid.

    Blue cells: orchestrator better, red cells: KK better, gray: tie,
    light gray background: CV not reachable for this distribution.
    The dashed line is std = 0.6 * mean (the orchestrator's CV threshold).
    `limit` fixes the color scale to [-limit, limit] (to compare several heatmaps).
    """
    means, stds, results = grid["means"], grid["stds"], grid["results"]

    values = [[math.nan if r is None else r["log_ratio"] for r in row] for row in results]
    limit = limit or _color_limit([grid])

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.set_facecolor(UNREACHABLE_COLOR)

    mesh = ax.pcolormesh(
        _cell_edges(means), _cell_edges(stds), values,
        cmap=DIVERGING, norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit),
        edgecolors="white", linewidth=1.5,
    )

    if annotate:
        for i, std in enumerate(stds):
            for j, mean in enumerate(means):
                result = results[i][j]
                if result is None:
                    continue
                ax.text(mean, std, f"{result['d_ratio']:.1f}×",
                        ha="center", va="center", fontsize=8, color="#0b0b0b")

    x_max = _cell_edges(means)[-1]
    ax.plot([0, x_max], [0, CV_THRESHOLD * x_max], linestyle="--", color="#0b0b0b",
            linewidth=1.5, label=f"CV = {CV_THRESHOLD} (std = {CV_THRESHOLD} · mean)")

    ax.set_xlim(_cell_edges(means)[0], x_max)
    ax.set_ylim(_cell_edges(stds)[0], _cell_edges(stds)[-1])
    ax.set_xlabel("Mean of the data (μ)")
    ax.set_ylabel("Standard deviation of the data (σ)")
    ax.set_title(
        f"Orchestrator vs KK: mean log10(D_orch / D_kk)\n"
        f"{grid['distribution']}, n = {grid['n']}, k = {grid['k']}, "
        f"{grid['num_datasets']} datasets per cell, seed = {grid['seed']}"
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), frameon=False)

    colorbar = fig.colorbar(mesh, ax=ax)
    colorbar.set_label("log10(D_orch / D_kk)   (< 0: orchestrator better, > 0: KK better)")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return fig


def _plot_for_distributions(plot_func, items, save_dir, file_prefix, **plot_kwargs):
    """Call `plot_func(item, save_path, **plot_kwargs)` for every distribution.
    `items` is a dict {distribution name: grid or sweep}. With `save_dir`
    every figure is saved as <save_dir>/<file_prefix>_<distribution>.png.
    """
    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)

    figures = {}
    for name, item in items.items():
        save_path = Path(save_dir) / f"{file_prefix}_{name}.png" if save_dir else None
        figures[name] = plot_func(item, save_path=save_path, **plot_kwargs)
    return figures


def plot_mu_sigma_heatmaps(grids, save_dir=None, show=True, annotate=True):
    """Plot one mu-sigma heatmap per distribution with a common color scale.

    `grids` is the dict returned by `run_mu_sigma_grids`.
    Files: <save_dir>/heatmap_mu_sigma_<distribution>.png.
    """
    return _plot_for_distributions(plot_mu_sigma_heatmap, grids, save_dir, "heatmap_mu_sigma",
                                   show=show, annotate=annotate,
                                   limit=_color_limit(grids.values()))


# Categorical colors (+ different marker and line style, so color is not the only cue).
ALGORITHM_STYLES = {
    "kk": {"label": "KK", "color": "#2a78d6", "marker": "o", "linestyle": "-"},
    "orch": {"label": "Orchestrator", "color": "#eb6834", "marker": "^", "linestyle": "--"},
}
QUALITY_METRICS = {
    "d": {"suffix": "_d", "offset": 1,
          "ylabel": "D + 1  (largest − smallest partition sum, log scale)",
          "title": "Partition quality vs CV"},
    "time": {"suffix": "_time", "offset": 0,
             "ylabel": "Running time [s]  (log scale)",
             "title": "Running time vs CV"},
}


def _bin_summary(chunk):
    """Return (median x, median y, 25th percentile of y, 75th percentile of y)."""
    xs = [x for x, _ in chunk]
    ys = [y for _, y in chunk]
    if len(ys) == 1:
        return xs[0], ys[0], ys[0], ys[0]
    q25, median, q75 = statistics.quantiles(ys, n=4, method="inclusive")
    return statistics.median(xs), median, q25, q75


def _binned_quantiles(xs, ys, points_per_bin, split_at=CV_THRESHOLD):
    """Group points by x and summarise every group with its median and quartiles.

    Points with x <= `split_at` and x > `split_at` are grouped separately, so no
    group mixes datasets on both sides of the orchestrator's threshold. Each side
    is sorted by x and split into groups of about `points_per_bin` points (sizes
    differ by at most one, every point is used).

    Returns one segment per non-empty side: (x medians, y medians, y 25th
    percentiles, y 75th percentiles).
    """
    points = sorted(zip(xs, ys))
    sides = [[p for p in points if p[0] <= split_at], [p for p in points if p[0] > split_at]]

    segments = []
    for side in sides:
        if not side:
            continue
        num_bins = max(1, len(side) // points_per_bin)
        bounds = [round(i * len(side) / num_bins) for i in range(num_bins + 1)]
        summaries = [_bin_summary(side[start:end]) for start, end in zip(bounds, bounds[1:])]
        segments.append(tuple(list(column) for column in zip(*summaries)))
    return segments


def _plot_binned(ax, xs, ys, points_per_bin, style, label, band_alpha=0.15):
    """Draw medians (one continuous line) and quartile bands (separately on each
    side of the threshold) of the binned points."""
    segments = _binned_quantiles(xs, ys, points_per_bin)
    for centers, _, lows, highs in segments:
        ax.fill_between(centers, lows, highs, color=style["color"], alpha=band_alpha, linewidth=0)

    centers = [x for segment in segments for x in segment[0]]
    medians = [y for segment in segments for y in segment[1]]
    ax.plot(centers, medians, color=style["color"], linestyle=style["linestyle"],
            marker=style["marker"], markersize=5, linewidth=2, label=label)


def plot_quality_vs_cv(sweep, metric="d", points_per_bin=15, save_path=None, show=True,
                       ylim=None):
    """Plot D or running time of KK and the orchestrator against the measured CV.

    metric: "d"    – D = largest minus smallest partition sum (D + 1 is plotted,
                     so a perfect partition D = 0 still fits on the log axis)
            "time" – running time in seconds
    Points are single datasets. Datasets are grouped by measured CV (about
    `points_per_bin` per group, separately below and above the CV threshold);
    the line joins the medians of the groups and the band spans the
    25th–75th percentile.
    `ylim` fixes the y-axis range (to compare several plots).
    """
    if metric not in QUALITY_METRICS:
        raise ValueError(f"metric must be one of {sorted(QUALITY_METRICS)}.")
    spec = QUALITY_METRICS[metric]
    records = sweep["records"]

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for name, style in ALGORITHM_STYLES.items():
        xs = [r["measured_cv"] for r in records]
        ys = [r[name + spec["suffix"]] + spec["offset"] for r in records]
        ax.scatter(xs, ys, s=12, alpha=0.25, color=style["color"], marker=style["marker"],
                   linewidths=0)

        _plot_binned(ax, xs, ys, points_per_bin, style, f"{style['label']} (median)")

    ax.axvline(CV_THRESHOLD, color="#0b0b0b", linestyle=":", linewidth=1.5,
               label=f"CV threshold = {CV_THRESHOLD}")
    ax.set_yscale("log")
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlabel("Measured CV of the dataset")
    ax.set_ylabel(spec["ylabel"])
    ax.set_title(
        f"{spec['title']}\n{sweep['distribution']}, n = {sweep['n']}, k = {sweep['k']}, "
        f"mean = {sweep['mean']}, {len(records)} datasets, seed = {sweep['seed']}"
    )
    ax.grid(which="major", color="#e1e0d9", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return fig


def plot_quality_vs_cv_all(sweeps, metric="d", save_dir=None, show=True, points_per_bin=15):
    """Plot `plot_quality_vs_cv` for every distribution with a common y-axis range.

    `sweeps` is the dict returned by `run_cv_sweeps`.
    Files: <save_dir>/quality_<d|time>_vs_cv_<distribution>.png.
    """
    if metric not in QUALITY_METRICS:
        raise ValueError(f"metric must be one of {sorted(QUALITY_METRICS)}.")
    spec = QUALITY_METRICS[metric]

    values = [r[name + spec["suffix"]] + spec["offset"]
              for sweep in sweeps.values() for r in sweep["records"]
              for name in ALGORITHM_STYLES]
    ylim = (min(values) / 1.5, max(values) * 1.5) if values else None

    return _plot_for_distributions(plot_quality_vs_cv, sweeps, save_dir,
                                   f"quality_{metric}_vs_cv", metric=metric,
                                   points_per_bin=points_per_bin, show=show, ylim=ylim)


DISTRIBUTION_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                       "#e87ba4", "#008300", "#6250d6", "#e34948"]
DISTRIBUTION_MARKERS = ["o", "^", "s", "D", "v", "P", "X", "*"]
DISTRIBUTION_LINESTYLES = ["-", "--", ":", "-."]


def distribution_style(name):
    """Return the plot style of a distribution.

    The style depends on the position of the distribution in DISTRIBUTIONS, so a
    distribution keeps the same color on every plot, whichever subset is drawn.
    """
    index = list(DISTRIBUTIONS).index(get_distribution(name).name)
    if index >= len(DISTRIBUTION_COLORS):
        raise ValueError(
            f"Only {len(DISTRIBUTION_COLORS)} distributions can be compared on one plot; "
            f"split them into several plots."
        )
    return {
        "color": DISTRIBUTION_COLORS[index],
        "marker": DISTRIBUTION_MARKERS[index],
        "linestyle": DISTRIBUTION_LINESTYLES[index % len(DISTRIBUTION_LINESTYLES)],
    }


def plot_ratio_vs_cv(sweeps, points_per_bin=15, save_path=None, show=True):
    """Compare distributions on one plot: D_orch / D_kk against the measured CV.

    For every dataset the ratio (D_orch + 1) / (D_kk + 1) is computed (faint points);
    the line is the median of groups of about `points_per_bin` datasets and the
    band spans the 25th–75th percentile.
    """
    fig, ax = plt.subplots(figsize=(9, 5.5))

    for name, sweep in sweeps.items():
        style = distribution_style(name)
        xs = [r["measured_cv"] for r in sweep["records"]]
        ys = [(r["orch_d"] + 1) / (r["kk_d"] + 1) for r in sweep["records"]]
        ax.scatter(xs, ys, s=10, alpha=0.2, color=style["color"], marker=style["marker"],
                   linewidths=0)
        _plot_binned(ax, xs, ys, points_per_bin, style, name, band_alpha=0.12)

    ax.axhline(1, color="#898781", linewidth=1)
    ax.axvline(CV_THRESHOLD, color="#0b0b0b", linestyle=":", linewidth=1.5,
               label=f"CV threshold = {CV_THRESHOLD}")
    ax.set_yscale("log")
    ax.set_xlabel("Measured CV of the dataset")
    ax.set_ylabel("(D_orch + 1) / (D_kk + 1)   (> 1: KK better, log scale)")
    first = next(iter(sweeps.values()))
    ax.set_title(
        f"Orchestrator vs KK for different distributions (median ratio)\n"
        f"n = {first['n']}, k = {first['k']}, mean = {first['mean']}, seed = {first['seed']}"
    )
    ax.grid(which="major", color="#e1e0d9", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=len(sweeps) + 1,
              frameon=False)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    return fig
