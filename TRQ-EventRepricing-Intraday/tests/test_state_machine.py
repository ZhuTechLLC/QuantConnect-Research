import unittest

from feature_engine import FeatureSnapshot
from state_machine import (
    EventRepricingStateMachine,
    RepricingState,
    RepricingStateTracker,
)


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


def expansion_snapshot(minute=60):
    return snapshot(
        minute=minute,
        return_5m=0.03,
        return_15m=0.05,
        return_z_5m=1.8,
        volume_z_5m=1.4,
        residual_return_5m=0.012,
        residual_return_15m=0.025,
        path_efficiency_5m=0.70,
        path_efficiency_15m=0.65,
        rv_ratio_5_30=0.90,
        volume_decay_ratio=1.2,
    )


def balance_snapshot(minute=50):
    return snapshot(
        minute=minute,
        peak_age=25,
        normalized_retracement=0.20,
        path_efficiency_5m=0.15,
        path_efficiency_15m=0.20,
        rv_ratio_5_30=0.50,
        residual_return_5m=0.002,
        volume_decay_ratio=0.70,
    )


class StateMachineTests(unittest.TestCase):
    def setUp(self):
        self.machine = EventRepricingStateMachine()

    def test_opening_window_is_price_discovery(self):
        f = snapshot(minute=10)
        self.assertEqual(self.machine.classify(f).state, RepricingState.PRICE_DISCOVERY)

    def test_raw_second_expansion_requires_multiple_features(self):
        self.assertEqual(
            self.machine.classify(expansion_snapshot()).state,
            RepricingState.SECOND_EXPANSION,
        )

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


class StatefulTransitionTests(unittest.TestCase):
    def setUp(self):
        self.machine = EventRepricingStateMachine()
        self.tracker = RepricingStateTracker()

    def tracked(self, f):
        return self.tracker.update(f, self.machine.classify(f))

    def test_raw_s5_without_prior_balance_is_rush_continuation(self):
        decision = self.tracked(expansion_snapshot(minute=35))
        self.assertEqual(decision.raw_state, RepricingState.SECOND_EXPANSION)
        self.assertEqual(decision.state, RepricingState.RUSH_CONTINUATION)

    def test_s5_requires_confirmed_balance_streak(self):
        self.tracked(balance_snapshot(50))
        self.tracked(balance_snapshot(51))
        third_balance = self.tracked(balance_snapshot(52))
        self.assertEqual(third_balance.state, RepricingState.ACCEPTANCE_BALANCE)

        expansion = self.tracked(expansion_snapshot(55))
        self.assertEqual(expansion.raw_state, RepricingState.SECOND_EXPANSION)
        self.assertEqual(expansion.state, RepricingState.SECOND_EXPANSION)

    def test_distribution_invalidates_old_balance_anchor(self):
        self.tracked(balance_snapshot(50))
        self.tracked(balance_snapshot(51))
        self.tracked(balance_snapshot(52))

        distribution = snapshot(
            minute=55,
            normalized_retracement=0.60,
            residual_return_15m=-0.03,
            rebound_efficiency=0.20,
            peak_age=30,
            path_efficiency_15m=0.70,
            return_15m=-0.04,
        )
        self.tracked(distribution)

        expansion = self.tracked(expansion_snapshot(60))
        self.assertEqual(expansion.state, RepricingState.RUSH_CONTINUATION)


if __name__ == "__main__":
    unittest.main()
