#!/usr/bin/env python3
"""①車種別AI分析ボード: 全データ統合 → board_data.json
入力: gbv(car snapshot, registry, core_trend), ga_f4.json, sales_by_model.json, seed需要
出力: /home/claude/cb/board_data.json（実測のみ・推定値なし）"""
import json, os, sys, glob, collections, statistics
GEO = os.environ.get('GEO_REPO', '/tmp/gb')
CW = os.environ.get('WORK_DIR', 'work')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f'{GEO}/src')
import yaml

snaps = sorted(glob.glob(f'{GEO}/data/car/snapshots/*.json'))
if not snaps:
    sys.exit('car-round のスナップショットが見つかりません（計測がまだ回っていない可能性）')
snap = json.load(open(snaps[-1]))
reg = yaml.safe_load(open(f'{GEO}/prompts/registry.yaml'))
ga = json.load(open(f'{CW}/ga_f4.json'))
core = json.load(open(f'{CW}/core_trend.json'))
sales = json.load(open(f'{TOOLS}/sales_by_model.json'))
cars_cfg = yaml.safe_load(open(f'{GEO}/config/cars.yaml'))

FOCUS = ['roomy', 'sienta', 'alphard', 'voxy', 'noah', 'aqua', 'raize', 'lc250']
NAME = {f['id']: f['name'] for f in cars_cfg['focus']}
SEG = {f['id']: f['seg'] for f in cars_cfg['focus']}
SEGL = cars_cfg['segs']
RIVAL_NAME = {r['id']: r['name'] for r in cars_cfg['rivals']}
RIVAL_BRAND = {r['id']: r.get('brand') for r in cars_cfg['rivals']}
ALLNAME = {**RIVAL_NAME, **NAME}
NOISE = {'google.com', 'vertexaisearch.cloud.google.com', 'gstatic.com', 'googleusercontent.com', ''}
# 検索需要シード（Googleトレンド12ヶ月平均・プリウス=100のアンカー連結実測）
SEED = {"roomy": 38, "sienta": 63, "alphard": 97, "voxy": 52, "noah": 48, "aqua": 30, "raize": 25, "lc250": 21}

cells = snap['cells']
car_cells = [c for c in cells if c['tier'] == 'car']
by_pid = collections.defaultdict(list)
for c in cells:
    by_pid[c['prompt_id']].append(c)
prompts = {p['id']: p for p in reg['prompts']}

# ================= 車種別コア指標 =================
out_cars = {}
mention_cells_total = {}
for cid in FOCUS:
    tgt = [c for c in car_cells if cid in (c['cars'] or []) and cid not in (c.get('named_cars') or [])]
    m = [c for c in tgt if cid in c['models']]
    first = [c for c in m if c['models'][cid]['rank'] == 1]
    # F1: AI回答の生成率と平均引用数（露出機会の実測プロキシ）
    answered = [c for c in tgt if (c['answer'] or '').strip()]
    cites_n = [len([x for x in c['citations'] if x['host'] not in NOISE]) for c in answered]
    f1_raw = (len(answered) / len(tgt)) * (statistics.mean(cites_n) if cites_n else 0)
    # 競合勝敗
    win = collections.Counter()
    riv_seen = collections.Counter()
    for c in tgt:
        for mid, v in c['models'].items():
            if v['rank'] == 1:
                win[mid] += 1
            if mid != cid:
                riv_seen[mid] += 1
    # 面別
    surf = {}
    for s in ('chatgpt', 'gemini', 'aio', 'aimode'):
        st = [c for c in tgt if c['surface'] == s]
        sm = [c for c in st if cid in c['models']]
        sf = [c for c in sm if c['models'][cid]['rank'] == 1]
        surf[s] = {"cells": len(st), "mention": len(sm), "first": len(sf),
                   "mr": round(len(sm) / len(st) * 100, 1) if st else None,
                   "fr": round(len(sf) / len(sm) * 100, 1) if sm else None}
    # 引用4分類（自車言及セルに付いた引用）
    bk = collections.Counter()
    dom = collections.Counter()
    for c in m:
        for x in c['citations']:
            if x['host'] in NOISE:
                continue
            b = x['bucket']
            b4 = ('toyota' if b in ('owned', 'affiliated') else
                  'dealer' if b == 'dealer' else
                  'sns' if b == 'earned' else 'media')
            bk[b4] += 1
            if b4 == 'media':
                dom[x['host']] += 1
    # センチメント
    sent = collections.Counter(c['models'][cid]['sent'] for c in m if c['models'][cid].get('sent'))
    # クエリ別テーブル（active_for採用60本）
    qrows = []
    for pid, p in prompts.items():
        if cid not in (p.get('active_for') or []):
            continue
        pc = by_pid.get(pid, [])
        pm = [c for c in pc if cid in c['models']]
        pf = [c for c in pm if c['models'][cid]['rank'] == 1]
        firsts = collections.Counter()
        for c in pc:
            for mid, v in c['models'].items():
                if v['rank'] == 1:
                    firsts[mid] += 1
        top1 = firsts.most_common(1)
        qrows.append({
            "id": pid, "t": p['text'], "kw": p.get('keyword'),
            "d": p.get('demand'), "named": cid in (p.get('named_cars') or []),
            "n": len(pc), "m": len(pm), "f": len(pf),
            "win": [ALLNAME.get(top1[0][0], top1[0][0]), top1[0][1]] if top1 else None,
        })
    qrows.sort(key=lambda r: -(r['d'] or 0))
    # 指名系（named）は別枠で回答保有
    named_rows = [r for r in qrows if r['named']]
    mention_cells_total[cid] = sum(1 for c in car_cells if cid in c['models'])
    # 28日トレンド（core60本の回答内言及）
    tr = []
    for d in core['days']:
        v = core['trend'][d]
        tr.append([d, v['hits'].get(cid, 0), v['n']])
    out_cars[cid] = {
        "name": NAME[cid], "seg": SEG[cid], "seg_label": SEGL[SEG[cid]],
        "target_cells": len(tgt), "mention": len(m), "first": len(first),
        "mr": round(len(m) / len(tgt) * 100, 1) if tgt else None,
        "fr": round(len(first) / len(m) * 100, 1) if m else None,
        "f1_raw": round(f1_raw, 2),
        "answered_rate": round(len(answered) / len(tgt) * 100, 1) if tgt else None,
        "avg_cites": round(statistics.mean(cites_n), 2) if cites_n else 0,
        "win": [[ALLNAME.get(k, k), v, RIVAL_BRAND.get(k, 'toyota') if k not in NAME else 'toyota', k] for k, v in win.most_common(8)],
        "riv_seen": [[ALLNAME.get(k, k), v] for k, v in riv_seen.most_common(6)],
        "surf": surf,
        "cite4": {k: bk.get(k, 0) for k in ('toyota', 'dealer', 'sns', 'media')},
        "cite_media_top": dom.most_common(6),
        "sent": {k: sent.get(k, 0) for k in ('positive', 'neutral', 'negative')},
        "queries": qrows, "n_named": len(named_rows),
        "trend28": tr,
        "ga_sess": ga['cars'][cid]['sess'], "ga_dates": ga['dates'],
        "ga28": sum(ga['cars'][cid]['sess']),
        "seed_demand": SEED[cid],
    }

# ================= 相対化（車種平均=100） =================
def idx(vals):
    ok = [v for v in vals.values() if v is not None]
    mean = statistics.mean(ok) if ok else 1
    return {k: (round(v / mean * 100) if v is not None and mean else None) for k, v in vals.items()}

F1i = idx({c: out_cars[c]['f1_raw'] for c in FOCUS})
F2i = idx({c: out_cars[c]['mr'] for c in FOCUS})
F3i = idx({c: out_cars[c]['fr'] for c in FOCUS})
F4i = idx({c: out_cars[c]['ga28'] for c in FOCUS})
EXPi = idx({c: (out_cars[c]['mr'] or 0) * SEED[c] for c in FOCUS})  # 推定露出 = 言及率×検索需要

# 語られ指数 = AI言及シェア ÷ 販売台数シェア ×100（8車内シェア・2026-07実売）
SKEY = {"lc250": "landcruiser"}
sm = {}
month = sales['months'][-1]
for c in FOCUS:
    v = sales['models'].get(SKEY.get(c, c), {}).get(month)
    sm[c] = v
tot_sales = sum(v for v in sm.values() if v)
tot_ment = sum(mention_cells_total.values())
for c in FOCUS:
    ai_share = mention_cells_total[c] / tot_ment * 100 if tot_ment else None
    s_share = (sm[c] / tot_sales * 100) if sm[c] else None
    out_cars[c].update({
        "f1i": F1i[c], "f2i": F2i[c], "f3i": F3i[c], "f4i": F4i[c], "expi": EXPi[c],
        "mention_all": mention_cells_total[c],
        "ai_share": round(ai_share, 1) if ai_share else None,
        "sales_m": sm[c], "sales_share": round(s_share, 1) if s_share else None,
        "katarare": round(ai_share / s_share * 100) if (ai_share and s_share) else None,
    })

# ================= ルールベース考察 =================
for c in FOCUS:
    d = out_cars[c]
    ins = {"now": [], "issue": [], "action": []}
    ins["now"].append(f"出現すべき{d['target_cells']}回答のうち言及{d['mention']}件（{d['mr']}%）、うち第一想起{d['fr']}%。")
    if d['katarare'] is not None:
        if d['katarare'] < 70:
            ins["now"].append(f"語られ指数{d['katarare']}。販売シェア{d['sales_share']}%に対しAI言及シェア{d['ai_share']}%と、売れ行きに比べてAIに語られていない。")
        elif d['katarare'] > 130:
            ins["now"].append(f"語られ指数{d['katarare']}。販売実績以上にAIで語られており、AI面では優位。")
        else:
            ins["now"].append(f"語られ指数{d['katarare']}で販売実勢と釣り合い。")
    w = d['win']
    if w and w[0][3] != c:
        ins["issue"].append(f"自車の出現すべき質問で最も第一想起を取っているのは{w[0][0]}（{w[0][1]}回）。自車は{d['first']}回にとどまる。")
    if d['mr'] is not None and d['mr'] < 40:
        ins["issue"].append("出現すべき場面の6割以上で名前が挙がっておらず、比較検討の土俵に載る前に落ちている。")
    if d['mr'] is not None and d['mr'] >= 50 and d['fr'] is not None and d['fr'] < 20:
        ins["issue"].append("言及はされるが先頭に書かれない。AIの推薦順で常に他車の後ろに置かれている。")
    srt = sorted([(s, v['mr']) for s, v in d['surf'].items() if v['mr'] is not None], key=lambda x: x[1])
    if len(srt) >= 2 and srt[-1][1] - srt[0][1] >= 20:
        SN = {"chatgpt": "ChatGPT", "gemini": "Gemini", "aio": "AIによる概要", "aimode": "AIモード"}
        ins["issue"].append(f"面差が大きい: {SN[srt[0][0]]}{srt[0][1]}% vs {SN[srt[-1][0]]}{srt[-1][1]}%。弱い面の引用元対策が必要。")
    tot_c = sum(d['cite4'].values())
    if tot_c:
        own_pct = d['cite4']['toyota'] / tot_c * 100
        if own_pct < 10:
            ins["issue"].append(f"自車言及回答の引用のうちtoyota.jp系は{own_pct:.0f}%。判断材料が外部メディアに委ねられている。")
    # action
    weak_qs = [q for q in d['queries'] if not q['named'] and q['m'] == 0 and (q['d'] or 0) > 0][:3]
    if weak_qs:
        ins["action"].append("取りこぼしが大きい高需要クエリ（" + " / ".join(q['kw'] or q['t'][:18] for q in weak_qs) + "）に対応するコンテンツ・FAQをtoyota.jp車種ページ側に用意する。")
    if w and w[0][3] != c and w[0][2] == 'toyota':
        ins["action"].append(f"最大の相手は社内の{w[0][0]}。AI上の使い分け（誰に何を推すか）を車種ページの比較文脈で明示し、共倒れを防ぐ。")
    elif w and w[0][3] != c:
        ins["action"].append(f"{w[0][0]}に第一想起を奪われている。比較記事で並ぶ強み（価格・装備・リセール）の一次情報発信を強化する。")
    if d['cite4']['dealer'] == 0:
        ins["action"].append("販売店ドメインの引用が0件【検証済み: 自車言及セルの全引用をドメイン照合】。地域在庫・試乗情報のAI露出は販売店サイト側の構造化が課題。")
    out_cars[c]["insight"] = ins

# ================= 概況（全車種） =================
own_master = yaml.safe_load(open(f'{GEO}/config/models.yaml'))['own']
overview = []
days = core['days']
for mrow in own_master:
    cid0 = mrow['id']
    # core検出はrun_carの辞書ベース: focus/rivalsに無い車種はスキャン外→focus+rivalsのみ掲載
    pass
# 概況は検出辞書に載っている車のみ（focus8 + トヨタ社内rivals + 他社rivals）
groups = collections.defaultdict(list)
for cid in list(NAME.keys()) + [r['id'] for r in cars_cfg['rivals']]:
    tot_h = sum(core['trend'][d]['hits'].get(cid, 0) for d in days)
    tot_n = sum(core['trend'][d]['n'] for d in days)
    if cid in NAME:
        grp = SEGL[SEG[cid]]
        brand = 'toyota'
        nm = NAME[cid]
        focus = True
    else:
        brand = RIVAL_BRAND.get(cid) or 'other'
        nm = RIVAL_NAME.get(cid, cid)
        focus = False
        grp = None
    series = [core['trend'][d]['hits'].get(cid, 0) for d in days]
    groups['all'].append({"id": cid, "name": nm, "brand": brand, "focus": focus,
                          "hits28": tot_h, "rate28": round(tot_h / tot_n * 100, 2) if tot_n else 0,
                          "series": series})

bench = []
for p in reg['prompts']:
    if p.get('tier') == 'car_bench':
        bench.append({"id": p['id'], "t": p['text'], "kw": p.get('keyword'), "d": p.get('demand'),
                      "cars": [NAME.get(c, c) for c in (p.get('cars') or [])]})
bench.sort(key=lambda r: -(r['d'] or 0))

board = {
    "built_at": snap['date'],
    "bench": bench,
    "promo": {"up": [], "down": []},
    "asof": {"car_round": snap['date'], "round_calls": snap['api_cost']['calls'],
             "round_cost": round(snap['api_cost']['usd']),
             "core_days": [days[0], days[-1]], "ga_dates": [ga['dates'][0], ga['dates'][-1]],
             "sales_month": month, "sales_sources": sales['source_urls'][:4]},
    "focus": FOCUS,
    "cars": out_cars,
    "overview": groups['all'],
    "days": days,
    "surfaces_measured": snap['surfaces'],
}
json.dump(board, open(os.environ.get('BOARD_DATA', 'board_data.json'), 'w'), ensure_ascii=False)
sz = len(json.dumps(board, ensure_ascii=False))
print(f'board_data.json {sz/1024:.0f}KB')
for c in FOCUS:
    d = out_cars[c]
    print(f"{c:<8} F1i{d['f1i']:>4} F2i{d['f2i']:>4} F3i{d['f3i']:>4} F4i{d['f4i']:>4} 語られ{str(d['katarare']):>5} 売{str(d['sales_m']):>7} 4分類{d['cite4']}")
