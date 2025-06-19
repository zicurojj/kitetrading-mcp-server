#!/usr/bin/env python3
"""
Setup Authentication for Kite MCP Server
Run this once to authenticate and save access token
"""

import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("Warning: python-dotenv not found. Please install it with: pip install python-dotenv", file=sys.stderr)
    print("Falling back to system environment variables only.", file=sys.stderr)

from auth import get_valid_access_token

def main():
    """Setup authentication for the MCP server"""
    print("🎯 Kite MCP Server - Authentication Setup")
    print("=" * 50)
    print()

    # Validate environment variables
    api_key = os.getenv("KITE_API_KEY")
    api_secret = os.getenv("KITE_API_SECRET")
    redirect_uri = os.getenv("KITE_REDIRECT_URI")

    print("📋 Environment Configuration:")
    print(f"   API Key: {api_key[:10]}..." if api_key else "   API Key: Not set")
    print(f"   API Secret: {api_secret[:10]}..." if api_secret else "   API Secret: Not set")
    print(f"   Redirect URI: {redirect_uri}")
    print()

    if not all([api_key, api_secret, redirect_uri]):
        print("⚠️  Warning: Some environment variables are missing!")
        print("   Please check your .env file and ensure all required variables are set.")
        print()

    print("This will:")
    print("1. Open your browser for Kite Connect login")
    print("2. Automatically handle the OAuth flow")
    print("3. Save your access token for the MCP server")
    print("4. Test the connection")
    print()
    
    # Check if token already exists
    if os.path.exists("kite_session.json"):
        print("📄 Found existing session file.")
        choice = input("Do you want to re-authenticate? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("✅ Using existing session. Run the MCP server with: python index.py")
            return
        else:
            # Remove existing session to force re-auth
            os.remove("kite_session.json")
            print("🗑️  Removed existing session. Starting fresh authentication...")
    
    print("\n🚀 Starting authentication process...")
    print("📝 Note: You'll need your Kite Connect login credentials")
    print()
    
    try:
        # Get access token
        access_token = get_valid_access_token()
        
        if access_token:
            print("\n" + "=" * 50)
            print("🎉 SUCCESS! Authentication completed.")
            print("✅ Access token saved and tested.")
            print("🚀 You can now run the MCP server with: python index.py")
            print("💡 The server will automatically use your saved credentials.")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ FAILED! Could not authenticate.")
            print("🔧 Please check your internet connection and try again.")
            print("📞 Make sure you have a valid Kite Connect account.")
            print("=" * 50)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Authentication cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
