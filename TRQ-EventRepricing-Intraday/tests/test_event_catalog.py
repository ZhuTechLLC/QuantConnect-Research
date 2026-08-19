import unittest
from datetime import datetime

from event_catalog import (
    CausalPrior,
    EventRecord,
    EventType,
    EvidenceGrade,
    InformationStrength,
)


class EventCatalogCausalGateTests(unittest.TestCase):
    def base_event(self, **overrides):
        values = dict(
            event_id="TEST_20260819",
            ticker="TEST",
            event_type=EventType.PHASE3,
            event_timestamp_et=datetime(2026, 8, 19, 7, 0),
            direction=1,
            evidence_grade=EvidenceGrade.PRIMARY_VERIFIED,
            information_strength=InformationStrength.EXTREME,
            full_data_available=False,
        )
        values.update(overrides)
        return EventRecord(**values)

    def test_extreme_headline_is_not_trade_eligible_without_causal_review(self):
        event = self.base_event()
        self.assertFalse(event.is_trade_eligible_positive())

    def test_constructive_label_alone_is_not_enough(self):
        event = self.base_event(causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE)
        self.assertFalse(event.is_trade_eligible_positive())

    def test_review_requires_thesis_provenance_and_counterevidence(self):
        event = self.base_event(
            causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE,
            causal_reviewed_at_et=datetime(2026, 8, 19, 8, 0),
            causal_thesis="Company-defining de-risking with retained economics.",
            causal_review_provenance=("issuer primary release",),
            counterevidence=("commercial adoption remains unproven",),
        )
        self.assertTrue(event.is_trade_eligible_positive())

    def test_mixed_event_is_not_trade_eligible_even_if_headline_is_extreme(self):
        event = self.base_event(
            causal_prior=CausalPrior.MIXED_CONTRADICTORY,
            causal_reviewed_at_et=datetime(2026, 8, 19, 8, 0),
            causal_thesis="Primary endpoint positive but material value-chain evidence conflicts.",
            causal_review_provenance=("issuer primary release",),
            counterevidence=("key secondary outcomes unresolved",),
        )
        self.assertFalse(event.is_trade_eligible_positive())

    def test_price_or_gap_is_not_an_input_to_causal_gate(self):
        event = self.base_event(
            causal_prior=CausalPrior.CONSTRUCTIVE_INCOMPLETE,
            causal_reviewed_at_et=datetime(2026, 8, 19, 8, 0),
            causal_thesis="Positive causal update with remaining commercial uncertainty.",
            causal_review_provenance=("issuer primary release",),
            counterevidence=("pricing and adoption remain uncertain",),
        )
        # EventRecord deliberately has no gap-return or intraday-price field in the gate.
        self.assertTrue(event.is_trade_eligible_positive())


if __name__ == "__main__":
    unittest.main()
