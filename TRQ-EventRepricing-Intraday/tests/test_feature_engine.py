import unittest

from feature_engine import Bar, IntradayFeatureEngine, path_efficiency


class FeatureEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = IntradayFeatureEngine()

    def test_running_high_is_point_in_time(self):
        observed = [
            Bar(0, 100, 105, 99, 104, 1_000),
            Bar(1, 104, 108, 103, 107, 1_100),
            Bar(2, 107, 109, 106, 108, 900),
        ]
        future = Bar(3, 108, 150, 107, 149, 5_000)

        before = self.engine.compute(observed)
        after = self.engine.compute(observed + [future])

        self.assertEqual(before.running_high, 109)
        self.assertEqual(after.running_high, 150)
        self.assertNotEqual(before.running_high, after.running_high)

    def test_path_efficiency_distinguishes_trend_from_chop(self):
        trend = [
            Bar(i, 100 + i, 101 + i, 99 + i, 100 + i, 1000)
            for i in range(6)
        ]
        chop_closes = [100, 104, 101, 105, 102, 103]
        chop = [
            Bar(i, c, c + 1, c - 1, c, 1000)
            for i, c in enumerate(chop_closes)
        ]

        self.assertGreater(path_efficiency(trend), path_efficiency(chop))

    def test_normalized_retracement_uses_running_peak(self):
        bars = [
            Bar(0, 100, 105, 99, 104, 1000),
            Bar(1, 104, 120, 103, 118, 1200),
            Bar(2, 118, 119, 110, 112, 1100),
        ]
        f = self.engine.compute(bars)
        expected = (120 - 112) / (120 - 100)
        self.assertAlmostEqual(f.normalized_retracement, expected)


if __name__ == "__main__":
    unittest.main()
