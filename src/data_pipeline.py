"""
Data Pipeline Module
====================
Handles fetching, cleaning, and storing market data.
"""

import yfinance as yf
import pandas as pd
import os
import yaml
from datetime import datetime
from loguru import logger

# Setup logging
logger.add("logs/data_pipeline.log", rotation="1 MB")


class DataPipeline:
    """
    Fetches and manages market data from Yahoo Finance.
    """

    def __init__(self, config_path="config.yaml"):
        """Initialize with configuration."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.symbols = self.config["data"]["symbols"]
        self.start_date = self.config["data"]["start_date"]
        self.end_date = self.config["data"]["end_date"]
        self.interval = self.config["data"]["interval"]
        self.raw_path = self.config["data"]["raw_data_path"]
        self.processed_path = self.config["data"]["processed_data_path"]

        # Create directories if they don't exist
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.processed_path, exist_ok=True)

        logger.info("DataPipeline initialized")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Date Range: {self.start_date} to {self.end_date}")

    def fetch_single_stock(self, symbol: str) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single stock.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Fetching data for {symbol}...")

            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=self.start_date,
                end=self.end_date,
                interval=self.interval
            )

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

            # Clean column names
            df.columns = [col.lower().replace(" ", "_") for col in df.columns]

            # Keep only OHLCV columns
            required_cols = ["open", "high", "low", "close", "volume"]
            df = df[required_cols]

            # Add metadata
            df["symbol"] = symbol
            df.index.name = "date"

            logger.info(f"✅ {symbol}: {len(df)} rows fetched")
            return df

        except Exception as e:
            logger.error(f"❌ Error fetching {symbol}: {e}")
            return pd.DataFrame()

    def fetch_all_stocks(self) -> dict:
        """
        Fetch data for all symbols in config.
        
        Returns:
            Dictionary of {symbol: DataFrame}
        """
        all_data = {}

        logger.info(f"Fetching data for {len(self.symbols)} symbols...")

        for symbol in self.symbols:
            df = self.fetch_single_stock(symbol)
            if not df.empty:
                all_data[symbol] = df

        logger.info(f"✅ Successfully fetched {len(all_data)}/{len(self.symbols)} symbols")
        return all_data

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate the data.
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df

        # Make a copy
        df = df.copy()

        # Remove duplicates
        df = df[~df.index.duplicated(keep="first")]

        # Sort by date
        df = df.sort_index()

        # Handle missing values
        missing_before = df.isnull().sum().sum()

        if missing_before > 0:
            # Forward fill then backward fill
            df = df.fillna(method="ffill").fillna(method="bfill")
            logger.info(f"Filled {missing_before} missing values")

        # Remove rows where price is 0 or negative
        df = df[(df["close"] > 0) & (df["volume"] >= 0)]

        # Validate OHLC relationship
        # High should be >= Open, Close, Low
        # Low should be <= Open, Close, High
        invalid_rows = df[
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) |
            (df["high"] < df["close"]) |
            (df["low"] > df["open"]) |
            (df["low"] > df["close"])
        ]

        if len(invalid_rows) > 0:
            logger.warning(f"Found {len(invalid_rows)} invalid OHLC rows — removing")
            df = df.drop(invalid_rows.index)

        logger.info(f"✅ Data cleaned: {len(df)} valid rows")
        return df

    def add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add basic calculated features to the data.
        
        Args:
            df: Cleaned OHLCV DataFrame
            
        Returns:
            DataFrame with additional features
        """
        if df.empty:
            return df

        df = df.copy()

        # Daily returns (percentage)
        df["daily_return"] = df["close"].pct_change()

        # Log returns (better for statistical analysis)
        import numpy as np
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))

        # Cumulative return
        df["cumulative_return"] = (1 + df["daily_return"]).cumprod() - 1

        # Price change
        df["price_change"] = df["close"] - df["close"].shift(1)

        # High-Low range
        df["hl_range"] = df["high"] - df["low"]

        # Average price
        df["avg_price"] = (df["high"] + df["low"] + df["close"]) / 3

        # Volume change
        df["volume_change"] = df["volume"].pct_change()

        # Rolling statistics
        df["rolling_mean_20"] = df["close"].rolling(window=20).mean()
        df["rolling_std_20"] = df["close"].rolling(window=20).std()
        df["rolling_volume_20"] = df["volume"].rolling(window=20).mean()

        logger.info("✅ Basic features added")
        return df

    def save_data(self, data: dict, data_type: str = "raw") -> None:
        """
        Save data to CSV files.
        
        Args:
            data: Dictionary of {symbol: DataFrame}
            data_type: 'raw' or 'processed'
        """
        path = self.raw_path if data_type == "raw" else self.processed_path

        for symbol, df in data.items():
            filepath = os.path.join(path, f"{symbol}.csv")
            df.to_csv(filepath)
            logger.info(f"💾 Saved {symbol} to {filepath}")

        logger.info(f"✅ All data saved to {path}")

    def load_data(self, symbol: str, data_type: str = "processed") -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Args:
            symbol: Stock ticker
            data_type: 'raw' or 'processed'
            
        Returns:
            DataFrame
        """
        path = self.raw_path if data_type == "raw" else self.processed_path
        filepath = os.path.join(path, f"{symbol}.csv")

        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()

        df = pd.read_csv(filepath, index_col="date", parse_dates=True)
        logger.info(f"📂 Loaded {symbol}: {len(df)} rows")
        return df

    def run_pipeline(self) -> dict:
        """
        Run the complete data pipeline.
        
        Returns:
            Dictionary of processed DataFrames
        """
        logger.info("=" * 50)
        logger.info("🚀 Starting Data Pipeline")
        logger.info("=" * 50)

        # Step 1: Fetch data
        raw_data = self.fetch_all_stocks()

        # Step 2: Save raw data
        self.save_data(raw_data, data_type="raw")

        # Step 3: Clean and process
        processed_data = {}
        for symbol, df in raw_data.items():
            cleaned = self.clean_data(df)
            featured = self.add_basic_features(cleaned)
            processed_data[symbol] = featured

        # Step 4: Save processed data
        self.save_data(processed_data, data_type="processed")

        logger.info("=" * 50)
        logger.info("✅ Data Pipeline Complete!")
        logger.info("=" * 50)

        return processed_data

    def get_summary(self, data: dict) -> pd.DataFrame:
        """
        Get summary statistics for all stocks.
        
        Args:
            data: Dictionary of DataFrames
            
        Returns:
            Summary DataFrame
        """
        summaries = []

        for symbol, df in data.items():
            summary = {
                "symbol": symbol,
                "start_date": df.index.min(),
                "end_date": df.index.max(),
                "total_days": len(df),
                "start_price": df["close"].iloc[0],
                "end_price": df["close"].iloc[-1],
                "total_return": f"{((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%",
                "avg_daily_return": f"{df['daily_return'].mean() * 100:.4f}%",
                "volatility": f"{df['daily_return'].std() * 100:.4f}%",
                "max_price": df["high"].max(),
                "min_price": df["low"].min(),
                "avg_volume": f"{df['volume'].mean():,.0f}",
            }
            summaries.append(summary)

        return pd.DataFrame(summaries)