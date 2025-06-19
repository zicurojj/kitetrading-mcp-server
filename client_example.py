#!/usr/bin/env python3
"""
Example client for FastAPI Trading Server
Shows how to interact with the trading API
"""

import requests
import json
from typing import Optional, Dict, Any

class KiteTradingClient:
    """Simple client for Kite Trading FastAPI server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if server is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def auth_status(self) -> Dict[str, Any]:
        """Check authentication status"""
        try:
            response = self.session.get(f"{self.base_url}/auth/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def buy_stock(self, 
                  stock: str, 
                  qty: int,
                  exchange: str = "NSE",
                  product: str = "CNC", 
                  order_type: str = "MARKET",
                  price: Optional[float] = None,
                  trigger_price: Optional[float] = None,
                  variety: str = "regular",
                  validity: str = "DAY") -> Dict[str, Any]:
        """Place a buy order"""
        try:
            order_data = {
                "stock": stock,
                "qty": qty,
                "exchange": exchange,
                "product": product,
                "order_type": order_type,
                "variety": variety,
                "validity": validity
            }
            
            if price is not None:
                order_data["price"] = price
            if trigger_price is not None:
                order_data["trigger_price"] = trigger_price
            
            response = self.session.post(f"{self.base_url}/trade/buy", json=order_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.json().get("message", "Unknown error")}
        except Exception as e:
            return {"error": str(e)}
    
    def sell_stock(self, 
                   stock: str, 
                   qty: int,
                   exchange: str = "NSE",
                   product: str = "CNC", 
                   order_type: str = "MARKET",
                   price: Optional[float] = None,
                   trigger_price: Optional[float] = None,
                   variety: str = "regular",
                   validity: str = "DAY") -> Dict[str, Any]:
        """Place a sell order"""
        try:
            order_data = {
                "stock": stock,
                "qty": qty,
                "exchange": exchange,
                "product": product,
                "order_type": order_type,
                "variety": variety,
                "validity": validity
            }
            
            if price is not None:
                order_data["price"] = price
            if trigger_price is not None:
                order_data["trigger_price"] = trigger_price
            
            response = self.session.post(f"{self.base_url}/trade/sell", json=order_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.json().get("message", "Unknown error")}
        except Exception as e:
            return {"error": str(e)}
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current portfolio positions"""
        try:
            response = self.session.get(f"{self.base_url}/trade/positions")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.json().get("message", "Unknown error")}
        except Exception as e:
            return {"error": str(e)}

def main():
    """Example usage of the trading client"""
    print("📱 Kite Trading Client Example")
    print("=" * 40)
    
    # Initialize client
    client = KiteTradingClient()
    
    # 1. Health check
    print("🏥 Checking server health...")
    health = client.health_check()
    if "error" in health:
        print(f"❌ Server not reachable: {health['error']}")
        print("💡 Make sure to start the server: python fastapi_server.py")
        return
    else:
        print(f"✅ Server is running: {health.get('status', 'Unknown')}")
    
    # 2. Check authentication
    print("\n🔐 Checking authentication...")
    auth = client.auth_status()
    if "error" in auth:
        print(f"❌ Auth check failed: {auth['error']}")
        return
    elif not auth.get('success'):
        print(f"⚠️  Not authenticated: {auth.get('message')}")
        print("💡 Run: python setup_auth.py")
        return
    else:
        user_info = auth.get('user_info', {})
        print(f"✅ Authenticated as: {user_info.get('user_name', 'Unknown')}")
    
    # 3. Get current positions
    print("\n📊 Getting current positions...")
    positions = client.get_positions()
    if "error" in positions:
        print(f"❌ Failed to get positions: {positions['error']}")
    else:
        print(f"✅ {positions.get('message')}")
        if positions.get('positions'):
            print(f"📈 Positions: {positions['positions']}")
    
    # 4. Example orders (commented out for safety)
    print("\n📝 Example order calls (not executed):")
    print("# Buy 1 RELIANCE at market price")
    print("# result = client.buy_stock('RELIANCE', 1)")
    print("# print(result)")
    print()
    print("# Buy 10 TCS with limit price")
    print("# result = client.buy_stock('TCS', 10, order_type='LIMIT', price=3500)")
    print("# print(result)")
    print()
    print("# Buy NIFTY options for intraday")
    print("# result = client.buy_stock('NIFTY2561926000CE', 75, exchange='NFO', product='MIS')")
    print("# print(result)")
    
    print("\n🎉 Example completed!")
    print("📖 For more details, check: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
