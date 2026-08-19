import unittest

from feature_engine import FeatureSnapshot
from state_machine import EventRepricingStateMachine, RepricingState


def snapshot(**overrides):
    base = dict(
        minute=60,
        price=100.0,
        return_1m=0.0,
        return_5m=0.0,
        return_15m=0.0,
        return_30m=0.0,
        return_from_open=0.20,
        running_high=120.0,
        running_low=95.0,
        peak_age=20,
        trough_age=5,
        normalized_retracement=0.20,
        rebound_efficiency=0.80,
        path_efficiency_5m=0.20,
        path_efficiency_15m=0.20,
        path_efficiency_30m=0.20,
        rv_5m=0.01,
        rv_15m=0.015,
        rv_30m=0.02,
        rv_ratio_5_30=0.50,
        rv_ratio_15_30=0.75,
        cumulative_volume=10_000_000,
        opening_volume_share=0.50,
        volume_decay_ratio=0.70,
        return_z_5m=0.0,
        volume_z_5m=0.0,
        residual_return_5m=0.0,
        residual_return_15m=0.0,
    )
    base.update(overrides)
    return FeatureSnapshot(**base)


class StateMachineTests(unittest.TestCase):
    def setUp(self):
        self.machine = EventRepricingStateMachine()

    def test_opening_window_is_price_discovery(self):
        f = snapshot(minute=10)
        self.assertEqual(self.machine.classify(f).state, RepricingState.PRICE_DISCOVERY)

    def test_second_expansion_requires_multiple_features(self):
        f = snapshot(
            return_z_5m=1.8,
            volume_z_5m=1.4,
            residual_return_5m=0.012,
            path_efficiency_5m=0.70,
            rv_ratio_5_30=0.90,
        )
        self.assertEqual(self.machine.classify(f).state, RepricingState.SECOND_EXPANSION)

    def test_single_large_return_does_not_create_second_expansion(self):
        f = snapshot(return_z_5m=3.0)
        self.assertNotEqual(self.machine.classify(f).state, RepricingState.SECOND_EXPANSION)

    def test_distribution_requires_joint_failure_evidence(self):
        f = snapshot(
            normalized_retracement=0.60,
            residual_return_15m=-0.03,
            rebound_efficiency=0.20,
            peak_age=30,
            path_efficiency_15m=0.70,
            return_15m=-0.04,
        )
        self.assertEqual(
            self.machine.classify(f).state,
            RepricingState.FAILED_EXTENSION_DISTRIBUTION,
        )

    def test_balance_is_not_defined_by_price_level(self):
        f1 = snapshot(price=80.0)
        f2 = snapshot(price=180.0)
        self.assertEqual(self.machine.classify(f1).state, self.machine.classify(f2).state)


if __name__ == "__main__":
    unittest.main()
