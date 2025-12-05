"""
Yahoo Finance client for fetching stock market time series data.
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd


def get_timeseries(
    symbol: str,
    interval: str = "daily",
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get time series data for a stock symbol using Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol (e.g., "MRNA", "BNTX")
        interval: Data interval - "daily", "weekly", or "monthly"
        period: Time period - "1m", "3m", "6m", "1y", "5y" (optional if start_date provided)
        start_date: Start date in YYYY-MM-DD format (optional, overrides period)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
    
    Returns:
        Dictionary with time series data including OHLCV
    """
    try:
        # Map interval to yfinance format
        interval_map = {
            "daily": "1d",
            "weekly": "1wk",
            "monthly": "1mo"
        }
        yf_interval = interval_map.get(interval, "1d")
        
        # Convert period to yfinance format if provided
        period_map = {
            "1m": "1mo",
            "3m": "3mo",
            "6m": "6mo",
            "1y": "1y",
            "5y": "5y"
        }
        
        # Download stock data
        ticker = yf.Ticker(symbol)
        
        # Determine if this is recent data (last 7 days) or historical
        is_recent = False
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
            is_recent = (end_dt - start_dt).days <= 7
        elif period in ["1m"]:
            is_recent = True
        
        # Fetch data based on parameters
        if start_date and end_date:
            # Use date range
            df = ticker.history(start=start_date, end=end_date, interval=yf_interval)
        elif start_date:
            # Start date only, use period or default to 1y
            df = ticker.history(start=start_date, interval=yf_interval)
        elif period:
            # Use period
            yf_period = period_map.get(period, "1y")
            df = ticker.history(period=yf_period, interval=yf_interval)
        else:
            # Default to 1 year
            df = ticker.history(period="1y", interval=yf_interval)
        
        if df.empty:
            return {
                "error": f"No data available for symbol {symbol}",
                "symbol": symbol,
                "count": 0,
                "data": []
            }
        
        # Convert DataFrame to list of dictionaries
        data_points = []
        for date, row in df.iterrows():
            data_point = {
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]) if pd.notna(row["Open"]) else None,
                "high": float(row["High"]) if pd.notna(row["High"]) else None,
                "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
                "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
            }
            
            # Add adjusted close if available
            if "Adj Close" in row and pd.notna(row["Adj Close"]):
                data_point["adj_close"] = float(row["Adj Close"])
            
            data_points.append(data_point)
        
        # Get metadata (handle potential failures gracefully)
        currency = "USD"  # Default
        try:
            info = ticker.info
            if info and isinstance(info, dict):
                currency = info.get("currency", "USD")
        except Exception:
            # If info call fails, use default currency
            pass
        
        # Determine actual date range
        if not data_points:
            actual_start = None
            actual_end = None
        else:
            actual_start = data_points[0]["date"]
            actual_end = data_points[-1]["date"]
        
        result = {
            "symbol": symbol.upper(),
            "interval": interval,
            "period": period or f"custom ({start_date} to {end_date or 'today'})",
            "start_date": actual_start or start_date,
            "end_date": actual_end or end_date or datetime.now().strftime("%Y-%m-%d"),
            "count": len(data_points),
            "data": data_points,
            "metadata": {
                "currency": currency,
                "data_source": "Yahoo Finance",
                "last_updated": datetime.now().isoformat(),
                "is_recent_data": is_recent
            }
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol,
            "count": 0,
            "data": []
        }

