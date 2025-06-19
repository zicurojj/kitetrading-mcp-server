from auth import get_valid_access_token, is_authenticated

if __name__ == "__main__":
    print("🔐 Kite Connect Authentication Setup")
    if is_authenticated():
        print("✅ Already authenticated")
    else:
        token = get_valid_access_token()
        print("✅ Auth complete, token:", token)
