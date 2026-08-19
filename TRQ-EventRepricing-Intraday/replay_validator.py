from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import sys

STATE_RE = re.compile(
    r"STATE\|(?P<time>[^|]+)\|(?P<ticker>[^|]+)\|"
    r"tracked=(?P<tracked>[^|]+)\|raw=(?P<raw>[^|]+)\|"
    r"score=(?P<score>[^|]+)\|px=(?P<px>[^|]+)\|"
)
SUMMARY_RE = re.compile(
    r"SUMMARY\|(?P<ticker>[^|]+)\|date=(?P<date>[^|]+)\|"
    r"transitions=(?P<transitions>\d+)\|counts=(?P<counts>.*)$"
)

S0 = "S0_PRICE_DISCOVERY"
S1 = "S1_RUSH_CONTINUATION"
S2 = "S2_RUSH_EXHAUSTION"
S3 = "S3_FAILED_EXTENSION_DISTRIBUTION"
S4 = "S4_ACCEPTANCE_BALANCE"
S5 = "S5_SECOND_EXPANSION"


@dataclass(frozen=True)
class Transition:
    timestamp: str
    ticker: str
    tracked: str
    raw: str
    score: float
    price: float


@dataclass
class ReplayAudit:
    ticker: str = ""
    transitions: list[Transition] = field(default_factory=list)
    summary_counts: dict[str, int] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)

    def first(self, state: str) -> Transition | None:
        return next((x for x in self.transitions if x.tracked == state), None)

    def has(self, state: str) -> bool:
        return self.first(state) is not None


def parse_timestamp(text: str) -> datetime | None:
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            pass
    return None


def parse_log(text: str) -> ReplayAudit:
    audit = ReplayAudit()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        marker = line.find("STATE|")
        if marker >= 0:
            m = STATE_RE.search(line[marker:])
            if not m:
                continue
            transition = Transition(
                timestamp=m.group("time"),
                ticker=m.group("ticker"),
                tracked=m.group("tracked"),
                raw=m.group("raw"),
                score=float(m.group("score")),
                price=float(m.group("px")),
            )
            audit.ticker = transition.ticker
            audit.transitions.append(transition)
            continue

        marker = line.find("SUMMARY|")
        if marker >= 0:
            m = SUMMARY_RE.search(line[marker:])
            if not m:
                continue
            audit.ticker = audit.ticker or m.group("ticker")
            for item in m.group("counts").split(","):
                if not item or ":" not in item:
                    continue
                key, value = item.rsplit(":", 1)
                audit.summary_counts[key] = int(value)
    return audit


def validate_semantics(audit: ReplayAudit) -> None:
    if not audit.transitions:
        audit.failures.append("no STATE transitions parsed")
        return

    first = audit.transitions[0]
    if first.tracked != S0:
        audit.failures.append(f"first tracked state is {first.tracked}, expected {S0}")

    # S5 is semantically illegal unless S4 occurred earlier in the tracked path.
    seen_s4 = False
    for tr in audit.transitions:
        if tr.tracked == S4:
            seen_s4 = True
        if tr.tracked == S5 and not seen_s4:
            audit.failures.append(
                f"illegal S5 at {tr.timestamp}: no prior tracked S4 in replay path"
            )

    downgraded = [
        tr for tr in audit.transitions if tr.raw == S5 and tr.tracked == S1
    ]
    if downgraded:
        audit.observations.append(
            f"{len(downgraded)} expansion-like raw state(s) correctly treated as initial rush continuation"
        )

    for state in (S1, S2, S3, S4, S5):
        tr = audit.first(state)
        if tr:
            audit.observations.append(f"first {state}: {tr.timestamp} @ {tr.price:.4f}")


def validate_case_signature(audit: ReplayAudit, case_id: str) -> None:
    """Case-specific QA is intentionally weak and falsifiable.

    These checks do not require exact historical hindsight sequences and do not tune
    thresholds. They catch contradictions to the reason each case was selected.
    """

    validate_semantics(audit)

    if case_id == "NVCR_20240327":
        # The control case should show deterioration after the opening spike. Requiring
        # either S2 or S3 is deliberately weaker than forcing a particular threshold.
        if not (audit.has(S2) or audit.has(S3)):
            audit.failures.append("NVCR never entered exhaustion/distribution")

    elif case_id in {"CYTK_20231227", "SRRK_20241007", "ARM_20240208"}:
        # These large-repricing cases must not be interpreted as failed solely because
        # the gap is large. We require evidence that the engine can represent a positive
        # continuation regime somewhere after S0.
        if not (audit.has(S1) or audit.has(S5)):
            audit.failures.append(f"{case_id} never expressed tracked continuation")

    elif case_id == "NVDA_20230525":
        # Strong causal prior does not require a second regular-session leg. No S5 is a
        # valid result. We only reject a pathological replay that immediately starts S3.
        post_open = [x for x in audit.transitions if x.tracked != S0]
        if post_open and post_open[0].tracked == S3:
            audit.failures.append("NVDA first post-discovery state is immediate distribution")

    elif case_id == "AVGO_20241213":
        if len(audit.transitions) < 2:
            audit.failures.append("AVGO replay has insufficient state differentiation")


def render_markdown(case_id: str, audit: ReplayAudit) -> str:
    status = "PASS" if not audit.failures else "FAIL"
    lines = [
        f"# Golden Replay Audit — {case_id}",
        "",
        f"**Status:** {status}",
        f"**Ticker:** {audit.ticker or 'unknown'}",
        f"**Parsed transitions:** {len(audit.transitions)}",
        "",
        "## Transition sequence",
        "",
    ]
    for tr in audit.transitions:
        lines.append(
            f"- {tr.timestamp}: tracked `{tr.tracked}`, raw `{tr.raw}`, "
            f"score {tr.score:.2f}, price {tr.price:.4f}"
        )
    lines += ["", "## Observations", ""]
    lines += [f"- {x}" for x in audit.observations] or ["- none"]
    lines += ["", "## Failures", ""]
    lines += [f"- {x}" for x in audit.failures] or ["- none"]
    lines += ["", "## State observation counts", ""]
    lines += [f"- `{k}`: {v}" for k, v in sorted(audit.summary_counts.items())] or ["- unavailable"]
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: python replay_validator.py CASE_ID LEAN_LOG [OUTPUT_MD]", file=sys.stderr)
        return 2
    case_id = sys.argv[1]
    log_path = Path(sys.argv[2])
    audit = parse_log(log_path.read_text(encoding="utf-8", errors="replace"))
    validate_case_signature(audit, case_id)
    report = render_markdown(case_id, audit)
    if len(sys.argv) >= 4:
        Path(sys.argv[3]).write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0 if not audit.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
