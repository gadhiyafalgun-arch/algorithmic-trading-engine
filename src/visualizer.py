"""
Visualizer Module
==================
Creates charts and visualizations for trading data and signals.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os
from loguru import logger


class Visualizer:
    """
    Creates interactive charts using Plotly.
    Charts are saved as HTML files you can open in browser.
    """

    def __init__(self, output_dir: str = "docs/charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info("Visualizer initialized")

    def plot_price_with_signals(self, df: pd.DataFrame, symbol: str,
                                 signal_column: str = "sma_signal") -> None:
        """
        Plot candlestick chart with BUY/SELL signals.
        """
        buys = df[df[signal_column] == 1]
        sells = df[df[signal_column] == -1]

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(
                f"{symbol} — Price & Signals ({signal_column})",
                "Volume",
                "RSI"
            )
        )

        # Row 1: Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Price",
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350"
            ),
            row=1, col=1
        )

        if "sma_20" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["sma_20"],
                    name="SMA 20",
                    line=dict(color="orange", width=1)
                ),
                row=1, col=1
            )

        if "sma_50" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["sma_50"],
                    name="SMA 50",
                    line=dict(color="blue", width=1)
                ),
                row=1, col=1
            )

        if "bb_upper" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["bb_upper"],
                    name="BB Upper",
                    line=dict(color="gray", width=0.5, dash="dash"),
                    opacity=0.5
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["bb_lower"],
                    name="BB Lower",
                    line=dict(color="gray", width=0.5, dash="dash"),
                    fill="tonexty",
                    fillcolor="rgba(128,128,128,0.1)",
                    opacity=0.5
                ),
                row=1, col=1
            )

        if len(buys) > 0:
            fig.add_trace(
                go.Scatter(
                    x=buys.index,
                    y=buys["close"],
                    mode="markers",
                    name="BUY",
                    marker=dict(
                        symbol="triangle-up",
                        size=12,
                        color="#00e676",
                        line=dict(width=1, color="darkgreen")
                    )
                ),
                row=1, col=1
            )

        if len(sells) > 0:
            fig.add_trace(
                go.Scatter(
                    x=sells.index,
                    y=sells["close"],
                    mode="markers",
                    name="SELL",
                    marker=dict(
                        symbol="triangle-down",
                        size=12,
                        color="#ff1744",
                        line=dict(width=1, color="darkred")
                    )
                ),
                row=1, col=1
            )

        # Row 2: Volume
        colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(df["close"], df["open"])]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        # Row 3: RSI
        if "rsi_14" in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["rsi_14"],
                    name="RSI 14",
                    line=dict(color="purple", width=1)
                ),
                row=3, col=1
            )

            fig.add_hline(y=70, line_dash="dash", line_color="red",
                         opacity=0.5, row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green",
                         opacity=0.5, row=3, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray",
                         opacity=0.3, row=3, col=1)

        fig.update_layout(
            title=f"Algo Trading Engine — {symbol}",
            template="plotly_dark",
            height=900,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        filepath = os.path.join(self.output_dir, f"{symbol}_{signal_column}.html")
        fig.write_html(filepath)
        logger.info(f"Chart saved: {filepath}")
        fig.show()

    def plot_strategy_comparison(self, df: pd.DataFrame, symbol: str) -> None:
        """
        Plot all strategy signals on one chart for comparison.
        """
        signal_cols = [col for col in df.columns
                      if "signal" in col.lower() and df[col].abs().sum() > 0]

        fig = make_subplots(
            rows=len(signal_cols) + 1, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.4] + [0.12] * len(signal_cols),
            subplot_titles=[f"{symbol} Price"] + signal_cols
        )

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["close"],
                name="Close Price",
                line=dict(color="white", width=1)
            ),
            row=1, col=1
        )

        colors = ["#00e676", "#2196f3", "#ff9800", "#e91e63", "#9c27b0"]

        for i, col in enumerate(signal_cols):
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df[col],
                    name=col,
                    marker_color=color,
                    opacity=0.7
                ),
                row=i + 2, col=1
            )

        fig.update_layout(
            title=f"Strategy Comparison — {symbol}",
            template="plotly_dark",
            height=200 + (200 * len(signal_cols)),
            showlegend=True,
            xaxis_rangeslider_visible=False
        )

        filepath = os.path.join(self.output_dir, f"{symbol}_comparison.html")
        fig.write_html(filepath)
        logger.info(f"Comparison chart saved: {filepath}")
        fig.show()

    def plot_macd(self, df: pd.DataFrame, symbol: str) -> None:
        """
        Dedicated MACD chart.
        """
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.4],
            subplot_titles=(f"{symbol} Price", "MACD")
        )

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["close"],
                name="Close",
                line=dict(color="white", width=1)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["macd_line"],
                name="MACD Line",
                line=dict(color="#2196f3", width=1.5)
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["macd_signal"],
                name="Signal Line",
                line=dict(color="#ff9800", width=1.5)
            ),
            row=2, col=1
        )

        colors = ["#26a69a" if v >= 0 else "#ef5350"
                  for v in df["macd_histogram"]]
        fig.add_trace(
            go.Bar(
                x=df.index, y=df["macd_histogram"],
                name="Histogram",
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        fig.update_layout(
            title=f"MACD Analysis — {symbol}",
            template="plotly_dark",
            height=700,
            showlegend=True
        )

        filepath = os.path.join(self.output_dir, f"{symbol}_macd.html")
        fig.write_html(filepath)
        logger.info(f"MACD chart saved: {filepath}")
        fig.show()

    def plot_backtest_results(self, portfolio_df: pd.DataFrame,
                               trades_df: pd.DataFrame,
                               symbol: str, strategy: str,
                               initial_capital: float) -> None:
        """
        Plot comprehensive backtest results.
        """
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(
                f"Portfolio Value — {symbol} ({strategy})",
                "Daily Returns",
                "Drawdown"
            )
        )

        # Row 1: Portfolio Value
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df["total_value"],
                name="Portfolio Value",
                line=dict(color="#00e676", width=2),
                fill="tozeroy",
                fillcolor="rgba(0, 230, 118, 0.1)"
            ),
            row=1, col=1
        )

        fig.add_hline(
            y=initial_capital,
            line_dash="dash",
            line_color="white",
            opacity=0.5,
            annotation_text=f"Initial: ${initial_capital:,.0f}",
            row=1, col=1
        )

        if not trades_df.empty:
            for _, trade in trades_df.iterrows():
                if trade["entry_date"] in portfolio_df.index:
                    fig.add_trace(
                        go.Scatter(
                            x=[trade["entry_date"]],
                            y=[portfolio_df.loc[trade["entry_date"], "total_value"]],
                            mode="markers",
                            marker=dict(symbol="triangle-up", size=8, color="#00e676"),
                            showlegend=False
                        ),
                        row=1, col=1
                    )

        # Row 2: Daily Returns
        colors = ["#26a69a" if r >= 0 else "#ef5350"
                  for r in portfolio_df["daily_return"]]

        fig.add_trace(
            go.Bar(
                x=portfolio_df.index,
                y=portfolio_df["daily_return"] * 100,
                name="Daily Return %",
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )

        # Row 3: Drawdown
        cumulative = (1 + portfolio_df["daily_return"]).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max * 100

        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=drawdown,
                name="Drawdown %",
                line=dict(color="#ef5350", width=1),
                fill="tozeroy",
                fillcolor="rgba(239, 83, 80, 0.2)"
            ),
            row=3, col=1
        )

        fig.update_layout(
            title=f"Backtest Results — {symbol} | {strategy}",
            template="plotly_dark",
            height=900,
            showlegend=True
        )

        fig.update_yaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Return (%)", row=2, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=3, col=1)

        filepath = os.path.join(self.output_dir, f"{symbol}_{strategy}_backtest.html")
        fig.write_html(filepath)
        logger.info(f"Backtest chart saved: {filepath}")
        fig.show()

    def plot_equity_comparison(self, all_results: dict, symbol: str) -> None:
        """
        Compare equity curves of all strategies.
        """
        fig = go.Figure()

        colors = ["#00e676", "#2196f3", "#ff9800", "#e91e63", "#9c27b0",
                  "#00bcd4", "#ffeb3b", "#4caf50"]

        initial_capital = 100000

        for i, (strategy_name, results) in enumerate(all_results.items()):
            portfolio_df = results["portfolio_history"]
            color = colors[i % len(colors)]
            initial_capital = results["initial_capital"]

            fig.add_trace(
                go.Scatter(
                    x=portfolio_df.index,
                    y=portfolio_df["total_value"],
                    name=strategy_name,
                    line=dict(color=color, width=2)
                )
            )

        fig.add_hline(
            y=initial_capital,
            line_dash="dash",
            line_color="white",
            opacity=0.3,
            annotation_text="Initial Capital"
        )

        fig.update_layout(
            title=f"Strategy Equity Comparison — {symbol}",
            template="plotly_dark",
            height=600,
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            showlegend=True
        )

        filepath = os.path.join(self.output_dir, f"{symbol}_equity_comparison.html")
        fig.write_html(filepath)
        logger.info(f"Equity comparison saved: {filepath}")
        fig.show()