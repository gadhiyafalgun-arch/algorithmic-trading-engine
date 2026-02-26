"""
Algorithmic Trading Engine
==========================
Main entry point for the application.

Author: Your Name
Version: 1.0.0
"""

from src.data_pipeline import DataPipeline
from src.utils import ensure_directories
from loguru import logger
import sys

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("logs/main.log", rotation="5 MB", level="DEBUG")


def main():
    """Main function — runs the trading engine."""
    
    logger.info("=" * 60)
    logger.info("🚀 ALGORITHMIC TRADING ENGINE v1.0.0")
    logger.info("=" * 60)

    # Step 0: Ensure all directories exist
    ensure_directories()

    # Step 1: Run Data Pipeline
    logger.info("\n📊 STEP 1: Data Pipeline")
    pipeline = DataPipeline()
    data = pipeline.run_pipeline()

    # Step 2: Show Summary
    logger.info("\n📋 DATA SUMMARY:")
    summary = pipeline.get_summary(data)
    print("\n")
    print(summary.to_string(index=False))
    print("\n")

    # Step 3: Show sample data
    for symbol in list(data.keys())[:1]:  # Show first stock
        logger.info(f"\n📈 Sample Data for {symbol}:")
        print(data[symbol].tail(5))
        print("\n")

    logger.info("✅ Phase 1 Complete — Data Pipeline is working!")
    logger.info("Next: Phase 2 — Technical Indicators & Strategies")


if __name__ == "__main__":
    main()