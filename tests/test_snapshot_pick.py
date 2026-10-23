"""car-round の回の選び方（2026-10-23 の不具合の再発防止）。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from snapshot_pick import pick_car_snapshot  # noqa: E402


def dump(path, obj):
    path.write_text(json.dumps(obj), encoding='utf-8')


class SnapshotPickTest(unittest.TestCase):
    def geo(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        d = Path(td.name) / 'data' / 'car' / 'snapshots'
        d.mkdir(parents=True)
        return Path(td.name), d

    def test_skips_newer_local_only_round(self):
        geo, d = self.geo()
        dump(d / '2026-08-28.json', dict(date='2026-08-28', tiers=['car', 'local'], cells=[dict(tier='car'), dict(tier='local')]))
        dump(d / '2026-09-09.json', dict(date='2026-09-09', tiers=['local'], cells=[dict(tier='local')]))
        path, snap, skipped = pick_car_snapshot(str(geo))
        self.assertEqual(snap['date'], '2026-08-28')
        self.assertEqual(skipped, ['2026-09-09.json'])

    def test_newest_car_round_wins(self):
        geo, d = self.geo()
        dump(d / '2026-08-28.json', dict(date='2026-08-28', tiers=['car'], cells=[dict(tier='car')]))
        dump(d / '2026-10-30.json', dict(date='2026-10-30', tiers=['car', 'local'], cells=[dict(tier='car')]))
        _, snap, skipped = pick_car_snapshot(str(geo))
        self.assertEqual(snap['date'], '2026-10-30')
        self.assertEqual(skipped, [])

    def test_without_tiers_key_scans_cells(self):
        geo, d = self.geo()
        dump(d / '2026-08-28.json', dict(date='2026-08-28', cells=[dict(tier='car')]))
        dump(d / '2026-09-09.json', dict(date='2026-09-09', cells=[dict(tier='local')]))
        _, snap, _ = pick_car_snapshot(str(geo))
        self.assertEqual(snap['date'], '2026-08-28')

    def test_no_car_round_falls_back_to_latest(self):
        geo, d = self.geo()
        dump(d / '2026-09-09.json', dict(date='2026-09-09', tiers=['local'], cells=[dict(tier='local')]))
        _, snap, _ = pick_car_snapshot(str(geo))
        self.assertEqual(snap['date'], '2026-09-09')

    def test_empty_dir(self):
        geo, _ = self.geo()
        self.assertEqual(pick_car_snapshot(str(geo))[1], None)


if __name__ == '__main__':
    unittest.main()
