#!/usr/bin/env python3
"""
Browser-assisted authentication for Kite Connect
Automatically opens browser for manual OTP entry, then captures token automatically
Works in both local and Docker environments
"""
import os
import sys
import json
import time
import webbrowser
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("Error: kiteconnect not found. Install it with: pip install kiteconnect")
    sys.exit(1)

# Configuration
API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
REDIRECT_URI = os.getenv("KITE_REDIRECT_URI")
DATA_DIR = os.getenv("DATA_DIR", "./data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
TOKEN_FILE = os.path.join(DATA_DIR, "kite_session.json")
DOCKER_MODE = os.getenv("DOCKER_MODE", "false").lower() == "true"

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"🌐 Received request: {self.path}")
        parsed_url = urlparse(self.path)
        expected_path = urlparse(REDIRECT_URI).path
        
        if parsed_url.path == expected_path:
            request_token = parse_qs(parsed_url.query).get('request_token', [None])[0]
            if request_token:
                print(f"✅ Request token captured: {request_token[:10]}...")
                self.server.request_token = request_token
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Send a nice success page
                success_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Kite Connect - Authentication Successful</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }}
                        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
                        .success {{ color: #28a745; font-size: 24px; margin-bottom: 20px; }}
                        .token {{ background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace; word-break: break-all; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="success">✅ Authentication Successful!</div>
                        <p>Your Kite Connect authentication has been completed successfully.</p>
                        <p><strong>Request Token:</strong></p>
                        <div class="token">{request_token}</div>
                        <p style="margin-top: 20px;">You can now close this window. The trading server will automatically exchange this token for an access token.</p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
            else:
                self.send_error(400, "Request token not received.")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return  # Suppress default logging

def save_session(session_data):
    """Save session data to file"""
    now = datetime.now()
    data = {
        'access_token': session_data['access_token'],
        'user_id': session_data['user_id'],
        'user_name': session_data.get('user_name', 'Unknown'),
        'created_date': now.isoformat(),
        'created_time': now.strftime('%H:%M:%S'),
        'browser_auth': True
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Session saved to: {TOKEN_FILE}")
    return data

def open_browser_for_auth(login_url):
    """Open browser for authentication"""
    if DOCKER_MODE:
        print("🐳 Running in Docker mode")
        print("📋 Please copy this URL and open it in your browser:")
        print(f"   {login_url}")
        print("\n📝 Steps:")
        print("   1. Copy the URL above")
        print("   2. Open it in your browser")
        print("   3. Login with your Zerodha credentials")
        print("   4. Enter the OTP when prompted")
        print("   5. Authorize the application")
        print("   6. The system will automatically capture the token")
        
        # Also try to detect if we're in WSL or have display forwarding
        display = os.getenv('DISPLAY')
        if display:
            print(f"\n🖥️  Display detected ({display}), attempting to open browser...")
            try:
                webbrowser.open(login_url)
                print("✅ Browser opened successfully")
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
    else:
        print("🌐 Opening browser for authentication...")
        try:
            webbrowser.open(login_url)
            print("✅ Browser opened successfully")
            print("\n📝 Please complete the authentication in your browser:")
            print("   1. Login with your Zerodha credentials")
            print("   2. Enter the OTP when prompted")
            print("   3. Authorize the application")
            print("   4. The system will automatically capture the token")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print(f"📋 Please manually open this URL: {login_url}")

def browser_assisted_auth():
    """Perform browser-assisted authentication"""
    print("🔐 Starting browser-assisted authentication...")
    
    # Validate environment
    if not (API_KEY and API_SECRET and REDIRECT_URI):
        missing = []
        if not API_KEY: missing.append("KITE_API_KEY")
        if not API_SECRET: missing.append("KITE_API_SECRET")
        if not REDIRECT_URI: missing.append("KITE_REDIRECT_URI")
        
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        return False
    
    try:
        # Create KiteConnect instance and generate login URL
        kc = KiteConnect(api_key=API_KEY)
        login_url = kc.login_url()
        
        # Start local server to capture redirect
        port = urlparse(REDIRECT_URI).port or 8080
        print(f"🔌 Starting local server on port {port}...")
        
        try:
            server = HTTPServer(('localhost', port), AuthHandler)
            server.request_token = None
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            print(f"✅ Local server started on http://localhost:{port}")
        except Exception as e:
            print(f"❌ Failed to start local server: {e}")
            print(f"💡 Make sure port {port} is not already in use")
            return False
        
        # Open browser for authentication
        open_browser_for_auth(login_url)
        
        # Wait for request token
        print(f"\n⏳ Waiting for authentication (timeout: 300s)...")
        timeout = 300
        start_time = time.time()
        
        while not server.request_token:
            if time.time() - start_time > timeout:
                server.shutdown()
                print("❌ Authentication timeout. Please try again.")
                return False
            time.sleep(1)
        
        # Get the request token
        request_token = server.request_token
        server.shutdown()
        
        # Exchange request token for access token
        print("🔄 Exchanging request token for access token...")
        session_data = kc.generate_session(request_token, api_secret=API_SECRET)
        
        # Save session
        saved_data = save_session(session_data)
        
        print(f"\n🎉 Authentication successful!")
        print(f"👤 User: {saved_data.get('user_name', 'Unknown')}")
        print(f"🆔 User ID: {saved_data.get('user_id', 'Unknown')}")
        print(f"📅 Session created: {saved_data.get('created_date', 'Unknown')}")
        
        # Test the token
        print("\n🧪 Testing access token...")
        kc.set_access_token(session_data['access_token'])
        profile = kc.profile()
        print(f"✅ Token test successful - Welcome {profile.get('user_name', 'Unknown')}!")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def check_existing_session():
    """Check if there's already a valid session"""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
            
            access_token = data.get('access_token')
            if access_token:
                # Test the token
                kc = KiteConnect(api_key=API_KEY)
                kc.set_access_token(access_token)
                profile = kc.profile()
                
                print(f"✅ Existing session found and valid")
                print(f"👤 User: {data.get('user_name', 'Unknown')}")
                print(f"🆔 User ID: {data.get('user_id', 'Unknown')}")
                print(f"📅 Created: {data.get('created_date', 'Unknown')}")
                return True
                
        except Exception as e:
            print(f"⚠️  Existing session invalid: {e}")
            print("🔄 Will create new session...")
    
    return False

def main():
    """Main authentication function"""
    print("🔐 Kite Connect Browser-Assisted Authentication")
    print("=" * 50)
    
    # Check for existing valid session
    if check_existing_session():
        print("\n🎉 Authentication already complete!")
        return
    
    # Run browser-assisted authentication
    if browser_assisted_auth():
        print("\n✅ Browser-assisted authentication complete!")
        print("🚀 You can now start the trading server")
    else:
        print("\n❌ Authentication failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
