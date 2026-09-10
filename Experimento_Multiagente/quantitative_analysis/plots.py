"""Step 5 - Black and white figures.

Generates the five figures required by the analysis plan:

* ``boxplot_services.png``      - config x service F1, grouped by LLM
* ``boxplot_interactions.png``  - config x interaction F1, grouped by LLM
* ``violin_services.png``       - same grouping, violin representation
* ``violin_interactions.png``   - same grouping, violin representation
* ``scatter_tokens_vs_f1.png``  - token cost vs F1, discriminated by marker

Every figure uses a grayscale palette only (no colours) and is rendered at
300 dpi, as required for print.

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/plots.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from _paths import FIGURES_DIR, OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import CONFIGS, LLMS  # noqa: E402

DATA_CSV = os.path.join(OUTPUT_DIR, "data.csv")

DPI = 300
# Grayscale palette: Gemini in light gray, DeepSeek in dark gray.
GRAY = {"Gemini": "0.85", "DeepSeek": "0.35"}
HATCH = {"Gemini": "", "DeepSeek": "//"}
MARKERS = {"C0": "o", "C1": "s", "C2": "^", "C3": "D"}


def grouped_positions(index: int, offset: float = 0.22) -> dict:
    """Return the x positions of the two LLM boxes for one configuration.

    Args:
        index: Zero-based index of the configuration on the x axis.
        offset: Horizontal offset of each box relative to the group centre.

    Returns:
        Mapping ``llm -> x position``.
    """
    return {LLMS[0]: index - offset, LLMS[1]: index + offset}


def style_axis(axis, metric_label: str) -> None:
    """Apply the shared styling to a grouped box/violin axis.

    Args:
        axis: Matplotlib axis to configure.
        metric_label: Text for the y axis.
    """
    axis.set_xticks(range(len(CONFIGS)))
    axis.set_xticklabels(CONFIGS)
    axis.set_xlabel("Configuration")
    axis.set_ylabel(metric_label)
    axis.set_ylim(-0.02, 1.05)
    axis.grid(axis="y", linestyle=":", color="0.7", linewidth=0.6)
    axis.set_axisbelow(True)


def llm_legend_handles(axis) -> None:
    """Add the shared LLM legend to a figure axis."""
    handles = [
        plt.Line2D([0], [0], color="black", marker="s", linestyle="None",
                   markerfacecolor=GRAY[llm], markeredgecolor="black", label=llm)
        for llm in LLMS
    ]
    axis.legend(handles=handles, title="LLM", loc="lower right", framealpha=1)


def draw_boxplot(frame: pd.DataFrame, metric: str, title: str, output: str) -> None:
    """Draw a grouped boxplot for one metric and save it as PNG.

    Args:
        frame: Full observation table.
        metric: Column to plot (``f1_serv`` or ``f1_inter``).
        title: Figure title.
        output: Destination PNG path.
    """
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    for index, config in enumerate(CONFIGS):
        positions = grouped_positions(index)
        for llm in LLMS:
            values = frame[(frame["config"] == config) & (frame["llm"] == llm)][metric].dropna()
            box = axis.boxplot(
                values,
                positions=[positions[llm]],
                widths=0.36,
                patch_artist=True,
                showfliers=False,
                medianprops={"color": "black", "linewidth": 1.2},
                whiskerprops={"color": "black"},
                capprops={"color": "black"},
            )
            for patch in box["boxes"]:
                patch.set_facecolor(GRAY[llm])
                patch.set_edgecolor("black")
                patch.set_hatch(HATCH[llm])
    style_axis(axis, metric.replace("f1_", "F1 ").upper())
    axis.set_title(title)
    llm_legend_handles(axis)
    figure.tight_layout()
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_violin(frame: pd.DataFrame, metric: str, title: str, output: str) -> None:
    """Draw a grouped violin plot for one metric and save it as PNG.

    Args:
        frame: Full observation table.
        metric: Column to plot (``f1_serv`` or ``f1_inter``).
        title: Figure title.
        output: Destination PNG path.
    """
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    for index, config in enumerate(CONFIGS):
        positions = grouped_positions(index)
        for llm in LLMS:
            values = frame[(frame["config"] == config) & (frame["llm"] == llm)][metric].dropna()
            if values.empty:
                continue
            parts = axis.violinplot(
                [values.to_numpy()],
                positions=[positions[llm]],
                widths=0.36,
                showmeans=False,
                showmedians=True,
                showextrema=False,
            )
            for body in parts["bodies"]:
                body.set_facecolor(GRAY[llm])
                body.set_edgecolor("black")
                body.set_alpha(1.0)
                body.set_hatch(HATCH[llm])
            parts["cmedians"].set_color("black")
    style_axis(axis, metric.replace("f1_", "F1 ").upper())
    axis.set_title(title)
    llm_legend_handles(axis)
    figure.tight_layout()
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_scatter(frame: pd.DataFrame, output: str) -> None:
    """Draw the token cost versus F1 scatter plot and save it as PNG.

    Marker shape encodes the configuration and marker fill encodes the LLM, so
    the figure stays readable in black and white.

    Args:
        frame: Full observation table.
        output: Destination PNG path.
    """
    figure, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharex=True)
    for axis, metric, title in zip(
        axes, ["f1_serv", "f1_inter"], ["Services F1", "Interactions F1"]
    ):
        for config in CONFIGS:
            for llm in LLMS:
                subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
                axis.scatter(
                    subset["total_tokens"],
                    subset[metric],
                    marker=MARKERS[config],
                    s=42,
                    facecolors="none" if llm == "DeepSeek" else "0.45",
                    edgecolors="black",
                    linewidths=0.8,
                    label="%s / %s" % (config, llm),
                )
        axis.set_xscale("log")
        axis.set_xlabel("Total tokens (log scale)")
        axis.set_ylabel(title)
        axis.set_ylim(-0.02, 1.05)
        axis.grid(linestyle=":", color="0.7", linewidth=0.6)
        axis.set_axisbelow(True)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, ncol=4, loc="lower center", fontsize=8, frameon=False)
    figure.suptitle("Token cost versus F1 (marker = configuration, fill = LLM)")
    figure.tight_layout(rect=(0, 0.08, 1, 0.97))
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def main() -> None:
    """Generate every figure required by the analysis plan."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)
    draw_boxplot(frame, "f1_serv", "Service F1 by configuration and LLM",
                 os.path.join(FIGURES_DIR, "boxplot_services.png"))
    draw_boxplot(frame, "f1_inter", "Interaction F1 by configuration and LLM",
                 os.path.join(FIGURES_DIR, "boxplot_interactions.png"))
    draw_violin(frame, "f1_serv", "Service F1 by configuration and LLM",
                os.path.join(FIGURES_DIR, "violin_services.png"))
    draw_violin(frame, "f1_inter", "Interaction F1 by configuration and LLM",
                os.path.join(FIGURES_DIR, "violin_interactions.png"))
    draw_scatter(frame, os.path.join(FIGURES_DIR, "scatter_tokens_vs_f1.png"))


if __name__ == "__main__":
    main()

