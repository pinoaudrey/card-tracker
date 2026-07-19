#!/usr/bin/env python3
"""Generate an eBay bulk-upload CSV from cards.json.

Produces exports/ebay_listings.csv in eBay's File Exchange flat-file format for
Sports Trading Card Singles (category 261328). Review it in Seller Hub
(Reports > Upload, or the bulk listing tool) before anything goes live —
nothing here touches eBay directly.

    python ebay_export.py                       # default: higher end (max of the 3 sources)
    python ebay_export.py --price market_value  # Card Ladder point estimate only
    python ebay_export.py --price point130      # 130pt median only
    python ebay_export.py --only 7,50,91        # just these card numbers

Fill in the CONFIG block below first (shipping/return/payment policy names,
your item location, and an image base URL if your photos are hosted somewhere
public). Anything left blank you finish in Seller Hub on review.
"""
import argparse, csv, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))

# Notion "Values (Card Ladder)" recent-avg/low/high per card, keyed by n.
# Used by PRICE_SOURCE="high" (list at the top of the value range). Optional.
try:
    NOTION = {int(k): v for k, v in json.load(open(os.path.join(ROOT, "notion_values.json"))).items()}
except FileNotFoundError:
    NOTION = {}

# ------------------------------------------------------------------ CONFIG ---
CATEGORY_ID = "261328"          # Sports Trading Card Singles (soccer = Sport aspect)
# "high" = the higher end: max(Card Ladder, 130pt, Notion High). Others:
# "market_value" (Card Ladder) | "point130" | "max" (of Card Ladder + 130pt).
PRICE_SOURCE = "high"
MARKUP = 1.0                    # multiply the estimate (e.g. 1.10 for +10%)
MIN_PRICE = 0.99                # eBay floor
QUANTITY = 1
DURATION = "GTC"                # Good-'Til-Cancelled (required for FixedPrice)

# Your account specifics. Blank = leave the column empty and finish in Seller Hub.
LOCATION_ZIP = "64102"          # Kansas City, MO
SHIPPING_POLICY = "Cards - package"   # named business-policy titles from your eBay account
RETURN_POLICY = "No returns"          # must match a "returns not accepted" policy in your account
PAYMENT_POLICY = "Cards - immediate"  # must match your payment policy name exactly

# Photos: eBay needs public HTTPS image URLs. The repo images are local/private,
# so this is blank by default and you add photos per row in Seller Hub. If you
# host docs/images somewhere public, set the base URL (no trailing slash).
IMAGE_BASE_URL = "https://raw.githubusercontent.com/pinoaudrey/card-tracker/main/docs/images"

# Ungraded cards need a Card Condition descriptor. Leave "" to pick per card in
# Seller Hub, or set a default you're comfortable asserting for the batch.
DEFAULT_UNGRADED_CONDITION = "" # e.g. "Near Mint or Better"
# ---------------------------------------------------------------------------

GRADERS = ("PSA", "SGC", "TAG", "BGS", "CGC", "CSG")
GENERIC_SUBSETS = {"autograph", "autographs", "chrome autograph", "base",
                   "chrome premium autograph relic", "future stars autograph",
                   "future stars autographs", "chrome autograph (rc)"}


def money(v):
    if v is None:
        return None
    return round(max(float(v) * MARKUP, MIN_PRICE), 2)


def pick_price(c):
    mv = c.get("market_value")
    p130 = (c.get("point130") or {}).get("v")
    if PRICE_SOURCE == "point130":
        return money(p130 if p130 is not None else mv)
    if PRICE_SOURCE == "high":  # the higher end: top of every value signal
        nhi = (NOTION.get(c["n"]) or {}).get("hi")
        vals = [x for x in (mv, p130, nhi) if x is not None]
        return money(max(vals)) if vals else None
    if PRICE_SOURCE == "max":
        vals = [x for x in (mv, p130) if x is not None]
        return money(max(vals)) if vals else None
    return money(mv if mv is not None else p130)


def manufacturer(setname):
    for m in ("Topps", "Panini", "Futera"):
        if setname.startswith(m):
            return m
    return setname.split(" ")[0] if setname else ""


def product_and_subset(setname):
    parts = [p.strip() for p in setname.split("—")]  # em-dash separates subset
    product = parts[0]
    subset = parts[1] if len(parts) > 1 else ""
    subset = re.sub(r"\s*\((RC|SSP[^)]*|Case Hit[^)]*)\)", "", subset).strip()
    return product, subset


def parse_grade(grade):
    """'SGC 9.5' -> ('SGC','9.5'); 'Raw' -> (None,None)."""
    if not grade or grade.strip().lower() == "raw":
        return None, None
    g = grade.split("(")[0].strip()
    grader = next((x for x in GRADERS if g.upper().startswith(x)), None)
    num = re.search(r"\d+(?:\.\d+)?", g)
    return grader, (num.group(0) if num else None)


def print_run(c):
    """Denominator of the serial or a '/N' in the parallel (50 from '40/50')."""
    for src in (c.get("serial", ""), c.get("parallel", "")):
        m = re.search(r"/\s*0*(\d+)", src)
        if m:
            return m.group(1)
    return ""


def clean_parallel(parallel):
    return re.sub(r"\s*/\s*\d+\s*$", "", parallel or "").strip()


def player_name(c):
    return re.sub(r"\s*\([^)]*\)", "", c.get("player", "")).strip()


def club(c):
    return (c.get("team", "") or "").split("/")[0].strip()


def primary_feature(c):
    if c.get("auto"):
        return "Autograph"
    if print_run(c):
        return "Serial Numbered"
    if c.get("relic"):
        return "Memorabilia"
    if "(RC)" in c.get("set", ""):
        return "Rookie"
    if "Refractor" in (c.get("parallel", "") or ""):
        return "Refractor"
    return ""


def variety(c):
    """Parallel/Variety aspect: the parallel, else a real (non-generic) subset."""
    par = clean_parallel(c.get("parallel", ""))
    if par:
        return par
    _, subset = product_and_subset(c.get("set", ""))
    return "" if subset.lower() in GENERIC_SUBSETS else subset


def build_title(c):
    """<=80 chars, most-searchable tokens first, drop the tail if over.

    Words already in the title are dropped from later tokens so we don't get
    'Helix Helix' or a doubled 'Chrome'."""
    product, subset = product_and_subset(c.get("set", ""))
    grader, gnum = parse_grade(c.get("grade", ""))
    run = print_run(c)
    tokens = [
        player_name(c),
        str(c.get("year", "")),
        product,
        "" if subset.lower() in GENERIC_SUBSETS else subset,
        variety(c),
        f"/{run}" if run else "",
        "Auto" if c.get("auto") else "",
        f"#{c['card_no']}" if c.get("card_no") else "",
        f"{grader} {gnum}" if grader else "",
    ]
    title, seen = "", set()
    for t in tokens:
        words = [w for w in t.split() if w.lower() not in seen or w.startswith(("/", "#"))]
        t = " ".join(words).strip()
        if not t:
            continue
        cand = (title + " " + t).strip()
        if len(cand) <= 80:
            title = cand
            seen.update(w.lower() for w in words)
    return title


def build_description(c):
    product, subset = product_and_subset(c.get("set", ""))
    grader, gnum = parse_grade(c.get("grade", ""))
    run = print_run(c)
    bits = [f"{c.get('year','')} {c.get('set','')}".strip(),
            f"{player_name(c)} ({club(c)})" if club(c) else player_name(c)]
    line2 = []
    if clean_parallel(c.get("parallel", "")):
        line2.append(clean_parallel(c["parallel"]))
    if c.get("serial"):
        line2.append(f"serial-numbered {c['serial']}")
    elif run:
        line2.append(f"numbered to /{run}")
    if c.get("auto"):
        line2.append("on-card/sticker autograph")
    if c.get("relic"):
        line2.append("memorabilia relic")
    if grader:
        line2.append(f"graded {grader} {gnum}")
    desc = ". ".join(bits)
    if line2:
        desc += ". " + ", ".join(line2).capitalize() + "."
    desc += " Ships securely in a penny sleeve + top-loader (graded slabs in a protective case), tracked. See photos for exact condition."
    return desc


COLUMNS = [
    "*Action(SiteID=US|Country=US|Currency=USD|CC=UTF-8)",
    "CustomLabel", "*Category", "*Title", "*Description", "*ConditionID",
    "PicURL", "*Quantity", "*Format", "*StartPrice", "*Duration",
    "Location", "ShippingProfileName", "ReturnProfileName", "PaymentProfileName",
    "C:Sport", "C:Player/Athlete", "C:Season", "C:Set", "C:Manufacturer",
    "C:Card Number", "C:Parallel/Variety", "C:Team", "C:Features",
    "C:Autographed", "C:Type", "C:Original/Licensed Reprint",
    "Professional Grader", "Grade", "Certification Number", "Card Condition",
]


def row_for(c):
    grader, gnum = parse_grade(c.get("grade", ""))
    graded = grader is not None
    product, subset = product_and_subset(c.get("set", ""))
    run = print_run(c)
    price = pick_price(c)
    pics = ""
    if IMAGE_BASE_URL:
        pics = "|".join(f"{IMAGE_BASE_URL}/{c[k]}.jpg" for k in ("front", "back") if c.get(k))
    return {
        "*Action(SiteID=US|Country=US|Currency=USD|CC=UTF-8)": "Add",
        "CustomLabel": f"CARD-{c['n']}",
        "*Category": CATEGORY_ID,
        "*Title": build_title(c),
        "*Description": build_description(c),
        "*ConditionID": "2750" if graded else "4000",
        "PicURL": pics,
        "*Quantity": QUANTITY,
        "*Format": "FixedPrice",
        "*StartPrice": price if price is not None else "",
        "*Duration": DURATION,
        "Location": LOCATION_ZIP,
        "ShippingProfileName": SHIPPING_POLICY,
        "ReturnProfileName": RETURN_POLICY,
        "PaymentProfileName": PAYMENT_POLICY,
        "C:Sport": "Soccer",
        "C:Player/Athlete": player_name(c),
        "C:Season": str(c.get("year", "")),
        "C:Set": product,
        "C:Manufacturer": manufacturer(c.get("set", "")),
        "C:Card Number": c.get("card_no", ""),
        "C:Parallel/Variety": variety(c),
        "C:Team": club(c),
        "C:Features": primary_feature(c),
        "C:Autographed": "Yes" if c.get("auto") else "No",
        "C:Type": "Sports Trading Card",
        "C:Original/Licensed Reprint": "Original",
        "Professional Grader": grader or "",
        "Grade": gnum or "",
        "Certification Number": "",
        "Card Condition": "" if graded else DEFAULT_UNGRADED_CONDITION,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", choices=("high", "market_value", "point130", "max"))
    ap.add_argument("--only", help="comma-separated card numbers")
    args = ap.parse_args()
    global PRICE_SOURCE
    if args.price:
        PRICE_SOURCE = args.price

    cards = json.load(open(os.path.join(ROOT, "cards.json")))
    if args.only:
        keep = {int(x) for x in args.only.split(",")}
        cards = [c for c in cards if c["n"] in keep]

    os.makedirs(os.path.join(ROOT, "exports"), exist_ok=True)
    out = os.path.join(ROOT, "exports", "ebay_listings.csv")
    no_price, long_titles, graded = [], [], []
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for c in cards:
            r = row_for(c)
            w.writerow(r)
            if r["*StartPrice"] == "":
                no_price.append(c["n"])
            if len(r["*Title"]) >= 80:
                long_titles.append(c["n"])
            if r["Professional Grader"]:
                graded.append(c["n"])

    print(f"wrote {out}  ({len(cards)} listings, price source: {PRICE_SOURCE})")
    if no_price:
        print(f"  ! no price ({len(no_price)}): {no_price} — set manually before listing")
    if graded:
        print(f"  i graded ({len(graded)}): {graded} — add Certification Number in Seller Hub")
    if not IMAGE_BASE_URL:
        print("  i PicURL blank — add photos per row in Seller Hub (or set IMAGE_BASE_URL)")
    if not (LOCATION_ZIP and SHIPPING_POLICY):
        print("  i fill Location + shipping/return/payment policies (CONFIG) or set them on review")


if __name__ == "__main__":
    main()
