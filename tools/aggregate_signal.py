#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIGNAL ROOM 用の実測集計。

入力:
  GEO_REPO    … toyota-geo-board のパス（snapshots / registry / search_volumes を読む）
  BOARD_DATA  … aggregate_board.py の出力（既定 board_data.json）
出力:
  SIGNAL_DATA … signal_data.json

規律: 推定値・デモ値を作らない。指名クエリ（named_cars）は当該車の分母・分子から除外。
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict

GEO = os.environ.get("GEO_REPO", "/tmp/gb")
BD_PATH = os.environ.get("BOARD_DATA", "board_data.json")
OUT = os.environ.get("SIGNAL_DATA", "signal_data.json")

bd = json.load(open(BD_PATH, encoding="utf-8"))
snap_path = sorted(glob.glob(os.path.join(GEO, "data", "car", "snapshots", "*.json")))[-1]
snap = json.load(open(snap_path, encoding="utf-8"))

# 計測時のカタログではなく“現行の”カタログで引き直す（誤検出修正・ブランド統合を遡及適用）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redetect import redetect  # noqa: E402
_n, _stat = redetect(snap["cells"], GEO)
print(f"再検出(signal): {_stat['cells_changed']}セル更新 (+{_stat['detections_added']} / -{_stat['detections_removed']})")

# リダイレクタ（Gemini/AIによる概要/AIモードの引用）を解決済みキャッシュで実URLに差し替える。
# ここで直しておくと、不明率・引用元カタログ・ホスト別集計がすべて実態に変わる。
_cite_cache_path = os.environ.get("CITE_CACHE", "data/cite_resolved.json")
try:
    _cmap = json.load(open(_cite_cache_path, encoding="utf-8")).get("resolved", {})
except Exception:
    _cmap = {}
if _cmap:
    sys.path.insert(0, os.path.join(GEO, "src"))
    try:
        from analyze import classify_url  # noqa: E402
    except Exception:
        classify_url = None
    _swapped = 0
    for _c in snap["cells"]:
        for _x in (_c.get("citations") or []):
            _real = _cmap.get(_x.get("url") or "")
            if not _real:
                continue
            _x["url"] = _real
            if classify_url:
                _cl = classify_url(_real)
                _x["host"], _x["bucket"] = _cl["host"], _cl["bucket"]
                _x["platform"] = _cl.get("platform")
            _swapped += 1
    print(f"引用リダイレクタ解決: {_swapped}件を実URLに差し替え（キャッシュ {len(_cmap)}件）")
else:
    print("引用リダイレクタ解決: キャッシュなし（Google系3面は「不明」のまま）")

cells = [c for c in snap["cells"] if c.get("tier") == "car"]

NAME = {o["id"]: o["name"] for o in bd["overview"]}
BRAND = {o["id"]: o["brand"] for o in bd["overview"]}
FOCUS = list(bd["cars"].keys())
CAT = {"safety": "安全", "eco": "燃費・環境", "cost": "費用", "model": "モデル比較",
       "service": "サービス", "brand": "ブランド", "purchase": "購入検討"}
SEGCARS = {
    "compact_tall": ["roomy", "thor", "solio", "delica_mini"],
    "minivan_s": ["sienta", "freed"],
    "minivan_m": ["voxy", "noah", "serena", "stepwgn"],
    "minivan_l": ["alphard", "vellfire", "elgrand"],
    "compact_hb": ["aqua", "yaris", "fit", "note"],
    "suv_compact": ["raize", "yariscross", "rocky", "crossbee", "wrv"],
    # lc300/lc70/prado は lc250（ランドクルーザー）に統合済み
    "suv_off": ["lc250", "rav4", "jimny_sierra", "xtrail", "outlander"],
}
SEGLABEL = {"compact_tall": "コンパクトトール", "minivan_s": "スモールミニバン", "minivan_m": "ミドルミニバン",
            "minivan_l": "ラージミニバン", "compact_hb": "コンパクト", "suv_compact": "コンパクトSUV",
            "suv_off": "本格オフローダー/SUV", "cross": "車型横断"}

pid_cat, pid_seg = {}, {}
for c in cells:
    pid_cat[c["prompt_id"]] = c.get("category")
    pid_seg[c["prompt_id"]] = c.get("seg")
segcells = defaultdict(list)
for c in cells:
    segcells[c["seg"]].append(c)

# ---------- 車型別集計 ----------
def agg_seg(seg):
    cs = segcells[seg]
    n = len(cs)
    answered = sum(1 for c in cs if (c.get("answer") or "").strip())
    dens_sum = dens_n = 0
    mention, first, den = defaultdict(int), defaultdict(int), defaultdict(int)
    first_total = 0
    for c in cs:
        named = set(c.get("named_cars") or [])
        eligible = {m: v for m, v in (c.get("models") or {}).items() if m not in named}
        if (c.get("answer") or "").strip():
            dens_sum += len(eligible); dens_n += 1
        for car in SEGCARS.get(seg, []):
            if car not in named:
                den[car] += 1
        for m in eligible:
            mention[m] += 1
        if eligible:
            top = min(eligible.items(), key=lambda kv: kv[1].get("rank", 999))[0]
            first[top] += 1; first_total += 1
    rows = []
    for car in SEGCARS.get(seg, []):
        d = den[car] or 1
        rows.append({"id": car, "name": NAME.get(car, car), "brand": BRAND.get(car, ""),
                     "mr": round(100 * mention[car] / d, 1), "mentions": mention[car],
                     "firsts": first[car],
                     "fshare": round(100 * first[car] / first_total, 1) if first_total else 0.0,
                     "den": den[car]})
    rows.sort(key=lambda r: -r["mr"])
    ty_m = sum(mention[c] for c in SEGCARS.get(seg, []) if BRAND.get(c) == "toyota")
    all_m = sum(mention[c] for c in SEGCARS.get(seg, [])) or 1
    ty_f = sum(first[c] for c in SEGCARS.get(seg, []) if BRAND.get(c) == "toyota")
    all_f = sum(first[c] for c in SEGCARS.get(seg, [])) or 1
    return {"seg": seg, "label": SEGLABEL[seg], "cells": n,
            "answered_rate": round(100 * answered / n, 1) if n else 0,
            "density": round(dens_sum / dens_n, 2) if dens_n else 0,
            "toyota_sov": round(100 * ty_m / all_m, 1), "toyota_fsov": round(100 * ty_f / all_f, 1),
            "rows": rows, "first_total": first_total}

segs_out = [agg_seg(s) for s in SEGCARS]

# ---------- 車型横断 ----------
cross_cells = segcells.get("cross", [])
cb_m, cb_f, car_m = Counter(), Counter(), Counter()
ft = dens_sum = dens_n = 0
for c in cross_cells:
    named = set(c.get("named_cars") or [])
    eligible = {m: v for m, v in (c.get("models") or {}).items() if m not in named}
    if (c.get("answer") or "").strip():
        dens_sum += len(eligible); dens_n += 1
    for m in eligible:
        cb_m[BRAND.get(m, "?")] += 1; car_m[m] += 1
    if eligible:
        top = min(eligible.items(), key=lambda kv: kv[1].get("rank", 999))[0]
        cb_f[BRAND.get(top, "?")] += 1; ft += 1
tot = sum(cb_m.values()) or 1
cross_out = {"cells": len(cross_cells), "density": round(dens_sum / dens_n, 2) if dens_n else 0,
             "brand_sov": sorted([{"brand": b, "sov": round(100 * v / tot, 1), "mentions": v}
                                  for b, v in cb_m.items()], key=lambda x: -x["sov"]),
             "brand_fsov": sorted([{"brand": b, "fshare": round(100 * v / max(ft, 1), 1)}
                                   for b, v in cb_f.items()], key=lambda x: -x["fshare"]),
             "top_cars": sorted([{"id": m, "name": NAME.get(m, m), "brand": BRAND.get(m, ""), "mentions": v}
                                 for m, v in car_m.items()], key=lambda x: -x["mentions"])[:12]}

# ---------- GA ----------
ga = []
for cid, cv in bd["cars"].items():
    ga.append({"id": cid, "name": cv["name"], "seg": cv["seg"], "mr": cv["mr"], "fr": cv["fr"],
               "ai_share": cv["ai_share"], "sales_share": cv["sales_share"], "katarare": cv["katarare"],
               "ga28": cv["ga28"], "f2i": cv["f2i"], "f3i": cv["f3i"], "f4i": cv["f4i"], "expi": cv["expi"],
               "trend28": cv["trend28"], "ga_sess": cv["ga_sess"], "ga_dates": cv["ga_dates"],
               "sales_m": cv["sales_m"]})
ga_total = sum(g["ga28"] for g in ga) or 1
for g in ga:
    g["ga_share"] = round(100 * g["ga28"] / ga_total, 1)

# ---------- カテゴリ×車種 / AI面×車種 / 好意率 ----------
catmat, surfmat, posrate = {}, {}, {}
for car in FOCUS:
    d, m = defaultdict(int), defaultdict(int)
    sd, sm_, sf = defaultdict(int), defaultdict(int), defaultdict(int)
    pm = pp = 0
    for c in cells:
        named = set(c.get("named_cars") or [])
        if car in named:
            continue
        mods = {k: v for k, v in (c.get("models") or {}).items() if k not in named}
        if car in mods:
            pm += 1
            if mods[car].get("sent") == "positive":
                pp += 1
        if car not in c.get("cars", []):
            continue
        cat = c.get("category") or "model"
        d[cat] += 1
        s = c["surface"]; sd[s] += 1
        if car in mods:
            m[cat] += 1; sm_[s] += 1
            top = min(mods.items(), key=lambda kv: kv[1].get("rank", 999))[0]
            if top == car:
                sf[s] += 1
    catmat[car] = {k: {"den": d[k], "m": m[k], "mr": round(100 * m[k] / d[k], 1) if d[k] else None} for k in CAT}
    surfmat[car] = {s: {"den": sd[s], "mr": round(100 * sm_[s] / sd[s], 1) if sd[s] else None,
                        "fr": round(100 * sf[s] / sd[s], 1) if sd[s] else None}
                    for s in ["chatgpt", "gemini", "aio", "aimode"]}
    posrate[car] = round(100 * pp / pm, 1) if pm else None

# ---------- 引用 ----------
OFFICIAL = {"toyota.jp": "toyota", "global.toyota": "toyota", "honda.co.jp": "honda", "global.honda": "honda",
            "www3.nissan.co.jp": "nissan", "www2.nissan.co.jp": "nissan", "nissan.co.jp": "nissan",
            "suzuki.co.jp": "suzuki", "daihatsu.co.jp": "daihatsu", "mitsubishi-motors.co.jp": "mitsubishi"}
REDIR = {"google.com", "vertexaisearch.cloud.google.com"}

def cite_pack(cs):
    bucket, host = Counter(), Counter()
    own = comp = deal = total = redir = 0
    for c in cs:
        for x in (c.get("citations") or []):
            total += 1
            b = x.get("bucket") or "—"; bucket[b] += 1
            h = x.get("host") or ""
            if h in REDIR:
                redir += 1
            else:
                host[h] += 1
            if b == "owned" or OFFICIAL.get(h) == "toyota":
                own += 1
            elif b == "competitor" or OFFICIAL.get(h) in ("honda", "nissan", "suzuki", "daihatsu", "mitsubishi"):
                comp += 1
            elif b == "dealer":
                deal += 1
    return {"total": total, "redir": redir, "bucket": dict(bucket), "own": own, "comp": comp, "dealer": deal,
            "top_hosts": [[h, n] for h, n in host.most_common(14) if h]}

cite_all = cite_pack(cells)
cite_car = {car: cite_pack([c for c in cells if car in c.get("cars", [])]) for car in FOCUS}
cite_surf = {s: cite_pack([c for c in cells if c["surface"] == s]) for s in ["chatgpt", "gemini", "aio", "aimode"]}
pagec, pageq = Counter(), defaultdict(set)
for c in cells:
    for p in (c.get("cited_car_pages") or []):
        u = p if isinstance(p, str) else p.get("url", "")
        pagec[u] += 1; pageq[u].add(c["prompt_id"])
# cited_car_pages は車種ID（"sienta"）で保存されている。画面でリンクにするため
# cars.yaml の slug から toyota.jp の実URLに直す（ID のままだと href="sienta" の壊れたリンクになる）。
import yaml as _yaml  # noqa: E402
_cars_cfg = _yaml.safe_load(open(os.path.join(GEO, "config", "cars.yaml"), encoding="utf-8"))
_SLUG = {c["id"]: c.get("slug") for c in _cars_cfg["focus"]}
_URL = {c["id"]: c.get("url") for c in _cars_cfg["focus"]}
_CARNAME = {c["id"]: c["name"] for c in _cars_cfg["focus"]}


def _page_url(key):
    if str(key).startswith("http"):
        return key
    if _URL.get(key):
        return _URL[key]
    slug = _SLUG.get(key)
    return f"https://toyota.jp{slug}/" if slug else None


cited_pages = [[_page_url(u), _CARNAME.get(u, u), n, len(pageq[u])]
               for u, n in pagec.most_common(12)]

def classify(h):
    if not h or h in REDIR: return "unknown"
    if h in ("toyota.jp", "global.toyota"): return "toyota"
    if h in ("honda.co.jp", "global.honda", "www3.nissan.co.jp", "www2.nissan.co.jp", "nissan.co.jp",
             "suzuki.co.jp", "daihatsu.co.jp", "mitsubishi-motors.co.jp"): return "rival"
    if "wikipedia" in h: return "wiki"
    if any(x in h for x in ("youtube.", "tiktok", "instagram", "twitter", "x.com", "chiebukuro", "minkara", "note.com", "ameblo")): return "sns"
    if any(x in h for x in ("toyota", "netz")) and h.endswith(".co.jp"): return "dealer"
    if any(x in h for x in ("kakaku", "goo-net", "carsensor", "bestcar", "autoc-one", "car.watch", "response.jp",
                            "kuruma-news", "carview", "webcg", "motor-fan", "clicccar", "cartop", "gazoo")): return "media3rd"
    return "other"

CATLABEL = {"toyota": "トヨタ公式", "rival": "競合公式", "dealer": "販売店(DMS)", "media3rd": "第三者サイト",
            "wiki": "Wikipedia", "sns": "SNS・UGC", "other": "その他実URL", "unknown": "発信元不明"}
doms = defaultdict(lambda: {"n": 0, "samples": []})
catn = Counter()
for c in cells:
    for x in (c.get("citations") or []):
        h = x.get("host") or ""
        cl = classify(h)
        catn[cl] += 1
        if cl == "unknown":
            continue
        d = doms[h]; d["n"] += 1; d["cat"] = cl
        if len(d["samples"]) < 3 and x.get("url") and x.get("title"):
            d["samples"].append({"t": x["title"][:70], "u": x["url"], "pid": c["prompt_id"]})
domcat = defaultdict(list)
for h, v in doms.items():
    domcat[v["cat"]].append({"h": h, "n": v["n"], "s": v["samples"]})
for k in domcat:
    domcat[k].sort(key=lambda x: -x["n"])
citecatalog = {"counts": {k: catn.get(k, 0) for k in CATLABEL}, "labels": CATLABEL,
               "domains": {k: v[:10] for k, v in domcat.items()}}

# ---------- 語彙（車名±250字の共起） ----------
AXES = {"価格・コスパ": ["価格", "安い", "コスパ", "リーズナブル", "予算", "値引"],
        "燃費": ["燃費", "km/L", "低燃費", "電費"],
        "広さ・室内": ["広い", "広さ", "室内", "荷室", "ラゲッジ", "積載", "3列"],
        "安全装備": ["安全", "セーフティ", "衝突", "運転支援", "サポカー"],
        "走行性能": ["走り", "加速", "走行", "パワー", "静粛"],
        "取り回し": ["取り回し", "小回り", "運転しやすい", "コンパクト", "5ナンバー"],
        "装備・快適": ["装備", "快適", "使い勝手", "便利"],
        "デザイン": ["デザイン", "見た目", "スタイリング", "おしゃれ", "かっこ"],
        "リセール": ["リセール", "下取り", "資産価値", "値落ち"]}
ALIAS = {"roomy": ["ルーミー"], "sienta": ["シエンタ"], "alphard": ["アルファード"],
         "voxy": ["ヴォクシー", "ボクシー"], "noah": ["ノア"], "aqua": ["アクア"],
         "raize": ["ライズ"], "lc250": ["ランドクルーザー250", "ランクル250"]}
vocab = {}
for car in FOCUS:
    hits = defaultdict(int); den = 0
    for c in cells:
        named = set(c.get("named_cars") or [])
        if car in named or car not in (c.get("models") or {}):
            continue
        a = c.get("answer") or ""
        spans = []
        for al in ALIAS.get(car, []):
            for mt in re.finditer(re.escape(al), a):
                spans.append(a[max(0, mt.start() - 250):mt.end() + 250])
        if not spans:
            continue
        den += 1; ctx = " ".join(spans)
        for ax, words in AXES.items():
            if any(w in ctx for w in words):
                hits[ax] += 1
    vocab[car] = {"den": den, "axes": {ax: round(100 * hits[ax] / den, 1) if den else 0 for ax in AXES}}

# ---------- OEM・兄弟 ----------
def pair_stats(a, b, seg):
    both = onlya = onlyb = either = 0
    for c in segcells[seg]:
        named = set(c.get("named_cars") or [])
        mods = set(k for k in (c.get("models") or {}) if k not in named)
        A, B = a in mods, b in mods
        if A or B: either += 1
        if A and B: both += 1
        elif A: onlya += 1
        elif B: onlyb += 1
    return {"both": both, "onlya": onlya, "onlyb": onlyb, "either": either}

oem = {"roomy_thor": {**pair_stats("roomy", "thor", "compact_tall"), "a": "ルーミー", "b": "トール", "note": "同一車（ダイハツ製造のOEM兄弟）"},
       "noah_voxy": {**pair_stats("noah", "voxy", "minivan_m"), "a": "ノア", "b": "ヴォクシー", "note": "兄弟車（同一プラットフォーム）"},
       "alphard_vellfire": {**pair_stats("alphard", "vellfire", "minivan_l"), "a": "アルファード", "b": "ヴェルファイア", "note": "兄弟車"}}

# ---------- 検索ボリューム（DataForSEO実測） ----------
volumes = {}
vol_path = os.path.join(GEO, "data", "search_volumes.json")
if os.path.exists(vol_path):
    try:
        volumes = json.load(open(vol_path, encoding="utf-8")).get("volumes", {})
    except Exception:
        volumes = {}
pid_kw = {}
try:
    import yaml
    reg = yaml.safe_load(open(os.path.join(GEO, "prompts", "registry.yaml"), encoding="utf-8"))
    for p in reg.get("prompts", []):
        if p.get("keyword"):
            pid_kw[p["id"]] = p["keyword"]
except Exception:
    pass

# ---------- 質問リスト（bd由来 + カテゴリ + vol） ----------
queries = {}
for car in FOCUS:
    qs = []
    for q in bd["cars"][car]["queries"]:
        kw = pid_kw.get(q["id"], "")
        vol = volumes.get(kw)
        qs.append({"id": q["id"], "t": q["t"], "named": q.get("named", False), "n": q.get("n", 0),
                   "m": q.get("m", 0), "f": q.get("f", 0), "win": q.get("win"),
                   "cat": CAT.get(pid_cat.get(q["id"]) or "", "—"), "kw": kw,
                   "vol": int(vol) if vol else None})
    queries[car] = qs

# ---------- ファネル ----------
funnel = []
for cid, cv in bd["cars"].items():
    fs = {"F1": cv["f1i"], "F2": cv["f2i"], "F3": cv["f3i"], "F4": cv["f4i"]}
    bott = min(fs, key=fs.get)
    funnel.append({"id": cid, "name": cv["name"], "seg": cv["seg"], "f1": cv["f1i"], "f2": cv["f2i"],
                   "f3": cv["f3i"], "f4": cv["f4i"], "expi": cv["expi"], "katarare": cv["katarare"],
                   "mr": cv["mr"], "fr": cv["fr"], "bottleneck": bott, "bv": fs[bott],
                   "ai_share": cv["ai_share"], "ga28": cv["ga28"], "sales_m": cv["sales_m"],
                   "sales_share": cv["sales_share"], "answered_rate": cv["answered_rate"],
                   "avg_cites": cv["avg_cites"], "target_cells": cv["target_cells"],
                   "mention": cv["mention"], "first": cv["first"], "pos_rate": posrate[cid],
                   # 打ち手の生成に使う: 先を越している競合と、公式ページの置き場所
                   "win": cv.get("win") or [], "slug": _SLUG.get(cid) or ("/" + cid),
                   "url": _page_url(cid)})

# ---------- 全クエリ4面詳細 ----------
qtext = {}
for cid in FOCUS:
    for q in bd["cars"][cid]["queries"]:
        qtext[q["id"]] = q["t"]
for b_ in bd.get("bench", []):
    qtext.setdefault(b_["id"], b_["t"])
qd = {}
for c in cells:
    pid = c["prompt_id"]
    if pid not in qd:
        qd[pid] = {"q": qtext.get(pid, ""), "cat": c.get("category"), "seg": c.get("seg"),
                   "cars": c.get("cars", []), "named": c.get("named_cars", []), "s": {}}
    named = set(c.get("named_cars") or [])
    order = sorted([(v.get("rank", 999), m, v.get("sent")) for m, v in (c.get("models") or {}).items()],
                   key=lambda x: x[0])[:6]
    ans = (c.get("answer") or "").strip()
    qd[pid]["s"][c["surface"]] = {
        "a": ans[:260] + ("…" if len(ans) > 260 else ""),
        "o": [{"id": m, "n": NAME.get(m, m), "b": BRAND.get(m, ""), "r": r, "x": m in named, "st": st}
              for r, m, st in order],
        "c": [{"t": (x.get("title") or x.get("host") or "")[:70], "h": x.get("host"),
               "u": x.get("url"), "b": x.get("bucket")} for x in (c.get("citations") or [])[:3]]}

# ---------- レーダー用 seg×cat×car ----------
segcat = {}
for seg, carlist in SEGCARS.items():
    out = {}
    for k in CAT:
        kcells = [c for c in segcells[seg] if c.get("category") == k]
        row = {}
        for car in carlist:
            den = m = first = 0
            for c in kcells:
                named = set(c.get("named_cars") or [])
                if car in named:
                    continue
                den += 1
                mods = {x: v for x, v in (c.get("models") or {}).items() if x not in named}
                if car in mods:
                    m += 1
                    top = min(mods.items(), key=lambda kv: kv[1].get("rank", 999))[0]
                    if top == car:
                        first += 1
            row[car] = {"den": den, "m": m, "mr": round(100 * m / den, 1) if den else None,
                        "fr": round(100 * first / m, 1) if m else None}
        out[k] = row
    segcat[seg] = out
rival_of = {}
for s in segs_out:
    nt = [r for r in s["rows"] if r["brand"] != "toyota"]
    top = max(nt, key=lambda r: r["mentions"]) if nt else None
    for r in s["rows"]:
        if r["brand"] == "toyota" and r["id"] in FOCUS:
            rival_of[r["id"]] = top["id"] if top else None

# ---------- ドロワー（実回答の同梱） ----------
def pick(car, seg, cond, tag):
    by = defaultdict(dict)
    for c in segcells[seg]:
        if car in set(c.get("named_cars") or []):
            continue
        by[c["prompt_id"]][c["surface"]] = c
    for pid, sur in by.items():
        if len(sur) < 4:
            continue
        ranks = [((c.get("models") or {}).get(car) or {}).get("rank") for c in sur.values()]
        if cond(ranks):
            item = {"pid": pid, "tag": tag, "category": CAT.get(pid_cat.get(pid) or "", "—"), "surfaces": {}}
            for s in ["chatgpt", "gemini", "aio", "aimode"]:
                c = sur.get(s)
                if not c:
                    continue
                named = set(c.get("named_cars") or [])
                order = sorted([(v.get("rank", 999), m) for m, v in (c.get("models") or {}).items()
                                if m not in named])
                item["surfaces"][s] = {
                    "answer": (c.get("answer") or "").strip(),
                    "order": [{"id": m, "name": NAME.get(m, m), "brand": BRAND.get(m, ""), "rank": r}
                              for r, m in order],
                    "cites": [{"title": (x.get("title") or "")[:90], "host": x.get("host"),
                               "bucket": x.get("bucket"), "url": x.get("url")}
                              for x in (c.get("citations") or [])[:6]]}
            item["q"] = qtext.get(pid, "")
            return item
    return None

drawer = {}
specs = [
    ("raize", "suv_compact", lambda r: all(x is None for x in r), "absent"),
    ("raize", "suv_compact", lambda r: sum(1 for x in r if x) >= 3 and all(x is None or x >= 2 for x in r), "behind"),
    ("raize", "suv_compact", lambda r: any(x == 1 for x in r if x), "win"),
    ("roomy", "compact_tall", lambda r: sum(1 for x in r if x) >= 2 and all(x is None or x >= 2 for x in r), "behind"),
    ("sienta", "minivan_s", lambda r: sum(1 for x in r if x) >= 3 and all(x is None or x >= 2 for x in r), "behind"),
    ("voxy", "minivan_m", lambda r: sum(1 for x in r if x) >= 2 and all(x is None or x >= 2 for x in r), "behind"),
]
used = set()
for car, seg, cond, tag in specs:
    it = pick(car, seg, lambda r, c=cond: c(r), tag)
    if it and (car, it["pid"]) not in used:
        used.add((car, it["pid"]))
        drawer.setdefault(car, []).append(it)

# ---------- 30車種トレンド ----------
ovtrend = [{"id": o["id"], "name": o["name"], "brand": o["brand"], "focus": o.get("focus", False),
            "hits28": o["hits28"], "series": o["series"]} for o in bd["overview"]]

out = {"built": snap["date"], "built_at": bd.get("built_at"), "segs": segs_out, "cross": cross_out,
       "ga": ga, "days": bd["days"], "kpi": {"cells": len(cells), "prompts": snap.get("n_prompts"), "focus": len(FOCUS)},
       "catmat": catmat, "cat_labels": CAT, "surfmat": surfmat,
       "cite": {"all": cite_all, "car": cite_car, "surf": cite_surf, "pages": cited_pages},
       "vocab": vocab, "axes": list(AXES.keys()), "oem": oem, "queries": queries, "funnel": funnel,
       "drawer": drawer, "qdetail": qd, "segcat": segcat, "rival_of": rival_of,
       "citecatalog": citecatalog, "ovtrend": ovtrend,
       "vol_meta": {"available": bool(volumes), "n": len(volumes)}}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print(f"signal_data: {OUT} {os.path.getsize(OUT)//1024}KB / cells={len(cells)} / snapshot={os.path.basename(snap_path)} / volumes={'あり('+str(len(volumes))+'kw)' if volumes else 'なし'}")
