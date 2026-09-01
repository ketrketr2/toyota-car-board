#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""保存済み回答本文から、車種検出を現行カタログで“引き直す”。

なぜ必要か:
  car-round のスナップショットは、計測した時点の cars.yaml で検出した結果
  （cell["models"]）をそのまま持っている。あとから誤検出（例:「トールワゴン」を
  ダイハツ・トールと数えていた）やブランド統合（ランクル250/300/70/プラド）を
  直しても、回答本文は保存されているのに数字が直らない。
  1周 $38 を払って再計測しなくても、本文から引き直せば遡及して正しくなる。

規律: 本文が無いセルには触らない（推定で埋めない）。
"""
import os
import sys


def redetect(cells, geo_repo=None):
    """cells の models を現行 cars.yaml で引き直す。戻り値は (変更セル数, 統計)。"""
    geo = geo_repo or os.environ.get("GEO_REPO", "/tmp/gb")
    sys.path.insert(0, os.path.join(geo, "src"))
    from run_car import detect_cars, _catalog  # noqa: E402

    catalog = _catalog()
    changed = 0
    added, removed = 0, 0
    for c in cells:
        ans = c.get("answer")
        if not ans:
            continue
        before = c.get("models") or {}
        after = detect_cars(ans, catalog)
        if after != before:
            changed += 1
            added += len(set(after) - set(before))
            removed += len(set(before) - set(after))
            c["models"] = after
        # cars（そのクエリが対象とする車種）は registry 由来なので触らない。
        # ただし統合で消えた id が残っていると集計側で迷子になるため落とす。
        ids = {row["id"] for row in catalog}
        if c.get("cars"):
            c["cars"] = [x for x in c["cars"] if x in ids]
        if c.get("named_cars"):
            c["named_cars"] = [x for x in c["named_cars"] if x in ids]
    return changed, {"cells_changed": changed, "detections_added": added,
                     "detections_removed": removed}
