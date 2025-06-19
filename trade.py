import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found.", file=sys.stderr)

try:
    from kiteconnect import KiteConnect
    from kiteconnect.exceptions import KiteException, InputException, NetworkException, TokenException
except ImportError:
    class KiteConnect:
        def __init__(self, api_key): pass
        def set_access_token(self, token): pass
        def place_order(self, variety, **kwargs): return {"order_id": "MOCK_ORDER_ID"}
        def positions(self): return {"net": []}
        def orders(self): return []

    # Mock exceptions for when kiteconnect is not installed
    class KiteException(Exception): pass
    class InputException(KiteException): pass
    class NetworkException(KiteException): pass
    class TokenException(KiteException): pass

from logger import log_order
from auth import get_valid_access_token

API_KEY = os.getenv("KITE_API_KEY")
DATA_DIR = os.getenv("DATA_DIR", "./data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

if not API_KEY:
    print("❌ KITE_API_KEY not found in environment", file=sys.stderr)
    exit(1)

kc = KiteConnect(api_key=API_KEY)

def _get_user_friendly_error(error_message: str) -> str:
    """Convert technical error messages to user-friendly messages"""
    error_lower = error_message.lower()

    if "insufficient stock holding" in error_lower or "holding quantity: 0" in error_lower:
        return "❌ Cannot sell: You don't own this stock or don't have enough shares to sell."

    elif "insufficient funds" in error_lower or "insufficient balance" in error_lower:
        return "❌ Cannot buy: Insufficient funds in your account."

    elif "invalid tradingsymbol" in error_lower or "instrument not found" in error_lower:
        return "❌ Invalid stock symbol. Please check the stock name/symbol."

    elif "market is closed" in error_lower or "outside market hours" in error_lower:
        return "❌ Market is closed. Trading hours are 9:30 AM to 3:30 PM on weekdays."

    elif "price band" in error_lower or "circuit limit" in error_lower:
        return "❌ Price is outside allowed range (circuit limits). Please adjust your price."

    elif "minimum quantity" in error_lower or "lot size" in error_lower:
        return "❌ Invalid quantity. Please check minimum lot size requirements for this instrument."

    elif "pending orders" in error_lower:
        return "❌ You have pending orders for this stock. Cancel them first or wait for execution."

    elif "invalid price" in error_lower:
        return "❌ Invalid price specified. Please check your limit/trigger price."

    elif "order rejected" in error_lower:
        return "❌ Order rejected by exchange. Please check order parameters and try again."

    else:
        return f"❌ Trading error: {error_message}"

async def place_order(tradingsymbol, quantity, transaction_type="BUY",
                      exchange="NSE", product="CNC", order_type="MARKET",
                      price=None, trigger_price=None, variety="regular", validity="DAY"):
    try:
        access_token = get_valid_access_token()
        kc.set_access_token(access_token)

        order_params = {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": int(quantity),
            "product": product,
            "order_type": order_type,
            "validity": validity
        }
        if price is not None: order_params["price"] = price
        if trigger_price is not None: order_params["trigger_price"] = trigger_price

        response = kc.place_order(variety, **order_params)

        # Handle different response formats from KiteConnect API
        if isinstance(response, dict):
            order_id = response.get("order_id", "UNKNOWN")
        elif isinstance(response, str):
            order_id = response  # KiteConnect sometimes returns order_id directly as string
        else:
            order_id = str(response) if response else "UNKNOWN"

        order_status = "UNKNOWN"

        try:
            for order in kc.orders():
                if order.get("order_id") == order_id:
                    order_status = order.get("status", "UNKNOWN")
                    break
        except Exception:
            order_status = "STATUS_CHECK_FAILED"

        log_order(
            timestamp=datetime.now().isoformat(),
            type=transaction_type,
            stock=tradingsymbol,
            quantity=quantity,
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=order_id,
            status="SUCCESS",
            order_status=order_status
        )

        # Return consistent success response format
        return {
            "status": "success",
            "message": f"✅ {transaction_type} order placed successfully",
            "order_id": order_id,
            "order_status": order_status,
            "details": {
                "stock": tradingsymbol,
                "quantity": quantity,
                "transaction_type": transaction_type,
                "exchange": exchange,
                "product": product,
                "order_type": order_type,
                "price": price,
                "trigger_price": trigger_price
            }
        }

    except InputException as err:
        # Handle specific trading errors gracefully
        error_msg = str(err)
        user_friendly_msg = _get_user_friendly_error(error_msg)

        log_order(
            timestamp=datetime.now().isoformat(),
            type=transaction_type,
            stock=tradingsymbol,
            quantity=quantity,
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=None,
            status="FAILED",
            error_message=error_msg,
            order_status="REJECTED"
        )

        # Return error response instead of raising exception
        return {
            "status": "error",
            "error_type": "trading_error",
            "message": user_friendly_msg,
            "original_error": error_msg,
            "order_id": None
        }

    except TokenException as err:
        error_msg = "Authentication token expired or invalid. Please re-authenticate."

        log_order(
            timestamp=datetime.now().isoformat(),
            type=transaction_type,
            stock=tradingsymbol,
            quantity=quantity,
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=None,
            status="FAILED",
            error_message=str(err),
            order_status="AUTH_FAILED"
        )

        return {
            "status": "error",
            "error_type": "auth_error",
            "message": error_msg,
            "original_error": str(err),
            "order_id": None
        }

    except NetworkException as err:
        error_msg = "Network connection error. Please check your internet connection and try again."

        log_order(
            timestamp=datetime.now().isoformat(),
            type=transaction_type,
            stock=tradingsymbol,
            quantity=quantity,
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=None,
            status="FAILED",
            error_message=str(err),
            order_status="NETWORK_ERROR"
        )

        return {
            "status": "error",
            "error_type": "network_error",
            "message": error_msg,
            "original_error": str(err),
            "order_id": None
        }

    except Exception as err:
        # Handle any other unexpected errors
        error_msg = f"Unexpected error occurred: {str(err)}"

        log_order(
            timestamp=datetime.now().isoformat(),
            type=transaction_type,
            stock=tradingsymbol,
            quantity=quantity,
            exchange=exchange,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=None,
            status="FAILED",
            error_message=str(err),
            order_status="UNKNOWN_ERROR"
        )

        return {
            "status": "error",
            "error_type": "unknown_error",
            "message": error_msg,
            "original_error": str(err),
            "order_id": None
        }

async def get_positions():
    try:
        access_token = get_valid_access_token()
        kc.set_access_token(access_token)
        positions = kc.positions()
        if positions and "net" in positions and positions["net"]:
            position_list = []
            for p in positions["net"]:
                if int(p.get('quantity', 0)) != 0:  # Only show non-zero positions
                    position_list.append(
                        f"📈 {p['tradingsymbol']}: {p['quantity']} shares @ ₹{p.get('last_price', 'N/A')}"
                    )

            if position_list:
                return "\n".join(position_list)
            else:
                return "📊 No active positions found (all positions have zero quantity)."
        return "📊 No positions found in your portfolio."

    except TokenException as err:
        return "❌ Authentication error: Please re-authenticate to view positions."

    except NetworkException as err:
        return "❌ Network error: Unable to fetch positions. Please check your connection."

    except Exception as err:
        return f"❌ Error fetching positions: {_get_user_friendly_error(str(err))}"