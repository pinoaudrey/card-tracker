
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
