from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    FDA = "FDA"
    EARNINGS = "EARNINGS"
    GUIDANCE = "GUIDANCE"
    PRODUCT = "PRODUCT"
    DEMAND = "DEMAND"
    OTHER = "OTHER"


class EvidenceGrade(str, Enum):
    PRIMARY_VERIFIED = "primary_verified"
    AUTHORITATIVE_SECONDARY = "authoritative_secondary"
    UNVERIFIED = "unverified"


class InformationStrength(str, Enum):
    """Headline information magnitude, not a valuation or trade score."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class EvidenceCompleteness(str, Enum):
    TOPLINE_PARTIAL = "topline_partial"
    TOPLINE_RICH = "topline_rich"
    FULL_DATA = "full_data"
    NOT_APPLICABLE = "not_applicable"


class CompanyStage(str, Enum):
    PRE_REVENUE = "pre_revenue"
    EARLY_COMMERCIAL = "early_commercial"
    COMMERCIAL = "commercial"
    MATURE = "mature"


class MacroRelevance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EconomicCapture(str, Enum):
    HIGH = "high"
    SHARED = "shared"
    ROYALTY_BURDENED = "royalty_burdened"
    LICENSED_OUT = "licensed_out"
    UNCLEAR = "unclear"


class AdoptionFriction(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClinicalOrProductContext:
    """What the product/event actually changes in the real world.

    Values must be point-in-time. Later full data may be stored in hindsight notes,
    never back-filled into an earlier event decision record.
    """

    disease_or_end_market: str = "unknown"
    target_population: str = "unknown"
    addressable_population_or_market: str = "unknown"
    disease_severity_or_customer_pain: str = "unknown"
    unmet_need: str = "unknown"
    current_standard_of_care_or_incumbent: str = "unknown"
    primary_evidence: str = "unknown"
    secondary_evidence: str = "unknown"
    hard_outcomes_or_durability: str = "unknown"
    safety_or_reliability: str = "unknown"
    subgroup_consistency: str = "unknown"
    treatment_or_adoption_burden: str = "unknown"
    evidence_completeness: EvidenceCompleteness = EvidenceCompleteness.NOT_APPLICABLE
    regulatory_or_customer_validation_path: str = "unknown"


@dataclass(frozen=True)
class CommercialContext:
    """How scientific/product success can become shareholder economics."""

    business_model: str = "unknown"
    economic_capture: EconomicCapture = EconomicCapture.UNCLEAR
    partner_or_royalty_economics: str = "unknown"
    commercialization_readiness: str = "unknown"
    existing_revenue_base: str = "unknown"
    pricing_reimbursement_or_contracting: str = "unknown"
    competition_and_differentiation: str = "unknown"
    adoption_friction: AdoptionFriction = AdoptionFriction.UNKNOWN
    financing_or_dilution_risk: str = "unknown"
    margin_or_operating_leverage: str = "unknown"


@dataclass(frozen=True)
class CompanyContext:
    stage: CompanyStage = CompanyStage.PRE_REVENUE
    market_cap_context: str = "unknown"
    cash_runway_or_balance_sheet: str = "unknown"
    profitability_context: str = "unknown"
    customer_or_product_concentration: str = "unknown"
    strategic_optionality: str = "unknown"


@dataclass(frozen=True)
class ExpectationContext:
    """What the market plausibly expected before the event and what changed."""

    known_pre_event_evidence: str = "unknown"
    pre_event_consensus_or_narrative: str = "unknown"
    key_bear_case_before_event: str = "unknown"
    key_bull_case_before_event: str = "unknown"
    uncertainty_removed_by_event: str = "unknown"
    uncertainty_remaining_after_event: str = "unknown"
    dominant_value_driver_changed: str = "unknown"
    event_increment_vs_expectation: str = "unknown"


@dataclass(frozen=True)
class MacroSectorContext:
    """Macro is a transmission layer, never a generic score adjustment."""

    relevance: MacroRelevance = MacroRelevance.LOW
    monetary_and_liquidity_regime: str = "unknown"
    sector_cycle: str = "unknown"
    broad_market_regime: str = "unknown"
    transmission_to_company: str = "unknown"
    event_day_sector_move: str = "to_be_computed_in_replay"
    event_day_broad_move: str = "to_be_computed_in_replay"


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    ticker: str
    event_type: EventType
    event_timestamp_et: datetime
    direction: int
    evidence_grade: EvidenceGrade
    information_strength: InformationStrength
    full_data_available: bool
    primary_endpoint_status: str | None = None
    secondary_endpoint_status: str | None = None
    safety_signal_status: str | None = None
    commercial_relevance: str = "unknown"
    sector_benchmark: str = "SPY"
    broad_benchmark: str = "SPY"
    clinical_or_product: ClinicalOrProductContext = field(default_factory=ClinicalOrProductContext)
    commercial: CommercialContext = field(default_factory=CommercialContext)
    company: CompanyContext = field(default_factory=CompanyContext)
    expectations: ExpectationContext = field(default_factory=ExpectationContext)
    macro_sector: MacroSectorContext = field(default_factory=MacroSectorContext)
    causal_prior: str = "unreviewed"
    causal_thesis: str = ""
    counterevidence: tuple[str, ...] = ()
    pit_source_notes: tuple[str, ...] = ()
    hindsight_validation_notes: tuple[str, ...] = ()
    notes: str = ""

    def passes_minimum_evidence_gate(self) -> bool:
        """Minimum research gate only; never treat this as an event-quality score."""
        return self.direction > 0 and self.evidence_grade == EvidenceGrade.PRIMARY_VERIFIED

    def is_trade_eligible_positive(self) -> bool:
        """Compatibility helper for v1.

        A high/extreme headline is necessary but explicitly insufficient. Production
        trade eligibility additionally requires a reviewed causal prior and the
        intraday state policy. This method must never be the sole order trigger.
        """
        return (
            self.passes_minimum_evidence_gate()
            and self.information_strength in {InformationStrength.HIGH, InformationStrength.EXTREME}
            and self.causal_prior not in {"unreviewed", "contradictory", "negative"}
        )


# Seed metadata is deliberately sparse. Causal contexts are populated only after a
# point-in-time case review; they must never be inferred from future stock returns.
SEED_EVENT_METADATA = {
    "MRNA_20260819": {"ticker": "MRNA", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "VKTX_20240227": {"ticker": "VKTX", "event_type": "PHASE2", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "MDGL_20221219": {"ticker": "MDGL", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "SMMT_20240909": {"ticker": "SMMT", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "NVDA_20230525": {"ticker": "NVDA", "event_type": "GUIDANCE", "sector_benchmark": "SOXX", "broad_benchmark": "QQQ"},
    "MU_20240321": {"ticker": "MU", "event_type": "GUIDANCE", "sector_benchmark": "SOXX", "broad_benchmark": "QQQ"},
    "CYTK_20231227": {"ticker": "CYTK", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "NVCR_20240327": {"ticker": "NVCR", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "SRRK_20241007": {"ticker": "SRRK", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "ALNY_20240624": {"ticker": "ALNY", "event_type": "PHASE3", "sector_benchmark": "XBI", "broad_benchmark": "QQQ"},
    "ARM_20240208": {"ticker": "ARM", "event_type": "GUIDANCE", "sector_benchmark": "SOXX", "broad_benchmark": "QQQ"},
    "AVGO_20241213": {"ticker": "AVGO", "event_type": "GUIDANCE", "sector_benchmark": "SOXX", "broad_benchmark": "QQQ"},
}
