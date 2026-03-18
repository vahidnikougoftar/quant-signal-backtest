# quant-signal-backtest

A lightweight quantitative research repo for a market-neutral mean-reversion idea. The project downloads a pair of equities, estimates a rolling hedge ratio, standardizes the residual spread into a z-score, simulates delayed execution with trading and borrow frictions, and writes research artifacts to `output/`.

The code is intentionally simple enough to review quickly, but it now follows assumptions and diagnostics that are closer to what a research interviewer or junior quant reviewer would expect than a toy "signal times spread return" notebook.

## What The Pipeline Does

1. Downloads daily adjusted prices for two equities with `yfinance`.
2. Aligns the pair on common timestamps and removes incomplete rows.
3. Estimates a rolling hedge ratio from recent log-price co-movement.
4. Builds a residual spread and converts it to a rolling z-score.
5. Generates stateful entry and exit signals.
6. Runs a backtest with one-bar execution lag, normalized pair weights, turnover costs, and short borrow costs.
7. Exports metrics, backtest data, and charts for review.

## Why This Looks More Like Real Research

- The hedge ratio is estimated from recent history instead of being hard-coded to `1.0`.
- The spread is traded through normalized long/short weights, not by pretending the raw spread is directly investable.
- Trading costs scale with actual portfolio turnover across both legs.
- Short exposure incurs a daily borrow charge.
- The metrics now include volatility, Sortino, Calmar, activity rate, and trade count in addition to return, Sharpe, and drawdown.
- Configuration is validated up front so bad parameter choices fail fast.

## Repository Layout

```text
quant-signal-backtest/
├── README.md
├── config.py
├── main.py
├── requirements.txt
├── sql/
│   └── example_queries.sql
├── output/
│   ├── backtest_results.csv
│   ├── performance_metrics.csv
│   ├── equity_curve.png
│   ├── drawdown.png
│   └── zscore_positions.png
└── src/
    ├── backtest.py
    ├── data_loader.py
    ├── metrics.py
    ├── plots.py
    └── signals.py
```

## Configuration

Research parameters live in `config.py`:

- `ticker_a`, `ticker_b`: assets in the pair
- `signal_window`: rolling window for z-score normalization
- `hedge_window`: rolling window for hedge-ratio estimation
- `entry_zscore`, `exit_zscore`: trading thresholds
- `transaction_cost_bps`: linear trading cost applied to turnover
- `short_borrow_cost_bps`: annualized borrow cost applied to short exposure
- `min_spread_vol`: floor for spread volatility to avoid unstable z-scores

The default example uses `NVDA` and `AMD`, which is reasonable for a relative-value demo because both names are exposed to similar semiconductor and AI-cycle drivers.

## Running The Project

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Generated artifacts are written to `output/`.

## Backtest Assumptions

### Signal Timing

Signals observed on day `t` are traded on day `t+1`. This prevents the common lookahead mistake of letting same-day returns benefit from same-day close information.

### Hedge Ratio

The hedge ratio is estimated with a rolling covariance/variance calculation on log prices:

```text
beta_t = Cov(log(price_a), log(price_b)) / Var(log(price_b))
```

This is still a simplified estimator. In a more serious research setting, you would likely compare it with rolling OLS, robust regression, or cointegration-aware specifications.

### Portfolio Construction

When the strategy is active, the pair is converted into normalized weights:

```text
weight_a = position / (1 + abs(beta))
weight_b = -position * beta / (1 + abs(beta))
```

That keeps gross exposure close to one unit of capital and makes turnover and cost calculations more interpretable.

### Frictions

Net returns subtract:

- transaction costs proportional to daily turnover
- borrow costs proportional to short exposure

This is still not a full execution model. There is no explicit slippage curve, no borrow availability filter, and no open/close auction modeling.

## Outputs

- `output/backtest_results.csv`: row-level backtest frame with returns, z-score, weights, turnover, and equity curve
- `output/performance_metrics.csv`: summary statistics for quick review
- `output/equity_curve.png`: cumulative net performance
- `output/drawdown.png`: peak-to-trough drawdown series
- `output/zscore_positions.png`: signal and position diagnostic

## Limitations

- Daily Yahoo data is fine for a demo but not institutional-grade.
- The strategy uses only one pair and one signal family.
- Borrow cost is static and does not vary by name or time.
- The hedge ratio estimator is simple and not robust to structural breaks.
- No statistical significance testing or parameter sweep is included.

These are reasonable next steps if the repo needs to support deeper research discussion.
