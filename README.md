# Card Tracker

A self-contained gallery + value tracker for a women's soccer trading card collection (121 cards).

## Files
- **`card_collection_gallery.html`** — the tracker. Open it in any browser; it works offline. Front/back photos are embedded, so it's a single portable file (~13 MB).
- **`cards.json`** — the underlying data: per-card identification, market estimate, last sale, recent Card Ladder comps, and a confidence flag.

## Using the gallery
- **Views:** Collection / Sold / All, each with running totals (cost basis, market value, realized/unrealized P/L).
- **Search & sort** by player / set / team, by value, or by P/L.
- **Cost & sale** (accordion on each card, collapsed by default): enter what you **Paid**, tick **Mark as sold**, and enter what you **Sold for**. P/L updates live.
- **Saved locally:** your Paid / Sold entries live in the browser (localStorage). Use **Export edits** to back them up to `card_edits.json`, and **Import edits** to restore them (e.g. on another device or after clearing browser data).

## Pricing
Estimates come from recent Card Ladder sale comps. Each card carries a confidence flag:
- **high** — an exact-parallel sale comp existed.
- **medium / low** — estimated from sibling parallels or thin/old comps (mostly numbered base parallels with no direct sales). See each card's `notes`.

## To verify
- Miedema 2021-22 #10 print run (read as /75; only /25 comps exist — value swings a lot).
- Possible duplicate cards across photo batches (e.g. Athenea del Castillo #24 cracked ice) — confirm before trusting the total count.
