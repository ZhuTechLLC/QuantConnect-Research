from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt
from statistics import mean, pstdev
from typing import Iterable, Sequence

EPS = 1e-12


@dataclass(frozen=True)
class Bar:
    minute: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class FeatureSnapshot:
    minute: int
    price: float
    return_1m: float
    return_5m: float
    return_15m: float
    return_30m: float
    return_from_open: float
    running_high: float
    running_low: float
    peak_age: int
    trough_age: int
    normalized_retracement: float
    rebound_efficiency: float
    path_efficiency_5m: float
    path_efficiency_15m: float
    path_efficiency_30m: float
    rv_5m: float
    rv_15m: float
    rv_30m: float
    rv_ratio_5_30: float
    rv_ratio_15_30: float
    cumulative_volume: float
    opening_volume_share: float
    volume_decay_ratio: float
    return_z_5m: float
    volume_z_5m: float
    residual_return_5m: float
    residual_return_15m: float


def simple_return(new: float, old: float) -> float:
    if old <= 0:
        return 0.0
    return new / old - 1.0


def _window(seq: Sequence[Bar], n: int) -> Sequence[Bar]:
    return seq[max(0, len(seq) - n):]


def _return_over(seq: Sequence[Bar], n: int) -> float:
    if len(seq) < 2:
        return 0.0
    start_index = max(0, len(seq) - 1 - n)
    return simple_return(seq[-1].close, seq[start_index].close)


def path_efficiency(seq: Sequence[Bar]) -> float:
    if len(seq) < 2:
        return 0.0
    closes = [bar.close for bar in seq]
    net = abs(closes[-1] - closes[0])
    gross = sum(abs(b - a) for a, b in zip(closes[:-1], closes[1:]))
    return net / max(gross, EPS)


def realized_volatility(seq: Sequence[Bar]) -> float:
    if len(seq) < 3:
        return 0.0
    rets = [log(b.close / a.close) for a, b in zip(seq[:-1], seq[1:]) if a.close > 0 and b.close > 0]
    if len(rets) < 2:
        return 0.0
    return pstdev(rets) * sqrt(len(rets))


def _zscore(value: float, history: Sequence[float]) -> float:
    if len(history) < 5:
        return 0.0
    sigma = pstdev(history)
    if sigma <= EPS:
        return 0.0
    return (value - mean(history)) / sigma


def _last_local_trough_index(bars: Sequence[Bar], peak_index: int) -> int:
    if peak_index >= len(bars) - 1:
        return peak_index
    lows = [bar.low for bar in bars[peak_index:]]
    return peak_index + lows.index(min(lows))


def rebound_efficiency(bars: Sequence[Bar], peak_index: int) -> float:
    if peak_index >= len(bars) - 1:
        return 0.0
    trough_index = _last_local_trough_index(bars, peak_index)
    if trough_index >= len(bars) - 1:
        return 0.0
    prior_peak = bars[peak_index].high
    trough = bars[trough_index].low
    bounce_high = max(bar.high for bar in bars[trough_index:])
    return max(0.0, bounce_high - trough) / max(prior_peak - trough, EPS)


class IntradayFeatureEngine:
    """Pure point-in-time feature calculator.

    The engine receives only bars observed through the current timestamp. It never
    references final-day high/low or later event information.
    """

    def __init__(self, opening_window_minutes: int = 30) -> None:
        self.opening_window_minutes = opening_window_minutes

    def compute(
        self,
        bars: Sequence[Bar],
        benchmark_bars: Sequence[Bar] | None = None,
        sector_bars: Sequence[Bar] | None = None,
    ) -> FeatureSnapshot:
        if not bars:
            raise ValueError("bars must not be empty")

        current = bars[-1]
        session_open = bars[0].open
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        running_high = max(highs)
        running_low = min(lows)
        peak_index = highs.index(running_high)
        trough_index = lows.index(running_low)
        peak_age = current.minute - bars[peak_index].minute
        trough_age = current.minute - bars[trough_index].minute

        normalized_retracement = max(0.0, running_high - current.close) / max(
            running_high - session_open, EPS
        )

        pe5 = path_efficiency(_window(bars, 6))
        pe15 = path_efficiency(_window(bars, 16))
        pe30 = path_efficiency(_window(bars, 31))
        rv5 = realized_volatility(_window(bars, 6))
        rv15 = realized_volatility(_window(bars, 16))
        rv30 = realized_volatility(_window(bars, 31))

        cumulative_volume = sum(b.volume for b in bars)
        opening_bars = bars[: min(len(bars), self.opening_window_minutes)]
        opening_volume = sum(b.volume for b in opening_bars)
        opening_volume_share = opening_volume / max(cumulative_volume, EPS)

        recent_volume = sum(b.volume for b in _window(bars, 10))
        prior_volume_window = bars[max(0, len(bars) - 20): max(0, len(bars) - 10)]
        prior_volume = sum(b.volume for b in prior_volume_window)
        volume_decay_ratio = recent_volume / max(prior_volume, EPS) if prior_volume_window else 1.0

        five_min_returns = []
        five_min_volumes = []
        for i in range(6, len(bars)):
            five_min_returns.append(simple_return(bars[i].close, bars[i - 5].close))
            five_min_volumes.append(sum(b.volume for b in bars[i - 4:i + 1]))

        current_ret5 = _return_over(bars, 5)
        current_vol5 = sum(b.volume for b in _window(bars, 5))
        return_z_5m = _zscore(current_ret5, five_min_returns[:-1]) if five_min_returns else 0.0
        volume_z_5m = _zscore(current_vol5, five_min_volumes[:-1]) if five_min_volumes else 0.0

        benchmark_ret5 = _return_over(benchmark_bars, 5) if benchmark_bars else 0.0
        benchmark_ret15 = _return_over(benchmark_bars, 15) if benchmark_bars else 0.0
        sector_ret5 = _return_over(sector_bars, 5) if sector_bars else 0.0
        sector_ret15 = _return_over(sector_bars, 15) if sector_bars else 0.0

        # Equal-weight benchmark adjustment is deliberately simple in v1. A rolling
        # beta residual model can replace it only after PIT beta estimation is tested.
        residual_5 = current_ret5 - 0.5 * (benchmark_ret5 + sector_ret5)
        residual_15 = _return_over(bars, 15) - 0.5 * (benchmark_ret15 + sector_ret15)

        return FeatureSnapshot(
            minute=current.minute,
            price=current.close,
            return_1m=_return_over(bars, 1),
            return_5m=current_ret5,
            return_15m=_return_over(bars, 15),
            return_30m=_return_over(bars, 30),
            return_from_open=simple_return(current.close, session_open),
            running_high=running_high,
            running_low=running_low,
            peak_age=peak_age,
            trough_age=trough_age,
            normalized_retracement=normalized_retracement,
            rebound_efficiency=rebound_efficiency(bars, peak_index),
            path_efficiency_5m=pe5,
            path_efficiency_15m=pe15,
            path_efficiency_30m=pe30,
            rv_5m=rv5,
            rv_15m=rv15,
            rv_30m=rv30,
            rv_ratio_5_30=rv5 / max(rv30, EPS),
            rv_ratio_15_30=rv15 / max(rv30, EPS),
            cumulative_volume=cumulative_volume,
            opening_volume_share=opening_volume_share,
            volume_decay_ratio=volume_decay_ratio,
            return_z_5m=return_z_5m,
            volume_z_5m=volume_z_5m,
            residual_return_5m=residual_5,
            residual_return_15m=residual_15,
        )
