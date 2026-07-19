// 130point sold-comp matcher for the add-card skill.
//
// Usage (in the in-app browser, via javascript_tool):
//   1. Navigate to https://130point.com/search and let the Cloudflare
//      "Just a moment..." challenge clear (~5s) so fetches inherit clearance.
//   2. Paste this whole file once to define window.p130.
//   3. Call it per card and read the result:
//        await p130("Katie McCabe 2024 Futera Gold", "McCabe", "Superstars", 11, 2024, 0, "")
//
// Args: (query, playerKey, parallelKey, printRun, year, auto, gradeCo)
//   query       broad search string: "<Player> <year> <product> <parallel words>"
//   playerKey   last name to require in the result title (dedupes cross-sport noise)
//   parallelKey one distinctive parallel word to match ("Gold Wave", "Refractor", "Cracked Ice")
//   printRun    the /N number (11, 25, 50...), or 0 if unnumbered
//   year        4-digit year (2024), or 0 to ignore
//   auto        1 if the card is an autograph, else 0
//   gradeCo     "PSA" | "SGC" | "TAG" to require a grade in the title, else ""
//
// Returns one of:
//   {v, lo, hi, k, tier, note}   tier = exact | close | broad; note explains a fallback
//   {v: null, tier: "none"}      no priced comps found
//   {err: 403}                   Cloudflare rate limit -> reload page, wait ~5s, retry
//
// Tiering: exact = parallel + print run + year all match. close = same parallel but the
// exact run/year had no sales, so it falls back to same-run-different-year, then
// same-year-different-run, then same-parallel-any (note records which). broad = the
// parallel never matched, so it's the player's overall median (directional only).
window.p130 = async (q, pk, park, run = 0, year = 0, au = 0, gc = "") => {
  const median = a => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2 * 100) / 100; };
  const mode = a => { const c = {}; let b = null, bn = 0; a.forEach(x => { c[x] = (c[x] || 0) + 1; if (c[x] > bn) { bn = c[x]; b = x; } }); return b; };
  const pR = t => { const s = new Set(); let m, re = /\/\s*(\d{1,4})\b/g; while (m = re.exec(t)) s.add(+m[1]); return s; };
  const pY = t => { const m = t.match(/20\d\d/); return m ? +m[0] : 0; };
  const priceRe = /\$\s*([\d,]+(?:\.\d+)?)\s*USD/g;
  const sold = (c, f) => { const n = [...c.textContent.matchAll(priceRe)].map(m => parseFloat(m[1].replace(/,/g, ''))); if (!n.length) return null; return (n.length >= 2 && /Best Offer/i.test(f)) ? Math.min(n[0], n[1]) : n[0]; };

  const r = await fetch('/api/search/html?q=' + encodeURIComponent(q) + '&sort=recent&mp=all');
  if (!r.ok) return { err: r.status };
  const doc = new DOMParser().parseFromString(await r.text(), 'text/html');
  const all = [...doc.querySelectorAll('[data-sold-result]')].map(c => {
    const t = ((c.querySelector('p.font-bold') || {}).textContent || '').replace(/\s+/g, ' ').trim();
    const f = ([...c.querySelectorAll('p')].map(p => p.textContent).find(x => /Auction|Fixed|Best Offer|Buy/i.test(x)) || '');
    return { t, p: sold(c, f), runs: pR(t), yr: pY(t) };
  }).filter(x => x.p != null);

  const pm = all.filter(x => x.t.toLowerCase().includes(pk.toLowerCase()));
  let cand = pm, hitPar = false;
  if (park) { const h = pm.filter(x => x.t.toLowerCase().includes(park.toLowerCase())); if (h.length) { cand = h; hitPar = true; } }
  if (au) { const a = cand.filter(x => /auto|signature|signed/i.test(x.t)); if (a.length) cand = a; }
  if (gc) { const g = cand.filter(x => x.t.toUpperCase().includes(gc)); if (g.length) cand = g; }

  const runOk = r => run === 0 || r.runs.has(run), yrOk = r => year === 0 || r.yr === year;
  let sel, tier, note = '';
  if (!hitPar) { sel = pm; tier = 'broad'; note = 'no parallel match — broad ' + pk + ' median'; }
  else {
    const exact = cand.filter(r => runOk(r) && yrOk(r));
    if (exact.length) { sel = exact; tier = 'exact'; }
    else {
      const sameRun = run ? cand.filter(r => r.runs.has(run)) : [];
      const sameYr = year ? cand.filter(r => r.yr === year) : [];
      if (sameRun.length) { sel = sameRun; tier = 'close'; const ys = [...new Set(sel.map(r => r.yr).filter(Boolean))]; note = 'closest: /' + run + ' from ' + (ys.join('/') || 'other yr') + (year ? ' (card ' + year + ')' : ''); }
      else if (sameYr.length) { sel = sameYr; tier = 'close'; const mr = mode(sel.flatMap(r => [...r.runs]).filter(x => x <= 500)); note = 'closest: ' + (mr ? '/' + mr : 'other run') + (run ? ' (card /' + run + ')' : ''); }
      else { sel = cand; tier = 'close'; const mr = mode(sel.flatMap(r => [...r.runs]).filter(x => x <= 500)); note = 'closest: same parallel' + (mr ? ' /' + mr : '') + (run ? ' (card /' + run + ')' : ''); }
    }
  }
  const P = sel.map(x => x.p);
  return P.length ? { v: median(P), lo: Math.min(...P), hi: Math.max(...P), k: P.length, tier, note } : { v: null, tier: 'none' };
};
