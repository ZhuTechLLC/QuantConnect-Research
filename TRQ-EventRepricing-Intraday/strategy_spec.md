# TRQ Event Repricing Intraday v1

## Purpose

Research and trade large positive event-day repricing without relying on deterministic support/resistance or breakout narratives. The model separates event quality from intraday state and uses only point-in-time information available at each decision timestamp.

## Scope

v1 only covers verified positive fundamental events with material price repricing:

- Biotech: Phase II, Phase III, FDA/regulatory decisions.
- Semiconductors/large-cap technology: earnings, guidance, major product or demand shocks.

v1 does not trade unverified social-media catalysts, rumor-only gaps, short squeezes without primary evidence, or options.

## Core Principle

Event quality determines directional prior. Intraday microstructure determines whether and when to trade.

The strategy must not use support/resistance or breakout levels as primary signal features. Price levels may be logged descriptively, but they cannot independently trigger entry or exit.

## Point-in-Time Event Record

Each event requires:

- ticker
- event_id
- event_type: PHASE2 | PHASE3 | FDA | EARNINGS | GUIDANCE | PRODUCT | DEMAND | OTHER
- event_timestamp_et
- direction
- evidence_grade: primary_verified | authoritative_secondary | unverified
- information_strength: low | medium | high | extreme
- full_data_available: bool
- primary_endpoint_status when applicable
- secondary_endpoint_status when applicable
- safety_signal_status when applicable
- pre_event_market_expectation_notes
- previous_close
- premarket_return when available
- sector_benchmark
- broad_benchmark

### Event Quality Prior

The prior must distinguish:

1. Endpoint/result quality.
2. Magnitude versus prior expectation.
3. Completeness of disclosed evidence.
4. Safety/regulatory uncertainty.
5. Commercial relevance.
6. Whether the information changes probability of success, earnings path, or terminal value.

A nominally positive headline is not automatically high quality. Example: a primary endpoint can be positive while secondary endpoints, durability, safety, or expected commercial impact weaken the event.

## State Machine

### S0 PRICE_DISCOVERY

Opening information absorption. Default no-entry state.

Typical characteristics:
- very high realized volatility;
- very high relative volume;
- unstable direction;
- low confidence in path persistence.

### S1 RUSH_CONTINUATION

Fast directional price discovery after the open.

Characteristics:
- high path efficiency in event direction;
- positive residual return versus sector/broad benchmark;
- expanding or sustained realized volatility;
- high volume participation.

v1 observes but does not initiate during the first rush by default.

### S2 RUSH_EXHAUSTION

The initial directional move loses efficiency.

Characteristics:
- running peak ages;
- normalized retracement rises;
- path efficiency falls;
- volume and realized volatility begin to decay;
- rebound attempts become less efficient.

### S3 FAILED_EXTENSION_DISTRIBUTION

Post-rush reversal becomes persistent rather than a normal pullback.

Characteristics:
- negative residual return over multiple windows;
- weak rebound efficiency;
- downward path efficiency increases;
- retracement deepens while peak age increases;
- failed recovery attempts occur without relying on fixed price levels.

### S4 ACCEPTANCE_BALANCE

The market forms a temporary new equilibrium after the rush/exhaustion.

Characteristics:
- realized volatility contraction;
- volume contraction relative to event-day opening intensity;
- low short-window path efficiency;
- reduced directional residual return;
- narrower return distribution.

### S5 SECOND_EXPANSION

A new directional move emerges from S4.

Characteristics:
- return z-score expands in event direction;
- volume surprise re-expands;
- residual return turns materially positive;
- path efficiency increases;
- realized volatility expands from a lower base.

Entry is based on state transition evidence, not a fixed price breakout.

## Point-in-Time Features

All features must be computable using only observations available through time t.

### Return Features
- gap_return
- return_1m
- return_5m
- return_15m
- return_30m
- return_from_open
- residual_return_5m
- residual_return_15m
- residual_return_30m

### Path Features
- running_high
- running_low
- peak_age_minutes
- trough_age_minutes
- normalized_retracement = (running_high - price) / max(running_high - open, epsilon) for positive event days
- rebound_efficiency = (bounce_high - local_trough) / max(prior_peak - local_trough, epsilon)
- path_efficiency_5m
- path_efficiency_15m
- path_efficiency_30m

Path efficiency:

PE = abs(P_t - P_start) / sum(abs(delta_P_i))

### Volatility Features
- rv_5m
- rv_15m
- rv_30m
- rv_ratio_5_30
- rv_ratio_15_30
- volatility_decay

### Volume Features
- cumulative_volume
- cumulative_rvol_same_time
- volume_z_5m
- volume_z_15m
- opening_volume_share
- volume_decay_ratio

Historical same-time volume baselines must use only dates prior to the event date.

### VWAP Features
- cumulative_vwap
- vwap_distance
- vwap_distance_z

VWAP is a state variable, not support/resistance.

### Relative/Residual Features
For biotech:
- XBI return
- QQQ/SPY return

For semiconductors:
- SOXX/SMH return when available
- QQQ return

Residual return should be estimated using rolling pre-event betas or a simple clearly documented benchmark-adjustment model. No future data allowed.

### Optional Quote/Order-Flow Features
Not required in v1:
- bid-ask spread
- quote imbalance
- order-flow imbalance

These can be added only when data availability is consistent across backtest/live environments.

## v1 Trading Policies

### Policy A: Post-Rush Fade

Research-only until validated.

Candidate condition requires a combination of:
- state S2 transitioning to S3;
- peak_age above threshold;
- normalized_retracement above threshold;
- rebound_efficiency below threshold;
- negative residual_return_15m;
- increasing downward path efficiency.

No short entry solely because gap size is large or price is far above prior close.

### Policy B: Post-Rush Second Expansion

Primary v1 strategy candidate.

Entry candidate requires:
- verified positive event quality at or above configured threshold;
- S4 balance state established;
- transition evidence toward S5;
- return_z_5m above threshold;
- volume_z_5m above threshold;
- residual_return_5m positive and improving;
- path_efficiency_5m/15m rising;
- no material contradictory new event evidence.

## Risk

Initial research parameters, to be optimized only through walk-forward validation:

- risk_per_trade_nav: 0.15% to 0.30%
- max_symbol_daily_loss_nav: 0.50% to 0.60%
- max_attempts_per_symbol_per_day: 2
- time_stop_minutes: 10 to 20
- no short-dated options in v1

Position sizing is volatility-based rather than fixed-share or fixed-percent stop based.

Approximate form:

shares = risk_budget / expected_volatility_loss_per_share

The exact estimator must be specified in code and validated against realized event-day volatility.

## Exit Logic

Exit when one or more occur:

- expected state transition fails within the time stop;
- residual return loses the expected sign and persistence;
- path efficiency collapses;
- volatility expansion fails after S5 entry;
- risk budget or daily loss limit is hit;
- material contradictory event evidence arrives.

Fixed support/resistance price stops are not primary exits.

## Labels

Do not train on next-bar direction as the primary objective.

Store forward outcomes at:
- 5m
- 15m
- 30m
- 60m
- close
- next_open
- next_close

For each decision timestamp store:
- forward_return
- MAE
- MFE
- time_to_MAE
- time_to_MFE

## Backtest Integrity

### Mandatory anti-lookahead rules
- Use running intraday high/low, never final HOD/LOD before they occur.
- Event timestamps must reflect actual public availability.
- Historical volume baselines use prior dates only.
- Rolling betas and z-scores use only past observations.
- Same event cannot be split across train/validation/test.
- No future analyst revisions or later full clinical data may alter the event record at earlier timestamps.

### Validation sequence
1. Golden case replay.
2. Expanded event sample.
3. Walk-forward validation.
4. Slippage/latency stress tests.
5. Paper live.
6. Micro-live.

## Golden Seed Cases

Existing seed cases:
- MRNA 2026-08-19 Phase III oncology event
- VKTX 2024-02-27 Phase II obesity event
- MDGL 2022-12-19 Phase III NASH event
- SMMT 2024-09-09 Phase III oncology event
- NVDA 2023-05-25 earnings/guidance event
- MU 2024-03-21 earnings/guidance event

Adversarial cases will be added before thresholds are frozen.

## Provisional Validation Gates

These are internal research gates, not claims of optimality:

- positive after-cost expectancy in a majority of walk-forward folds;
- aggregate profit factor approximately >1.2;
- positive expectancy under 2x base slippage stress;
- no single event contributes more than roughly 20%-25% of total PnL;
- small parameter perturbations do not destroy the edge;
- performance is reported separately by event type, gap bucket, market-cap bucket, and year;
- bootstrap uncertainty is reported.

Failure to pass means research continues; no live capital deployment.
