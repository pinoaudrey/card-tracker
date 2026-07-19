# Card Tracker

A static, browsable value tracker for a women's soccer trading card collection (121 cards).
Open `docs/index.html` locally, or view it live on GitHub Pages.

## What's here
```
cards.json              # source of truth: one record per card (id, price, comps, notes)
build.py                # generates the docs/ site from cards.json (stdlib only)
ingest_images.py        # convert card photos into docs/images/ (HEIC via macOS `sips`)
refresh_snapshot.py     # logs a dated value snapshot to history/
check_dupes.py          # flags possible duplicate cards
history/snapshots.json  # value-over-time history (one point per refresh)
.claude/skills/add-card # Claude Code skill: identify, price, and add a card
docs/                   # the generated site (this is what GitHub Pages serves)
  index.html            #   gallery + collection value chart
  cards/<n>.html        #   one detail page per card (big images, comps, price history)
  images/               #   front/back photos
  assets/               #   shared CSS + JS
```

## Using the tracker
- **Gallery** (`docs/index.html`): search/sort, Collection / Sold / All views with running totals, and a collection value-over-time chart.
- **Click any card** → detail page: large front/back images, full card data, every recent comp, a per-card value-history chart, and the cost/sale editor.
- **Cost & sale** (accordion on each gallery card, or on the detail page): enter **Paid**, tick **Mark as sold**, enter **Sold for**. P/L (unrealized → realized) updates live.
- **Saved locally:** your Paid/Sold entries live in the browser (localStorage). Use **Export** to back them up to `card_edits.json` and **Import** to restore (e.g. moving between the old single-file gallery and this one, or across devices).

## Common tasks
```bash
python build.py            # regenerate the site after editing cards.json
python check_dupes.py      # report likely duplicates / same player+card# to review
python refresh_snapshot.py # append today's values to history, then re-run build.py
```

### Adding a card
Drop the card's photo(s) and use the **`add-card`** skill (`.claude/skills/add-card/`) — it walks through
ingesting the images, identifying the card, checking Card Ladder comps, pricing it, appending to
`cards.json`, and rebuilding. Or do it by hand: `python ingest_images.py <photos>`, add a row to
`cards.json`, then `python build.py`.

### Refreshing prices
1. Update `market_value` (and comps) in `cards.json` — re-check Card Ladder for recent sales.
2. `python refresh_snapshot.py` to log a dated snapshot (same-day runs overwrite).
3. `python build.py` to regenerate the charts and pages.

The Card Ladder search technique (for a future `add-card` skill): set the search box value, read the results dropdown **on a separate step** (it debounces), use **broad** queries — parallel words like *cracked ice* / *sunset* aren't indexed. Graded SGC/TAG trade a bit under PSA.

## GitHub Pages
`.github/workflows/deploy.yml` rebuilds the site and deploys `docs/` on every push to `main`.
Pages for a **private** repo needs a paid GitHub plan (Pro/Team); on the free plan, either keep it local (`docs/index.html`) or make the repo public — but note the pages embed personal card photos.

## Pricing
Two independent sources per card:
- **Card Ladder** (the green value) — the primary market estimate, with a confidence flag (**high** = exact-parallel comp, **medium/low** = estimated). See each card's notes.
- **130pt** — the median of matched sold listings from [130point](https://130point.com) (eBay + auction houses), pulled via its search API. A **~** means the parallel match was loose or thin (e.g. a graded card's median got mixed with raw copies, or an auto with base) — treat those as rough. The detail page shows the sold-count and low–high range so you can judge. Where the two sources agree, confidence is high; where they diverge, it's a card worth a manual look (e.g. #34 Russo Orange /25).

## To verify
- Miedema 2021-22 #10 print run (read as /75; only /25 comps exist).
- `check_dupes.py` flags a couple of likely cross-batch re-shoots (Gwinn #22, Athenea #24) — confirm before trusting the count.
