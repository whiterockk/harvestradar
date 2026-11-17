"""Print the whole source code of HarvestRadar into one PDF (cover, contents, every file with line numbers).

Usage: python scripts/code_listing.py  ->  dist/doc/HarvestRadar_source_code.pdf and .md (same files, plain text)
Files: every tracked source and configuration file (Python, JavaScript, HTML, YAML, TOML, prompts, lock files);
data, images, fonts and documentation are left out (they are in the repository).
"""

from __future__ import annotations

import datetime as dt
import html
import subprocess
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, TextLexer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "doc" / "HarvestRadar_source_code.pdf"
MD = OUT.with_suffix(".md")
FENCE = {".py": "python", ".js": "javascript", ".html": "html", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".md": "markdown"}
KEEP = (".py", ".js", ".html", ".yaml", ".yml", ".toml", ".lock", ".cfg")
EXTRA = {"Makefile", ".gitignore"}
ORDER = ["pyproject.toml", "Makefile", "requirements.lock", "requirements-llm.lock", ".gitignore", ".streamlit/",
         "config/", ".github/", "src/harvestradar/", "web/", "scripts/", "tests/"]


def files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    keep = [f for f in tracked if (f.endswith(KEEP) or Path(f).name in EXTRA or f.startswith("src/harvestradar/report/prompts/"))
            and not f.startswith(("data/", "docs/", "reports/"))]

    def rank(f: str) -> tuple[int, str]:
        return next((i for i, p in enumerate(ORDER) if f == p or f.startswith(p)), len(ORDER)), f
    return sorted(keep, key=rank)


def lexer(name: str):
    try:
        return get_lexer_for_filename(name if not name.endswith(".lock") else "x.txt")
    except Exception:  # noqa: BLE001
        return TextLexer()


def main() -> None:
    from playwright.sync_api import sync_playwright

    fs = files()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    fmt = HtmlFormatter(style="friendly", linenos="inline", nowrap=False)
    parts, toc, total = [], [], 0
    for i, f in enumerate(fs, 1):
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        n = text.count("\n") + (0 if text.endswith("\n") else 1)
        total += n
        toc.append(f'<tr><td>{i}</td><td><a href="#f{i}">{html.escape(f)}</a></td><td class="r">{n:,}</td></tr>')
        parts.append(f'<section class="file" id="f{i}"><h2>{i}. {html.escape(f)} <span>{n:,} lines</span></h2>'
                     f'{highlight(text, lexer(f), fmt)}</section>')
    today = dt.date.today()
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>HarvestRadar source code</title><style>
{fmt.get_style_defs('.highlight')}
body {{ font-family: Helvetica, Arial, sans-serif; color: #111; }}
.cover {{ height: 240mm; display: flex; flex-direction: column; justify-content: center; }}
.cover h1 {{ font-size: 34pt; margin: 0 0 8mm; }} .cover p {{ font-size: 12pt; line-height: 1.6; margin: 0; }}
h2 {{ font-size: 11pt; background: #f1f3f5; padding: 2mm 3mm; border-left: 3px solid #f5a93a; margin: 0 0 2mm; }}
h2 span {{ font-weight: 400; color: #666; float: right; }}
table.toc {{ border-collapse: collapse; width: 100%; font-size: 9.5pt; }} table.toc td {{ padding: 1.2mm 2mm; border-bottom: 1px solid #e5e5e5; }}
td.r {{ text-align: right; }} a {{ color: #111; text-decoration: none; }}
section.file {{ break-before: page; }}
.highlight pre {{ font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace; font-size: 7.6pt; line-height: 1.35;
  white-space: pre-wrap; word-break: break-all; margin: 0; }}
.highlight .linenos {{ color: #999; }}
</style></head><body>
<div class="cover"><h1>HarvestRadar<br>source code</h1>
<p>Complete source of the HarvestRadar app and pipeline: {len(fs)} files, {total:,} lines.</p>
<p>Commit {commit} of github.com/whiterockk/harvestradar, printed {today.day} {today:%B %Y}.</p>
<p>Data, images, fonts and documentation are in the repository and are not printed here.</p></div>
<section style="break-before: page"><h2>Contents</h2><table class="toc"><tr><td></td><td><b>File</b></td><td class="r"><b>Lines</b></td></tr>{''.join(toc)}</table></section>
{''.join(parts)}</body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".html")
    tmp.write_text(doc, encoding="utf-8")
    with sync_playwright() as p:
        exe = next(iter(sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux*/chrome"))), None)
        b = p.chromium.launch(executable_path=str(exe) if exe else None)
        page = b.new_page()
        page.goto(tmp.as_uri(), wait_until="load")
        page.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
                 margin={"top": "14mm", "bottom": "16mm", "left": "12mm", "right": "12mm"},
                 header_template="<span></span>",
                 footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#888">HarvestRadar source code'
                                 ' · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
        b.close()
    tmp.unlink()
    # the same code as one Markdown file: a contents list, then each file in a fenced block
    md = [f"# HarvestRadar source code\n\nCommit {commit} of https://github.com/whiterockk/harvestradar, {len(fs)} files, "
          f"{total:,} lines, printed {today.day} {today:%B %Y}. To rebuild the project, copy each block into the file "
          "named in its heading (or download the repository as a zip from GitHub).\n\n## Contents\n"]
    md += [f"{i}. `{f}`" for i, f in enumerate(fs, 1)]
    for i, f in enumerate(fs, 1):
        text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        fence = "````" if "```" in text else "```"
        md.append(f"\n## {i}. `{f}`\n\n{fence}{FENCE.get(Path(f).suffix, '')}\n{text.rstrip()}\n{fence}")
    MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"written {OUT} ({OUT.stat().st_size / 1e6:.1f} MB) and {MD} ({MD.stat().st_size / 1e6:.1f} MB): "
          f"{len(fs)} files, {total:,} lines")


if __name__ == "__main__":
    main()
