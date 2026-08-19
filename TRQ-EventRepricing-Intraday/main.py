from AlgorithmImports import *
from datetime import datetime

from feature_engine import Bar, IntradayFeatureEngine
from state_machine import EventRepricingStateMachine


class EventRepricingIntradayAlgorithm(QCAlgorithm):
    """v1 case-replay adapter.

    This first LEAN integration does NOT place orders. It streams point-in-time
    minute bars into the feature engine, classifies the event-day state, and logs
    transitions for golden-case validation. Trading is enabled only after state
    replay and anti-lookahead validation pass.
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

        self.event_bars = []
        self.sector_bars = []
        self.broad_bars = []
        self.last_state = None
        self.session_date = None

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
            self.last_state = None

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
        decision = self.state_machine.classify(features)

        if decision.state != self.last_state:
            self.last_state = decision.state
            self.log(
                f"STATE|{self.time}|{self.event_symbol.value}|{decision.state.value}|"
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
