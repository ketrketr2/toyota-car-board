/* ============ クエリ管理 ============ */
function rQueries(){
 const all=[];
 D.focus.forEach(c=>D.cars[c].queries.forEach(q=>{
  const e=all.find(x=>x.id===q.id);
  if(e){e.cars.push(D.cars[c].name);}
  else all.push({...q,cars:[D.cars[c].name]});
 }));
 all.sort((a,b)=>(b.d||0)-(a.d||0));
 const miss=all.filter(q=>!q.named&&q.m===0);
 const bench=D.bench||[];
 let h=`<div class="crumb fade"><h2>クエリ管理<small>現役 ${all.length}本 ／ 補欠 ${bench.length}本</small></h2>
  <span class="chip">共有クエリ含む実登録 <b>377</b>本</span>
  <span class="chip">取りこぼし <b>${miss.length}</b>本</span>
  <button class="hbtn" onclick="help('queries')">?</button></div>`;
 h+=`<div class="g fade" style="grid-template-columns:repeat(auto-fit,minmax(190px,1fr))">
  <div class="card hl"><div class="ct">入替の仕組み</div><div class="sub2" style="font-size:11.5px;line-height:2">毎週月曜、登録全クエリの検索ボリュームを実測で取り直し、needsスコアを再計算。<b>現役60本/車</b>と補欠が自動で入れ替わります。IDは絶対に振り直さないため、入れ替わっても時系列は壊れません。</div></div>
  <div class="card"><div class="ct">今週の昇格</div><div class="kpi up">${(D.promo&&D.promo.up.length)||0}<small>本</small></div><div class="sub2">${(D.promo&&D.promo.up.length)?D.promo.up.map(x=>esc(x)).join('<br>'):'初回計測のため入替なし。次回月曜から表示されます。'}</div></div>
  <div class="card"><div class="ct">今週の降格</div><div class="kpi dn">${(D.promo&&D.promo.down.length)||0}<small>本</small></div><div class="sub2">${(D.promo&&D.promo.down.length)?D.promo.down.map(x=>esc(x)).join('<br>'):'初回計測のため入替なし。'}</div></div>
  <div class="card"><div class="ct">クエリを追加したい</div><div class="sub2" style="font-size:11.5px;line-height:2">担当者が「これも見たい」という質問を随時追加できます。<a href="mailto:nakai@slashslash.jp?subject=【車種別AI分析】クエリ追加要望&body=車種:%0D%0A追加したい質問:%0D%0A理由:">メールで送る →</a><br>次回計測から反映されます。</div></div>
 </div>`;
 h+=`<div class="card fade" style="margin-top:14px"><div class="ct">取りこぼしクエリ（需要があるのに1回も名前が挙がらなかった質問）</div>
  <div class="tblwrap"><table class="tbl"><thead><tr><th>クエリ</th><th>needs</th><th>対象車種</th><th>この質問の勝者</th></tr></thead><tbody>
  ${miss.slice(0,25).map(q=>`<tr><td style="max-width:460px">${esc(q.t)}<div style="font-size:9.5px;color:var(--tx3)">${esc(q.kw||'')}</div></td><td class="mono">${q.d??'—'}</td><td style="font-size:11px">${q.cars.join('・')}</td><td style="font-size:11px">${q.win?esc(q.win[0])+' <span style="color:var(--tx3)">'+q.win[1]+'回</span>':'—'}</td></tr>`).join('')}
  </tbody></table></div>
  <div class="sub2" style="margin-top:8px">上位25本を表示（全${miss.length}本）。ここが最も改善余地の大きい領域です。</div></div>`;
 if(bench.length)h+=`<div class="card fade" style="margin-top:14px"><div class="ct">補欠クエリ ${bench.length}本（需要が上がれば現役に昇格）</div>
  <div class="tblwrap"><table class="tbl"><thead><tr><th>クエリ</th><th>needs</th><th>想定車種</th></tr></thead><tbody>
  ${bench.map(q=>`<tr><td style="max-width:470px">${esc(q.t)}<div style="font-size:9.5px;color:var(--tx3)">${esc(q.kw||'')}</div></td><td class="mono">${q.d??'—'}</td><td style="font-size:11px">${(q.cars||[]).join('・')}</td></tr>`).join('')}
  </tbody></table></div></div>`;
 h+=`<div class="card fade" style="margin-top:14px"><div class="ct">全クエリ一覧（需要順）</div>
  <div class="tblwrap"><table class="tbl"><thead><tr><th>クエリ</th><th>needs</th><th>言及</th><th>対象車種</th><th>種別</th></tr></thead><tbody>
  ${all.slice(0,120).map(q=>`<tr><td style="max-width:430px">${esc(q.t)}</td><td class="mono">${q.d??'—'}</td><td>${q.named?'<span class="pill n">指名</span>':q.m>0?`<span class="pill ok">${q.m}/${q.n}</span>`:`<span class="pill ng">0/${q.n}</span>`}</td><td style="font-size:11px">${q.cars.join('・')}</td><td>${q.named?'<span class="pill n">指名</span>':'<span class="pill">出現期待</span>'}</td></tr>`).join('')}
  </tbody></table></div><div class="sub2" style="margin-top:8px">需要上位120本を表示（現役計${all.length}本）。</div></div>`;
 return h;
}

/* ============ 読み方ガイド ============ */
function rGuide(){
 return `<div class="crumb fade"><h2>読み方ガイド<small>このボードは何を測っているのか</small></h2></div>
 <div class="g fade" style="grid-template-columns:1fr 1fr">
  <div class="card hl"><div class="ct">このボードの目的</div><p style="font-size:12.5px;line-height:2;color:var(--tx2)">生活者が車を選ぶとき、検索の代わりにAIへ質問する場面が増えています。そのときAIが<b>どの車を候補に挙げ、どれを最初に薦めるか</b>は、カタログや広告ではなくAIが参照する情報源で決まります。このボードは重点8車種について、<mark>本来その車が出てくるべき質問</mark>を用意し、4つのAI面に実際に投げて、出現しているか・先頭に書かれているか・何を根拠に語られているかを毎回実測します。</p></div>
  <div class="card"><div class="ct">なぜ「車名を入れない質問」で測るのか</div><p style="font-size:12.5px;line-height:2;color:var(--tx2)">「ルーミーの燃費は？」と聞けばルーミーは必ず出てきます。それでは<b>出現しているかどうかの検査になりません</b>。実際の購入検討は「スライドドアで小回りが利く車は？」のような車名なしの質問から始まります。そこで名前が挙がるかどうかが勝負であり、ファネルはこの前提でのみ成立します。車名入りの指名クエリは<b>語られ方（評判・引用元）の分析</b>に使い、出現率の分母からは除外しています。</p></div>
 </div>
 <div class="card fade" style="margin-top:14px"><div class="ct">4段ファネルの定義と計算式</div>
  <div class="tblwrap"><table class="tbl"><thead><tr><th>段</th><th>指標</th><th>定義</th><th>データ源</th></tr></thead><tbody>
   <tr><td class="mono ac">F1</td><td>露出機会</td><td>その車が出るべき質問群でAIが回答を生成した率 × 平均引用数（ノイズドメイン除外）</td><td>AI4面の実測回答</td></tr>
   <tr><td class="mono ac">F2</td><td>車種言及</td><td>同じ質問群で車名が回答本文に登場した率。表記ゆれ・誤検出ガード（例:「アクアリウム」を除外）済み</td><td>回答本文スキャン</td></tr>
   <tr><td class="mono ac">F3</td><td>第一想起</td><td>言及された回答のうち、全車種中いちばん先に書かれた率。AI回答は推薦順に並ぶ性質を利用</td><td>回答本文の出現位置</td></tr>
   <tr><td class="mono ac">F4</td><td>流入</td><td>toyota.jp該当車種ページのセッション（直近28日）</td><td>GA4実測（Windsor経由）</td></tr>
  </tbody></table></div>
  <div class="sub2" style="margin-top:10px">すべて<b>8車種平均=100</b>の指数で相対表示します。絶対値だけでは「多いのか少ないのか」を判断できないためです。</div></div>
 <div class="g fade" style="grid-template-columns:1fr 1fr;margin-top:14px">
  <div class="card"><div class="ct">語られ指数</div><p style="font-size:12.5px;line-height:2;color:var(--tx2)">AI言及シェア ÷ 販売台数シェア × 100（どちらも重点8車種内）。<b>100未満＝売れているのにAIに語られていない</b>。販売台数は自販連・全軽自協の公表実数（${D.asof.sales_month}）を使用しています。<br><span style="color:var(--tx3);font-size:11px">※ランドクルーザー250は自販連の通称名集計の都合上、ランドクルーザー系合算値です。</span></p></div>
  <div class="card"><div class="ct">推定露出指数</div><p style="font-size:12.5px;line-height:2;color:var(--tx2)">全国で実際に何回AIに語られたかは誰にも計測できません。そこで<b>F2言及率 × その車の検索需要</b>で相対規模を指数化しています。検索需要はGoogleトレンド12ヶ月平均をプリウス=100のアンカーで連結した実測値です。絶対数の推定ではなく、<b>車種間の比較にのみ使う指数</b>です。</p></div>
 </div>
 <div class="card fade" style="margin-top:14px"><div class="ct">データの鮮度と信頼性</div>
  <div class="tblwrap"><table class="tbl"><thead><tr><th>データ</th><th>取得</th><th>更新</th><th>備考</th></tr></thead><tbody>
   <tr><td>AI 4面の回答</td><td>${D.asof.car_round}</td><td>計測実行のたび</td><td>${fmt(D.asof.round_calls)}回答・全文と引用URLを保存</td></tr>
   <tr><td>日次AI言及トレンド</td><td>${D.asof.core_days[0]}〜${D.asof.core_days[1]}</td><td>毎朝自動</td><td>既存の日次60クエリの回答を車種名でスキャン</td></tr>
   <tr><td>GA4 車種ページ流入</td><td>${D.asof.ga_dates[0]}〜${D.asof.ga_dates[1]}</td><td>毎朝自動</td><td>実測。推定値は含みません</td></tr>
   <tr><td>販売台数</td><td>${D.asof.sales_month}</td><td>月次</td><td>${(D.asof.sales_sources||[]).map(s=>`<a href="${s.url}" target="_blank">${esc(s.label)}</a>`).join(' / ')}</td></tr>
  </tbody></table></div>
  <div class="sub2" style="margin-top:10px">このボードには<b>推定値・デモ値を一切表示しません</b>。数値が出ていない箇所は「—」と表示されます。ゼロと表示されている場合は、検証を行ったうえでの実測ゼロです。</div></div>
 <div class="card fade" style="margin-top:14px"><div class="ct">よくある質問</div>
  ${[['なぜ車種によって対象クエリ数が違わないのか','各車60本に揃えています。需要スコア上位から自動選抜しており、指名クエリは最大22本までとしています。'],
     ['第一想起率が低いのは悪いことか','言及率が高いのに第一想起が低い場合、「候補には入るが本命として推されていない」状態です。ヴォクシーがこの典型で、常にノアの後ろに書かれます。'],
     ['社内の車種を競合として出していいのか','販売現場では実在の比較対象であるため表示しています。共倒れを防ぐには、AI上での使い分け文脈を自ら提示する必要があります。'],
     ['計測はいくらかかるのか','1周あたり約$38（4面×377本）の実測です。頻度は運用方針に応じて調整できます。']]
   .map(([q,a])=>`<div class="ibox" style="margin-top:10px;border-color:var(--cy)"><h4 style="color:var(--cy)">Q. ${q}</h4><p>${a}</p></div>`).join('')}
 </div>`;
}

/* ============ boot ============ */
buildNav();
if(!location.hash)location.hash='hq';
render();
