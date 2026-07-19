---
name: add-card
description: Add a trading card to the card-tracker. Use when someone drops one or more card photos (front/back, HEIC or JPG) and wants the card identified, priced from recent Card Ladder sale comps, and added to cards.json + the gallery. Covers photo ingest, identification, the Card Ladder comp-search technique and its gotchas, pricing + confidence, the cards.json schema, and rebuilding the site. Trigger on "add this card", "price this card", "add to the tracker", or a card photo dropped in the card-tracker repo.
---

# Add a card to the tracker

Pipeline: **ingest photos → identify → check comps on Card Ladder → price → append to `cards.json` → rebuild**. Work from the repo root (where `build.py` lives).

## 1. Ingest the photos
Convert each photo into a site image and note its name:
```bash
python ingest_images.py /path/to/IMG_front.HEIC /path/to/IMG_back.HEIC
```
It writes `docs/images/<basename>.jpg` and prints the names. Keep track of which is **front** and which is **back**. If only one photo was provided, use it as `front` and leave `back` empty.

## 2. Identify the card
Read the front and back and capture:
- **player, team** (club, plus country for a national-team card)
- **year** (e.g. `2024-25`, `2025-26`, `2025`) — read the back copyright / set line
- **set** — product + insert/subset, e.g. `Topps Chrome UWCL — Autographs`, `Topps Now UWCL #23`, `Panini Obsidian — Color Blast (SSP)`
- **card_no** (e.g. `AV-CGH`, `H-6`, `23`) — blank for many autos/inserts
- **parallel** — color/finish + print run, e.g. `Gold Wave Refractor`, `Orange Cracked Ice`, `Black /10`
- **serial** — e.g. `16/50`, `/99`, or blank if unnumbered
- **auto** / **relic** — booleans (visible signature / memorabilia swatch)
- **grade** — `Raw`, or a slab grade like `SGC 10`, `PSA 9`, `TAG 10` (the slab label carries year/set/parallel/serial/cert)

## 3. Check comps on Card Ladder
The user is logged in at `app.cardladder.com`. In the browser:
1. `read_page` to find the search **textbox** (`type="search"`), grab its `ref`.
2. Set the query with `form_input` on that ref.
3. **Read the results on the NEXT step** with `get_page_text` — the search debounces, so a same-step read returns stale/empty results.
4. Read the "Sales History" rows (title / date / price) from the returned text.

Query rules (important):
- Use **broad** queries: `"<Player> <product>"` or `"<Player> <set word>"` (e.g. `Lauren Hemp Chrome`, `Chloe Kelly Topps Now`).
- **Do NOT** put parallel words in the query — `cracked ice`, `sunset`, `gold cracked ice`, etc. are **not indexed** and return "No results". Filter for the parallel yourself in the returned rows.
- If a query returns nothing, broaden it (drop the parallel/serial, keep player + product).
- One broad search often covers several of a player's cards at once.

## 3b. Cross-check on 130point (second source)
Card Ladder is the primary value; 130point (eBay + auction-house sold listings) is an independent sanity check. It ships as the `point130` field and the `130pt` number on the site.

1. Navigate the browser to `https://130point.com/search`. Wait for the Cloudflare **"Just a moment..."** challenge to clear (~5s, title becomes "130 Point") so in-page fetches inherit clearance.
2. Paste the contents of **`p130.js`** (in this skill folder) via `javascript_tool` once, to define `window.p130`.
3. Call it for the card and read the result on the **next** step:
   ```js
   await p130("<Player> <year> <product> <parallel words>", "<LastName>", "<ParallelWord>", <printRun|0>, <year|0>, <auto 0|1>, "<PSA|SGC|TAG|"">")
   ```
   e.g. `await p130("Katie McCabe 2024 Futera Gold", "McCabe", "Superstars", 11, 2024, 0, "")`.
4. It returns `{v, lo, hi, k, tier, note}` (tier = `exact` | `close` | `broad`), or `{v:null, tier:"none"}` if nothing matched. Store it verbatim as the card's `point130` (drop `note` when empty; use `null` for `none`).

Rules:
- Unlike Card Ladder, the **130point query CAN include parallel words** — its search indexes them. Still keep `parallelKey` to one distinctive word.
- **Tiers**: `exact` = parallel + run + year all matched; `close` = same parallel but the exact run/year had no sales (the `note` says what it fell back to, e.g. `/50 (card /75)`); `broad` = parallel never matched, so it's the player's overall median (directional only). This tiering is the point of the second source — a `close`/`broad` value with an honest note beats a fake-precise number.
- **Rate limit**: after ~150 API hits Cloudflare returns `{err:403}`. Reload `https://130point.com/search`, wait ~5s for the challenge to clear, then continue. For a bulk re-run, throttle to sequential calls (~180ms apart), not `Promise.all`.
- If `v` is far from Card Ladder on an `exact` match, note it (it's a genuine divergence worth flagging, not a matching artifact).

## 4. Price it + set confidence
- **market_value**: the most recent sale of the **exact** parallel + print run. If there's no exact comp, estimate from sibling parallels (scale by rarity: a `/50` sits below a `/25`, above a `/99`), and lower the confidence.
- **Graded**: SGC / TAG / CGC trade a bit **under** PSA. Price off PSA 10/9 comps and shade down.
- **confidence**: `high` = exact-parallel comp existed; `medium`/`low` = estimated or thin/old comps. Never invent a precise number for a card with no comps — estimate and say so in `notes`.
- **comps**: keep 3–5 as strings like `"Gold Wave Auto /50 — $122.50 (Jul 10, 2026)"`.

## 5. Append to cards.json
Use the next `n` (current max + 1). Record schema (match existing rows):
```json
{
  "n": 122,
  "front": "IMG_1234", "back": "IMG_1235",
  "player": "Full Name", "team": "Club / Country",
  "year": "2024-25", "set": "Topps Chrome UWCL — Autographs",
  "card_no": "AV-XX", "parallel": "Gold Refractor", "serial": "16/50",
  "auto": true, "relic": false, "grade": "Raw",
  "market_value": 42, "last_sale": 40, "last_sale_date": "2026-04-20",
  "comps": ["Gold /50 — $40.00 (Apr 20, 2026)", "Black /10 — $52.00 (Feb 4, 2026)"],
  "notes": "Short note; flag any estimate or thing to verify.",
  "confidence": "high",
  "point130": {"v": 44, "lo": 38, "hi": 61, "k": 5, "tier": "exact"}
}
```
Fields: `market_value` / `last_sale` are numbers (or `null`); `comps` is an array; `auto`/`relic` are booleans. `front`/`back` are the image basenames (no `.jpg`). `point130` is the object returned by `p130()` (step 3b), or `null` if no comps matched — include its `note` string only when it's a `close`/`broad` match.

## 6. Rebuild
```bash
python check_dupes.py       # did this clash with an existing card (same player + card #)?
python refresh_snapshot.py  # optional: log the new collection total to history/
python build.py             # regenerate index + detail pages
```
Then open `docs/index.html` (or the new `docs/cards/<n>.html`) to confirm, and commit if the user wants it in the repo.

## Gotchas (hard-won)
- **Search debounce** (Card Ladder) — always `form_input` then read on the *next* step.
- **Parallel words aren't searchable on Card Ladder** — broad player+product queries only. (130point is the opposite: it *does* index parallel words.)
- **SGC/TAG < PSA** — shade graded values down from PSA comps.
- **No-comp base parallels are common** — estimate + `low` confidence, don't fake precision.
- **Duplicates** — the same player + card # across photo batches may be a re-shoot, not a second card. Run `check_dupes.py`; if it's a genuine duplicate, don't add it.
- **130point Cloudflare** — you must load `https://130point.com/search` in the browser and let the challenge clear before `p130()` works; `{err:403}` means you've been rate-limited (~150 hits), so reload + wait ~5s. Run `p130` calls in-page (`javascript_tool`), never as an external fetch — they need the browser's Cloudflare clearance.
