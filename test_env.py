import os
from dotenv import load_dotenv
from auth import get_session_info

load_dotenv()

print("🔍 Verifying environment...")

required_vars = ["KITE_API_KEY", "KITE_API_SECRET", "KITE_REDIRECT_URI"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    print("❌ Missing:", ", ".join(missing))
else:
    print("✅ All required variables present")

info = get_session_info()
if info:
    print("✅ Authenticated as:", info.get("user_id"))
else:
    print("⚠️ No active session")
