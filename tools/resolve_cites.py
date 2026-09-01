#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI回答の引用に混じるリダイレクタURLを、実URLに解決してキャッシュする。

背景（実測 2026-08-28 の car-round）:
  ChatGPT の引用は実URLで返るので公式/競合の判定が効く。一方 Google 系3面は
    Gemini      … vertexaisearch.cloud.google.com/grounding-api-redirect/…  3,907件
    AIによる概要 … google.com/goto?url=CAES…                                2,604件
    AIモード     … 同上                                                     1,713件
  と全部リダイレクタで返るため、そのままでは「不明率100%」になり、
  この3面の引用実態（誰が根拠にされているか）を一切語れない。
  リダイレクタは 302 の Location に実URLを持っているので、辿れば復元できる。

設計:
  - 解決結果は data/cite_resolved.json に永続キャッシュする（URLは不変なので再解決不要）
  - 1回の実行で解決する件数と実行時間に上限を置き、CIを詰まらせない（残りは翌日に持ち越す）
  - 失敗したURLは失敗として記録し、毎日無駄に叩き直さない（RETRY_AFTER 日で再挑戦）
  - ネットワークが無い環境ではキャッシュだけ読んで正常終了する（画面は「不明」のまま）

使い方:
  GEO_REPO=/tmp/gb CACHE=data/cite_resolved.json python3 tools/resolve_cites.py
"""
import glob
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

GEO = os.environ.get("GEO_REPO", "/tmp/gb")
CACHE = os.environ.get("CITE_CACHE", "data/cite_resolved.json")
MAX_RESOLVE = int(os.environ.get("CITE_MAX", "9000"))     # 1回で解決する上限
BUDGET_SEC = int(os.environ.get("CITE_BUDGET", "900"))    # 全体の時間予算
WORKERS = int(os.environ.get("CITE_WORKERS", "12"))
RETRY_AFTER_DAYS = 7

REDIR_MARKS = ("vertexaisearch.cloud.google.com", "grounding-api-redirect",
               "google.com/goto", "google.com/url")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0 Safari/537.36")


def is_redirector(url: str) -> bool:
    u = (url or "").lower()
    return u.startswith(("http://", "https://")) and any(m in u for m in REDIR_MARKS)


def load_cache(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {"resolved": {}, "failed": {}}


def resolve_one(session, url, depth=0):
    """302 を辿って実URLを返す。辿れなければ空文字。"""
    if depth > 4:
        return ""
    try:
        r = session.get(url, allow_redirects=False, timeout=12,
                        headers={"User-Agent": UA, "Accept": "*/*"})
    except Exception:
        return ""
    loc = r.headers.get("Location") or r.headers.get("location") or ""
    if r.status_code in (301, 302, 303, 307, 308) and loc:
        if any(m in loc.lower() for m in REDIR_MARKS):
            return resolve_one(session, loc, depth + 1)
        return loc
    if r.status_code == 200:
        # まれに meta refresh / JS 遷移。HTML から実URLを拾えるか試す。
        body = (r.text or "")[:4000]
        for key in ('url=', 'URL='):
            i = body.find('http-equiv="refresh"')
            if i > 0:
                j = body.find(key, i)
                if j > 0:
                    cand = body[j + len(key):].split('"')[0].split("'")[0].strip()
                    if cand.startswith("http"):
                        return cand
        return ""
    return ""


def main():
    snaps = sorted(glob.glob(os.path.join(GEO, "data", "car", "snapshots", "*.json")))
    if not snaps:
        print("スナップショットなし。何もしない")
        return
    urls = set()
    for p in snaps:
        try:
            snap = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        for c in snap.get("cells", []):
            for x in (c.get("citations") or []):
                u = x.get("url") or ""
                if is_redirector(u):
                    urls.add(u)
    cache = load_cache(CACHE)
    done = cache.setdefault("resolved", {})
    failed = cache.setdefault("failed", {})
    now = time.time()
    todo = [u for u in urls
            if u not in done and now - failed.get(u, 0) > RETRY_AFTER_DAYS * 86400]
    print(f"リダイレクタURL {len(urls)}件 / 解決済み {len(done)} / 今回対象 {len(todo)}")
    if not todo:
        os.makedirs(os.path.dirname(CACHE) or ".", exist_ok=True)
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        return

    try:
        import requests
    except ImportError:
        print("requests が無いためスキップ")
        return
    session = requests.Session()
    todo = todo[:MAX_RESOLVE]
    t0 = time.time()
    ok = 0

    def work(u):
        if time.time() - t0 > BUDGET_SEC:
            return u, ""
        return u, resolve_one(session, u)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, (u, real) in enumerate(ex.map(work, todo), 1):
            if real:
                done[u] = real
                ok += 1
            else:
                failed[u] = now
            if i % 500 == 0:
                print(f"  {i}/{len(todo)} 解決 {ok}件 ({int(time.time()-t0)}秒)", flush=True)

    os.makedirs(os.path.dirname(CACHE) or ".", exist_ok=True)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"解決 {ok}/{len(todo)} 件（累計 {len(done)}件）／{int(time.time()-t0)}秒 → {CACHE}")


if __name__ == "__main__":
    sys.exit(main())
