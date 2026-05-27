#!/usr/bin/env python3
"""Build a card-style HTML gallery from a crawled J. Peterman collection.

Reads the folders produced by crawl.py (each holds a story.md plus
<handle>-NN.jpg illustrations) and writes a single self-contained HTML page.

The gallery is a masonry card grid rendered in batches: only the first
BATCH cards exist in the DOM at load, and each "Show me more" click appends
the next batch. Images for un-rendered cards are never requested, so a
large collection stays light until the visitor asks for more.

Usage:
    python3 gallery.py                       # scan ./output -> gallery.html
    python3 gallery.py output-drawings       # scan a different dir
    python3 gallery.py output index.html     # name it for a Pages site root
"""
import json
import os
import re
import sys
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
BATCH = 12  # cards revealed per "Show me more" click


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


def build_record(folder: Path, out_dir: Path):
    """Return a compact dict for one product, or None to skip."""
    story_md = folder / "story.md"
    if not story_md.exists():
        return None
    images = find_images(folder)
    if not images:
        return None
    title, paras = parse_story(story_md)
    srcs = [os.path.relpath(img, out_dir) for img in images]
    # keys kept short to keep the embedded JSON small: t=title, s=story, i=images
    return {"t": title, "s": paras, "i": srcs}


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
  header h1 {{ font-size: 2.6rem; letter-spacing: .04em; margin: 0 0 .3rem; }}
  header p {{ margin: 0; font-style: italic; color: var(--accent); }}
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
  .art {{ position: relative; background: #fff; padding: 1rem 1rem 0; }}
  .art img {{ display: block; width: 100%; height: auto; }}
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
  .more-wrap {{ text-align: center; padding: 1rem 1rem 4rem; }}
  #count {{ display: block; margin-bottom: 1rem; color: #998; font-style: italic; }}
  #more {{
    font-family: inherit;
    font-size: 1.05rem;
    color: var(--paper);
    background: var(--accent);
    border: none;
    padding: .8rem 2.2rem;
    cursor: pointer;
    letter-spacing: .03em;
    transition: opacity .2s ease;
  }}
  #more:hover {{ opacity: .85; }}
  footer {{ text-align: center; padding: 2rem; color: #998; font-size: .85rem; }}
</style>
</head>
<body>
<header>
  <h1>The Catalogue</h1>
  <p>{total} pieces &mdash; each with its drawing and its story</p>
</header>
<main id="gallery" class="gallery"></main>
<div class="more-wrap">
  <span id="count"></span>
  <button id="more" type="button">Show me more</button>
</div>
<footer>Generated from scraped data &middot; illustrations &amp; stories &copy; J. Peterman</footer>

<script>
const DATA = {data_json};
const BATCH = {batch};
const gallery = document.getElementById('gallery');
const moreBtn = document.getElementById('more');
const countEl = document.getElementById('count');
let shown = 0;

function makeCard(p) {{
  const card = document.createElement('article');
  card.className = 'card';

  const art = document.createElement('div');
  art.className = 'art' + (p.i.length > 1 ? ' has-flip' : '');
  const front = document.createElement('img');
  front.className = 'front';
  front.loading = 'lazy';
  front.alt = p.t;
  front.src = p.i[0];
  art.appendChild(front);
  if (p.i.length > 1) {{
    const back = document.createElement('img');
    back.className = 'back';
    back.loading = 'lazy';
    back.alt = p.t + ' sketch';
    back.src = p.i[1];
    art.appendChild(back);
  }}

  const body = document.createElement('div');
  body.className = 'body';
  const h = document.createElement('h2');
  h.textContent = p.t;            // textContent => no HTML injection
  body.appendChild(h);
  const story = document.createElement('div');
  story.className = 'story';
  p.s.forEach(function (para) {{
    const el = document.createElement('p');
    el.textContent = para;
    story.appendChild(el);
  }});
  body.appendChild(story);

  card.appendChild(art);
  card.appendChild(body);
  return card;
}}

function showMore() {{
  const next = DATA.slice(shown, shown + BATCH);
  const frag = document.createDocumentFragment();
  next.forEach(function (p) {{ frag.appendChild(makeCard(p)); }});
  gallery.appendChild(frag);
  shown += next.length;
  countEl.textContent = 'Showing ' + shown + ' of ' + DATA.length;
  if (shown >= DATA.length) moreBtn.style.display = 'none';
}}

moreBtn.addEventListener('click', showMore);
showMore();  // initial batch
</script>
</body>
</html>
"""


def build(scan_dir: Path, out_file: Path):
    out_dir = out_file.resolve().parent
    folders = sorted(p for p in scan_dir.iterdir() if p.is_dir())
    records = [r for r in (build_record(f, out_dir) for f in folders) if r]

    # json.dumps handles all escaping; neutralize "</script>" just in case a
    # story ever contains that literal, so it can't terminate the script block.
    data_json = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")

    html_doc = PAGE.format(total=len(records), data_json=data_json, batch=BATCH)
    out_file.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {out_file}  ({len(records)} cards, {BATCH}/batch)")


if __name__ == "__main__":
    scan = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("gallery.html")
    build(scan, out)
