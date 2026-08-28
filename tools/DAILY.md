# 車種別AI分析（CAR × AI DEEP DIVE）運用手順

## 構成

| 要素 | 置き場所 | 役割 |
|---|---|---|
| 公開ページ | `docs/index.html` | AES-GCM暗号化済み。ゲート突破後にボード本体を復号表示 |
| 計測 | **toyota-geo-board** リポジトリの `car-round` ワークフロー | ①②の実測（tier=car / local）。結果は同リポジトリの `data/car/snapshots/` |
| 再ビルド | 本リポジトリ `.github/workflows/daily.yml` | geo-boardのスナップショット＋GA4＋販売台数からボードを作り直す |

計測とボードは分離している。**計測はgeo-board側**、**表示はこちら**。

## 日次の流れ（自動）

1. `tools/pull_ga_trend.py` — GA4（Windsor REST）で8車種ページの28日セッションを取得し、
   geo-boardの日次スナップショットの回答本文を車種名でスキャンして28日トレンドを作る
2. `tools/aggregate_board.py` — 上記＋car-roundスナップショット＋registry＋販売台数を統合し
   `board_data.json`（ファネル指数・語られ指数・引用4分類・考察）を生成
3. `tools/build.py` — `part_head.html` + `part_js1〜3.js` + データ を結合して `plain.html`
4. `tools/verify.js` — Playwrightで全11ビュー×2幅を描画検証（ERRORS:none が必須）
5. `tools/encrypt.py` — `CAR_GATE_KEY`（"id:pw"）で暗号化して `docs/index.html` を更新

検証で1件でもエラーが出たらデプロイしない。

## 必要なシークレット

| 名前 | 値 | 用途 |
|---|---|---|
| `WINDSOR_API_KEY` | Windsor.aiのAPIキー | GA4実測の取得 |
| `CAR_GATE_KEY` | `toyota:toyota2026` | ページ暗号化の鍵素材（ID:パスワード） |

未登録の場合、ワークフローは何もせず正常終了する（古いページがそのまま残る）。

## 手で作り直したいとき

```bash
export WINDSOR_API_KEY=...
python3 tools/pull_ga_trend.py      # GA4とトレンド
python3 tools/aggregate_board.py    # データ統合
python3 tools/build.py              # plain.html
node tools/verify.js                # 全ビュー検証
CAR_GATE_KEY="toyota:toyota2026" python3 tools/encrypt.py
mv index_new.html docs/index.html
```

## 販売台数の更新

`tools/sales_by_model.json` を月次で差し替える。出典は自販連（乗用車ブランド通称名別）と
全軽自協（軽四輪通称名別）。**推定値は入れない**。取得できない車種は `null` のままにし、
ボード側は「—」と表示する。

ランドクルーザー250は自販連の通称名集計の都合上、ランドクルーザー系合算値である点に注意。
ボードにもその旨を明記している。

## 表示に関する約束

- 推定値・デモ値は一切表示しない。数値がなければ「—」
- ゼロと表示する場合は、検証を経た実測ゼロのみ
- パスワードや機密数値をリポジトリに置かない（暗号化前の `plain.html` はコミットしない）
