#!/usr/bin/env python3
"""Append a dated value snapshot to history/snapshots.json from the current cards.json.
Run after updating market values (e.g. a Card Ladder price refresh), then re-run build.py.
Same-day runs overwrite that day's snapshot. Usage: python refresh_snapshot.py [YYYY-MM-DD]"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
cards = json.load(open(os.path.join(ROOT, "cards.json")))
hp = os.path.join(ROOT, "history", "snapshots.json")
history = json.load(open(hp)) if os.path.exists(hp) else []

date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
total = round(sum((c.get("market_value") or 0) for c in cards), 2)
snap = {"date": date, "total": total, "cards": {str(c["n"]): (c.get("market_value") or 0) for c in cards}}

history = [s for s in history if s.get("date") != date]
history.append(snap)
history.sort(key=lambda s: s["date"])
json.dump(history, open(hp, "w"), indent=1)
print(f"snapshot {date}: total ${total:,.0f} across {len(cards)} cards | history now has {len(history)} point(s)")
