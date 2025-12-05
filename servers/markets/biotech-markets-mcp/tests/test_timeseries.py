#!/usr/bin/env python3
"""
Test script for markets.get_timeseries functionality.

Tests the yfinance_client and markets_get_timeseries function with various
parameters including intervals, periods, and caching.
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from yfinance_client import get_timeseries
from server import markets_get_timeseries


def test_basic_timeseries():
    """Test basic timeseries retrieval."""
    print("=" * 60)
    print("Test 1: Basic timeseries retrieval")
    print("=" * 60)
    
    try:
        result = get_timeseries(
            symbol="MRNA",
            interval="daily",
            period="1y"
        )
        
        assert "symbol" in result, "Result should contain 'symbol'"
        assert result["symbol"] == "MRNA", f"Symbol should be MRNA, got {result['symbol']}"
        assert "count" in result, "Result should contain 'count'"
        assert "data" in result, "Result should contain 'data'"
        assert result["count"] > 0, "Should have at least one data point"
        
        # Check data structure
        if result["data"]:
            first_point = result["data"][0]
            required_fields = ["date", "open", "high", "low", "close", "volume"]
            for field in required_fields:
                assert field in first_point, f"Data point should contain '{field}'"
        
        print(f"✅ Test passed!")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Count: {result['count']}")
        print(f"   Interval: {result.get('interval', 'N/A')}")
        if result["data"]:
            print(f"   First date: {result['data'][0]['date']}")
            print(f"   Last date: {result['data'][-1]['date']}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intervals():
    """Test different intervals."""
    print("\n" + "=" * 60)
    print("Test 2: Testing different intervals")
    print("=" * 60)
    
    intervals = ["daily", "weekly", "monthly"]
    symbol = "BNTX"
    
    for interval in intervals:
        try:
            print(f"\n   Testing interval: {interval}")
            result = get_timeseries(
                symbol=symbol,
                interval=interval,
                period="6m"
            )
            
            assert "error" not in result or not result.get("error"), f"Should not have error for {interval}"
            assert result["interval"] == interval, f"Interval should be {interval}"
            assert result["count"] > 0, f"Should have data points for {interval}"
            
            print(f"      ✅ {interval}: {result['count']} data points")
        except Exception as e:
            print(f"      ❌ {interval} failed: {e}")
            return False
    
    return True


def test_periods():
    """Test different periods."""
    print("\n" + "=" * 60)
    print("Test 3: Testing different periods")
    print("=" * 60)
    
    periods = ["1m", "3m", "6m", "1y", "5y"]
    symbol = "GILD"
    
    for period in periods:
        try:
            print(f"\n   Testing period: {period}")
            result = get_timeseries(
                symbol=symbol,
                interval="daily",
                period=period
            )
            
            assert "error" not in result or not result.get("error"), f"Should not have error for {period}"
            assert result["count"] > 0, f"Should have data points for {period}"
            
            print(f"      ✅ {period}: {result['count']} data points")
        except Exception as e:
            print(f"      ❌ {period} failed: {e}")
            return False
    
    return True


def test_date_range():
    """Test custom date range."""
    print("\n" + "=" * 60)
    print("Test 4: Testing custom date range")
    print("=" * 60)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        result = get_timeseries(
            symbol="REGN",
            interval="daily",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        assert "error" not in result or not result.get("error"), "Should not have error"
        assert result["count"] > 0, "Should have data points"
        
        print(f"✅ Date range test passed!")
        print(f"   Start: {result.get('start_date')}")
        print(f"   End: {result.get('end_date')}")
        print(f"   Count: {result['count']}")
        
        return True
    except Exception as e:
        print(f"❌ Date range test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_caching():
    """Test caching functionality."""
    print("\n" + "=" * 60)
    print("Test 5: Testing caching")
    print("=" * 60)
    
    try:
        symbol = "VRTX"
        interval = "daily"
        period = "1m"
        
        # First call - should be fresh
        print(f"\n   First call (should be fresh)...")
        start1 = datetime.now()
        result1 = await markets_get_timeseries(
            symbol=symbol,
            interval=interval,
            period=period
        )
        elapsed1 = (datetime.now() - start1).total_seconds()
        
        assert "metadata" in result1, "Result should have metadata"
        assert result1["metadata"].get("cache_status") == "fresh", "First call should be fresh"
        print(f"      ✅ First call completed in {elapsed1:.2f}s (status: fresh)")
        
        # Second call - should be cached
        print(f"\n   Second call (should be cached)...")
        start2 = datetime.now()
        result2 = await markets_get_timeseries(
            symbol=symbol,
            interval=interval,
            period=period
        )
        elapsed2 = (datetime.now() - start2).total_seconds()
        
        assert "metadata" in result2, "Result should have metadata"
        assert result2["metadata"].get("cache_status") == "cached", "Second call should be cached"
        assert result1["count"] == result2["count"], "Cached result should match"
        print(f"      ✅ Second call completed in {elapsed2:.2f}s (status: cached)")
        print(f"      ✅ Cached call was {elapsed1/elapsed2:.1f}x faster")
        
        return True
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_symbol():
    """Test with invalid symbol."""
    print("\n" + "=" * 60)
    print("Test 6: Testing invalid symbol")
    print("=" * 60)
    
    try:
        result = get_timeseries(
            symbol="INVALID_SYMBOL_XYZ123",
            interval="daily",
            period="1m"
        )
        
        # Should handle gracefully (either error message or empty data)
        assert "symbol" in result, "Result should contain 'symbol'"
        print(f"✅ Invalid symbol handled gracefully")
        if "error" in result:
            print(f"   Error message: {result['error']}")
        
        return True
    except Exception as e:
        print(f"❌ Invalid symbol test failed: {e}")
        return False


def test_ohlcv_data():
    """Test that OHLCV data is properly formatted."""
    print("\n" + "=" * 60)
    print("Test 7: Testing OHLCV data format")
    print("=" * 60)
    
    try:
        result = get_timeseries(
            symbol="AMGN",
            interval="daily",
            period="3m"
        )
        
        assert result["count"] > 0, "Should have data points"
        
        # Check a few data points
        for i, point in enumerate(result["data"][:5]):
            assert "date" in point, f"Point {i} should have date"
            assert "open" in point, f"Point {i} should have open"
            assert "high" in point, f"Point {i} should have high"
            assert "low" in point, f"Point {i} should have low"
            assert "close" in point, f"Point {i} should have close"
            assert "volume" in point, f"Point {i} should have volume"
            
            # Validate data types and ranges
            assert isinstance(point["open"], (int, float)) or point["open"] is None
            assert isinstance(point["high"], (int, float)) or point["high"] is None
            assert isinstance(point["low"], (int, float)) or point["low"] is None
            assert isinstance(point["close"], (int, float)) or point["close"] is None
            assert isinstance(point["volume"], int)
        
        print(f"✅ OHLCV data format test passed!")
        print(f"   Checked {min(5, len(result['data']))} data points")
        
        return True
    except Exception as e:
        print(f"❌ OHLCV data format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running markets.get_timeseries Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Timeseries", test_basic_timeseries),
        ("Intervals", test_intervals),
        ("Periods", test_periods),
        ("Date Range", test_date_range),
        ("Caching", test_caching),
        ("Invalid Symbol", test_invalid_symbol),
        ("OHLCV Data Format", test_ohlcv_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

