#!/usr/bin/env python3
"""
Simple verification script for Phase 1 implementation.

This script verifies that:
1. SERVICE_NOT_CONFIGURED error code is available
2. Config module can be imported and used
3. Cache module can be imported and used
4. All exports are available from common.__init__
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    # Test error code
    from common.errors import ErrorCode
    assert hasattr(ErrorCode, 'SERVICE_NOT_CONFIGURED')
    assert ErrorCode.SERVICE_NOT_CONFIGURED == "SERVICE_NOT_CONFIGURED"
    print("✓ ErrorCode.SERVICE_NOT_CONFIGURED is available")
    
    # Test config module
    from common.config import (
        ServerConfig,
        ConfigValidationError,
        ConfigIssue,
        validate_config_or_raise,
    )
    print("✓ Config module imports successful")
    
    # Test cache module
    from common.cache import (
        Cache,
        CacheEntry,
        get_cache,
        build_cache_key,
        build_cache_key_simple,
    )
    print("✓ Cache module imports successful")
    
    # Test common.__init__ exports
    from common import (
        ErrorCode,
        ServerConfig,
        ConfigValidationError,
        Cache,
        get_cache,
        build_cache_key,
    )
    print("✓ Common module exports successful")
    
    return True

def test_cache_basic():
    """Test basic cache functionality."""
    print("\nTesting cache functionality...")
    
    from common.cache import Cache, build_cache_key
    
    cache = Cache()
    
    # Test set/get
    cache.set("test_key", "test_value", ttl_seconds=60)
    value = cache.get("test_key")
    assert value == "test_value"
    print("✓ Cache set/get works")
    
    # Test build_cache_key
    key = build_cache_key("server1", "tool1", {"param": "value"})
    assert isinstance(key, str)
    assert key.startswith("server1:tool1:")
    print("✓ build_cache_key works")
    
    # Test cache key normalization
    key1 = build_cache_key("server", "tool", {"a": 1, "b": 2})
    key2 = build_cache_key("server", "tool", {"b": 2, "a": 1})
    assert key1 == key2, "Cache keys should be normalized"
    print("✓ Cache key normalization works")
    
    return True

def test_config_basic():
    """Test basic config functionality."""
    print("\nTesting config functionality...")
    
    from common.config import ServerConfig, ConfigIssue, ConfigValidationError
    
    # Test basic ServerConfig
    config = ServerConfig()
    issues = config.validate()
    assert issues == []
    assert config.is_valid() is True
    print("✓ ServerConfig basic functionality works")
    
    # Test ConfigIssue
    issue = ConfigIssue(field="TEST", message="Test message", critical=True)
    assert issue.field == "TEST"
    assert issue.critical is True
    print("✓ ConfigIssue works")
    
    # Test ConfigValidationError
    error = ConfigValidationError([issue])
    assert len(error.issues) == 1
    assert "Configuration validation failed" in str(error)
    print("✓ ConfigValidationError works")
    
    return True

if __name__ == "__main__":
    try:
        test_imports()
        test_cache_basic()
        test_config_basic()
        print("\n✅ All Phase 1 verification tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
