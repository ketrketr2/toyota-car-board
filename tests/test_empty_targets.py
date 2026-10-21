"""外部API・シークレットなしで、実際の集計スクリプトを最後まで実行する。"""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
FOCUS = ['roomy', 'sienta', 'alphard', 'voxy', 'noah', 'aqua', 'raize', 'lc250']
SEGS = ['compact_tall', 'minivan_s', 'minivan_l', 'minivan_m', 'minivan_m',
        'compact_hb', 'suv_compact', 'suv_off']


class EmptyTargetsTest(unittest.TestCase):
    def cells(self):
        # 各車2対象、回答生成率50%、有効引用2件 → F1=1、言及率50%。
        result = []
        for cid, seg in zip(FOCUS, SEGS):
            for i in range(2):
                result.append(dict(tier='car', prompt_id=cid, cars=[cid], named_cars=[],
                                   seg=seg, category='cost', surface=['chatgpt', 'gemini'][i],
                                   answer=cid if i == 0 else ' ',
                                   models={cid: dict(rank=1, sent='positive')} if i == 0 else {},
                                   citations=[dict(host=h, bucket='media') for h in
                                              ['example.jp', 'example.org', 'google.com']] if i == 0 else []))
        return result

    def aggregate(self, cells, zero_ga=False):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            geo = base / 'geo'
            for directory in ['data/car/snapshots', 'prompts', 'config']:
                (geo / directory).mkdir(parents=True)
            def dump(path, obj):
                path.write_text(json.dumps(obj), encoding='utf-8')
            dump(geo / 'data/car/snapshots/2026-10-21.json', dict(
                date='2026-10-21', api_cost=dict(calls=len(cells), usd=1),
                surfaces=['chatgpt', 'gemini'], cells=cells))
            cfg = dict(focus=[dict(id=c, name=c, seg=s) for c, s in zip(FOCUS, SEGS)],
                       rivals=[dict(id=c, name=c, brand='toyota') for c in
                               ['thor', 'solio', 'delica_mini', 'freed', 'serena', 'stepwgn',
                                'vellfire', 'elgrand', 'yaris', 'fit', 'note', 'yariscross',
                                'rocky', 'crossbee', 'wrv', 'rav4', 'jimny_sierra', 'xtrail', 'outlander']],
                       segs={s: s for s in SEGS})
            (geo / 'config/cars.yaml').write_text(yaml.safe_dump(cfg))
            (geo / 'config/models.yaml').write_text('own: []\n')
            (geo / 'prompts/registry.yaml').write_text(yaml.safe_dump(dict(
                prompts=[dict(id=c, text=c, active_for=[c]) for c in FOCUS])))
            dump(base / 'ga_f4.json', dict(dates=['2026-10-20'],
                 cars={c: dict(sess=[0 if zero_ga else 100]) for c in FOCUS}))
            dump(base / 'core_trend.json', dict(days=['2026-10-20'],
                 trend={'2026-10-20': dict(hits={}, n=0)}))
            board_path, signal_path = base / 'board.json', base / 'signal.json'
            env = dict(GEO_REPO=str(geo), WORK_DIR=str(base), BOARD_DATA=str(board_path),
                       SIGNAL_DATA=str(signal_path), CITE_CACHE=str(base / 'missing.json'))
            # 再検出は変更対象外。テストで明示した検出済みセルをそのまま渡す。
            redetect = types.ModuleType('redetect')
            redetect.redetect = lambda *a: (0, dict(cells_changed=0, detections_added=0, detections_removed=0))
            with patch.dict(os.environ, env), patch.dict(sys.modules, redetect=redetect), \
                    patch.object(sys, 'path', sys.path.copy()), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(ROOT / 'tools/aggregate_board.py'), run_name='__main__')
                runpy.run_path(str(ROOT / 'tools/aggregate_signal.py'), run_name='__main__')
            rendered = subprocess.run(['node', str(ROOT / 'tests/test_empty_render.js'),
                                      str(board_path), str(signal_path)], capture_output=True, text=True)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            if os.environ.get('EMPTY_RENDER_BROWSER') == '1':
                for script in ['build.py', 'build_signal.py']:
                    subprocess.run([sys.executable, str(ROOT / 'tools' / script)],
                                   cwd=base, env={**os.environ, **env}, check=True, capture_output=True)
                browser = subprocess.run(['node', str(ROOT / 'tests/verify_empty_render_browser.js'),
                                          str(base)], capture_output=True, text=True)
                self.assertEqual(browser.returncode, 0, browser.stderr)
            return json.loads(board_path.read_text()), json.loads(signal_path.read_text())

    def test_normal_values_unchanged(self):
        board, signal = self.aggregate(self.cells())
        for car in board['cars'].values():
            self.assertEqual((car['target_cells'], car['mention'], car['first']), (2, 1, 1))
            self.assertEqual((car['f1_raw'], car['answered_rate'], car['avg_cites']), (1, 50, 2))
            self.assertEqual((car['f1i'], car['f2i'], car['f3i'], car['f4i']), (100, 100, 100, 100))
        self.assertTrue(all(f['f1'] == 100 for f in signal['funnel']))

    def test_missing_one_car_does_not_change_other_cars(self):
        original, _ = self.aggregate(self.cells())
        cells = [c for c in self.cells() if c['cars'] != ['roomy']]
        board, signal = self.aggregate(cells)
        car = board['cars']['roomy']
        self.assertEqual(car['target_cells'], 0)
        for key in ['f1_raw', 'f1i', 'mr', 'fr', 'answered_rate', 'f2i', 'f3i', 'avg_cites', 'expi']:
            self.assertIsNone(car[key], key)
        # 未計測をゼロ扱いすると他7車のF1指数が114になる。100を保持すること。
        for cid in FOCUS[1:]:
            for key in ['f1_raw', 'f1i', 'f2i', 'f3i', 'f4i', 'cite4', 'ga28', 'sales_m']:
                self.assertEqual(board['cars'][cid][key], original['cars'][cid][key], (cid, key))
        funnel = next(f for f in signal['funnel'] if f['id'] == 'roomy')
        self.assertIsNone(funnel['f1'])
        self.assertEqual(funnel['bottleneck'], 'F4')

    def test_named_only_is_not_a_target(self):
        cells = self.cells()
        for c in cells:
            if c['cars'] == ['roomy']:
                c['named_cars'] = ['roomy']
        board, _ = self.aggregate(cells)
        self.assertEqual(board['cars']['roomy']['target_cells'], 0)
        self.assertIsNone(board['cars']['roomy']['f1_raw'])

    def test_all_targets_missing(self):
        board, signal = self.aggregate([])
        self.assertTrue(all(c['f1_raw'] is None and c['f1i'] is None for c in board['cars'].values()))
        self.assertTrue(all(f['f1'] is None and f['bottleneck'] == 'F4' for f in signal['funnel']))

    def test_unanswered_is_measured_zero(self):
        cells = self.cells()
        for c in cells:
            c.update(answer='', models={}, citations=[])
        board, _ = self.aggregate(cells)
        for c in board['cars'].values():
            self.assertEqual((c['f1_raw'], c['answered_rate'], c['avg_cites'], c['mr']), (0, 0, 0, 0))
            self.assertIsNone(c['f1i'])  # 車種平均自体が0なので相対指数は未定義。

    def test_answered_without_citations(self):
        cells = self.cells()
        for c in cells:
            c['citations'] = []
        board, _ = self.aggregate(cells)
        self.assertTrue(all(c['f1_raw'] == 0 and c['avg_cites'] == 0 for c in board['cars'].values()))

    def test_no_measurable_funnel_stage(self):
        _, signal = self.aggregate([], zero_ga=True)
        for f in signal['funnel']:
            self.assertIsNone(f['bottleneck'])
            self.assertIsNone(f['bv'])
            self.assertFalse(f['weak'])


if __name__ == '__main__':
    unittest.main()
