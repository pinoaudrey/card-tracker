#!/usr/bin/env python3
"""Build the static Card Tracker site into docs/ from cards.json + history/ + docs/images/.
No external deps beyond the standard library. Run: python build.py"""
import os, json, html, re, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
cards = json.load(open(os.path.join(ROOT, "cards.json")))
cards.sort(key=lambda c: c["n"])
try:
    history = json.load(open(os.path.join(ROOT, "history", "snapshots.json")))
except Exception:
    history = []

def esc(s): return html.escape(str(s if s is not None else ""))
def money(v):
    if v is None: return "&mdash;"
    return "$%s" % (f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}")

# ---------- duplicate detection ----------
def norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())
groups = {}
for c in cards:
    if not (c.get("card_no") or "").strip():
        continue
    groups.setdefault((norm(c["player"]), norm(c["card_no"])), []).append(c)
def compat(a, b):
    """True when a and b could be the SAME physical card (re-shoot): one parallel
    describes/contains the other (or is blank), and they aren't two distinct numbered copies."""
    pa, pb = norm(a.get("parallel")), norm(b.get("parallel"))
    if pa == pb or (pa and pa in pb) or (pb and pb in pa) or not pa or not pb:
        sa, sb = a.get("serial"), b.get("serial")
        if sa and sb and sa != sb:
            return False  # two different serials -> intentional separate copies
        return True
    return False
dupinfo = {c["n"]: {"tier": 0, "partners": []} for c in cards}
for grp in groups.values():
    if len(grp) < 2:
        continue
    for c in grp:
        partners = [d for d in grp if d["n"] != c["n"]]
        t1 = any(compat(c, d) for d in partners)
        dupinfo[c["n"]] = {
            "tier": 1 if t1 else 2,
            "partners": [{"n": d["n"], "player": d["player"], "parallel": d.get("parallel", ""),
                          "serial": d.get("serial", "")} for d in partners]
        }

def card_series(n):
    return [{"date": s["date"], "value": s.get("cards", {}).get(str(n))} for s in history]

total_value = sum((c.get("market_value") or 0) for c in cards)

# ============================================================ ASSETS
STYLE = r"""
:root{--bg:#0f1115;--panel:#171a21;--panel2:#1e222b;--line:#2a2f3a;--text:#e8eaed;
  --muted:#9aa3af;--accent:#4ade80;--accent2:#38bdf8;--warn:#fbbf24;--red:#f87171;--chip:#252a34}
@media (prefers-color-scheme:light){:root{--bg:#f5f6f8;--panel:#fff;--panel2:#f0f2f5;--line:#e2e5ea;
  --text:#171a21;--muted:#5b6472;--chip:#eef1f5}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2);text-decoration:none}
header{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--line);
  padding:12px 20px;display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
header h1{font-size:18px;margin:0;font-weight:800}
header h1 a{color:var(--text)}
.stat{display:flex;flex-direction:column;line-height:1.15}
.stat .k{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.stat .v{font-size:16px;font-weight:700}
.grow{flex:1}
.tabs{display:inline-flex;background:var(--panel2);border:1px solid var(--line);border-radius:9px;overflow:hidden}
.tabs button{background:transparent;border:none;color:var(--muted);padding:7px 13px;font-size:13px;font-weight:600;cursor:pointer}
.tabs button.on{background:var(--accent);color:#0b0b0b}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input[type=search],select{background:var(--panel2);color:var(--text);border:1px solid var(--line);
  border-radius:8px;padding:8px 11px;font-size:14px}
input[type=search]{min-width:190px}
.lnk{background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:8px;
  padding:8px 11px;font-size:12.5px;font-weight:600;cursor:pointer}
main{padding:20px;max-width:1400px;margin:0 auto}
.banner{background:#3a2e12;color:var(--warn);border:1px solid var(--warn);border-radius:8px;
  padding:9px 13px;font-size:12.5px;margin-bottom:16px}
.pcard{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:18px}
.pcard h2{margin:0 0 4px;font-size:14px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;display:flex;flex-direction:column}
.card.issold{border-color:var(--accent2)}
.thumb{position:relative;aspect-ratio:3/4;background:var(--panel2);display:block;overflow:hidden}
.thumb img{width:100%;height:100%;object-fit:contain}
.thumb .soldtag,.thumb .duptag{position:absolute;top:8px;font-size:10px;font-weight:800;padding:3px 8px;
  border-radius:999px;letter-spacing:.5px}
.thumb .soldtag{right:8px;background:var(--accent2);color:#06121a}
.thumb .duptag{left:8px;background:var(--warn);color:#3a2e12}
.body{padding:11px 13px;display:flex;flex-direction:column;gap:7px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.player{font-size:15px;font-weight:800;margin:0;line-height:1.2}
.player a{color:var(--text)}
.team{color:var(--muted);font-size:12px}
.val .big{font-size:18px;font-weight:800;color:var(--accent);text-align:right;white-space:nowrap}
.p130{font-size:11px;color:var(--muted);text-align:right;white-space:nowrap;margin-top:2px}
.p130 b{color:var(--text);font-weight:700}.p130.rough b{color:var(--muted)}
.setline{font-size:12px;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:2px 8px;font-size:10.5px;font-weight:600}
.chip.auto{color:#111;background:var(--accent2);border-color:var(--accent2)}
.chip.relic{color:#111;background:var(--warn);border-color:var(--warn)}
.chip.grade{color:#111;background:var(--accent);border-color:var(--accent)}
.detailslink{font-size:12px;font-weight:600}
/* cost & sale accordion */
.track{border-top:1px solid var(--line);padding-top:7px}
.track>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:7px;font-size:12px;font-weight:600}
.track>summary::-webkit-details-marker{display:none}
.track>summary::before{content:"\25B8";color:var(--muted);font-size:10px;transition:transform .15s}
.track[open]>summary::before{transform:rotate(90deg)}
.track>summary .muted{color:var(--muted);font-weight:500}
.track-body{padding:9px 2px 2px;display:flex;flex-direction:column;gap:8px}
.money-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.money-row label{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);min-width:54px}
input.money{width:92px;background:var(--panel2);color:var(--text);border:1px solid var(--line);
  border-radius:7px;padding:6px 8px;font-size:13px;font-weight:600}
.soldline{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;cursor:pointer;user-select:none}
.soldline input{width:16px;height:16px;accent-color:var(--accent2);cursor:pointer}
.pl{font-size:13px;font-weight:700}
.pl.pos{color:var(--accent)}.pl.neg{color:var(--red)}.pl.zero{color:var(--muted)}
.conf{font-size:10px;text-transform:uppercase;letter-spacing:.5px}
.conf.high{color:var(--accent)}.conf.medium{color:var(--warn)}.conf.low{color:var(--red)}
.empty{color:var(--muted);text-align:center;padding:60px}
footer{color:var(--muted);font-size:12px;text-align:center;padding:26px}
/* chart */
.chart{width:100%;height:auto;display:block}
.chart .cl{fill:none;stroke:var(--accent);stroke-width:2}
.chart .area{fill:var(--accent);opacity:.08}
.chart .dot{fill:var(--accent2);stroke:var(--panel);stroke-width:1.5}
.chart .ax{fill:var(--muted);font-size:10px}
.chart-note{font-size:11px;color:var(--muted);margin-top:6px}
.chart-empty{color:var(--muted);font-size:13px;padding:20px 0}
/* detail page */
.detail{max-width:1000px;margin:0 auto;padding:20px}
.back{font-size:13px;font-weight:600;display:inline-block;margin-bottom:14px}
.dhead{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;align-items:flex-start}
.dhead h1{font-size:26px;margin:0}
.dbig{font-size:30px;font-weight:800;color:var(--accent)}
.dimgs{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0}
.dimgs figure{margin:0;background:var(--panel2);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.dimgs img{width:100%;display:block;cursor:zoom-in}
.dimgs figcaption{font-size:11px;color:var(--muted);text-align:center;padding:5px}
.dcols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:720px){.dcols{grid-template-columns:1fr}.dimgs{grid-template-columns:1fr}}
.kv{display:grid;grid-template-columns:auto 1fr;gap:5px 14px;font-size:13.5px}
.kv .k{color:var(--muted)}
.section{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:16px}
.section h3{margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.comps{list-style:none;margin:0;padding:0;font-size:13px}
.comps li{padding:5px 0;border-bottom:1px solid var(--line);color:var(--muted)}
.comps li:last-child{border:none}
.notes{font-size:12.5px;color:var(--muted);font-style:italic}
.dupwarn{background:#3a2e12;border:1px solid var(--warn);color:var(--warn);border-radius:10px;padding:10px 13px;font-size:13px;margin-bottom:16px}
.lightbox{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;z-index:50;padding:24px;cursor:zoom-out}
.lightbox img{max-width:96vw;max-height:94vh;object-fit:contain;border-radius:8px}
"""

TRACKER_JS = r"""
const KEY="cc_state_v1";
let STATE={}, HASLS=true;
try{STATE=JSON.parse(localStorage.getItem(KEY)||"{}");localStorage.setItem("cc_t","1");localStorage.removeItem("cc_t");}catch(e){HASLS=false;}
function save(){if(!HASLS)return;try{localStorage.setItem(KEY,JSON.stringify(STATE));}catch(e){HASLS=false;}}
function st(n){return STATE[n]||{};}
function setSt(n,p){STATE[n]=Object.assign({},st(n),p);save();}
const money=v=>(v==null||isNaN(v))?"—":(Number.isInteger(v)?"$"+v.toLocaleString():"$"+v.toFixed(2));
const signed=v=>(v>=0?"+":"−")+"$"+Math.abs(v).toLocaleString(undefined,{maximumFractionDigits:2});
const plClass=v=>v>0?'pos':(v<0?'neg':'zero');
const numv=v=>{const x=parseFloat(v);return isNaN(x)?null:x;};
function drawChart(el,series,opts){
  opts=opts||{};const pts=series.filter(p=>p.value!=null);
  if(!pts.length){el.innerHTML='<div class="chart-empty">No history yet.</div>';return;}
  const W=opts.w||560,H=opts.h||150,pad=30;
  const vals=pts.map(p=>p.value);let mn=Math.min(...vals),mx=Math.max(...vals);
  if(mn===mx){mn=Math.max(0,mn*0.9);mx=mx*1.1||1;}
  const n=pts.length,X=i=>pad+(n===1?(W-2*pad)/2:i*(W-2*pad)/(n-1)),Y=v=>H-pad-(v-mn)/(mx-mn)*(H-2*pad);
  const poly=pts.map((p,i)=>X(i)+","+Y(p.value)).join(' ');
  const area="M"+X(0)+","+(H-pad)+" L"+poly.split(' ').join(' L ')+" L"+X(n-1)+","+(H-pad)+" Z";
  const dots=pts.map((p,i)=>`<circle cx="${X(i)}" cy="${Y(p.value)}" r="3.5" class="dot"><title>${p.date}: ${money(p.value)}</title></circle>`).join('');
  el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet">
    <text x="4" y="${pad-6}" class="ax">${money(Math.round(mx))}</text>
    <text x="4" y="${H-pad+10}" class="ax">${money(Math.round(mn))}</text>
    ${n>1?`<path d="${area}" class="area"/><polyline points="${poly}" class="cl"/>`:''}
    ${dots}
    <text x="${pad}" y="${H-6}" class="ax">${pts[0].date}</text>
    <text x="${W-pad}" y="${H-6}" class="ax" text-anchor="end">${pts[n-1].date}</text>
  </svg>${n<2?'<div class="chart-note">One snapshot so far — run a price refresh to grow the trend line.</div>':''}`;
}
"""

def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(s)

write(os.path.join(DOCS, "assets", "style.css"), STYLE)
write(os.path.join(DOCS, "assets", "tracker.js"), TRACKER_JS)

# ============================================================ INDEX
def chips_html(c):
    out = []
    if c.get("auto"): out.append('<span class="chip auto">AUTO</span>')
    if c.get("relic"): out.append('<span class="chip relic">RELIC</span>')
    if c.get("grade") and c["grade"] != "Raw": out.append(f'<span class="chip grade">{esc(c["grade"])}</span>')
    if c.get("serial"): out.append(f'<span class="chip">#{esc(c["serial"])}</span>')
    return "".join(out)

client = []
for c in cards:
    client.append({k: c.get(k) for k in ("n","player","team","year","set","card_no","parallel","serial",
        "auto","relic","grade","market_value","last_sale","last_sale_date","confidence","front","back","notes","comps","point130")})
CARDS_JSON = json.dumps(client)
HIST_TOTALS = json.dumps([{"date": s["date"], "value": s.get("total")} for s in history])
DUP_JSON = json.dumps(dupinfo)

INDEX = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Card Collection</title><link rel="stylesheet" href="assets/style.css">
<script src="assets/tracker.js" defer></script></head><body>
<header>
  <h1>&#9917; Card Collection</h1>
  <div class="stat"><span class="k" id="lblCount">Cards</span><span class="v" id="count"></span></div>
  <div class="stat"><span class="k" id="lblA">Market est.</span><span class="v" id="statA"></span></div>
  <div class="stat"><span class="k">Cost basis</span><span class="v" id="statB"></span></div>
  <div class="stat"><span class="k" id="lblPL">Unrealized P/L</span><span class="v" id="statPL"></span></div>
  <div class="grow"></div>
  <div class="tabs" id="tabs"><button data-v="collection" class="on">Collection</button>
    <button data-v="sold">Sold</button><button data-v="all">All</button></div>
  <div class="controls">
    <input type="search" id="q" placeholder="Search player, set, team&hellip;">
    <select id="sort"><option value="n">Order added</option><option value="value_desc">Value &darr;</option>
      <option value="value_asc">Value &uarr;</option><option value="player">Player A&ndash;Z</option>
      <option value="pl_desc">P/L &darr;</option></select>
    <button class="lnk" id="exp">&#8681; Export</button>
    <button class="lnk" id="imp">&#8679; Import</button>
    <input type="file" id="impfile" accept="application/json" style="display:none">
  </div>
</header>
<main>
  <div class="banner" id="banner" style="display:none"></div>
  <div class="pcard"><h2>Collection value over time</h2><div id="collchart"></div></div>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">No cards in this view.</div>
</main>
<footer>Green value = Card Ladder market est. &middot; <b>130pt</b> = median of matched 130point sold listings.
  No marker = exact parallel + print-run + year match &middot; <b>&#8776;</b> = close match (nearest run/year of the same parallel; see the note) &middot; <b>~</b> = broad player median (no parallel match found). &middot;
  Click any card for both values, the sold-count, range and match note &middot; Paid/Sold entries saved in this browser (Export to back up).</footer>
<script>
const CARDS={CARDS_JSON};
const HIST={HIST_TOTALS};
const DUP={DUP_JSON};
let VIEW="collection";
const grid=document.getElementById('grid');
function showBanner(){{const b=document.getElementById('banner');b.style.display='block';
  b.innerHTML="This browser won't auto-save edits (common with local files in Safari). Use <b>Export</b> to back up your Paid/Sold entries.";}}
function unreal(c,s){{return(s.paid!=null&&c.market_value!=null)?c.market_value-s.paid:null;}}
function real(c,s){{return(s.sold&&s.paid!=null&&s.soldFor!=null)?s.soldFor-s.paid:null;}}
function plInfo(c,s){{if(s.sold){{const r=real(c,s);return r!=null?{{v:r,label:' realized'}}:null;}}
  const u=unreal(c,s);return u!=null?{{v:u,label:' vs market'}}:null;}}
function trackSummary(c,s){{
  if(s.sold){{const r=real(c,s);return `<b>SOLD</b>${{s.soldFor!=null?' &middot; $'+s.soldFor.toLocaleString():''}}`+(r!=null?` &middot; <span class="pl ${{plClass(r)}}">${{signed(r)}}</span>`:'');}}
  if(s.paid!=null){{const u=unreal(c,s);return `Paid $${{s.paid.toLocaleString()}}`+(u!=null?` &middot; <span class="pl ${{plClass(u)}}">${{signed(u)}}</span>`:'');}}
  return `<span class="muted">Cost &amp; sale &mdash; add</span>`;}}
function plHTML(c,s){{const p=plInfo(c,s);return p?`<span class="pl ${{plClass(p.v)}}">${{signed(p.v)}}${{p.label}}</span>`:`<span class="pl zero">enter a cost</span>`;}}
function chip(t,cl){{return `<span class="chip ${{cl||''}}">${{t}}</span>`;}}
function cardHTML(c){{
  const s=st(c.n),isSold=!!s.sold,d=DUP[c.n]||{{tier:0}};
  const chips=[c.auto?chip('AUTO','auto'):'',c.relic?chip('RELIC','relic'):'',
    (c.grade&&c.grade!=='Raw')?chip(c.grade,'grade'):'',c.serial?chip('#'+c.serial,''):''].join('');
  return `<div class="card ${{isSold?'issold':''}}" data-n="${{c.n}}">
    <a class="thumb" href="cards/${{c.n}}.html">${{isSold?'<span class="soldtag">SOLD</span>':''}}${{d.tier===1?`<span class="duptag">&#9888; DUP?</span>`:''}}
      ${{c.front?`<img loading=lazy src="images/${{c.front}}.jpg" alt="">`:''}}</a>
    <div class="body">
      <div class="top"><div><p class="player"><a href="cards/${{c.n}}.html">${{c.player}}</a></p>
        <div class="team">${{c.team||''}}</div></div>
        <div class="val"><div class="big">${{money(c.market_value)}}</div>${{c.point130?`<div class="p130 ${{c.point130.tier!=='exact'?'rough':''}}" title="130point: ${{c.point130.note||'exact parallel match'}}">130pt&nbsp;<b>${{money(c.point130.v)}}</b>${{c.point130.tier==='close'?'&nbsp;≈':c.point130.tier==='broad'?'&nbsp;~':''}}</div>`:''}}</div></div>
      <div class="setline">${{c.year||''}} ${{c.set||''}} ${{c.card_no?'&middot; #'+c.card_no:''}}<br>${{c.parallel||''}}</div>
      <div class="chips">${{chips}}</div>
      <details class="track"${{isSold?' open':''}}><summary><span class="track-sum">${{trackSummary(c,s)}}</span></summary>
        <div class="track-body">
          <div class="money-row"><label>Paid</label><span>$</span><input class="money paid" data-n="${{c.n}}" type="number" min="0" step="0.01" value="${{s.paid??''}}" placeholder="0"></div>
          <label class="soldline"><input type="checkbox" class="soldchk" data-n="${{c.n}}" ${{isSold?'checked':''}}> Mark as sold</label>
          <div class="money-row"><label>Sold for</label><span>$</span><input class="money soldfor" data-n="${{c.n}}" type="number" min="0" step="0.01" value="${{s.soldFor??''}}" placeholder="0"></div>
          <div class="plrow">${{plHTML(c,s)}}</div>
        </div></details>
      <a class="detailslink" href="cards/${{c.n}}.html">View details &amp; history &rarr;</a>
    </div></div>`;
}}
function visible(){{
  const q=document.getElementById('q').value.toLowerCase().trim(),so=document.getElementById('sort').value;
  let list=CARDS.filter(c=>{{const sold=!!st(c.n).sold;
    if(VIEW==='collection'&&sold)return false;if(VIEW==='sold'&&!sold)return false;
    return !q||[c.player,c.set,c.team,c.parallel,c.year].join(' ').toLowerCase().includes(q);}});
  const plOf=c=>{{const p=st(c.n).paid;return(p!=null&&c.market_value!=null)?c.market_value-p:-1e9;}};
  if(so==='value_desc')list.sort((a,b)=>(b.market_value||0)-(a.market_value||0));
  else if(so==='value_asc')list.sort((a,b)=>(a.market_value||0)-(b.market_value||0));
  else if(so==='player')list.sort((a,b)=>a.player.localeCompare(b.player));
  else if(so==='pl_desc')list.sort((a,b)=>plOf(b)-plOf(a));
  else list.sort((a,b)=>a.n-b.n);
  return list;}}
function stats(list){{let mkt=0,paid=0,sold=0,un=0,re=0;list.forEach(c=>{{const s=st(c.n);mkt+=c.market_value||0;
  if(s.paid!=null){{paid+=s.paid;if(c.market_value!=null&&!s.sold)un+=c.market_value-s.paid;if(s.sold&&s.soldFor!=null)re+=s.soldFor-s.paid;}}
  if(s.sold&&s.soldFor!=null)sold+=s.soldFor;}});return {{mkt,paid,sold,un,re,n:list.length}};}}
function paintHeader(list){{const s=stats(list);
  document.getElementById('count').textContent=s.n;
  document.getElementById('lblCount').textContent=VIEW==='sold'?'Sold':(VIEW==='collection'?'Cards (unsold)':'All cards');
  if(VIEW==='sold'){{document.getElementById('lblA').textContent='Sold for (total)';document.getElementById('statA').innerHTML=money(s.sold);
    document.getElementById('lblPL').textContent='Realized P/L';document.getElementById('statPL').innerHTML=`<span class="pl ${{plClass(s.re)}}">${{signed(s.re)}}</span>`;}}
  else{{document.getElementById('lblA').textContent='Market est.';document.getElementById('statA').innerHTML=money(s.mkt);
    document.getElementById('lblPL').textContent='Unrealized P/L';document.getElementById('statPL').innerHTML=`<span class="pl ${{plClass(s.un)}}">${{signed(s.un)}}</span>`;}}
  document.getElementById('statB').innerHTML=money(s.paid);}}
function render(){{const list=visible();grid.innerHTML=list.map(cardHTML).join('');
  document.getElementById('empty').style.display=list.length?'none':'block';paintHeader(list);}}
function liveUpdate(n){{const card=grid.querySelector(`.card[data-n="${{n}}"]`);if(!card)return;
  const c=CARDS.find(x=>String(x.n)===String(n)),s=st(n);
  const pr=card.querySelector('.plrow');if(pr)pr.innerHTML=plHTML(c,s);
  const su=card.querySelector('.track-sum');if(su)su.innerHTML=trackSummary(c,s);paintHeader(visible());}}
window.addEventListener('DOMContentLoaded',()=>{{
  if(!HASLS)showBanner();
  drawChart(document.getElementById('collchart'),HIST,{{w:1100,h:150}});
  document.getElementById('tabs').addEventListener('click',e=>{{const b=e.target.closest('button');if(!b)return;
    VIEW=b.dataset.v;[...document.querySelectorAll('#tabs button')].forEach(x=>x.classList.toggle('on',x===b));render();}});
  document.getElementById('q').addEventListener('input',render);
  document.getElementById('sort').addEventListener('change',render);
  grid.addEventListener('input',e=>{{const t=e.target;if(!t.classList.contains('money'))return;
    const n=t.dataset.n,v=numv(t.value);if(t.classList.contains('paid'))setSt(n,{{paid:v}});else if(t.classList.contains('soldfor'))setSt(n,{{soldFor:v}});liveUpdate(n);}});
  grid.addEventListener('change',e=>{{const t=e.target;if(!t.classList.contains('soldchk'))return;const n=t.dataset.n;
    if(t.checked){{const c=CARDS.find(x=>String(x.n)===String(n));setSt(n,{{sold:true,soldFor:st(n).soldFor??(c.market_value??null)}});}}else setSt(n,{{sold:false}});render();}});
  document.getElementById('exp').addEventListener('click',()=>{{const b=new Blob([JSON.stringify(STATE,null,1)],{{type:'application/json'}});
    const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='card_edits.json';a.click();}});
  document.getElementById('imp').addEventListener('click',()=>document.getElementById('impfile').click());
  document.getElementById('impfile').addEventListener('change',e=>{{const f=e.target.files[0];if(!f)return;const r=new FileReader();
    r.onload=()=>{{try{{STATE=Object.assign({{}},STATE,JSON.parse(r.result));save();render();}}catch(err){{alert('Could not read that file.');}}}};r.readAsText(f);}});
  render();
}});
</script></body></html>"""
write(os.path.join(DOCS, "index.html"), INDEX)

# ============================================================ DETAIL PAGES
for c in cards:
    n = c["n"]; s = card_series(n); d = dupinfo[n]
    comps = "".join(f"<li>{esc(x)}</li>" for x in (c.get("comps") or [])) or "<li>No recorded comps.</li>"
    dupwarn = ""
    if d["tier"]:
        partners = ", ".join(f'<a href="{p["n"]}.html">{esc(p["player"])} ({esc(p["parallel"])} {esc(p["serial"])})</a>' for p in d["partners"])
        label = "Likely duplicate" if d["tier"] == 1 else "Shares player + card # with"
        dupwarn = f'<div class="dupwarn">&#9888; {label}: {partners}. Verify these are different physical cards before trusting the count/total.</div>'
    back_img = f'<figure><img src="../images/{esc(c["back"])}.jpg" onclick="zoom(this.src)" alt=""><figcaption>Back</figcaption></figure>' if c.get("back") else ""
    front_img = f'<figure><img src="../images/{esc(c["front"])}.jpg" onclick="zoom(this.src)" alt=""><figcaption>Front</figcaption></figure>' if c.get("front") else ""
    _p = c.get("point130")
    if _p:
        _tier = _p.get("tier", "exact")
        _note = esc(_p.get("note", ""))
        if _tier == "exact":
            _tag = ' <span style="color:var(--muted)">(exact parallel)</span>'
        elif _tier == "close":
            _tag = f' <span style="color:var(--warn)">&#8776; {_note}</span>'
        else:
            _tag = f' <span style="color:var(--muted)">&#126; {_note}</span>'
        p130row = f'<span class="k">130point</span><span>{money(_p["v"])} &middot; {_p["k"]} sold &middot; {money(_p["lo"])}&ndash;{money(_p["hi"])}{_tag}</span>'
    else:
        p130row = '<span class="k">130point</span><span>&mdash; no match</span>'
    DETAIL = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(c['player'])} &middot; Card Tracker</title><link rel="stylesheet" href="../assets/style.css">
<script src="../assets/tracker.js" defer></script></head><body>
<div class="detail">
<a class="back" href="../index.html">&larr; Back to collection</a>
{dupwarn}
<div class="dhead"><div><h1>{esc(c['player'])}</h1><div class="team">{esc(c.get('team'))}</div></div>
  <div style="text-align:right"><div class="dbig">{money(c.get('market_value'))}</div>
  <div class="team">market est. &middot; {esc(c.get('confidence'))} confidence</div></div></div>
<div class="chips" style="margin-top:10px">{chips_html(c)}</div>
<div class="dimgs">{front_img}{back_img}</div>
<div class="dcols">
  <div>
    <div class="section"><h3>Card</h3><div class="kv">
      <span class="k">Year</span><span>{esc(c.get('year'))}</span>
      <span class="k">Set</span><span>{esc(c.get('set'))}</span>
      <span class="k">Card #</span><span>{esc(c.get('card_no')) or '&mdash;'}</span>
      <span class="k">Parallel</span><span>{esc(c.get('parallel')) or '&mdash;'}</span>
      <span class="k">Serial</span><span>{esc(c.get('serial')) or '&mdash;'}</span>
      <span class="k">Last sale</span><span>{money(c.get('last_sale'))} {('&middot; '+esc(c.get('last_sale_date'))) if c.get('last_sale_date') else ''}</span>
      <span class="k">Card Ladder</span><span>{money(c.get('market_value'))} <span style="color:var(--muted)">(market est.)</span></span>
      {p130row}
    </div></div>
    <div class="section"><h3>Recent comps</h3><ul class="comps">{comps}</ul></div>
    {f'<div class="section"><h3>Notes</h3><div class="notes">{esc(c.get("notes"))}</div></div>' if c.get('notes') else ''}
  </div>
  <div>
    <div class="section"><h3>Value history</h3><div id="cchart"></div></div>
    <div class="section"><h3>Cost &amp; sale</h3>
      <div class="track-body">
        <div class="money-row"><label>Paid</label><span>$</span><input class="money" id="paid" type="number" min="0" step="0.01" placeholder="0"></div>
        <label class="soldline"><input type="checkbox" id="soldchk"> Mark as sold</label>
        <div class="money-row"><label>Sold for</label><span>$</span><input class="money" id="soldfor" type="number" min="0" step="0.01" placeholder="0"></div>
        <div class="plrow" id="plrow"></div>
      </div></div>
  </div>
</div>
<div style="text-align:right;color:var(--muted);font-size:11px;margin-top:8px">{esc(c.get('front'))}{(' / '+esc(c.get('back'))) if c.get('back') else ''}</div>
</div>
<div class="lightbox" id="lb"><img id="lbimg" src=""></div>
<script>
const C={json.dumps(client[[cc['n'] for cc in client].index(n)])};
const SERIES={json.dumps(s)};
function unreal(s){{return(s.paid!=null&&C.market_value!=null)?C.market_value-s.paid:null;}}
function real(s){{return(s.sold&&s.paid!=null&&s.soldFor!=null)?s.soldFor-s.paid:null;}}
function plHTML(s){{let v,lab='';if(s.sold){{v=real(s);lab=' realized';}}else{{v=unreal(s);lab=' vs market';}}
  return v==null?'<span class="pl zero">enter a cost</span>':`<span class="pl ${{plClass(v)}}">${{signed(v)}}${{lab}}</span>`;}}
window.addEventListener('DOMContentLoaded',()=>{{
  drawChart(document.getElementById('cchart'),SERIES,{{w:460,h:150}});
  const s=st(C.n);const paid=document.getElementById('paid'),sf=document.getElementById('soldfor'),chk=document.getElementById('soldchk'),pr=document.getElementById('plrow');
  if(s.paid!=null)paid.value=s.paid;if(s.soldFor!=null)sf.value=s.soldFor;chk.checked=!!s.sold;pr.innerHTML=plHTML(s);
  paid.addEventListener('input',()=>{{setSt(C.n,{{paid:numv(paid.value)}});pr.innerHTML=plHTML(st(C.n));}});
  sf.addEventListener('input',()=>{{setSt(C.n,{{soldFor:numv(sf.value)}});pr.innerHTML=plHTML(st(C.n));}});
  chk.addEventListener('change',()=>{{if(chk.checked){{setSt(C.n,{{sold:true,soldFor:st(C.n).soldFor??(C.market_value??null)}});if(sf.value==='')sf.value=C.market_value??'';}}else setSt(C.n,{{sold:false}});pr.innerHTML=plHTML(st(C.n));}});
}});
function zoom(u){{const lb=document.getElementById('lb');document.getElementById('lbimg').src=u;lb.style.display='flex';}}
document.getElementById('lb').onclick=function(){{this.style.display='none';}};
</script></body></html>"""
    write(os.path.join(DOCS, "cards", f"{n}.html"), DETAIL)

print(f"built site: index + {len(cards)} detail pages | total est value: {money(total_value)}")
dups = [c['n'] for c in cards if dupinfo[c['n']]['tier']]
print(f"duplicate flags: {len(dups)} cards -> {dups}")
