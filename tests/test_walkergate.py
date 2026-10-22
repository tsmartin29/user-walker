import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import walkergate as wg  # noqa: E402


def ns(d, **kw):
    base = dict(dir=d, spent=0.0, cap=None, five_hour=None, stale_min=None)
    base.update(kw)
    return SimpleNamespace(**base)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, "walker.json"), "w") as f:
            json.dump({"products": [{"name": "A"}, {"name": "B"}, "C"], "daily_cap": 20}, f)

    def test_first_start_sets_baseline_and_goes(self):
        self.assertEqual(wg.cmd_start(ns(self.d, spent=100.0), now=1000.0, today="2026-10-21"), wg.GO)
        b = json.load(open(os.path.join(self.d, "budget.json")))
        self.assertEqual(b, {"date": "2026-10-21", "baseline": 100.0})

    def test_lock_blocks_second_walker(self):
        wg.cmd_start(ns(self.d, spent=0.0), now=1000.0, today="2026-10-21")
        self.assertEqual(wg.cmd_start(ns(self.d, spent=0.0), now=1000.0 + 60 * 10, today="2026-10-21"), wg.SKIP)

    def test_stale_lock_is_ignored(self):
        wg.cmd_start(ns(self.d, spent=0.0), now=1000.0, today="2026-10-21")
        self.assertEqual(wg.cmd_start(ns(self.d, spent=0.0), now=1000.0 + 60 * 91, today="2026-10-21"), wg.GO)

    def test_cap_counts_only_todays_increase(self):
        wg.cmd_start(ns(self.d, spent=500.0), now=1.0, today="2026-10-21")
        wg.cmd_done(ns(self.d))
        self.assertEqual(wg.cmd_start(ns(self.d, spent=519.0), now=2.0, today="2026-10-21"), wg.GO)
        wg.cmd_done(ns(self.d))
        self.assertEqual(wg.cmd_start(ns(self.d, spent=521.0), now=3.0, today="2026-10-21"), wg.SKIP)

    def test_new_day_resets_baseline(self):
        wg.cmd_start(ns(self.d, spent=500.0), now=1.0, today="2026-10-21")
        wg.cmd_done(ns(self.d))
        self.assertEqual(wg.cmd_start(ns(self.d, spent=530.0), now=2.0, today="2026-10-22"), wg.GO)

    def test_five_hour_gate(self):
        self.assertEqual(wg.cmd_start(ns(self.d, spent=0.0, five_hour=95.0), now=1.0, today="2026-10-21"), wg.SKIP)

    def test_rotation_wraps_and_counts_runs(self):
        seen = []
        for _ in range(4):
            seen.append(wg.cmd_next(ns(self.d), quiet=True))
            wg.cmd_done(ns(self.d))
        self.assertEqual(seen, ["A", "B", "C", "A"])
        self.assertEqual(json.load(open(os.path.join(self.d, "state.json")))["runs"], 4)

    def test_done_empties_lock_instead_of_deleting(self):
        wg.cmd_start(ns(self.d, spent=0.0), now=1.0, today="2026-10-21")
        wg.cmd_done(ns(self.d))
        p = os.path.join(self.d, "lock")
        self.assertTrue(os.path.exists(p))
        self.assertIsNone(wg.lock_age_min(self.d))

    def test_unknown_next_falls_back_to_first(self):
        json.dump({"next": "gone"}, open(os.path.join(self.d, "state.json"), "w"))
        self.assertEqual(wg.cmd_next(ns(self.d), quiet=True), "A")


if __name__ == "__main__":
    unittest.main()
