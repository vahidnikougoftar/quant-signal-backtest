"""Entry point for the quant signal backtest project."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import CONFIG, OUTPUT_DIR
from src.backtest import run_backtest
from src.data_loader import build_research_frame, download_price_data
from src.metrics import compute_performance_metrics
from src.plots import plot_drawdown, plot_equity_curve, plot_zscore_and_positions
from src.signals import compute_spread_and_zscore, generate_positions


def ensure_output_directory(output_dir: Path) -> None:
    """Create the output directory when it does not already exist."""

    output_dir.mkdir(parents=True, exist_ok=True)


def save_outputs(results: pd.DataFrame, metrics: pd.DataFrame, output_dir: Path) -> None:
    """Persist tabular artifacts from the pipeline to CSV files."""

    results.to_csv(output_dir / "backtest_results.csv", index=True)
    metrics.to_csv(output_dir / "performance_metrics.csv", index=False)


def main() -> None:
    """Execute the end-to-end research pipeline from data ingestion to reporting."""

    ensure_output_directory(OUTPUT_DIR)

    raw_prices = download_price_data(
        tickers=[CONFIG.ticker_a, CONFIG.ticker_b],
        start_date=CONFIG.start_date,
        end_date=CONFIG.end_date,
        price_field=CONFIG.price_field,
    )

    research_frame = build_research_frame(
        prices=raw_prices,
        ticker_a=CONFIG.ticker_a,
        ticker_b=CONFIG.ticker_b,
        minimum_history=max(CONFIG.signal_window, CONFIG.hedge_window),
    )

    signal_frame = compute_spread_and_zscore(
        prices=research_frame,
        ticker_a=CONFIG.ticker_a,
        ticker_b=CONFIG.ticker_b,
        signal_window=CONFIG.signal_window,
        hedge_window=CONFIG.hedge_window,
        min_spread_vol=CONFIG.min_spread_vol,
    )

    signal_frame["position"] = generate_positions(
        zscore=signal_frame["zscore"],
        entry_threshold=CONFIG.entry_zscore,
        exit_threshold=CONFIG.exit_zscore,
    )

    backtest_results = run_backtest(
        signal_frame=signal_frame,
        transaction_cost_bps=CONFIG.transaction_cost_bps,
        short_borrow_cost_bps=CONFIG.short_borrow_cost_bps,
        annualization_factor=CONFIG.annualization_factor,
    )

    metrics = compute_performance_metrics(
        strategy_returns=backtest_results["strategy_return_net"],
        turnover=backtest_results["turnover"],
        positions=backtest_results["position_lagged"],
        annualization_factor=CONFIG.annualization_factor,
    )

    save_outputs(backtest_results, metrics, OUTPUT_DIR)

    plot_equity_curve(backtest_results, OUTPUT_DIR / "equity_curve.png")
    plot_drawdown(backtest_results, OUTPUT_DIR / "drawdown.png")
    plot_zscore_and_positions(backtest_results, OUTPUT_DIR / "zscore_positions.png")

    print("\nPerformance Metrics")
    print(metrics.to_string(index=False))
    print(f"\nArtifacts saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
