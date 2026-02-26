"""
Algorithmic Trading Engine
==========================
Main entry point for the application.

Author: Your Name
Version: 4.0.0 — Phase 4 (Risk Management)
"""

from src.data_pipeline import DataPipeline
from src.indicators import TechnicalIndicators
from src.strategy import TradingStrategy
from src.backtester import Backtester
from src.performance import PerformanceAnalyzer
from src.risk_manager import RiskManager
from src.portfolio_manager import PortfolioManager
from src.visualizer import Visualizer
from src.utils import ensure_directories
from loguru import logger
import sys

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("logs/main.log", rotation="5 MB", level="DEBUG")


def main():
    """Main function — runs the complete trading engine."""

    logger.info("=" * 60)
    logger.info("🚀 ALGORITHMIC TRADING ENGINE v4.0.0")
    logger.info("=" * 60)

    ensure_directories()

    # ==========================================
    # PHASE 1: Data Pipeline
    # ==========================================
    logger.info("\n📊 PHASE 1: Data Pipeline")
    pipeline = DataPipeline()
    data = pipeline.run_pipeline()

    summary = pipeline.get_summary(data)
    print("\n📋 DATA SUMMARY:")
    print(summary.to_string(index=False))
    print()

    # ==========================================
    # PHASE 2: Technical Indicators & Strategy
    # ==========================================
    logger.info("\n📈 PHASE 2: Technical Indicators & Strategy")

    indicators = TechnicalIndicators()
    strategy = TradingStrategy()

    processed_data = {}
    for symbol, df in data.items():
        logger.info(f"Processing {symbol}...")
        df = indicators.add_all_indicators(df)
        df = strategy.apply_all_strategies(df)
        processed_data[symbol] = df

    # ==========================================
    # PHASE 3: Basic Backtesting
    # ==========================================
    logger.info("\n🏃 PHASE 3: Basic Backtesting (Single Stock)")

    backtester = Backtester()
    performance = PerformanceAnalyzer()
    visualizer = Visualizer()

    first_symbol = list(processed_data.keys())[0]
    first_df = processed_data[first_symbol]

    # Run basic backtest on first stock for comparison
    basic_results = backtester.run_multiple_strategies(
        first_df, first_symbol,
        ["sma_signal", "rsi_signal", "macd_trade_signal",
         "bb_signal", "combined_signal"]
    )

    # Performance metrics
    basic_metrics = {}
    for strat_name, results in basic_results.items():
        metrics = performance.calculate_all_metrics(
            results["portfolio_history"],
            results["trades"],
            results["initial_capital"]
        )
        basic_metrics[strat_name] = metrics

    # Print comparison
    if basic_metrics:
        comparison = performance.generate_comparison_report(basic_metrics)
        print(comparison)

    # ==========================================
    # PHASE 4: Advanced Risk Management
    # ==========================================
    logger.info("\n🛡️ PHASE 4: Advanced Risk Management")

    risk_manager = RiskManager()

    # 4A: Risk Report
    logger.info("\n📋 Generating Risk Report...")
    first_results = list(basic_results.values())[0] if basic_results else None
    portfolio_value = first_results["final_value"] if first_results else 100000

    risk_report = risk_manager.generate_risk_report(processed_data, portfolio_value)
    print(risk_report)

    # 4B: Position Sizing Demo
    logger.info("\n📏 Position Sizing Recommendations:")
    for symbol, df in list(processed_data.items())[:3]:  # First 3 stocks
        latest = df.iloc[-1]
        price = latest["close"]
        atr = latest.get("atr_14", price * 0.02)

        # Calculate win rate from basic backtest
        win_rate = 0.5
        avg_win = 1000
        avg_loss = -500
        if symbol == first_symbol and basic_metrics:
            best_strat = list(basic_metrics.values())[0]
            win_rate = best_strat.get("win_rate", 0.5)
            avg_win = best_strat.get("avg_win", 1000)
            avg_loss = best_strat.get("avg_loss", -500)

        recommendations = risk_manager.recommend_position_size(
            capital=100000,
            entry_price=price,
            atr=atr,
            win_rate=max(win_rate, 0.1),
            avg_win=max(avg_win, 1),
            avg_loss=min(avg_loss, -1)
        )

        print(f"\n📊 {symbol} (Price: ${price:.2f}, ATR: ${atr:.2f})")
        print(f"   Fixed Fractional:  {recommendations['fixed_fractional']['shares']} shares "
              f"(${recommendations['fixed_fractional']['value']:,.0f} = "
              f"{recommendations['fixed_fractional']['pct_of_capital']:.1f}%)")
        print(f"   Kelly Criterion:   {recommendations['kelly_criterion']['shares']} shares "
              f"(${recommendations['kelly_criterion']['value']:,.0f} = "
              f"{recommendations['kelly_criterion']['pct_of_capital']:.1f}%)")
        print(f"   Volatility-Based:  {recommendations['volatility_based']['shares']} shares "
              f"(${recommendations['volatility_based']['value']:,.0f} = "
              f"{recommendations['volatility_based']['pct_of_capital']:.1f}%)")
        print(f"   ➡️  Conservative:   {recommendations['recommended_conservative']} shares")
        print(f"   ➡️  Moderate:       {recommendations['recommended_moderate']} shares")

    # 4C: Portfolio Backtest (Multi-Stock with Risk Management)
    logger.info("\n\n🏃 Running PORTFOLIO Backtest (Multi-Stock with Risk Management)...")
    portfolio_mgr = PortfolioManager()

    portfolio_results = portfolio_mgr.run_portfolio_backtest(
        processed_data, signal_column="combined_signal"
    )

    # Portfolio performance metrics
    if portfolio_results["portfolio_history"] is not None and not portfolio_results["portfolio_history"].empty:
        portfolio_metrics = performance.calculate_all_metrics(
            portfolio_results["portfolio_history"],
            portfolio_results["trades"],
            portfolio_results["initial_capital"]
        )

        portfolio_report = performance.generate_report(
            portfolio_metrics, "PORTFOLIO", "combined_signal + Risk Mgmt"
        )
        print(portfolio_report)

    # ==========================================
    # VISUALIZATION
    # ==========================================
    logger.info("\n📊 Generating Charts...")

    # Chart 1: Price with signals
    visualizer.plot_price_with_signals(
        first_df, first_symbol, signal_column="combined_signal"
    )

    # Chart 2: Basic backtest results
    if "combined_signal" in basic_results:
        visualizer.plot_backtest_results(
            basic_results["combined_signal"]["portfolio_history"],
            basic_results["combined_signal"]["trades"],
            first_symbol, "combined_signal",
            basic_results["combined_signal"]["initial_capital"]
        )

    # Chart 3: Strategy comparison
    visualizer.plot_equity_comparison(basic_results, first_symbol)

    # Chart 4: Portfolio backtest
    if portfolio_results["portfolio_history"] is not None and not portfolio_results["portfolio_history"].empty:
        visualizer.plot_backtest_results(
            portfolio_results["portfolio_history"],
            portfolio_results["trades"],
            "PORTFOLIO", "combined + risk_mgmt",
            portfolio_results["initial_capital"]
        )

    # ==========================================
    # SAVE
    # ==========================================
    logger.info("\n💾 Saving all data...")
    pipeline.save_data(processed_data, data_type="processed")

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL PHASES (1-4) COMPLETE!")
    logger.info("=" * 60)
    logger.info("📁 Charts saved in: docs/charts/")
    logger.info("📁 Data saved in: data/processed/")
    logger.info("🔜 Next: Phase 5 — Machine Learning Integration")


if __name__ == "__main__":
    main()