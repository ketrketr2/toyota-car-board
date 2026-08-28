/* ============ 車種詳細 ============ */
function rCar(cid){
 const d=D.cars[cid];
 const F=[
  {k:'F1',n:'露出機会',s:'AI回答生成率×引用量',idx:d.f1i,raw:`生成${d.answered_rate}%・引用${d.avg_cites}件/回答`},
  {k:'F2',n:'車種言及',s:'出るべき質問で名前が出た率',idx:d.f2i,raw:`${d.mr}%（${d.mention}/${d.target_cells}回答）`},
  {k:'F3',n:'第一想起',s:'言及の中で先頭に書かれた率',idx:d.f3i,raw:`${d.fr}%（${d.first}回）`},
  {k:'F4',n:'流入（GA4）',s:'toyota.jp車種ページ 28日',idx:d.f4i,raw:`${fmt(d.ga28)} sess`},
 ];
 let h=`<div class="crumb fade"><h2>${d.name}<small>${d.seg_label} ｜ 対象クエリ${d.queries.length}本（うち指名${d.n_named}本）</small></h2>
  <span class="chip">販売 <b>${fmt(d.sales_m)}</b>台/${D.asof.sales_month.slice(5)}月${cid==='lc250'?'（ランクル系合算）':''}</span>
  <span class="chip">GA <b>${fmt(d.ga28)}</b>sess/28日</span>
  <button class="hbtn" onclick="help('funnel')">?</button></div>`;

 /* ファネル + 語られ */
 h+=`<div class="g fade" style="grid-template-columns:1.35fr 1fr">
  <div class="card hl"><div class="ct">マーケティングファネル（8車種平均=100）<span class="q" onclick="help('funnel')">?</span></div><div class="fun">`;
 F.forEach(f=>{
  const wpc=Math.min((f.idx||0)/200*100,100);
  h+=`<div class="fstage" onmouseenter="tip('<b>${f.k} ${f.n}</b><br>${f.s}<br>実測: ${f.raw}')" onmouseleave="untip()">
   <div class="fl">${f.k}｜${f.n}<small>${f.s}</small></div>
   <div><div class="bar" style="height:12px;position:relative"><i style="width:${wpc}%;background:linear-gradient(90deg,${idxCol(f.idx)}55,${idxCol(f.idx)})"></i>
    <span style="position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:#5F729166"></span></div></div>
   <div class="fv" style="color:${idxCol(f.idx)}">${f.idx??'—'}<small>${f.raw}</small></div></div>`;});
 h+=`</div><div class="legend"><span>中央線=車種平均100</span><span style="color:var(--gn)">■115以上=強い</span><span style="color:var(--rd)">■85未満=弱い</span></div></div>`;
 h+=`<div class="g" style="grid-template-rows:auto auto;gap:14px">
   <div class="card"><div class="ct">語られ指数<span class="q" onclick="help('katarare')">?</span></div>
    <div style="display:flex;align-items:center;gap:18px">
     <div class="kpi" style="font-size:44px;color:${idxCol(d.katarare)}">${d.katarare??'—'}</div>
     <div class="sub2" style="font-size:11.5px">AI言及シェア <b class="mono">${d.ai_share??'—'}%</b> ÷ 販売シェア <b class="mono">${d.sales_share??'—'}%</b><br>${d.katarare==null?'':d.katarare<70?'<mark>売れ行きに対してAIに語られていない</mark>':d.katarare>130?'販売実績以上にAIで語られている':'販売実勢と釣り合っている'}</div>
    </div></div>
   <div class="card"><div class="ct">推定露出指数（言及率×検索需要）</div>
    <div class="kpi" style="color:${idxCol(d.expi)}">${d.expi??'—'}<small>/ 平均100</small></div>
    <div class="sub2">検索需要シード ${d.seed_demand}（プリウス=100・Googleトレンド12ヶ月実測）× F2言及率で、全国のAI接触量の相対規模を指数化</div></div>
  </div></div>`;

 /* 考察 */
 h+=`<div class="card fade" style="margin-top:14px"><div class="ct">考察 — 今どう・何が問題・だからどうする</div>
  <div class="ibox"><h4>■ 今どう</h4><p>${d.insight.now.map(esc).join(' ')}</p></div>
  ${d.insight.issue.length?`<div class="ibox is2"><h4>■ 何が問題か</h4><p>${d.insight.issue.map(esc).join(' ')}</p></div>`:''}
  ${d.insight.action.length?`<div class="ibox is3"><h4>■ だからどうする</h4><p>${d.insight.action.map(esc).join(' ')}</p></div>`:''}
 </div>`;

 /* 競合勝敗 + 引用 */
 const winRows=d.win.slice(0,7).map(w=>({label:w[0],val:w[1],color:w[3]===cid?'#EAF1FB':BRAND_C[w[2]]||'#5F7291',me:w[3]===cid}));
 const c4=d.cite4;const ctot=c4.toyota+c4.dealer+c4.sns+c4.media;
 h+=`<div class="g fade" style="grid-template-columns:1.2fr 1fr;margin-top:14px">
  <div class="card"><div class="ct">この車の質問で第一想起を取った車（社内競合含む）</div>
   ${hbar(winRows,560,{lw:150,suffix:'回'})}
   <div class="sub2">白帯=自車。${d.win[0]&&d.win[0][3]!==cid?`<mark>${d.win[0][0]}に本来の場面を奪われている</mark>`:'自車が最多獲得'}。同席頻度: ${d.riv_seen.slice(0,4).map(r=>`${r[0]}${r[1]}回`).join('・')}</div></div>
  <div class="card"><div class="ct">引用ドメイン4分類（自車が言及された回答の引用元）</div>
   <div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap">
    ${donut([{val:c4.toyota,color:'#FFB020'},{val:c4.dealer,color:'#3DDC97'},{val:c4.sns,color:'#9B8CFF'},{val:c4.media,color:'#22C7D6'}],150,ctot?Math.round(c4.toyota/ctot*100)+'%':'—','toyota.jp系比率')}
    <div style="flex:1;min-width:150px;font-size:11px;line-height:2.2">
     <span style="color:#FFB020">●</span> toyota.jp系 <b class="mono">${c4.toyota}</b><br>
     <span style="color:#3DDC97">●</span> 販売店サイト <b class="mono">${c4.dealer}</b><br>
     <span style="color:#9B8CFF">●</span> SNS・UGC <b class="mono">${c4.sns}</b><br>
     <span style="color:#22C7D6">●</span> メディア・まとめ <b class="mono">${c4.media}</b></div></div>
   <div class="sub2">メディア上位: ${d.cite_media_top.slice(0,4).map(m=>`${m[0]}(${m[1]})`).join('・')||'—'}</div></div>
 </div>`;

 /* AI面別 + トレンド */
 h+=`<div class="g fade" style="grid-template-columns:repeat(4,1fr);margin-top:14px">`;
 Object.entries(d.surf).forEach(([s,v])=>{
  h+=`<div class="card" style="border-top:2px solid ${SC[s]}"><div class="ct">${SN[s]}<span class="q" onclick="help('surface')">?</span></div>
   <div class="kpi" style="font-size:22px;color:${SC[s]}">${v.mr??'—'}<small>%言及</small></div>
   <div class="sub2">第一想起 ${v.fr??'—'}%（${v.mention}/${v.cells}回答）</div></div>`;});
 h+=`</div>`;
 const sent=d.sent;const stot=sent.positive+sent.neutral+sent.negative;
 h+=`<div class="g fade" style="grid-template-columns:1.4fr 1fr;margin-top:14px">
  <div class="card"><div class="ct">28日トレンド — 日次60クエリでの言及回数（実測） × GA流入</div>
   ${lineChart(D.days,[{vals:d.trend28.map(r=>r[1]),color:'#22C7D6',label:'AI言及'},],640,190)}
   <div class="legend"><span><i style="background:#22C7D6"></i>AI言及回数/日（既存日次計測の回答スキャン）</span></div>
   ${lineChart(d.ga_dates,[{vals:d.ga_sess,color:'#FFB020'}],640,150)}
   <div class="legend"><span><i style="background:#FFB020"></i>toyota.jp 車種ページ sessions/日（GA4実測）</span></div></div>
  <div class="card"><div class="ct">語られ方（センチメント・意見が示された${stot}回答）</div>
   <div class="g" style="gap:8px">
    ${[['positive','肯定的','#3DDC97'],['neutral','中立','#5F7291'],['negative','否定的','#FF6B87']].map(([k,l,c])=>{
      const v=sent[k]||0;const p=stot?Math.round(v/stot*100):0;
      return `<div><div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px"><span>${l}</span><span class="mono">${v}回答（${p}%）</span></div><div class="bar"><i style="width:${p}%;background:${c}"></i></div></div>`;}).join('')}
   </div>
   <div class="sub2" style="margin-top:10px">自車を含む文のみを判定対象にした語彙ベース判定。詳細な文脈はクエリ表の回答から確認できます。</div></div>
 </div>`;

 /* クエリテーブル */
 h+=`<div class="card fade" style="margin-top:14px"><div class="ct">対象クエリ ${d.queries.length}本 — 需要順（クリックでソート）<span class="q" onclick="help('queries')">?</span></div>
  <div class="tblwrap"><table class="tbl" id="qt_${cid}">
   <thead><tr><th onclick="sortQ('${cid}',0)">クエリ</th><th onclick="sortQ('${cid}',1)">needs↓</th><th onclick="sortQ('${cid}',2)">言及</th><th onclick="sortQ('${cid}',3)">1位獲得</th><th>この質問の勝者</th><th>種別</th></tr></thead>
   <tbody>${qRows(d.queries,cid)}</tbody></table></div>
  <div class="sub2" style="margin-top:8px"><mark>黄色マーク</mark>=needs上位なのに言及ゼロの取りこぼしクエリ。クエリの追加要望は <a href="mailto:nakai@slashslash.jp?subject=【車種別AI分析】クエリ追加要望（${d.name}）">こちらから</a>。毎週月曜に需要スコアが実測更新され、現役60本と補欠が入れ替わります。</div></div>`;
 return h;
}
function qRows(qs,cid){
 return qs.map(q=>{
  const miss=!q.named&&q.m===0&&(q.d||0)>15;
  return `<tr>
   <td style="max-width:420px;${miss?'':''}">${miss?'<mark>':''}${esc(q.t)}${miss?'</mark>':''}<div style="font-size:9.5px;color:var(--tx3)">${esc(q.kw||'')}</div></td>
   <td class="mono">${q.d??'—'}</td>
   <td>${q.named?'<span class="pill n">指名=自明</span>':q.m>0?`<span class="pill ok">${q.m}/${q.n}</span>`:`<span class="pill ng">0/${q.n}</span>`}</td>
   <td class="mono">${q.named?'—':(q.f||0)}</td>
   <td style="font-size:11px">${q.win?`${esc(q.win[0])} <span style="color:var(--tx3)">${q.win[1]}回</span>`:'—'}</td>
   <td>${q.named?'<span class="pill n">指名</span>':'<span class="pill">出現期待</span>'}</td></tr>`;
 }).join('');
}
const qSort={};
function sortQ(cid,col){
 const d=D.cars[cid];const key=['t','d','m','f'][col];
 qSort[cid]=qSort[cid]===key?'-'+key:key;
 const dir=qSort[cid].startsWith('-')?-1:1;
 const qs=[...d.queries].sort((a,b)=>{
  const av=a[key]??-1,bv=b[key]??-1;
  return (typeof av==='string'?av.localeCompare(bv):av-bv)*(-dir);
 });
 document.querySelector(`#qt_${cid} tbody`).innerHTML=qRows(qs,cid);
}
