#!/usr/bin/env python3
"""Quick verification script for improvements."""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    
    errors = []
    
    # Test core modules
    try:
        from app.core.config import AppConfig
        print("  ✅ AppConfig")
    except Exception as e:
        errors.append(f"AppConfig: {e}")
    
    try:
        from app.core.logger import get_logger, setup_logger
        print("  ✅ Logger")
    except Exception as e:
        errors.append(f"Logger: {e}")
    
    try:
        from app.core.constants import SessionKeys, ProcessingStatus, UIConstants
        print("  ✅ Constants")
    except Exception as e:
        errors.append(f"Constants: {e}")
    
    try:
        from app.core.exceptions import (
            AppError, DatabaseError, LLMError, 
            retry, retry_llm_call
        )
        print("  ✅ Exceptions")
    except Exception as e:
        errors.append(f"Exceptions: {e}")
    
    try:
        from app.core.models import (
            WorkspaceModel, FileMetadataModel, MessageModel,
            Workspace, FileMetadata, Message
        )
        print("  ✅ Models")
    except Exception as e:
        errors.append(f"Models: {e}")
    
    try:
        from app.core.router import PageRouter, resolve_page
        print("  ✅ Router")
    except Exception as e:
        errors.append(f"Router: {e}")
    
    try:
        from app.core.health import HealthChecker, get_health_checker
        print("  ✅ Health")
    except Exception as e:
        errors.append(f"Health: {e}")
    
    try:
        from app.core.cache import LRUCache, get_message_cache
        print("  ✅ Cache")
    except Exception as e:
        errors.append(f"Cache: {e}")
    
    try:
        from app.core.sanitizer import Sanitizer, validate_email
        print("  ✅ Sanitizer")
    except Exception as e:
        errors.append(f"Sanitizer: {e}")
    
    try:
        from app.core.rate_limiter import RateLimiter, rate_limit
        print("  ✅ Rate Limiter")
    except Exception as e:
        errors.append(f"Rate Limiter: {e}")
    
    try:
        from app.core.container import Container, get_container
        print("  ✅ Container")
    except Exception as e:
        errors.append(f"Container: {e}")
    
    try:
        from app.core.prompts import get_prompt_loader, get_system_identity
        print("  ✅ Prompts")
    except Exception as e:
        errors.append(f"Prompts: {e}")
    
    try:
        from app.core.repositories import (
            WorkspaceRepository, FileRepository,
            SQLiteWorkspaceRepository, SQLiteFileRepository
        )
        print("  ✅ Repositories")
    except Exception as e:
        errors.append(f"Repositories: {e}")
    
    return errors


def test_basic_functionality():
    """Test basic functionality of new modules."""
    print("\nTesting basic functionality...")
    
    errors = []
    
    # Test cache
    try:
        from app.core.cache import LRUCache
        cache = LRUCache(max_size=10)
        cache.set("test", "value")
        assert cache.get("test") == "value"
        print("  ✅ Cache works")
    except Exception as e:
        errors.append(f"Cache functionality: {e}")
    
    # Test models
    try:
        from app.core.models import WorkspaceModel
        ws = WorkspaceModel(name="Test Workspace")
        assert ws.name == "Test Workspace"
        print("  ✅ Models work")
    except Exception as e:
        errors.append(f"Model functionality: {e}")
    
    # Test sanitizer
    try:
        from app.core.sanitizer import Sanitizer
        result = Sanitizer.sanitize_string("Hello World")
        assert result.is_valid
        print("  ✅ Sanitizer works")
    except Exception as e:
        errors.append(f"Sanitizer functionality: {e}")
    
    # Test rate limiter
    try:
        from app.core.rate_limiter import RateLimiter, RateLimitConfig
        config = RateLimitConfig(requests_per_minute=10)
        limiter = RateLimiter(config)
        info = limiter.check("test")
        assert info.allowed
        print("  ✅ Rate limiter works")
    except Exception as e:
        errors.append(f"Rate limiter functionality: {e}")
    
    # Test retry decorator
    try:
        from app.core.exceptions import retry
        call_count = 0
        
        @retry(max_attempts=2, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_func()
        assert result == "success"
        print("  ✅ Retry decorator works")
    except Exception as e:
        errors.append(f"Retry functionality: {e}")
    
    return errors


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("PDF Analyzer Pro - Improvements Verification")
    print("=" * 60)
    
    all_errors = []
    
    # Test imports
    import_errors = test_imports()
    all_errors.extend(import_errors)
    
    # Test functionality
    func_errors = test_basic_functionality()
    all_errors.extend(func_errors)
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ Found {len(all_errors)} errors:")
        for error in all_errors:
            print(f"   - {error}")
        return 1
    else:
        print("✅ All improvements verified successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
