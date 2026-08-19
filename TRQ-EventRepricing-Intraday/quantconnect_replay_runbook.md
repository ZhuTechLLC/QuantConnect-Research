# QuantConnect Golden Case Replay Runbook

## Goal

Run the first LEAN validation stage without placing orders. The algorithm only streams historical minute bars through the PIT feature engine and state machine and logs state transitions.

Do not merge or deploy live until golden replay and anti-lookahead checks pass.

## Current branch

`chatgpt/event-repricing-v1-20260819`

## One-time cloud binding

The current ChatGPT TRQuant DevOps allowlist is tied to an older fixed QuantConnect project and must **not** be used to overwrite it. Bind this new project once from the local QuantConnect/LEAN workspace.

From the existing `QuantConnect-Research` workspace:

```bash
cd /home/taotao/dev/QuantConnect-Research

git fetch origin
git switch chatgpt/event-repricing-v1-20260819
```

First try the minimal path supported by current LEAN CLI:

```bash
lean cloud push --project "TRQ-EventRepricing-Intraday"
```

Current QuantConnect documentation states that `lean cloud push` creates a cloud project when a project with the same path does not yet exist. If the local directory is not recognized as a LEAN project because it does not yet have generated project metadata, use the fallback below instead of editing a cloud id by hand.

### Safe fallback if project metadata is missing

```bash
lean project-create --language python "TRQ-EventRepricing-Intraday-QC"

cp TRQ-EventRepricing-Intraday/main.py TRQ-EventRepricing-Intraday-QC/main.py
cp TRQ-EventRepricing-Intraday/feature_engine.py TRQ-EventRepricing-Intraday-QC/feature_engine.py
cp TRQ-EventRepricing-Intraday/state_machine.py TRQ-EventRepricing-Intraday-QC/state_machine.py
cp TRQ-EventRepricing-Intraday/event_catalog.py TRQ-EventRepricing-Intraday-QC/event_catalog.py
cp TRQ-EventRepricing-Intraday/golden_case_manifest.py TRQ-EventRepricing-Intraday-QC/golden_case_manifest.py

lean cloud push --project "TRQ-EventRepricing-Intraday-QC"
```

Do not manually invent a `cloud-id` or reuse another project's config.

## Golden replay commands

The current `main.py` accepts `ticker`, `sector`, `broad`, `year`, `month`, and `day` parameters. It does not place trades.

### CYTK — strong pivotal continuation case

```bash
lean cloud backtest "TRQ-EventRepricing-Intraday" --push \
  --name "ER-v1-CYTK-20231227" \
  --parameter ticker CYTK \
  --parameter sector XBI \
  --parameter broad QQQ \
  --parameter year 2023 \
  --parameter month 12 \
  --parameter day 27
```

### NVCR — positive headline / contested causal prior / gap-fade control

```bash
lean cloud backtest "TRQ-EventRepricing-Intraday" --push \
  --name "ER-v1-NVCR-20240327" \
  --parameter ticker NVCR \
  --parameter sector XBI \
  --parameter broad QQQ \
  --parameter year 2024 \
  --parameter month 3 \
  --parameter day 27
```

### SRRK — company-transforming pivotal repricing

```bash
lean cloud backtest "TRQ-EventRepricing-Intraday" --push \
  --name "ER-v1-SRRK-20241007" \
  --parameter ticker SRRK \
  --parameter sector XBI \
  --parameter broad QQQ \
  --parameter year 2024 \
  --parameter month 10 \
  --parameter day 7
```

### ARM — IP/royalty + low-float amplification

```bash
lean cloud backtest "TRQ-EventRepricing-Intraday" --push \
  --name "ER-v1-ARM-20240208" \
  --parameter ticker ARM \
  --parameter sector SOXX \
  --parameter broad QQQ \
  --parameter year 2024 \
  --parameter month 2 \
  --parameter day 8
```

### NVDA — model-ready overnight earnings repricing

```bash
lean cloud backtest "TRQ-EventRepricing-Intraday" --push \
  --name "ER-v1-NVDA-20230525" \
  --parameter ticker NVDA \
  --parameter sector SOXX \
  --parameter broad QQQ \
  --parameter year 2023 \
  --parameter month 5 \
  --parameter day 25
```

### AVGO — custom XPU/networking + software cash-flow rerating

```bash
lean cloud backtest "TRQ-EventRepricing-Intraday" --push \
  --name "ER-v1-AVGO-20241213" \
  --parameter ticker AVGO \
  --parameter sector SOXX \
  --parameter broad QQQ \
  --parameter year 2024 \
  --parameter month 12 \
  --parameter day 13
```

If the fallback project name was used, replace `TRQ-EventRepricing-Intraday` in the backtest commands with `TRQ-EventRepricing-Intraday-QC`.

## What to capture from each replay

Copy/save the LEAN lines beginning with:

`STATE|`

For each transition we need:

- timestamp ET;
- state;
- price only as descriptive context;
- 5m/15m returns;
- normalized retracement using running high only;
- peak age;
- rebound efficiency;
- 5m/15m path efficiency;
- short/long realized-volatility ratio;
- volume decay;
- return and volume z-scores;
- sector/broad residual returns;
- transition reasons.

The first objective is **classification validity**, not PnL.

## Golden replay acceptance criteria

Do not optimize thresholds yet. First ask whether the fixed v1 rules make qualitatively defensible distinctions across contradictory cases.

Minimum acceptance checks:

1. Opening 15 minutes remain `S0_PRICE_DISCOVERY` by policy.
2. A large gap alone never creates `S2`, `S3` or `S5`.
3. CYTK/SRRK can remain/return to constructive microstructure despite enormous absolute gaps.
4. NVCR must be able to move into exhaustion/distribution from joint path evidence rather than a fixed price level.
5. NVDA must be allowed to show a strong causal prior without requiring a large regular-session second leg.
6. ARM price behavior may be amplified by float, but float is not a state-engine input in v1.
7. AVGO's sector/broad residual return should distinguish company-specific repricing from market beta.
8. No transition at time t may depend on a later high, low, volume, analyst revision or later clinical/product evidence.

If these fail, change the feature/state definition only for a causal reason that improves multiple cases. Do not tune a threshold to make one famous case look correct.

## Next phase after replay

Only after the six-case replay is acceptable:

1. Add MRNA 2026-08-19 as a seventh live-observed golden case after its event causal record is finalized.
2. Expand to 50-100 manually audited event records.
3. Build the 200-500+ machine-readable PIT event sample.
4. Add forward-return/MAE/MFE labels that are invisible to the feature engine.
5. Run walk-forward tests and slippage/latency stress.
6. Only then implement actual order logic.

## Official CLI references verified 2026-08-19

- `lean cloud push --project <project>`: pushes a local project; if the cloud project does not exist, QuantConnect documents that it creates it.
- `lean cloud backtest <project> --push --parameter name value`: pushes current code and runs a cloud backtest with parameters.
- `lean project-create --language python <name>`: generates valid local project metadata and starter files when needed.
