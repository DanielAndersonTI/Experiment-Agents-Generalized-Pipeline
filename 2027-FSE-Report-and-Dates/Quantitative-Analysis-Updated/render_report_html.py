"""Step 8 - Render the Markdown report as a standalone HTML file.

The generated HTML embeds every figure as a base64 data URI, so the file can be
opened in any browser (and printed to PDF) without needing the ``figures/``
folder next to it.

Run from this folder:

    python render_report_html.py
"""

from __future__ import annotations

import base64
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from markdown_it import MarkdownIt  # noqa: E402

from _paths import FIGURES_DIR, OUTPUT_DIR  # noqa: E402

REPORT_MD = os.path.join(OUTPUT_DIR, "report.md")
REPORT_HTML = os.path.join(OUTPUT_DIR, "report.html")

# Minimal print-friendly stylesheet (grayscale, serif body, bordered tables).
STYLE = """
:root { color-scheme: light; }
body {
  max-width: 900px; margin: 0 auto; padding: 32px 24px 64px;
  font-family: Georgia, 'Times New Roman', serif; font-size: 16px;
  line-height: 1.65; color: #111; background: #fff;
}
h1 { font-size: 1.9em; border-bottom: 2px solid #333; padding-bottom: .3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #999; padding-bottom: .2em; margin-top: 1.8em; }
h3 { font-size: 1.2em; margin-top: 1.4em; }
img { max-width: 100%; height: auto; border: 1px solid #ccc; margin: 8px 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.9em; }
th, td { border: 1px solid #999; padding: 5px 8px; text-align: left; }
th { background: #ededed; }
tr:nth-child(even) td { background: #fafafa; }
code { background: #f2f2f2; padding: 1px 4px; font-size: 0.9em; }
pre { background: #f7f7f7; border: 1px solid #ddd; padding: 10px; overflow-x: auto; }
pre code { background: none; }
blockquote { border-left: 3px solid #999; margin-left: 0; padding-left: 12px; color: #444; }
li { margin: 4px 0; }
@media print { body { max-width: none; padding: 0; } h2 { page-break-after: avoid; } img { page-break-inside: avoid; } }
"""

_IMAGE_SRC = re.compile(r'src="(?!data:)(?P<path>[^"]+\.png)"')


def embed_images(html: str, base_dir: str) -> str:
    """Replace local PNG references by inline base64 data URIs.

    Args:
        html: HTML produced by the Markdown renderer.
        base_dir: Directory used to resolve the relative image paths.

    Returns:
        The HTML with every image embedded.
    """
    def replace(match: re.Match) -> str:
        path = os.path.join(base_dir, match.group("path").replace("/", os.sep))
        if not os.path.isfile(path):
            raise FileNotFoundError("figure not found: %s" % path)
        with open(path, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode("ascii")
        return 'src="data:image/png;base64,%s"' % encoded

    return _IMAGE_SRC.sub(replace, html)


def main() -> None:
    """Convert ``report.md`` into the standalone ``report.html``."""
    with open(REPORT_MD, encoding="utf-8") as handle:
        markdown_text = handle.read()

    renderer = MarkdownIt("commonmark", {"html": True}).enable("table")
    body = renderer.render(markdown_text)
    body = embed_images(body, OUTPUT_DIR)

    title = markdown_text.splitlines()[0].lstrip("# ").strip()
    document = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        "<title>%s</title>\n"
        "<style>%s</style>\n</head>\n<body>\n%s</body>\n</html>\n" % (title, STYLE, body)
    )
    with open(REPORT_HTML, "w", encoding="utf-8") as handle:
        handle.write(document)

    embedded = document.count("data:image/png;base64,")
    print("figures embedded: %d" % embedded)
    print("html written: %s (%.1f KB)" % (REPORT_HTML, os.path.getsize(REPORT_HTML) / 1024.0))


if __name__ == "__main__":
    main()
