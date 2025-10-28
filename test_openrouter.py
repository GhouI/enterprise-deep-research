#!/usr/bin/env python3
"""
Test script for OpenRouter integration.

This script verifies that:
1. OpenRouter API key is configured
2. Connection to OpenRouter works
3. Claude Sonnet 4 model is accessible
4. Response quality is good

Usage:
    python test_openrouter.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_vars():
    """Test that required environment variables are set."""
    print("=" * 60)
    print("STEP 1: Checking Environment Variables")
    print("=" * 60)

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    valyu_key = os.getenv("VALYU_API_KEY")

    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY is not set!")
        print("   Please add it to your .env file:")
        print('   OPENROUTER_API_KEY="sk-or-v1-your-key-here"')
        return False

    print(f"✅ OPENROUTER_API_KEY is set: {openrouter_key[:15]}...")

    if not valyu_key:
        print("⚠️  VALYU_API_KEY is not set (optional for basic testing)")
    else:
        print(f"✅ VALYU_API_KEY is set: {valyu_key[:15]}...")

    llm_provider = os.getenv("LLM_PROVIDER", "not set")
    llm_model = os.getenv("LLM_MODEL", "not set")

    print(f"✅ LLM_PROVIDER: {llm_provider}")
    print(f"✅ LLM_MODEL: {llm_model}")

    return True

def test_openrouter_connection():
    """Test connection to OpenRouter API."""
    print("\n" + "=" * 60)
    print("STEP 2: Testing OpenRouter Connection")
    print("=" * 60)

    try:
        from llm_clients import get_llm_client
        print("✅ Imported llm_clients successfully")

        # Get OpenRouter client
        print("⏳ Creating OpenRouter client...")
        llm = get_llm_client(
            provider="openrouter",
            model_name="anthropic/claude-sonnet-4"
        )
        print("✅ OpenRouter client created successfully")

        return llm
    except Exception as e:
        print(f"❌ Failed to create OpenRouter client: {e}")
        return None

def test_basic_query(llm):
    """Test a basic query to OpenRouter."""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Basic Query")
    print("=" * 60)

    try:
        from langchain.schema import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="You are a helpful AI assistant."),
            HumanMessage(content="Hello! Please respond with 'OpenRouter connection successful!' if you can read this.")
        ]

        print("⏳ Sending test message to Claude Sonnet 4 via OpenRouter...")
        response = llm.invoke(messages)

        print("\n📨 Response received:")
        print("-" * 60)
        print(response.content)
        print("-" * 60)

        if "openrouter" in response.content.lower() or "successful" in response.content.lower():
            print("✅ Response looks correct!")
        else:
            print("⚠️  Response received, but doesn't match expected format")

        return True
    except Exception as e:
        print(f"❌ Failed to get response: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_research_query(llm):
    """Test a market research-style query."""
    print("\n" + "=" * 60)
    print("STEP 4: Testing Market Research Query")
    print("=" * 60)

    try:
        from langchain.schema import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="You are an expert market research analyst."),
            HumanMessage(content="""
Please provide a brief 2-3 sentence overview of what key topics you would research
for a brand selling organic skincare products targeting millennial women.
            """)
        ]

        print("⏳ Sending market research query...")
        response = llm.invoke(messages)

        print("\n📊 Market Research Response:")
        print("-" * 60)
        print(response.content)
        print("-" * 60)
        print("✅ Market research query successful!")

        return True
    except Exception as e:
        print(f"❌ Failed market research query: {e}")
        return False

def test_model_switching():
    """Test switching between different models."""
    print("\n" + "=" * 60)
    print("STEP 5: Testing Model Switching")
    print("=" * 60)

    try:
        from llm_clients import get_llm_client
        from langchain.schema import HumanMessage

        models_to_test = [
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3.5-sonnet",
        ]

        for model in models_to_test:
            try:
                print(f"\n⏳ Testing model: {model}")
                llm = get_llm_client("openrouter", model)
                response = llm.invoke([HumanMessage(content="Say 'OK' if you receive this.")])
                print(f"✅ {model}: Response received (length: {len(response.content)} chars)")
            except Exception as e:
                print(f"⚠️  {model}: Failed - {str(e)[:100]}")

        return True
    except Exception as e:
        print(f"❌ Model switching test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "🚀" * 30)
    print("OPENROUTER INTEGRATION TEST SUITE")
    print("🚀" * 30 + "\n")

    # Step 1: Check environment variables
    if not test_env_vars():
        print("\n❌ Environment check failed. Please configure your .env file.")
        return False

    # Step 2: Test OpenRouter connection
    llm = test_openrouter_connection()
    if not llm:
        print("\n❌ Connection test failed. Check your API key and configuration.")
        return False

    # Step 3: Test basic query
    if not test_basic_query(llm):
        print("\n❌ Basic query test failed.")
        return False

    # Step 4: Test market research query
    if not test_market_research_query(llm):
        print("\n❌ Market research query test failed.")
        return False

    # Step 5: Test model switching
    if not test_model_switching():
        print("\n⚠️  Model switching test had issues (non-critical)")

    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ All critical tests passed!")
    print("\n✨ OpenRouter integration is working correctly!")
    print("\nYou can now:")
    print("  1. Use OpenRouter in your application")
    print("  2. Access Claude Sonnet 4 and other models")
    print("  3. Implement the Tally webhook integration")
    print("  4. Start processing market research requests")
    print("\n" + "🎉" * 30 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
