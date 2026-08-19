from AlgorithmImports import *

from feature_engine import Bar, IntradayFeatureEngine
from state_machine import EventRepricingStateMachine, RepricingStateTracker


class EventRepricingIntradayAlgorithm(QCAlgorithm):
    """Golden-case replay adapter.

    No orders are placed. Historical minute bars are streamed through the PIT feature
    engine, raw classifier and stateful transition tracker. Logs intentionally expose
    both raw and tracked states so semantic downgrades (for example raw S5 without a
    prior confirmed S4) remain auditable.
    """

    def initialize(self):
        ticker = self.get_parameter("ticker") or "MRNA"
        sector = self.get_parameter("sector") or "XBI"
        broad = self.get_parameter("broad") or "QQQ"
        year = int(self.get_parameter("year") or 2026)
        month = int(self.get_parameter("month") or 8)
        day = int(self.get_parameter("day") or 19)

        self.set_start_date(year, month, day)
        self.set_end_date(year, month, day)
        self.set_cash(1_000_000)
        self.set_time_zone("America/New_York")

        self.event_symbol = self.add_equity(
            ticker, Resolution.MINUTE, extended_market_hours=False
        ).symbol
        self.sector_symbol = self.add_equity(
            sector, Resolution.MINUTE, extended_market_hours=False
        ).symbol
        self.broad_symbol = self.add_equity(
            broad, Resolution.MINUTE, extended_market_hours=False
        ).symbol

        self.feature_engine = IntradayFeatureEngine(opening_window_minutes=30)
        self.state_machine = EventRepricingStateMachine()
        self.state_tracker = RepricingStateTracker()

        self.event_bars = []
        self.sector_bars = []
        self.broad_bars = []
        self.last_tracked_state = None
        self.session_date = None
        self.state_counts = {}
        self.transition_count = 0

    def on_data(self, data: Slice):
        if not self.securities[self.event_symbol].exchange.hours.is_open(self.time, False):
            return

        event_bar = data.bars.get(self.event_symbol)
        sector_bar = data.bars.get(self.sector_symbol)
        broad_bar = data.bars.get(self.broad_symbol)
        if event_bar is None or sector_bar is None or broad_bar is None:
            return

        if self.session_date != self.time.date():
            self.session_date = self.time.date()
            self.event_bars.clear()
            self.sector_bars.clear()
            self.broad_bars.clear()
            self.last_tracked_state = None
            self.state_tracker.reset()
            self.state_counts.clear()
            self.transition_count = 0

        minute = (self.time.hour * 60 + self.time.minute) - (9 * 60 + 30)
        if minute < 0:
            return

        self.event_bars.append(self._to_bar(minute, event_bar))
        self.sector_bars.append(self._to_bar(minute, sector_bar))
        self.broad_bars.append(self._to_bar(minute, broad_bar))

        features = self.feature_engine.compute(
            self.event_bars,
            benchmark_bars=self.broad_bars,
            sector_bars=self.sector_bars,
        )
        raw = self.state_machine.classify(features)
        decision = self.state_tracker.update(features, raw)

        state_name = decision.state.value
        self.state_counts[state_name] = self.state_counts.get(state_name, 0) + 1

        if decision.state != self.last_tracked_state:
            self.transition_count += 1
            self.last_tracked_state = decision.state
            self.log(
                f"STATE|{self.time}|{self.event_symbol.value}|"
                f"tracked={decision.state.value}|raw={decision.raw_state.value}|"
                f"score={decision.score:.2f}|px={features.price:.4f}|"
                f"ret5={features.return_5m:.4%}|ret15={features.return_15m:.4%}|"
                f"retr={features.normalized_retracement:.3f}|"
                f"peak_age={features.peak_age}|rebound={features.rebound_efficiency:.3f}|"
                f"pe5={features.path_efficiency_5m:.3f}|pe15={features.path_efficiency_15m:.3f}|"
                f"rv5_30={features.rv_ratio_5_30:.3f}|vol_decay={features.volume_decay_ratio:.3f}|"
                f"rz5={features.return_z_5m:.3f}|vz5={features.volume_z_5m:.3f}|"
                f"res5={features.residual_return_5m:.4%}|res15={features.residual_return_15m:.4%}|"
                f"reasons={';'.join(decision.reasons)}"
            )

        # Sparse periodic trace keeps case replay auditable even when tracked state does
        # not transition for a long interval. It is descriptive only, never a signal.
        if minute in {15, 30, 60, 90, 120, 180, 270, 360}:
            self.log(
                f"TRACE|{self.time}|{self.event_symbol.value}|"
                f"tracked={decision.state.value}|raw={decision.raw_state.value}|"
                f"px={features.price:.4f}|retr={features.normalized_retracement:.3f}|"
                f"pe15={features.path_efficiency_15m:.3f}|rv5_30={features.rv_ratio_5_30:.3f}|"
                f"res5={features.residual_return_5m:.4%}|res15={features.residual_return_15m:.4%}"
            )

    def on_end_of_algorithm(self):
        counts = ",".join(f"{k}:{v}" for k, v in sorted(self.state_counts.items()))
        self.log(
            f"SUMMARY|{self.event_symbol.value}|date={self.session_date}|"
            f"transitions={self.transition_count}|counts={counts}"
        )

    @staticmethod
    def _to_bar(minute: int, trade_bar: TradeBar) -> Bar:
        return Bar(
            minute=minute,
            open=float(trade_bar.open),
            high=float(trade_bar.high),
            low=float(trade_bar.low),
            close=float(trade_bar.close),
            volume=float(trade_bar.volume),
        )
