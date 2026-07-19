#!/usr/bin/env python3
"""Flag possible duplicate cards (same player + card #). Run: python check_dupes.py"""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
cards = json.load(open(os.path.join(ROOT, "cards.json")))
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())

groups = {}
for c in cards:
    if (c.get("card_no") or "").strip():
        groups.setdefault((norm(c["player"]), norm(c["card_no"])), []).append(c)

t1, t2 = [], []
for grp in groups.values():
    if len(grp) < 2:
        continue
    for c in grp:
        others = [d for d in grp if d["n"] != c["n"]]
        def compat(a, b):
            pa, pb = norm(a.get("parallel")), norm(b.get("parallel"))
            if pa == pb or (pa and pa in pb) or (pb and pb in pa) or not pa or not pb:
                sa, sb = a.get("serial"), b.get("serial")
                return not (sa and sb and sa != sb)
            return False
        likely = any(compat(c, d) for d in others)
        (t1 if likely else t2).append((c, others))

def line(c):
    return f'#{c["n"]:>3} {c["player"]} — {c.get("set","")} {c.get("parallel","")} {c.get("serial","")} (${c.get("market_value")})'

print("=" * 70)
print("DUPLICATE CHECK")
print("=" * 70)
if t1:
    print("\n⚠  LIKELY DUPLICATES (same player + card # + parallel, matching/blank serial):")
    for c, o in t1:
        print("  " + line(c))
else:
    print("\nNo likely duplicates.")
if t2:
    print("\n•  REVIEW (same player + card #, different parallel/serial — often legit multiples):")
    seen = set()
    for c, o in t2:
        key = tuple(sorted([c["n"]] + [d["n"] for d in o]))
        if key in seen: continue
        seen.add(key)
        print("  " + line(c))
        for d in o:
            print("      ↔ " + line(d))
print(f"\nTotal cards: {len(cards)} | likely dups: {len(t1)} | review pairs: {len(set(tuple(sorted([c['n']]+[d['n'] for d in o])) for c,o in t2))}")
