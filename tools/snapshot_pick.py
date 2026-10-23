#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""car-round のスナップショットから「車種ボードに使える回」を選ぶ。

背景（2026-10-23 修正）
  これまでは data/car/snapshots/ の一番新しいファイルをそのまま使っていた。
  2026-09-09 の回は販売店・地域クエリ（tier=local）だけを測った回で、車種クエリ（tier=car）を含まない。
  そのため 09-09 以降、車種別AI分析・SIGNAL ROOM の AI指標が全車「未計測（—）」のまま毎日公開されていた。
規則
  tier=car のセルを含む回のうち、最も新しいものを使う（local だけの回は飛ばす）。
  car の回が1つも無いときだけ、従来どおり最新の回を返す（画面は「未計測」と正直に出る）。
"""
import glob
import json
import os


def has_car(snap: dict) -> bool:
    tiers = snap.get("tiers")
    if isinstance(tiers, list):
        return "car" in tiers
    return any(c.get("tier") == "car" for c in snap.get("cells") or [])


def pick_car_snapshot(geo: str):
    """(path, snap, skipped) を返す。skipped は飛ばした新しい回のファイル名（local だけの回など）。"""
    snaps = sorted(glob.glob(os.path.join(geo, "data", "car", "snapshots", "*.json")))
    if not snaps:
        return None, None, []
    skipped = []
    for p in reversed(snaps):
        with open(p, encoding="utf-8") as f:
            s = json.load(f)
        if has_car(s):
            return p, s, skipped
        skipped.append(os.path.basename(p))
    p = snaps[-1]
    with open(p, encoding="utf-8") as f:
        return p, json.load(f), skipped
