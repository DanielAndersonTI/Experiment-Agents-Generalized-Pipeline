"""Step 6 - Black and white figures of the updated corpus.

Generates the figures of the report:

* ``boxplot_services.png``      - config x service F1, grouped by model
* ``violin_services.png``       - same grouping, violin representation
* ``boxplot_interactions.png``  - config x interaction F1, grouped by model
* ``violin_interactions.png``   - same grouping, violin representation
* ``scatter_tokens_vs_f1.png``  - token cost vs F1, marker = configuration
* ``cost_quality_frontier.png`` - combined F1 against mean tokens, Pareto front
* ``efficiency_per_token.png``  - F1 points per 1000 tokens, sorted
* ``effect_sizes.png``          - Cliff's delta of every contrast, both metrics
* ``yaml_validity.png``         - well-formed specifications per cell
* ``per_system_heatmap.png``    - interaction F1 by system, one panel per model
* ``c4_proposals.png``          - the two proposals of C4 and the final architecture

Every figure uses a grayscale palette only (no colours), three tones for the three
models and hatches for the two darker ones, and is rendered at 300 dpi.

Run from this folder:

    python plots.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from _paths import DATA_CSV, FIGURES_DIR, OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import COMPARISONS, CONFIGS, LLMS, SYSTEMS  # noqa: E402

DPI = 300
# Grayscale palette: Gemini in light gray, DeepSeek in mid gray, Claude in dark gray.
GRAY = {"Gemini": "0.88", "DeepSeek": "0.62", "Claude": "0.30"}
HATCH = {"Gemini": "", "DeepSeek": "//", "Claude": "xx"}
MARKERS = {"C0": "o", "C1": "s", "C2": "^", "C3": "D", "C4": "v"}
OFFSETS = {"Gemini": -0.26, "DeepSeek": 0.0, "Claude": 0.26}
WIDTH = 0.24


def grouped_positions(index: int) -> dict:
    """Return the x position of each model box inside one configuration group."""
    return {llm: index + OFFSETS[llm] for llm in LLMS}


def style_axis(axis, metric_label: str) -> None:
    """Apply the shared styling to a grouped box/violin axis."""
    axis.set_xticks(range(len(CONFIGS)))
    axis.set_xticklabels(CONFIGS)
    axis.set_xlabel("Configuration")
    axis.set_ylabel(metric_label)
    axis.set_ylim(-0.02, 1.05)
    axis.grid(axis="y", linestyle=":", color="0.7", linewidth=0.6)
    axis.set_axisbelow(True)


def llm_legend_handles(axis, location: str = "lower right") -> None:
    """Add the shared model legend to a figure axis."""
    handles = [
        Line2D([0], [0], color="black", marker="s", linestyle="None",
               markerfacecolor=GRAY[llm], markeredgecolor="black", label=llm)
        for llm in LLMS
    ]
    axis.legend(handles=handles, title="Model", loc=location, framealpha=1, fontsize=8,
                title_fontsize=8)


def draw_boxplot(frame: pd.DataFrame, metric: str, title: str, output: str) -> None:
    """Draw a grouped boxplot for one metric and save it as PNG."""
    figure, axis = plt.subplots(figsize=(7.6, 4.4))
    for index, config in enumerate(CONFIGS):
        positions = grouped_positions(index)
        for llm in LLMS:
            values = frame[(frame["config"] == config) & (frame["llm"] == llm)][metric].dropna()
            if values.empty:
                continue
            box = axis.boxplot(
                values,
                positions=[positions[llm]],
                widths=WIDTH,
                patch_artist=True,
                manage_ticks=False,
            )
            for patch in box["boxes"]:
                patch.set_facecolor(GRAY[llm])
                patch.set_edgecolor("black")
                patch.set_hatch(HATCH[llm])
            for element in ["whiskers", "caps", "medians"]:
                for artist in box[element]:
                    artist.set_color("black")
            for artist in box["fliers"]:
                artist.set_markerfacecolor("none")
                artist.set_markeredgecolor("black")
    style_axis(axis, metric.replace("f1_", "F1 ").upper())
    axis.set_title(title)
    llm_legend_handles(axis)
    figure.tight_layout()
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_violin(frame: pd.DataFrame, metric: str, title: str, output: str) -> None:
    """Draw a grouped violin plot for one metric and save it as PNG."""
    figure, axis = plt.subplots(figsize=(7.6, 4.4))
    for index, config in enumerate(CONFIGS):
        positions = grouped_positions(index)
        for llm in LLMS:
            values = frame[(frame["config"] == config) & (frame["llm"] == llm)][metric].dropna()
            if values.empty:
                continue
            parts = axis.violinplot(
                [values.to_numpy()],
                positions=[positions[llm]],
                widths=WIDTH * 1.5,
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

    Marker shape encodes the configuration, marker fill encodes the model and the
    hatch of the two darker models keeps the figure readable in black and white.
    """
    figure, axes = plt.subplots(1, 2, figsize=(11.8, 4.6), sharex=True)
    for axis, metric, title in zip(
        axes, ["f1_serv", "f1_inter"], ["Service F1", "Interaction F1"]
    ):
        for config in CONFIGS:
            for llm in LLMS:
                subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
                axis.scatter(
                    subset["total_tokens"],
                    subset[metric],
                    marker=MARKERS[config],
                    s=44,
                    facecolors=GRAY[llm],
                    edgecolors="black",
                    linewidths=0.7,
                    hatch=HATCH[llm],
                    label="%s / %s" % (config, llm),
                )
        axis.set_xscale("log")
        axis.set_xlabel("Total tokens per execution (log scale)")
        axis.set_ylabel(title)
        axis.set_ylim(-0.04, 1.06)
        axis.grid(linestyle=":", color="0.7", linewidth=0.6)
        axis.set_axisbelow(True)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, ncol=5, loc="lower center", fontsize=7, frameon=False)
    figure.suptitle("Token cost versus F1 (marker = configuration, fill = model)")
    figure.tight_layout(rect=(0, 0.10, 1, 0.96))
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_frontier(rows: list, election: dict, knee: dict, output: str) -> None:
    """Draw the cost-benefit frontier of the fifteen cells."""
    figure, axis = plt.subplots(figsize=(8.2, 5.0))
    front = [row for row in rows if row.get("pareto")]

    for llm in LLMS:
        subset = [row for row in rows if row["llm"] == llm]
        axis.scatter(
            [row["mean_tokens"] for row in subset],
            [row["combined"] for row in subset],
            marker="o", s=70, facecolors=GRAY[llm], edgecolors="black",
            hatch=HATCH[llm], linewidths=0.7, label=llm, zorder=3,
        )

    ordered = sorted(front, key=lambda row: row["mean_tokens"])
    axis.plot(
        [row["mean_tokens"] for row in ordered],
        [row["combined"] for row in ordered],
        linestyle="--", color="0.45", linewidth=0.9, zorder=2,
        label="Pareto front",
    )

    for row in rows:
        if row["cell"] in {election["elected_cell"], knee.get("knee")}:
            continue
        axis.annotate(
            row["config"], (row["mean_tokens"], row["combined"]),
            textcoords="offset points", xytext=(5, 3), fontsize=6, color="0.25",
        )

    elected = election["elected_cell"]
    elected_row = next(row for row in rows if row["cell"] == elected)
    axis.scatter(
        [elected_row["mean_tokens"]], [elected_row["combined"]],
        marker="*", s=320, facecolors="none", edgecolors="black", linewidths=1.2,
        zorder=4, label="elected (quality-equivalent, cheapest)",
    )
    axis.annotate(
        elected, (elected_row["mean_tokens"], elected_row["combined"]),
        textcoords="offset points", xytext=(10, -14), fontsize=7.5, fontweight="bold",
    )
    if knee.get("knee"):
        knee_row = next(row for row in rows if row["cell"] == knee["knee"])
        axis.scatter(
            [knee_row["mean_tokens"]], [knee_row["combined"]],
            marker="P", s=150, facecolors="none", edgecolors="black", linewidths=1.2,
            zorder=4, label="knee of the frontier",
        )
        axis.annotate(
            knee["knee"] + " (knee)", (knee_row["mean_tokens"], knee_row["combined"]),
            textcoords="offset points", xytext=(10, -16), fontsize=7.5, style="italic",
        )

    axis.set_xscale("log")
    axis.set_xlabel("Mean tokens per system execution (log scale)")
    axis.set_ylabel("Combined F1 (mean of service and interaction F1)")
    axis.set_title("Cost-benefit map of the fifteen cells")
    axis.grid(linestyle=":", color="0.7", linewidth=0.6)
    axis.set_axisbelow(True)
    axis.legend(loc="lower right", fontsize=7, framealpha=1)
    figure.tight_layout()
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_efficiency(rows: list, output: str) -> None:
    """Draw the F1 points produced per 1000 tokens, sorted."""
    ordered = sorted(rows, key=lambda row: row["quality_per_ktoken"])
    figure, axis = plt.subplots(figsize=(8.2, 5.2))
    positions = np.arange(len(ordered))
    for position, row in zip(positions, ordered):
        axis.barh(
            position, row["quality_per_ktoken"], height=0.72,
            facecolor=GRAY[row["llm"]], edgecolor="black", hatch=HATCH[row["llm"]],
        )
        axis.text(
            row["quality_per_ktoken"] + 0.004, position,
            "%.3f" % row["quality_per_ktoken"], va="center", fontsize=6.5,
        )
    axis.set_yticks(positions)
    axis.set_yticklabels(["%s" % row["cell"] for row in ordered], fontsize=7)
    axis.set_xlabel("Combined F1 points per 1000 tokens")
    axis.set_title("Quality per token, fifteen cells")
    axis.grid(axis="x", linestyle=":", color="0.7", linewidth=0.6)
    axis.set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_effect_sizes(wilcoxon: list, output: str) -> None:
    """Draw Cliff's delta of every contrast as two grayscale matrices."""
    figure, axes = plt.subplots(1, 2, figsize=(11.6, 5.0))
    labels = ["%s vs %s" % (first, second) for first, second in COMPARISONS]
    for axis, metric, title in zip(
        axes, ["f1_serv", "f1_inter"], ["Service F1", "Interaction F1"]
    ):
        matrix = np.full((len(COMPARISONS), len(LLMS)), np.nan)
        p_values = np.full((len(COMPARISONS), len(LLMS)), np.nan)
        for column, llm in enumerate(LLMS):
            for row_index, (first, second) in enumerate(COMPARISONS):
                entry = next(
                    item for item in wilcoxon
                    if item["metric"] == metric and item["llm"] == llm
                    and item["comparison"] == "%s vs %s" % (first, second)
                )
                matrix[row_index, column] = entry["cliffs_delta"]
                p_values[row_index, column] = entry["p_value"]

        axis.imshow((matrix + 0.75) / 1.5, cmap="Greys", vmin=0, vmax=1, aspect="auto")
        for row_index in range(len(COMPARISONS)):
            for column in range(len(LLMS)):
                value = matrix[row_index, column]
                marker = "*" if p_values[row_index, column] < 0.05 else ""
                axis.text(
                    column, row_index, "%.2f%s" % (value, marker),
                    ha="center", va="center", fontsize=7,
                    color="white" if (value + 0.75) / 1.5 < 0.4 else "black",
                )
        axis.set_xticks(range(len(LLMS)))
        axis.set_xticklabels(LLMS, fontsize=8)
        axis.set_yticks(range(len(COMPARISONS)))
        axis.set_yticklabels(labels, fontsize=7)
        axis.set_title(title)
    figure.suptitle("Cliff's delta per contrast (darker = first configuration better; "
                    "* = p < 0.05)", fontsize=9)
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_yaml_validity(yaml_summary: dict, output: str) -> None:
    """Draw the share of well-formed specifications of every cell."""
    figure, axis = plt.subplots(figsize=(7.6, 4.4))
    for index, config in enumerate(CONFIGS):
        positions = grouped_positions(index)
        for llm in LLMS:
            entry = yaml_summary["%s|%s" % (llm, config)]
            rate = 100.0 * entry["n_valid_normalised"] / entry["n_executions"]
            axis.bar(
                positions[llm], rate, width=WIDTH, facecolor=GRAY[llm],
                edgecolor="black", hatch=HATCH[llm],
            )
            axis.text(
                positions[llm], rate + 2, "%d/%d" % (
                    entry["n_valid_normalised"], entry["n_executions"]),
                ha="center", fontsize=6.5, rotation=90,
            )
    axis.axhline(90, linestyle="--", color="0.3", linewidth=0.8)
    axis.text(len(CONFIGS) - 0.5, 91, "90 % floor", fontsize=7, ha="right", color="0.25")
    axis.set_xticks(range(len(CONFIGS)))
    axis.set_xticklabels(CONFIGS)
    axis.set_xlabel("Configuration")
    axis.set_ylabel("Well-formed specifications (%)")
    axis.set_ylim(0, 118)
    axis.set_title("YAML validity of the emitted specification (normalised verdict)")
    axis.grid(axis="y", linestyle=":", color="0.7", linewidth=0.6)
    axis.set_axisbelow(True)
    handles = [
        Line2D([0], [0], color="black", marker="s", linestyle="None",
               markerfacecolor=GRAY[llm], markeredgecolor="black", label=llm)
        for llm in LLMS
    ]
    axis.legend(handles=handles, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13),
                frameon=False, fontsize=8)
    figure.tight_layout()
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_per_system(per_system: dict, output: str) -> None:
    """Draw the interaction F1 of every system, one panel per model."""
    figure, axes = plt.subplots(1, len(LLMS), figsize=(13.0, 4.4), sharey=True)
    for axis, llm in zip(axes, LLMS):
        matrix = np.array([
            [per_system[llm]["f1_inter"][system][config] for config in CONFIGS]
            for system in SYSTEMS
        ], dtype=float)
        axis.imshow(matrix, cmap="Greys", vmin=0.2, vmax=1.0, aspect="auto")
        for row_index in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                value = matrix[row_index, column]
                axis.text(
                    column, row_index, "%.2f" % value, ha="center", va="center",
                    fontsize=6.5, color="white" if value < 0.6 else "black",
                )
        axis.set_xticks(range(len(CONFIGS)))
        axis.set_xticklabels(CONFIGS, fontsize=8)
        axis.set_yticks(range(len(SYSTEMS)))
        axis.set_yticklabels(SYSTEMS if axis is axes[0] else [], fontsize=8)
        axis.set_title(llm, fontsize=9)
    figure.suptitle("Mean interaction F1 by subject system (darker = lower)", fontsize=9)
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def draw_proposals(proposals: dict, output: str) -> None:
    """Draw the two C4 proposals and the architecture the consolidation kept."""
    figure, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    styles = [("a", "Proposal A (architect)", "", "0.82"),
              ("b", "Proposal B (second architect)", "//", "0.55"),
              ("final", "Consolidated", "xx", "0.25")]
    for axis, stem, title in zip(axes, ["serv", "inter"], ["Service F1", "Interaction F1"]):
        positions = np.arange(len(LLMS))
        for offset_index, (key, label, hatch, color) in enumerate(styles):
            values = [proposals[llm][stem][key] for llm in LLMS]
            axis.bar(
                positions + (offset_index - 1) * 0.26, values, width=0.25,
                facecolor=color, edgecolor="black", hatch=hatch, label=label,
            )
        axis.set_xticks(positions)
        axis.set_xticklabels(LLMS, fontsize=8)
        axis.set_ylim(0, 1.05)
        axis.set_ylabel(title)
        axis.grid(axis="y", linestyle=":", color="0.7", linewidth=0.6)
        axis.set_axisbelow(True)
        axis.legend(fontsize=7, loc="lower right", framealpha=1)
    figure.suptitle("C4: the two proposals and the consolidated architecture", fontsize=9)
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output, dpi=DPI)
    plt.close(figure)
    print("figure: %s" % output)


def main() -> None:
    """Generate every figure of the report."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)
    with open(os.path.join(OUTPUT_DIR, "results.json"), encoding="utf-8") as handle:
        payload = json.load(handle)

    draw_boxplot(frame, "f1_serv", "Service F1 by configuration and model",
                 os.path.join(FIGURES_DIR, "boxplot_services.png"))
    draw_boxplot(frame, "f1_inter", "Interaction F1 by configuration and model",
                 os.path.join(FIGURES_DIR, "boxplot_interactions.png"))
    draw_violin(frame, "f1_serv", "Service F1 by configuration and model",
                os.path.join(FIGURES_DIR, "violin_services.png"))
    draw_violin(frame, "f1_inter", "Interaction F1 by configuration and model",
                os.path.join(FIGURES_DIR, "violin_interactions.png"))
    draw_scatter(frame, os.path.join(FIGURES_DIR, "scatter_tokens_vs_f1.png"))
    draw_frontier(payload["ranking"], payload["election"], payload["knee"],
                  os.path.join(FIGURES_DIR, "cost_quality_frontier.png"))
    draw_efficiency(payload["ranking"], os.path.join(FIGURES_DIR, "efficiency_per_token.png"))
    draw_effect_sizes(payload["wilcoxon"], os.path.join(FIGURES_DIR, "effect_sizes.png"))
    draw_yaml_validity(payload["yaml"], os.path.join(FIGURES_DIR, "yaml_validity.png"))
    draw_per_system(payload["per_system"], os.path.join(FIGURES_DIR, "per_system_heatmap.png"))
    draw_proposals(payload["proposals"], os.path.join(FIGURES_DIR, "c4_proposals.png"))


if __name__ == "__main__":
    main()
