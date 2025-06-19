#!/usr/bin/env python3
"""
Test Environment Variable Loading
Verify that all files properly load credentials from .env file
"""

import os
import sys

def test_dotenv_loading():
    """Test if python-dotenv is working"""
    print("🧪 Testing python-dotenv loading...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv imported and loaded successfully")
        return True
    except ImportError:
        print("❌ python-dotenv not found")
        return False

def test_environment_variables():
    """Test if environment variables are loaded correctly"""
    print("\n📋 Testing environment variables...")
    
    required_vars = {
        "KITE_API_KEY": "API Key",
        "KITE_API_SECRET": "API Secret", 
        "KITE_REDIRECT_URI": "Redirect URI"
    }
    
    all_present = True
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if "SECRET" in var_name or "KEY" in var_name:
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"✅ {description}: {display_value}")
        else:
            print(f"❌ {description}: Not set")
            all_present = False
    
    return all_present

def test_auth_module():
    """Test if auth module loads environment variables correctly"""
    print("\n🔐 Testing auth module...")
    
    try:
        from auth import API_KEY, API_SECRET, REDIRECT_URI
        print(f"✅ Auth module loaded successfully")
        print(f"   API Key: {API_KEY[:10]}..." if API_KEY else "   API Key: Not set")
        print(f"   API Secret: {API_SECRET[:10]}..." if API_SECRET else "   API Secret: Not set")
        print(f"   Redirect URI: {REDIRECT_URI}")
        return True
    except Exception as e:
        print(f"❌ Error loading auth module: {e}")
        return False

def test_trade_module():
    """Test if trade module loads environment variables correctly"""
    print("\n📈 Testing trade module...")
    
    try:
        from trade import api_key
        print(f"✅ Trade module loaded successfully")
        print(f"   API Key: {api_key[:10]}..." if api_key else "   API Key: Not set")
        return True
    except Exception as e:
        print(f"❌ Error loading trade module: {e}")
        return False

def main():
    """Run all environment variable tests"""
    print("🎯 Kite Trading Server - Environment Variable Test")
    print("=" * 60)
    
    # Test 1: python-dotenv loading
    dotenv_ok = test_dotenv_loading()
    
    # Test 2: Environment variables
    env_vars_ok = test_environment_variables()
    
    # Test 3: Auth module
    auth_ok = test_auth_module()
    
    # Test 4: Trade module
    trade_ok = test_trade_module()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   python-dotenv: {'✅ PASS' if dotenv_ok else '❌ FAIL'}")
    print(f"   Environment Variables: {'✅ PASS' if env_vars_ok else '❌ FAIL'}")
    print(f"   Auth Module: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    print(f"   Trade Module: {'✅ PASS' if trade_ok else '❌ FAIL'}")
    
    if all([dotenv_ok, env_vars_ok, auth_ok, trade_ok]):
        print("\n🎉 All tests passed! Environment configuration is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check your .env file and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
