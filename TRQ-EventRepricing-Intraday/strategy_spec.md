# TRQ Event Repricing Intraday v1

## Purpose

Research and trade large positive event-day repricing without relying on deterministic support/resistance or breakout narratives. The model separates **causal event underwriting** from **intraday market-state inference** and uses only point-in-time information available at each decision timestamp.

## Scope

v1 covers verified positive fundamental events with material price repricing:

- Biotech: Phase II, Phase III, FDA/regulatory decisions.
- Semiconductors/large-cap technology: earnings, guidance, major product or demand shocks.

v1 does not trade unverified social-media catalysts, rumor-only gaps, short squeezes without primary evidence, or options.

## Core Principle

**Event causality determines the directional/economic prior. Intraday microstructure determines whether and when to trade.**

The strategy must not use support/resistance or breakout levels as primary signal features. Price levels may be logged descriptively, but they cannot independently trigger entry or exit.

A large gap, a small p-value, a Phase III primary-endpoint win, a large addressable market, or an earnings beat is never sufficient by itself. The same numerical event can have radically different shareholder value implications depending on disease severity, unmet need, endpoint quality, safety, durability, standard of care, competition, economic ownership, pricing/reimbursement, commercialization readiness, financing needs, company maturity, prior expectations and the macro/sector regime.

## Two-Layer Architecture

### Layer 1 — Causal Event Underwriting

This layer answers **why the stock should be worth materially more or less after the event**. It is built from primary/authoritative evidence and is point-in-time.

It does not look at future returns and it does not use intraday price success to retroactively label an event as high quality.

Required domains:

#### A. Clinical / Product Evidence
- disease or end market;
- addressable patient/customer population available at the event timestamp;
- disease severity / customer pain;
- unmet need;
- current standard of care / incumbent;
- trial phase or product maturity;
- trial design, control arm and population;
- primary endpoint result and effect magnitude;
- secondary endpoints;
- hard outcomes, durability and follow-up when available;
- subgroup consistency;
- safety/reliability;
- evidence completeness: topline partial vs rich topline vs full data;
- regulatory/customer validation path;
- treatment/adoption burden.

#### B. Commercial Translation
- business model;
- who owns the economics;
- partner, profit-share, royalty or licensing obligations;
- commercialization readiness and sales infrastructure;
- existing revenue base;
- likely pricing/reimbursement/contracting constraints;
- competition and differentiation;
- adoption friction;
- manufacturing/distribution constraints when material;
- financing/dilution risk;
- margin and operating-leverage implications.

#### C. Company Context
- pre-revenue / early-commercial / commercial / mature;
- market-cap context at the event timestamp;
- cash runway and balance sheet;
- profitability/cash-burn context;
- product/customer concentration;
- strategic platform optionality.

#### D. Expectations and Surprise
- evidence already known before the event;
- contemporaneous consensus/narrative where supportable;
- key bear and bull cases before the event;
- what uncertainty the event actually removed;
- what uncertainty remained immediately after the event;
- whether the dominant shareholder-value driver changed;
- event increment versus prior expectation.

#### E. Macro / Sector Transmission
Macro is not a generic score. Record only the causal path:
- monetary/liquidity regime;
- broad-market regime;
- sector cycle;
- rates/risk-premium/funding conditions when they matter;
- event-day sector and broad benchmark moves;
- explicit transmission to valuation, financing, demand or adoption.

For company-specific biotech readouts, macro is often a secondary valuation/risk-budget overlay. For semiconductors, industry demand, capex, inventory, hyperscaler spending, rates and broad risk appetite may be much more directly relevant.

### Causal Prior

The output is a **reviewed causal prior**, not a weighted score.

Allowed working labels may include:
- strongly constructive;
- constructive but incomplete;
- mixed/contradictory;
- economically limited despite positive headline;
- unreviewed.

Every label must be accompanied by a short causal thesis and explicit counterevidence.

The prior can change when new public evidence arrives, but later full data may not be back-filled into an earlier timestamp.

### Layer 2 — Intraday State Inference

This layer answers **how the market is currently processing the event**. It uses price, volume, volatility and relative/residual-return features. It does not reinterpret the clinical or commercial facts.

The same state engine may be shared across biotech and semiconductor events, while the causal priors remain domain-specific.

## Point-in-Time Event Record

Each event requires at minimum:
- ticker, event_id, event_type, event_timestamp_et;
- direction and evidence grade;
- evidence completeness;
- clinical/product context when applicable;
- commercial context;
- company context;
- expectation context;
- macro/sector transmission context;
- reviewed causal prior and causal thesis;
- counterevidence;
- PIT source notes;
- separate hindsight-validation notes;
- sector and broad benchmarks.

## State Machine

### S0 PRICE_DISCOVERY
Opening information absorption. Default no-entry state.

### S1 RUSH_CONTINUATION
Fast directional price discovery after the open. v1 observes but does not initiate during the first rush by default.

### S2 RUSH_EXHAUSTION
The initial directional move loses efficiency: peak age rises, normalized retracement rises, path efficiency falls, and volume/realized volatility begin to decay.

### S3 FAILED_EXTENSION_DISTRIBUTION
Post-rush reversal becomes persistent: negative residual returns, weak rebound efficiency, increasing downward path efficiency and deepening retracement.

### S4 ACCEPTANCE_BALANCE
A temporary new equilibrium: volatility and volume contract, directional residual return weakens and short-window path efficiency becomes low.

### S5 SECOND_EXPANSION
A new directional move emerges from S4: return and volume surprise re-expand, residual return becomes materially directional and path efficiency increases.

Entry is based on state-transition evidence, not a fixed price breakout.

## Point-in-Time Features

All features must be computable using only observations available through time t.

### Return Features
- gap_return; return_1m/5m/15m/30m; return_from_open;
- residual_return_5m/15m/30m.

### Path Features
- running_high/running_low;
- peak_age_minutes/trough_age_minutes;
- normalized_retracement using running high only;
- rebound_efficiency;
- path_efficiency_5m/15m/30m.

PE = abs(P_t - P_start) / sum(abs(delta_P_i))

### Volatility Features
- rv_5m/15m/30m;
- rv_ratio_5_30 / rv_ratio_15_30;
- volatility_decay.

### Volume Features
- cumulative_volume;
- cumulative_rvol_same_time;
- volume_z_5m/15m;
- opening_volume_share;
- volume_decay_ratio.

Historical same-time volume baselines must use only dates prior to the event date.

### VWAP Features
- cumulative_vwap;
- vwap_distance;
- vwap_distance_z.

VWAP is a state variable, not support/resistance.

### Relative/Residual Features
Biotech: XBI + broad benchmark. Semiconductors: SOXX/SMH + QQQ where available.

Residual return must use a documented past-only benchmark-adjustment model.

### Optional Quote/Order-Flow Features
Not required in v1: spread, quote imbalance, order-flow imbalance. Add only when backtest/live data parity is verified.

## Trading Policies

### Policy A — Post-Rush Fade
Research-only until validated. Requires joint evidence of S2→S3 deterioration; never trigger solely from gap size or distance from prior close.

### Policy B — Post-Rush Second Expansion
Primary v1 candidate. Requires:
- reviewed causal prior that remains constructive;
- no contradictory new event evidence;
- S4 balance established;
- transition evidence toward S5;
- return/volume/residual/path-efficiency re-expansion.

A constructive causal prior is necessary but not sufficient. A strong S5 microstructure state cannot rescue a contradictory/poorly-understood event without an explicit research override.

## Risk

Initial research parameters only:
- risk_per_trade_nav: 0.15%-0.30%;
- max_symbol_daily_loss_nav: 0.50%-0.60%;
- max_attempts_per_symbol_per_day: 2;
- time_stop_minutes: 10-20;
- no short-dated options in v1.

Position sizing is volatility-based. Exact estimators must be validated against event-day realized volatility.

## Exit Logic

Exit when the expected state transition fails, residual return loses expected persistence, path efficiency collapses, volatility expansion fails after S5 entry, risk limits are hit, or contradictory new evidence arrives. Fixed support/resistance stops are not primary exits.

## Labels

Do not train primarily on next-bar direction. Store forward outcomes at 5m, 15m, 30m, 60m, close, next_open and next_close, plus MAE/MFE and timing.

## Backtest Integrity

Mandatory:
- running HOD/LOD only;
- actual public event timestamps;
- prior-only volume baselines, betas and z-scores;
- no event leakage across train/validation/test;
- no later analyst revisions/full clinical data back-filled into earlier records;
- causal-prior labels cannot be derived from future price performance.

Validation sequence:
1. causal case audit;
2. golden case replay;
3. expanded event sample;
4. walk-forward validation;
5. slippage/latency stress tests;
6. paper live;
7. micro-live.

## Golden / Adversarial Case Philosophy

Cases are not selected merely because their gaps differ. They are selected because the **causal chain from event evidence to shareholder value differs**.

Each case review must answer:
1. What exactly changed scientifically/product-wise?
2. How big and valuable is the addressable problem?
3. Who captures the economics and with what friction?
4. What did investors plausibly expect beforehand?
5. Which uncertainties disappeared and which remained?
6. How did macro/sector conditions transmit into the stock, if at all?
7. How much of the move was company-specific residual repricing?
8. Only then: how did Morning Rush, exhaustion, balance, continuation or distribution unfold?

## Provisional Validation Gates

Internal research gates, not claims of optimality:
- positive after-cost expectancy in a majority of walk-forward folds;
- aggregate profit factor approximately >1.2;
- positive expectancy under 2x slippage stress;
- no single event contributes >20%-25% of PnL;
- modest parameter perturbations do not destroy the edge;
- performance reported by event type, causal-prior category, gap bucket, market-cap bucket, macro/sector regime and year;
- bootstrap uncertainty reported.

Failure means research continues; no live capital deployment.
