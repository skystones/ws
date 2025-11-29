from __future__ import annotations

from typing import Mapping, Tuple

import matplotlib.pyplot as plt


def plot_cumulative_histogram(
    probabilities: Mapping[int, float],
    *,
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> Tuple[plt.Figure, plt.Axes]:
    if not probabilities:
        raise ValueError("probabilities cannot be empty")

    sorted_thresholds = sorted(probabilities.keys())
    values = [probabilities[thr] for thr in sorted_thresholds]

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
    else:
        fig = ax.get_figure()

    ax.bar(sorted_thresholds, values, width=0.8, align="center")
    ax.set_xlabel("Damage threshold (≥ X)")
    ax.set_ylabel("Probability")
    ax.set_ylim(0, 1)
    ax.set_title("Probability of total damage meeting or exceeding threshold")

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")

    return fig, ax
