# J. Peterman Gallery

A small toolkit that crawls a [J. Peterman](https://www.jpeterman.com) Shopify
collection and builds a card-style web gallery pairing each product's
hand-drawn illustration with its narrative "story."

🔗 **Live gallery:** https://mrinalinisin.github.io/jpeterman

## Scripts

| Script | What it does |
|---|---|
| `crawl.py` | Crawls a collection via Shopify's `products.json` API and saves each product's illustrations + `story.md` into `output/<handle>/`. |
| `gallery.py` | Scans `output/` and generates a self-contained `index.html` masonry gallery. |

```bash
python3 crawl.py all-womens output       # scrape a collection
python3 gallery.py output index.html     # build the gallery page
```

## Disclaimer

This project is an **unofficial, non-commercial** experiment for personal and
educational use only. **All product illustrations and story/description text are
the property of The J. Peterman Company** and are reproduced here solely to
demonstrate the scraping and gallery-building code.

This repository is **not affiliated with, authorized, endorsed by, or sponsored
by The J. Peterman Company**. All trademarks, artwork, and copy remain the
property of their respective owner. Content was retrieved from publicly
accessible pages on jpeterman.com. If you are the rights holder and want this
content removed, please open an issue.
