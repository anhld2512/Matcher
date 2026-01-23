#!/usr/bin/env python3
"""
Quick test script to verify AI Provider System

IMPORTANT: Run from project root directory:
$ python tests/test_ai_system.py

NOT from tests/ directory:
$ cd tests && python test_ai_system.py  # ❌ Will fail
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all imports"""
    print("🔍 Testing imports...")
    try:
        from app.database import engine, Base, AISettings
        print("  ✅ Database imports OK")

        from app.ai_providers import (
            GeminiProvider, ChatGPTProvider,
            DeepSeekProvider, HuggingFaceProvider,
            get_ai_provider, load_active_provider_from_db
        )
        print("  ✅ AI providers imports OK")

        from app.worker import call_ai_provider, process_evaluation
        print("  ✅ Worker imports OK")

        from app.main import app
        print("  ✅ FastAPI app imports OK")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_app_routes():
    """Test FastAPI routes"""
    print("\n🔍 Testing API routes...")
    try:
        from app.main import app

        total_routes = len(app.routes)
        ai_routes = [r for r in app.routes if hasattr(r, 'path') and 'ai' in r.path.lower()]

        print(f"  ✅ Total routes: {total_routes}")
        print(f"  ✅ AI routes: {len(ai_routes)}")

        print("\n  AI Endpoints:")
        for route in ai_routes:
            methods = route.methods if hasattr(route, 'methods') else {'GET'}
            methods_str = ', '.join(sorted(methods))
            print(f"    - {methods_str:10s} {route.path}")

        return len(ai_routes) == 6
    except Exception as e:
        print(f"  ❌ Route test failed: {e}")
        return False


def test_providers():
    """Test AI provider instantiation"""
    print("\n🔍 Testing AI providers...")
    try:
        from app.ai_providers import get_ai_provider

        # Test each provider
        providers = {
            'gemini': {'api_key': 'test_key', 'model': 'gemini-1.5-flash'},
            'chatgpt': {'api_key': 'test_key', 'model': 'gpt-3.5-turbo'},
            'deepseek': {'api_key': 'test_key', 'model': 'deepseek-chat'},
            'huggingface': {'api_key': 'test_key', 'model': 'meta-llama/Llama-2-70b-chat-hf'}
        }

        for name, config in providers.items():
            try:
                provider = get_ai_provider(name, config)
                print(f"  ✅ {name:15s} - {provider.name}")
            except Exception as e:
                print(f"  ❌ {name:15s} - Failed: {e}")
                return False

        return True
    except Exception as e:
        print(f"  ❌ Provider test failed: {e}")
        return False


def test_database_model():
    """Test database model"""
    print("\n🔍 Testing database model...")
    try:
        from app.database import AISettings

        # Check table name
        print(f"  ✅ Table name: {AISettings.__tablename__}")

        # Check columns
        columns = ['id', 'provider', 'model_name', 'api_key', 'host', 'port', 'is_active', 'created_at', 'updated_at']
        for col in columns:
            if hasattr(AISettings, col):
                print(f"  ✅ Column: {col}")
            else:
                print(f"  ❌ Missing column: {col}")
                return False

        return True
    except Exception as e:
        print(f"  ❌ Database model test failed: {e}")
        return False


def test_worker_functions():
    """Test worker functions"""
    print("\n🔍 Testing worker functions...")
    try:
        from app.worker import call_ai_provider, process_evaluation, get_fallback_evaluation

        print(f"  ✅ call_ai_provider: {callable(call_ai_provider)}")
        print(f"  ✅ process_evaluation: {callable(process_evaluation)}")
        print(f"  ✅ get_fallback_evaluation: {callable(get_fallback_evaluation)}")

        # Test fallback
        result = get_fallback_evaluation("test error")
        if result.get('score') == 5 and 'error' in result:
            print(f"  ✅ Fallback evaluation works")
        else:
            print(f"  ❌ Fallback evaluation incorrect")
            return False

        return True
    except Exception as e:
        print(f"  ❌ Worker test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI Provider System Verification")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("API Routes", test_app_routes()))
    results.append(("AI Providers", test_providers()))
    results.append(("Database Model", test_database_model()))
    results.append(("Worker Functions", test_worker_functions()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20s} {status}")

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Setup database: python scripts/migrate_db.py")
        print("2. Configure AI provider (see docs/README.md)")
        print("3. Start app: uvicorn app.main:app --reload")
        print("\n📚 Documentation: docs/README.md (bilingual)")
        return 0
    else:
        print("\n❌ Some tests failed. Please check errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
