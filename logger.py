import os
import sys
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Please install it with: pip install python-dotenv", file=sys.stderr)
    print("Falling back to system environment variables only.", file=sys.stderr)

# Enhanced logging to match JavaScript version
LOG_FILE = os.getenv("LOG_FILE", "order.log")

def log_order(timestamp=None, type=None, stock=None, quantity=None,
              exchange="NSE", product="CNC", order_type="MARKET",
              price=None, trigger_price=None, order_id=None, status="SUCCESS",
              error_message=None, order_status=None):
    """Enhanced log order details with order ID, status tracking, and order status"""

    if timestamp is None:
        timestamp = datetime.now().isoformat()

    # Build log entry with order ID, status, and order status
    log_entry = f"{timestamp} | {status} | {type} | {stock} | Qty: {quantity} | {exchange} | {product} | {order_type}"

    if price is not None:
        log_entry += f" | Price: {price}"

    if trigger_price is not None:
        log_entry += f" | Trigger: {trigger_price}"

    # Add order ID if available
    if order_id is not None:
        log_entry += f" | OrderID: {order_id}"

    # Add order status from Zerodha (COMPLETE, OPEN, CANCELLED, REJECTED, etc.)
    if order_status is not None:
        log_entry += f" | OrderStatus: {order_status}"

    # Add error message if failed
    if "FAILED" in status and error_message is not None:
        log_entry += f" | Error: {error_message}"

    log_entry += "\n"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write order log: {e}")
