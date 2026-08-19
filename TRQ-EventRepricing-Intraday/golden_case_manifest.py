"""Golden/adversarial case replay manifest.

This manifest contains only replay metadata and research-reviewed causal priors.
It must never be generated from future returns. `expected_replay_notes` are QA/hindsight
annotations used to compare the state engine with observed historical paths; they are
not inputs to the algorithm.
"""

from dataclasses import dataclass

from event_catalog import CausalPrior


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    ticker: str
    year: int
    month: int
    day: int
    sector: str
    broad: str
    causal_prior: CausalPrior
    research_basis: str
    expected_replay_notes: str


REPLAY_CASES = (
    ReplayCase(
        case_id="CYTK_20231227",
        ticker="CYTK",
        year=2023,
        month=12,
        day=27,
        sector="XBI",
        broad="QQQ",
        causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE,
        research_basis="biotech_causal_case_studies_v1.md",
        expected_replay_notes=(
            "Large positive pivotal repricing with sustained continuation potential; "
            "state engine should not classify the opening gap itself as automatic exhaustion."
        ),
    ),
    ReplayCase(
        case_id="NVCR_20240327",
        ticker="NVCR",
        year=2024,
        month=3,
        day=27,
        sector="XBI",
        broad="QQQ",
        causal_prior=CausalPrior.MIXED_CONTRADICTORY,
        research_basis="biotech_causal_case_studies_v1.md",
        expected_replay_notes=(
            "Headline primary-endpoint spike followed by rapid compression; the event is a "
            "control case proving that positive clinical headlines do not imply constructive prior."
        ),
    ),
    ReplayCase(
        case_id="SRRK_20241007",
        ticker="SRRK",
        year=2024,
        month=10,
        day=7,
        sector="XBI",
        broad="QQQ",
        causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE,
        research_basis="biotech_causal_case_studies_v1.md",
        expected_replay_notes=(
            "Company-transforming pivotal repricing. Extreme gap must not by itself trigger fade."
        ),
    ),
    ReplayCase(
        case_id="ARM_20240208",
        ticker="ARM",
        year=2024,
        month=2,
        day=8,
        sector="SOXX",
        broad="QQQ",
        causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE,
        research_basis="semiconductor_causal_case_studies_v1.md",
        expected_replay_notes=(
            "Strong continuation with possible float amplification; state engine must treat float as "
            "price-formation context rather than fundamental quality."
        ),
    ),
    ReplayCase(
        case_id="NVDA_20230525",
        ticker="NVDA",
        year=2023,
        month=5,
        day=25,
        sector="SOXX",
        broad="QQQ",
        causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE,
        research_basis="semiconductor_causal_case_studies_v1.md",
        expected_replay_notes=(
            "Extreme-quality estimate revision with much of price discovery occurring before/open; "
            "constructive prior does not require large regular-session second expansion."
        ),
    ),
    ReplayCase(
        case_id="AVGO_20241213",
        ticker="AVGO",
        year=2024,
        month=12,
        day=13,
        sector="SOXX",
        broad="QQQ",
        causal_prior=CausalPrior.STRONGLY_CONSTRUCTIVE,
        research_basis="semiconductor_causal_case_studies_v1.md",
        expected_replay_notes=(
            "Mega-cap structural rerating combining current AI cash economics and forward hyperscaler "
            "opportunity; forecast narrative and reported revenue must remain distinct."
        ),
    ),
)


def get_case(case_id: str) -> ReplayCase:
    for case in REPLAY_CASES:
        if case.case_id == case_id:
            return case
    raise KeyError(case_id)
