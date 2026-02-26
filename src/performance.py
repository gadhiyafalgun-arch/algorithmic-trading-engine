"""
Performance Metrics Module
===========================
Calculates all important performance metrics for backtesting results.

Metrics included:
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Win Rate
- Profit Factor
- Value at Risk (VaR)
- And more...
"""

import pandas as pd
import numpy as np
from loguru import logger


class PerformanceAnalyzer:
    """
    Calculates performance metrics from backtest results.
    
    These metrics are what RECRUITERS look for!
    """

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Args:
            risk_free_rate: Annual risk-free rate (default 5% — current US Treasury)
        """
        self.risk_free_rate = risk_free_rate
        self.daily_rf = (1 + risk_free_rate) ** (1/252) - 1  # Convert to daily
        logger.info("PerformanceAnalyzer initialized")

    def calculate_all_metrics(self, portfolio_df: pd.DataFrame,
                               trades_df: pd.DataFrame,
                               initial_capital: float) -> dict:
        """
        Calculate ALL performance metrics.
        
        Args:
            portfolio_df: DataFrame with daily portfolio values
            trades_df: DataFrame with trade history
            initial_capital: Starting capital
            
        Returns:
            Dictionary with all metrics
        """
        metrics = {}

        # --- Return Metrics ---
        metrics["initial_capital"] = initial_capital
        metrics["final_value"] = portfolio_df["total_value"].iloc[-1]
        metrics["total_return"] = (metrics["final_value"] - initial_capital) / initial_capital
        metrics["total_return_pct"] = metrics["total_return"] * 100

        # Annualized return
        num_days = len(portfolio_df)
        num_years = num_days / 252  # Trading days per year
        if num_years > 0:
            metrics["annualized_return"] = (
                (metrics["final_value"] / initial_capital) ** (1 / num_years) - 1
            )
        else:
            metrics["annualized_return"] = 0

        # --- Risk Metrics ---
        daily_returns = portfolio_df["daily_return"].dropna()

        metrics["volatility_daily"] = daily_returns.std()
        metrics["volatility_annual"] = daily_returns.std() * np.sqrt(252)

        # --- Sharpe Ratio ---
        # (Return - Risk Free Rate) / Volatility
        excess_returns = daily_returns - self.daily_rf
        if metrics["volatility_daily"] > 0:
            metrics["sharpe_ratio"] = (
                excess_returns.mean() / daily_returns.std() * np.sqrt(252)
            )
        else:
            metrics["sharpe_ratio"] = 0

        # --- Sortino Ratio ---
        # Like Sharpe but only uses DOWNSIDE deviation
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0

        if downside_std > 0:
            metrics["sortino_ratio"] = (
                excess_returns.mean() / downside_std * np.sqrt(252)
            )
        else:
            metrics["sortino_ratio"] = 0

        # --- Maximum Drawdown ---
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        metrics["max_drawdown"] = drawdown.min()
        metrics["max_drawdown_pct"] = metrics["max_drawdown"] * 100

        # Max drawdown date
        if len(drawdown) > 0:
            metrics["max_drawdown_date"] = drawdown.idxmin()
        else:
            metrics["max_drawdown_date"] = None

        # --- Calmar Ratio ---
        # Annualized Return / Max Drawdown
        if abs(metrics["max_drawdown"]) > 0:
            metrics["calmar_ratio"] = metrics["annualized_return"] / abs(metrics["max_drawdown"])
        else:
            metrics["calmar_ratio"] = 0

        # --- Value at Risk (VaR) ---
        # 95% VaR — worst expected daily loss 95% of the time
        metrics["var_95"] = np.percentile(daily_returns, 5) if len(daily_returns) > 0 else 0
        metrics["var_99"] = np.percentile(daily_returns, 1) if len(daily_returns) > 0 else 0

        # --- Trade Metrics ---
        if not trades_df.empty:
            metrics["total_trades"] = len(trades_df)
            
            winning = trades_df[trades_df["pnl"] > 0]
            losing = trades_df[trades_df["pnl"] <= 0]

            metrics["winning_trades"] = len(winning)
            metrics["losing_trades"] = len(losing)
            metrics["win_rate"] = len(winning) / len(trades_df) if len(trades_df) > 0 else 0

            metrics["avg_win"] = winning["pnl"].mean() if len(winning) > 0 else 0
            metrics["avg_loss"] = losing["pnl"].mean() if len(losing) > 0 else 0

            # Profit Factor = Gross Profit / Gross Loss
            gross_profit = winning["pnl"].sum() if len(winning) > 0 else 0
            gross_loss = abs(losing["pnl"].sum()) if len(losing) > 0 else 0
            metrics["profit_factor"] = gross_profit / gross_loss if gross_loss > 0 else float("inf")

            # Average trade
            metrics["avg_trade_pnl"] = trades_df["pnl"].mean()
            metrics["avg_trade_return"] = trades_df["pnl_percent"].mean()

            # Best and worst trades
            metrics["best_trade"] = trades_df["pnl"].max()
            metrics["worst_trade"] = trades_df["pnl"].min()

            # Average holding period
            if "entry_date" in trades_df.columns and "exit_date" in trades_df.columns:
                trades_df_copy = trades_df.copy()
                trades_df_copy["holding_days"] = (
                    pd.to_datetime(trades_df_copy["exit_date"]) - 
                    pd.to_datetime(trades_df_copy["entry_date"])
                ).dt.days
                metrics["avg_holding_days"] = trades_df_copy["holding_days"].mean()
            else:
                metrics["avg_holding_days"] = 0

            # Total commissions paid
            metrics["total_commissions"] = trades_df["commission"].sum()

            # Expectancy
            # Expected $ per trade
            metrics["expectancy"] = (
                (metrics["win_rate"] * metrics["avg_win"]) + 
                ((1 - metrics["win_rate"]) * metrics["avg_loss"])
            )

        else:
            metrics["total_trades"] = 0
            metrics["winning_trades"] = 0
            metrics["losing_trades"] = 0
            metrics["win_rate"] = 0
            metrics["profit_factor"] = 0
            metrics["expectancy"] = 0

        # --- Additional Stats ---
        metrics["positive_days"] = (daily_returns > 0).sum()
        metrics["negative_days"] = (daily_returns < 0).sum()
        metrics["best_day"] = daily_returns.max()
        metrics["worst_day"] = daily_returns.min()
        metrics["avg_daily_return"] = daily_returns.mean()

        logger.info("✅ All performance metrics calculated")
        return metrics

    def generate_report(self, metrics: dict, symbol: str = "",
                        strategy: str = "") -> str:
        """
        Generate a beautiful text report of performance metrics.
        
        Args:
            metrics: Dictionary from calculate_all_metrics()
            symbol: Stock ticker
            strategy: Strategy name
            
        Returns:
            Formatted string report
        """
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║            📊 BACKTEST PERFORMANCE REPORT                   ║
║            Symbol: {symbol:<20}                       ║
║            Strategy: {strategy:<20}                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  💰 RETURNS                                                  ║
║  ─────────────────────────────────                           ║
║  Initial Capital:     ${metrics['initial_capital']:>12,.2f}                  ║
║  Final Value:         ${metrics['final_value']:>12,.2f}                  ║
║  Total Return:         {metrics['total_return_pct']:>11.2f}%                  ║
║  Annualized Return:    {metrics['annualized_return']*100:>11.2f}%                  ║
║                                                              ║
║  📈 RISK METRICS                                             ║
║  ─────────────────────────────────                           ║
║  Sharpe Ratio:         {metrics['sharpe_ratio']:>11.3f}                    ║
║  Sortino Ratio:        {metrics['sortino_ratio']:>11.3f}                    ║
║  Max Drawdown:         {metrics['max_drawdown_pct']:>11.2f}%                  ║
║  Calmar Ratio:         {metrics['calmar_ratio']:>11.3f}                    ║
║  Annual Volatility:    {metrics['volatility_annual']*100:>11.2f}%                  ║
║  VaR (95%):            {metrics['var_95']*100:>11.3f}%                  ║
║  VaR (99%):            {metrics['var_99']*100:>11.3f}%                  ║
║                                                              ║
║  🎯 TRADE STATISTICS                                         ║
║  ─────────────────────────────────                           ║
║  Total Trades:         {metrics['total_trades']:>11}                    ║
║  Winning Trades:       {metrics['winning_trades']:>11}                    ║
║  Losing Trades:        {metrics['losing_trades']:>11}                    ║
║  Win Rate:             {metrics['win_rate']*100:>11.1f}%                  ║
║  Profit Factor:        {metrics['profit_factor']:>11.2f}                    ║
║  Expectancy:          ${metrics['expectancy']:>11.2f}                    ║
║                                                              ║
║  💵 TRADE DETAILS                                            ║
║  ─────────────────────────────────                           ║
║  Avg Win:             ${metrics.get('avg_win', 0):>11.2f}                    ║
║  Avg Loss:            ${metrics.get('avg_loss', 0):>11.2f}                    ║
║  Best Trade:          ${metrics.get('best_trade', 0):>11.2f}                    ║
║  Worst Trade:         ${metrics.get('worst_trade', 0):>11.2f}                    ║
║  Total Commissions:   ${metrics.get('total_commissions', 0):>11.2f}                    ║
║  Avg Holding (days):   {metrics.get('avg_holding_days', 0):>11.1f}                    ║
║                                                              ║
║  📅 DAILY STATS                                              ║
║  ─────────────────────────────────                           ║
║  Positive Days:        {metrics['positive_days']:>11}                    ║
║  Negative Days:        {metrics['negative_days']:>11}                    ║
║  Best Day:             {metrics['best_day']*100:>11.3f}%                  ║
║  Worst Day:            {metrics['worst_day']*100:>11.3f}%                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

        # Grade the strategy
        grade = self._grade_strategy(metrics)
        report += f"\n🏆 STRATEGY GRADE: {grade}\n"

        return report

    def _grade_strategy(self, metrics: dict) -> str:
        """
        Grade the strategy based on key metrics.
        
        Returns:
            Grade string (A+, A, B, C, D, F)
        """
        score = 0

        # Sharpe Ratio scoring
        sharpe = metrics["sharpe_ratio"]
        if sharpe > 2.0:
            score += 30
        elif sharpe > 1.5:
            score += 25
        elif sharpe > 1.0:
            score += 20
        elif sharpe > 0.5:
            score += 10
        elif sharpe > 0:
            score += 5

        # Win Rate scoring
        win_rate = metrics["win_rate"]
        if win_rate > 0.6:
            score += 20
        elif win_rate > 0.5:
            score += 15
        elif win_rate > 0.4:
            score += 10
        elif win_rate > 0.3:
            score += 5

        # Profit Factor scoring
        pf = metrics["profit_factor"]
        if pf > 2.0:
            score += 20
        elif pf > 1.5:
            score += 15
        elif pf > 1.0:
            score += 10
        elif pf > 0.5:
            score += 5

        # Max Drawdown scoring (less is better)
        mdd = abs(metrics["max_drawdown"])
        if mdd < 0.05:
            score += 15
        elif mdd < 0.10:
            score += 12
        elif mdd < 0.15:
            score += 8
        elif mdd < 0.20:
            score += 5

        # Total Return scoring
        ret = metrics["total_return"]
        if ret > 0.5:
            score += 15
        elif ret > 0.2:
            score += 12
        elif ret > 0.1:
            score += 8
        elif ret > 0:
            score += 5

        # Grade assignment
        if score >= 85:
            return "A+ 🌟 (Excellent — Hedge Fund Material!)"
        elif score >= 70:
            return "A  ⭐ (Very Good — Strong Strategy)"
        elif score >= 55:
            return "B  👍 (Good — Has Potential)"
        elif score >= 40:
            return "C  😐 (Average — Needs Improvement)"
        elif score >= 25:
            return "D  👎 (Below Average — Major Issues)"
        else:
            return "F  ❌ (Poor — Back to Drawing Board)"

    def generate_comparison_report(self, all_metrics: dict) -> str:
        """
        Compare multiple strategies side by side.
        
        Args:
            all_metrics: Dict of {strategy_name: metrics_dict}
        """
        report = "\n📊 STRATEGY COMPARISON\n"
        report += "=" * 80 + "\n"
        report += f"{'Strategy':<25} {'Return':>10} {'Sharpe':>10} {'Win Rate':>10} {'MaxDD':>10} {'Trades':>8}\n"
        report += "-" * 80 + "\n"

        for name, metrics in all_metrics.items():
            report += (
                f"{name:<25} "
                f"{metrics['total_return_pct']:>9.2f}% "
                f"{metrics['sharpe_ratio']:>10.3f} "
                f"{metrics['win_rate']*100:>9.1f}% "
                f"{metrics['max_drawdown_pct']:>9.2f}% "
                f"{metrics['total_trades']:>8}\n"
            )

        report += "=" * 80 + "\n"

        # Find best strategy
        best = max(all_metrics.items(), key=lambda x: x[1]["sharpe_ratio"])
        report += f"\n🏆 BEST STRATEGY (by Sharpe): {best[0]}\n"

        return report