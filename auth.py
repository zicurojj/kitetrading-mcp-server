#!/usr/bin/env python3
import os
import sys
import json
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Install it with: pip install python-dotenv", file=sys.stderr)

try:
    from kiteconnect import KiteConnect
except ImportError:
    print("Warning: kiteconnect not found. Install it with: pip install kiteconnect")
    sys.exit(1)

# Configuration
API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
REDIRECT_URI = os.getenv("KITE_REDIRECT_URI")
DATA_DIR = os.getenv("DATA_DIR", "./data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
TOKEN_FILE = os.path.join(DATA_DIR, "kite_session.json")

# Validation
if not (API_KEY and API_SECRET and REDIRECT_URI):
    print("❌ Missing required environment variables. Check .env.")
    sys.exit(1)

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        expected_path = urlparse(REDIRECT_URI).path

        if parsed_url.path == expected_path:
            request_token = parse_qs(parsed_url.query).get('request_token', [None])[0]
            if request_token:
                self.server.request_token = request_token
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authentication successful. You can close this window.")
            else:
                self.send_error(400, "Request token not received.")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return

class KiteAuth:
    def __init__(self):
        self.kc = KiteConnect(api_key=API_KEY)
        self.access_token = None
        self.user_id = None
        self.session_data = None

    def load_saved_session(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE) as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.user_id = data.get('user_id')
                if self.access_token and self.user_id:
                    self.kc.set_access_token(self.access_token)
                    return True
        return False

    def save_session(self, session_data):
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

    def start_auth_flow(self):
        login_url = self.kc.login_url()
        print(f"\n🌐 Please open this URL in your browser to authenticate:\n{login_url}\n")
        port = urlparse(REDIRECT_URI).port or 8080
        server = HTTPServer(('localhost', port), AuthHandler)
        server.request_token = None
        threading.Thread(target=server.serve_forever, daemon=True).start()

        timeout = 300
        start_time = time.time()
        while not server.request_token:
            if time.time() - start_time > timeout:
                server.shutdown()
                raise TimeoutError("Login timeout.")
            time.sleep(1)

        token = server.request_token
        server.shutdown()
        session_data = self.kc.generate_session(token, api_secret=API_SECRET)
        self.save_session(session_data)
        return session_data['access_token']

    def get_access_token(self):
        if self.load_saved_session():
            try:
                self.kc.profile()
                return self.access_token
            except Exception:
                print("Saved token invalid. Re-authenticating.")
        return self.start_auth_flow()

def get_valid_access_token():
    return KiteAuth().get_access_token()

def get_session_info():
    auth = KiteAuth()
    if auth.load_saved_session():
        return auth.session_data
    return None

def is_authenticated():
    auth = KiteAuth()
    return auth.load_saved_session()

def clear_session():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        return True
    return False

if __name__ == "__main__":
    print("Kite Connect Auth Module")
    if is_authenticated():
        print("✅ Already authenticated")
    else:
        get_valid_access_token()
