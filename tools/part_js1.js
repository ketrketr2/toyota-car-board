/* ============ helpers ============ */
const $=s=>document.querySelector(s);
const D=window.DATA;
const SN={chatgpt:'ChatGPT',gemini:'Gemini',aio:'AIによる概要',aimode:'AIモード'};
const SC={chatgpt:'#3DDC97',gemini:'#9B8CFF',aio:'#22C7D6',aimode:'#FFB020'};
const BRAND_C={toyota:'#FFB020',suzuki:'#22C7D6',honda:'#FF6B87',nissan:'#9B8CFF',daihatsu:'#3DDC97',mitsubishi:'#FF9C6B',other:'#5F7291'};
const BRAND_L={toyota:'トヨタ',suzuki:'スズキ',honda:'ホンダ',nissan:'日産',daihatsu:'ダイハツ',mitsubishi:'三菱',other:'他'};
const fmt=n=>n==null?'—':(typeof n==='number'?n.toLocaleString('ja-JP'):n);
const pct=n=>n==null?'—':n+'%';
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function idxCol(v){return v==null?'var(--tx3)':v>=115?'var(--gn)':v>=85?'var(--ac)':'var(--rd)';}

/* ---- SVG chart helpers ---- */
function spark(vals,w,h,color,fill){
 if(!vals||!vals.length)return '';
 const mx=Math.max(...vals,1),mn=0;
 const pts=vals.map((v,i)=>[(i/(vals.length-1))*(w-4)+2, h-3-((v-mn)/(mx-mn||1))*(h-8)]);
 const d='M'+pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join('L');
 const area=d+`L${pts[pts.length-1][0]},${h-2}L${pts[0][0]},${h-2}Z`;
 return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${fill?`<path d="${area}" fill="${color}" opacity=".12"/>`:''}<path d="${d}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round"/></svg>`;
}
function lineChart(dates,series,w,h,opts){
 // series: [{vals,color,label}]
 const o=opts||{};const pad={l:38,r:10,t:12,b:20};
 const mx=Math.max(...series.flatMap(s=>s.vals),1);
 const X=i=>pad.l+(i/(dates.length-1||1))*(w-pad.l-pad.r);
 const Y=v=>pad.t+(1-v/mx)*(h-pad.t-pad.b);
 let g='';
 for(let k=0;k<=3;k++){const v=mx*k/3,y=Y(v);
  g+=`<line x1="${pad.l}" y1="${y}" x2="${w-pad.r}" y2="${y}" stroke="#1E2C46" stroke-dasharray="3 4"/><text x="${pad.l-6}" y="${y+3.5}" font-size="9" fill="#5F7291" text-anchor="end">${Math.round(v)}</text>`;}
 const step=Math.max(1,Math.floor(dates.length/5));
 dates.forEach((d,i)=>{if(i%step===0)g+=`<text x="${X(i)}" y="${h-5}" font-size="8.5" fill="#5F7291" text-anchor="middle">${d.slice(5)}</text>`;});
 series.forEach(s=>{
  const pts=s.vals.map((v,i)=>[X(i),Y(v)]);
  g+=`<path d="M${pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join('L')}" fill="none" stroke="${s.color}" stroke-width="2.2" stroke-linejoin="round"/>`;
  const lp=pts[pts.length-1];g+=`<circle cx="${lp[0]}" cy="${lp[1]}" r="3.2" fill="${s.color}"/>`;
 });
 return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block">${g}</svg>`;
}
function hbar(rows,w,opts){
 // rows: [{label,val,color,sub,me}]
 const o=opts||{};const bh=22,gap=9,lw=o.lw||110,vw=52;
 const mx=Math.max(...rows.map(r=>r.val),1);
 const h=rows.length*(bh+gap);
 let g='';
 rows.forEach((r,i)=>{
  const y=i*(bh+gap);const bwid=(r.val/mx)*(w-lw-vw-14);
  g+=`<text x="${lw-8}" y="${y+bh/2+4}" font-size="11" fill="${r.me?'#EAF1FB':'#9EB1CD'}" font-weight="${r.me?'700':'400'}" text-anchor="end">${esc(r.label)}</text>`;
  g+=`<rect x="${lw}" y="${y+2}" width="${Math.max(bwid,2)}" height="${bh-4}" rx="5" fill="${r.color}" opacity="${r.me?1:.75}"/>`;
  if(r.me)g+=`<rect x="${lw-3}" y="${y}" width="3" height="${bh}" rx="1.5" fill="#EAF1FB"/>`;
  g+=`<text x="${lw+Math.max(bwid,2)+8}" y="${y+bh/2+4}" font-size="11" fill="#EAF1FB" font-family="JetBrains Mono">${r.val}${o.suffix||''}</text>`;
 });
 return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block">${g}</svg>`;
}
function donut(parts,size,label,sub){
 // parts: [{val,color,name}]
 const tot=parts.reduce((a,b)=>a+b.val,0)||1;const r=size/2-8,cx=size/2,cy=size/2;let a0=-Math.PI/2,g='';
 parts.forEach(p=>{
  const a1=a0+(p.val/tot)*Math.PI*2;
  const x0=cx+r*Math.cos(a0),y0=cy+r*Math.sin(a0),x1=cx+r*Math.cos(a1),y1=cy+r*Math.sin(a1);
  const big=(a1-a0)>Math.PI?1:0;
  if(p.val>0)g+=`<path d="M${x0},${y0}A${r},${r} 0 ${big} 1 ${x1},${y1}" fill="none" stroke="${p.color}" stroke-width="13" stroke-linecap="butt"/>`;
  a0=a1;
 });
 g+=`<text x="${cx}" y="${cy-2}" text-anchor="middle" font-size="17" font-weight="800" fill="#EAF1FB" font-family="JetBrains Mono">${label}</text><text x="${cx}" y="${cy+14}" text-anchor="middle" font-size="8.5" fill="#5F7291">${sub}</text>`;
 return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${g}</svg>`;
}
function scatter(pts,w,h){
 // pts: [{x,y,label,col,id}] x=販売シェア y=AI言及シェア
 const pad={l:44,r:16,t:14,b:30};
 const mx=Math.max(...pts.map(p=>Math.max(p.x,p.y)))*1.15;
 const X=v=>pad.l+(v/mx)*(w-pad.l-pad.r), Y=v=>h-pad.b-(v/mx)*(h-pad.t-pad.b);
 let g=`<line x1="${X(0)}" y1="${Y(0)}" x2="${X(mx)}" y2="${Y(mx)}" stroke="#2B3D5E" stroke-dasharray="5 5"/>`;
 g+=`<text x="${X(mx*0.86)}" y="${Y(mx*0.86)-9}" font-size="9" fill="#5F7291" text-anchor="end" transform="rotate(-33 ${X(mx*0.86)} ${Y(mx*0.86)-9})">語られ指数100（販売＝AI言及）</text>`;
 for(let k=0;k<=4;k++){const v=mx*k/4;
  g+=`<text x="${X(v)}" y="${h-10}" font-size="9" fill="#5F7291" text-anchor="middle">${v.toFixed(0)}%</text>`;
  g+=`<text x="${pad.l-8}" y="${Y(v)+3}" font-size="9" fill="#5F7291" text-anchor="end">${v.toFixed(0)}%</text>`;
  g+=`<line x1="${X(v)}" y1="${pad.t}" x2="${X(v)}" y2="${h-pad.b}" stroke="#14203650"/>`;}
 g+=`<text x="${(w+pad.l)/2}" y="${h-0.5}" font-size="9.5" fill="#9EB1CD" text-anchor="middle">販売台数シェア（8車種内・${D.asof.sales_month}）</text>`;
 g+=`<text x="12" y="${h/2}" font-size="9.5" fill="#9EB1CD" text-anchor="middle" transform="rotate(-90 12 ${h/2})">AI言及シェア（8車種内）</text>`;
 pts.forEach(p=>{
  g+=`<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="7" fill="${p.col}" opacity=".9" style="cursor:pointer" onclick="go('car:${p.id}')"><title>${p.label}</title></circle>`;
  g+=`<text x="${X(p.x)}" y="${Y(p.y)-11}" font-size="10" fill="#EAF1FB" text-anchor="middle" font-weight="700">${p.label}</text>`;
 });
 return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block">${g}</svg>`;
}

/* ============ modal & tips ============ */
function openModal(html){$('#modal').innerHTML=`<button class="x" onclick="closeModal()">閉じる ✕</button>`+html;$('#mback').classList.add('on');}
function closeModal(){$('#mback').classList.remove('on');}
const HELP={
 hq:`<h3>概況の読み方</h3><p><b>語られ指数マップ</b>: 横軸が販売台数シェア、縦軸がAIの回答に登場するシェア（どちらも重点8車種内）。対角線より<b>下</b>にある車種は「売れているのにAIに語られていない」＝AI経由の比較検討で取りこぼしが起きやすい車種です。</p><p><b>ファネル指数</b>は8車種平均を100とした相対値。F1=露出機会（AI回答の生成率×引用量）、F2=車種言及率、F3=第一想起率、F4=toyota.jp車種ページ流入（GA4実測）。</p><p>下段の<b>全車種28日トレンド</b>は既存の日次60クエリの回答本文を車種名でスキャンした実測です。</p>`,
 funnel:`<h3>4段ファネルの定義</h3><p><b>F1 露出機会</b>: その車が出てくるべき質問（車名を含まない生活文脈・競合名クエリ）に対して、AIが回答を生成した率 × 平均引用数。<b>F2 車種言及</b>: 同じ質問群で車名が回答に登場した率。<b>F3 第一想起</b>: 言及された回答の中で、全車種中いちばん先に書かれた率（AI回答は推薦順に並ぶ性質を利用）。<b>F4 流入</b>: toyota.jp該当車種ページのセッション（GA4・直近28日）。</p><p>すべて<b>8車種平均=100</b>の指数で表示し、実数はカッコ内。指名クエリ（車名入り）は出現が自明なためF2/F3の分母から除外しています。</p>`,
 katarare:`<h3>語られ指数とは</h3><p>AI言及シェア ÷ 販売台数シェア × 100。<b>100未満＝売れ行きに比べてAIに語られていない</b>（AI比較で不利）、100超＝販売実績以上に語られている。販売台数は自販連・全軽自協の実測（${'${D.asof.sales_month}'}）。ランドクルーザー250の販売台数は自販連の通称名集計の都合上ランドクルーザー系合算値です。</p>`,
 queries:`<h3>クエリ管理の読み方</h3><p>登録済み全クエリの現役／補欠と成績。<b>needs</b>はGoogleトレンド実測を起点にした需要スコアで、毎週月曜にDataForSEOの検索ボリューム実測で自動更新→現役と補欠が入れ替わります（昇格・降格はこの画面に表示）。<b>言及/回答</b>は今回の計測でその車が登場した回答数。指名バッジ付きは車名入りクエリです。</p><p>クエリの追加要望は下部のリンクから送れます。</p>`,
 surface:`<h3>AI面別の見方</h3><p>同じ質問を4つのAI面（ChatGPT・Gemini・Googleの「AIによる概要」・「AIモード」）に投げた結果の言及率。面によって参照する情報源が違うため、弱い面はその面が引用しやすいメディアへの露出が課題になります。</p>`,
};
function help(k){let h=HELP[k]||HELP.hq;h=h.replace('${D.asof.sales_month}',D.asof.sales_month);openModal(h);}
let tipEl=null;
document.addEventListener('mousemove',e=>{const t=$('#tip');if(t.style.display==='block'){t.style.left=Math.min(e.clientX+14,innerWidth-320)+'px';t.style.top=(e.clientY+14)+'px';}});
function tip(html){const t=$('#tip');t.innerHTML=html;t.style.display='block';}
function untip(){$('#tip').style.display='none';}

/* ============ nav & router ============ */
const VIEWS=[['hq','◈','概況'],...D.focus.map(c=>['car:'+c,'▸',D.cars[c].name]),['queries','⌸','クエリ管理'],['guide','?','読み方ガイド']];
function buildNav(){
 let h='<div class="sec">OVERVIEW</div>';
 VIEWS.forEach(([id,ic,label])=>{
  if(id==='car:'+D.focus[0])h+='<div class="sec">CAR DEEP DIVE</div>';
  if(id==='queries')h+='<div class="sec">SYSTEM</div>';
  let bd='';
  if(id.startsWith('car:')){const c=D.cars[id.slice(4)];
   bd=`<span class="bd ${c.katarare!=null&&c.katarare<70?'hot':c.katarare>=115?'good':''}">${c.katarare==null?'—':c.katarare}</span>`;}
  h+=`<button class="nv" data-v="${id}" onclick="go('${id}')"><span class="ic">${ic}</span>${label}${bd}</button>`;
 });
 $('#nav').innerHTML=h;
 $('#sfoot').innerHTML=`計測: ${D.asof.car_round}（${fmt(D.asof.round_calls)}回答）<br>日次スキャン: ${D.asof.core_days[0].slice(5)}〜${D.asof.core_days[1].slice(5)}<br>GA4: 直近28日実測<br>販売: 自販連/全軽自協 ${D.asof.sales_month}`;
}
function go(v){location.hash=v;render();}
function cur(){return location.hash.replace('#','')||'hq';}
function render(){
 const v=cur();
 document.querySelectorAll('.nv').forEach(b=>b.classList.toggle('on',b.dataset.v===v));
 const m=$('#main');
 if(v==='hq')m.innerHTML=rHQ();
 else if(v.startsWith('car:'))m.innerHTML=rCar(v.slice(4));
 else if(v==='queries')m.innerHTML=rQueries();
 else m.innerHTML=rGuide();
 m.querySelectorAll('.fade');window.scrollTo(0,0);
}
window.addEventListener('hashchange',render);

/* ============ 概況 ============ */
function rHQ(){
 const F=D.focus.map(c=>D.cars[c]);
 const worst=[...F].sort((a,b)=>(a.katarare??999)-(b.katarare??999))[0];
 const best=[...F].sort((a,b)=>(b.katarare??-1)-(a.katarare??-1))[0];
 const pts=D.focus.filter(c=>D.cars[c].ai_share!=null&&D.cars[c].sales_share!=null).map(c=>({x:D.cars[c].sales_share,y:D.cars[c].ai_share,label:D.cars[c].name,col:D.cars[c].katarare<70?'#FF6B87':D.cars[c].katarare>115?'#3DDC97':'#FFB020',id:c}));
 const ov=[...D.overview].sort((a,b)=>b.hits28-a.hits28).slice(0,18);
 let h=`<div class="crumb fade"><h2>概況<small>重点8車種 × AI 4面 実測</small></h2>
  <span class="chip">計測 <b>${fmt(D.asof.round_calls)}</b>回答/周</span>
  <span class="chip">クエリ <b>377</b>本</span>
  <span class="chip">AI面 <b>4</b></span>
  <button class="hbtn" onclick="help('hq')">?</button></div>`;
 h+=`<div class="g fade" style="grid-template-columns:repeat(auto-fit,minmax(170px,1fr))">
  <div class="card hl"><div class="ct">最も語られていない車</div><div class="kpi dn">${worst.name}</div><div class="sub2">語られ指数 <b class="mono">${worst.katarare}</b> — 販売シェア${worst.sales_share}%に対しAI言及${worst.ai_share}%</div></div>
  <div class="card"><div class="ct">最もAIに強い車</div><div class="kpi up">${best.name}</div><div class="sub2">語られ指数 <b class="mono">${best.katarare}</b>・第一想起率${pct(best.fr)}</div></div>
  <div class="card"><div class="ct">8車種の平均言及率<span class="q" onclick="help('funnel')">?</span></div><div class="kpi">${(F.reduce((a,c)=>a+(c.mr||0),0)/8).toFixed(1)}<small>%</small></div><div class="sub2">出てくるべき質問で名前が挙がった率（F2）</div></div>
  <div class="card"><div class="ct">計測コスト</div><div class="kpi">$${D.asof.round_cost}<small>/周</small></div><div class="sub2">${D.asof.car_round} 実測。全回答本文・引用を保存済み</div></div>
 </div>`;
 h+=`<div class="g" style="grid-template-columns:1.25fr 1fr;margin-top:14px">
  <div class="card fade"><div class="ct">語られ指数マップ — 売れ行き vs AI言及<span class="q" onclick="help('katarare')">?</span></div>${scatter(pts,560,420)}
   <div class="legend"><span><i style="background:#FF6B87"></i>語られ指数&lt;70（AIで過小）</span><span><i style="background:#FFB020"></i>70〜115</span><span><i style="background:#3DDC97"></i>&gt;115（AIで優位）</span><span>●クリックで車種詳細へ</span></div></div>
  <div class="card fade"><div class="ct">車種別サマリ（クリックで深掘り）</div><div class="g" style="gap:8px">`;
 D.focus.forEach(c=>{const d=D.cars[c];
  h+=`<div class="fstage" onclick="go('car:${c}')" style="grid-template-columns:96px 1fr 74px 60px">
   <div class="fl">${d.name}<small>${d.seg_label}</small></div>
   <div>${spark(d.trend28.map(r=>r[1]),190,30,'#22C7D6',1)}</div>
   <div class="fv" style="color:${idxCol(d.katarare)}">${d.katarare??'—'}<small>語られ指数</small></div>
   <div class="fv">${d.mr}%<small>言及率</small></div></div>`;});
 h+=`</div></div></div>`;
 h+=`<div class="card fade" style="margin-top:14px"><div class="ct">全車種・28日AI言及ランキング（日次60クエリの回答スキャン実測 / 太字=重点8車種）</div>
  ${hbar(ov.map(o=>({label:o.name,val:o.hits28,color:BRAND_C[o.brand]||'#5F7291',me:o.focus})),640,{lw:130})}
  <div class="legend">${Object.entries(BRAND_L).filter(([k])=>ov.some(o=>o.brand===k)).map(([k,l])=>`<span><i style="background:${BRAND_C[k]}"></i>${l}</span>`).join('')}</div></div>`;
 // 全体考察
 const low=F.filter(c=>c.katarare!=null&&c.katarare<70).map(c=>c.name);
 const hi=F.filter(c=>c.katarare!=null&&c.katarare>150).map(c=>c.name);
 h+=`<div class="g" style="grid-template-columns:1fr;margin-top:14px"><div class="card fade"><div class="ct">全体考察 — 今どうなっているか</div>
  <div class="ibox"><h4>■ 現状</h4><p>販売上位なのにAIに語られていないのは<mark>${low.join('・')||'該当なし'}</mark>。逆に${hi.join('・')||'ノア・ヴォクシー'}は販売実績以上に語られている（ミニバン比較の定番として常時列挙されるため）。</p></div>
  <div class="ibox is2"><h4>■ 何が問題か</h4><p>語られない車種は、AI検索・AI比較の入口で<b>候補リストに載る前に脱落</b>している。ライズ（月販${fmt(D.cars.raize.sales_m)}台=8車種中最多）とルーミーは受け皿がヤリス系・他社兄弟車に流れ、ランドクルーザー250はジムニー系に本格SUV文脈を奪われている。</p></div>
  <div class="ibox is3"><h4>■ だからどうする</h4><p>①語られ指数&lt;70の3車種を優先ターゲットに設定。②各車の詳細画面の「取りこぼしクエリ」に対応する一次情報（比較・価格・納期FAQ）をtoyota.jp側へ整備。③第一想起を社内車種が奪っている場合は使い分け文脈を明示し共倒れを防ぐ。</p></div>
 </div></div>`;
 return h;
}
