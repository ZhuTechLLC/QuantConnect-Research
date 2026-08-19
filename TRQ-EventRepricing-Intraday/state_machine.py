from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from feature_engine import FeatureSnapshot


class RepricingState(str, Enum):
    PRICE_DISCOVERY = "S0_PRICE_DISCOVERY"
    RUSH_CONTINUATION = "S1_RUSH_CONTINUATION"
    RUSH_EXHAUSTION = "S2_RUSH_EXHAUSTION"
    FAILED_EXTENSION_DISTRIBUTION = "S3_FAILED_EXTENSION_DISTRIBUTION"
    ACCEPTANCE_BALANCE = "S4_ACCEPTANCE_BALANCE"
    SECOND_EXPANSION = "S5_SECOND_EXPANSION"


@dataclass(frozen=True)
class StateThresholds:
    # Research defaults only. These must be validated and perturbed in walk-forward tests.
    discovery_minutes: int = 15
    rush_path_efficiency: float = 0.60
    rush_residual_5m: float = 0.01
    exhaustion_peak_age: int = 10
    exhaustion_retracement: float = 0.25
    exhaustion_path_efficiency: float = 0.45
    distribution_retracement: float = 0.45
    distribution_residual_15m: float = -0.015
    weak_rebound_efficiency: float = 0.45
    balance_rv_ratio_5_30: float = 0.70
    balance_path_efficiency_15m: float = 0.35
    balance_abs_residual_5m: float = 0.01
    second_expansion_return_z: float = 1.25
    second_expansion_volume_z: float = 1.00
    second_expansion_residual_5m: float = 0.005
    second_expansion_path_efficiency_5m: float = 0.55


@dataclass(frozen=True)
class StateDecision:
    state: RepricingState
    score: float
    reasons: tuple[str, ...]


class EventRepricingStateMachine:
    """Deterministic v1 state classifier.

    The classifier intentionally uses multiple orthogonal features. No fixed price
    level or support/resistance rule is allowed to trigger a state by itself.
    """

    def __init__(self, thresholds: StateThresholds | None = None) -> None:
        self.t = thresholds or StateThresholds()

    def classify(self, f: FeatureSnapshot) -> StateDecision:
        if f.minute < self.t.discovery_minutes:
            return StateDecision(
                RepricingState.PRICE_DISCOVERY,
                1.0,
                ("inside opening discovery window",),
            )

        second_expansion_votes = [
            f.return_z_5m >= self.t.second_expansion_return_z,
            f.volume_z_5m >= self.t.second_expansion_volume_z,
            f.residual_return_5m >= self.t.second_expansion_residual_5m,
            f.path_efficiency_5m >= self.t.second_expansion_path_efficiency_5m,
            f.rv_ratio_5_30 >= 0.80,
        ]
        if sum(second_expansion_votes) >= 4:
            return StateDecision(
                RepricingState.SECOND_EXPANSION,
                sum(second_expansion_votes) / len(second_expansion_votes),
                tuple(
                    reason
                    for ok, reason in zip(
                        second_expansion_votes,
                        (
                            "5m return z-score expanded",
                            "5m volume surprise expanded",
                            "positive residual return",
                            "short-window path efficiency high",
                            "short-window volatility re-expanded",
                        ),
                    )
                    if ok
                ),
            )

        distribution_votes = [
            f.normalized_retracement >= self.t.distribution_retracement,
            f.residual_return_15m <= self.t.distribution_residual_15m,
            f.rebound_efficiency <= self.t.weak_rebound_efficiency,
            f.peak_age >= self.t.exhaustion_peak_age,
            f.path_efficiency_15m >= 0.45 and f.return_15m < 0,
        ]
        if sum(distribution_votes) >= 4:
            return StateDecision(
                RepricingState.FAILED_EXTENSION_DISTRIBUTION,
                sum(distribution_votes) / len(distribution_votes),
                tuple(
                    reason
                    for ok, reason in zip(
                        distribution_votes,
                        (
                            "deep normalized retracement",
                            "negative 15m residual return",
                            "weak rebound efficiency",
                            "peak is no longer recent",
                            "efficient downward 15m path",
                        ),
                    )
                    if ok
                ),
            )

        balance_votes = [
            f.rv_ratio_5_30 <= self.t.balance_rv_ratio_5_30,
            f.path_efficiency_15m <= self.t.balance_path_efficiency_15m,
            abs(f.residual_return_5m) <= self.t.balance_abs_residual_5m,
            f.volume_decay_ratio <= 1.0,
            f.peak_age >= self.t.exhaustion_peak_age,
        ]
        if sum(balance_votes) >= 4:
            return StateDecision(
                RepricingState.ACCEPTANCE_BALANCE,
                sum(balance_votes) / len(balance_votes),
                tuple(
                    reason
                    for ok, reason in zip(
                        balance_votes,
                        (
                            "short volatility contracted",
                            "15m path efficiency low",
                            "residual return near neutral",
                            "volume intensity decayed",
                            "morning peak has aged",
                        ),
                    )
                    if ok
                ),
            )

        exhaustion_votes = [
            f.peak_age >= self.t.exhaustion_peak_age,
            f.normalized_retracement >= self.t.exhaustion_retracement,
            f.path_efficiency_15m <= self.t.exhaustion_path_efficiency,
            f.rv_ratio_5_30 <= 1.0,
            f.volume_decay_ratio <= 1.0,
        ]
        if sum(exhaustion_votes) >= 3:
            return StateDecision(
                RepricingState.RUSH_EXHAUSTION,
                sum(exhaustion_votes) / len(exhaustion_votes),
                tuple(
                    reason
                    for ok, reason in zip(
                        exhaustion_votes,
                        (
                            "running peak has aged",
                            "retracement expanded",
                            "path efficiency decayed",
                            "short volatility not expanding",
                            "recent volume not re-accelerating",
                        ),
                    )
                    if ok
                ),
            )

        rush_votes = [
            f.return_5m > 0,
            f.path_efficiency_15m >= self.t.rush_path_efficiency,
            f.residual_return_5m >= self.t.rush_residual_5m,
            f.rv_ratio_5_30 >= 0.90,
        ]
        if sum(rush_votes) >= 3:
            return StateDecision(
                RepricingState.RUSH_CONTINUATION,
                sum(rush_votes) / len(rush_votes),
                tuple(
                    reason
                    for ok, reason in zip(
                        rush_votes,
                        (
                            "positive 5m return",
                            "high 15m path efficiency",
                            "positive idiosyncratic residual",
                            "short volatility sustained",
                        ),
                    )
                    if ok
                ),
            )

        return StateDecision(
            RepricingState.PRICE_DISCOVERY,
            0.5,
            ("features are mixed; no higher-confidence state",),
        )
