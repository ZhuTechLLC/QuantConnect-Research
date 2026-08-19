from __future__ import annotations

from dataclasses import dataclass
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
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


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
    notes: str = ""

    def is_trade_eligible_positive(self) -> bool:
        return (
            self.direction > 0
            and self.evidence_grade == EvidenceGrade.PRIMARY_VERIFIED
            and self.information_strength in {InformationStrength.HIGH, InformationStrength.EXTREME}
        )


# Golden/adversarial records are deliberately explicit rather than inferred from future data.
# Exact event timestamps must be verified before production replay/backtest.
SEED_EVENT_METADATA = {
    "MRNA_20260819": {
        "ticker": "MRNA",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "VKTX_20240227": {
        "ticker": "VKTX",
        "event_type": "PHASE2",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "MDGL_20221219": {
        "ticker": "MDGL",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "SMMT_20240909": {
        "ticker": "SMMT",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "NVDA_20230525": {
        "ticker": "NVDA",
        "event_type": "GUIDANCE",
        "sector_benchmark": "SOXX",
        "broad_benchmark": "QQQ",
    },
    "MU_20240321": {
        "ticker": "MU",
        "event_type": "GUIDANCE",
        "sector_benchmark": "SOXX",
        "broad_benchmark": "QQQ",
    },
    "CYTK_20231227": {
        "ticker": "CYTK",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "NVCR_20240327": {
        "ticker": "NVCR",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "SRRK_20241007": {
        "ticker": "SRRK",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "ALNY_20240624": {
        "ticker": "ALNY",
        "event_type": "PHASE3",
        "sector_benchmark": "XBI",
        "broad_benchmark": "QQQ",
    },
    "ARM_20240208": {
        "ticker": "ARM",
        "event_type": "GUIDANCE",
        "sector_benchmark": "SOXX",
        "broad_benchmark": "QQQ",
    },
    "AVGO_20241213": {
        "ticker": "AVGO",
        "event_type": "GUIDANCE",
        "sector_benchmark": "SOXX",
        "broad_benchmark": "QQQ",
    },
}
