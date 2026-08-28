#!/usr/bin/env python3
"""①ボード用: GA(F4)車種ページ日次sessions(28日) + geo回答28日車種言及トレンドを取得・集計。"""
import json, os, sys, time, urllib.parse, urllib.request, glob, collections
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

KEY = os.environ.get('WINDSOR_API_KEY') or sys.exit('WINDSOR_API_KEY 未設定')
ACC = '324699885'
BASE = 'https://connectors.windsor.ai/googleanalytics4'
TODAY = datetime.now(ZoneInfo('Asia/Tokyo')).date()
YB = TODAY - timedelta(days=1)
D28 = YB - timedelta(days=27)

GEO = os.environ.get('GEO_REPO', '/tmp/gb')
OUT = os.environ.get('WORK_DIR', 'work')
os.makedirs(OUT, exist_ok=True)

SLUG = {"roomy": "/roomy/", "sienta": "/sienta/", "alphard": "/alphard/", "voxy": "/voxy/",
        "noah": "/noah/", "aqua": "/aqua/", "raize": "/raize/", "lc250": "/landcruiser250/"}

def q(fields, dfrom, dto, flt=None, extra=None):
    p = {'api_key': KEY, 'select_accounts': ACC, '_renderer': 'json',
         'fields': ','.join(fields), 'date_from': str(dfrom), 'date_to': str(dto)}
    if flt is not None:
        p['filter'] = json.dumps(flt, ensure_ascii=False)
    if extra:
        p.update(extra)
    url = BASE + '?' + urllib.parse.urlencode(p)
    for att in range(3):
        try:
            with urllib.request.urlopen(url, timeout=240) as r:
                data = json.loads(r.read().decode('utf-8'))
            return data.get('data', data if isinstance(data, list) else [])
        except Exception as e:
            last = e
            time.sleep(6 * (att + 1))
    raise SystemExit(f'Windsor失敗: {last}')

dates = [str(D28 + timedelta(days=i)) for i in range(28)]
ga = {"dates": dates, "cars": {}}
for cid, slug in SLUG.items():
    rows = q(['date', 'sessions', 'totalusers'], D28, YB, [['page_path', 'contains', slug]])
    by = {r['date'][:10]: r for r in rows}
    ga['cars'][cid] = {
        "sess": [int(float(by.get(d, {}).get('sessions') or 0)) for d in dates],
        "users": [int(float(by.get(d, {}).get('totalusers') or 0)) for d in dates],
    }
    print(cid, 'sess28d=', sum(ga['cars'][cid]['sess']), flush=True)
json.dump(ga, open(f'{OUT}/ga_f4.json', 'w'), ensure_ascii=False)

# ---- geo回答 28日 車種言及トレンド（coreスキャン） ----
sys.path.insert(0, f'{GEO}/src')
from run_car import detect_cars, _catalog  # noqa
catalog = _catalog()
files = sorted(glob.glob(f'{GEO}/data/snapshots/2026-*.json'))
trend = {}   # car -> {date: [hit, cells]}
days = []
for f in files:
    try:
        s = json.load(open(f))
    except Exception:
        continue
    if s.get('mode') == 'demo':
        continue
    cells = s.get('cells') or []
    if not cells or not any(c.get('answer') for c in cells):
        continue
    d = f[-15:-5]
    days.append(d)
    cnt = collections.Counter()
    for c in cells:
        det = detect_cars(c.get('answer') or '', catalog)
        for cid in det:
            cnt[cid] += 1
    trend[d] = {"n": len(cells), "hits": dict(cnt)}
json.dump({"days": days, "trend": trend}, open(f'{OUT}/core_trend.json', 'w'), ensure_ascii=False)
print('core trend days:', len(days), days[0], '..', days[-1])
