#!/usr/bin/env python3
"""Build a card-style HTML gallery from a crawled J. Peterman collection.

Reads the folders produced by crawl.py (each holds a story.md plus
<handle>-NN.jpg illustrations) and writes a single self-contained HTML page
with a masonry card grid: the hand-drawn illustration up top (hover to flip
to the ink sketch when present) and the story beneath.

Usage:
    python3 gallery.py                       # scan ./output -> gallery.html
    python3 gallery.py output-drawings       # scan a different dir
    python3 gallery.py output my-gallery.html
"""
import html
import os
import re
import sys
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def parse_story(md_path: Path):
    """Return (title, [paragraphs]) from a story.md file."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = "Untitled"
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        lines = lines[1:]
    body = "\n".join(lines).strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return title, paras


def find_images(folder: Path):
    imgs = [p for p in folder.iterdir() if p.suffix.lower() in IMG_EXTS]
    return sorted(imgs, key=lambda p: p.name)


def build_card(folder: Path, out_dir: Path) -> str:
    story_md = folder / "story.md"
    if not story_md.exists():
        return ""
    title, paras = parse_story(story_md)
    images = find_images(folder)
    if not images:
        return ""

    # src paths relative to the gallery HTML file's directory
    srcs = [html.escape(os.path.relpath(img, out_dir)) for img in images]
    primary = srcs[0]
    secondary = srcs[1] if len(srcs) > 1 else None

    flip_class = " has-flip" if secondary else ""
    img_html = f'<img class="front" src="{primary}" alt="{html.escape(title)}" loading="lazy">'
    if secondary:
        img_html += f'<img class="back" src="{secondary}" alt="{html.escape(title)} sketch" loading="lazy">'

    story_html = "".join(f"<p>{html.escape(p)}</p>" for p in paras)

    return f"""
    <article class="card">
      <div class="art{flip_class}">{img_html}</div>
      <div class="body">
        <h2>{html.escape(title)}</h2>
        <div class="story">{story_html}</div>
      </div>
    </article>"""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>J. Peterman Gallery</title>
<style>
  :root {{
    --paper: #f4efe4;
    --ink: #2b2622;
    --accent: #7a1f2b;
    --rule: #d8cdb6;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: Georgia, "Times New Roman", serif;
    line-height: 1.55;
  }}
  header {{
    text-align: center;
    padding: 3rem 1rem 1.5rem;
    border-bottom: 2px solid var(--rule);
  }}
  header h1 {{
    font-size: 2.6rem;
    letter-spacing: .04em;
    margin: 0 0 .3rem;
  }}
  header p {{
    margin: 0;
    font-style: italic;
    color: var(--accent);
  }}
  .gallery {{
    column-count: 4;
    column-gap: 1.5rem;
    padding: 2rem;
    max-width: 1500px;
    margin: 0 auto;
  }}
  @media (max-width: 1200px) {{ .gallery {{ column-count: 3; }} }}
  @media (max-width: 850px)  {{ .gallery {{ column-count: 2; }} }}
  @media (max-width: 560px)  {{ .gallery {{ column-count: 1; }} }}
  .card {{
    break-inside: avoid;
    background: #fff;
    border: 1px solid var(--rule);
    margin: 0 0 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
  }}
  .art {{
    position: relative;
    background: #fff;
    padding: 1rem 1rem 0;
  }}
  .art img {{
    display: block;
    width: 100%;
    height: auto;
  }}
  .art .back {{
    position: absolute;
    inset: 1rem 1rem 0;
    width: calc(100% - 2rem);
    opacity: 0;
    transition: opacity .35s ease;
  }}
  .art.has-flip:hover .front {{ opacity: 0; }}
  .art.has-flip:hover .back  {{ opacity: 1; }}
  .art.has-flip::after {{
    content: "hover \\2192 sketch";
    position: absolute;
    bottom: .5rem; right: 1.3rem;
    font-size: .7rem; font-style: italic;
    color: var(--accent); opacity: .6;
  }}
  .body {{ padding: 1rem 1.3rem 1.4rem; }}
  .body h2 {{
    font-size: 1.25rem;
    margin: .2rem 0 .6rem;
    border-bottom: 1px solid var(--rule);
    padding-bottom: .4rem;
  }}
  .story p {{ margin: 0 0 .7rem; font-size: .95rem; }}
  .story p:first-child {{ font-style: italic; }}
  footer {{
    text-align: center;
    padding: 2rem;
    color: #998;
    font-size: .85rem;
  }}
</style>
</head>
<body>
<header>
  <h1>The Catalogue</h1>
  <p>{count} pieces &mdash; each with its drawing and its story</p>
</header>
<main class="gallery">{cards}
</main>
<footer>Generated from scraped data &middot; illustrations &amp; stories &copy; J. Peterman</footer>
</body>
</html>
"""


def build(scan_dir: Path, out_file: Path):
    out_dir = out_file.resolve().parent
    folders = sorted(p for p in scan_dir.iterdir() if p.is_dir())
    cards = []
    for folder in folders:
        card = build_card(folder, out_dir)
        if card:
            cards.append(card)
    html_doc = PAGE.format(count=len(cards), cards="".join(cards))
    out_file.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {out_file}  ({len(cards)} cards)")


if __name__ == "__main__":
    scan = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("gallery.html")
    build(scan, out)
