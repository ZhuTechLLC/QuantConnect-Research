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
class TransitionThresholds:
    """Semantic transition rules, separate from market-feature thresholds.

    `SECOND_EXPANSION` means expansion *after* a confirmed balance regime. A raw
    expansion candidate that occurs without prior balance is continuation of the
    opening/rush price-discovery process, not a second leg.
    """

    min_balance_observations: int = 3
    max_minutes_since_confirmed_balance: int = 15


@dataclass(frozen=True)
class StateDecision:
    state: RepricingState
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TrackedStateDecision:
    state: RepricingState
    raw_state: RepricingState
    score: float
    reasons: tuple[str, ...]


class EventRepricingStateMachine:
    """Deterministic v1 raw-state classifier.

    This layer classifies the current feature configuration. It deliberately uses
    multiple orthogonal features and never uses a fixed support/resistance price.
    Sequence semantics are enforced by `RepricingStateTracker` below.
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
            ("features are mixed; no higher-confidence raw state",),
        )


class RepricingStateTracker:
    """Stateful transition layer for replay and eventual trading policy.

    The raw classifier says what the current features resemble. The tracker decides
    whether that label is semantically valid given the path that preceded it.

    Most importantly, S5 is impossible without a previously confirmed S4. If an
    expansion-like feature bundle appears before balance, it is labeled S1 because
    it is still part of the initial price-discovery/rush process.
    """

    def __init__(self, thresholds: TransitionThresholds | None = None) -> None:
        self.t = thresholds or TransitionThresholds()
        self.reset()

    def reset(self) -> None:
        self.current_state: RepricingState | None = None
        self.balance_streak = 0
        self.last_confirmed_balance_minute: int | None = None

    def update(self, f: FeatureSnapshot, raw: StateDecision) -> TrackedStateDecision:
        raw_state = raw.state
        reasons = list(raw.reasons)

        if raw_state == RepricingState.ACCEPTANCE_BALANCE:
            self.balance_streak += 1
            if self.balance_streak >= self.t.min_balance_observations:
                self.last_confirmed_balance_minute = f.minute
                reasons.append(
                    f"balance confirmed for >= {self.t.min_balance_observations} observations"
                )
            self.current_state = RepricingState.ACCEPTANCE_BALANCE
            return TrackedStateDecision(
                state=self.current_state,
                raw_state=raw_state,
                score=raw.score,
                reasons=tuple(reasons),
            )

        # Any non-balance raw observation ends the current consecutive balance streak,
        # but a recently confirmed balance remains eligible to seed a second leg.
        self.balance_streak = 0

        if raw_state == RepricingState.SECOND_EXPANSION:
            recently_balanced = (
                self.last_confirmed_balance_minute is not None
                and 0
                <= f.minute - self.last_confirmed_balance_minute
                <= self.t.max_minutes_since_confirmed_balance
            )
            if self.current_state == RepricingState.SECOND_EXPANSION or recently_balanced:
                self.current_state = RepricingState.SECOND_EXPANSION
                reasons.append("expansion follows a confirmed recent balance regime")
            else:
                self.current_state = RepricingState.RUSH_CONTINUATION
                reasons.append(
                    "expansion-like raw signal without confirmed prior balance; "
                    "classified as rush continuation, not second expansion"
                )
            return TrackedStateDecision(
                state=self.current_state,
                raw_state=raw_state,
                score=raw.score,
                reasons=tuple(reasons),
            )

        if raw_state == RepricingState.FAILED_EXTENSION_DISTRIBUTION:
            # A material distribution state invalidates an older balance anchor. A later
            # S5 therefore requires a newly established S4 rather than reusing stale balance.
            self.last_confirmed_balance_minute = None

        self.current_state = raw_state
        return TrackedStateDecision(
            state=self.current_state,
            raw_state=raw_state,
            score=raw.score,
            reasons=tuple(reasons),
        )
