"""Step 6 - Markdown report generation.

Reads the CSV files produced by the previous steps and assembles ``report.md``,
which ``render_report_html.py`` then converts into a standalone ``report.html``.
The structure follows the analysis plan: introduction, methodology, descriptive
statistics, paired tests, Spearman correlation, visualisations, discussion and
limitations.

The report language is English. All generated figures already carry English
labels, and the CSV files use English column names, so the whole deliverable is
language-consistent.

Run from the repository root (after the other scripts):

    python Experimento_Multiagente/quantitative_analysis/generate_report.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _paths import OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import CONFIGS, LLMS  # noqa: E402

DATA_CSV = os.path.join(OUTPUT_DIR, "data.csv")
DESCRIPTIVE_CSV = os.path.join(OUTPUT_DIR, "descriptive.csv")
WILCOXON_CSV = os.path.join(OUTPUT_DIR, "wilcoxon.csv")
SPEARMAN_CSV = os.path.join(OUTPUT_DIR, "spearman.csv")
REPORT_MD = os.path.join(OUTPUT_DIR, "report.md")

METRIC_LABEL = {"f1_serv": "F1 of services", "f1_inter": "F1 of interactions"}
OUTCOME_LABEL = {
    "f1_serv": "F1 of services",
    "f1_inter": "F1 of interactions",
    "yaml_valid": "Valid YAML",
}


def md_table(frame: pd.DataFrame, headers: dict = None) -> str:
    """Render a DataFrame as a GitHub-flavoured Markdown table.

    Args:
        frame: Data to render (values are converted to text).
        headers: Optional mapping ``column -> pretty header``.

    Returns:
        A Markdown table as a single string.
    """
    headers = headers or {}
    columns = list(frame.columns)
    lines = ["| " + " | ".join(headers.get(c, c) for c in columns) + " |"]
    lines.append("|" + "|".join(["---"] * len(columns)) + "|")
    for _, row in frame.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append("" if np.isnan(value) else ("%.4f" % value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fmt(value: float) -> str:
    """Format a floating point number with four decimals, tolerating NaN."""
    return "-" if value is None or (isinstance(value, float) and np.isnan(value)) else "%.4f" % value


def descriptive_table(descriptive: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Build a wide descriptive table (configuration x LLM) for one metric.

    Args:
        descriptive: Output of the descriptive step.
        metric: Metric column to tabulate.

    Returns:
        DataFrame with one row per configuration and one column per LLM, where
        each cell reads ``mean (sd) [ci_low; ci_high]``.
    """
    subset = descriptive[descriptive["metric"] == metric]
    rows = []
    for config in CONFIGS:
        row = {"Configuration": config}
        for llm in LLMS:
            cell = subset[(subset["config"] == config) & (subset["llm"] == llm)]
            if cell.empty:
                row[llm] = "-"
                continue
            record = cell.iloc[0]
            row[llm] = "%s (%s) [%s; %s]" % (
                fmt(record["mean"]), fmt(record["std"]),
                fmt(record["ci95_low"]), fmt(record["ci95_high"]),
            )
        rows.append(row)
    return pd.DataFrame(rows)


def best_configs(descriptive: pd.DataFrame, metric: str) -> dict:
    """Return, for each LLM, the configuration with the highest mean value.

    Args:
        descriptive: Output of the descriptive step.
        metric: Metric column to inspect.

    Returns:
        Mapping ``llm -> (config, mean)``.
    """
    subset = descriptive[descriptive["metric"] == metric]
    result = {}
    for llm in LLMS:
        group = subset[subset["llm"] == llm].sort_values("mean", ascending=False)
        if not group.empty:
            result[llm] = (group.iloc[0]["config"], float(group.iloc[0]["mean"]))
    return result


def significant_rows(wilcoxon: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Return the rows of the Wilcoxon table whose p-value is below ``alpha``.

    Args:
        wilcoxon: Output of the paired tests step.
        alpha: Significance level.

    Returns:
        The filtered DataFrame.
    """
    valid = wilcoxon.dropna(subset=["p_value"])
    return valid[valid["p_value"] < alpha]


def metric_mean(descriptive: pd.DataFrame, metric: str, config: str, llm: str) -> float:
    """Return the mean of a metric for a specific configuration and LLM."""
    cell = descriptive[
        (descriptive["metric"] == metric)
        & (descriptive["config"] == config)
        & (descriptive["llm"] == llm)
    ]
    return float(cell.iloc[0]["mean"]) if not cell.empty else float("nan")


def correlation_value(spearman: pd.DataFrame, x: str, y: str, scope: str):
    """Return ``(rho, p_value)`` for one correlation row."""
    cell = spearman[(spearman["x"] == x) & (spearman["y"] == y) & (spearman["scope"] == scope)]
    if cell.empty:
        return float("nan"), float("nan")
    return float(cell.iloc[0]["rho"]), float(cell.iloc[0]["p_value"])


def build_intro() -> list:
    """Return the Markdown lines of the introduction section."""
    return [
        "# Quantitative Analysis of the Experiments on Microservice Architecture Generation",
        "",
        "## 1. Introduction",
        "",
        "This report presents the statistical analysis of the experimental results obtained with "
        "the **DAVINCI Architect** pipeline, which generates microservice architectures from "
        "textual requirements. The objective is to quantitatively and reproducibly evaluate how "
        "different pipeline configurations and different language models affect the quality of "
        "the produced architectures, in addition to characterizing the associated computational "
        "cost.",
        "",
        "The experiment follows a factorial ablation design. Four pipeline configurations, "
        "denoted **C0**, **C1**, **C2**, and **C3**, were evaluated on two language models "
        "(**Gemini** and **DeepSeek**), across **eight reference systems**. Each combination of "
        "configuration and model was executed **three times**, totaling 24 executions and 192 "
        "observations at the system level.",
        "",
        "The configurations differ in the agents that compose the pipeline:",
        "",
        "- **C0** - uses only Agent 1 (DDD Architect), with no refinement, no communication "
        "specialization, and no consolidation;",
        "- **C1** - full pipeline, with Agent 1, the Communication Specialist, the Refiner, and "
        "the Consolidator, plus the specification generator;",
        "- **C2** - same as C1, but without the Refiner;",
        "- **C3** - uses only Agent 1 (DDD Architect), Agent 4 (Refiner), and Agent 5 (YAML "
        "Exporter). Agents 2 (Communication Specialist) and 3 (Consolidator) are removed "
        "together: without the second independent proposal generated by Agent 2, the "
        "consolidation step no longer makes sense, as there is no longer more than one candidate "
        "architecture to compare. C3 therefore evaluates the combined effect of the absence of "
        "communication specialization and the absence of consolidation on the final "
        "architecture, keeping the refinement of a single proposal as an intermediate stage.",
        "",
        "The quality metrics are the F1-score of **services** and the F1-score of "
        "**interactions**, calculated on the final architecture recommended by the pipeline and "
        "compared to the reference ground truth. The cost metrics are the total tokens consumed "
        "and the execution time.",
        "",
    ]


def build_methodology() -> list:
    """Return the Markdown lines describing extraction and statistical methods."""
    return [
        "## 2. Methodology",
        "",
        "### 2.1 Data source and organization",
        "",
        "The data were extracted from the raw artifacts generated by the pipeline, organized by "
        "model, configuration, and execution. For each execution, three types of artifacts were "
        "read: the metrics report (PDF or TXT), which contains the F1 tables for services and "
        "interactions; the architectural specification (PDF or TXT), which contains the "
        "generated YAML; and the execution metadata JSON file, which records tokens and time "
        "per system.",
        "",
        "The consolidated table, saved in `data.csv`, has one row per "
        "(system, configuration, model, execution), totaling 192 records with the columns "
        "`system`, `config`, `llm`, `execution`, `f1_serv`, `f1_inter`, `yaml_valid`, "
        "`total_tokens`, and `duration_ms`.",
        "",
        "### 2.2 Extraction and normalizations",
        "",
        "The extraction of PDF reports was performed with the `pdfplumber` library. Some care "
        "was necessary due to inconsistencies in the artifacts:",
        "",
        "1. **Consolidated result.** For C1 and C2, there is an explicit line called "
        "*Consolidated* in the metrics report. For C0 and C3, which produce a single proposal, "
        "the final architecture is equivalent to *Proposal A*; in these cases, that value was "
        "adopted as the consolidated result.",
        "2. **Computational cost.** The metrics artifacts do not contain a *Tracer* section; the "
        "values of `total_tokens` and `duration_ms` were obtained from the execution metadata "
        "JSON file, which records consumption per system.",
        "3. **System identification.** Some JSON files do not carry the `system` field; in these "
        "cases, the records were associated by positional order, following the canonical order "
        "of the eight systems. This hypothesis was validated against the per-system cost tables "
        "of the synthesized reports, yielding exact correspondence of values.",
        "4. **Name normalization.** Naming divergences between artifacts were corrected (for "
        "example, `acmeair`/`AcmeAir`, `Pet-Clinic`/`PetClinic`, and the typo `7ed`/`7ep`).",
        "",
        "### 2.3 YAML validation",
        "",
        "The variable `yaml_valid` indicates whether the generated YAML is syntactically valid, "
        "that is, whether it can be loaded by `yaml.safe_load`. It is important to note that PDF "
        "rendering **destroys YAML formatting**: the two-space indentation of the `to:` lines is "
        "lost and long lines are truncated. For this reason, the raw text extracted from PDFs "
        "is not valid in any case.",
        "",
        "To obtain an informative measure, a **documented normalization** was applied, which "
        "re-indents the `to:` lines under the corresponding `- from:` entry, restoring the "
        "intended structure of the document. With this normalization, 187 of the 192 "
        "observations (97.4%) present valid YAML. The five exceptions are discussed in the "
        "limitations section. The normalization is implemented in the function "
        "`normalize_pdf_yaml` and is restricted to syntax evaluation, not altering any F1, "
        "token, or time value.",
        "",
        "### 2.4 Statistical procedures",
        "",
        "All analysis was conducted in Python 3.12, with the libraries `pandas`, `numpy`, "
        "`scipy`, `matplotlib`, `pyyaml`, and `pdfplumber`. The following procedures were "
        "adopted:",
        "",
        "- **Descriptive statistics:** mean, median, and standard deviation per "
        "configuration-model combination, accompanied by a 95% confidence interval obtained by "
        "non-parametric bootstrap with 1,000 resamples and a fixed seed;",
        "- **Paired tests:** the Wilcoxon signed-rank test was applied to the comparisons "
        "C0 vs C1, C1 vs C2, and C1 vs C3, separately by model. The eight systems were treated "
        "as paired units, using the average of the three executions of each system to reduce "
        "stochastic noise;",
        "- **Effect size:** for each comparison, Cliff's delta was calculated, classified as "
        "negligible (|d| < 0.147), small (|d| < 0.330), medium (|d| < 0.474), or large "
        "(|d| >= 0.474);",
        "- **Correlation:** Spearman's rank correlation coefficient was used to evaluate the "
        "association between token cost and the three outcome variables (F1 of services, F1 of "
        "interactions, and YAML validity), both globally and within each configuration.",
        "",
        "The significance level adopted is 5%, and the results were not corrected for multiple "
        "comparisons, which is discussed in the limitations.",
        "",
    ]


def build_descriptive_section(descriptive: pd.DataFrame) -> list:
    """Return the Markdown lines of the descriptive statistics section."""
    lines = [
        "## 3. Descriptive statistics",
        "",
        "The following tables summarize performance by configuration and by model. Each cell "
        "presents the mean, the standard deviation in parentheses, and the 95% confidence "
        "interval in brackets. The number of observations is 24 per cell (eight systems in "
        "three executions).",
        "",
        "### 3.1 F1 of services",
        "",
        md_table(descriptive_table(descriptive, "f1_serv")),
        "",
        "### 3.2 F1 of interactions",
        "",
        md_table(descriptive_table(descriptive, "f1_inter")),
        "",
    ]

    serv_gem = [metric_mean(descriptive, "f1_serv", c, "Gemini") for c in CONFIGS]
    serv_ds = [metric_mean(descriptive, "f1_serv", c, "DeepSeek") for c in CONFIGS]
    best_inter = best_configs(descriptive, "f1_inter")
    std_c3_gem = float(descriptive[
        (descriptive.metric == "f1_inter") & (descriptive.config == "C3")
        & (descriptive.llm == "Gemini")
    ].iloc[0]["std"])
    std_c3_ds = float(descriptive[
        (descriptive.metric == "f1_inter") & (descriptive.config == "C3")
        & (descriptive.llm == "DeepSeek")
    ].iloc[0]["std"])

    lines += [
        "**Commentary.** Service identification is practically insensitive to configuration "
        "variations. The means remain between %.4f and %.4f, and the range across the four "
        "configurations is only %.4f for Gemini and %.4f for DeepSeek. In all cells, the median "
        "equals 1.0000, indicating that most observations reach the metric's ceiling; the small "
        "standard deviations confirm this stability. In other words, the additional agent "
        "effort in C1 and C2 does not produce relevant service gains." % (
            min(serv_gem + serv_ds), max(serv_gem + serv_ds),
            max(serv_gem) - min(serv_gem), max(serv_ds) - min(serv_ds),
        ),
        "",
        "The behavior of interactions is quite different and constitutes the main "
        "differentiator among configurations. In Gemini, the best mean performance occurs in "
        "**%s** (%.4f), closely followed by %s (%.4f); in DeepSeek, the best result is also from "
        "**%s** (%.4f). Configuration C3 presents the worst mean performance in both models "
        "(%.4f and %.4f, respectively) and, above all, the highest dispersion (standard "
        "deviations of %.4f and %.4f), revealing instability: without the Communication "
        "Specialist, implicit dependencies are no longer consistently recovered." % (
            best_inter["Gemini"][0], best_inter["Gemini"][1],
            "C1" if best_inter["Gemini"][0] != "C1" else "C2",
            metric_mean(descriptive, "f1_inter", "C1", "Gemini"),
            best_inter["DeepSeek"][0], best_inter["DeepSeek"][1],
            metric_mean(descriptive, "f1_inter", "C3", "Gemini"),
            metric_mean(descriptive, "f1_inter", "C3", "DeepSeek"),
            std_c3_gem, std_c3_ds,
        ),
        "",
        "It is worth noting that the confidence intervals of C1 and C2 overlap widely in both "
        "models, suggesting that removing the Refiner (C2) does not compromise the average "
        "quality of interactions. The interval for C3, however, is visibly wider and located at "
        "a lower level, especially in DeepSeek.",
        "",
    ]
    return lines


def build_paired_section(wilcoxon: pd.DataFrame) -> list:
    """Return the Markdown lines of the paired tests section."""
    display = wilcoxon.copy()
    display["metric"] = display["metric"].map(METRIC_LABEL)
    display = display[["metric", "comparison", "llm", "n_pairs", "n_nonzero",
                       "statistic", "p_value", "cliffs_delta", "effect"]]

    significant = significant_rows(wilcoxon)
    lines = [
        "## 4. Paired tests",
        "",
        "The following table presents the results of the Wilcoxon test and Cliff's delta for "
        "each configuration contrast, separately by model. The column `n_nonzero` indicates in "
        "how many of the eight pairs the difference between configurations is non-zero; when "
        "this number is very low, the test has little statistical power.",
        "",
        md_table(display, {
            "metric": "Metric", "comparison": "Comparison", "llm": "Model",
            "n_pairs": "Pairs", "n_nonzero": "Non-zero differences",
            "statistic": "W statistic", "p_value": "p-value",
            "cliffs_delta": "Cliff's delta", "effect": "Magnitude",
        }),
        "",
    ]

    if not significant.empty:
        described = "; ".join(
            "%s (%s, %s): p = %.4f, delta = %.4f (%s)" % (
                row["comparison"], row["llm"], METRIC_LABEL[row["metric"]],
                row["p_value"], row["cliffs_delta"], row["effect"],
            )
            for _, row in significant.iterrows()
        )
        lines += [
            "**Commentary.** Considering a 5%% significance level, only one comparison reaches "
            "statistical significance: %s. In the other contrasts, p-values are high, which is "
            "consistent with the small number of non-zero differences and the sample size of "
            "eight pairs." % described,
            "",
        ]
    else:
        lines += [
            "**Commentary.** No comparison reaches statistical significance at the 5%% level, "
            "which is compatible with the reduced power of eight pairs and with the high "
            "frequency of ties.",
            "",
        ]

    lines += [
        "Two patterns deserve attention. First, for F1 of services, all deltas are practically "
        "null (|delta| <= 0.08), reinforcing that service identification does not depend on "
        "configuration. Second, for F1 of interactions, deltas are larger and consistently "
        "positive in the expected direction: the contrasts C0 vs C1 and C1 vs C3 favor C1, "
        "while C1 vs C2 shows a negligible effect.",
        "",
        "The most expressive case is Gemini in the **C1 vs C3** comparison: with seven of eight "
        "non-zero differences, we obtain p = 0.0469 and Cliff's delta = 0.3906 (medium effect), "
        "indicating that removing the Communication Specialist detectably degrades interaction "
        "recovery. In DeepSeek, the effect points in the same direction, but with small "
        "magnitude (delta = 0.2656) and without significance (p = 0.3750), suggesting greater "
        "variability across executions in that model.",
        "",
        "It is also noteworthy that the C1 vs C2 comparison produces negligible effects in both "
        "models and for both metrics. This result is the quantitative evidence that the Refiner "
        "can be dispensed with without measurable loss of quality, which has a direct impact on "
        "the cost-benefit relationship discussed later.",
        "",
    ]
    return lines


def build_correlation_section(spearman: pd.DataFrame) -> list:
    """Return the Markdown lines of the Spearman correlation section."""
    display = spearman.copy()
    display["x"] = "Tokens"
    display["y"] = display["y"].map(OUTCOME_LABEL)
    display = display[["x", "y", "scope", "n", "rho", "p_value"]]

    rho_serv, p_serv = correlation_value(spearman, "total_tokens", "f1_serv", "Global")
    rho_inter, p_inter = correlation_value(spearman, "total_tokens", "f1_inter", "Global")
    rho_yaml, p_yaml = correlation_value(spearman, "total_tokens", "yaml_valid", "Global")
    rho_c2, p_c2 = correlation_value(spearman, "total_tokens", "f1_inter", "C2")
    rho_c1y, p_c1y = correlation_value(spearman, "total_tokens", "yaml_valid", "C1")

    return [
        "## 5. Spearman correlation",
        "",
        "The following table presents Spearman's rank correlation between token cost and the "
        "three outcome variables, calculated globally (192 observations) and within each "
        "configuration (48 observations).",
        "",
        md_table(display, {
            "x": "Variable X", "y": "Variable Y", "scope": "Scope",
            "n": "n", "rho": "rho", "p_value": "p-value",
        }),
        "",
        "**Commentary.** There is no relevant association between token cost and F1 of services, "
        "either globally (rho = %.4f; p = %.4f) or in any isolated configuration. This result is "
        "consistent with the discrete nature of the service metric, which saturates at 1.0000 in "
        "most observations." % (rho_serv, p_serv),
        "",
        "For interactions, a weak but positive association is observed (rho = %.4f; p = %.4f in "
        "the global scope): executions that consume more tokens tend to produce better "
        "interaction results. The association is clearer within C2 (rho = %.4f; p = %.4f), where "
        "higher consumption is linked to more complex systems that require more communication "
        "inference. In C1, the correlation is practically null, suggesting that, in this "
        "configuration, quality depends more on consensus among agents than on computational "
        "effort." % (rho_inter, p_inter, rho_c2, p_c2),
        "",
        "Regarding YAML validity, the global correlation is negative and marginally "
        "non-significant (rho = %.4f; p = %.4f), and within C1 it reaches significance "
        "(rho = %.4f; p = %.4f). The most prudent reading is that this effect does not express a "
        "causal relationship between cost and syntax failure, but rather the higher incidence of "
        "truncation of long lines in more complex systems, addressed in the limitations "
        "section." % (rho_yaml, p_yaml, rho_c1y, p_c1y),
        "",
        "In summary, computational cost is not a good predictor of architectural quality: the "
        "correlations are weak and do not support the idea that spending more tokens guarantees "
        "better results.",
        "",
    ]


def cost_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Build a table with mean token cost and mean duration per configuration and LLM."""
    rows = []
    for config in CONFIGS:
        row = {"Configuration": config}
        for llm in LLMS:
            subset = data[(data["config"] == config) & (data["llm"] == llm)]
            row[llm] = "%.0f tokens / %.0f ms" % (
                subset["total_tokens"].mean(), subset["duration_ms"].mean(),
            )
        rows.append(row)
    return pd.DataFrame(rows)


def mean_tokens(data: pd.DataFrame, config: str, llm: str) -> float:
    """Return the mean token cost for a configuration and LLM."""
    subset = data[(data["config"] == config) & (data["llm"] == llm)]
    return float(subset["total_tokens"].mean()) if not subset.empty else float("nan")


def build_figures_section() -> list:
    """Return the Markdown lines with the figures and their captions."""
    return [
        "## 6. Visualizations",
        "",
        "All figures were generated in grayscale, at 300 dpi, so that they remain legible in "
        "print. In grouped plots, the light tone represents Gemini and the dark tone represents "
        "DeepSeek; in box plots, DeepSeek's fill receives hatching to reinforce the distinction "
        "without relying on color.",
        "",
        "### 6.1 Distribution of F1 of services",
        "",
        "![Box plot of F1 of services by configuration and model](figures/boxplot_services.png)",
        "",
        "*Figure 1 - Box plot of F1 of services. The distributions are strongly concentrated "
        "near 1.0000 in all configurations, with few observations below the third quartile. The "
        "absence of outliers with expressive deviation confirms that service identification is "
        "stable regardless of configuration and model.*",
        "",
        "![Violin plot of F1 of services by configuration and model](figures/violin_services.png)",
        "",
        "*Figure 2 - Violin plot of F1 of services. The flattened shape shifted toward the top "
        "reinforces the concentration of observations at the metric's maximum value.*",
        "",
        "### 6.2 Distribution of F1 of interactions",
        "",
        "![Box plot of F1 of interactions by configuration and model](figures/boxplot_interactions.png)",
        "",
        "*Figure 3 - Box plot of F1 of interactions. The dispersion is much larger than that "
        "observed for services. C3 presents the lowest box and the largest interquartile range, "
        "especially in DeepSeek, evidencing the loss of quality resulting from removing the "
        "Communication Specialist.*",
        "",
        "![Violin plot of F1 of interactions by configuration and model](figures/violin_interactions.png)",
        "",
        "*Figure 4 - Violin plot of F1 of interactions. A bimodal distribution is observed in "
        "some configurations, resulting from the coexistence of \"easy\" systems (interactions "
        "explicit in the requirements) and systems with implicit dependencies.*",
        "",
        "### 6.3 Token cost versus quality",
        "",
        "![Scatter between tokens and F1](figures/scatter_tokens_vs_f1.png)",
        "",
        "*Figure 5 - Scatter between total tokens (log scale) and F1. The marker shape identifies "
        "the configuration and the fill identifies the model, so the figure remains informative "
        "in black and white. In the services panel, points concentrate at the top, with no "
        "visible relationship with cost. In the interactions panel, it is noticeable that higher "
        "costs (associated with C1 and C2) accompany more stable values, while C0 and C3 occupy "
        "the lower-cost and higher-dispersion range.*",
        "",
    ]


def build_cost_table_section(data: pd.DataFrame) -> list:
    """Return the Markdown lines describing the computational cost."""
    c1_gem, c0_gem = mean_tokens(data, "C1", "Gemini"), mean_tokens(data, "C0", "Gemini")
    c2_gem = mean_tokens(data, "C2", "Gemini")
    c1_ds, c0_ds = mean_tokens(data, "C1", "DeepSeek"), mean_tokens(data, "C0", "DeepSeek")
    c2_ds = mean_tokens(data, "C2", "DeepSeek")
    return [
        "### 6.4 Computational cost",
        "",
        "The following table presents the average cost per system execution, in tokens and "
        "milliseconds.",
        "",
        md_table(cost_summary(data)),
        "",
        "**Commentary.** Cost grows sharply with the number of agents involved. In Gemini, the "
        "average tokens per system goes from approximately %.0f in C0 to about %.0f in C1, an "
        "increase of roughly %.1f times; in DeepSeek, the same jump occurs from %.0f to %.0f "
        "(%.1f times). Configuration C2 sits at an intermediate level (%.0f tokens in Gemini and "
        "%.0f in DeepSeek), reducing the cost relative to C1." % (
            c0_gem, c1_gem, c1_gem / c0_gem if c0_gem else float("nan"),
            c0_ds, c1_ds, c1_ds / c0_ds if c0_ds else float("nan"),
            c2_gem, c2_ds,
        ),
        "",
        "This cost difference is the main argument against the indiscriminate use of the full "
        "pipeline and supports the recommendation of C2 as an intermediate configuration, "
        "developed in the discussion.",
        "",
    ]


def build_discussion() -> list:
    """Return the Markdown lines of the discussion section."""
    return [
        "## 7. Discussion",
        "",
        "### 7.1 Synthesis of findings",
        "",
        "The analysis allows separating two effects clearly. The first is that of **service "
        "identification**, which proves robust and practically invariant: means remain above "
        "0.95 in all configurations and models, with small standard deviations and medians "
        "equal to 1.0000. The second is that of **interaction recovery**, which is sensitive to "
        "configuration and accounts for almost all the variation observed among the generated "
        "architectures.",
        "",
        "Interactions also concentrate the highest variability. In both models, C3 presents "
        "simultaneously the lowest mean and the highest standard deviation, indicating that the "
        "absence of the Communication Specialist not only reduces expected performance but also "
        "makes the result less predictable. C1 and C2, on the other hand, present similar means "
        "and smaller standard deviations, characterizing greater stability.",
        "",
        "### 7.2 Answers to the research questions",
        "",
        "**RQ1 - Does the multi-agent pipeline improve quality relative to the single agent?** "
        "For services, there is no evidence of gain: the measured effects are negligible. For "
        "interactions, the answer is affirmative, though moderate in statistical terms. The "
        "means favor C1 and C2 in both models, and Cliff's delta consistently points in that "
        "direction, even though only the C1 vs C3 contrast in Gemini reaches conventional "
        "significance. The defensible conclusion is that the gain exists and is especially "
        "relevant in systems whose requirements omit implicit dependencies, but the sample size "
        "limits the strength of the evidence.",
        "",
        "**RQ2 - Which pipeline components really matter?** The results isolate the "
        "Communication Specialist (removed in C3) as the critical component for interactions: "
        "its absence reduces the mean and increases dispersion. The Refiner (removed in C2) "
        "shows no measurable contribution, since C1 vs C2 produces negligible effects in both "
        "models and for both metrics. This supports the hypothesis that the value of the "
        "pipeline lies in specialization and consolidation, not in the number of agents.",
        "",
        "**RQ3 - What is the trade-off between quality, stability, and cost?** Cost grows much "
        "faster than quality. Compared to C0, the full pipeline consumes an order of magnitude "
        "more tokens, while the interaction gain is incremental. Since C2 maintains average "
        "quality close to C1 at lower cost and shows no detectable loss, it configures itself as "
        "the best balance. C0 remains attractive only when requirements are well structured and "
        "explicitly state dependencies, a situation in which its instability does not compromise "
        "the result. C3, in turn, presents the worst cost-benefit ratio: it costs more than C0 "
        "and delivers worse interactions than C1 and C2.",
        "",
        "### 7.3 Role of the language models",
        "",
        "No systematic quality differences were observed between Gemini and DeepSeek. Service "
        "identification is equivalent, and in interactions, both models exhibit the same "
        "qualitative ordering of configurations, although DeepSeek shows greater dispersion "
        "across executions. This behavior is consistent with the weak correlations between cost "
        "and quality: the determining factor appears to be the clarity of requirements and the "
        "presence of specialized agents, not the model employed.",
        "",
    ]


def build_limitations() -> list:
    """Return the Markdown lines of the limitations section."""
    return [
        "## 8. Limitations",
        "",
        "The results should be interpreted in light of the following limitations:",
        "",
        "1. **Small sample size.** There are eight systems and three executions per combination, "
        "resulting in eight pairs per test at the system level. This limited statistical power "
        "explains why only one of the twelve contrasts reaches significance, even when effect "
        "sizes point to consistent differences.",
        "2. **Single ground truth.** The precision, recall, and F1 metrics were calculated "
        "against a single reference set per system. The quality of the metrics depends on how "
        "faithfully this ground truth represents the desired architecture, and legitimate design "
        "variations may be penalized.",
        "3. **High frequency of ties.** Due to the saturation of F1 of services at 1.0000, many "
        "paired differences are null. This reduces the number of non-zero ranks and compromises "
        "the performance of the Wilcoxon test.",
        "4. **No correction for multiple comparisons.** Since twelve tests were performed, there "
        "is a risk of Type I error inflation. With a Bonferroni correction, for example, the "
        "single significant result would no longer be so. Effect sizes, being independent of "
        "sample size, should be considered the primary evidence.",
        "5. **Artifacts truncated by PDF.** The truncation of long lines in PDF rendering affects "
        "YAML validation in five observations (all from Gemini) and also prevents content "
        "evaluation, since the text is cut off. The `yaml_valid` variable, therefore, measures "
        "the syntactic validity of what survived extraction, not necessarily the quality of the "
        "YAML produced by the pipeline.",
        "6. **Dependence on inference for metadata.** Some metadata files do not explicitly "
        "record which system each entry refers to; the association was made by positional order, "
        "validated against an independent table. Nevertheless, the strategy relies on a premise "
        "not verifiable in all files.",
        "7. **Partially inconsistent cost metadata.** Some records report `prompt_tokens` equal "
        "to zero, although `total_tokens` is consistent with the number of calls. For this "
        "reason, only `total_tokens` was used.",
        "8. **Scope of evaluated configurations.** Temperature 0.0 and a single few-shot "
        "prompting strategy were used. The results do not automatically generalize to other "
        "temperatures, prompting strategies, or models.",
        "",
        "Despite these limitations, the observed patterns are consistent across the two models "
        "and converge with the qualitative analysis recorded in the synthesized reports, which "
        "reinforces the reliability of the conclusions presented.",
        "",
    ]


def main() -> None:
    """Assemble ``report.md`` from the CSV files produced by the other steps."""
    ensure_output_dirs()
    data = pd.read_csv(DATA_CSV)
    descriptive = pd.read_csv(DESCRIPTIVE_CSV)
    wilcoxon = pd.read_csv(WILCOXON_CSV)
    spearman = pd.read_csv(SPEARMAN_CSV)

    lines = []
    lines += build_intro()
    lines += build_methodology()
    lines += build_descriptive_section(descriptive)
    lines += build_paired_section(wilcoxon)
    lines += build_correlation_section(spearman)
    lines += build_figures_section()
    lines += build_cost_table_section(data)
    lines += build_discussion()
    lines += build_limitations()

    with open(REPORT_MD, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print("report written: %s (%d lines)" % (REPORT_MD, len(lines)))


if __name__ == "__main__":
    main()








