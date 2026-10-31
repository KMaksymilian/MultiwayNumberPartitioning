"""Plots for the KK vs orchestrator experiments (matplotlib)."""

import math

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

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


def plot_mu_sigma_heatmap(grid, save_path=None, show=True, annotate=True):
    """Heatmap of log10(D_orch / D_kk) over the (mean, std) grid.

    Blue cells: orchestrator better, red cells: KK better, gray: tie.
    The dashed line is std = 0.6 * mean (the orchestrator's CV threshold).
    """
    means, stds, results = grid["means"], grid["stds"], grid["results"]

    values = [[math.nan if r is None else r["log_ratio"] for r in row] for row in results]
    finite = [abs(v) for row in values for v in row if not math.isnan(v)]
    limit = max(max(finite, default=1.0), 0.1)

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
