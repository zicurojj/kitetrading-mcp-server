import sys
import os
from datetime import datetime

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
    print("Warning: kiteconnect not found. Please install it with: pip install kiteconnect", file=sys.stderr)
    # Mock KiteConnect for testing
    class KiteConnect:
        def __init__(self, api_key):
            self.api_key = api_key
        def set_access_token(self, token):
            _ = token  # Acknowledge parameter
            pass
        def place_order(self, variety, **kwargs):
            _ = variety  # Acknowledge parameter
            _ = kwargs   # Acknowledge parameter
            return {"order_id": "MOCK_ORDER_ID"}
        def positions(self):
            return {"net": []}

from logger import log_order
from auth import get_valid_access_token

# API credentials - Load from .env file
api_key = os.getenv("KITE_API_KEY")

# Validate required environment variable
if not api_key:
    print("❌ Error: KITE_API_KEY not found in environment variables", file=sys.stderr)
    print("   Please set KITE_API_KEY in your .env file", file=sys.stderr)
    exit(1)

# Initialize KiteConnect client
kc = KiteConnect(api_key=api_key)

# Use the auth system directly

async def place_order(tradingsymbol, quantity, transaction_type="BUY",
                     exchange="NSE", product="CNC", order_type="MARKET",
                     price=None, trigger_price=None, variety="regular", validity="DAY"):
    """Simple place_order function with fixed defaults for Claude Desktop"""

    # Validate input parameters
    if (not isinstance(tradingsymbol, str) or
        not isinstance(quantity, (int, float)) or
        transaction_type not in ["BUY", "SELL"]):
        raise ValueError("Invalid input parameters")

    try:
        # Get fresh access token
        access_token = get_valid_access_token()
        if not access_token:
            raise Exception("Failed to get valid access token")
        kc.set_access_token(access_token)

        # Build order parameters (excluding variety since it's passed separately)
        order_params = {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": int(quantity),
            "product": product,
            "order_type": order_type,
            "validity": validity
        }

        # Add optional parameters
        if price is not None:
            order_params["price"] = price
        if trigger_price is not None:
            order_params["trigger_price"] = trigger_price

        # Place order (variety is passed as first argument, not in params)
        response = kc.place_order(variety, **order_params)
        timestamp = datetime.now().isoformat()

        # Extract order ID from response
        order_id = None
        if isinstance(response, dict) and 'order_id' in response:
            order_id = response['order_id']
        elif isinstance(response, str):
            order_id = response

        print(f"{transaction_type} order placed for {quantity} shares of {tradingsymbol} | Order ID: {order_id}", file=sys.stderr)

        # Check order status after placement
        order_status = None
        if order_id:
            try:
                # Get order status from Zerodha
                orders = kc.orders()
                for order in orders:
                    if order.get('order_id') == order_id:
                        order_status = order.get('status', 'UNKNOWN')
                        status_message = order.get('status_message', '')

                        print(f"📋 Order Status: {order_status}", file=sys.stderr)
                        if status_message:
                            print(f"💬 Status Message: {status_message}", file=sys.stderr)
                        break
            except Exception as status_err:
                print(f"⚠️ Could not fetch order status: {status_err}", file=sys.stderr)
                order_status = "STATUS_CHECK_FAILED"

        # Enhanced logging with order ID, success status, and order status
        log_order(
            timestamp=timestamp,
            type=transaction_type,
            stock=tradingsymbol,
            quantity=int(quantity),
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=order_id,
            status="SUCCESS",
            order_status=order_status
        )

        return response

    except Exception as err:
        timestamp = datetime.now().isoformat()
        error_message = str(err)

        # Enhanced error detection and categorization
        if "insufficient" in error_message.lower():
            error_type = "INSUFFICIENT_FUNDS"
            print(f"💰 INSUFFICIENT FUNDS: Cannot place {transaction_type} order for {quantity} {tradingsymbol}", file=sys.stderr)
            print(f"💡 Please add funds to your account or reduce quantity", file=sys.stderr)
        elif "margin" in error_message.lower():
            error_type = "MARGIN_SHORTAGE"
            print(f"📊 MARGIN SHORTAGE: Insufficient margin for {quantity} {tradingsymbol}", file=sys.stderr)
        elif "quantity" in error_message.lower() and "holdings" in error_message.lower():
            error_type = "INSUFFICIENT_HOLDINGS"
            print(f"📉 INSUFFICIENT HOLDINGS: Cannot sell {quantity} {tradingsymbol} - not enough shares", file=sys.stderr)
        elif "market" in error_message.lower() and "closed" in error_message.lower():
            error_type = "MARKET_CLOSED"
            print(f"🕐 MARKET CLOSED: Cannot place order outside trading hours", file=sys.stderr)
        else:
            error_type = "OTHER_ERROR"
            print(f"❌ ORDER FAILED: {error_message}", file=sys.stderr)

        print(f"🔍 Full error details: {err}", file=sys.stderr)

        # Log failed order with enhanced error categorization
        log_order(
            timestamp=timestamp,
            type=transaction_type,
            stock=tradingsymbol,
            quantity=int(quantity),
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=None,
            status=f"FAILED_{error_type}",
            error_message=error_message,
            order_status="REJECTED"
        )

        raise



async def get_positions():
    """Get current positions from Zerodha - matching JavaScript version"""
    try:
        # Get fresh access token
        access_token = get_valid_access_token()
        if not access_token:
            raise Exception("Failed to get valid access token")
        kc.set_access_token(access_token)
        positions = kc.positions()

        # Format positions exactly like JavaScript version
        position_strings = []
        for pos in positions["net"]:
            position_str = f"stock: {pos['tradingsymbol']}, qty: {pos['quantity']}, currentPrice: {pos['last_price']}"
            position_strings.append(position_str)

        return "\n".join(position_strings) if position_strings else "No positions found."

    except Exception as err:
        print(f"Error fetching positions: {err}", file=sys.stderr)
        return "Failed to fetch positions."