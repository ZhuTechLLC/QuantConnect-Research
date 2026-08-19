# Adversarial Case Set for EventRepricingIntraday v1

Purpose: challenge the state machine with positive events that produce materially different intraday paths. These cases are not used to prove profitability. They test whether event priors and intraday states remain distinct under contradictory examples.

## Case A — CYTK, 2023-12-27, Phase 3 positive / strong continuation

Event: SEQUOIA-HCM Phase 3 aficamten topline results.

Primary evidence:
- Primary endpoint: statistically significant and clinically meaningful improvement.
- Improvements across all prespecified subgroups.
- All secondary endpoints improved.
- No treatment interruptions due to low LVEF in the topline release.

Observed market reaction from contemporaneous reporting:
- More than 50% premarket.
- Shares later surged more than 80% intraday.

Why it matters:
- Strong positive event quality can sustain repricing even after a very large opening gap.
- Gap magnitude cannot be used as a standalone fade trigger.
- Full-event quality includes secondary endpoints and safety, not just primary endpoint status.

## Case B — NVCR, 2024-03-27, Phase 3 primary positive / gap-fade

Event: METIS Phase 3 met its primary endpoint.

Primary evidence:
- Median time to intracranial progression 21.9 months vs 11.3 months.
- Hazard ratio 0.67; p=0.016.

Contradictory evidence available the same morning:
- Preliminary analyses of key secondary endpoints including overall survival and several other measures did not reach statistical significance.

Observed reaction:
- Shares were reported up roughly 33% premarket.
- By about 10:00 ET, contemporaneous reporting showed the stock only around +9.3%.

Why it matters:
- A positive primary endpoint does not guarantee a high-quality event prior.
- Missing/weak secondary outcomes can cause rapid expectation compression after the opening print.
- `event_quality` must be multi-dimensional and point-in-time.

## Case C — SRRK, 2024-10-07, Phase 3 positive / extreme repricing

Event: SAPPHIRE Phase 3 apitegromab topline results.

Primary evidence:
- Primary endpoint met with statistically significant and clinically meaningful improvement in motor function.
- 30.4% of treated patients achieved >3 point HFMSE improvement vs 12.5% placebo.
- Favorable safety profile reported.
- Regulatory submissions planned for Q1 2025.

Observed reaction:
- Shares rose more than 300% during the morning according to contemporaneous reporting.

Why it matters:
- Even a >300% event-day move cannot automatically be classified as overextension.
- In binary-risk biotech, probability-of-success repricing can dominate ordinary technical priors.
- Position sizing and no-chase rules still matter because absolute volatility becomes extreme.

## Case D — ALNY, 2024-06-24, Phase 3 positive / high-quality commercial de-risking

Event: HELIOS-B Phase 3 vutrisiran topline results.

Primary evidence:
- Primary endpoint and all secondary endpoints achieved statistical significance in overall and monotherapy populations.
- Later detailed disclosure confirmed broad disease-progression benefits.

Observed reaction:
- Shares were reported up roughly 30%-38% during the morning/session.

Why it matters:
- A mature biotech with an established commercial platform can still exhibit a large clinical repricing event.
- Event type alone is insufficient; company maturity and incremental commercial value must be metadata.

## Case E — ARM, 2024-02-08, earnings/guidance / mature-market gap continuation then intraday giveback

Event: fiscal Q3 results and raised guidance released after the February 7 close.

Primary evidence:
- Q3 revenue $824m versus prior guidance $720m-$800m.
- Q4 revenue guidance $850m-$900m.
- FY24 revenue guidance raised to $3.155b-$3.205b from $2.960b-$3.080b.

Observed reaction:
- Shares closed about +48% the next day and traded as high as roughly $126.58 intraday before closing $113.89.

Why it matters:
- A powerful earnings/guidance event can support a very large day return while still producing a large intraday peak-to-close giveback.
- Closing return and intraday continuation are different labels.
- The state model needs MAE/MFE and time-to-peak labels, not only close-to-close return.

## Case F — AVGO, 2024-12-13, earnings/AI outlook / large-cap continuation

Event: fiscal Q4/FY24 results plus AI outlook.

Primary evidence:
- FY24 AI revenue $12.2b, +220% y/y.
- Q1 FY25 revenue guidance approximately $14.6b, +22% y/y.
- Management discussed a very large AI accelerator/networking opportunity for FY27.

Observed reaction:
- Shares closed +24.4%, the largest one-day gain in company history at the time, despite Broadcom already being a mega-cap company.

Why it matters:
- Market-cap size reduces but does not eliminate event-day repricing magnitude.
- Semiconductor earnings events should have different priors from clinical binary-risk events, but can share the same intraday state features.

# Schema Lessons from the Six Adversarial Cases

1. `primary_endpoint_met` is not an event-quality score.
2. Secondary endpoints, safety, evidence completeness, commercial relevance, and prior expectations are required inputs.
3. Gap magnitude is descriptive, not directional.
4. Intraday peak-to-close giveback must be modeled separately from event-day close return.
5. Binary-risk biotech and earnings/guidance events need separate event priors but can share the same state engine.
6. `Morning Rush -> Exhaustion -> Balance -> Second Expansion` must be inferred from path/volume/volatility/residual-return features, not fixed prices.
7. Every case replay must preserve the event release timestamp and the information that was actually available at each minute.
