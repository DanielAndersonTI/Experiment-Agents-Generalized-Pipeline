# Updated quantitative analysis (three models x C0-C4)

This folder re-runs the quantitative analysis of the DAVINCI Architect experiment
over the **whole** corpus of `2027-FSE-Report-and-Dates`: three models (Gemini,
DeepSeek, Claude Sonnet 4.5), five pipeline configurations (C0-C4), eight subject
systems and three rounds, that is **360 executions**.

It is a parallel pipeline of `Experimento_Multiagente/quantitative_analysis` and
reuses its procedures unchanged - percentile bootstrap with a fixed seed (1,000
resamples), Wilcoxon signed-rank test with `zero_method='wilcox'` on per-system
pairs, Cliff's delta with the original magnitude thresholds, Spearman rank
correlation - so the numbers here are directly comparable with the frozen
analysis of the two-model, four-configuration corpus.

## Outputs

| File | Content |
|---|---|
| `report.md` | the analysis written as an article section (English, with tables and figures) |
| `report.html` | the same report as a standalone page, every figure embedded as base64 |
| `figures/` | eleven figures, grayscale, 300 dpi |
| `descriptive.csv` | mean, median, standard deviation, min, max and 95% bootstrap CI per cell and metric |
| `wilcoxon.csv` | 60 contrasts: Wilcoxon statistic, p-value, Cliff's delta and magnitude |
| `spearman.csv` | Spearman rho of tokens against the two F1 metrics and against validity |
| `cost.csv` | tokens, wall-clock time and LLM calls per cell, with the count of executions that recorded a budget |
| `yaml.csv` | well-formed specifications per cell (normalised and raw) and metric coverage |
| `precision_recall.csv` | mean precision and recall of services and interactions per cell |
| `proposals_c4.csv` | the two proposals of C4 and what the consolidation keeps |
| `per_system.csv` | per-system means of both metrics, per cell |
| `ranking.csv` | cost-benefit table: combined F1, tokens, cost index, F1 per 1,000 tokens |
| `results.json` | every number the report cites, in one file |
| `data.csv` | observation table in the column layout of the frozen analysis |
| `source_all_data.csv` | observation table as extracted from the artifacts by `scan_all.py` |

## Running it

```
python run_all.py          # every step, in order
python verify_report.py    # integrity checks of report.md, report.html and the tables
```

Individual steps: `prepare_data.py`, `descriptive_stats.py`, `paired_tests.py`,
`correlation.py`, `cost_report.py`, `plots.py`, `generate_report.py`,
`render_report_html.py`.

## Conventions

* **Unit of analysis.** One row per (model, configuration, system, round). The
  inferential tests pair the eight systems, using the mean of a system's rounds
  as its value in a configuration.
* **Final architecture.** The consolidated proposal when the configuration has
  two candidates (C1, C2, C4), the first proposal otherwise (C0, C3).
* **Cost.** Mean tokens and wall-clock time per system execution, over the
  executions that recorded a budget (four executions of Claude / C4 recorded
  none).
* **Validity.** `yaml_valid` is the normalised verdict (the indentation destroyed
  by PDF rendering is restored); `yaml_valid_raw` is the verdict exactly as
  emitted.
* **Election.** The recommended configuration is selected by an explicit,
  reproducible rule: among the cells whose interaction F1 is statistically
  indistinguishable from the best cell (negligible Cliff's delta) and whose
  specifications are well formed in at least 90% of the executions, the cheapest
  in tokens. Section 4.4 of the report also reports which cell each quality floor
  would elect.
