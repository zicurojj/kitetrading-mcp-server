import os
from datetime import datetime
from pathlib import Path

LOG_FILE = os.getenv("LOG_FILE", "./logs/order.log")
Path(os.path.dirname(LOG_FILE)).mkdir(parents=True, exist_ok=True)

def log_order(timestamp=None, type=None, stock=None, quantity=None,
              exchange="NSE", product="CNC", order_type="MARKET",
              price=None, trigger_price=None, order_id=None, status="SUCCESS",
              error_message=None, order_status=None):
    timestamp = timestamp or datetime.now().isoformat()
    parts = [
        timestamp, status, type, stock, f"Qty: {quantity}", exchange,
        product, order_type
    ]
    if price is not None: parts.append(f"Price: {price}")
    if trigger_price is not None: parts.append(f"Trigger: {trigger_price}")
    if order_id: parts.append(f"OrderID: {order_id}")
    if order_status: parts.append(f"OrderStatus: {order_status}")
    if "FAILED" in status and error_message: parts.append(f"Error: {error_message}")
    line = " | ".join(str(p) for p in parts) + "\n"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"Failed to log order: {e}")
