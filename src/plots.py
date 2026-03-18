"""Plotting helpers for visual inspection of strategy behavior."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _prepare_output_path(path: Path) -> None:
    """Ensure the target directory for a plot exists before saving."""

    path.parent.mkdir(parents=True, exist_ok=True)


def plot_equity_curve(results: pd.DataFrame, output_path: Path) -> None:
    """Plot and save the strategy equity curve.

    The equity curve is the fastest way to visually inspect whether gains are
    smooth, episodic, or dominated by a small number of observations.
    """

    _prepare_output_path(output_path)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(results.index, results["equity_curve"], label="Equity Curve", linewidth=2.0)
    ax.set_title("Strategy Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_drawdown(results: pd.DataFrame, output_path: Path) -> None:
    """Plot and save the drawdown series.

    Drawdown complements the equity curve by highlighting the depth and
    persistence of losses, which often matters as much as return magnitude in
    professional strategy evaluation.
    """

    _prepare_output_path(output_path)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(results.index, results["drawdown"], 0.0, alpha=0.4, color="tab:red")
    ax.plot(results.index, results["drawdown"], color="tab:red", linewidth=1.5)
    ax.set_title("Strategy Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_zscore_and_positions(results: pd.DataFrame, output_path: Path) -> None:
    """Plot z-score and position overlay for signal diagnostics.

    This chart helps a researcher verify that position changes occur when the
    z-score meaningfully deviates from and then reverts toward its local mean.
    """

    _prepare_output_path(output_path)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.plot(results.index, results["zscore"], color="tab:blue", label="Z-Score", linewidth=1.5)
    ax1.axhline(0.0, color="black", linestyle="--", linewidth=1.0)
    ax1.set_title("Z-Score With Position Overlay")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Z-Score", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.step(
        results.index,
        results["position"],
        where="post",
        color="tab:orange",
        label="Position",
        linewidth=1.2,
    )
    ax2.set_ylabel("Position", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")
    ax2.set_yticks([-1, 0, 1])

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
