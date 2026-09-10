# Quantitative Analysis - C0–C3 Experiments

Scripts that perform the statistical analysis of the experimental results on
microservice architecture generation with multi-agent pipelines
(DAVINCI Architect).

## How to run

From the repository root:

```bash
python Experimento_Multiagente/quantitative_analysis/run_all.py
```

Use `--refresh-cache` to force the re-extraction of the text from every PDF
(only needed when the source artifacts change):

```bash
python Experimento_Multiagente/quantitative_analysis/run_all.py --refresh-cache
```

Each step can also be executed individually, in the order below.

## Step order

| Step | Script | Output |
|---|---|---|
| 0 | `inspect_sources.py` | verification report printed to the console |
| - | `cache_texts.py` | `_text_cache.json` (performance cache) |
| 1 | `extract_data.py` | `data.csv` |
| 2 | `descriptive_stats.py` | `descriptive.csv` |
| 3 | `paired_tests.py` | `wilcoxon.csv` |
| 4 | `correlation.py` | `spearman.csv` |
| 5 | `plots.py` | `figures/*.png` |
| 6 | `generate_report.py` | `report.md` |
| 7 | `render_report_html.py` | `report.html` (standalone HTML preview) |

## How to read the report

The final report is `report.md`. There are three ways to read it rendered:

1. **VS Code built-in preview** (no extra files): open `report.md` and use
   `Ctrl+Shift+V` (preview tab) or `Ctrl+K V` (side-by-side preview).
2. **Standalone HTML**: run
   `python Experimento_Multiagente/quantitative_analysis/render_report_html.py`
   and open the generated `report.html` in any browser. The figures are
   embedded as base64, so the file works on its own. To obtain a PDF, use
   `Ctrl+P` in the browser and choose "Save as PDF".
3. **Markdown PDF extension** for VS Code, if you prefer exporting straight
   from the editor (`Ctrl+Shift+P` -> "Markdown PDF: Export (pdf)").

`report.html` is only a preview artifact and can be deleted without affecting
the analysis.

## Outputs

Every result is written to
`2027-FSE-Report-and-Dates/Quantitative-Analysis/`:

```
Quantitative-Analysis/
├── data.csv
├── descriptive.csv
├── wilcoxon.csv
├── spearman.csv
├── figures/
│   ├── boxplot_services.png
│   ├── boxplot_interactions.png
│   ├── violin_services.png
│   ├── violin_interactions.png
│   └── scatter_tokens_vs_f1.png
├── report.md
└── report.html          (optional preview)
```

## Helper modules

- `_paths.py` - shared source and output paths.
- `_source_scan.py` - artifact discovery, metrics parsing, YAML validation and
  execution-metadata reading.

## Methodological decisions

1. **Consolidated result.** C1 and C2 have an explicit `Consolidated` row;
   C0 and C3 produce a single proposal and use `Proposal A` as the final result.
2. **Cost.** `total_tokens` and `duration_ms` come from the execution metadata
   JSON files, because the metrics reports do not contain a *Tracer* section.
3. **YAML validation.** PDFs destroy the YAML indentation. A documented
   normalization (`normalize_pdf_yaml`, which re-indents the `to:` lines) is
   applied before evaluating the syntax with `yaml.safe_load`.
4. **Metadata without the `system` field.** Records are associated by
   positional order; this assumption was validated against the per-system cost
   tables of the synthesized reports.
5. **Paired tests.** The mean of the three executions per system is used,
   yielding eight pairs per contrast and per model.
6. **Language.** All outputs (figures, CSV column names and the report) are in
   English.
