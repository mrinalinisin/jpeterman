#!/usr/bin/env python3
"""Crawl a J. Peterman (Shopify) collection and save each product's
hand-drawn illustrations plus its narrative story.

Usage:
    python3 crawl.py                          # default womens-sale-dresses-1
    python3 crawl.py <collection-handle>      # any collection
    python3 crawl.py <collection-handle> out  # custom output dir
    python3 crawl.py --drawings-only          # keep only positions 01-02

Output layout:
    <out>/<product-handle>/story.md
    <out>/<product-handle>/<product-handle>-01.jpg
    <out>/<product-handle>/<product-handle>-02.jpg
    ...
"""
import argparse
import html
import json
import re
import time
import urllib.request
from pathlib import Path

DRAWING_POSITIONS = (1, 2)  # 01 = color gouache, 02 = ink sketch

STORE = "https://jpeterman.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (collection-crawler; polite)"}
PAGE_LIMIT = 250  # Shopify max per page


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_products(collection: str):
    """Yield every product dict in a collection, paginating until empty."""
    page = 1
    while True:
        url = f"{STORE}/collections/{collection}/products.json?limit={PAGE_LIMIT}&page={page}"
        products = json.loads(fetch(url))["products"]
        if not products:
            return
        yield from products
        page += 1
        time.sleep(0.5)  # be polite


def html_to_text(body_html: str) -> str:
    """Turn the body_html into readable plain text, one blank line per <p>."""
    text = re.sub(r"(?i)</p\s*>", "\n\n", body_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)          # strip remaining tags
    text = html.unescape(text)                    # decode &amp; &rsquo; etc.
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse extra blank lines
    return text.strip()


def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def crawl(collection: str, out_dir: Path, drawings_only: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in fetch_products(collection):
        handle = p["handle"]
        pdir = out_dir / safe(handle)
        pdir.mkdir(parents=True, exist_ok=True)

        story = html_to_text(p.get("body_html") or "")
        (pdir / "story.md").write_text(f"# {p['title']}\n\n{story}\n", encoding="utf-8")

        images = sorted(p.get("images", []), key=lambda i: i.get("position", 0))
        if drawings_only:
            images = [i for i in images if i.get("position", 0) in DRAWING_POSITIONS]
        for img in images:
            src = img["src"].split("?")[0]
            ext = Path(src).suffix or ".jpg"
            fname = f"{safe(handle)}-{img.get('position', 0):02d}{ext}"
            dest = pdir / fname
            if dest.exists():
                continue
            try:
                dest.write_bytes(fetch(img["src"]))
            except Exception as e:
                print(f"  ! failed image {src}: {e}")
            time.sleep(0.2)

        count += 1
        print(f"[{count}] {p['title']}  ->  {pdir}  ({len(images)} images)")
    label = " (drawings only)" if drawings_only else ""
    print(f"\nDone. {count} products saved under {out_dir}/{label}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Crawl a J. Peterman (Shopify) collection.")
    ap.add_argument("collection", nargs="?", default="womens-sale-dresses-1",
                    help="collection handle (default: womens-sale-dresses-1)")
    ap.add_argument("out", nargs="?", default="output",
                    help="output directory (default: output)")
    ap.add_argument("--drawings-only", action="store_true",
                    help="save only the illustration images (positions 01-02)")
    args = ap.parse_args()
    crawl(args.collection, Path(args.out), drawings_only=args.drawings_only)
