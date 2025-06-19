#!/usr/bin/env python3
"""
Kite Connect Authentication Handler
Simple and efficient authentication flow:
1. User logs in once on web with mobile app OTP
2. Captures request token automatically
3. Swaps for access token automatically
4. Saves access token for continuous trading
"""

import os
import sys
import json
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Please install it with: pip install python-dotenv", file=sys.stderr)
    print("Falling back to system environment variables only.", file=sys.stderr)

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("Warning: kiteconnect not found. Please install it with: pip install kiteconnect")
    exit(1)

# Configuration - Load from .env file
API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
REDIRECT_URI = os.getenv("KITE_REDIRECT_URI")
TOKEN_FILE = os.getenv("SESSION_FILE", "kite_session.json")

# Validate required environment variables
if not API_KEY:
    print("❌ Error: KITE_API_KEY not found in environment variables")
    print("   Please set KITE_API_KEY in your .env file")
    exit(1)

if not API_SECRET:
    print("❌ Error: KITE_API_SECRET not found in environment variables")
    print("   Please set KITE_API_SECRET in your .env file")
    exit(1)

if not REDIRECT_URI:
    print("❌ Error: KITE_REDIRECT_URI not found in environment variables")
    print("   Please set KITE_REDIRECT_URI in your .env file")
    exit(1)

class AuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from Kite Connect callback"""
        parsed_url = urlparse(self.path)

        # Extract expected path from REDIRECT_URI
        expected_path = urlparse(REDIRECT_URI).path

        if parsed_url.path == expected_path:
            # Extract request token from callback
            query_params = parse_qs(parsed_url.query)
            request_token = query_params.get('request_token', [None])[0]
            
            if request_token:
                # Store request token for processing
                self.server.request_token = request_token
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>Authorization Successful</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 100px;">
                    <h1 style="color: green;">✅ Authorization Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                    <p>Your access token has been saved automatically.</p>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
            else:
                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = """
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: Arial; text-align: center; margin-top: 100px;">
                    <h1 style="color: red;">❌ Authorization Failed!</h1>
                    <p>No request token received. Please try again.</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
        else:
            # Handle other paths
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        _ = format, args  # Acknowledge parameters
        pass

class KiteAuth:
    """Simple Kite Connect Authentication Manager"""

    def __init__(self):
        self.kc = KiteConnect(api_key=API_KEY)
        self.access_token = None
        self.user_id = None
        self.session_data = None

    def load_saved_session(self):
        """Load previously saved session data"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    self.session_data = json.load(f)

                    self.access_token = self.session_data.get('access_token')
                    self.user_id = self.session_data.get('user_id')

                    if not all([self.access_token, self.user_id]):
                        print("⚠️  Incomplete session data")
                        return False

                    print(f"✅ Using saved session for user: {self.user_id}")
                    return True

        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return False

        return False
    
    def save_session(self, session_data):
        """Save complete session data"""
        try:
            now = datetime.now()

            data = {
                'access_token': session_data['access_token'],
                'user_id': session_data['user_id'],
                'user_name': session_data.get('user_name', 'Unknown'),
                'created_date': now.isoformat(),
                'created_time': now.strftime('%H:%M:%S')
            }

            with open(TOKEN_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            self.session_data = data
            self.access_token = data['access_token']
            self.user_id = data['user_id']

            print(f"💾 Session saved for {data['user_name']}")

        except Exception as e:
            print(f"❌ Error saving session: {e}")
    
    def start_auth_flow(self):
        """Start the complete authorization flow with mobile app OTP"""
        print("🚀 Starting Kite Connect authentication...")
        print("📱 You'll need to:")
        print("   1. Login on Kite web with your credentials")
        print("   2. Enter the 6-digit OTP from your Kite mobile app")
        print("   3. Complete the login process")
        print()

        # Generate login URL
        login_url = self.kc.login_url()
        print(f"🔗 Opening browser for login...")

        # Extract port and path from REDIRECT_URI
        parsed_uri = urlparse(REDIRECT_URI)
        port = parsed_uri.port or 8080

        # Start local server to handle callback
        server = HTTPServer(('localhost', port), AuthHandler)
        server.request_token = None

        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # Open browser for user login
        webbrowser.open(login_url)

        print("⏳ Waiting for login completion...")
        print("💡 After entering mobile app OTP, you'll be redirected automatically")

        # Wait for callback with timeout
        timeout = 300  # 5 minutes (enough time for mobile app OTP entry)
        start_time = time.time()

        while server.request_token is None:
            if time.time() - start_time > timeout:
                server.shutdown()
                raise TimeoutError("Login timeout. Please try again.")
            time.sleep(1)

        # Get request token
        request_token = server.request_token
        server.shutdown()

        print(f"✅ Login successful! Request token received: {request_token[:10]}...")

        # Exchange request token for access token and session data
        try:
            print("🔄 Exchanging request token for access token...")
            session_data = self.kc.generate_session(request_token, api_secret=API_SECRET)

            print(f"✅ Access token generated for user: {session_data.get('user_name', 'Unknown')}")

            # Save complete session
            self.save_session(session_data)

            return session_data["access_token"]

        except Exception as e:
            raise Exception(f"Failed to generate session: {e}")
    
    def get_access_token(self):
        """Get valid access token with intelligent session management"""
        # Try to load saved session first
        if self.load_saved_session():
            # Test if token still works
            if self.test_token(self.access_token):
                return self.access_token
            else:
                print("🔄 Saved token invalid, need fresh authentication")

        # If no valid saved session, start auth flow
        print("🔐 Starting fresh authentication...")
        return self.start_auth_flow()

    def test_token(self, access_token):
        """Test if access token is working"""
        try:
            self.kc.set_access_token(access_token)
            profile = self.kc.profile()
            user_name = profile.get('user_name', 'Unknown')

            print(f"✅ Token valid! User: {user_name}")
            return True
        except Exception as e:
            print(f"❌ Token test failed: {e}")
            return False

    def get_session_info(self):
        """Get current session information"""
        if self.session_data:
            return {
                'user_name': self.session_data.get('user_name'),
                'user_id': self.session_data.get('user_id'),
                'created_time': self.session_data.get('created_time'),
                'created_date': self.session_data.get('created_date')
            }
        return None

def get_valid_access_token():
    """Main function to get a valid access token with efficient session management"""
    auth = KiteAuth()

    try:
        access_token = auth.get_access_token()

        if access_token:
            return access_token
        else:
            print("❌ Failed to get valid access token")
            return None

    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        return None

def get_session_info():
    """Get current session information"""
    auth = KiteAuth()
    if auth.load_saved_session():
        return auth.get_session_info()
    return None

def is_authenticated():
    """Check if user is currently authenticated"""
    auth = KiteAuth()
    if auth.load_saved_session():
        return auth.test_token(auth.access_token)
    return False

def clear_session():
    """Clear saved session (force re-authentication)"""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("🗑️  Session cleared. Next login will require fresh authentication.")
        return True
    return False

if __name__ == "__main__":
    print("🎯 Kite Connect Authentication Manager")
    print("=" * 50)
    print("📈 Market Hours: 9:30 AM - 3:00 PM")
    print("🔐 One login per day with mobile app code")
    print("=" * 50)

    # Show current status
    if is_authenticated():
        info = get_session_info()
        if info:
            print(f"✅ Already authenticated as: {info['user_name']}")
            print(f"🕐 Session created: {info['created_time']}")
            print(f"📅 Session date: {info['created_date']}")
            print("\n💡 No need to re-authenticate today!")
        exit(0)

    # Start authentication
    token = get_valid_access_token()

    if token:
        print(f"\n🎉 Authentication successful!")
        info = get_session_info()
        if info:
            print(f"👤 User: {info['user_name']}")
            print(f"📅 Session: {info['created_date']}")
        print("🚀 MCP server can now use this session automatically.")
    else:
        print("\n❌ Authentication failed.")
