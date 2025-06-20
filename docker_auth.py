#!/usr/bin/env python3
"""
Docker-compatible authentication module for Kite Connect
Handles token expiration gracefully in containerized environments
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found.", file=sys.stderr)

try:
    from kiteconnect import KiteConnect
    from kiteconnect.exceptions import TokenException
except ImportError:
    print("Error: kiteconnect not found. Install it with: pip install kiteconnect")
    sys.exit(1)

# Configuration
API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
DATA_DIR = os.getenv("DATA_DIR", "./data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
TOKEN_FILE = os.path.join(DATA_DIR, "kite_session.json")
DOCKER_MODE = os.getenv("DOCKER_MODE", "false").lower() == "true"

class DockerKiteAuth:
    def __init__(self):
        self.kc = KiteConnect(api_key=API_KEY)
        self.access_token = None
        self.user_id = None
        self.session_data = None

    def load_saved_session(self):
        """Load session from file"""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE) as f:
                    data = json.load(f)
                self.access_token = data.get('access_token')
                self.user_id = data.get('user_id')
                self.session_data = data
                if self.access_token and self.user_id:
                    self.kc.set_access_token(self.access_token)
                    return True
            except Exception as e:
                print(f"Error loading session: {e}")
        return False

    def is_token_valid(self):
        """Test if current token is valid"""
        try:
            self.kc.profile()
            return True
        except TokenException:
            return False
        except Exception as e:
            print(f"Error testing token: {e}")
            return False

    def get_access_token(self):
        """Get valid access token with automatic re-authentication support"""
        if self.load_saved_session():
            if self.is_token_valid():
                return self.access_token
            else:
                print("⚠️ Access token has expired!")
                return self._handle_token_expiration()
        else:
            print("❌ No saved session found")
            return self._handle_no_session()

    def _handle_token_expiration(self):
        """Handle token expiration with browser-assisted re-authentication"""
        browser_reauth_enabled = os.getenv("BROWSER_REAUTH", "true").lower() == "true"

        if browser_reauth_enabled:
            print("🌐 Attempting browser-assisted re-authentication...")
            if self._attempt_browser_reauth():
                print("✅ Browser-assisted re-authentication successful!")
                return self.access_token
            else:
                print("❌ Browser-assisted re-authentication failed")

        if DOCKER_MODE:
            print("💡 Re-authentication options:")
            print("   # Browser-assisted (recommended):")
            print("   docker-compose run --rm fastapi-server python browser_auth.py")
            print("   # Manual token entry:")
            print("   docker-compose run --rm fastapi-server python docker_auth_setup.py")
            raise TokenException("Access token expired. Re-authentication required.")
        else:
            print("💡 Re-authentication required:")
            print("   python browser_auth.py")
            raise TokenException("Access token expired. Please re-authenticate.")

    def _handle_no_session(self):
        """Handle missing session"""
        if DOCKER_MODE:
            print("💡 Authentication required:")
            print("   docker-compose run --rm fastapi-server python docker_auth_setup.py")
            raise TokenException("No authentication session found. Please authenticate first.")
        else:
            raise TokenException("No authentication session found. Please authenticate.")

    def _attempt_browser_reauth(self):
        """Attempt browser-assisted re-authentication"""
        try:
            import subprocess
            print("🌐 Opening browser for re-authentication...")
            result = subprocess.run([
                sys.executable, "browser_auth.py"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Reload session after successful browser auth
                return self.load_saved_session() and self.is_token_valid()
            else:
                print(f"Browser auth failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Browser auth error: {e}")
            return False

    def get_session_info(self):
        """Get session information"""
        if self.load_saved_session():
            return self.session_data
        return None

    def is_authenticated(self):
        """Check if user is authenticated with valid token"""
        if self.load_saved_session():
            return self.is_token_valid()
        return False

    def clear_session(self):
        """Clear saved session"""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            return True
        return False

# Global instance
_auth_instance = None

def get_auth_instance():
    """Get singleton auth instance"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = DockerKiteAuth()
    return _auth_instance

def get_valid_access_token():
    """Get valid access token - Docker compatible"""
    return get_auth_instance().get_access_token()

def get_session_info():
    """Get session info - Docker compatible"""
    return get_auth_instance().get_session_info()

def is_authenticated():
    """Check authentication status - Docker compatible"""
    return get_auth_instance().is_authenticated()

def clear_session():
    """Clear session - Docker compatible"""
    return get_auth_instance().clear_session()

# Backwards compatibility
def get_kite_instance():
    """Get configured KiteConnect instance"""
    auth = get_auth_instance()
    if auth.load_saved_session() and auth.is_token_valid():
        return auth.kc
    else:
        raise TokenException("No valid authentication session")

if __name__ == "__main__":
    print("Docker-compatible Kite Connect Auth Module")
    if is_authenticated():
        print("✅ Authentication valid")
        session = get_session_info()
        if session:
            print(f"👤 User: {session.get('user_name', 'Unknown')}")
            print(f"🆔 User ID: {session.get('user_id', 'Unknown')}")
    else:
        print("❌ No valid authentication")
        if DOCKER_MODE:
            print("💡 Run: docker-compose run --rm fastapi-server python docker_auth_setup.py")
        else:
            print("💡 Run: python docker_auth_setup.py")
